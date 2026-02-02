# -*- coding: utf-8 -*-
"""
Slash 命令注册表

管理所有可用的 slash 命令
"""
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from .parser import SlashCommandCall


T = TypeVar("T", bound=Callable[..., Any])


@dataclass(frozen=True, slots=True)
class SlashCommand(Generic[T]):
    """Slash 命令定义"""
    name: str
    """命令名称（不含斜杠）"""

    func: T
    """命令处理函数"""

    description: str
    """命令描述"""

    aliases: list[str] = field(default_factory=list)
    """命令别名列表"""

    @property
    def all_names(self) -> list[str]:
        """获取所有名称（包括别名）"""
        return [self.name, *self.aliases]


class SlashCommandRegistry(Generic[T]):
    """
    Slash 命令注册表

    使用装饰器模式注册命令：
    ```python
    registry = SlashCommandRegistry()

    @registry.command
    def my_command(engine, args):
        pass
    ```
    """

    def __init__(self) -> None:
        self._commands: dict[str, SlashCommand[T]] = {}
        self._aliases: dict[str, str] = {}

    def command(
        self,
        name: str | None = None,
        description: str = "",
        aliases: list[str] | None = None,
    ) -> Callable[[T], T]:
        """
        装饰器：注册一个 slash 命令

        Args:
            name: 命令名称（默认使用函数名）
            description: 命令描述
            aliases: 命令别名列表

        Returns:
            装饰器函数
        """

        def decorator(func: T) -> T:
            cmd_name = name if name is not None else func.__name__
            cmd_aliases = aliases or []

            # 检查名称冲突
            if cmd_name in self._commands:
                raise ValueError(f"Command '{cmd_name}' already registered")

            # 检查别名冲突
            for alias in cmd_aliases:
                if alias in self._commands or alias in self._aliases:
                    raise ValueError(f"Alias '{alias}' already registered")

            # 创建命令
            command = SlashCommand(
                name=cmd_name,
                func=func,
                description=description,
                aliases=cmd_aliases,
            )

            # 注册主命令
            self._commands[cmd_name] = command

            # 注册别名
            for alias in cmd_aliases:
                self._aliases[alias] = cmd_name

            return func

        return decorator

    def register(
        self,
        name: str,
        func: T,
        description: str = "",
        aliases: list[str] | None = None,
    ) -> SlashCommand[T]:
        """
        直接注册一个 slash 命令

        Args:
            name: 命令名称
            func: 命令处理函数
            description: 命令描述
            aliases: 命令别名列表

        Returns:
            创建的 SlashCommand 对象
        """
        cmd_aliases = aliases or []

        # 检查名称冲突
        if name in self._commands:
            raise ValueError(f"Command '{name}' already registered")

        # 检查别名冲突
        for alias in cmd_aliases:
            if alias in self._commands or alias in self._aliases:
                raise ValueError(f"Alias '{alias}' already registered")

        # 创建命令
        command = SlashCommand(
            name=name,
            func=func,
            description=description,
            aliases=cmd_aliases,
        )

        # 注册主命令
        self._commands[name] = command

        # 注册别名
        for alias in cmd_aliases:
            self._aliases[alias] = name

        return command

    def get(self, name: str) -> SlashCommand[T] | None:
        """
        获取命令

        Args:
            name: 命令名称或别名

        Returns:
            SlashCommand 对象，如果不存在则返回 None
        """
        # 首先检查是否是主命令
        if name in self._commands:
            return self._commands[name]

        # 检查是否是别名
        if name in self._aliases:
            return self._commands[self._aliases[name]]

        return None

    def find(self, call: SlashCommandCall) -> SlashCommand[T] | None:
        """
        根据命令调用查找命令

        Args:
            call: Slash 命令调用

        Returns:
            SlashCommand 对象，如果不存在则返回 None
        """
        return self.get(call.name)

    def list_commands(self) -> list[SlashCommand[T]]:
        """
        列出所有已注册的命令

        Returns:
            SlashCommand 列表
        """
        return list(self._commands.values())

    def list_names(self) -> list[str]:
        """
        列出所有命令名称

        Returns:
            命令名称列表
        """
        return list(self._commands.keys())

    @property
    def commands(self) -> Mapping[str, SlashCommand[T]]:
        """获取命令字典（只读）"""
        return self._commands

    @property
    def aliases(self) -> Mapping[str, str]:
        """获取别名映射（只读）"""
        return self._aliases

    def __contains__(self, name: str) -> bool:
        """检查命令是否存在"""
        return name in self._commands or name in self._aliases

    def __len__(self) -> int:
        """获取命令数量"""
        return len(self._commands)


__all__ = [
    "SlashCommand",
    "SlashCommandRegistry",
]
