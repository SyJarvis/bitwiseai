# -*- coding: utf-8 -*-
"""
Skill 索引器

将技能索引到记忆系统，支持技能语义搜索
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path


class SkillIndexer:
    """
    技能索引器

    负责将技能元数据和内容索引到记忆系统，支持语义搜索
    """

    def __init__(
        self,
        memory_manager,
        collection_name: str = "skills"
    ):
        """
        初始化技能索引器

        Args:
            memory_manager: MemoryManager 实例
            collection_name: 技能索引集合名称（保留参数用于兼容性）
        """
        from ..core.memory import MemoryManager

        if not isinstance(memory_manager, MemoryManager):
            raise TypeError("memory_manager must be an instance of MemoryManager")

        self.memory_manager = memory_manager
        self.collection_name = collection_name

    def _create_index_text(self, skill_metadata: Dict[str, Any], content_summary: str = "") -> str:
        """
        创建用于索引的文本内容

        Args:
            skill_metadata: 技能元数据
            content_summary: 内容摘要

        Returns:
            索引文本
        """
        name = skill_metadata.get("name", "")
        description = skill_metadata.get("description", "")
        tags = skill_metadata.get("tags", [])

        # 组合索引文本：name + description + tags + content_summary
        parts = [f"Skill: {name}"]
        if description:
            parts.append(f"Description: {description}")
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")
        if content_summary:
            parts.append(f"Content:\n{content_summary}")

        return "\n\n".join(parts)

    def index_skill(
        self,
        skill_name: str,
        skill_metadata: Dict[str, Any],
        skill_path: str,
        content_summary: str = ""
    ) -> bool:
        """
        索引单个技能

        Args:
            skill_name: 技能名称
            skill_metadata: 技能元数据
            skill_path: 技能路径
            content_summary: 内容摘要（SKILL.md 正文的前 500 字符）

        Returns:
            是否索引成功
        """
        try:
            # 创建索引文本
            index_text = self._create_index_text(skill_metadata, content_summary)

            # 准备元数据
            metadata = {
                "skill_name": skill_name,
                "description": skill_metadata.get("description", ""),
                "tags": skill_metadata.get("tags", []),
                "path": skill_path,
                "content_summary": content_summary[:2000]  # 限制长度
            }

            # 使用 MemoryManager 索引技能
            self.memory_manager.index_skill(
                skill_path=skill_path,
                skill_metadata=metadata,
                content=index_text
            )

            return True

        except Exception as e:
            print(f"⚠️  索引技能失败 {skill_name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def search_skills(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关技能

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            技能信息列表，每个元素包含：
            - skill_name: 技能名称
            - description: 技能描述
            - path: 技能路径
            - score: 相似度分数
        """
        try:
            # 使用 MemoryManager 搜索
            results = self.memory_manager.search_sync(
                query=query,
                max_results=top_k,
                source_filter=["skills"]
            )

            # 格式化结果
            skills = []
            for result in results:
                skills.append({
                    "skill_name": result.metadata.get("skill_name", ""),
                    "description": result.metadata.get("description", ""),
                    "path": result.metadata.get("path", result.path),
                    "content_summary": result.metadata.get("content_summary", ""),
                    "score": result.score
                })

            return skills

        except Exception as e:
            print(f"⚠️  搜索技能失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def remove_skill(self, skill_name: str) -> bool:
        """
        从索引中移除技能

        Args:
            skill_name: 技能名称

        Returns:
            是否移除成功
        """
        try:
            # 通过搜索找到技能路径
            results = self.memory_manager.search_sync(
                query=skill_name,
                max_results=1,
                source_filter=["skills"]
            )

            if results:
                # 移除索引
                self.memory_manager.remove_index(results[0].path)
                return True

            return False
        except Exception as e:
            print(f"⚠️  移除技能索引失败 {skill_name}: {e}")
            return False

    def update_index(self, skill_name: str, skill_metadata: Dict[str, Any], skill_path: str, content_summary: str = "") -> bool:
        """
        更新技能索引

        Args:
            skill_name: 技能名称
            skill_metadata: 技能元数据
            skill_path: 技能路径
            content_summary: 内容摘要

        Returns:
            是否更新成功
        """
        # 先移除旧索引
        self.remove_skill(skill_name)
        # 重新索引
        return self.index_skill(skill_name, skill_metadata, skill_path, content_summary)


__all__ = ["SkillIndexer"]
