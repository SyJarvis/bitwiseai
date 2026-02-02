#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BitwiseAI Agent 使用示例

演示如何使用 Agent 循环自动执行复杂任务
"""
import asyncio
from bitwiseai import BitwiseAI
from bitwiseai.core import AgentConfig, LoopConfig


async def example_1_basic_agent():
    """示例 1: 基础 Agent 使用"""
    print("=" * 60)
    print("示例 1: 基础 Agent 使用")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # Agent 会自动执行任务，迭代直到完成
    response = await ai.chat_with_agent(
        "分析以下代码的问题，并生成修复建议：\n\n"
        "def foo(x, y):\n"
        "    return x + y\n"
        "    print(x + z)  # 这行永远不会执行",
        agent_config=AgentConfig(
            name="code_analyzer",
            system_prompt="你是代码分析专家，擅长发现代码问题。",
            max_steps=5,
        ),
    )

    print(f"Agent 分析结果:\n{response}\n")


async def example_2_multi_turn_agent():
    """示例 2: 多轮对话 Agent"""
    print("=" * 60)
    print("示例 2: 多轮对话 Agent")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 启用自动继续的多轮对话
    response = await ai.chat_with_agent(
        "帮我创建一个待办事项管理应用，包含增删改查功能。",
        agent_config=AgentConfig(
            name="full_stack",
            system_prompt="你是全栈开发专家，能独立完成应用开发。",
            max_steps=10,
        ),
        loop_config=LoopConfig(
            max_turns=3,  # 最多 3 轮对话
            auto_continue=True,  # 自动继续
            continue_threshold=0.8,  # 继续阈值
        ),
    )

    print(f"多轮 Agent 结果:\n{response[:200]}...\n")


async def example_3_streaming_agent():
    """示例 3: 流式 Agent 输出"""
    print("=" * 60)
    print("示例 3: 流式 Agent 输出")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    print("AI 回答: ", end="", flush=True)

    # 流式输出
    async for token in ai.chat_with_agent_stream(
        "讲一个关于 AI 的有趣故事，不要太长。",
        agent_config=AgentConfig(
            name="storyteller",
            system_prompt="你是一个擅长讲故事的 AI。",
            max_steps=3,
        ),
    ):
        print(token, end="", flush=True)

    print("\n")


async def example_4_agent_with_tools():
    """示例 4: 带工具的 Agent"""
    print("=" * 60)
    print("示例 4: 带工具的 Agent")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 加载一些 Skills
    skills = ai.list_skills()
    for skill in skills[:3]:
        ai.load_skill(skill)

    print(f"已加载 Skills: {ai.list_skills(loaded_only=True)}")

    # Agent 会自动使用可用的工具
    response = await ai.chat_with_agent(
        "帮我计算 0x100 + 0x200，并转换成十进制",
        agent_config=AgentConfig(
            name="calculator",
            system_prompt="你是计算助手，会使用工具完成计算任务。",
            max_steps=5,
        ),
    )

    print(f"带工具的 Agent 结果:\n{response}\n")


async def example_5_thinking_mode():
    """示例 5: 启用思考模式"""
    print("=" * 60)
    print("示例 5: 启用思考模式")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 启用思考模式，可以看到 Agent 的推理过程
    response = await ai.chat_with_agent(
        "分析一下为什么这段代码可能会有性能问题：\n\n"
        "result = []\n"
        "for i in range(10000):\n"
        "    result.append(str(i))",
        agent_config=AgentConfig(
            name="performance_analyzer",
            system_prompt="你是性能分析专家。",
            max_steps=5,
            enable_thinking=True,  # 启用思考模式
        ),
    )

    print(f"思考模式结果:\n{response}\n")


async def example_6_agent_with_checkpoints():
    """示例 6: Agent 配合检查点使用"""
    print("=" * 60)
    print("示例 6: Agent 配合检查点使用")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建检查点
    cp = ai.create_checkpoint("Agent 任务开始")
    print(f"✓ 创建检查点: {cp}")

    # 执行 Agent 任务
    response = await ai.chat_with_agent(
        "帮我设计一个用户认证系统的架构",
        agent_config=AgentConfig(
            name="architect",
            system_prompt="你是系统架构专家。",
            max_steps=8,
        ),
    )

    print(f"架构设计结果:\n{response[:300]}...")

    # 如果不满意，可以回滚重来
    # ai.rollback_to_checkpoint(cp)
    # print("\n✓ 已回滚到检查点")


async def example_7_session_with_agent():
    """示例 7: 在独立会话中使用 Agent"""
    print("=" * 60)
    print("示例 7: 在独立会话中使用 Agent")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建一个专门用于代码审查的会话
    session = await ai.new_session("代码审查")
    print(f"✓ 创建会话: {session.info.name}")

    # 在会话中使用 Agent
    response = await ai.chat_with_agent(
        "审查这段代码的质量：\n\n"
        "def process_data(data):\n"
        "    # TODO: 实现处理逻辑\n"
        "    pass",
        agent_config=AgentConfig(
            name="code_reviewer",
            system_prompt="你是代码审查专家，关注代码质量、安全性和可维护性。",
            max_steps=5,
        ),
    )

    print(f"代码审查结果:\n{response}\n")

    # 列出所有会话
    sessions = ai.list_sessions()
    print(f"当前会话: {[s.get('name', '未命名') for s in sessions]}")


async def example_8_agent_configurations():
    """示例 8: 各种 Agent 配置"""
    print("=" * 60)
    print("示例 8: 各种 Agent 配置")
    print("=" * 60)

    print("""
