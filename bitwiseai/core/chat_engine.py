# -*- coding: utf-8 -*-
"""
聊天引擎

整合 RAG、Skills、Slash 命令和 Flow，支持 LangChain Agent 和流式输出
"""
from typing import Iterator, Optional, List
from ..llm import LLM
from .rag_engine import RAGEngine
from .skill_manager import SkillManager
from .slash import SlashCommandRegistry, parse_slash_command_call
from .flow import create_ralph_flow, FlowRunner
from .flow.ralph import RalphLoopConfig


class ChatEngine:
    """
    聊天引擎

    整合 RAG、Skills、Slash 命令和 Flow，提供统一的聊天接口
    """

    def __init__(
        self,
        llm: LLM,
        rag_engine: Optional[RAGEngine] = None,
        skill_manager: Optional[SkillManager] = None,
        system_prompt: str = "",
        enable_slash: bool = True,
        enable_ralph_loop: bool = True,
        ralph_max_iterations: int = 10,
    ):
        """
        初始化聊天引擎

        Args:
            llm: LLM 实例
            rag_engine: RAG 引擎（可选）
            skill_manager: Skill 管理器（可选）
            system_prompt: 系统提示词
            enable_slash: 是否启用 Slash 命令
            enable_ralph_loop: 是否启用 Ralph Loop 自动迭代
            ralph_max_iterations: Ralph Loop 默认最大迭代次数
        """
        self.llm = llm
        self.rag_engine = rag_engine
        self.skill_manager = skill_manager
        self.system_prompt = system_prompt

        # Slash 命令系统
        self.enable_slash = enable_slash
        self._slash_registry = SlashCommandRegistry()
        self._setup_slash_commands()

        # Ralph Loop 配置
        self.enable_ralph_loop = enable_ralph_loop
        self.ralph_max_iterations = ralph_max_iterations
        self.ralph_config = RalphLoopConfig(max_iterations=ralph_max_iterations)

        # 历史消息（用于上下文）
        self.history: List[dict] = []

        # YOLO 模式（自动审批）
        self.yolo_mode = False

    def _setup_slash_commands(self) -> None:
        """设置所有 Slash 命令"""
        if not self.enable_slash:
            return

        from .slash.commands import register_all_commands
        register_all_commands(self._slash_registry)

    def list_slash_commands(self) -> List[str]:
        """
        列出所有可用的 Slash 命令

        Returns:
            命令名称列表
        """
        return self._slash_registry.list_names()

    def get_slash_command_help(self, command_name: str) -> str | None:
        """
        获取 Slash 命令的帮助信息

        Args:
            command_name: 命令名称

        Returns:
            命令描述，如果不存在则返回 None
        """
        cmd = self._slash_registry.get(command_name)
        return cmd.description if cmd else None

    async def _handle_slash_command(self, query: str) -> str | None:
        """
        处理 Slash 命令

        支持两种格式：
        1. /command - 内置命令（如 /help, /clear）
        2. /skill-name - 技能名称（自动加载并使用技能上下文）

        Args:
            query: 用户输入

        Returns:
            命令执行结果，如果不是命令则返回 None
        """
        if not self.enable_slash:
            return None

        call = parse_slash_command_call(query)
        if call is None:
            return None

        cmd = self._slash_registry.find(call)
        if cmd is None:
            # 检查是否是技能名称
            if self.skill_manager and call.name in self.skill_manager.list_available_skills():
                # 自动加载技能
                skill = self.skill_manager.get_skill(call.name)
                if skill and not skill.loaded:
                    self.skill_manager.load_skill(call.name)

                # 获取技能内容作为上下文
                skill = self.skill_manager.get_skill(call.name)
                if skill and skill.content:
                    # 使用技能上下文进行对话
                    actual_query = call.args if call.args else f"使用 {call.name} 技能帮助我"
                    return await self._run_with_skill_context(actual_query, skill)
                else:
                    return f"技能 {call.name} 已加载，但没有找到内容。请尝试: {actual_query}"

            return f"未知命令或技能: /{call.name}\n使用 /help 查看可用命令，或 /skills 查看可用技能。"

        # 执行命令
        import inspect

        result = cmd.func(self, call.args)
        if inspect.isawaitable(result):
            result = await result

        return result

    async def _run_with_skill_context(self, query: str, skill) -> str:
        """
        使用技能上下文运行对话

        Args:
            query: 用户问题
            skill: 技能对象

        Returns:
            AI 回答
        """
        # 使用 RAG 和工具，但带技能上下文
        return self._chat_with_tools(
            query=query,
            use_rag=True,
            history=None,
            skill_context=skill.content
        )

    async def _run_ralph_loop(self, query: str) -> str:
        """
        运行 Ralph Loop 自动迭代

        Args:
            query: 用户任务描述
            **kwargs: 传递给 chat 的其他参数

        Returns:
            最终结果
        """
        flow = create_ralph_flow(query, self.ralph_config.max_iterations)
        runner = FlowRunner(flow, self, max_moves=self.ralph_config.max_iterations * 2)

        result = await runner.run()

        # 构建结果消息
        if result.stop_reason == "completed":
            return result.final_message or "任务完成。"
        elif result.stop_reason == "max_moves":
            return f"达到最大迭代次数 ({self.ralph_config.max_iterations})。\n\n{result.final_message or ''}"
        else:
            return result.final_message or "执行中断。"

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
        history: Optional[List[dict]] = None,
        skill_context: Optional[str] = None,
        use_ralph_loop: bool = False,
    ) -> str:
        """
        聊天方法（非流式）

        Args:
            query: 用户问题
            use_rag: 是否使用 RAG 模式
            use_tools: 是否使用工具
            history: 历史消息列表 [{"role": "user", "content": "..."}, ...]
            skill_context: 技能上下文内容（可选）
            use_ralph_loop: 是否使用 Ralph Loop 自动迭代

        Returns:
            LLM 生成的回答
        """
        import asyncio

        # 处理 Slash 命令
        slash_result = asyncio.run(self._handle_slash_command(query))
        if slash_result is not None:
            return slash_result

        # 使用 Ralph Loop 自动迭代
        if use_ralph_loop and self.enable_ralph_loop:
            return asyncio.run(self._run_ralph_loop(query, use_rag=use_rag, use_tools=use_tools, history=history, skill_context=skill_context))

        # 如果有工具且启用工具调用，使用带工具的聊天
        if use_tools and self.skill_manager:
            loaded_skills = self.skill_manager.list_loaded_skills()
            if len(loaded_skills) > 0 or skill_context:
                return self._chat_with_tools(query, use_rag=use_rag, history=history, skill_context=skill_context)

        if use_rag and self.rag_engine:
            return self._chat_with_rag(query, history=history, skill_context=skill_context)
        else:
            return self._chat_with_llm(query, history=history, skill_context=skill_context)

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

    def _chat_with_rag(self, query: str, history: Optional[List[dict]] = None, skill_context: Optional[str] = None) -> str:
        """
        RAG 模式对话（非流式）
        """
        if not self.rag_engine:
            return self._chat_with_llm(query, history=history, skill_context=skill_context)

        # 检索相关文档
        context = self.rag_engine.search(query, top_k=5)

        # 构建消息列表
        messages = self._convert_history_to_messages(history)
        
        # 构建系统提示词
        system_parts = []
        base_prompt = self.system_prompt or "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。"
        system_parts.append(base_prompt)
        
        # 添加技能上下文
        if skill_context:
            skills_context = "\n\n" + "=" * 60 + "\n"
            skills_context += "技能指导内容（请严格按照这些指导执行任务）:\n"
            skills_context += "=" * 60 + "\n\n"
            skills_context += skill_context
            skills_context += "\n\n" + "=" * 60 + "\n"
            system_parts.append(skills_context)
        
        # 添加 RAG 上下文
        if context:
            rag_prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请直接说不知道。

