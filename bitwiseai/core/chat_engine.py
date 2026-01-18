# -*- coding: utf-8 -*-
"""
聊天引擎

整合 RAG 和 Skills，支持 LangChain Agent 和流式输出
"""
from typing import Iterator, Optional, List, Any, Callable
from ..llm import LLM
from .rag_engine import RAGEngine
from .skill_manager import SkillManager


class ChatEngine:
    """
    聊天引擎

    整合 RAG 和 Skills，提供统一的聊天接口
    """

    def __init__(
        self,
        llm: LLM,
        rag_engine: Optional[RAGEngine] = None,
        skill_manager: Optional[SkillManager] = None,
        system_prompt: str = ""
    ):
        """
        初始化聊天引擎

        Args:
            llm: LLM 实例
            rag_engine: RAG 引擎（可选）
            skill_manager: Skill 管理器（可选）
            system_prompt: 系统提示词
        """
        self.llm = llm
        self.rag_engine = rag_engine
        self.skill_manager = skill_manager
        self.system_prompt = system_prompt

    def chat(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True
    ) -> str:
        """
        聊天方法（非流式）

        Args:
            query: 用户问题
            use_rag: 是否使用 RAG 模式
            use_tools: 是否使用工具

        Returns:
            LLM 生成的回答
        """
        # 如果有工具且启用工具调用，使用带工具的聊天
        if use_tools and self.skill_manager:
            loaded_skills = self.skill_manager.list_loaded_skills()
            if len(loaded_skills) > 0:
                print(f"🔧 检测到 {len(loaded_skills)} 个已加载的 skills，尝试使用工具调用")
                return self._chat_with_tools(query, use_rag=use_rag)
            else:
                print("⚠️  没有已加载的 skills，跳过工具调用")
        
        if use_rag and self.rag_engine:
            return self._chat_with_rag(query)
        else:
            return self._chat_with_llm(query)

    def chat_stream(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True
    ) -> Iterator[str]:
        """
        流式聊天方法

        Args:
            query: 用户问题
            use_rag: 是否使用 RAG 模式
            use_tools: 是否使用工具

        Yields:
            每个 token 的字符串片段
        """
        # 如果有工具且启用工具调用，使用带工具的流式聊天
        if use_tools and self.skill_manager and len(self.skill_manager.list_loaded_skills()) > 0:
            yield from self._chat_with_tools_stream(query, use_rag=use_rag)
        elif use_rag and self.rag_engine:
            yield from self._chat_with_rag_stream(query)
        else:
            yield from self._chat_with_llm_stream(query)

    def _chat_with_rag(self, query: str) -> str:
        """
        RAG 模式对话（非流式）
        """
        if not self.rag_engine:
            return self._chat_with_llm(query)

        # 检索相关文档
        context = self.rag_engine.search(query, top_k=5)

        if context:
            prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请直接说不知道。

上下文:
{context}

问题: {query}

