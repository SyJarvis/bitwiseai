# -*- coding: utf-8 -*-
"""
Milvus 向量数据库

本地 Milvus 向量数据库实现
"""
import os
from typing import List, Optional

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
        """创建集合"""
        if self.client.has_collection(self.collection_name):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            dimension=self.embedding_dim,
            metric_type="IP",
            consistency_level="Strong"
        )
        print(f"✓ 集合 '{self.collection_name}' 已创建")

    def add_texts(self, texts: List[str]) -> int:
        """
        添加文本到向量数据库

        Args:
            texts: 文本列表

        Returns:
            插入的文本数量
        """
        if not texts:
            return 0

        # 生成嵌入
        vectors = self.embedding_model.embed_documents(texts)

        # 准备数据
        data = []
        for i, (text, vector) in enumerate(zip(texts, vectors)):
            data.append({
                "id": i,
                "vector": vector,
                "text": text
            })

        # 插入数据
        insert_res = self.client.insert(
            collection_name=self.collection_name,
            data=data
        )

        # 持久化
        try:
            self.client.flush()
        except Exception:
            pass

        return insert_res["insert_count"]

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> str:
        """
        搜索相似文本

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索到的文本内容（用换行符连接）
        """
        # 生成查询向量
        query_vector = self.embedding_model.embed_text(query)

        # 搜索
        search_res = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=top_k,
            output_fields=["text"]
        )

        # 解析结果
        if not search_res or not search_res[0]:
            return ""

        contexts = []
        for res in search_res[0]:
            text = res["entity"]["text"]
            contexts.append(text)

        return "\n".join(contexts)

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
