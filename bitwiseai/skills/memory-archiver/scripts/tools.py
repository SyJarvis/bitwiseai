# -*- coding: utf-8 -*-
"""
记忆归档工具

将 CLI 对话历史归档到长期记忆
"""
from datetime import datetime
from typing import List, Dict, Any, Optional


def archive_current_conversation(
    summary_title: str = "",
    include_summary: bool = True
) -> str:
    """
    将当前 CLI 对话归档到长期记忆

    Args:
        summary_title: 归档标题（可选，会自动生成）
        include_summary: 是否使用 LLM 生成智能摘要

    Returns:
        归档结果信息
    """
    # 通过全局上下文获取当前会话
    from bitwiseai.cli import get_current_chat_session

    session = get_current_chat_session()
    if not session:
        return "错误：当前没有活跃的 CLI 对话会话"

    messages = session.get_history()
    if not messages:
        return "错误：当前对话历史为空，无需归档"

    # 1. 格式化对话历史
    conversation_text = _format_conversation(messages)

    # 2. 生成标题
    if not summary_title:
        summary_title = _generate_title(messages)

    # 3. 生成摘要（保持原意）
    summary_section = ""
    if include_summary:
        summary = _generate_summary(messages, session.ai)
        summary_section = f"### 摘要\n\n{summary}\n\n"

    # 4. 构建存储内容
    content_to_store = f"""{summary_section}### 原始对话记录

{conversation_text}
"""

    # 5. 存储到长期记忆 (MEMORY.md)
    try:
        session.ai.memory_manager.promote_to_long_term(
            content=content_to_store,
            summary=f"[对话归档] {summary_title}"
        )
    except Exception as e:
        return f"错误：归档到长期记忆失败: {e}"

    # 6. 在短期记忆中添加归档标记
    try:
        archive_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.ai.memory_manager.append_to_short_term(
            content=f"📦 对话已归档到长期记忆\n"
                    f"   标题: {summary_title}\n"
                    f"   消息数: {len(messages)}\n"
                    f"   归档时间: {archive_time}",
            metadata={
                "type": "archive_marker",
                "archived_title": summary_title,
                "message_count": len(messages),
                "archived_at": archive_time
            }
        )
    except Exception as e:
        # 标记失败不影响主流程
        pass

    # 7. 清空当前 CLI 对话历史
    message_count = len(messages)
    session.clear_history()

    return (
        f"✓ 对话已归档到长期记忆\n"
        f"  标题: {summary_title}\n"
        f"  消息数: {message_count}\n"
        f"  存储位置: ~/.bitwiseai/MEMORY.md"
    )


def _format_conversation(messages: List[Dict[str, str]]) -> str:
    """格式化对话历史为文本"""
    lines = []

    for i, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "user":
            lines.append(f"**用户**: {content}")
        elif role == "assistant":
            lines.append(f"**AI**: {content}")
        elif role == "system":
            lines.append(f"*[系统]*: {content}")
        else:
            lines.append(f"**{role}**: {content}")

        lines.append("")  # 空行分隔

    return "\n".join(lines)


def _generate_title(messages: List[Dict[str, str]]) -> str:
    """基于第一条用户消息生成标题"""
    for msg in messages:
        if msg.get("role") == "user":
            first_msg = msg.get("content", "未命名对话")
            # 截取前 30 个字符作为标题
            if len(first_msg) > 30:
                return first_msg[:30] + "..."
            return first_msg

    return f"对话归档 {datetime.now().strftime('%Y-%m-%d %H:%M')}"


def _generate_summary(messages: List[Dict[str, str]], ai) -> str:
    """使用 LLM 生成对话摘要（保持原意）"""
    # 构建对话文本
    conversation = _format_conversation(messages)

    # 构建 Prompt（强调不篡改原意）
    prompt = f"""请对以下对话进行摘要总结。要求：
1. 准确概括对话的核心内容和关键结论
2. 保留重要的技术细节、解决方案、决策理由
3. 不要添加对话中没有的信息
4. 不要改变原意或过度解读
5. 使用简洁的 bullet points 格式

对话内容：
{conversation}

请生成摘要："""

    try:
        # 调用 LLM 生成摘要
        summary = ai.llm_manager.complete(
            prompt=prompt,
            temperature=0.3,  # 低温度，减少创造性，保持准确
            max_tokens=500
        )
        return summary.strip()
    except Exception:
        # 如果 LLM 调用失败，返回简单统计
        user_count = sum(1 for m in messages if m.get("role") == "user")
        assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
        return f"对话包含 {user_count} 条用户消息和 {assistant_count} 条 AI 回复"
