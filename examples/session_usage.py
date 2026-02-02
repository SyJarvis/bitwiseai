#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BitwiseAI 会话管理示例

演示如何使用多会话功能管理工作流
"""
import asyncio
from bitwiseai import BitwiseAI


async def example_1_create_sessions():
    """示例 1: 创建多个会话"""
    print("=" * 60)
    print("示例 1: 创建多个会话")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建不同的会话用于不同任务
    session1 = await ai.new_session("代码审查")
    print(f"✓ 创建会话 1: {session1.info.name} (ID: {session1.info.session_id[:16]}...)")

    # 在会话 1 中对话
    ai.chat("我们正在审查一个 Python 项目")
    print("  - 会话 1: 开始代码审查讨论")

    # 创建第二个会话
    session2 = await ai.new_session("文档编写")
    print(f"✓ 创建会话 2: {session2.info.name} (ID: {session2.info.session_id[:16]}...)")

    # 在会话 2 中对话
    ai.chat("我们需要编写 API 文档")
    print("  - 会话 2: 开始文档编写讨论")

    # 创建第三个会话
    session3 = await ai.new_session("Bug 追踪")
    print(f"✓ 创建会话 3: {session3.info.name} (ID: {session3.info.session_id[:16]}...)")

    ai.chat("列表当前已知的 Bug")
    print("  - 会话 3: 开始 Bug 追踪讨论")

    # 列出所有会话
    sessions = ai.list_sessions()
    print(f"\n总共有 {len(sessions)} 个会话:")
    for i, s in enumerate(sessions, 1):
        print(f"  {i}. {s.get('name', '未命名')} ({s.get('message_count', 0)} 条消息)")


async def example_2_switch_sessions():
    """示例 2: 切换会话"""
    print("=" * 60)
    print("示例 2: 切换会话")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建两个会话
    session_a = await ai.new_session("项目 A")
    session_b = await ai.new_session("项目 B")

    print(f"✓ 创建: {session_a.info.name}")
    print(f"✓ 创建: {session_b.info.name}")

    # 在项目 A 中对话
    await ai.switch_session(session_a.info.session_id)
    print(f"\n切换到: {session_a.info.name}")
    ai.chat("项目 A 使用 React 框架")
    print("  - 记录: 项目 A 使用 React")

    # 在项目 B 中对话
    await ai.switch_session(session_b.info.session_id)
    print(f"\n切换到: {session_b.info.name}")
    ai.chat("项目 B 使用 Vue 框架")
    print("  - 记录: 项目 B 使用 Vue")

    # 切回项目 A
    await ai.switch_session(session_a.info.session_id)
    print(f"\n切换回: {session_a.info.name}")
    response = ai.chat("我刚才说项目 A 用什么框架？")
    print(f"  - AI 记得: {response[:50]}...")


async def example_3_session_with_checkpoints():
    """示例 3: 会话配合检查点使用"""
    print("=" * 60)
    print("示例 3: 会话配合检查点使用")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建会话
    session = await ai.new_session("需求分析")
    print(f"✓ 创建会话: {session.info.name}")

    # 进行一些对话
    ai.chat("用户需要一个登录功能")
    print("  - 需求 1: 登录功能")

    ai.chat("需要支持邮箱和手机号登录")
    print("  - 需求 2: 邮箱和手机号登录")

    # 创建检查点
    cp1 = ai.create_checkpoint("基础需求完成")
    print(f"✓ 创建检查点 1: {cp1}")

    # 继续添加需求
    ai.chat("还需要支持第三方登录（微信、QQ）")
    print("  - 需求 3: 第三方登录")

    # 发现需要修改，回滚到检查点
    print("\n发现第三方登录太复杂，决定先不做...")
    ai.rollback_to_checkpoint(cp1)
    print("✓ 回滚到检查点 1")

    # 继续其他讨论
    ai.chat("先实现基础的邮箱和手机号登录即可")
    print("  - 继续讨论: 基础登录实现")


async def example_4_session_lifecycle():
    """示例 4: 会话生命周期管理"""
    print("=" * 60)
    print("示例 4: 会话生命周期管理")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建会话
    session = await ai.new_session("临时讨论")
    print(f"✓ 创建会话: {session.info.name}")

    # 进行一些对话
    ai.chat("讨论一些临时想法")
    ai.chat("想法 1: ...")
    ai.chat("想法 2: ...")

    sessions = ai.list_sessions()
    print(f"\n当前会话数: {len(sessions)}")

    # 删除不需要的会话
    session_id = session.info.session_id
    success = await ai.delete_session(session_id)
    if success:
        print(f"✓ 已删除会话: {session.info.name}")

    sessions = ai.list_sessions()
    print(f"剩余会话数: {len(sessions)}")


async def example_5_session_persistence():
    """示例 5: 会话持久化"""
    print("=" * 60)
    print("示例 5: 会话持久化")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建会话并进行对话
    session = await ai.new_session("持久化测试")
    print(f"✓ 创建会话: {session.info.name}")

    # 模拟一系列对话
    conversations = [
        "我叫 Alice",
        "我是一名软件工程师",
        "我擅长 Python 和 JavaScript",
        "我正在学习 Go 语言",
    ]

    for conv in conversations:
        ai.chat(conv)
        print(f"  - 记录: {conv}")

    # 保存会话状态
    if hasattr(ai.enhanced_engine, 'save'):
        await ai.enhanced_engine.save()
        print("\n✓ 会话状态已保存到磁盘")

    # 会话数据保存在 ~/.bitwiseai/sessions/ 目录
    print(f"\n会话文件位置: ~/.bitwiseai/sessions/{session.info.session_id}.jsonl")

    # 下次启动时可以恢复会话
    print("\n提示: 下次启动 BitwiseAI 时，这些会话会自动加载")


async def example_6_session_for_different_contexts():
    """示例 6: 使用会话隔离不同上下文"""
    print("=" * 60)
    print("示例 6: 使用会话隔离不同上下文")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建不同主题的会话
    contexts = [
        ("技术讨论", "我们正在讨论微服务架构"),
        ("产品规划", "下一版本需要添加用户反馈功能"),
        ("团队管理", "下周要进行代码审查培训"),
    ]

    sessions = {}
    for name, initial_message in contexts:
        session = await ai.new_session(name)
        ai.chat(initial_message)
        sessions[name] = session
        print(f"✓ 创建会话 '{name}': {initial_message}")

    # 在不同上下文之间切换
    print("\n在不同上下文间切换:")

    await ai.switch_session(sessions["技术讨论"].info.session_id)
    response = ai.chat("微服务的优势是什么？")
    print(f"  [技术讨论] AI: {response[:60]}...")

    await ai.switch_session(sessions["产品规划"].info.session_id)
    response = ai.chat("用户反馈功能应该包含哪些内容？")
    print(f"  [产品规划] AI: {response[:60]}...")

    await ai.switch_session(sessions["团队管理"].info.session_id)
    response = ai.chat("代码审查需要注意什么？")
    print(f"  [团队管理] AI: {response[:60]}...")


async def example_7_cli_session_management():
    """示例 7: CLI 会话管理"""
    print("=" * 60)
    print("示例 7: CLI 会话管理")
    print("=" * 60)

    print("""
