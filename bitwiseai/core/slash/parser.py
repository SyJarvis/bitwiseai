# -*- coding: utf-8 -*-
"""
Slash 命令解析器

解析用户输入中的 slash 命令
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class SlashCommandCall:
    """Slash 命令调用"""
    name: str
    """命令名称（不含斜杠）"""

    args: str
    """命令参数字符串"""

    raw: str
    """原始输入字符串"""


def parse_slash_command_call(text: str) -> Optional[SlashCommandCall]:
    """
    解析文本中的 slash 命令调用

    支持格式：
    - /command
    - /command arg1 arg2
    - /command "quoted arg" arg2

    Args:
        text: 用户输入文本

    Returns:
        SlashCommandCall 对象，如果不是命令则返回 None
    """
    text = text.strip()

    # 检查是否以斜杠开头
    if not text.startswith("/"):
        return None

    # 提取命令部分（第一个空格之前）
    # 支持命令名包含字母、数字、下划线、连字符、冒号
    match = re.match(r'^/([a-zA-Z0-9_\-:]+)(?:\s+(.*))?$', text)

    if not match:
        return None

    command_name = match.group(1)
    args = match.group(2) or ""

    return SlashCommandCall(
        name=command_name,
        args=args,
        raw=text
    )


def is_slash_command(text: str) -> bool:
    """
    检查文本是否是 slash 命令

    Args:
        text: 用户输入文本

    Returns:
        是否是 slash 命令
    """
    return parse_slash_command_call(text) is not None


def strip_slash_prefix(text: str) -> str:
    """
    移除文本中的 slash 前缀

    Args:
        text: 用户输入文本

    Returns:
        移除前缀后的文本
    """
    if text.startswith("/"):
        return text[1:].strip()
    return text


__all__ = [
    "SlashCommandCall",
    "parse_slash_command_call",
    "is_slash_command",
    "strip_slash_prefix",
]
