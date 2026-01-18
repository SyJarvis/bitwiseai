# -*- coding: utf-8 -*-
"""
BitwiseAI - 硬件调试和日志分析的 AI 工具

专注于硬件指令验证、日志解析和智能分析
基于 LangChain，支持本地 Milvus 向量数据库
"""

__version__ = "2.0.0"
__author__ = "BitwiseAI"

from .bitwiseai import BitwiseAI
from .interfaces import (
    LogParserInterface,
    VerifierInterface,
    TaskInterface,
    AnalysisTask,
    AnalysisResult,
)
# 旧的工具系统已废弃，请使用 Skills 系统
# from .tools import ToolRegistry, Tool, register_builtin_tools
from .reporter import Reporter

# 导出核心模块（Skills 系统）
from .core import SkillManager, Skill, RAGEngine, ChatEngine

# 可选导出：内置实现（作为参考）
from .log_parser import LogParser, Instruction, InstructionType
from .verifier import InstructionVerifier, VerifyResult, VerifyStatus

__all__ = [
    # 核心类
    "BitwiseAI",
    
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
    
    # 报告生成
    "Reporter",
    
    # 内置实现（可选使用）
    "LogParser",
    "Instruction",
    "InstructionType",
    "InstructionVerifier",
    "VerifyResult",
    "VerifyStatus",
    
    # 版本信息
    "__version__",
]