使用 CLI 管理会话:

1. 列出所有会话:
   $ bitwiseai session --list

2. 创建新会话:
   $ bitwiseai session --new "项目讨论"

3. 切换会话:
   $ bitwiseai session --switch <session-id>

4. 删除会话:
   $ bitwiseai session --delete <session-id>

5. 在交互模式中使用:
   $ bitwiseai chat
   你: /sessions        # 列出会话
   你: /new 项目 A       # 创建新会话
   你: /switch <id>      # 切换会话

提示: 会话 ID 只需要输入前几位即可，系统会自动匹配
    """)


async def example_8_session_with_agent():
    """示例 8: 在会话中使用 Agent"""
    print("=" * 60)
    print("示例 8: 在会话中使用 Agent")
    print("=" * 60)

    from bitwiseai.core import AgentConfig

    ai = BitwiseAI(use_enhanced=True)

    # 创建专门用于代码生成的会话
    session = await ai.new_session("代码生成")
    print(f"✓ 创建会话: {session.info.name}")

    # 在会话中使用 Agent
    response = await ai.chat_with_agent(
        "帮我生成一个用户认证类的代码",
        agent_config=AgentConfig(
            name="code_generator",
            system_prompt="你是代码生成专家，擅长编写高质量的代码。",
            max_steps=8,
        ),
    )

    print(f"\n生成的代码:\n{response[:300]}...")

    # 在同一个会话中继续讨论
    ai.chat("刚才生成的代码很好，但需要添加密码加密")
    print("\n继续优化代码...")

    # 查看会话信息
    sessions = ai.list_sessions()
    current = [s for s in sessions if s.get('name') == '代码生成']
    if current:
        print(f"\n会话 '{current[0]['name']}' 中有 {current[0].get('message_count', 0)} 条消息")


async def example_9_complete_workflow():
    """示例 9: 完整工作流"""
    print("=" * 60)
    print("示例 9: 完整工作流")
    print("=" * 60)

    from bitwiseai.core import AgentConfig, LoopConfig

    ai = BitwiseAI(use_enhanced=True)

    print("场景: 管理多个项目的讨论\n")

    # 项目 1: 代码审查
    session1 = await ai.new_session("项目 A - 代码审查")
    print(f"1. ✓ 创建: {session1.info.name}")

    await ai.switch_session(session1.info.session_id)
    ai.chat("这是项目 A 的代码仓库")
    cp1 = ai.create_checkpoint("项目初始化")

    # 在项目 A 中使用 Agent 进行代码审查
    review = await ai.chat_with_agent(
        "审查 src/main.py 的代码质量",
        agent_config=AgentConfig(
            name="reviewer",
            max_steps=5,
        ),
    )
    print(f"   代码审查完成: {review[:100]}...")

    # 项目 2: 架构设计
    session2 = await ai.new_session("项目 B - 架构设计")
    print(f"2. ✓ 创建: {session2.info.name}")

    await ai.switch_session(session2.info.session_id)
    ai.chat("项目 B 需要设计微服务架构")
    cp2 = ai.create_checkpoint("需求收集完成")

    # 在项目 B 中使用 Agent 进行架构设计
    design = await ai.chat_with_agent(
        "设计一个用户服务的微服务架构",
        agent_config=AgentConfig(
            name="architect",
            max_steps=8,
        ),
        loop_config=LoopConfig(max_turns=2),
    )
    print(f"   架构设计完成: {design[:100]}...")

    # 总结
    sessions = ai.list_sessions()
    print(f"\n3. 总共管理 {len(sessions)} 个会话")
    print("4. 所有会话状态已自动保存")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("BitwiseAI 会话管理示例")
    print("=" * 60 + "\n")

    examples = [
        ("示例 1: 创建多个会话", example_1_create_sessions),
        ("示例 2: 切换会话", example_2_switch_sessions),
        ("示例 3: 会话配合检查点", example_3_session_with_checkpoints),
        ("示例 4: 会话生命周期管理", example_4_session_lifecycle),
        ("示例 5: 会话持久化", example_5_session_persistence),
        ("示例 6: 隔离不同上下文", example_6_session_for_different_contexts),
        ("示例 7: CLI 会话管理", example_7_cli_session_management),
        ("示例 8: 在会话中使用 Agent", example_8_session_with_agent),
        ("示例 9: 完整工作流", example_9_complete_workflow),
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
        # 默认运行第一个示例
        asyncio.run(example_1_create_sessions())


if __name__ == "__main__":
    main()
