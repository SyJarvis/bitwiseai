# -*- coding: utf-8 -*-
"""
Embedding 模型封装

基于 LangChain OpenAIEmbeddings
"""
from typing import List
from langchain_openai import OpenAIEmbeddings


class Embedding:
    """
    Embedding 模型封装

    基于 LangChain 的 OpenAIEmbeddings，支持自定义 API 地址
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str = None,
        base_url: str = None
    ):
        """
        初始化 Embedding 模型

        Args:
            model: 模型名称
            api_key: API 密钥
            base_url: API 基础地址
        """
        self.model = model

        # 创建 LangChain OpenAIEmbeddings 实例
        self.client = OpenAIEmbeddings(
            model=model,
            api_key=api_key,
            base_url=base_url
        )

    def embed_text(self, text: str) -> List[float]:
        """
        将单个文本转换为向量

        Args:
            text: 输入文本

        Returns:
            文本的向量表示
        """
        return self.client.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文本批量转换为向量

        Args:
            texts: 文本列表

        Returns:
            文本向量的列表
        """
        return self.client.embed_documents(texts)


__all__ = ["Embedding"]
