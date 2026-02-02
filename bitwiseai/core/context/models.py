# -*- coding: utf-8 -*-
"""
上下文数据模型

定义消息、检查点和上下文的数据结构
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from langchain_core.messages import BaseMessage


class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(slots=True)
class Message:
    """统一的消息模型"""
    role: MessageRole
    """消息角色"""

    content: str
    """消息内容"""

    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    """消息时间戳"""

    tool_calls: list[dict] = field(default_factory=list)
    """工具调用列表（仅 assistant 消息）"""

    tool_id: str | None = None
    """工具 ID（仅 tool 消息）"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """额外的元数据"""

    def to_langchain(self) -> BaseMessage:
        """转换为 LangChain 消息格式"""
        from langchain_core.messages import (
            HumanMessage,
            AIMessage,
            SystemMessage,
            ToolMessage,
        )

        if self.role == MessageRole.USER:
            return HumanMessage(content=self.content)
        elif self.role == MessageRole.ASSISTANT:
            return AIMessage(
                content=self.content,
                tool_calls=self.tool_calls if self.tool_calls else None,
            )
        elif self.role == MessageRole.SYSTEM:
            return SystemMessage(content=self.content)
        elif self.role == MessageRole.TOOL:
            return ToolMessage(
                content=self.content,
                tool_call_id=self.tool_id or "",
            )
        else:
            raise ValueError(f"Unknown role: {self.role}")

    @classmethod
    def from_langchain(cls, message: BaseMessage) -> "Message":
        """从 LangChain 消息创建"""
        from langchain_core.messages import (
            HumanMessage,
            AIMessage,
            SystemMessage,
            ToolMessage,
        )

        if isinstance(message, HumanMessage):
            return cls(role=MessageRole.USER, content=message.content)
        elif isinstance(message, AIMessage):
            return cls(
                role=MessageRole.ASSISTANT,
                content=message.content or "",
                tool_calls=message.tool_calls or [],
            )
        elif isinstance(message, SystemMessage):
            return cls(role=MessageRole.SYSTEM, content=message.content)
        elif isinstance(message, ToolMessage):
            return cls(
                role=MessageRole.TOOL,
                content=message.content,
                tool_id=message.tool_call_id,
            )
        else:
            raise ValueError(f"Unknown message type: {type(message)}")

    def to_dict(self) -> dict:
        """转换为字典（用于序列化）"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "tool_calls": self.tool_calls,
            "tool_id": self.tool_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """从字典创建（用于反序列化）"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            tool_calls=data.get("tool_calls", []),
            tool_id=data.get("tool_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass(slots=True)
class Checkpoint:
    """检查点"""
    id: int
    """检查点 ID"""

    timestamp: float
    """创建时间戳"""

    message_count: int
    """当前消息数量"""

    description: str = ""
    """检查点描述"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """额外的元数据"""

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "message_count": self.message_count,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        """从字典创建"""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            message_count=data["message_count"],
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(slots=True)
class ContextMetadata:
    """上下文元数据"""
    created_at: float
    """创建时间"""

    updated_at: float
    """更新时间"""

    total_messages: int
    """总消息数"""

    total_tokens: int
    """总 token 数（估算）"""

    checkpoint_count: int
    """检查点数量"""

    session_id: str
    """会话 ID"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """额外的元数据"""

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_messages": self.total_messages,
            "total_tokens": self.total_tokens,
            "checkpoint_count": self.checkpoint_count,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContextMetadata":
        """从字典创建"""
        return cls(
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            total_messages=data["total_messages"],
            total_tokens=data["total_tokens"],
            checkpoint_count=data["checkpoint_count"],
            session_id=data["session_id"],
            metadata=data.get("metadata", {}),
        )


__all__ = [
    "MessageRole",
    "Message",
    "Checkpoint",
    "ContextMetadata",
]
