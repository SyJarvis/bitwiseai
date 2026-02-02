# -*- coding: utf-8 -*-
"""
Flow 数据模型

定义工作流的数据结构
"""
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class FlowNode:
    """Flow 节点"""
    id: str
    """节点 ID（唯一标识符）"""

    label: str | list[str]
    """节点标签或提示内容"""

    kind: Literal["begin", "end", "task", "decision"]
    """节点类型"""


@dataclass(frozen=True, slots=True)
class FlowEdge:
    """Flow 边（连接节点）"""
    src: str
    """源节点 ID"""

    dst: str
    """目标节点 ID"""

    label: str | None = None
    """边标签（用于 decision 节点）"""


@dataclass(slots=True)
class Flow:
    """Flow 工作流"""
    nodes: dict[str, FlowNode]
    """所有节点字典，key 为节点 ID"""

    outgoing: dict[str, list[FlowEdge]]
    """每个节点的出边字典，key 为源节点 ID"""

    begin_id: str
    """开始节点 ID"""

    end_id: str
    """结束节点 ID"""

    def get_node(self, node_id: str) -> FlowNode | None:
        """
        获取节点

        Args:
            node_id: 节点 ID

        Returns:
            FlowNode 对象，如果不存在则返回 None
        """
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> list[FlowEdge]:
        """
        获取节点的出边

        Args:
            node_id: 节点 ID

        Returns:
            出边列表
        """
        return self.outgoing.get(node_id, [])


@dataclass(slots=True)
class TurnOutcome:
    """单次执行结果"""
    stop_reason: str | None
    """停止原因"""

    final_message: str | None
    """最终消息"""

    step_count: int
    """使用的步数"""


def parse_choice(text: str) -> str | None:
    """
    从文本中解析 choice（用于 decision 节点）

    支持格式：
    - <choice>OPTION</choice>
    - [OPTION]
    - 选择：OPTION

    Args:
        text: 待解析文本

    Returns:
        解析出的 choice，如果未找到则返回 None
    """
    import re

    # 尝试 <choice> 标签
    match = re.search(r"<choice>\s*(.+?)\s*</choice>", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 尝试方括号
    match = re.search(r"\[(.+?)\]", text)
    if match:
        return match.group(1).strip()

    # 尝试 "选择：" 格式
    match = re.search(r"选择[：:]\s*(.+?)(?:\n|$)", text)
    if match:
        return match.group(1).strip()

    return None


__all__ = [
    "FlowNode",
    "FlowEdge",
    "Flow",
    "TurnOutcome",
    "parse_choice",
]
