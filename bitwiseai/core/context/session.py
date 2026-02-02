# -*- coding: utf-8 -*-
"""
会话管理器

管理多个会话的创建、切换和删除
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid

from .manager import ContextManager
from .storage import FileStorage


@dataclass(slots=True)
class SessionInfo:
    """会话信息"""
    session_id: str
    """会话 ID"""

    name: str
    """会话名称"""

    created_at: float
    """创建时间"""

    updated_at: float
    """更新时间"""

    message_count: int
    """消息数量"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """额外的元数据"""

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class Session:
    """会话"""
    info: SessionInfo
    """会话信息"""

    context: ContextManager
    """上下文管理器"""


class SessionManager:
    """
    会话管理器

    管理多个会话，支持：
    - 创建新会话
    - 切换会话
    - 列出所有会话
    - 删除会话
    """

    def __init__(self, base_dir: Path | None = None):
        """
        初始化会话管理器

        Args:
            base_dir: 会话存储基础目录
        """
        self.base_dir = base_dir
        self._sessions: dict[str, Session] = {}
        self._current_session_id: str | None = None

    @property
    def current_session(self) -> Session | None:
        """获取当前会话"""
        if self._current_session_id is None:
            return None
        return self._sessions.get(self._current_session_id)

    @property
    def current_context(self) -> ContextManager | None:
        """获取当前会话的上下文管理器"""
        session = self.current_session
        return session.context if session else None

    async def create_session(
        self,
        name: str | None = None,
        session_id: str | None = None,
    ) -> Session:
        """
        创建新会话

        Args:
            name: 会话名称
            session_id: 会话 ID（可选，默认自动生成）

        Returns:
            创建的会话
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        if name is None:
            name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # 创建上下文管理器
        storage = FileStorage(self.base_dir)
        context = ContextManager(session_id=session_id, storage=storage)
        await context.initialize()

        # 创建会话信息
        info = SessionInfo(
            session_id=session_id,
            name=name,
            created_at=datetime.now().timestamp(),
            updated_at=datetime.now().timestamp(),
            message_count=0,
        )

        # 创建会话
        session = Session(info=info, context=context)
        self._sessions[session_id] = session
        self._current_session_id = session_id

        # 保存会话
        await context.save()

        return session

    async def switch_session(self, session_id: str) -> Session | None:
        """
        切换到指定会话

        Args:
            session_id: 会话 ID

        Returns:
            切换后的会话，如果不存在则返回 None
        """
        # 如果会话已加载，直接切换
        if session_id in self._sessions:
            self._current_session_id = session_id
            return self._sessions[session_id]

        # 从文件加载会话
        storage = FileStorage(self.base_dir)
        storage.set_session_id(session_id)

        await storage.initialize()
        data = await storage.load()

        if data is None:
            return None

        # 创建上下文管理器
        context = ContextManager(session_id=session_id, storage=storage)

        # 恢复数据
        from .models import Message, Checkpoint
        context.messages = [Message.from_dict(m) for m in data.get("messages", [])]
        context.checkpoints = [Checkpoint.from_dict(c) for c in data.get("checkpoints", [])]
        context._next_checkpoint_id = data.get("next_checkpoint_id", 0)
        context._total_tokens = data.get("total_tokens", 0)
        context._created_at = data.get("created_at", datetime.now().timestamp())

        # 创建会话信息
        info = SessionInfo(
            session_id=session_id,
            name=f"Session {datetime.fromtimestamp(context._created_at).strftime('%Y-%m-%d %H:%M')}",
            created_at=context._created_at,
            updated_at=data.get("updated_at", datetime.now().timestamp()),
            message_count=len(context.messages),
        )

        # 创建并缓存会话
        session = Session(info=info, context=context)
        self._sessions[session_id] = session
        self._current_session_id = session_id

        return session

    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            是否成功删除
        """
        # 从内存移除
        if session_id in self._sessions:
            del self._sessions[session_id]

        # 如果删除的是当前会话，清空当前会话
        if self._current_session_id == session_id:
            self._current_session_id = None

        # 删除文件
        return await FileStorage.delete_session(session_id, self.base_dir)

    async def rename_session(self, session_id: str, new_name: str) -> bool:
        """
        重命名会话

        Args:
            session_id: 会话 ID
            new_name: 新名称

        Returns:
            是否成功
        """
        session = self._sessions.get(session_id)
        if session is None:
            return False

        session.info.name = new_name
        session.info.updated_at = datetime.now().timestamp()

        await session.context.save()
        return True

    def list_sessions(self) -> list[SessionInfo]:
        """
        列出所有会话

        Returns:
            会话信息列表
        """
        # 从存储加载所有会话
        all_sessions = FileStorage.list_sessions(self.base_dir)

        # 合并内存中的会话
        session_dict = {}

        # 添加存储中的会话
        for s in all_sessions:
            session_dict[s["session_id"]] = SessionInfo(
                session_id=s["session_id"],
                name=f"Session {datetime.fromtimestamp(s.get('modified', 0)).strftime('%Y-%m-%d %H:%M')}",
                created_at=s.get("created_at", datetime.now().timestamp()),
                updated_at=s.get("updated_at", datetime.now().timestamp()),
                message_count=0,  # 需要加载才能知道
            )

        # 更新内存中的会话信息
        for session in self._sessions.values():
            session_dict[session.info.session_id] = session.info

        return list(session_dict.values())

    async def get_or_create_current(self) -> Session:
        """
        获取当前会话，如果不存在则创建

        Returns:
            当前会话
        """
        if self.current_session is not None:
            return self.current_session

        # 创建新会话
        return await self.create_session()

    async def save_current(self) -> None:
        """保存当前会话"""
        if self.current_context is not None:
            await self.current_context.save()

    def __repr__(self) -> str:
        """字符串表示"""
        current = self._current_session_id[:8] + "..." if self._current_session_id else "None"
        return f"SessionManager(current={current}, total={len(self._sessions)})"


__all__ = [
    "SessionInfo",
    "Session",
    "SessionManager",
]
