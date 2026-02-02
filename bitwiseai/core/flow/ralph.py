# -*- coding: utf-8 -*-
"""
Ralph Loop - 自动迭代执行

自动重复执行任务直到完成
"""
from dataclasses import dataclass, field

from .models import Flow, FlowEdge, FlowNode, TurnOutcome


def create_ralph_flow(
    user_message: str,
    max_iterations: int = 10,
) -> Flow:
    """
    创建 Ralph Loop 工作流

    Ralph Loop 会自动重复执行相同的任务，直到：
    1. 用户明确选择 STOP
    2. 达到最大迭代次数
    3. 任务完全完成

    Args:
        user_message: 用户任务描述
        max_iterations: 最大迭代次数

    Returns:
        Flow 工作流对象
    """
    # 计算总运行次数
    if max_iterations < 0:
        # 负数表示无限迭代（实际上是很大的数）
        total_runs = 10**12
    else:
        total_runs = max_iterations + 1

    # 创建节点
    nodes: dict[str, FlowNode] = {
        "BEGIN": FlowNode(id="BEGIN", label="", kind="begin"),
        "END": FlowNode(id="END", label="", kind="end"),
    }

    # 创建 R1 节点（任务执行）
    nodes["R1"] = FlowNode(
        id="R1",
        label=user_message,
        kind="task",
    )

    # 创建 R2 节点（决策点）
    decision_prompt = (
        f"{user_message}\n\n"
        "（注意：你正在自动循环模式下运行。只有当你完全确定任务已经完成时，"
        "才选择 STOP。如果还有任何未完成的工作，请选择 CONTINUE。）"
    )
    nodes["R2"] = FlowNode(
        id="R2",
        label=decision_prompt,
        kind="decision",
    )

    # 创建边
    outgoing: dict[str, list[FlowEdge]] = {
        "BEGIN": [FlowEdge(src="BEGIN", dst="R1", label=None)],
        "R1": [FlowEdge(src="R1", dst="R2", label=None)],
        "R2": [
            FlowEdge(src="R2", dst="R2", label="CONTINUE"),
            FlowEdge(src="R2", dst="END", label="STOP"),
        ],
        "END": [],
    }

    return Flow(
        nodes=nodes,
        outgoing=outgoing,
        begin_id="BEGIN",
        end_id="END",
    )


@dataclass(slots=True)
class RalphLoopConfig:
    """Ralph Loop 配置"""
    max_iterations: int = 10
    """最大迭代次数"""

    auto_stop: bool = True
    """是否自动停止（当检测到任务完成时）"""

    stop_keywords: list[str] = field(default_factory=lambda: [
        "完成",
        "done",
        "finished",
        "结束",
        "结束",
        "已解决",
        "resolved",
        "fixed",
        "修复",
    ])
    """自动停止的关键词"""


@dataclass(slots=True)
class RalphLoopResult:
    """Ralph Loop 执行结果"""
    total_iterations: int
    """实际迭代次数"""

    stopped_by: str
    """停止原因：user/auto/max_iterations"""

    final_message: str | None
    """最终消息"""

    total_steps: int
    """总步数"""


def should_auto_stop(message: str, keywords: list[str]) -> bool:
    """
    检查是否应该自动停止

    Args:
        message: 消息内容
        keywords: 停止关键词列表

    Returns:
        是否应该自动停止
    """
    message_lower = message.lower()

    # 检查是否包含完成关键词
    for keyword in keywords:
        if keyword.lower() in message_lower:
            return True

    # 检查是否明确表示不需要继续
    negative_patterns = [
        "不需要继续",
        "no need to continue",
        "任务已完成",
        "task is complete",
        "没有什么需要做的",
        "nothing more to do",
    ]

    for pattern in negative_patterns:
        if pattern.lower() in message_lower:
            return True

    return False


__all__ = [
    "create_ralph_flow",
    "RalphLoopConfig",
    "RalphLoopResult",
    "should_auto_stop",
]
