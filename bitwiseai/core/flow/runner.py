# -*- coding: utf-8 -*-
"""
Flow 执行器

执行 Flow 工作流
"""
import asyncio
from typing import Any

from .models import Flow, FlowNode, TurnOutcome, parse_choice


class FlowRunner:
    """
    Flow 执行器

    执行状态机式的工作流
    """

    def __init__(
        self,
        flow: Flow,
        engine: Any,
        max_moves: int = 1000,
    ):
        """
        初始化 Flow 执行器

        Args:
            flow: Flow 工作流
            engine: ChatEngine 实例
            max_moves: 最大移动次数（防止无限循环）
        """
        self._flow = flow
        self._engine = engine
        self._max_moves = max_moves

    async def run(self) -> TurnOutcome:
        """
        执行工作流

        Returns:
            执行结果
        """
        current_id = self._flow.begin_id
        moves = 0
        total_steps = 0

        while True:
            node = self._flow.get_node(current_id)
            edges = self._flow.get_outgoing_edges(current_id)

            if node is None:
                return TurnOutcome(
                    stop_reason=f"node_not_found:{current_id}",
                    final_message=f"错误：找不到节点 {current_id}",
                    step_count=total_steps,
                )

            # 处理结束节点
            if node.kind == "end":
                return TurnOutcome(
                    stop_reason="completed",
                    final_message=None,
                    step_count=total_steps,
                )

            # 处理开始节点
            if node.kind == "begin":
                if not edges:
                    return TurnOutcome(
                        stop_reason="no_edges",
                        final_message=f"错误：开始节点 {node.id} 没有出边",
                        step_count=total_steps,
                    )
                current_id = edges[0].dst
                continue

            # 检查最大移动次数
            if moves >= self._max_moves:
                return TurnOutcome(
                    stop_reason="max_moves",
                    final_message=f"已达到最大移动次数 ({self._max_moves})",
                    step_count=total_steps,
                )

            # 执行节点
            next_id, steps_used = await self._execute_node(node, edges)
            total_steps += steps_used

            if next_id is None:
                # 执行失败或中断
                return TurnOutcome(
                    stop_reason="execution_failed",
                    final_message=None,
                    step_count=total_steps,
                )

            moves += 1
            current_id = next_id

    async def _execute_node(
        self,
        node: FlowNode,
        edges: list,
    ) -> tuple[str | None, int]:
        """
        执行单个节点

        Args:
            node: 要执行的节点
            edges: 节点的出边列表

        Returns:
            (下一个节点 ID, 使用的步数)
        """
        if not edges:
            return None, 0

        # 构建提示词
        prompt = self._build_prompt(node, edges)

        # 执行一轮对话
        turn_result = await self._execute_turn(prompt)

        if turn_result.stop_reason in ("tool_rejected", "error"):
            return None, turn_result.step_count

        # 对于非决策节点，直接返回下一个节点
        if node.kind != "decision":
            return edges[0].dst, turn_result.step_count

        # 对于决策节点，解析选择
        choice = parse_choice(turn_result.final_message or "")
        next_id = self._match_edge(edges, choice)

        if next_id is not None:
            return next_id, turn_result.step_count

        # 选择无效，重新尝试
        options = ", ".join(edge.label or "" for edge in edges if edge.label)
        retry_prompt = (
            f"{prompt}\n\n"
            f"你的回答不是一个有效的选择。可选选项有：{options}。\n"
            f"请使用 <choice>...</choice> 标签明确指定你的选择。"
        )

        turn_result = await self._execute_turn(retry_prompt)
        choice = parse_choice(turn_result.final_message or "")
        next_id = self._match_edge(edges, choice)

        return next_id or edges[0].dst, turn_result.step_count + turn_result.step_count

    def _build_prompt(self, node: FlowNode, edges: list) -> str:
        """
        构建节点执行的提示词

        Args:
            node: 节点
            edges: 出边列表

        Returns:
            提示词字符串
        """
        if node.kind != "decision":
            # 非决策节点，直接返回标签
            if isinstance(node.label, str):
                return node.label
            return " ".join(str(item) for item in node.label)

        # 决策节点，列出选项
        label_text = (
            node.label if isinstance(node.label, str)
            else " ".join(str(item) for item in node.label)
        )

        choices = [edge.label for edge in edges if edge.label]
        lines = [
            label_text,
            "",
            "可用的分支：",
            *(f"- {choice}" for choice in choices),
            "",
            "请使用 <choice>...</choice> 标签来选择一个分支。",
        ]

        return "\n".join(lines)

    async def _execute_turn(self, prompt: str) -> TurnOutcome:
        """
        执行一轮对话

        Args:
            prompt: 提示词

        Returns:
            执行结果
        """
        # 调用 ChatEngine
        response = self._engine.chat(prompt, use_rag=False, use_tools=False)

        return TurnOutcome(
            stop_reason=None,
            final_message=response,
            step_count=1,
        )

    @staticmethod
    def _match_edge(edges: list, choice: str | None) -> str | None:
        """
        根据选择匹配边

        Args:
            edges: 边列表
            choice: 选择内容

        Returns:
            匹配的目标节点 ID，如果未匹配则返回 None
        """
        if not choice:
            return None

        for edge in edges:
            if edge.label == choice:
                return edge.dst

        return None


__all__ = ["FlowRunner"]
