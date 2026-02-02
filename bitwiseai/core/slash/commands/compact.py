# -*- coding: utf-8 -*-
"""
/compact 命令

压缩对话上下文，保留关键信息
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...slash import SlashCommandRegistry


def register(registry: "SlashCommandRegistry") -> None:
    """
    注册 /compact 命令

    Args:
        registry: 命令注册表
    """

    @registry.command(
        name="compact",
        description="压缩对话上下文，保留关键信息以节省 token",
    )
    def compact(engine, args: str) -> str:
        """
        压缩对话上下文

        Args:
            engine: ChatEngine 实例
            args: 命令参数（忽略）

        Returns:
            操作结果消息
        """
        if hasattr(engine, "history") and engine.history:
            original_length = len(engine.history)

            # 简单的压缩策略：保留最近 N 条消息
            # TODO: 更智能的压缩策略，使用 LLM 总结历史
            keep_count = min(10, len(engine.history))
            engine.history = engine.history[-keep_count:]

            return f"上下文已压缩：从 {original_length} 条消息压缩到 {keep_count} 条。"

        return "没有需要压缩的上下文。"


__all__ = ["register"]
