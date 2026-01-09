# -*- coding: utf-8 -*-
"""
LLM 模型封装

基于 LangChain ChatOpenAI
"""
from langchain_openai import ChatOpenAI


class LLM:
    """
    LLM 模型封装

    基于 LangChain 的 ChatOpenAI，支持自定义 API 地址
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str = None,
        base_url: str = None,
        temperature: float = 0.7
    ):
        """
        初始化 LLM 模型

        Args:
            model: 模型名称
            api_key: API 密钥
            base_url: API 基础地址
            temperature: 温度参数
        """
        self.model = model
        self.temperature = temperature

        # 创建 LangChain ChatOpenAI 实例
        self.client = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature
        )

    def invoke(self, message: str) -> str:
        """
        调用 LLM 生成回答

        Args:
            message: 输入消息

        Returns:
            LLM 生成的回答
        """
        response = self.client.invoke(message)
        return response.content


__all__ = ["LLM"]