常用 Agent 配置示例:

1. 简单对话 Agent:
   AgentConfig(
       name="simple",
       system_prompt="你是一个友好的助手。",
       max_steps=3,
   )

2. 复杂任务 Agent:
   AgentConfig(
       name="complex",
       system_prompt="你是专家级 AI，能处理复杂的多步骤任务。",
       max_steps=50,
       max_execution_time=600,  # 10 分钟超时
       enable_thinking=True,
       retry_on_error=True,
       max_retries=3,
   )

3. 需要审批的 Agent:
   AgentConfig(
       name="cautious",
       system_prompt="你是谨慎的助手，重要操作会征得同意。",
       max_steps=20,
       require_approval=True,  # 危险操作需要审批
   )

4. Loop 配置:
   # 单轮对话
   LoopConfig(max_turns=1)

   # 多轮自动继续
   LoopConfig(
       max_turns=5,
       auto_continue=True,
       continue_threshold=0.8,
   )

   # 带检查点的多轮
   LoopConfig(
       max_turns=10,
       enable_checkpoint=True,
       checkpoint_frequency=5,
   )
    """)


def example_9_cli_usage():
    """示例 9: CLI 使用 Agent"""
    print("=" * 60)
    print("示例 9: CLI 使用 Agent")
    print("=" * 60)

    print("""
使用 CLI 运行 Agent:

1. 基础 Agent 模式:
   $ bitwiseai agent "分析这段代码并生成报告"

2. 流式输出:
   $ bitwiseai agent "讲一个故事" --stream

3. 在交互模式中使用:
   $ bitwiseai chat
   你: /agent 分析代码

4. 结合 RAG:
   $ bitwiseai agent "根据文档解释这个指令" --use-rag
    """)


async def example_10_complete_workflow():
    """示例 10: 完整工作流"""
    print("=" * 60)
    print("示例 10: 完整工作流")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 1. 创建会话
    session = await ai.new_session("项目分析")
    print(f"1. ✓ 创建会话: {session.info.name}")

    # 2. 加载相关 Skills
    skills = ai.list_skills()
    for skill in skills[:2]:
        ai.load_skill(skill)
    print(f"2. ✓ 已加载 Skills: {ai.list_skills(loaded_only=True)}")

    # 3. 创建检查点
    cp = ai.create_checkpoint("开始分析")
    print(f"3. ✓ 创建检查点: {cp}")

    # 4. 使用 Agent 执行任务
    response = await ai.chat_with_agent(
        "分析当前项目的结构，生成一份技术文档。",
        agent_config=AgentConfig(
            name="project_analyzer",
            system_prompt="你是项目分析专家。",
            max_steps=10,
        ),
        loop_config=LoopConfig(
            max_turns=2,
            auto_continue=True,
        ),
    )
    print(f"4. ✓ Agent 分析完成")

    print(f"\n分析结果:\n{response[:300]}...")

    # 5. 保存状态
    if hasattr(ai.enhanced_engine, 'save'):
        await ai.enhanced_engine.save()
        print("\n5. ✓ 状态已保存")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("BitwiseAI Agent 使用示例")
    print("=" * 60 + "\n")

    examples = [
        ("示例 1: 基础 Agent 使用", example_1_basic_agent),
        ("示例 2: 多轮对话 Agent", example_2_multi_turn_agent),
        ("示例 3: 流式 Agent 输出", example_3_streaming_agent),
        ("示例 4: 带工具的 Agent", example_4_agent_with_tools),
        ("示例 5: 启用思考模式", example_5_thinking_mode),
        ("示例 6: Agent 配合检查点", example_6_agent_with_checkpoints),
        ("示例 7: 独立会话中使用 Agent", example_7_session_with_agent),
        ("示例 8: 各种 Agent 配置", example_8_agent_configurations),
        ("示例 9: CLI 使用 Agent", example_9_cli_usage),
        ("示例 10: 完整工作流", example_10_complete_workflow),
    ]

    print("可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print()

    import sys
    if len(sys.argv) > 1:
        try:
            idx = int(sys.argv[1]) - 1
            if 0 <= idx < len(examples):
                _, func = examples[idx]
                if asyncio.iscoroutinefunction(func):
                    asyncio.run(func())
                else:
                    func()
            else:
                print(f"❌ 无效的示例编号: {sys.argv[1]}")
        except ValueError:
            print("❌ 请输入数字编号")
    else:
        # 默认运行配置说明
        asyncio.run(example_8_agent_configurations())


if __name__ == "__main__":
    main()
