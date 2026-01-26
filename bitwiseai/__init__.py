# -*- coding: utf-8 -*-
"""
BitwiseAI - 硬件调试和日志分析的 AI 工具

专注于硬件指令验证、日志解析和智能分析
基于 LangChain，支持本地 Milvus 向量数据库
"""

__version__ = "0.1.3"
__author__ = "SyJarvis"

from .bitwiseai import BitwiseAI
from .interfaces import (
    LogParserInterface,
    VerifierInterface,
    TaskInterface,
    AnalysisTask,
    AnalysisResult,
)

# 导出核心模块（Skills 系统）
from .core import SkillManager, Skill, RAGEngine, ChatEngine

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
    
    # 版本信息
    "__version__",
]
