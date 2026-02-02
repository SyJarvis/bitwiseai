# -*- coding: utf-8 -*-
"""
上下文管理器

管理对话上下文、检查点和历史记录
"""
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid

from .models import Checkpoint, ContextMetadata, Message, MessageRole
from .storage import FileStorage


@dataclass(slots=True)
class ContextManager:
    """
    上下文管理器

    管理对话上下文，支持：
    - 消息追加和检索
    - 检查点创建和回滚
    - 文件持久化
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """会话 ID"""

    storage: FileStorage = field(default_factory=FileStorage)
    """文件存储后端"""

    messages: list[Message] = field(default_factory=list)
    """内存中的消息列表"""

    checkpoints: list[Checkpoint] = field(default_factory=list)
    """检查点列表"""

    _next_checkpoint_id: int = 0
    """下一个检查点 ID"""

    _created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    """创建时间"""

    _updated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    """更新时间"""

    _total_tokens: int = 0
    """总 token 数（估算）"""

    def __post_init__(self):
        """初始化后设置存储路径"""
        self.storage.set_session_id(self.session_id)

    @property
    def metadata(self) -> ContextMetadata:
        """获取上下文元数据"""
        return ContextMetadata(
            created_at=self._created_at,
            updated_at=self._updated_at,
            total_messages=len(self.messages),
            total_tokens=self._total_tokens,
            checkpoint_count=len(self.checkpoints),
            session_id=self.session_id,
        )

    @property
    def is_empty(self) -> bool:
        """是否为空上下文"""
        return len(self.messages) == 0

    async def initialize(self) -> None:
        """
        初始化上下文管理器

        从文件加载之前的状态（如果存在）
        """
        await self.storage.initialize()
        loaded_data = await self.storage.load()

        if loaded_data:
            self.messages = [Message.from_dict(m) for m in loaded_data.get("messages", [])]
            self.checkpoints = [Checkpoint.from_dict(c) for c in loaded_data.get("checkpoints", [])]
            self._next_checkpoint_id = loaded_data.get("next_checkpoint_id", 0)
            self._total_tokens = loaded_data.get("total_tokens", 0)
            self._created_at = loaded_data.get("created_at", self._created_at)

    async def save(self) -> None:
        """
        保存当前状态到文件
        """
        self._updated_at = datetime.now().timestamp()
        await self.storage.save(
            messages=[m.to_dict() for m in self.messages],
            checkpoints=[c.to_dict() for c in self.checkpoints],
            next_checkpoint_id=self._next_checkpoint_id,
            total_tokens=self._total_tokens,
            created_at=self._created_at,
            updated_at=self._updated_at,
        )

    def add_message(self, message: Message | list[Message]) -> None:
        """
        添加消息到上下文

        Args:
            message: 单个消息或消息列表
        """
        if isinstance(message, list):
            self.messages.extend(message)
        else:
            self.messages.append(message)

        # 更新 token 计数（简单估算：1 token ≈ 4 字符）
        if isinstance(message, list):
            for msg in message:
                self._total_tokens += len(msg.content) // 4 + 1
        else:
            self._total_tokens += len(message.content) // 4 + 1

    def get_messages(self, max_count: int | None = None) -> list[Message]:
        """
        获取消息列表

        Args:
            max_count: 最多返回的消息数量，None 表示全部

        Returns:
            消息列表
        """
        if max_count is None:
            return self.messages.copy()
        return self.messages[-max_count:]

    def get_last_n_messages(self, n: int) -> list[Message]:
        """
        获取最近 N 条消息

        Args:
            n: 消息数量

        Returns:
            消息列表
        """
        return self.messages[-n:] if n > 0 else []

    def clear(self) -> None:
        """清空上下文"""
        self.messages.clear()
        self.checkpoints.clear()
        self._next_checkpoint_id = 0
        self._total_tokens = 0

    def create_checkpoint(self, description: str = "") -> Checkpoint:
        """
        创建检查点

        Args:
            description: 检查点描述

        Returns:
            创建的检查点
        """
        checkpoint = Checkpoint(
            id=self._next_checkpoint_id,
            timestamp=datetime.now().timestamp(),
            message_count=len(self.messages),
            description=description,
        )

        self.checkpoints.append(checkpoint)
        self._next_checkpoint_id += 1

        return checkpoint

    def get_checkpoint(self, checkpoint_id: int) -> Checkpoint | None:
        """
        获取指定检查点

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            检查点对象，如果不存在则返回 None
        """
        for checkpoint in self.checkpoints:
            if checkpoint.id == checkpoint_id:
                return checkpoint
        return None

    def rollback_to_checkpoint(self, checkpoint_id: int) -> bool:
        """
        回滚到指定检查点

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            是否成功回滚
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            return False

        # 截断消息到检查点时的数量
        self.messages = self.messages[: checkpoint.message_count]

        # 移除检查点之后的所有检查点
        self.checkpoints = [c for c in self.checkpoints if c.id <= checkpoint_id]

        return True

    def rollback_last_checkpoint(self) -> bool:
        """
        回滚到上一个检查点

        Returns:
            是否成功回滚
        """
        if not self.checkpoints:
            return False

        # 回滚到倒数第二个检查点
        if len(self.checkpoints) >= 2:
            return self.rollback_to_checkpoint(self.checkpoints[-2].id)
        elif len(self.checkpoints) == 1:
            # 只有一个检查点，回滚到空状态
            self.messages.clear()
            self.checkpoints.clear()
            self._next_checkpoint_id = 0
            return True

        return False

    def list_checkpoints(self) -> list[Checkpoint]:
        """
        列出所有检查点

        Returns:
            检查点列表
        """
        return self.checkpoints.copy()

    def compact(self, keep_last_n: int = 10) -> int:
        """
        压缩上下文，只保留最近 N 条消息

        Args:
            keep_last_n: 保留的消息数量

        Returns:
            删除的消息数量
        """
        if len(self.messages) <= keep_last_n:
            return 0

        removed_count = len(self.messages) - keep_last_n
        self.messages = self.messages[-keep_last_n:]

        # 清理无效的检查点
        self.checkpoints = [
            c for c in self.checkpoints if c.message_count <= keep_last_n
        ]

        return removed_count

    def estimate_tokens(self) -> int:
        """
        估算当前上下文的 token 数量

        Returns:
            估算的 token 数
        """
        return self._total_tokens

    def to_langchain_messages(self) -> list:
        """
        转换为 LangChain 消息格式

        Returns:
            LangChain 消息列表
        """
        return [msg.to_langchain() for msg in self.messages]

    def __len__(self) -> int:
        """获取消息数量"""
        return len(self.messages)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ContextManager(session_id={self.session_id[:8]}..., messages={len(self.messages)}, checkpoints={len(self.checkpoints)})"


__all__ = [
    "ContextManager",
]
