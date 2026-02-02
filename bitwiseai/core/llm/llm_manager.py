# -*- coding: utf-8 -*-
"""
LLM 管理器

统一的 LLM 接口，支持多提供商和流式传输
"""
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterator, Optional, Union

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

# 支持的提供商
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None


class LLMProvider(str, Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    CUSTOM = "custom"


@dataclass(slots=True)
class LLMConfig:
    """LLM 配置"""
    provider: LLMProvider = LLMProvider.OPENAI
    """提供商"""

    model: str = "gpt-4o-mini"
    """模型名称"""

    api_key: str | None = None
    """API 密钥"""

    base_url: str | None = None
    """API 基础地址"""

    temperature: float = 0.7
    """温度参数"""

    max_tokens: int | None = None
    """最大 token 数"""

    streaming: bool = True
    """是否启用流式传输"""

    kwargs: dict[str, Any] = field(default_factory=dict)
    """额外参数"""


class LLMManager:
    """
    LLM 管理器

    提供统一的 LLM 接口，支持：
    - 多提供商切换
    - 流式传输
    - 上下文管理
    """

    def __init__(self, config: LLMConfig | None = None):
        """
        初始化 LLM 管理器

        Args:
            config: LLM 配置
        """
        self.config = config or LLMConfig()
        self._client: BaseChatModel | None = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """初始化 LLM 客户端"""
        # 从环境变量获取 API 密钥
        api_key = self.config.api_key
        if api_key is None:
            api_key = self._get_default_api_key()

        match self.config.provider:
            case LLMProvider.OPENAI:
                if ChatOpenAI is None:
                    raise ImportError("langchain-openai is not installed")
                self._client = ChatOpenAI(
                    model=self.config.model,
                    api_key=api_key,
                    base_url=self.config.base_url,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    streaming=self.config.streaming,
                    **self.config.kwargs,
                )

            case LLMProvider.ANTHROPIC:
                if ChatAnthropic is None:
                    raise ImportError("langchain-anthropic is not installed")
                self._client = ChatAnthropic(
                    model=self.config.model,
                    api_key=api_key,
                    base_url=self.config.base_url,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    streaming=self.config.streaming,
                    **self.config.kwargs,
                )

            case LLMProvider.GOOGLE:
                if ChatGoogleGenerativeAI is None:
                    raise ImportError("langchain-google-genai is not installed")
                self._client = ChatGoogleGenerativeAI(
                    model=self.config.model,
                    api_key=api_key,
                    temperature=self.config.temperature,
                    **self.config.kwargs,
                )

            case LLMProvider.OLLAMA:
                if ChatOllama is None:
                    raise ImportError("langchain-ollama is not installed")
                self._client = ChatOllama(
                    model=self.config.model,
                    base_url=self.config.base_url,
                    temperature=self.config.temperature,
                    **self.config.kwargs,
                )

            case LLMProvider.CUSTOM:
                # 自定义端点，使用 OpenAI 兼容接口
                if ChatOpenAI is None:
                    raise ImportError("langchain-openai is required for custom endpoints")
                self._client = ChatOpenAI(
                    model=self.config.model,
                    api_key=api_key or "dummy",  # 某些端点不需要 API 密钥
                    base_url=self.config.base_url,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    streaming=self.config.streaming,
                    **self.config.kwargs,
                )

    def _get_default_api_key(self) -> str | None:
        """从环境变量获取默认 API 密钥"""
        match self.config.provider:
            case LLMProvider.OPENAI | LLMProvider.CUSTOM:
                return os.getenv("OPENAI_API_KEY")
            case LLMProvider.ANTHROPIC:
                return os.getenv("ANTHROPIC_API_KEY")
            case LLMProvider.GOOGLE:
                return os.getenv("GOOGLE_API_KEY")
            case LLMProvider.OLLAMA:
                return None  # Ollama 不需要 API 密钥
            case _:
                return None

    @property
    def client(self) -> BaseChatModel:
        """获取 LLM 客户端"""
        if self._client is None:
            raise RuntimeError("LLM client not initialized")
        return self._client

    @property
    def model_name(self) -> str:
        """获取模型名称"""
        return self.config.model

    def invoke(
        self,
        messages: Union[str, BaseMessage, list[BaseMessage]],
        system_prompt: str | None = None,
    ) -> str:
        """
        调用 LLM（非流式）

        Args:
            messages: 输入消息
            system_prompt: 系统提示词（可选）

        Returns:
            LLM 生成的回答
        """
        prepared_messages = self._prepare_messages(messages, system_prompt)
        response = self.client.invoke(prepared_messages)

        if isinstance(response, AIMessage):
            return response.content or ""
        return str(response)

    def stream(
        self,
        messages: Union[str, BaseMessage, list[BaseMessage]],
        system_prompt: str | None = None,
        callback: Callable[[str], None] | None = None,
    ) -> Iterator[str]:
        """
        流式调用 LLM

        Args:
            messages: 输入消息
            system_prompt: 系统提示词（可选）
            callback: 每个 token 的回调函数

        Yields:
            每个 token 的字符串片段
        """
        prepared_messages = self._prepare_messages(messages, system_prompt)

        for chunk in self.client.stream(prepared_messages):
            content = ""

            if hasattr(chunk, "content"):
                content = chunk.content or ""
            elif isinstance(chunk, str):
                content = chunk
            elif hasattr(chunk, "delta"):
                # 某些提供商使用 delta
                delta = getattr(chunk, "delta", {})
                content = delta.get("content", "")

            if content:
                if callback:
                    callback(content)
                yield content

    def stream_with_callback(
        self,
        messages: Union[str, BaseMessage, list[BaseMessage]],
        callback: Callable[[str], None],
        system_prompt: str | None = None,
    ) -> str:
        """
        流式调用 LLM（回调方式）

        Args:
            messages: 输入消息
            callback: 每个 token 的回调函数
            system_prompt: 系统提示词（可选）

        Returns:
            完整的回答内容
        """
        full_content = ""

        for token in self.stream(messages, system_prompt, callback):
            full_content += token

        return full_content

    async def astream(
        self,
        messages: Union[str, BaseMessage, list[BaseMessage]],
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """
        异步流式调用 LLM

        Args:
            messages: 输入消息
            system_prompt: 系统提示词（可选）

        Yields:
            每个 token 的字符串片段
        """
        prepared_messages = self._prepare_messages(messages, system_prompt)

        async for chunk in self.client.astream(prepared_messages):
            content = ""

            if hasattr(chunk, "content"):
                content = chunk.content or ""
            elif isinstance(chunk, str):
                content = chunk
            elif hasattr(chunk, "delta"):
                delta = getattr(chunk, "delta", {})
                content = delta.get("content", "")

            if content:
                yield content

    def _prepare_messages(
        self,
        messages: Union[str, BaseMessage, list[BaseMessage]],
        system_prompt: str | None = None,
    ) -> list[BaseMessage]:
        """
        准备消息格式

        Args:
            messages: 输入消息
            system_prompt: 系统提示词

        Returns:
            消息列表
        """
        if isinstance(messages, str):
            result = [HumanMessage(content=messages)]
        elif isinstance(messages, BaseMessage):
            result = [messages]
        elif isinstance(messages, list):
            if all(isinstance(m, str) for m in messages):
                result = [HumanMessage(content=m) for m in messages]
            else:
                result = messages
        else:
            raise ValueError(f"Unsupported message type: {type(messages)}")

        # 添加系统提示词
        if system_prompt:
            result = [SystemMessage(content=system_prompt)] + result

        return result

    def bind_tools(self, tools: list) -> "LLMManager":
        """
        绑定工具到 LLM

        Args:
            tools: 工具列表

        Returns:
            自身（支持链式调用）
        """
        if hasattr(self._client, "bind_tools"):
            self._client = self._client.bind_tools(tools)
        return self

    def with_config(self, **kwargs) -> "LLMManager":
        """
        更新配置

        Args:
            **kwargs: 配置参数

        Returns:
            新的 LLM 管理器实例
        """
        new_config = LLMConfig(
            provider=self.config.provider,
            model=kwargs.get("model", self.config.model),
            api_key=kwargs.get("api_key", self.config.api_key),
            base_url=kwargs.get("base_url", self.config.base_url),
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            streaming=kwargs.get("streaming", self.config.streaming),
            kwargs=kwargs,
        )

        return LLMManager(new_config)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"LLMManager(provider={self.config.provider.value}, model={self.config.model})"


__all__ = [
    "LLMProvider",
    "LLMConfig",
    "LLMManager",
]
