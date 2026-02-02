# -*- coding: utf-8 -*-
"""
/help 命令

显示帮助信息和可用命令列表
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...slash import SlashCommandRegistry


def register(registry: "SlashCommandRegistry") -> None:
    """
    注册 /help 命令

    Args:
        registry: 命令注册表
    """

    @registry.command(
        name="help",
        description="显示帮助信息和可用命令列表",
        aliases=["?"],
    )
    def help(engine, args: str) -> str:
        """
        显示帮助信息

        Args:
            engine: ChatEngine 实例
            args: 命令参数（可选：命令名称）

        Returns:
            帮助信息
        """
        args = args.strip()

        # 如果指定了命令名称，显示该命令的详细帮助
        if args:
            cmd = engine._slash_registry.get(args.lstrip("/"))
            if cmd:
                aliases_str = f" (别名: {', '.join(f'/{a}' for a in cmd.aliases)})" if cmd.aliases else ""
                return f"/{cmd.name}{aliases_str}\n\n{cmd.description}"
            else:
                return f"未知命令: {args}\n使用 /help 查看所有可用命令。"

        # 显示所有可用命令
        lines = [
            "## 可用的 Slash 命令",
            "",
        ]

        commands = engine._slash_registry.list_commands()
        for cmd in sorted(commands, key=lambda c: c.name):
            aliases_str = f" (别名: {', '.join(f'/{a}' for a in cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"- **/{cmd.name}**{aliases_str}: {cmd.description}")

        lines.extend([
            "",
            "## Ralph Loop 模式",
            "",
            "启用 Ralph Loop 后，AI 会自动迭代执行任务直到完成。",
            "使用方式：在调用时设置 `use_ralph_loop=True`",
            "",
            "## YOLO 模式",
            "",
            "YOLO 模式会自动批准所有操作，无需确认。",
            f"当前状态: {'🔥 已启用' if engine.yolo_mode else '🛡️ 已禁用'}",
            "使用 /yolo 切换状态。",
        ])

        return "\n".join(lines)


__all__ = ["register"]
