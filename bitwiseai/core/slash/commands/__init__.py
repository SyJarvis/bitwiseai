# -*- coding: utf-8 -*-
"""
Slash 命令实现

所有内置 slash 命令的实现
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..registry import SlashCommandRegistry

# 命令处理函数的类型签名
# func: Callable[[ChatEngine, str], None | Awaitable[None]]


def register_all_commands(registry: "SlashCommandRegistry") -> None:
    """
    注册所有内置命令到注册表

    Args:
        registry: 命令注册表
    """
    from . import clear, compact, help as help_cmd, init, yolo

    clear.register(registry)
    compact.register(registry)
    help_cmd.register(registry)
    init.register(registry)
    yolo.register(registry)


__all__ = [
    "register_all_commands",
]
