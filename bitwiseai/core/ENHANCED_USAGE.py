# -*- coding: utf-8 -*-
"""
增强版聊天引擎使用示例

演示上下文管理、会话管理、LLM 集成、流式传输等功能
"""

import asyncio
from pathlib import Path


# ============================================================================
# 基础使用
# ============================================================================


async def demo_basic_usage():
    """基础使用示例"""
    from bitwiseai.core import create_chat_engine

    # 创建引擎
    engine = create_chat_engine(
        model="gpt-4o-mini",
        provider="openai",
        api_key="your-api-key",  # 或设置 OPENAI_API_KEY 环境变量
        system_prompt="你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。",
    )

    # 初始化引擎
    await engine.initialize()

    # 非流式聊天
    response = await engine.chat("你好！")
    print(response)

    # 流式聊天
    for token in engine.chat_stream("请介绍一下你自己。"):
        print(token, end="", flush=True)
    print()

    # 保存状态
    await engine.save()


# ============================================================================
# 上下文管理和检查点
# ============================================================================


async def demo_context_management():
    """上下文管理和检查点示例"""
    from bitwiseai.core import create_chat_engine, MessageRole

    engine = create_chat_engine()
    await engine.initialize()

    # 进行一些对话
    await engine.chat("我的名字是 Alice")
    await engine.chat("我是一名软件工程师")

    # 创建检查点
    checkpoint_id = engine.create_checkpoint(description="保存用户基本信息")
    print(f"创建检查点: {checkpoint_id}")

    # 继续对话
    await engine.chat("我正在学习 Python")

    # 回滚到检查点
    success = engine.rollback_to_checkpoint(checkpoint_id)
    if success:
        print("已回滚到检查点")
        # 当前上下文只有前两条消息

    # 列出所有检查点
    checkpoints = engine.list_checkpoints()
    print(f"检查点数量: {len(checkpoints)}")

    # 获取上下文信息
    info = engine.get_context_info()
    print(f"上下文信息: {info}")


# ============================================================================
# 会话管理
# ============================================================================


async def demo_session_management():
    """会话管理示例"""
    from bitwiseai.core import create_chat_engine

    engine = create_chat_engine()
    await engine.initialize()

    # 创建新会话
    session1 = await engine.new_session("工作项目")
    await engine.chat("讨论工作项目 A")
    await engine.save()

    # 创建另一个会话
    session2 = await engine.new_session("学习计划")
    await engine.chat("制定 Python 学习计划")
    await engine.save()

    # 列出所有会话
    sessions = engine.list_sessions()
    print(f"总共有 {len(sessions)} 个会话")
    for session in sessions:
        print(f"  - {session.name} ({session.session_id[:8]}...)")

    # 切换会话
    await engine.switch_session(session1.session_id)
    print(f"当前会话消息数: {len(engine.context.messages)}")

    # 删除会话
    await engine.delete_session(session2.session_id)


# ============================================================================
# 多提供商支持
# ============================================================================


async def demo_multi_provider():
    """多提供商支持示例"""
    from bitwiseai.core import LLMConfig, LLMProvider, EnhancedChatEngine

    # 使用 OpenAI
    openai_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        api_key="your-openai-key",
    )

    # 使用 Anthropic Claude
    anthropic_config = LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-5-sonnet-20241022",
        api_key="your-anthropic-key",
    )

    # 使用本地 Ollama
    ollama_config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        model="llama3.2",
        base_url="http://localhost:11434",
    )

    # 使用自定义端点（兼容 OpenAI API）
    custom_config = LLMConfig(
        provider=LLMProvider.CUSTOM,
        model="qwen2.5",
        base_url="http://localhost:8000/v1",
        api_key="dummy",
    )

    # 创建引擎
    engine = EnhancedChatEngine(llm_config=openai_config)
    await engine.initialize()

    # 切换提供商
    engine.llm = LLMManager(anthropic_config)

    response = await engine.chat("你好！")
    print(response)


# ============================================================================
# 异步流式传输
# ============================================================================


