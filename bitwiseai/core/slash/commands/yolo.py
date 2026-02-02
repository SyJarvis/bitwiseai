# -*- coding: utf-8 -*-
"""
/yolo 命令

切换自动审批模式（You Only Live Once）
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...slash import SlashCommandRegistry


def register(registry: "SlashCommandRegistry") -> None:
    """
    注册 /yolo 命令

    Args:
        registry: 命令注册表
    """

    @registry.command(
        name="yolo",
        description="切换自动审批模式（启用后所有操作无需确认）",
    )
    def yolo(engine, args: str) -> str:
        """
        切换 YOLO 模式

        Args:
            engine: ChatEngine 实例
            args: 命令参数（可选：on/off）

        Returns:
            操作结果消息
        """
        args_lower = args.strip().lower()

        # 获取当前状态
        current_yolo = getattr(engine, "yolo_mode", False)

        # 处理参数
        if args_lower in ("on", "true", "1", "yes"):
            new_yolo = True
        elif args_lower in ("off", "false", "0", "no"):
            new_yolo = False
        elif not args_lower:
            # 无参数，切换状态
            new_yolo = not current_yolo
        else:
            return f"无效的参数: {args}。使用 'on' 或 'off'，或不带参数切换状态。"

        # 设置新状态
        engine.yolo_mode = new_yolo

        if new_yolo:
            return "🔥 You Only Live Once! 所有操作将自动批准，无需确认。"
        else:
            return "🛡️ 安全模式已启用。危险操作将需要确认。"


__all__ = ["register"]
