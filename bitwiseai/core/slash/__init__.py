# -*- coding: utf-8 -*-
"""
Slash 命令系统

提供命令解析、注册和执行功能
"""
from .parser import (
    SlashCommandCall,
    is_slash_command,
    parse_slash_command_call,
    strip_slash_prefix,
)
from .registry import SlashCommand, SlashCommandRegistry

__all__ = [
    "SlashCommandCall",
    "SlashCommand",
    "SlashCommandRegistry",
    "parse_slash_command_call",
    "is_slash_command",
    "strip_slash_prefix",
]