回答:"""
        else:
            # 没有检索到相关文档，退回纯 LLM 模式
            return self._chat_with_llm(query)

        # 调用 LLM
        return self.llm.invoke(prompt)

    def _chat_with_rag_stream(self, query: str) -> Iterator[str]:
        """
        RAG 模式对话（流式）
        """
        if not self.rag_engine:
            yield from self._chat_with_llm_stream(query)
            return

        # 检索相关文档
        context = self.rag_engine.search(query, top_k=5)

        if context:
            prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请直接说不知道。

上下文:
{context}

问题: {query}

回答:"""
        else:
            # 没有检索到相关文档，退回纯 LLM 模式
            yield from self._chat_with_llm_stream(query)
            return

        # 流式调用 LLM
        yield from self.llm.stream(prompt)

    def _chat_with_llm(self, query: str) -> str:
        """
        纯 LLM 模式对话（非流式）
        """
        if self.system_prompt:
            prompt = f"{self.system_prompt}\n\n用户: {query}"
        else:
            prompt = query

        return self.llm.invoke(prompt)

    def _chat_with_llm_stream(self, query: str) -> Iterator[str]:
        """
        纯 LLM 模式对话（流式）
        """
        if self.system_prompt:
            prompt = f"{self.system_prompt}\n\n用户: {query}"
        else:
            prompt = query

        yield from self.llm.stream(prompt)

    def _chat_with_tools(self, query: str, use_rag: bool = True) -> str:
        """
        使用工具的对话模式（非流式）
        
        使用最新的 LangChain create_agent API
        """
        from langchain.agents import create_agent
        from langchain_core.messages import HumanMessage, AIMessage

        # 获取工具
        if not self.skill_manager:
            if use_rag and self.rag_engine:
                return self._chat_with_rag(query)
            else:
                return self._chat_with_llm(query)

        try:
            langchain_tools = self.skill_manager.get_tools()
        except Exception as e:
            print(f"⚠️  获取工具失败: {str(e)}，退回普通模式")
            if use_rag and self.rag_engine:
                return self._chat_with_rag(query)
            else:
                return self._chat_with_llm(query)

        if not langchain_tools:
            if use_rag and self.rag_engine:
                return self._chat_with_rag(query)
            else:
                return self._chat_with_llm(query)

        # 构建系统提示词
        base_prompt = self.system_prompt or "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。"
        
        # 添加工具使用提示
        tools_info = []
        for tool in langchain_tools:
            tools_info.append(f"- {tool.name}: {tool.description}")
        
        tools_prompt = f"""
你有以下工具可以使用：
{chr(10).join(tools_info)}

重要提示：
- 当用户要求解析 ASM 指令时，必须使用 parse_asm_instruction 工具
- 当用户要求解析 ASM 文件时，必须使用 parse_asm_file 工具
- 当用户提供十六进制、二进制或十进制的指令值时，应该调用相应的解析工具
- 不要尝试自己解析指令，必须使用提供的工具
"""
        
        system_message = base_prompt + tools_prompt

        # 如果有 RAG，检索相关文档
        context = ""
        if use_rag and self.rag_engine:
            context_docs = self.rag_engine.search(query, top_k=5)
            if context_docs:
                context = f"\n\n相关文档上下文:\n{context_docs}\n"

        # 创建 Agent
        try:
            # 打印调试信息
            print(f"🔧 使用 {len(langchain_tools)} 个工具进行对话")
            for tool in langchain_tools:
                print(f"   - {tool.name}: {tool.description[:50]}...")
            
            # 使用最新的 create_agent API
            print(f"🔧 创建 Agent，模型: {type(self.llm.client).__name__}")
            
            # 构建系统提示词
            system_prompt_text = system_message + context if context else system_message
            
            # 使用 create_agent API（LangChain 1.1.0+）
            agent = create_agent(
                model=self.llm.client,  # 直接使用模型实例
                tools=langchain_tools,
                system_prompt=system_prompt_text
            )
            
            # 调用 agent（使用 messages 格式）
            result = agent.invoke({"messages": [HumanMessage(content=query)]})
            
            # 从结果中提取最后一条消息的内容
            messages = result.get("messages", [])
            if messages:
                # 获取最后一条 AI 消息
                ai_messages = [m for m in messages if isinstance(m, AIMessage)]
                if ai_messages:
                    return ai_messages[-1].content
                # 如果没有 AI 消息，返回最后一条消息的内容
                return str(messages[-1].content) if hasattr(messages[-1], 'content') else str(messages[-1])
            
            return str(result)

        except Exception as e:
            print(f"⚠️  Agent 执行失败: {str(e)}，退回普通模式")
            if use_rag and self.rag_engine:
                return self._chat_with_rag(query)
            else:
                return self._chat_with_llm(query)

    def _chat_with_tools_stream(self, query: str, use_rag: bool = True) -> Iterator[str]:
        """
        使用工具的对话模式（流式）

        注意：LangChain Agent 的流式输出比较复杂，这里先实现简化版本
        对于工具调用场景，先执行工具，然后流式输出结果
        """
        # 对于工具调用场景，先使用非流式模式获取完整回答
        # 然后逐字符流式输出（简化实现）
        # 未来可以改进为真正的 Agent 流式输出
        full_response = self._chat_with_tools(query, use_rag=use_rag)
        
        # 逐字符流式输出
        for char in full_response:
            yield char


__all__ = ["ChatEngine"]

