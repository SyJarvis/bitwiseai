# -*- coding: utf-8 -*-
"""
Agent 主循环

实现对话 → 执行 → 反馈的正向循环
"""
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Iterator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from .models import (
    AgentConfig,
    AgentSpec,
    ExecutionContext,
    StopReason,
    TurnResult,
)
from .multi_agent import Agent, MultiAgentOrchestrator


@dataclass(slots=True)
class LoopConfig:
    """循环配置"""
    max_turns: int = 1
    """最大轮次（1 表示单轮对话）"""

    max_steps_per_turn: int = 10
    """每轮最大步骤数"""

    max_execution_time: float = 300.0
    """最大执行时间（秒）"""

    enable_checkpoint: bool = True
    """是否启用检查点"""

    checkpoint_frequency: int = 5
    """检查点频率（每 N 步）"""

    enable_streaming: bool = False
    """是否启用流式输出"""

    auto_continue: bool = False
    """是否自动继续（多轮对话）"""

    continue_threshold: float = 0.8
    """继续阈值（任务完成度低于此值时继续）"""


@dataclass(slots=True)
class LoopState:
    """循环状态"""
    turn_count: int = 0
    """当前轮次"""

    total_steps: int = 0
    """总步骤数"""

    start_time: float = field(default_factory=lambda: datetime.now().timestamp())
    """开始时间"""

    last_checkpoint_step: int = 0
    """上次检查点的步骤数"""

    messages: list[BaseMessage] = field(default_factory=list)
    """消息历史"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """额外元数据"""

    def elapsed_time(self) -> float:
        """获取已用时间"""
        return datetime.now().timestamp() - self.start_time

    def should_checkpoint(self, frequency: int) -> bool:
        """判断是否应该创建检查点"""
        steps_since_last = self.total_steps - self.last_checkpoint_step
        return steps_since_last >= frequency

    def create_checkpoint(self) -> int:
        """创建检查点"""
        self.last_checkpoint_step = self.total_steps
        return self.total_steps


class AgentLoop:
    """
    Agent 主循环

    实现完整的对话-执行-反馈循环：
    1. 接收用户输入（对话）
    2. 执行 Agent 步骤（执行）
    3. 处理结果和反馈（反馈）
    4. 判断是否继续
    """

    def __init__(
        self,
        orchestrator: MultiAgentOrchestrator,
        config: LoopConfig,
        tools: list[Any] = None,
    ):
        """
        初始化 Agent 循环

        Args:
            orchestrator: 多 Agent 编排器
            config: 循环配置
            tools: 可用工具列表
        """
        self.orchestrator = orchestrator
        self.config = config
        self.tools = tools or []

        # 回调函数
        self._on_step_callback: Optional[Callable] = None
        self._on_turn_callback: Optional[Callable] = None
        self._on_stream_callback: Optional[Callable] = None

        # 状态
        self._state: Optional[LoopState] = None
        self._running = False

    @property
    def state(self) -> LoopState:
        """获取当前循环状态"""
        if self._state is None:
            self._state = LoopState()
        return self._state

    def on_step(self, callback: Callable) -> None:
        """
        注册步骤回调

        Args:
            callback: 回调函数，签名为 callback(step_output: StepOutput) -> None
        """
        self._on_step_callback = callback

    def on_turn(self, callback: Callable) -> None:
        """
        注册轮次回调

        Args:
            callback: 回调函数，签名为 callback(turn_result: TurnResult) -> None
        """
        self._on_turn_callback = callback

    def on_stream(self, callback: Callable) -> None:
        """
        注册流式输出回调

        Args:
            callback: 回调函数，签名为 callback(token: str) -> None
        """
        self._on_stream_callback = callback

    async def run(
        self,
        query: str,
        system_prompt: str | None = None,
    ) -> TurnResult:
        """
        运行 Agent 循环

        Args:
            query: 用户查询
            system_prompt: 系统提示词（可选）

        Returns:
            最终执行结果
        """
        self._running = True
        self._state = LoopState()

        # 初始化消息历史
        messages = [HumanMessage(content=query)]

        try:
            # 执行轮次循环
            while self._running:
                self._state.turn_count += 1

                # 检查轮次限制
                if self._state.turn_count > self.config.max_turns:
                    break

                # 检查执行时间
                if self._state.elapsed_time() > self.config.max_execution_time:
                    break

                # 执行单轮
                result = await self._run_turn(
                    query=query,
                    messages=messages,
                    system_prompt=system_prompt,
                )

                # 更新消息历史
                if result.final_message:
                    messages.append(result.final_message)

                self._state.total_steps += result.total_steps

                # 调用轮次回调
                if self._on_turn_callback:
                    self._on_turn_callback(result)

                # 判断是否继续
                if not self._should_continue(result):
                    break

                # 更新查询为 AI 的输出（用于多轮对话）
                query = result.final_output or ""

            return TurnResult(
                stop_reason=StopReason.COMPLETED,
                final_message=self._state.messages[-1] if self._state.messages else None,
                steps=[],
                total_steps=self._state.total_steps,
                total_time=self._state.elapsed_time(),
                final_output=query,
            )

        finally:
            self._running = False

    async def run_stream(
        self,
        query: str,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """
        运行 Agent 循环（流式）

        Args:
            query: 用户查询
            system_prompt: 系统提示词（可选）

        Yields:
            每个 token 的字符串片段
        """
        self._running = True
        self._state = LoopState()

        messages = [HumanMessage(content=query)]

        try:
            while self._running:
                self._state.turn_count += 1

                if self._state.turn_count > self.config.max_turns:
                    break

                # 流式执行单轮
                async for token in self._run_turn_stream(
                    query=query,
                    messages=messages,
                    system_prompt=system_prompt,
                ):
                    yield token

                # 检查是否继续
                # TODO: 根据输出内容判断
                break

        finally:
            self._running = False

    async def _run_turn(
        self,
        query: str,
        messages: list[BaseMessage],
        system_prompt: str | None = None,
    ) -> TurnResult:
        """
        执行单轮对话

        Args:
            query: 查询内容
            messages: 消息历史
            system_prompt: 系统提示词

        Returns:
            轮次结果
        """
        # 创建执行上下文
        context = ExecutionContext(
            session_id=uuid.uuid4().hex,
            turn_id=uuid.uuid4().hex,
            step_number=self._state.total_steps,
            metadata=self._state.metadata.copy(),
        )

        # 执行 Agent
        result = await self.orchestrator.execute(
            query=query,
            messages=messages,
            tools=self.tools,
            context=context,
        )

        # 检查点管理
        if self.config.enable_checkpoint and self._state.should_checkpoint(
            self.config.checkpoint_frequency
        ):
            self._state.create_checkpoint()
            # TODO: 保存检查点到存储

        # 调用步骤回调
        if self._on_step_callback:
            for step in result.steps:
                self._on_step_callback(step)

        return result

    async def _run_turn_stream(
        self,
        query: str,
        messages: list[BaseMessage],
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """
        流式执行单轮对话

        Args:
            query: 查询内容
            messages: 消息历史
            system_prompt: 系统提示词

        Yields:
            每个 token 的字符串片段
        """
        # 创建执行上下文
        context = ExecutionContext(
            session_id=uuid.uuid4().hex,
            turn_id=uuid.uuid4().hex,
            step_number=self._state.total_steps,
            metadata=self._state.metadata.copy(),
        )

        # 流式执行
        input_data = self.orchestrator.main_agent.executor.llm.stream(
            messages,
            system_prompt=system_prompt,
            callback=self._on_stream_callback,
        )

        full_response = ""
        async for token in input_data:
            full_response += token
            if self._on_stream_callback:
                self._on_stream_callback(token)
            yield token

        # 更新消息历史
        messages.append(AIMessage(content=full_response))

    def _should_continue(self, result: TurnResult) -> bool:
        """
        判断是否应该继续执行

        Args:
            result: 轮次结果

        Returns:
            是否继续
        """
        # 检查停止原因
        if result.stop_reason == StopReason.TOOL_REJECTED:
            return False

        if result.stop_reason == StopReason.MAX_STEPS:
            return False

        if result.stop_reason == StopReason.ERROR:
            return False

        # 单轮模式
        if self.config.max_turns == 1:
            return False

        # 自动继续模式
        if self.config.auto_continue:
            # TODO: 更智能的判断逻辑
            # 检查输出是否包含"完成"、"结束"等关键词
            if result.final_output:
                content = result.final_output.lower()
                stop_keywords = [
                    "完成",
                    "结束",
                    "done",
                    "finished",
                    "completed",
                ]
                for keyword in stop_keywords:
                    if keyword in content:
                        return False
            return True

        return False

    def stop(self) -> None:
        """停止循环"""
        self._running = False

    def reset(self) -> None:
        """重置循环状态"""
        self._state = None
        self._running = False

    def get_stats(self) -> dict[str, Any]:
        """
        获取循环统计信息

        Returns:
            统计信息字典
        """
        return {
            "turn_count": self._state.turn_count if self._state else 0,
            "total_steps": self._state.total_steps if self._state else 0,
            "elapsed_time": self._state.elapsed_time() if self._state else 0.0,
            "is_running": self._running,
        }


__all__ = [
    "LoopConfig",
    "LoopState",
    "AgentLoop",
]
