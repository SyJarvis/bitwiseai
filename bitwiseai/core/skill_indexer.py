# -*- coding: utf-8 -*-
"""
Skill 索引器

将技能索引到向量数据库，支持技能语义搜索
"""
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from ..vector_database import MilvusDB


class SkillIndexer:
    """
    技能索引器
    
    负责将技能元数据和内容索引到向量数据库，支持语义搜索
    """
    
    def __init__(
        self,
        vector_db: MilvusDB,
        collection_name: str = "bitwiseai_skills",
        embedding_dim: Optional[int] = None
    ):
        """
        初始化技能索引器
        
        Args:
            vector_db: Milvus 向量数据库实例
            collection_name: 技能索引集合名称
            embedding_dim: 向量维度（如果为 None，使用 vector_db 的维度）
        """
        self.vector_db = vector_db
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim or vector_db.embedding_dim
        
        # 创建技能索引集合（如果不存在）
        self._ensure_collection()
    
    def _ensure_collection(self):
        """确保技能索引集合存在"""
        # 检查集合是否存在
        if not self.vector_db.client.has_collection(self.collection_name):
            # 创建集合（使用 MilvusClient 的简化 API，支持动态字段）
            try:
                self.vector_db.client.create_collection(
                    collection_name=self.collection_name,
                    dimension=self.embedding_dim,
                    metric_type="IP",
                    consistency_level="Strong",
                    enable_dynamic_field=True  # 启用动态字段以支持元数据
                )
                print(f"✓ 技能索引集合 '{self.collection_name}' 已创建")
            except Exception as e:
                print(f"⚠️  创建技能索引集合失败: {e}")
                # 尝试使用基本方式
                try:
                    self.vector_db.client.create_collection(
                        collection_name=self.collection_name,
                        dimension=self.embedding_dim,
                        metric_type="IP",
                        consistency_level="Strong"
                    )
                    print(f"✓ 技能索引集合 '{self.collection_name}' 已创建（基本模式）")
                except Exception as e2:
                    print(f"❌ 创建技能索引集合失败: {e2}")
    
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
        
        # 组合索引文本：name + description + content_summary
        parts = [name, description]
        if content_summary:
            parts.append(content_summary)
        
        return "\n".join(parts)
    
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
            
            # 生成向量
            embedding = self.vector_db.embedding_model.embed_text(index_text)
            
            # 准备数据（使用动态字段存储元数据）
            # 注意：MilvusClient 使用 id 作为主键，但需要是整数
            # 我们使用 skill_name 的哈希值作为 id
            import hashlib
            skill_id = int(hashlib.md5(skill_name.encode()).hexdigest()[:8], 16)
            
            data = {
                "id": skill_id,
                "vector": embedding,
                "text": index_text,  # 主要文本字段
                "skill_name": skill_name,
                "description": skill_metadata.get("description", ""),
                "content_summary": content_summary[:2000],  # 限制长度
                "path": skill_path
            }
            
            # 插入或更新数据
            # 先删除旧数据（如果存在）
            try:
                self.vector_db.client.delete(
                    collection_name=self.collection_name,
                    filter=f'skill_name == "{skill_name}"'
                )
            except Exception:
                pass  # 如果删除失败（可能不存在），继续插入
            
            # 插入新数据
            self.vector_db.client.insert(
                collection_name=self.collection_name,
                data=[data]
            )
            
            # 持久化
            try:
                self.vector_db.client.flush()
            except Exception:
                pass
            
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
            # 生成查询向量
            query_vector = self.vector_db.embedding_model.embed_text(query)
            
            # 搜索
            results = self.vector_db.client.search(
                collection_name=self.collection_name,
                data=[query_vector],
                limit=top_k,
                output_fields=["skill_name", "description", "path", "content_summary"]
            )
            
            # 格式化结果
            skills = []
            if results and len(results) > 0:
                for hit in results[0]:
                    # 兼容不同的返回格式
                    entity = hit.get("entity", hit)
                    skills.append({
                        "skill_name": entity.get("skill_name", ""),
                        "description": entity.get("description", ""),
                        "path": entity.get("path", ""),
                        "content_summary": entity.get("content_summary", ""),
                        "score": hit.get("distance", hit.get("score", 0.0))
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
            self.vector_db.client.delete(
                collection_name=self.collection_name,
                filter=f'skill_name == "{skill_name}"'
            )
            return True
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
        return self.index_skill(skill_name, skill_metadata, skill_path, content_summary)


__all__ = ["SkillIndexer"]

