# -*- coding: utf-8 -*-
"""
聊天对话模块

优化后的聊天界面：
- 使用 Gradio 字典格式 [{"role": "user", "content": "..."}, ...]
- 用户消息立即显示
- 真正的流式传输
- 支持回车发送
"""
import gradio as gr
from typing import List, Dict, Optional


def create_chat_interface(web_app):
    """
    创建聊天对话界面

    Args:
        web_app: BitwiseAIWeb 实例

    Returns:
        聊天界面组件
    """
    ai = web_app.ai

    def messages_to_context(messages: List[Dict[str, str]]) -> str:
        """
        将消息列表转换为上下文文本（用于构建查询）
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            
        Returns:
            上下文文本
        """
        context_text = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user" and content:
                context_text += f"用户: {content}\n"
            elif role == "assistant" and content:
                context_text += f"助手: {content}\n"
        return context_text

    def chat_fn(message: str, history: List[Dict[str, str]], use_rag: bool, use_streaming: bool):
        """
        聊天处理函数（支持流式输出）
        
        使用 Gradio 字典格式：[{"role": "user", "content": "..."}, ...]

        Args:
            message: 用户消息
            history: 聊天历史（Gradio 字典格式）
            use_rag: 是否使用 RAG
            use_streaming: 是否使用流式输出

        Yields:
            更新后的聊天历史
        """
        if not message or not message.strip():
            yield history or []
            return

        if not ai:
            history = history or []
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": "❌ BitwiseAI 未初始化，请先配置 API 密钥。"})
            yield history
            return

        history = history or []

        try:
            # 1. 立即添加用户消息到历史
            history.append({"role": "user", "content": message})
            yield history  # 立即显示用户消息

            # 2. 构建上下文（从历史消息中提取，排除刚添加的用户消息）
            context_messages = history[:-1]  # 排除刚添加的用户消息
            
            # 3. 构建当前查询（包含历史上下文）
            if context_messages:
                context_text = messages_to_context(context_messages)
                current_query = context_text + f"用户: {message}"
            else:
                current_query = message

            # 4. 调用 AI（流式或非流式），传递历史消息
            if use_streaming:
                # 真正的流式输出
                response = ""
                # 先添加一个空的 assistant 消息
                history.append({"role": "assistant", "content": ""})
                
                # 传递历史消息（排除刚添加的用户消息和空的 assistant 消息）
                history_for_llm = context_messages
                
                for token in ai.chat_stream(message, use_rag=use_rag, use_tools=True, history=history_for_llm):
                    response += token
                    # 更新最后一条消息（assistant 响应）
                    history[-1] = {"role": "assistant", "content": response}
                    yield history
            else:
                # 非流式输出
                # 传递历史消息（排除刚添加的用户消息）
                history_for_llm = context_messages
                response = ai.chat(message, use_rag=use_rag, use_tools=True, history=history_for_llm)
                history.append({"role": "assistant", "content": response})
                yield history

        except Exception as e:
            # 错误处理
            if history and history[-1].get("role") == "user":
                # 如果最后一条是用户消息，添加错误响应
                history.append({"role": "assistant", "content": f"❌ 发生错误: {str(e)}"})
            else:
                # 如果已经有 assistant 消息，更新它
                history[-1] = {"role": "assistant", "content": f"❌ 发生错误: {str(e)}"}
            yield history

    def clear_chat():
        """清空聊天历史"""
        return []

    # 创建聊天界面
    with gr.Row() as interface:
        with gr.Column(scale=3):
            # 聊天配置区域
            with gr.Row():
                use_rag_checkbox = gr.Checkbox(
                    value=True,
                    label="使用 RAG (知识库检索)",
                    info="启用后会从知识库中检索相关内容"
                )
                use_streaming_checkbox = gr.Checkbox(
                    value=True,
                    label="流式输出",
                    info="启用后实时显示 AI 回答"
                )

            # 聊天界面（使用 Gradio 字典格式）
            chatbot = gr.Chatbot(
                label="对话历史",
                height=500
            )

            with gr.Row():
                msg = gr.Textbox(
                    label="输入消息",
                    placeholder="请输入您的问题...（按 Enter 发送，Shift+Enter 换行）",
                    scale=4,
                    lines=2,
                    max_lines=5
                )
                send_btn = gr.Button("发送", scale=1, variant="primary")

            with gr.Row():
                clear_btn = gr.Button("清空对话", variant="secondary")

            # 示例问题
            gr.Examples(
                examples=[
                    ["什么是 MUL 指令？"],
                    ["如何验证 SHIFT 指令？"],
                    ["PE 寄存器的 func_sel 参数含义是什么？"],
                    ["帮我分析这个日志文件中的错误"],
                ],
                inputs=msg,
                label="示例问题"
            )

        with gr.Column(scale=1):
            # 系统信息面板
            gr.Markdown("### ⚙️ 系统状态")

            system_info = gr.Markdown(
                value=get_system_info(ai),
                label="系统信息"
            )

            refresh_info_btn = gr.Button("刷新状态", size="sm")

            # 快捷操作
            gr.Markdown("### ⚡ 快捷操作")

            with gr.Column():
                set_prompt_btn = gr.Button("设置系统提示词", size="sm")
                new_prompt = gr.Textbox(
                    label="新提示词",
                    placeholder="输入新的系统提示词...",
                    lines=3
                )

            gr.Markdown("### 📖 使用提示")
            gr.Markdown("""
            - **RAG 模式**: 从知识库检索相关内容后回答
            - **纯 LLM 模式**: 直接使用大模型回答
            - 支持多轮对话，上下文会被保留
            - 按 **Enter** 发送消息，**Shift+Enter** 换行
            """)

    # 事件绑定
    # 发送按钮点击
    send_btn.click(
        fn=chat_fn,
        inputs=[msg, chatbot, use_rag_checkbox, use_streaming_checkbox],
        outputs=chatbot
    ).then(
        fn=lambda: "",  # 清空输入框
        outputs=msg
    )

    # 回车发送（Enter 键）
    msg.submit(
        fn=chat_fn,
        inputs=[msg, chatbot, use_rag_checkbox, use_streaming_checkbox],
        outputs=chatbot
    ).then(
        fn=lambda: "",  # 清空输入框
        outputs=msg
    )

    # 清空对话
    clear_btn.click(
        fn=clear_chat,
        outputs=chatbot
    )

    # 刷新系统信息
    refresh_info_btn.click(
        fn=lambda: get_system_info(ai),
        outputs=system_info
    )

    # 设置系统提示词
    set_prompt_btn.click(
        fn=lambda p: set_system_prompt(p, ai),
        inputs=[new_prompt],
        outputs=system_info
    ).then(
        fn=lambda: "",
        outputs=new_prompt
    )

    return interface


def get_system_info(ai) -> str:
    """获取系统信息"""
    if not ai:
        return "❌ BitwiseAI 未初始化"

    info = f"""
| 项目 | 状态 |
|------|------|
| LLM 模型 | {ai.llm.model if hasattr(ai.llm, 'model') else 'Unknown'} |
| Embedding | {ai.embedding.model if hasattr(ai.embedding, 'model') else 'Unknown'} |
| 向量库集合 | {ai.rag_engine.collection_name} |
| 可用 Skills | {len(ai.skill_manager.list_available_skills())} 个 |
| 已加载 Skills | {len(ai.skill_manager.list_loaded_skills())} 个 |
| 已注册任务 | {len(ai.tasks)} 个 |
    """
    return info


def set_system_prompt(new_prompt: str, ai) -> str:
    """设置系统提示词"""
    if not ai:
        return "❌ BitwiseAI 未初始化"

    try:
        ai.set_system_prompt(new_prompt)
        return f"✅ 系统提示词已更新\n\n{new_prompt[:100]}{'...' if len(new_prompt) > 100 else ''}"
    except Exception as e:
        return f"❌ 更新失败: {str(e)}"
