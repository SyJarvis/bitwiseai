# -*- coding: utf-8 -*-
"""
文件存储后端

提供上下文的文件持久化功能
"""
import asyncio
import json
from pathlib import Path
from typing import Any
import os
from datetime import datetime


class FileStorage:
    """
    文件存储后端

    将上下文数据保存到 ~/.bitwiseai/sessions/ 目录
    """

    def __init__(self, base_dir: Path | None = None):
        """
        初始化文件存储

        Args:
            base_dir: 基础目录，默认为 ~/.bitwiseai/
        """
        if base_dir is None:
            # 默认使用 ~/.bitwiseai/
            home = Path.home()
            self.base_dir = home / ".bitwiseai" / "sessions"
        else:
            self.base_dir = Path(base_dir)

        # 确保目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.session_id: str | None = None
        """当前会话 ID"""

        self.context_file: Path | None = None
        """上下文文件路径"""

        self._lock = asyncio.Lock()
        """异步锁，防止并发写入"""

    def set_session_id(self, session_id: str) -> None:
        """
        设置会话 ID

        Args:
            session_id: 会话 ID
        """
        self.session_id = session_id
        self.context_file = self.base_dir / f"{session_id}.jsonl"

    async def initialize(self) -> None:
        """
        初始化存储

        确保目录和文件存在
        """
        if self.context_file is None:
            raise RuntimeError("Session ID not set. Call set_session_id() first.")

        # 确保文件存在
        if not self.context_file.exists():
            self.context_file.touch()

    async def load(self) -> dict[str, Any] | None:
        """
        从文件加载上下文数据

        Returns:
            加载的数据字典，如果文件为空或不存在则返回 None
        """
        if self.context_file is None or not self.context_file.exists():
            return None

        # 检查文件大小
        if self.context_file.stat().st_size == 0:
            return None

        async with self._lock:
            try:
                data = {
                    "messages": [],
                    "checkpoints": [],
                    "next_checkpoint_id": 0,
                    "total_tokens": 0,
                    "created_at": datetime.now().timestamp(),
                    "updated_at": datetime.now().timestamp(),
                }

                def load_from_file():
                    result = {
                        "messages": [],
                        "checkpoints": [],
                        "next_checkpoint_id": 0,
                        "total_tokens": 0,
                        "created_at": datetime.now().timestamp(),
                        "updated_at": datetime.now().timestamp(),
                    }
                    with open(self.context_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue

                            try:
                                item = json.loads(line)
                                item_type = item.get("type")

                                if item_type == "message":
                                    result["messages"].append(item["data"])
                                elif item_type == "checkpoint":
                                    result["checkpoints"].append(item["data"])
                                elif item_type == "metadata":
                                    # 元数据更新
                                    result.update(item.get("data", {}))
                                elif item_type == "next_checkpoint_id":
                                    result["next_checkpoint_id"] = item["value"]
                                elif item_type == "total_tokens":
                                    result["total_tokens"] = item["value"]
                                elif item_type == "created_at":
                                    result["created_at"] = item["value"]
                                elif item_type == "updated_at":
                                    result["updated_at"] = item["value"]

                            except json.JSONDecodeError:
                                continue
                    return result

                data = await asyncio.to_thread(load_from_file)
                return data

            except Exception as e:
                # 加载失败，返回 None
                print(f"Warning: Failed to load context: {e}")
                return None

    async def save(
        self,
        messages: list[dict],
        checkpoints: list[dict],
        next_checkpoint_id: int,
        total_tokens: int,
        created_at: float,
        updated_at: float,
    ) -> None:
        """
        保存上下文数据到文件

        Args:
            messages: 消息列表
            checkpoints: 检查点列表
            next_checkpoint_id: 下一个检查点 ID
            total_tokens: 总 token 数
            created_at: 创建时间
            updated_at: 更新时间
        """
        if self.context_file is None:
            raise RuntimeError("Session ID not set. Call set_session_id() first.")

        async with self._lock:
            # 写入临时文件
            temp_file = self.context_file.with_suffix(".tmp")

            # 正确使用 asyncio.to_thread 进行文件操作
            def write_context_file():
                with open(temp_file, "w", encoding="utf-8") as f:
                    # 写入元数据
                    f.write(
                        json.dumps({
                            "type": "metadata",
                            "data": {
                                "session_id": self.session_id,
                                "created_at": created_at,
                                "updated_at": updated_at,
                            }
                        })
                        + "\n"
                    )

                    # 写入消息
                    for msg in messages:
                        f.write(json.dumps({"type": "message", "data": msg}) + "\n")

                    # 写入检查点
                    for cp in checkpoints:
                        f.write(json.dumps({"type": "checkpoint", "data": cp}) + "\n")

                    # 写入状态
                    f.write(json.dumps({"type": "next_checkpoint_id", "value": next_checkpoint_id}) + "\n")
                    f.write(json.dumps({"type": "total_tokens", "value": total_tokens}) + "\n")
                    f.write(json.dumps({"type": "updated_at", "value": updated_at}) + "\n")

            # 执行文件写入
            await asyncio.to_thread(write_context_file)

            # 原子性替换
            await asyncio.to_thread(temp_file.replace, self.context_file)

    async def append_message(self, message: dict) -> None:
        """
        追加单条消息到文件

        Args:
            message: 消息数据
        """
        if self.context_file is None:
            raise RuntimeError("Session ID not set. Call set_session_id() first.")

        async with self._lock:
            def append_to_file():
                with open(self.context_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"type": "message", "data": message}) + "\n")

            await asyncio.to_thread(append_to_file)

    async def append_checkpoint(self, checkpoint: dict) -> None:
        """
        追加检查点到文件

        Args:
            checkpoint: 检查点数据
        """
        if self.context_file is None:
            raise RuntimeError("Session ID not set. Call set_session_id() first.")

        async with self._lock:
            def append_to_file():
                with open(self.context_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"type": "checkpoint", "data": checkpoint}) + "\n")

            await asyncio.to_thread(append_to_file)

    async def clear(self) -> None:
        """清空上下文文件"""
        if self.context_file is None:
            return

        async with self._lock:
            if self.context_file.exists():
                # 备份旧文件
                backup_file = self._get_backup_path()
                await asyncio.to_thread(self.context_file.rename, backup_file)

            # 创建新文件
            self.context_file.touch()

    async def delete(self) -> None:
        """删除上下文文件"""
        if self.context_file is None:
            return

        async with self._lock:
            if self.context_file.exists():
                # 先备份
                backup_file = self._get_backup_path()
                await asyncio.to_thread(self.context_file.rename, backup_file)

    def _get_backup_path(self) -> Path:
        """
        获取备份文件路径

        Returns:
            备份文件路径
        """
        if self.context_file is None:
            raise RuntimeError("Session ID not set.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.context_file.with_suffix(f".backup.{timestamp}")

    @classmethod
    def list_sessions(cls, base_dir: Path | None = None) -> list[dict]:
        """
        列出所有会话

        Args:
            base_dir: 基础目录

        Returns:
            会话信息列表
        """
        if base_dir is None:
            home = Path.home()
            sessions_dir = home / ".bitwiseai" / "sessions"
        else:
            sessions_dir = Path(base_dir)

        if not sessions_dir.exists():
            return []

        sessions = []

        for file_path in sessions_dir.glob("*.jsonl"):
            try:
                stat = file_path.stat()
                session_id = file_path.stem

                # 读取第一行获取元数据
                metadata = {}
                with open(file_path, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if first_line:
                        try:
                            data = json.loads(first_line)
                            if data.get("type") == "metadata":
                                metadata = data.get("data", {})
                        except json.JSONDecodeError:
                            pass

                sessions.append({
                    "session_id": session_id,
                    "file_path": str(file_path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                })

            except Exception:
                continue

        # 按修改时间排序
        sessions.sort(key=lambda s: s.get("modified", 0), reverse=True)

        return sessions

    @classmethod
    async def delete_session(cls, session_id: str, base_dir: Path | None = None) -> bool:
        """
        删除指定会话

        Args:
            session_id: 会话 ID
            base_dir: 基础目录

        Returns:
            是否成功删除
        """
        if base_dir is None:
            home = Path.home()
            sessions_dir = home / ".bitwiseai" / "sessions"
        else:
            sessions_dir = Path(base_dir)

        session_file = sessions_dir / f"{session_id}.jsonl"

        if not session_file.exists():
            return False

        try:
            # 备份后删除
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = session_file.with_suffix(f".backup.{timestamp}")
            await asyncio.to_thread(session_file.rename, backup_file)
            return True
        except Exception:
            return False


__all__ = [
    "FileStorage",
]
