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

    def _convert_history_to_messages(self, history: Optional[List[dict]]) -> List:
        """
        将历史消息转换为 LangChain 消息格式
        
        Args:
            history: 历史消息列表 [{"role": "user", "content": "..."}, ...]
            
        Returns:
            LangChain 消息列表
        """
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        messages = []
        
        # 转换历史消息（不包括系统提示词，系统提示词会在调用时单独添加）
        if history:
            for msg in history:
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role", "")
                content = msg.get("content", "")
                if not content:
                    continue
                    
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                elif role == "system":
                    messages.append(SystemMessage(content=content))
        
        return messages

    def chat(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True,
        history: Optional[List[dict]] = None
    ) -> str:
        """
        聊天方法（非流式）

        Args:
            query: 用户问题
            use_rag: 是否使用 RAG 模式
            use_tools: 是否使用工具
            history: 历史消息列表 [{"role": "user", "content": "..."}, ...]

        Returns:
            LLM 生成的回答
        """
        # 如果有工具且启用工具调用，使用带工具的聊天
        if use_tools and self.skill_manager:
            loaded_skills = self.skill_manager.list_loaded_skills()
            if len(loaded_skills) > 0:
                print(f"🔧 检测到 {len(loaded_skills)} 个已加载的 skills，尝试使用工具调用")
                return self._chat_with_tools(query, use_rag=use_rag, history=history)
            else:
                print("⚠️  没有已加载的 skills，跳过工具调用")
        
        if use_rag and self.rag_engine:
            return self._chat_with_rag(query, history=history)
        else:
            return self._chat_with_llm(query, history=history)

    def chat_stream(
        self,
        query: str,
        use_rag: bool = True,
        use_tools: bool = True,
        history: Optional[List[dict]] = None
    ) -> Iterator[str]:
        """
        流式聊天方法

        Args:
            query: 用户问题
            use_rag: 是否使用 RAG 模式
            use_tools: 是否使用工具
            history: 历史消息列表 [{"role": "user", "content": "..."}, ...]

        Yields:
            每个 token 的字符串片段
        """
        # 如果有工具且启用工具调用，使用带工具的流式聊天
        if use_tools and self.skill_manager and len(self.skill_manager.list_loaded_skills()) > 0:
            yield from self._chat_with_tools_stream(query, use_rag=use_rag, history=history)
        elif use_rag and self.rag_engine:
            yield from self._chat_with_rag_stream(query, history=history)
        else:
            yield from self._chat_with_llm_stream(query, history=history)

    def _chat_with_rag(self, query: str, history: Optional[List[dict]] = None) -> str:
        """
        RAG 模式对话（非流式）
        """
        if not self.rag_engine:
            return self._chat_with_llm(query, history=history)

        # 检索相关文档
        context = self.rag_engine.search(query, top_k=5)

        # 构建消息列表
        messages = self._convert_history_to_messages(history)
        
        if context:
            # 添加 RAG 上下文到系统提示词
            rag_prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请直接说不知道。

上下文:
{context}"""
            
            # 更新系统消息或添加新的系统消息
            if messages and isinstance(messages[0], type(messages[0])) and hasattr(messages[0], 'content'):
                from langchain_core.messages import SystemMessage
                if isinstance(messages[0], SystemMessage):
                    messages[0].content = f"{messages[0].content}\n\n{rag_prompt}"
                else:
                    messages.insert(0, SystemMessage(content=rag_prompt))
            else:
                from langchain_core.messages import SystemMessage
                messages.insert(0, SystemMessage(content=rag_prompt))
        
        # 添加当前用户消息
        from langchain_core.messages import HumanMessage
        messages.append(HumanMessage(content=query))

        # 调用 LLM（如果有历史消息，使用消息列表；否则使用字符串）
        if len(messages) > 1:
            return self.llm.invoke(messages)
        else:
            # 没有历史，使用简单字符串格式
            prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请直接说不知道。

上下文:
{context}

问题: {query}

回答:"""
            return self.llm.invoke(prompt)

    def _chat_with_rag_stream(self, query: str, history: Optional[List[dict]] = None) -> Iterator[str]:
        """
        RAG 模式对话（流式）
        """
        if not self.rag_engine:
            yield from self._chat_with_llm_stream(query, history=history)
            return

        # 检索相关文档
        context = self.rag_engine.search(query, top_k=5)

        # 构建消息列表
        messages = self._convert_history_to_messages(history)
        
        if context:
            # 添加 RAG 上下文到系统提示词
            rag_prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请直接说不知道。