上下文:
{context}"""
            system_parts.append(rag_prompt)
        
        system_content = "\n\n".join(system_parts)
        
        # 更新系统消息或添加新的系统消息
        if messages and isinstance(messages[0], type(messages[0])) and hasattr(messages[0], 'content'):
            from langchain_core.messages import SystemMessage
            if isinstance(messages[0], SystemMessage):
                messages[0].content = system_content
            else:
                messages.insert(0, SystemMessage(content=system_content))
        else:
            from langchain_core.messages import SystemMessage
            messages.insert(0, SystemMessage(content=system_content))
        
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

        # 构建系统提示词
        from langchain_core.messages import SystemMessage, HumanMessage
        base_prompt = self.system_prompt or "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。"

        if context:
            system_content = f"""{base_prompt}

基于以下上下文回答问题。如果上下文中没有相关信息，请直接说不知道。

上下文:
{context}"""
        else:
            system_content = base_prompt

        # 添加或更新系统消息
        if messages and isinstance(messages[0], SystemMessage):
            messages[0].content = system_content
        else:
            messages.insert(0, SystemMessage(content=system_content))

        # 添加当前用户消息
        messages.append(HumanMessage(content=query))

        # 流式调用 LLM
        yield from self.llm.stream(messages)

    def _chat_with_llm(self, query: str, history: Optional[List[dict]] = None, skill_context: Optional[str] = None) -> str:
        """
        纯 LLM 模式对话（非流式）
        """
        # 构建消息列表
        messages = self._convert_history_to_messages(history)
        
        # 构建系统提示词
        system_parts = []
        base_prompt = self.system_prompt or "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。"
        system_parts.append(base_prompt)
        
        # 添加技能上下文
        if skill_context:
            skills_context = "\n\n" + "=" * 60 + "\n"
            skills_context += "技能指导内容（请严格按照这些指导执行任务）:\n"
            skills_context += "=" * 60 + "\n\n"
            skills_context += skill_context
            skills_context += "\n\n" + "=" * 60 + "\n"
            system_parts.append(skills_context)
        
        system_content = "\n\n".join(system_parts)
        
        # 添加系统消息
        from langchain_core.messages import SystemMessage, HumanMessage
        if messages and isinstance(messages[0], SystemMessage):
            messages[0].content = system_content
        else:
            messages.insert(0, SystemMessage(content=system_content))
        
        # 添加当前用户消息
        messages.append(HumanMessage(content=query))
        
        # 如果有历史消息，使用消息列表；否则使用简单字符串格式
        if len(messages) > 1:
            return self.llm.invoke(messages)
        else:
            # 没有历史，使用简单字符串格式
            prompt = f"{system_content}\n\n用户: {query}"
            return self.llm.invoke(prompt)

    def _chat_with_llm_stream(self, query: str, history: Optional[List[dict]] = None) -> Iterator[str]:
        """
        纯 LLM 模式对话（流式）
        """
        # 构建消息列表
        messages = self._convert_history_to_messages(history)

        # 添加系统提示词
        from langchain_core.messages import SystemMessage, HumanMessage
        if self.system_prompt:
            if messages and isinstance(messages[0], SystemMessage):
                messages[0].content = self.system_prompt
            else:
                messages.insert(0, SystemMessage(content=self.system_prompt))

        # 添加当前用户消息
        messages.append(HumanMessage(content=query))

        # 流式调用 LLM
        yield from self.llm.stream(messages)

    def _chat_with_tools(self, query: str, use_rag: bool = True, history: Optional[List[dict]] = None, skill_context: Optional[str] = None) -> str:
        """
        使用工具的对话模式（非流式）

        支持两种方式：
        1. 直接 Function Calling（如果模型支持）：使用 bind_tools
        2. 简化模式（fallback）：在系统提示中描述工具
        """
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

        # 获取工具
        if not self.skill_manager:
            if use_rag and self.rag_engine:
                return self._chat_with_rag(query, history=history, skill_context=skill_context)
            else:
                return self._chat_with_llm(query, history=history, skill_context=skill_context)

        try:
            langchain_tools = self.skill_manager.get_tools()
        except Exception as e:
            print(f"⚠️  获取工具失败: {str(e)}，退回普通模式")
            if use_rag and self.rag_engine:
                return self._chat_with_rag(query, history=history, skill_context=skill_context)
            else:
                return self._chat_with_llm(query, history=history, skill_context=skill_context)

        # 如果没有工具但有技能上下文，使用普通模式但包含技能上下文
        if not langchain_tools:
            if skill_context:
                # 有技能上下文但没有工具，使用普通模式但包含技能上下文
                if use_rag and self.rag_engine:
                    return self._chat_with_rag(query, history=history, skill_context=skill_context)
                else:
                    return self._chat_with_llm(query, history=history, skill_context=skill_context)
            else:
                # 没有工具也没有技能上下文，正常回退
                if use_rag and self.rag_engine:
                    return self._chat_with_rag(query, history=history)
                else:
                    return self._chat_with_llm(query, history=history)

        # 构建系统提示词
        base_prompt = self.system_prompt or "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。"

        # 添加技能上下文（如果提供）- 限制长度避免 API 错误
        skills_context = ""
        if skill_context:
            # 限制技能上下文长度，避免超过 API 限制
            max_skill_length = 3000  # 限制为 3000 字符
            truncated_skill = skill_context[:max_skill_length]
            if len(skill_context) > max_skill_length:
                truncated_skill += "\n\n...(技能内容已截断以适应 API 限制)"

            skills_context = "\n\n" + "=" * 60 + "\n"
            skills_context += "技能指导内容（请严格按照这些指导执行任务）:\n"
            skills_context += "=" * 60 + "\n\n"
            skills_context += truncated_skill
            skills_context += "\n\n" + "=" * 60 + "\n"

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
                    import os
                    filename = os.path.basename(source_file)
                    context_parts.append(f"[文档 {i}: {filename}]\n{text}")
                context = "\n\n---\n\n".join(context_parts)
                context = f"\n\n重要：请优先使用以下检索到的文档内容回答问题。如果文档中有相关信息，必须基于文档内容回答，不要说自己不知道。\n\n检索到的文档内容:\n{context}\n"

        system_prompt_text = base_prompt + skills_context + (context if context else "")

        # 尝试使用直接 Function Calling（如果模型支持）
        try:
            # 使用 bind_tools 绑定工具到模型（原生 Function Calling）
            if hasattr(self.llm.client, 'bind_tools'):
                # 绑定工具到模型
                model_with_tools = self.llm.client.bind_tools(langchain_tools)

                # 构建消息（包含历史消息）
                messages = self._convert_history_to_messages(history)
                # 更新系统提示词
                if messages and isinstance(messages[0], type(messages[0])) and hasattr(messages[0], 'content'):
                    if isinstance(messages[0], SystemMessage):
                        messages[0].content = system_prompt_text
                    else:
                        messages.insert(0, SystemMessage(content=system_prompt_text))
                else:
                    messages.insert(0, SystemMessage(content=system_prompt_text))

                # 添加当前用户消息
                messages.append(HumanMessage(content=query))

                # 调用模型 - 捕获 API 错误
                try:
                    response = model_with_tools.invoke(messages)
                except Exception as api_error:
                    error_msg = str(api_error)
                    # 如果是参数配置错误（如 2013），尝试不使用 bind_tools
                    if '2013' in error_msg or 'invalid' in error_msg.lower() or 'params' in error_msg.lower():
                        print(f"⚠️  bind_tools 与当前 LLM 不兼容，降级到 Agent 模式")
                        raise AttributeError("bind_tools not compatible")
                    else:
                        raise

                # 检查是否有工具调用
                if hasattr(response, 'tool_calls') and response.tool_calls:
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
                            except Exception as e:
                                tool_messages.append(
                                    ToolMessage(
                                        content=f"工具执行失败: {str(e)}",
                                        tool_call_id=tool_id
                                    )
                                )
                                print(f"❌ 工具 {tool_name} 执行失败: {e}")
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
            # Fallback: 使用 Agent 模式或简化模式
            if "bind_tools" in str(e) or "2013" in str(e) or "compatible" in str(e):
                print(f"⚠️  直接 Function Calling 不可用，尝试简化模式")
            else:
                print(f"⚠️  Function Calling 失败: {str(e)}，尝试简化模式")

            # 使用简化模式：直接在系统提示中描述工具
            try:
                # 构建工具描述
                tools_description = "\n\n可用工具:\n"
                for tool in langchain_tools:
                    tools_description += f"- {tool.name}: {tool.description}\n"

                simplified_prompt = system_prompt_text + tools_description + "\n请使用上述工具来完成任务。"

                # 构建消息
                messages = self._convert_history_to_messages(history)
                if messages and isinstance(messages[0], SystemMessage):
                    messages[0].content = simplified_prompt
                else:
                    messages.insert(0, SystemMessage(content=simplified_prompt))

                messages.append(HumanMessage(content=query))

                # 调用 LLM（不带工具绑定）
                response = self.llm.client.invoke(messages)

                if hasattr(response, 'content'):
                    content = response.content
                    # 检查是否需要调用工具（简单解析）
                    for tool in langchain_tools:
                        tool_name = tool.name
                        if f"调用{tool_name}" in content or f"使用{tool_name}" in content or f"{tool_name}(" in content:
                            # 尝试提取参数并调用工具
                            try:
                                # 这里可以添加更复杂的参数解析逻辑
                                # 目前先简单返回，让用户手动调用
                                print(f"\n💡 检测到可能需要调用工具: {tool_name}")
                                print(f"   请尝试直接使用: /{tool.name} <参数>")
                            except:
                                pass
                    return content
                else:
                    return str(response)

            except Exception as simple_error:
                print(f"⚠️  简化模式也失败: {str(simple_error)}，退回普通模式")
                if use_rag and self.rag_engine:
                    return self._chat_with_rag(query, history=history, skill_context=skill_context)
                else:
                    return self._chat_with_llm(query, history=history, skill_context=skill_context)

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
                            except Exception as e:
                                tool_messages.append(
                                    ToolMessage(
                                        content=f"工具执行失败: {str(e)}",
                                        tool_call_id=tool_id
                                    )
                                )
                                print(f"❌ 工具 {tool_name} 执行失败: {e}")
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
            print(f"⚠️  直接 Function Calling 不可用，使用 Agent 模式: {str(e)}")
            
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


__all__ = ["ChatEngine", "SlashCommandRegistry"]

