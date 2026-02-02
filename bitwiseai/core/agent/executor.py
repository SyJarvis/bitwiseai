# -*- coding: utf-8 -*-
"""
步骤执行器

执行单个 Agent 步骤，处理 LLM 调用和工具执行
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Optional
from langchain_core.messages import AIMessage, ToolMessage

from .models import (
    AgentConfig,
    ExecutionContext,
    StepInput,
    StepOutput,
    StepStatus,
    StopReason,
    ToolCall,
)


class StepExecutor:
    """
    步骤执行器

    负责执行单个 Agent 步骤：
    1. 调用 LLM 生成响应
    2. 解析工具调用
    3. 执行工具
    4. 返回结果
    """

    def __init__(
        self,
        llm_manager,
        config: AgentConfig,
        approval_callback: Optional[Callable[[str, str], bool]] = None,
    ):
        """
        初始化步骤执行器

        Args:
            llm_manager: LLM 管理器
            config: Agent 配置
            approval_callback: 审批回调函数
        """
        self.llm = llm_manager
        self.config = config
        self.approval_callback = approval_callback

    async def execute_step(
        self,
        input_data: StepInput,
        context: ExecutionContext,
    ) -> StepOutput:
        """
        执行单个步骤

        Args:
            input_data: 步骤输入
            context: 执行上下文

        Returns:
            步骤输出
        """
        start_time = datetime.now().timestamp()
        step_number = context.increment_step()

        try:
            # 1. 调用 LLM
            llm_response = await self._call_llm(input_data, context)

            # 2. 检查是否需要工具调用
            tool_calls = self._extract_tool_calls(llm_response)

            if not tool_calls:
                # 没有工具调用，直接返回
                return StepOutput(
                    message=llm_response,
                    status=StepStatus.SUCCESS,
                    step_number=step_number,
                    execution_time=datetime.now().timestamp() - start_time,
                )

            # 3. 执行工具调用
            tool_results = await self._execute_tool_calls(
                tool_calls,
                input_data.tools,
                context,
            )

            # 4. 创建输出
            output = StepOutput(
                message=llm_response,
                tool_calls=tool_results,
                status=self._determine_status(tool_results),
                step_number=step_number,
                execution_time=datetime.now().timestamp() - start_time,
            )

            return output

        except Exception as e:
            return StepOutput(
                message=AIMessage(content=f"执行错误: {str(e)}"),
                status=StepStatus.FAILED,
                step_number=step_number,
                execution_time=datetime.now().timestamp() - start_time,
            )

    async def _call_llm(
        self,
        input_data: StepInput,
        context: ExecutionContext,
    ) -> AIMessage:
        """
        调用 LLM

        Args:
            input_data: 步骤输入
            context: 执行上下文

        Returns:
            LLM 响应消息
        """
        # 准备消息
        messages = input_data.messages.copy()

        # 添加系统提示词
        if input_data.system_prompt or self.config.system_prompt:
            from langchain_core.messages import SystemMessage

            system_prompt = input_data.system_prompt or self.config.system_prompt
            messages = [SystemMessage(content=system_prompt)] + messages

        # 绑定工具（如果有）
        if input_data.tools and hasattr(self.llm.client, "bind_tools"):
            try:
                llm_with_tools = self.llm.client.bind_tools(input_data.tools)
                response = await llm_with_tools.ainvoke(messages)
            except Exception:
                # 绑定工具失败，使用普通调用
                response = await self.llm.client.ainvoke(messages)
        else:
            response = await self.llm.client.ainvoke(messages)

        # 确保返回 AIMessage
        if isinstance(response, AIMessage):
            return response
        else:
            return AIMessage(content=str(response))

    def _extract_tool_calls(self, message: AIMessage) -> list[ToolCall]:
        """
        从消息中提取工具调用

        Args:
            message: AI 消息

        Returns:
            工具调用列表
        """
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            return []

        tool_calls = []
        for tc in message.tool_calls:
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", f"call_{len(tool_calls)}"),
                    name=tc.get("name", ""),
                    arguments=tc.get("args", {}),
                )
            )

        return tool_calls

    async def _execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
        available_tools: list[Any],
        context: ExecutionContext,
    ) -> list[ToolCall]:
        """
        执行工具调用

        Args:
            tool_calls: 工具调用列表
            available_tools: 可用工具列表
            context: 执行上下文

        Returns:
            执行后的工具调用列表
        """
        # 构建工具字典
        tool_dict = {tool.name: tool for tool in available_tools if hasattr(tool, "name")}

        results = []

        for tool_call in tool_calls:
            # 查找工具
            tool = tool_dict.get(tool_call.name)
            if tool is None:
                tool_call.status = StepStatus.FAILED
                tool_call.error = f"工具不存在: {tool_call.name}"
                results.append(tool_call)
                continue

            # 检查是否需要审批
            if self.config.require_approval and self.approval_callback:
                action_name = f"tool:{tool_call.name}"
                description = f"调用工具 {tool_call.name}，参数: {json.dumps(tool_call.arguments, ensure_ascii=False)}"
                approved = self.approval_callback(action_name, description)

                if not approved:
                    tool_call.status = StepStatus.STOPPED
                    tool_call.error = "用户拒绝了工具调用"
                    results.append(tool_call)
                    continue

            # 执行工具
            try:
                # 调用工具的 invoke 方法
                if hasattr(tool, "ainvoke"):
                    result = await tool.ainvoke(tool_call.arguments)
                elif hasattr(tool, "invoke"):
                    result = tool.invoke(tool_call.arguments)
                else:
                    # 尝试直接调用
                    result = tool(**tool_call.arguments)

                tool_call.result = result
                tool_call.status = StepStatus.SUCCESS
                results.append(tool_call)

            except Exception as e:
                tool_call.status = StepStatus.FAILED
                tool_call.error = str(e)
                results.append(tool_call)

                # 如果启用了重试，可以在这里重试
                if self.config.retry_on_error:
                    # TODO: 实现重试逻辑
                    pass

        return results

    def _determine_status(self, tool_calls: list[ToolCall]) -> StepStatus:
        """
        根据工具调用结果确定步骤状态

        Args:
            tool_calls: 工具调用列表

        Returns:
            步骤状态
        """
        if not tool_calls:
            return StepStatus.SUCCESS

        # 检查是否有失败
        failed = [tc for tc in tool_calls if tc.status == StepStatus.FAILED]
        if failed:
            return StepStatus.FAILED

        # 检查是否有被拒绝的
        rejected = [tc for tc in tool_calls if tc.status == StepStatus.STOPPED]
        if rejected:
            return StepStatus.STOPPED

        return StepStatus.SUCCESS

    def should_stop(self, step_output: StepOutput, context: ExecutionContext) -> StopReason | None:
        """
        判断是否应该停止

        Args:
            step_output: 步骤输出
            context: 执行上下文

        Returns:
            停止原因，如果不应该停止则返回 None
        """
        # 检查步骤数限制
        if step_output.step_number >= self.config.max_steps:
            return StopReason.MAX_STEPS

        # 检查执行时间限制
        if context.elapsed_time() >= self.config.max_execution_time:
            return StopReason.COMPLETED

        # 检查工具调用状态
        if step_output.status == StepStatus.STOPPED:
            return StopReason.TOOL_REJECTED

        if step_output.status == StepStatus.FAILED:
            # 检查是否应该继续
            if not self.config.retry_on_error:
                return StopReason.ERROR

        # 没有工具调用，可以停止
        if not step_output.tool_calls:
            return StopReason.NO_TOOL_CALLS

        # 继续执行
        return None


__all__ = [
    "StepExecutor",
]
