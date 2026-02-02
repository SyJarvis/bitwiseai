# -*- coding: utf-8 -*-
"""
BitwiseAI - 硬件调试和日志分析的 AI 工具

专注于硬件指令验证、日志解析和智能分析
支持 Agent 循环、多会话管理、Skill 系统等高级功能
"""

__version__ = "2.0.0"
__author__ = "SyJarvis"

from .bitwiseai import BitwiseAI
from .interfaces import (
    LogParserInterface,
    VerifierInterface,
    TaskInterface,
    AnalysisTask,
    AnalysisResult,
)

# 导出核心模块
from .core import (
    SkillManager,
    Skill,
    RAGEngine,
    ChatEngine,
    # 增强版功能
    EnhancedChatEngine,
    create_chat_engine,
    LLMConfig,
    LLMProvider,
    AgentConfig,
    LoopConfig,
    # 上下文管理
    ContextManager,
    SessionManager,
    Message,
    MessageRole,
    Checkpoint,
    # Agent 系统
    Agent,
    MultiAgentOrchestrator,
    AgentLoop,
)

__all__ = [
    # 核心类
    "BitwiseAI",
    "EnhancedChatEngine",
    "create_chat_engine",

    # 接口
    "LogParserInterface",
    "VerifierInterface",
    "TaskInterface",
    "AnalysisTask",
    "AnalysisResult",

    # Skills 系统
    "SkillManager",
    "Skill",
    "RAGEngine",
    "ChatEngine",

    # 增强版功能
    "LLMConfig",
    "LLMProvider",
    "AgentConfig",
    "LoopConfig",

    # 上下文管理
    "ContextManager",
    "SessionManager",
    "Message",
    "MessageRole",
    "Checkpoint",

    # Agent 系统
    "Agent",
    "MultiAgentOrchestrator",
    "AgentLoop",

    # 版本信息
    "__version__",
]