async def demo_async_streaming():
    """异步流式传输示例"""
    from bitwiseai.core import create_chat_engine

    engine = create_chat_engine()
    await engine.initialize()

    # 异步流式聊天
    print("AI 回答: ", end="", flush=True)
    async for token in engine.astream("讲一个短故事"):
        print(token, end="", flush=True)
    print()


# ============================================================================
# Slash 命令和 Ralph Loop
# ============================================================================


async def demo_slash_and_ralph():
    """Slash 命令和 Ralph Loop 示例"""
    from bitwiseai.core import create_chat_engine

    engine = create_chat_engine()
    await engine.initialize()

    # 使用 Slash 命令
    response = await engine.chat("/help")
    print(response)

    # 切换 YOLO 模式
    response = await engine.chat("/yolo on")
    print(response)

    # 使用 Ralph Loop 自动迭代
    response = await engine.chat(
        "分析当前目录的 Python 文件，找出所有未使用的导入。",
        use_ralph_loop=True,
    )
    print(response)


# ============================================================================
# 完整示例：多轮对话 + 检查点 + 会话管理
# ============================================================================


async def demo_complete_workflow():
    """完整工作流示例"""
    from bitwiseai.core import create_chat_engine

    engine = create_chat_engine(
        system_prompt="你是一个专业的编程助手，擅长分析和改进代码。",
    )
    await engine.initialize()

    print("=" * 60)
    print("开始多轮对话")
    print("=" * 60)

    # 第一轮对话
    print("\n用户: 我正在学习 Python 装饰器")
    response1 = await engine.chat("我正在学习 Python 装饰器，能帮我解释一下吗？")
    print(f"助手: {response1}")

    # 创建检查点
    cp1 = engine.create_checkpoint("学习装饰器")
    print(f"\n[创建检查点 {cp1}]")

    # 第二轮对话
    print("\n用户: 给我一个例子")
    response2 = await engine.chat("能给我写一个简单的装饰器例子吗？")
    print(f"助手: {response2}")

    # 创建检查点
    cp2 = engine.create_checkpoint("获取装饰器例子")
    print(f"[创建检查点 {cp2}]")

    # 第三轮对话
    print("\n用户: 这个例子怎么用？")
    response3 = await engine.chat("这个装饰器怎么使用？")
    print(f"助手: {response3}")

    # 查看上下文
    info = engine.get_context_info()
    print(f"\n[上下文: {info['message_count']} 条消息]")

    # 回滚到第一个检查点
    print(f"\n[回滚到检查点 {cp1}]")
    engine.rollback_to_checkpoint(cp1)

    # 继续对话（从检查点开始）
    print("\n用户: 装饰器有什么用？")
    response4 = await engine.chat("装饰器主要有什么用途？")
    print(f"助手: {response4}")

    # 保存会话
    await engine.save()
    print("\n[会话已保存]")


# ============================================================================
# 配置示例
# ============================================================================


def demo_configurations():
    """各种配置示例"""
    from bitwiseai.core import (
        LLMConfig,
        LLMProvider,
        EnhancedChatEngine,
    )

    # 基础配置
    basic_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
    )

    # 高级配置
    advanced_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        temperature=0.5,
        max_tokens=4000,
        streaming=True,
        kwargs={
            "top_p": 0.9,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5,
        },
    )

    # 创建引擎
    engine = EnhancedChatEngine(
        llm_config=basic_config,
        system_prompt="你是 BitwiseAI 助手",
        data_dir=Path("~/.bitwiseai").expanduser(),
        enable_slash=True,
        enable_ralph_loop=True,
        ralph_max_iterations=10,
        auto_save=True,
    )


if __name__ == "__main__":
    # 运行示例
    asyncio.run(demo_basic_usage())
    # asyncio.run(demo_context_management())
    # asyncio.run(demo_session_management())
    # asyncio.run(demo_multi_provider())
    # asyncio.run(demo_async_streaming())
    # asyncio.run(demo_slash_and_ralph())
    # asyncio.run(demo_complete_workflow())
