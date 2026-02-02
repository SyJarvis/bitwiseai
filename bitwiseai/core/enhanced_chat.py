# -*- coding: utf-8 -*-
"""
增强版聊天引擎

整合上下文管理、会话管理、LLM 集成、Slash 命令、Flow 系统和 Agent 循环
"""
import asyncio
from typing import Any, Callable, Iterator, Optional, Union
from pathlib import Path

from .context import (
    ContextManager,
    Message,
    MessageRole,
    Session,
    SessionManager,
)
from .llm import LLMConfig, LLMManager, LLMProvider
from .slash import SlashCommandRegistry, parse_slash_command_call
from .flow import create_ralph_flow, FlowRunner, RalphLoopConfig
from .agent import (
    Agent,
    AgentConfig,
    AgentLoop,
    AgentSpec,
    LoopConfig,
    MultiAgentOrchestrator,
)
from .rag_engine import RAGEngine
from .skill_manager import SkillManager


class EnhancedChatEngine:
    """
    增强版聊天引擎

    整合所有功能：
    - 上下文管理和持久化
    - 会话管理
    - 多提供商 LLM 支持
    - 流式传输
    - 检查点和回滚
    - Slash 命令
    - Ralph Loop
    """

    def __init__(
        self,
        llm_config: LLMConfig | None = None,
        rag_engine: Optional[RAGEngine] = None,
        skill_manager: Optional[SkillManager] = None,
        system_prompt: str = "",
        data_dir: Optional[Path] = None,
        enable_slash: bool = True,
        enable_ralph_loop: bool = True,
        ralph_max_iterations: int = 10,
        auto_save: bool = True,
    ):
        """
        初始化增强版聊天引擎

        Args:
            llm_config: LLM 配置
            rag_engine: RAG 引擎（可选）
            skill_manager: Skill 管理器（可选）
            system_prompt: 系统提示词
            data_dir: 数据存储目录
            enable_slash: 是否启用 Slash 命令
            enable_ralph_loop: 是否启用 Ralph Loop
            ralph_max_iterations: Ralph Loop 最大迭代次数
            auto_save: 是否自动保存
        """
        # LLM 管理
        self.llm = LLMManager(llm_config or LLMConfig())
        self.rag_engine = rag_engine
        self.skill_manager = skill_manager
        self.system_prompt = system_prompt

        # 会话管理
        self.session_manager = SessionManager(data_dir)
        self._current_session: Optional[Session] = None

        # Slash 命令系统
        self.enable_slash = enable_slash
        self._slash_registry = SlashCommandRegistry()
        if enable_slash:
            self._setup_slash_commands()

        # Ralph Loop 配置
        self.enable_ralph_loop = enable_ralph_loop
        self.ralph_config = RalphLoopConfig(max_iterations=ralph_max_iterations)

        # 自动保存
        self.auto_save = auto_save

    async def initialize(self) -> None:
        """初始化引擎"""
        # 获取或创建当前会话
        self._current_session = await self.session_manager.get_or_create_current()

    @property
    def current_session(self) -> Session:
        """获取当前会话"""
        if self._current_session is None:
            raise RuntimeError("Engine not initialized. Call initialize() first.")
        return self._current_session

    @property
    def context(self) -> ContextManager:
        """获取当前上下文管理器"""
        return self.current_session.context

    def _setup_slash_commands(self) -> None:
        """设置 Slash 命令"""
        from .slash.commands import register_all_commands
        register_all_commands(self._slash_registry)

    async def chat(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True,
        use_ralph_loop: bool = False,
        history: Optional[list] = None,
        skill_context: Optional[str] = None,
    ) -> str:
        """
        聊天方法（非流式）

        Args:
            query: 用户输入
            use_rag: 是否使用 RAG
            use_tools: 是否使用工具
            use_ralph_loop: 是否使用 Ralph Loop
            history: 历史消息列表（可选，用于临时覆盖上下文）
            skill_context: 技能上下文内容（可选）

        Returns:
            AI 回答
        """
        # 处理 Slash 命令
        slash_result = await self._handle_slash_command(query)
        if slash_result is not None:
            return slash_result

        # 使用 Ralph Loop
        if use_ralph_loop and self.enable_ralph_loop:
            return await self._run_ralph_loop(query, use_rag=use_rag, use_tools=use_tools,
                                              history=history, skill_context=skill_context)

        # 如果提供了 history，使用它（不保存到会话）
        if history is not None:
            return await self._chat_with_history(query, use_rag=use_rag, use_tools=use_tools,
                                                  history=history, skill_context=skill_context)

        # 添加用户消息到上下文
        user_message = Message(role=MessageRole.USER, content=query)
        self.context.add_message(user_message)

        # 构建输入
        messages = self._build_input_messages(use_rag=use_rag, use_tools=use_tools,
                                               skill_context=skill_context)

        # 调用 LLM
        response = self.llm.invoke(messages, system_prompt=self.system_prompt)

        # 添加助手消息到上下文
        assistant_message = Message(role=MessageRole.ASSISTANT, content=response)
        self.context.add_message(assistant_message)

        # 自动保存
        if self.auto_save:
            await self.context.save()

        return response

    def chat_stream(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True,
        callback: Optional[Callable[[str], None]] = None,
        history: Optional[list] = None,
        skill_context: Optional[str] = None,
    ) -> Iterator[str]:
        """
        聊天方法（流式）

        Args:
            query: 用户输入
            use_rag: 是否使用 RAG
            use_tools: 是否使用工具
            callback: 每个 token 的回调函数
            history: 历史消息列表（可选，用于临时覆盖上下文）
            skill_context: 技能上下文内容（可选）

        Yields:
            每个 token 的字符串片段
        """
        # 如果提供了 history，使用非流式方式（简化实现）
        if history is not None:
            # 运行异步方法并返回结果
            import asyncio
            response = asyncio.run(self._chat_with_history(
                query, use_rag=use_rag, use_tools=use_tools,
                history=history, skill_context=skill_context
            ))
            yield response
            return

        # 添加用户消息到上下文
        user_message = Message(role=MessageRole.USER, content=query)
        self.context.add_message(user_message)

        # 构建输入
        messages = self._build_input_messages(use_rag=use_rag, use_tools=use_tools,
                                               skill_context=skill_context)

        # 流式调用 LLM
        full_response = ""
        for token in self.llm.stream(messages, system_prompt=self.system_prompt, callback=callback):
            full_response += token
            yield token

        # 添加助手消息到上下文
        assistant_message = Message(role=MessageRole.ASSISTANT, content=full_response)
        self.context.add_message(assistant_message)

        # 异步保存（不阻塞）
        if self.auto_save:
            asyncio.create_task(self.context.save())

    async def astream(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True,
    ) -> Iterator[str]:
        """
        异步流式聊天

        Args:
            query: 用户输入
            use_rag: 是否使用 RAG
            use_tools: 是否使用工具

        Yields:
            每个 token 的字符串片段
        """
        # 添加用户消息到上下文
        user_message = Message(role=MessageRole.USER, content=query)
        self.context.add_message(user_message)

        # 构建输入
        messages = self._build_input_messages(use_rag=use_rag, use_tools=use_tools)

        # 异步流式调用
        full_response = ""
        async for token in self.llm.astream(messages, system_prompt=self.system_prompt):
            full_response += token
            yield token

        # 添加助手消息到上下文
        assistant_message = Message(role=MessageRole.ASSISTANT, content=full_response)
        self.context.add_message(assistant_message)

        # 保存
        if self.auto_save:
            await self.context.save()

    def _build_input_messages(self, use_rag: bool = True, use_tools: bool = True,
                               skill_context: Optional[str] = None) -> list:
        """
        构建输入消息

        Args:
            use_rag: 是否使用 RAG
            use_tools: 是否使用工具
            skill_context: 技能上下文内容

        Returns:
            消息列表
        """
        messages = self.context.to_langchain_messages()

        # 如果需要 RAG，添加上下文
        if use_rag and self.rag_engine:
            # 获取最近的消息作为查询
            recent_messages = self.context.get_last_n_messages(3)
            if recent_messages:
                query = " ".join(m.content for m in recent_messages if m.role == MessageRole.USER)
                if query:
                    context = self.rag_engine.search(query, top_k=5)
                    if context:
                        # 添加 RAG 上下文
                        from langchain_core.messages import SystemMessage
                        rag_message = SystemMessage(content=f"参考上下文：\n{context}")
                        messages = [rag_message] + messages

        # 添加技能上下文
        if skill_context:
            from langchain_core.messages import SystemMessage
            skill_message = SystemMessage(content=f"技能上下文：\n{skill_context}")
            messages = [skill_message] + messages

        return messages

    async def _chat_with_history(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True,
        history: Optional[list] = None,
        skill_context: Optional[str] = None,
    ) -> str:
        """
        使用提供的历史消息进行对话（不保存到会话）

        Args:
            query: 用户输入
            use_rag: 是否使用 RAG
            use_tools: 是否使用工具
            history: 历史消息列表
            skill_context: 技能上下文

        Returns:
            AI 回答
        """
        # 构建消息列表
        messages = []

        # 添加历史消息
        if history:
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                from langchain_core.messages import HumanMessage, AIMessage
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

        # 添加当前用户消息
        from langchain_core.messages import HumanMessage
        messages.append(HumanMessage(content=query))

        # 如果需要 RAG，添加上下文
        if use_rag and self.rag_engine:
            context = self.rag_engine.search(query, top_k=5)
            if context:
                from langchain_core.messages import SystemMessage
                rag_message = SystemMessage(content=f"参考上下文：\n{context}")
                messages = [rag_message] + messages

        # 添加技能上下文
        if skill_context:
            from langchain_core.messages import SystemMessage
            skill_message = SystemMessage(content=f"技能上下文：\n{skill_context}")
            messages = [skill_message] + messages

        # 调用 LLM
        response = self.llm.invoke(messages, system_prompt=self.system_prompt)

        return response

    async def _handle_slash_command(self, query: str) -> Optional[str]:
        """处理 Slash 命令"""
        if not self.enable_slash:
            return None

        call = parse_slash_command_call(query)
        if call is None:
            return None

        cmd = self._slash_registry.find(call)
        if cmd is None:
            return f"未知命令: /{call.name}\n使用 /help 查看可用命令。"

        # 执行命令
        result = cmd.func(self, call.args)
        import inspect
        if inspect.isawaitable(result):
            result = await result

        return result

    async def _run_ralph_loop(self, query: str, use_rag: bool = True, use_tools: bool = True,
                              history: Optional[list] = None, skill_context: Optional[str] = None) -> str:
        """运行 Ralph Loop"""
        flow = create_ralph_flow(query, self.ralph_config.max_iterations)
        runner = FlowRunner(flow, self, max_moves=self.ralph_config.max_iterations * 2)

        result = await runner.run()

        if result.stop_reason == "completed":
            return result.final_message or "任务完成。"
        elif result.stop_reason == "max_moves":
            return f"达到最大迭代次数 ({self.ralph_config.max_iterations})。\n\n{result.final_message or ''}"
        else:
            return result.final_message or "执行中断。"

    # ========== 检查点管理 ==========

    def create_checkpoint(self, description: str = "") -> int:
        """
        创建检查点

        Args:
            description: 检查点描述

        Returns:
            检查点 ID
        """
        checkpoint = self.context.create_checkpoint(description)

        # 异步保存
        if self.auto_save:
            asyncio.create_task(self.context.save())

        return checkpoint.id

    def rollback_to_checkpoint(self, checkpoint_id: int) -> bool:
        """
        回滚到检查点

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            是否成功
        """
        success = self.context.rollback_to_checkpoint(checkpoint_id)

        if success and self.auto_save:
            asyncio.create_task(self.context.save())

        return success

    def rollback_last(self) -> bool:
        """
        回滚到上一个检查点

        Returns:
            是否成功
        """
        success = self.context.rollback_last_checkpoint()

        if success and self.auto_save:
            asyncio.create_task(self.context.save())

        return success

    def list_checkpoints(self) -> list:
        """列出所有检查点"""
        return self.context.list_checkpoints()

    # ========== 会话管理 ==========

    async def new_session(self, name: Optional[str] = None) -> Session:
        """
        创建新会话

        Args:
            name: 会话名称

        Returns:
            新会话
        """
        self._current_session = await self.session_manager.create_session(name)
        return self._current_session

    async def switch_session(self, session_id: str) -> Optional[Session]:
        """
        切换会话

        Args:
            session_id: 会话 ID

        Returns:
            切换后的会话
        """
        self._current_session = await self.session_manager.switch_session(session_id)
        return self._current_session

    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        return await self.session_manager.delete_session(session_id)

    def list_sessions(self) -> list:
        """列出所有会话"""
        return self.session_manager.list_sessions()

    async def save(self) -> None:
        """保存当前状态"""
        await self.context.save()

    async def clear_context(self) -> None:
        """清空当前上下文"""
        self.context.clear()
        await self.context.save()

    def get_context_info(self) -> dict:
        """获取上下文信息"""
        metadata = self.context.metadata
        return {
            "session_id": metadata.session_id,
            "message_count": metadata.total_messages,
            "checkpoint_count": metadata.checkpoint_count,
            "estimated_tokens": metadata.total_tokens,
            "created_at": metadata.created_at,
            "updated_at": metadata.updated_at,
        }

    # ========== Agent 循环 ==========

    async def chat_with_agent(
        self,
        query: str,
        agent_config: AgentConfig | None = None,
        loop_config: LoopConfig | None = None,
    ) -> str:
        """
        使用 Agent 循环进行对话

        Args:
            query: 用户查询
            agent_config: Agent 配置（可选）
            loop_config: 循环配置（可选）

        Returns:
            AI 回答
        """
        # 创建主 Agent
        agent_spec = AgentSpec(
            name="main",
            config=agent_config or AgentConfig(
                name="main",
                system_prompt=self.system_prompt,
            ),
        )

        main_agent = Agent(
            name="main",
            spec=agent_spec,
            llm_manager=self.llm,
        )

        # 添加子 Agent（如果有 skills）
        if self.skill_manager:
            tools = self.skill_manager.get_tools()
        else:
            tools = []

        # 创建编排器
        orchestrator = MultiAgentOrchestrator(main_agent)

        # 创建循环
        loop = AgentLoop(
            orchestrator=orchestrator,
            config=loop_config or LoopConfig(max_turns=1),
            tools=tools,
        )

        # 设置回调
        def on_step(step):
            """步骤回调"""
            # 可以在这里添加日志、进度更新等
            pass

        loop.on_step(on_step)

        # 执行循环
        result = await loop.run(query, system_prompt=self.system_prompt)

        # 保存到上下文
        user_message = Message(role=MessageRole.USER, content=query)
        assistant_message = Message(role=MessageRole.ASSISTANT, content=result.final_output or "")
        self.context.add_message([user_message, assistant_message])

        # 自动保存
        if self.auto_save:
            await self.context.save()

        return result.final_output or ""

    async def chat_with_agent_stream(
        self,
        query: str,
        agent_config: AgentConfig | None = None,
        loop_config: LoopConfig | None = None,
    ) -> Iterator[str]:
        """
        使用 Agent 循环进行对话（流式）

        Args:
            query: 用户查询
            agent_config: Agent 配置（可选）
            loop_config: 循环配置（可选）

        Yields:
            每个 token 的字符串片段
        """
        # 创建主 Agent
        agent_spec = AgentSpec(
            name="main",
            config=agent_config or AgentConfig(
                name="main",
                system_prompt=self.system_prompt,
            ),
        )

        main_agent = Agent(
            name="main",
            spec=agent_spec,
            llm_manager=self.llm,
        )

        # 获取工具
        if self.skill_manager:
            tools = self.skill_manager.get_tools()
        else:
            tools = []

        # 创建编排器
        orchestrator = MultiAgentOrchestrator(main_agent)

        # 创建循环
        loop = AgentLoop(
            orchestrator=orchestrator,
            config=loop_config or LoopConfig(max_turns=1),
            tools=tools,
        )

        # 流式执行
        full_response = ""
        async for token in loop.run_stream(query, system_prompt=self.system_prompt):
            full_response += token
            yield token

        # 保存到上下文
        user_message = Message(role=MessageRole.USER, content=query)
        assistant_message = Message(role=MessageRole.ASSISTANT, content=full_response)
        self.context.add_message([user_message, assistant_message])

        # 异步保存
        if self.auto_save:
            asyncio.create_task(self.context.save())

    def create_agent(
        self,
        name: str,
        system_prompt: str,
        tools: list[Any] | None = None,
        max_steps: int = 10,
    ) -> Agent:
        """
        创建一个新的 Agent

        Args:
            name: Agent 名称
            system_prompt: 系统提示词
            tools: 工具列表
            max_steps: 最大步骤数

        Returns:
            创建的 Agent
        """
        agent_config = AgentConfig(
            name=name,
            system_prompt=system_prompt,
            max_steps=max_steps,
        )

        agent_spec = AgentSpec(
            name=name,
            config=agent_config,
            tools=tools or [],
        )

        agent = Agent(
            name=name,
            spec=agent_spec,
            llm_manager=self.llm,
        )

        return agent

    def add_subagent(self, agent: Agent) -> None:
        """
        添加子 Agent

        Args:
            agent: 子 Agent 实例
        """
        # TODO: 存储子 Agent 引用
        pass

    def __repr__(self) -> str:
        """字符串表示"""
        return f"EnhancedChatEngine(model={self.llm.model_name}, sessions={len(self.session_manager._sessions)})"


# 为了向后兼容，创建一个工厂函数
def create_chat_engine(
    model: str = "gpt-4o-mini",
    provider: Union[str, LLMProvider] = LLMProvider.OPENAI,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    system_prompt: str = "",
    data_dir: Optional[Path] = None,
    **kwargs
) -> EnhancedChatEngine:
    """
    创建聊天引擎（工厂函数）

    Args:
        model: 模型名称
        provider: 提供商
        api_key: API 密钥
        base_url: API 基础地址
        system_prompt: 系统提示词
        data_dir: 数据目录
        **kwargs: 其他配置

    Returns:
        增强版聊天引擎
    """
    if isinstance(provider, str):
        provider = LLMProvider(provider)

    llm_config = LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )

    return EnhancedChatEngine(
        llm_config=llm_config,
        system_prompt=system_prompt,
        data_dir=data_dir,
    )


__all__ = [
    "EnhancedChatEngine",
    "create_chat_engine",
]
