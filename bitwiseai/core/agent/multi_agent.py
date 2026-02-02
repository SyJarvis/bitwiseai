# -*- coding: utf-8 -*-
"""
多 Agent 协作系统

实现主从 Agent 架构和 Agent 之间的协作
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from .models import (
    AgentConfig,
    AgentSpec,
    ExecutionContext,
    StepInput,
    StepOutput,
    StopReason,
    TurnResult,
)
from .executor import StepExecutor


@dataclass(slots=True)
class AgentTask:
    """Agent 任务"""
    task_id: str
    """任务 ID"""

    parent_agent: str
    """父 Agent 名称"""

    target_agent: str
    """目标 Agent 名称"""

    input_data: StepInput
    """输入数据"""

    context: ExecutionContext
    """执行上下文"""

    status: str = "pending"
    """状态"""

    result: Any = None
    """结果"""

    error: str | None = None
    """错误信息"""


class AgentLaborMarket:
    """
    Agent 劳动力市场

    管理所有可用的 Agent 和子 Agent
    """

    def __init__(self):
        """初始化 Agent 劳动力市场"""
        self._agents: dict[str, "Agent"] = {}
        self._fixed_subagents: dict[str, "Agent"] = {}
        self._dynamic_subagents: dict[str, "Agent"] = {}

    def register_agent(self, agent: "Agent") -> None:
        """
        注册 Agent

        Args:
            agent: Agent 实例
        """
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> Optional["Agent"]:
        """
        获取 Agent

        Args:
            name: Agent 名称

        Returns:
            Agent 实例，如果不存在则返回 None
        """
        # 首先检查固定子 Agent
        if name in self._fixed_subagents:
            return self._fixed_subagents[name]

        # 检查动态子 Agent
        if name in self._dynamic_subagents:
            return self._dynamic_subagents[name]

        # 检查主 Agent
        return self._agents.get(name)

    def add_fixed_subagent(self, agent: "Agent") -> None:
        """
        添加固定子 Agent

        Args:
            agent: 子 Agent 实例
        """
        self._fixed_subagents[agent.name] = agent
        self._agents[agent.name] = agent

    def add_dynamic_subagent(self, agent: "Agent") -> None:
        """
        添加动态子 Agent

        Args:
            agent: 子 Agent 实例
        """
        self._dynamic_subagents[agent.name] = agent
        self._agents[agent.name] = agent

    def list_agents(self) -> list[str]:
        """
        列出所有 Agent

        Returns:
            Agent 名称列表
        """
        return list(self._agents.keys())

    def list_subagents(self) -> list[str]:
        """
        列出所有子 Agent

        Returns:
            子 Agent 名称列表
        """
        return list(self._fixed_subagents.keys()) + list(self._dynamic_subagents.keys())


class Agent:
    """
    Agent 基类

    每个 Agent 有：
    - 名称和配置
    - 执行器
    - 可选的子 Agent
    """

    def __init__(
        self,
        name: str,
        spec: AgentSpec,
        llm_manager,
        labor_market: Optional[AgentLaborMarket] = None,
    ):
        """
        初始化 Agent

        Args:
            name: Agent 名称
            spec: Agent 规格
            llm_manager: LLM 管理器
            labor_market: Agent 劳动力市场
        """
        self.name = name
        self.spec = spec
        self.llm = llm_manager
        self.labor_market = labor_market or AgentLaborMarket()

        # 创建执行器
        self.executor = StepExecutor(
            llm_manager=llm_manager,
            config=spec.config,
        )

        # 注册自己到劳动力市场
        self.labor_market.register_agent(self)

    async def execute(
        self,
        query: str,
        messages: list[BaseMessage],
        tools: list[Any],
        context: ExecutionContext,
    ) -> TurnResult:
        """
        执行 Agent 任务

        Args:
            query: 用户查询
            messages: 消息历史
            tools: 可用工具
            context: 执行上下文

        Returns:
            执行结果
        """
        # 创建输入
        input_data = StepInput(
            query=query,
            messages=messages,
            tools=tools,
            context=context.metadata,
            system_prompt=self.spec.config.system_prompt,
        )

        # 执行步骤
        steps = []
        total_time = 0.0

        while True:
            # 执行单步
            step_output = await self.executor.execute_step(input_data, context)
            steps.append(step_output)
            total_time += step_output.execution_time

            # 判断是否应该停止
            stop_reason = self.executor.should_stop(step_output, context)

            if stop_reason:
                # 检查是否需要调用子 Agent
                if stop_reason == StopReason.NO_TOOL_CALLS and self.labor_market.list_subagents():
                    # 尝试委托给子 Agent
                    delegated = await self._delegate_to_subagent(
                        step_output.message,
                        messages,
                        context,
                    )
                    if delegated:
                        continue

                # 构建最终结果
                return TurnResult(
                    stop_reason=stop_reason,
                    final_message=step_output.message,
                    steps=steps,
                    total_steps=len(steps),
                    total_time=total_time,
                    final_output=step_output.message.content,
                )

            # 更新消息历史
            messages.append(step_output.message)

            # 添加工具结果到消息历史
            if step_output.tool_calls:
                from langchain_core.messages import ToolMessage

                for tc in step_output.tool_calls:
                    if tc.status == "success":
                        tool_msg = ToolMessage(
                            content=str(tc.result),
                            tool_call_id=tc.id,
                        )
                        messages.append(tool_msg)
                    elif tc.error:
                        tool_msg = ToolMessage(
                            content=f"错误: {tc.error}",
                            tool_call_id=tc.id,
                        )
                        messages.append(tool_msg)

    async def _delegate_to_subagent(
        self,
        message: BaseMessage,
        messages: list[BaseMessage],
        context: ExecutionContext,
    ) -> bool:
        """
        委托任务给子 Agent

        Args:
            message: 当前消息
            messages: 消息历史
            context: 执行上下文

        Returns:
            是否成功委托
        """
        content = message.content if isinstance(message, AIMessage) else ""

        # 分析内容，决定是否需要委托
        # TODO: 更智能的委托逻辑
        subagent_names = self.labor_market.list_subagents()

        if not subagent_names:
            return False

        # 简单实现：选择第一个可用的子 Agent
        # 实际应该根据内容选择合适的子 Agent
        subagent = self.labor_market.get_agent(subagent_names[0])
        if subagent is None:
            return False

        # 委托执行
        result = await subagent.execute(
            query=content,
            messages=messages,
            tools=[],
            context=context,
        )

        # 将结果添加到消息历史
        if result.final_message:
            messages.append(result.final_message)

        return True


class MultiAgentOrchestrator:
    """
    多 Agent 编排器

    协调多个 Agent 之间的协作
    """

    def __init__(self, main_agent: Agent):
        """
        初始化多 Agent 编排器

        Args:
            main_agent: 主 Agent
        """
        self.main_agent = main_agent
        self.labor_market = main_agent.labor_market

    def add_subagent(self, agent: Agent, fixed: bool = True) -> None:
        """
        添加子 Agent

        Args:
            agent: 子 Agent 实例
            fixed: 是否为固定子 Agent
        """
        if fixed:
            self.labor_market.add_fixed_subagent(agent)
        else:
            self.labor_market.add_dynamic_subagent(agent)

    async def execute(
        self,
        query: str,
        messages: list[BaseMessage],
        tools: list[Any],
        context: ExecutionContext,
    ) -> TurnResult:
        """
        执行多 Agent 协作任务

        Args:
            query: 用户查询
            messages: 消息历史
            tools: 可用工具
            context: 执行上下文

        Returns:
            执行结果
        """
        # 首先让主 Agent 处理
        result = await self.main_agent.execute(
            query=query,
            messages=messages,
            tools=tools,
            context=context,
        )

        return result

    async def parallel_execute(
        self,
        queries: list[str],
        context: ExecutionContext,
    ) -> list[TurnResult]:
        """
        并行执行多个查询

        Args:
            queries: 查询列表
            context: 执行上下文

        Returns:
            执行结果列表
        """
        import asyncio

        tasks = []
        for query in queries:
            messages = [HumanMessage(content=query)]
            task = self.main_agent.execute(
                query=query,
                messages=messages,
                tools=[],
                context=context,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results


__all__ = [
    "AgentTask",
    "AgentLaborMarket",
    "Agent",
    "MultiAgentOrchestrator",
]
