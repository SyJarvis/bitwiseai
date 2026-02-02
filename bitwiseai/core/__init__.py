# -*- coding: utf-8 -*-
"""
BitwiseAI 核心引擎模块

包含 Skill Manager、RAG Engine、Chat Engine、Slash 命令系统、Flow 工作流、上下文管理、LLM 集成和 Agent 循环
"""
from .skill_manager import SkillManager, Skill
from .rag_engine import RAGEngine
from .chat_engine import ChatEngine
from .document_manager import DocumentManager
from .skill_indexer import SkillIndexer
from .document_matcher import DocumentNameMatcher

# Slash 命令系统
from .slash import SlashCommandRegistry, SlashCommand, parse_slash_command_call

# Flow 工作流系统
from .flow import (
    Flow,
    FlowNode,
    FlowEdge,
    FlowRunner,
    TurnOutcome,
    create_ralph_flow,
    RalphLoopConfig,
    RalphLoopResult,
    parse_choice,
)

# 上下文管理系统
from .context import (
    ContextManager,
    FileStorage,
    Session,
    SessionInfo,
    SessionManager,
    Message,
    MessageRole,
    Checkpoint,
    ContextMetadata,
)

# LLM 管理系统
from .llm import LLMConfig, LLMManager, LLMProvider

# Agent 系统
from .agent import (
    Agent,
    AgentConfig,
    AgentLoop,
    AgentSpec,
    LoopConfig,
    MultiAgentOrchestrator,
    StepExecutor,
    ExecutionContext,
    TurnResult,
    StopReason,
    StepStatus,
)

# 增强版聊天引擎
from .enhanced_chat import EnhancedChatEngine, create_chat_engine

# 记忆系统
from .memory import (
    MemoryManager,
    EmbeddingProvider,
    EmbeddingError,
    EmbeddingRateLimitError,
    EmbeddingAuthenticationError,
    OpenAIEmbeddingProvider,
    ZhipuEmbeddingProvider,
    ChunkConfig,
    CompactResult,
    HybridConfig,
    IndexResult,
    MemoryChunk,
    MemoryConfig,
    MemorySource,
    MemoryStats,
    MemoryStatus,
    SearchResult,
    SyncResult,
)

__all__ = [
    # 核心组件
    "SkillManager",
    "Skill",
    "RAGEngine",
    "ChatEngine",
    "EnhancedChatEngine",
    "create_chat_engine",
    "DocumentManager",
    "SkillIndexer",
    "DocumentNameMatcher",
    # Slash 命令
    "SlashCommandRegistry",
    "SlashCommand",
    "parse_slash_command_call",
    # Flow 系统
    "Flow",
    "FlowNode",
    "FlowEdge",
    "FlowRunner",
    "TurnOutcome",
    "create_ralph_flow",
    "RalphLoopConfig",
    "RalphLoopResult",
    "parse_choice",
    # 上下文管理
    "ContextManager",
    "FileStorage",
    "Session",
    "SessionInfo",
    "SessionManager",
    "Message",
    "MessageRole",
    "Checkpoint",
    "ContextMetadata",
    # LLM 管理
    "LLMConfig",
    "LLMManager",
    "LLMProvider",
    # Agent 系统
    "Agent",
    "AgentConfig",
    "AgentSpec",
    "AgentLoop",
    "LoopConfig",
    "MultiAgentOrchestrator",
    "StepExecutor",
    "ExecutionContext",
    "TurnResult",
    "StopReason",
    "StepStatus",
    # 记忆系统
    "MemoryManager",
    "EmbeddingProvider",
    "EmbeddingError",
    "EmbeddingRateLimitError",
    "EmbeddingAuthenticationError",
    "OpenAIEmbeddingProvider",
    "ZhipuEmbeddingProvider",
    "ChunkConfig",
    "CompactResult",
    "HybridConfig",
    "IndexResult",
    "MemoryChunk",
    "MemoryConfig",
    "MemorySource",
    "MemoryStats",
    "MemoryStatus",
    "SearchResult",
    "SyncResult",
]