上下文:
{context}"""
            
            # 更新系统消息或添加新的系统消息
            if messages and isinstance(messages[0], type(messages[0])) and hasattr(messages[0], 'content'):
                from langchain_core.messages import SystemMessage
                if isinstance(messages[0], SystemMessage):
                    messages[0].content = f"{messages[0].content}\n\n{rag_prompt}"
                else:
                    messages.insert(0, SystemMessage(content=rag_prompt))
            else:
                from langchain_core.messages import SystemMessage
                messages.insert(0, SystemMessage(content=rag_prompt))
        
        # 添加当前用户消息
        from langchain_core.messages import HumanMessage
        messages.append(HumanMessage(content=query))

        # 流式调用 LLM（如果有历史消息，使用消息列表；否则使用字符串）
        if len(messages) > 1:
            yield from self.llm.stream(messages)
        else:
            # 没有历史，使用简单字符串格式
            prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请直接说不知道。

上下文:
{context}

问题: {query}

回答:"""
            yield from self.llm.stream(prompt)

    def _chat_with_llm(self, query: str, history: Optional[List[dict]] = None) -> str:
        """
        纯 LLM 模式对话（非流式）
        """
        # 构建消息列表
        messages = self._convert_history_to_messages(history)
        
        # 添加当前用户消息
        from langchain_core.messages import HumanMessage
        messages.append(HumanMessage(content=query))
        
        # 如果有历史消息，使用消息列表；否则使用简单字符串格式
        if len(messages) > 1:
            return self.llm.invoke(messages)
        else:
            # 没有历史，使用简单字符串格式
            if self.system_prompt:
                prompt = f"{self.system_prompt}\n\n用户: {query}"
            else:
                prompt = query
            return self.llm.invoke(prompt)

    def _chat_with_llm_stream(self, query: str, history: Optional[List[dict]] = None) -> Iterator[str]:
        """
        纯 LLM 模式对话（流式）
        """
        # 构建消息列表
        messages = self._convert_history_to_messages(history)
        
        # 添加当前用户消息
        from langchain_core.messages import HumanMessage
        messages.append(HumanMessage(content=query))
        
        # 如果有历史消息，使用消息列表；否则使用简单字符串格式
        if len(messages) > 1:
            yield from self.llm.stream(messages)
        else:
            # 没有历史，使用简单字符串格式
            if self.system_prompt:
                prompt = f"{self.system_prompt}\n\n用户: {query}"
            else:
                prompt = query
            yield from self.llm.stream(prompt)

    def _chat_with_tools(self, query: str, use_rag: bool = True, history: Optional[List[dict]] = None) -> str:
        """
        使用工具的对话模式（非流式）
        
        支持两种方式：
        1. 直接 Function Calling（如果模型支持）：使用 bind_tools
        2. Agent 模式（fallback）：使用 create_agent API
        """
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        from langchain.agents import create_agent

        # 获取工具
        if not self.skill_manager:
            if use_rag and self.rag_engine:
                return self._chat_with_rag(query, history=history)
            else:
                return self._chat_with_llm(query, history=history)

        try:
            langchain_tools = self.skill_manager.get_tools()
        except Exception as e:
            print(f"⚠️  获取工具失败: {str(e)}，退回普通模式")
            if use_rag and self.rag_engine:
                return self._chat_with_rag(query, history=history)
            else:
                return self._chat_with_llm(query, history=history)

        if not langchain_tools:
            if use_rag and self.rag_engine:
                return self._chat_with_rag(query, history=history)
            else:
                return self._chat_with_llm(query, history=history)

        # 构建系统提示词
        base_prompt = self.system_prompt or "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。"
        
        # 如果有 RAG，检索相关文档
        context = ""
        if use_rag and self.rag_engine:
            # 使用 search_with_metadata 获取更详细的检索结果
            results = self.rag_engine.search_with_metadata(query, top_k=5, use_hybrid=True)
            if results:
                # 格式化检索结果，包含文档来源信息
                context_parts = []
                for i, result in enumerate(results, 1):
                    source_file = result.get('source_file', '未知')
                    text = result.get('text', '')
                    score = result.get('score', 0.0)
                    import os
                    filename = os.path.basename(source_file)
                    context_parts.append(f"[文档 {i}: {filename}]\n{text}")
                context = "\n\n---\n\n".join(context_parts)
                context = f"\n\n重要：请优先使用以下检索到的文档内容回答问题。如果文档中有相关信息，必须基于文档内容回答，不要说自己不知道。\n\n检索到的文档内容:\n{context}\n"
        
        system_prompt_text = base_prompt + context if context else base_prompt

        # 尝试使用直接 Function Calling（如果模型支持）
        try:
            # 使用 bind_tools 绑定工具到模型（原生 Function Calling）
            if hasattr(self.llm.client, 'bind_tools'):
                print(f"🔧 使用原生 Function Calling，模型: {type(self.llm.client).__name__}")
                print(f"🔧 可用工具 ({len(langchain_tools)} 个):")
                for tool in langchain_tools:
                    print(f"   - {tool.name}: {tool.description[:50]}...")
                
                # 绑定工具到模型
                model_with_tools = self.llm.client.bind_tools(langchain_tools)
                
                # 构建消息（包含历史消息）
                messages = self._convert_history_to_messages(history)
                # 更新系统提示词
                if messages and isinstance(messages[0], type(messages[0])) and hasattr(messages[0], 'content'):
                    from langchain_core.messages import SystemMessage
                    if isinstance(messages[0], SystemMessage):
                        messages[0].content = system_prompt_text
                    else:
                        messages.insert(0, SystemMessage(content=system_prompt_text))
                else:
                    from langchain_core.messages import SystemMessage
                    messages.insert(0, SystemMessage(content=system_prompt_text))
                
                # 添加当前用户消息
                messages.append(HumanMessage(content=query))
                
                # 调用模型
                response = model_with_tools.invoke(messages)
                
                # 检查是否有工具调用
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    print(f"🔧 检测到 {len(response.tool_calls)} 个工具调用")
                    
                    # 执行工具调用
                    tool_messages = []
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.get('name', '')
                        tool_args = tool_call.get('args', {})
                        tool_id = tool_call.get('id', '')
                        
                        # 查找对应的工具
                        tool_func = None
                        for tool in langchain_tools:
                            if tool.name == tool_name:
                                tool_func = tool
                                break
                        
                        if tool_func:
                            try:
                                # 执行工具
                                tool_result = tool_func.invoke(tool_args)
                                tool_messages.append(
                                    ToolMessage(
                                        content=str(tool_result),
                                        tool_call_id=tool_id
                                    )
                                )
                                print(f"   ✓ {tool_name}({tool_args}) = {tool_result}")
                            except Exception as e:
                                tool_messages.append(
                                    ToolMessage(
                                        content=f"工具执行失败: {str(e)}",
                                        tool_call_id=tool_id
                                    )
                                )
                                print(f"   ❌ {tool_name} 执行失败: {e}")
                        else:
                            tool_messages.append(
                                ToolMessage(
                                    content=f"工具不存在: {tool_name}",
                                    tool_call_id=tool_id
                                )
                            )
                    
                    # 将工具结果添加到消息历史，再次调用模型
                    messages.append(response)
                    messages.extend(tool_messages)
                    
                    # 获取最终回答
                    final_response = model_with_tools.invoke(messages)
                    return final_response.content
                else:
                    # 没有工具调用，直接返回回答
                    return response.content
            else:
                # 模型不支持 bind_tools，使用 Agent 模式
                raise AttributeError("模型不支持 bind_tools，使用 Agent 模式")
                
        except (AttributeError, Exception) as e:
            # Fallback: 使用 Agent 模式
            print(f"⚠️  直接 Function Calling 不可用: {str(e)}")
            print(f"🔧 使用 Agent 模式，模型: {type(self.llm.client).__name__}")
            print(f"🔧 可用工具 ({len(langchain_tools)} 个):")
            for tool in langchain_tools:
                print(f"   - {tool.name}: {tool.description[:50]}...")
            
            try:
                # 使用 create_agent API（LangChain 1.1.0+）
                agent = create_agent(
                    model=self.llm.client,
                    tools=langchain_tools,
                    system_prompt=system_prompt_text
                )
                
                # 构建消息（包含历史消息）
                messages = self._convert_history_to_messages(history)
                # 更新系统提示词
                if messages and isinstance(messages[0], type(messages[0])) and hasattr(messages[0], 'content'):
                    from langchain_core.messages import SystemMessage
                    if isinstance(messages[0], SystemMessage):
                        messages[0].content = system_prompt_text
                    else:
                        messages.insert(0, SystemMessage(content=system_prompt_text))
                else:
                    from langchain_core.messages import SystemMessage
                    messages.insert(0, SystemMessage(content=system_prompt_text))
                
                # 添加当前用户消息
                messages.append(HumanMessage(content=query))
                
                # 调用 agent
                result = agent.invoke({"messages": messages})
                
                # 从结果中提取最后一条消息的内容
                messages = result.get("messages", [])
                if messages:
                    ai_messages = [m for m in messages if isinstance(m, AIMessage)]
                    if ai_messages:
                        return ai_messages[-1].content
                    return str(messages[-1].content) if hasattr(messages[-1], 'content') else str(messages[-1])
                
                return str(result)
            except Exception as agent_error:
                print(f"⚠️  Agent 执行失败: {str(agent_error)}，退回普通模式")
                if use_rag and self.rag_engine:
                    return self._chat_with_rag(query, history=history)
                else:
                    return self._chat_with_llm(query, history=history)

    def _chat_with_tools_stream(self, query: str, use_rag: bool = True, history: Optional[List[dict]] = None) -> Iterator[str]:
        """
        使用工具的对话模式（流式）
        
        实现真正的流式传输：
        1. 如果模型支持 bind_tools，工具调用后流式获取最终回答
        2. 对于 Agent 模式，使用流式 Agent 执行器
        """
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
        from langchain.agents import create_agent

        # 获取工具
        if not self.skill_manager:
            if use_rag and self.rag_engine:
                yield from self._chat_with_rag_stream(query, history=history)
            else:
                yield from self._chat_with_llm_stream(query, history=history)
            return

        try:
            langchain_tools = self.skill_manager.get_tools()
        except Exception as e:
            print(f"⚠️  获取工具失败: {str(e)}，退回普通模式")
            if use_rag and self.rag_engine:
                yield from self._chat_with_rag_stream(query, history=history)
            else:
                yield from self._chat_with_llm_stream(query, history=history)
            return

        if not langchain_tools:
            if use_rag and self.rag_engine:
                yield from self._chat_with_rag_stream(query, history=history)
            else:
                yield from self._chat_with_llm_stream(query, history=history)
            return

        # 构建系统提示词
        base_prompt = self.system_prompt or "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。"
        
        # 如果有 RAG，检索相关文档
        context = ""
        if use_rag and self.rag_engine:
            # 使用 search_with_metadata 获取更详细的检索结果
            results = self.rag_engine.search_with_metadata(query, top_k=5, use_hybrid=True)
            if results:
                # 格式化检索结果，包含文档来源信息
                context_parts = []
                for i, result in enumerate(results, 1):
                    source_file = result.get('source_file', '未知')
                    text = result.get('text', '')
                    score = result.get('score', 0.0)
                    import os
                    filename = os.path.basename(source_file)
                    context_parts.append(f"[文档 {i}: {filename}]\n{text}")
                context = "\n\n---\n\n".join(context_parts)
                context = f"\n\n重要：请优先使用以下检索到的文档内容回答问题。如果文档中有相关信息，必须基于文档内容回答，不要说自己不知道。\n\n检索到的文档内容:\n{context}\n"
        
        system_prompt_text = base_prompt + context if context else base_prompt

        # 尝试使用直接 Function Calling（如果模型支持）
        try:
            # 使用 bind_tools 绑定工具到模型（原生 Function Calling）
            if hasattr(self.llm.client, 'bind_tools'):
                print(f"🔧 使用原生 Function Calling（流式），模型: {type(self.llm.client).__name__}")
                print(f"🔧 可用工具 ({len(langchain_tools)} 个):")
                for tool in langchain_tools:
                    print(f"   - {tool.name}: {tool.description[:50]}...")
                
                # 绑定工具到模型
                model_with_tools = self.llm.client.bind_tools(langchain_tools)
                
                # 构建消息（包含历史消息）
                messages = self._convert_history_to_messages(history)
                # 更新系统提示词
                if messages and isinstance(messages[0], type(messages[0])) and hasattr(messages[0], 'content'):
                    from langchain_core.messages import SystemMessage
                    if isinstance(messages[0], SystemMessage):
                        messages[0].content = system_prompt_text
                    else:
                        messages.insert(0, SystemMessage(content=system_prompt_text))
                else:
                    from langchain_core.messages import SystemMessage
                    messages.insert(0, SystemMessage(content=system_prompt_text))
                
                # 添加当前用户消息
                messages.append(HumanMessage(content=query))
                
                # 调用模型（非流式，获取工具调用）
                response = model_with_tools.invoke(messages)
                
                # 检查是否有工具调用
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    print(f"🔧 检测到 {len(response.tool_calls)} 个工具调用")
                    
                    # 执行工具调用
                    tool_messages = []
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.get('name', '')
                        tool_args = tool_call.get('args', {})
                        tool_id = tool_call.get('id', '')
                        
                        # 查找对应的工具
                        tool_func = None
                        for tool in langchain_tools:
                            if tool.name == tool_name:
                                tool_func = tool
                                break
                        
                        if tool_func:
                            try:
                                # 执行工具
                                tool_result = tool_func.invoke(tool_args)
                                tool_messages.append(
                                    ToolMessage(
                                        content=str(tool_result),
                                        tool_call_id=tool_id
                                    )
                                )
                                print(f"   ✓ {tool_name}({tool_args}) = {tool_result}")
                            except Exception as e:
                                tool_messages.append(
                                    ToolMessage(
                                        content=f"工具执行失败: {str(e)}",
                                        tool_call_id=tool_id
                                    )
                                )
                                print(f"   ❌ {tool_name} 执行失败: {e}")
                        else:
                            tool_messages.append(
                                ToolMessage(
                                    content=f"工具不存在: {tool_name}",
                                    tool_call_id=tool_id
                                )
                            )
                    
                    # 将工具结果添加到消息历史
                    messages.append(response)
                    messages.extend(tool_messages)
                    
                    # 流式获取最终回答
                    print(f"🔧 流式获取最终回答...")
                    for chunk in model_with_tools.stream(messages):
                        if hasattr(chunk, 'content') and chunk.content:
                            yield chunk.content
                        elif isinstance(chunk, str):
                            yield chunk
                else:
                    # 没有工具调用，流式返回回答
                    for chunk in model_with_tools.stream(messages):
                        if hasattr(chunk, 'content') and chunk.content:
                            yield chunk.content
                        elif isinstance(chunk, str):
                            yield chunk
            else:
                # 模型不支持 bind_tools，使用 Agent 模式
                raise AttributeError("模型不支持 bind_tools，使用 Agent 模式")
                
        except (AttributeError, Exception) as e:
            # Fallback: 使用 Agent 模式
            # 注意：LangChain Agent 的流式输出比较复杂，这里先获取完整回答，然后流式输出
            print(f"⚠️  直接 Function Calling 不可用: {str(e)}")
            print(f"🔧 使用 Agent 模式，模型: {type(self.llm.client).__name__}")
            
            try:
                # 使用 create_agent API
                agent = create_agent(
                    model=self.llm.client,
                    tools=langchain_tools,
                    system_prompt=system_prompt_text
                )
                
                # 构建消息（包含历史消息）
                messages = self._convert_history_to_messages(history)
                # 更新系统提示词
                if messages and isinstance(messages[0], type(messages[0])) and hasattr(messages[0], 'content'):
                    from langchain_core.messages import SystemMessage
                    if isinstance(messages[0], SystemMessage):
                        messages[0].content = system_prompt_text
                    else:
                        messages.insert(0, SystemMessage(content=system_prompt_text))
                else:
                    from langchain_core.messages import SystemMessage
                    messages.insert(0, SystemMessage(content=system_prompt_text))
                
                # 添加当前用户消息
                messages.append(HumanMessage(content=query))
                
                # 执行 Agent（非流式）
                result = agent.invoke({"messages": messages})
                messages = result.get("messages", [])
                ai_messages = [m for m in messages if isinstance(m, AIMessage)]
                
                if ai_messages:
                    # 获取最终回答内容
                    content = ai_messages[-1].content
                    # 流式输出（逐字符，至少提供流式体验）
                    # 注意：这是简化实现，真正的 Agent 流式需要更复杂的处理
                    for char in content:
                        yield char
                else:
                    # 如果没有 AI 消息，输出整个结果
                    yield str(result)
                        
            except Exception as agent_error:
                print(f"⚠️  Agent 执行失败: {str(agent_error)}，退回普通模式")
                if use_rag and self.rag_engine:
                    yield from self._chat_with_rag_stream(query, history=history)
                else:
                    yield from self._chat_with_llm_stream(query, history=history)


__all__ = ["ChatEngine"]

