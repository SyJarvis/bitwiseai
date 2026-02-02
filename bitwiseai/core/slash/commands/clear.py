# -*- coding: utf-8 -*-
"""
/clear 命令

清空对话上下文
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...slash import SlashCommandRegistry


def register(registry: "SlashCommandRegistry") -> None:
    """
    注册 /clear 命令

    Args:
        registry: 命令注册表
    """

    @registry.command(
        name="clear",
        description="清空对话上下文（历史记录）",
        aliases=["reset"],
    )
    def clear(engine, args: str) -> None:
        """
        清空对话上下文

        Args:
            engine: ChatEngine 实例
            args: 命令参数（忽略）
        """
        # 清空历史消息
        if hasattr(engine, "history") and engine.history:
            engine.history.clear()

        # 如果有上下文管理器，也清空
        if hasattr(engine, "context") and engine.context:
            engine.context.clear()

        return "对话上下文已清空。"


__all__ = ["register"]
