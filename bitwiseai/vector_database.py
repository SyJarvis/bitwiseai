# -*- coding: utf-8 -*-
"""
Milvus 向量数据库

本地 Milvus 向量数据库实现
"""
import os
import time
import hashlib
from typing import List, Optional, Dict, Any

try:
    from pymilvus import MilvusClient
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False


class MilvusDB:
    """
    Milvus 向量数据库

    基于 pymilvus 的本地文件模式
    """

    def __init__(
        self,
        db_file: str,
        embedding_model,
        collection_name: str = "polarisrag",
        embedding_dim: int = 1024
    ):
        """
        初始化 Milvus 数据库

        Args:
            db_file: 数据库文件路径
            embedding_model: 嵌入模型
            collection_name: 集合名称
            embedding_dim: 向量维度
        """
        if not MILVUS_AVAILABLE:
            raise ImportError("请安装 pymilvus: pip install pymilvus")

        self.db_file = db_file
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim

        # 确保目录存在
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        # 初始化客户端
        self.client = MilvusClient(uri=db_file)

        # 创建集合
        self._create_collection()

    def _create_collection(self):
        """创建集合（支持元数据字段）"""
        if self.client.has_collection(self.collection_name):
            # 检查现有集合的schema，如果缺少元数据字段，需要迁移
            return

        # MilvusClient的简化API：使用create_collection，支持动态字段
        # 通过enable_dynamic_field=True，可以自动处理额外的元数据字段
        # auto_id 默认为 True，不需要手动设置
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                dimension=self.embedding_dim,
                metric_type="IP",
                consistency_level="Strong",
                enable_dynamic_field=True  # 启用动态字段以支持元数据
            )
            print(f"✓ 集合 '{self.collection_name}' 已创建（支持元数据）")
        except Exception as e:
            # 如果创建失败，尝试使用基本方式（向后兼容）
            print(f"⚠️  创建集合时出错: {e}，尝试使用基本方式")
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    dimension=self.embedding_dim,
                    metric_type="IP",
                    consistency_level="Strong"
                )
                print(f"✓ 集合 '{self.collection_name}' 已创建（基本模式）")
            except Exception as e2:
                print(f"❌ 创建集合失败: {e2}")

    def add_texts(self, texts: List[str]) -> int:
        """
        添加文本到向量数据库（兼容旧接口）

        Args:
            texts: 文本列表

        Returns:
            插入的文本数量
        """
        if not texts:
            return 0

        # 生成嵌入
        vectors = self.embedding_model.embed_documents(texts)

        # 准备数据（使用默认元数据）
        metadata = []
        current_time = time.time()
        for i, text in enumerate(texts):
            metadata.append({
                "source_file": "",
                "file_hash": "",
                "chunk_index": i,
                "chunk_total": len(texts),
                "timestamp": current_time,
                "text_length": len(text)
            })

        return self.add_texts_with_metadata(texts, metadata)

    def add_texts_with_metadata(self, texts: List[str], metadata: List[Dict[str, Any]]) -> int:
        """
        添加文本到向量数据库（带元数据）

        Args:
            texts: 文本列表
            metadata: 元数据列表，每个元素包含：
                - source_file: 源文件路径
                - file_hash: 文件哈希值
                - chunk_index: 切分块索引
                - chunk_total: 总切分块数
                - timestamp: 时间戳
                - text_length: 文本长度

        Returns:
            插入的文本数量
        """
        if not texts:
            return 0

        if len(texts) != len(metadata):
            raise ValueError("文本列表和元数据列表长度必须一致")

        # 生成嵌入
        vectors = self.embedding_model.embed_documents(texts)

        # 准备数据
        # 注意：如果集合没有设置 auto_id，需要手动生成 id
        data = []
        import random
        base_id = int(time.time() * 1000)  # 使用时间戳作为基础ID
        
        for idx, (text, vector, meta) in enumerate(zip(texts, vectors, metadata)):
            # 生成唯一ID（时间戳 + 索引 + 随机数）
            doc_id = base_id + idx * 1000 + random.randint(0, 999)
            
            data.append({
                "id": doc_id,  # 手动生成ID
                "vector": vector,
                "text": text,
                "source_file": meta.get("source_file", ""),
                "file_hash": meta.get("file_hash", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "chunk_total": meta.get("chunk_total", 1),
                "timestamp": meta.get("timestamp", time.time()),
                "text_length": meta.get("text_length", len(text))
            })

        # 插入数据
        try:
            insert_res = self.client.insert(
                collection_name=self.collection_name,
                data=data
            )

            # 持久化
            try:
                self.client.flush()
            except Exception:
                pass

            return insert_res.get("insert_count", len(texts))
        except Exception as e:
            print(f"⚠️  插入数据失败: {e}")
            return 0

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> str:
        """
        搜索相似文本（兼容旧接口）

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索到的文本内容（用换行符连接）
        """
        results = self.search_with_metadata(query, top_k)
        return "\n".join([r["text"] for r in results])

    def search_with_metadata(
        self,
        query: str,
        top_k: int = 5,
        output_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文本（返回元数据）

        Args:
            query: 查询文本
            top_k: 返回结果数量
            output_fields: 需要返回的字段列表，默认返回所有字段

        Returns:
            检索结果列表，每个元素包含text和元数据
        """
        # 生成查询向量
        query_vector = self.embedding_model.embed_text(query)

        # 设置输出字段
        if output_fields is None:
            output_fields = ["text", "source_file", "file_hash", "chunk_index", "chunk_total", "timestamp"]

        # 搜索
        try:
            search_res = self.client.search(
                collection_name=self.collection_name,
                data=[query_vector],
                limit=top_k,
                output_fields=output_fields
            )

            # 解析结果
            if not search_res or not search_res[0]:
                return []

            results = []
            for res in search_res[0]:
                # 兼容不同的返回格式
                # pymilvus可能返回 {"entity": {...}} 或直接返回字段
                if isinstance(res, dict):
                    entity = res.get("entity", res)  # 如果没有entity字段，直接使用res
                    result = {
                        "text": entity.get("text", ""),
                        "score": res.get("distance", res.get("score", 0.0)),
                        "source_file": entity.get("source_file", ""),
                        "file_hash": entity.get("file_hash", ""),
                        "chunk_index": entity.get("chunk_index", 0),
                        "chunk_total": entity.get("chunk_total", 1),
                        "timestamp": entity.get("timestamp", 0.0)
                    }
                    results.append(result)

            return results
        except Exception as e:
            print(f"⚠️  搜索失败: {e}")
            return []

    def search_similar_vectors(
        self,
        vectors: List[List[float]],
        threshold: float = 0.85,
        top_k: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        搜索相似向量（用于去重）

        Args:
            vectors: 查询向量列表
            threshold: 相似度阈值（余弦相似度）
            top_k: 每个向量返回的最大结果数

        Returns:
            每个查询向量的相似结果列表
        """
        if not vectors:
            return []

        try:
            # 在Milvus中搜索
            search_res = self.client.search(
                collection_name=self.collection_name,
                data=vectors,
                limit=top_k,
                output_fields=["text", "source_file", "file_hash", "chunk_index"]
            )

            # 转换IP距离为余弦相似度
            # Milvus使用IP（内积），需要转换为相似度
            results = []
            for res_list in search_res:
                similar_items = []
                for res in res_list:
                    # IP距离转换为相似度（近似）
                    # 对于归一化向量，IP ≈ 余弦相似度
                    distance = res.get("distance", res.get("score", 0.0))
                    # 假设向量已归一化，IP值接近余弦相似度
                    # 如果向量未归一化，需要更复杂的转换
                    # IP metric: 值越大越相似，通常范围在[-1, 1]（归一化向量）
                    # 转换为[0, 1]范围的相似度
                    similarity = max(0.0, min(1.0, (distance + 1.0) / 2.0))  # 将[-1,1]映射到[0,1]
                    
                    if similarity >= threshold:
                        # 兼容不同的返回格式
                        entity = res.get("entity", res)
                        similar_items.append({
                            "text": entity.get("text", ""),
                            "score": similarity,
                            "source_file": entity.get("source_file", ""),
                            "file_hash": entity.get("file_hash", ""),
                            "chunk_index": entity.get("chunk_index", 0)
                        })
                results.append(similar_items)

            return results
        except Exception as e:
            print(f"⚠️  相似向量搜索失败: {e}")
            return [[] for _ in vectors]

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        use_keyword: bool = True,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        混合检索（向量搜索 + 关键词搜索）

        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_keyword: 是否使用关键词搜索
            vector_weight: 向量搜索权重
            keyword_weight: 关键词搜索权重

        Returns:
            合并后的检索结果列表
        """
        # 向量搜索
        vector_results = self.search_with_metadata(query, top_k=top_k * 2)

        if not use_keyword:
            return vector_results[:top_k]

        # 关键词搜索（简单实现：在文本中搜索关键词）
        keyword_results = self._keyword_search(query, top_k=top_k * 2)

        # 合并结果
        combined = self._merge_search_results(
            vector_results, keyword_results,
            vector_weight, keyword_weight
        )

        return combined[:top_k]

    def _keyword_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        关键词搜索（简单实现）

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        # 简单实现：获取所有文档，按关键词匹配度排序
        # 注意：对于大数据集，这需要优化（如使用倒排索引）
        try:
            # 获取所有文档（限制数量以避免性能问题）
            query_result = self.client.query(
                collection_name=self.collection_name,
                filter="",
                limit=min(1000, top_k * 20),  # 限制查询数量
                output_fields=["text", "source_file", "file_hash", "chunk_index", "chunk_total", "timestamp"]
            )

            if not query_result:
                return []

            # 计算关键词匹配分数
            query_words = set(query.lower().split())
            scored_results = []
            for item in query_result:
                text = item.get("text", "").lower()
                # 计算匹配的关键词数量
                matched_words = sum(1 for word in query_words if word in text)
                if matched_words > 0:
                    score = matched_words / len(query_words) if query_words else 0.0
                    scored_results.append({
                        "text": item.get("text", ""),
                        "score": score,
                        "source_file": item.get("source_file", ""),
                        "file_hash": item.get("file_hash", ""),
                        "chunk_index": item.get("chunk_index", 0),
                        "chunk_total": item.get("chunk_total", 1),
                        "timestamp": item.get("timestamp", 0.0)
                    })

            # 按分数排序
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            return scored_results[:top_k]
        except Exception as e:
            print(f"⚠️  关键词搜索失败: {e}")
            return []

    def _merge_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        合并向量搜索和关键词搜索结果

        Args:
            vector_results: 向量搜索结果
            keyword_results: 关键词搜索结果
            vector_weight: 向量搜索权重
            keyword_weight: 关键词搜索权重

        Returns:
            合并后的结果列表
        """
        # 创建文本到结果的映射
        combined_map = {}

        # 添加向量搜索结果
        for i, result in enumerate(vector_results):
            text = result["text"]
            if text not in combined_map:
                combined_map[text] = result.copy()
                combined_map[text]["combined_score"] = vector_weight * (1.0 - result.get("score", 0.0))
            else:
                # 如果已存在，更新分数
                combined_map[text]["combined_score"] += vector_weight * (1.0 - result.get("score", 0.0))

        # 添加关键词搜索结果
        for result in keyword_results:
            text = result["text"]
            if text not in combined_map:
                combined_map[text] = result.copy()
                combined_map[text]["combined_score"] = keyword_weight * result.get("score", 0.0)
            else:
                # 如果已存在，更新分数
                combined_map[text]["combined_score"] += keyword_weight * result.get("score", 0.0)

        # 转换为列表并按分数排序
        combined = list(combined_map.values())
        combined.sort(key=lambda x: x.get("combined_score", 0.0), reverse=True)

        return combined

    def clear(self):
        """
        清空集合
        """
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)
            self._create_collection()

    def count(self) -> int:
        """
        获取集合中的文档数量

        Returns:
            文档数量
        """
        if not self.client.has_collection(self.collection_name):
            return 0

        try:
            stats = self.client.get_collection_stats(self.collection_name)
            return stats.get("row_count", 0)
        except Exception:
            return 0


__all__ = ["MilvusDB"]
