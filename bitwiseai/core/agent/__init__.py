# -*- coding: utf-8 -*-
"""
Agent 系统

实现完整的 Agent 循环，包括对话、执行、反馈的正向循环
"""
from .models import (
    AgentCapability,
    AgentConfig,
    AgentSpec,
    ExecutionContext,
    StopReason,
    StepInput,
    StepOutput,
    StepStatus,
    ToolCall,
    TurnResult,
)
from .executor import StepExecutor
from .multi_agent import Agent, AgentLaborMarket, MultiAgentOrchestrator
from .loop import AgentLoop, LoopConfig, LoopState

__all__ = [
    # Models
    "StepStatus",
    "StopReason",
    "StepInput",
    "ToolCall",
    "StepOutput",
    "TurnResult",
    "AgentConfig",
    "AgentCapability",
    "AgentSpec",
    "ExecutionContext",
    # Executor
    "StepExecutor",
    # Multi-Agent
    "Agent",
    "AgentLaborMarket",
    "MultiAgentOrchestrator",
    # Loop
    "AgentLoop",
    "LoopConfig",
    "LoopState",
]
