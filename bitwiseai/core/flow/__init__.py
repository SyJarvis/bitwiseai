# -*- coding: utf-8 -*-
"""
Flow 工作流系统

提供状态机式工作流执行和 Ralph Loop 自动迭代功能
"""
from .models import Flow, FlowEdge, FlowNode, TurnOutcome, parse_choice
from .ralph import RalphLoopConfig, RalphLoopResult, create_ralph_flow, should_auto_stop
from .runner import FlowRunner

__all__ = [
    # Models
    "Flow",
    "FlowNode",
    "FlowEdge",
    "TurnOutcome",
    "parse_choice",
    # Ralph Loop
    "create_ralph_flow",
    "RalphLoopConfig",
    "RalphLoopResult",
    "should_auto_stop",
    # Runner
    "FlowRunner",
]
