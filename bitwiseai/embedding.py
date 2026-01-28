# -*- coding: utf-8 -*-
"""
Embedding 模型封装

基于 LangChain OpenAIEmbeddings
"""
from typing import List, Optional
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
        base_url: str = None,
        show_progress_bar: bool = False
    ):
        """
        初始化 Embedding 模型

        Args:
            model: 模型名称
            api_key: API 密钥
            base_url: API 基础地址
            show_progress_bar: 是否显示进度条（默认 False，不显示）
        """
        self.model = model

        # 创建 LangChain OpenAIEmbeddings 实例
        self.client = OpenAIEmbeddings(
            model=model,
            api_key=api_key,
            base_url=base_url,
            show_progress_bar=show_progress_bar
        )

    def embed_text(self, text: str) -> List[float]:
        """
        将单个文本转换为向量

        Args:
            text: 输入文本

        Returns:
            文本的向量表示
        """
        if not text or not text.strip():
            raise ValueError("输入文本不能为空")
        
        try:
            return self.client.embed_query(text)
        except Exception as e:
            error_msg = str(e)
            if "No embedding data received" in error_msg or "data" in error_msg.lower():
                base_url = getattr(self.client, 'openai_api_base', '未知')
                raise ValueError(
                    f"嵌入向量生成失败：API 未返回数据。\n"
                    f"请检查：\n"
                    f"  1) API 地址是否正确: {base_url}\n"
                    f"  2) API Key 是否有效\n"
                    f"  3) 模型名称是否正确: {self.model}\n"
                    f"  4) 网络连接是否正常"
                ) from e
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文本批量转换为向量

        Args:
            texts: 文本列表

        Returns:
            文本向量的列表
        """
        if not texts:
            return []
        
        # 过滤空文本
        non_empty_texts = [t for t in texts if t and t.strip()]
        if not non_empty_texts:
            return []
        
        try:
            return self.client.embed_documents(non_empty_texts)
        except Exception as e:
            error_msg = str(e)
            if "No embedding data received" in error_msg or "data" in error_msg.lower():
                base_url = getattr(self.client, 'openai_api_base', '未知')
                raise ValueError(
                    f"嵌入向量生成失败：API 未返回数据。\n"
                    f"请检查：\n"
                    f"  1) API 地址是否正确: {base_url}\n"
                    f"  2) API Key 是否有效\n"
                    f"  3) 模型名称是否正确: {self.model}\n"
                    f"  4) 文本数量是否过多（当前: {len(texts)} 个）\n"
                    f"  5) 网络连接是否正常"
                ) from e
            raise


__all__ = ["Embedding"]
