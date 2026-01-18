# -*- coding: utf-8 -*-
"""
LLM 模型封装

基于 LangChain ChatOpenAI，支持流式输出
"""
from typing import Iterator, Callable, Optional, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage


class LLM:
    """
    LLM 模型封装

    基于 LangChain 的 ChatOpenAI，支持自定义 API 地址和流式输出
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

    def invoke(self, message: Union[str, BaseMessage, list]) -> str:
        """
        调用 LLM 生成回答（非流式）

        Args:
            message: 输入消息，可以是字符串、BaseMessage 或消息列表

        Returns:
            LLM 生成的回答
        """
        # 转换消息格式
        messages = self._prepare_messages(message)
        response = self.client.invoke(messages)
        return response.content

    def stream(self, message: Union[str, BaseMessage, list]) -> Iterator[str]:
        """
        流式调用 LLM（生成器方式）

        Args:
            message: 输入消息，可以是字符串、BaseMessage 或消息列表

        Yields:
            每个 token 的字符串片段
        """
        # 转换消息格式
        messages = self._prepare_messages(message)
        
        # 使用 LangChain 的 stream 方法
        for chunk in self.client.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
            elif isinstance(chunk, str):
                yield chunk

    def stream_with_callback(
        self,
        message: Union[str, BaseMessage, list],
        callback: Callable[[str], None]
    ) -> str:
        """
        流式调用 LLM（回调方式）

        Args:
            message: 输入消息，可以是字符串、BaseMessage 或消息列表
            callback: 回调函数，每个 token 都会调用 callback(token)

        Returns:
            完整的回答内容
        """
        full_content = ""
        
        for token in self.stream(message):
            full_content += token
            callback(token)
        
        return full_content

    def _prepare_messages(self, message: Union[str, BaseMessage, list]) -> list:
        """
        准备消息格式

        Args:
            message: 输入消息

        Returns:
            消息列表
        """
        if isinstance(message, str):
            return [HumanMessage(content=message)]
        elif isinstance(message, BaseMessage):
            return [message]
        elif isinstance(message, list):
            # 如果是字符串列表，转换为 HumanMessage
            if message and isinstance(message[0], str):
                return [HumanMessage(content=msg) for msg in message]
            return message
        else:
            raise ValueError(f"不支持的消息类型: {type(message)}")


__all__ = ["LLM"]
