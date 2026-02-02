#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BitwiseAI 完整工作流示例

演示如何组合使用所有功能完成复杂的实际任务
"""
import asyncio
import os
from bitwiseai import BitwiseAI
from bitwiseai.core import AgentConfig, LoopConfig


async def workflow_1_code_review_project():
    """工作流 1: 代码审查项目"""
    print("=" * 60)
    print("工作流 1: 代码审查项目")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 1. 创建专门会话
    session = await ai.new_session("代码审查 - Project X")
    print(f"1. ✓ 创建会话: {session.info.name}")

    # 2. 加载相关 Skills
    skills = [s for s in ai.list_skills() if 'asm' in s.lower() or 'error' in s.lower()]
    for skill in skills:
        ai.load_skill(skill)
    print(f"2. ✓ 已加载 Skills: {ai.list_skills(loaded_only=True)}")

    # 3. 加载项目文档
    ai.add_text("""
    Project X 代码规范
    ==================

    1. 所有函数必须有文档字符串
    2. 变量名使用 snake_case
    3. 每行不超过 80 字符
    4. 使用类型注解
    """)
    print("3. ✓ 已加载项目文档")

    # 4. 创建检查点
    cp = ai.create_checkpoint("审查开始")
    print(f"4. ✓ 创建检查点: {cp}")

    # 5. 使用 Agent 进行代码审查
    print("\n5. 使用 Agent 进行代码审查...")
    code = """
    def calculate(x,y):
        r=x+y
        return r
    """

    review = await ai.chat_with_agent(
        f"根据项目规范审查以下代码:\n\n{code}",
        agent_config=AgentConfig(
            name="code_reviewer",
            system_prompt="你是代码审查专家，严格按规范检查代码。",
            max_steps=8,
            enable_thinking=True,
        ),
    )

    print(f"   审查结果:\n{review}")

    # 6. 生成报告
    print("\n6. 生成审查报告...")
    await ai.enhanced_engine.save()
    print("   ✓ 审查会话已保存")


async def workflow_2_learn_hardware_instructions():
    """工作流 2: 学习硬件指令"""
    print("\n" + "=" * 60)
    print("工作流 2: 学习硬件指令")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 1. 创建学习会话
    session = await ai.new_session("硬件指令学习")
    print(f"1. ✓ 创建会话: {session.info.name}")

    # 2. 加载指令文档到 RAG
    instructions = {
        "MUL": "MUL: 乘法指令，格式 MUL Rd, Rn, Rm",
        "ADD": "ADD: 加法指令，格式 ADD Rd, Rn, Rm",
        "SUB": "SUB: 减法指令，格式 SUB Rd, Rn, Rm",
        "SHIFT": "SHIFT: 位移指令，支持 LSL/LSR/ASR/ROR",
    }
    for name, desc in instructions.items():
        ai.add_text(f"{name} 指令\n{desc}")
    print("2. ✓ 已加载指令文档")

    # 3. 第一轮：学习基本概念
    print("\n3. 学习基本概念...")
    q1 = "MUL 指令的格式是什么？"
    a1 = ai.chat(q1, use_rag=True)
    print(f"   Q: {q1}")
    print(f"   A: {a1[:100]}...")

    # 4. 第二轮：实践练习
    print("\n4. 实践练习...")
    q2 = "帮我写一个 MUL 指令的例子，将 R1 和 R2 相乘，结果存到 R3"
    a2 = ai.chat(q2, use_rag=True)
    print(f"   Q: {q2}")
    print(f"   A: {a2[:100]}...")

    # 5. 第三轮：使用工具验证
    print("\n5. 使用工具验证...")
    # 加载解析器 Skill
    if "asm_parser" in ai.list_skills():
        ai.load_skill("asm_parser")
        q3 = "验证指令 'MUL R3, R1, R2' 是否正确"
        a3 = ai.chat(q3, use_tools=True, use_rag=True)
        print(f"   Q: {q3}")
        print(f"   A: {a3[:100]}...")

    # 6. 创建学习总结检查点
    cp = ai.create_checkpoint("完成基础学习")
    print(f"\n6. ✓ 创建检查点: {cp}")


async def workflow_3_debug_with_checkpoints():
    """工作流 3: 使用检查点调试"""
    print("\n" + "=" * 60)
    print("工作流 3: 使用检查点调试")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 1. 创建调试会话
    session = await ai.new_session("调试会话")
    print(f"1. ✓ 创建会话: {session.info.name}")

    # 2. 初始实现
    print("\n2. 初始实现...")
    ai.chat("我要实现一个快速排序函数")
    ai.chat("使用 Python 实现，支持整数列表")
    cp1 = ai.create_checkpoint("需求定义")
    print(f"   ✓ 检查点 1: 需求定义")

    # 3. 第一版实现
    print("\n3. 第一版实现...")
    ai.chat("""
    第一版代码:
    def quicksort(arr):
        if len(arr) <= 1:
            return arr
        pivot = arr[0]
        left = [x for x in arr[1:] if x < pivot]
        right = [x for x in arr[1:] if x >= pivot]
        return quicksort(left) + [pivot] + quicksort(right)
    """)
    cp2 = ai.create_checkpoint("第一版完成")
    print(f"   ✓ 检查点 2: 第一版完成")

    # 4. 发现问题，需要优化
    print("\n4. 发现内存问题...")
    ai.chat("这个版本使用了太多内存，因为创建了新列表")
    ai.chat("需要原地排序的版本")

    # 回滚到需求定义，重新设计
    print("\n5. 回滚并重新设计...")
    ai.rollback_to_checkpoint(cp1)
    ai.chat("重新设计：使用原地排序，通过索引分区")
    cp3 = ai.create_checkpoint("重新设计完成")
    print(f"   ✓ 检查点 3: 重新设计完成")

    # 6. 第二版实现
    print("\n6. 第二版实现...")
    optimized = await ai.chat_with_agent(
        "实现原地快速排序",
        agent_config=AgentConfig(
            name="optimizer",
            max_steps=5,
        ),
    )
    print(f"   优化版本:\n{optimized[:150]}...")

    # 查看所有检查点
    checkpoints = ai.list_checkpoints()
    print(f"\n7. 本次调试使用了 {len(checkpoints)} 个检查点")


async def workflow_4_multi_project_management():
    """工作流 4: 多项目管理"""
    print("\n" + "=" * 60)
    print("工作流 4: 多项目管理")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建多个项目会话
    projects = {
        "Project Alpha": "Web 应用开发",
        "Project Beta": "数据分析脚本",
        "Project Gamma": "自动化工具",
    }

    sessions = {}
    print("\n1. 创建项目会话...")
    for name, desc in projects.items():
        session = await ai.new_session(name)
        ai.chat(f"项目描述: {desc}")
        sessions[name] = session
        print(f"   ✓ {name}: {desc}")

    # 在不同项目间切换工作
    print("\n2. 在项目间切换...")

    # Project Alpha: 技术选型
    await ai.switch_session(sessions["Project Alpha"].info.session_id)
    tech = await ai.chat_with_agent(
        "为 Web 应用推荐技术栈",
        agent_config=AgentConfig(name="architect", max_steps=5),
    )
    print(f"   [Alpha] 技术栈: {tech[:80]}...")

    # Project Beta: 数据处理
    await ai.switch_session(sessions["Project Beta"].info.session_id)
    data = ai.chat("使用 pandas 处理 CSV 文件，需要哪些步骤？", use_rag=True)
    print(f"   [Beta] 数据处理: {data[:80]}...")

    # Project Gamma: 任务调度
    await ai.switch_session(sessions["Project Gamma"].info.session_id)
    auto = ai.chat("如何用 Python 实现定时任务？", use_rag=True)
    print(f"   [Gamma] 自动化: {auto[:80]}...")

    # 总结所有项目
    print("\n3. 项目总结...")
    all_sessions = ai.list_sessions()
    print(f"   总共管理 {len(all_sessions)} 个项目会话")


async def workflow_5_document_generation():
    """工作流 5: 文档生成"""
    print("\n" + "=" * 60)
    print("工作流 5: 文档生成")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 1. 创建文档项目会话
    session = await ai.new_session("API 文档生成")
    print(f"1. ✓ 创建会话: {session.info.name}")

    # 2. 加载代码文档
    print("\n2. 加载代码文档...")
    api_docs = """
    API: 用户认证
    =============

    POST /api/auth/register
    - 描述: 用户注册
    - 参数: {username, password, email}
    - 返回: {user_id, token}

    POST /api/auth/login
    - 描述: 用户登录
    - 参数: {username, password}
    - 返回: {user_id, token, expires}

    POST /api/auth/logout
    - 描述: 用户登出
    - 参数: {token}
    - 返回: {success}
    """
    ai.add_text(api_docs)
    print("   ✓ 已加载 API 文档")

    # 3. 使用 Agent 生成用户文档
    print("\n3. 生成用户文档...")
    user_doc = await ai.chat_with_agent(
        "基于 API 文档生成用户使用指南，包含示例代码",
        agent_config=AgentConfig(
            name="tech_writer",
            system_prompt="你是技术文档专家，擅长生成清晰的用户指南。",
            max_steps=10,
            enable_thinking=True,
        ),
        loop_config=LoopConfig(
            max_turns=2,
            auto_continue=True,
        ),
    )

    print(f"\n生成的用户文档:\n{'='*60}")
    print(user_doc[:500] + "...")

    # 4. 创建检查点保存文档
    cp = ai.create_checkpoint("文档生成完成")
    print(f"\n4. ✓ 文档已保存到检查点: {cp}")


async def workflow_6_learning_path():
    """工作流 6: 学习路径规划"""
    print("\n" + "=" * 60)
    print("工作流 6: 学习路径规划")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 1. 创建学习会话
    session = await ai.new_session("Python 学习路径")
    print(f"1. ✓ 创建会话: {session.info.name}")

    # 2. 第一阶段：基础
    print("\n2. 第一阶段：Python 基础...")
    basic = await ai.chat_with_agent(
        "制定 Python 基础学习计划，适合零基础",
        agent_config=AgentConfig(
            name="teacher",
            system_prompt="你是 Python 老师，擅长制定学习计划。",
            max_steps=5,
        ),
    )
    print(f"   基础阶段:\n{basic[:200]}...")
    cp1 = ai.create_checkpoint("基础阶段完成")

    # 3. 第二阶段：进阶
    print("\n3. 第二阶段：Python 进阶...")
    advanced = await ai.chat_with_agent(
        "制定 Python 进阶学习计划，包含异步编程和装饰器",
        agent_config=AgentConfig(
            name="teacher",
            max_steps=5,
        ),
    )
    print(f"   进阶阶段:\n{advanced[:200]}...")
    cp2 = ai.create_checkpoint("进阶阶段完成")

    # 4. 第三阶段：实战
    print("\n4. 第三阶段：项目实战...")
    project = await ai.chat_with_agent(
        "推荐 3 个 Python 实战项目，巩固所学知识",
        agent_config=AgentConfig(
            name="mentor",
            max_steps=5,
        ),
    )
    print(f"   实战项目:\n{project[:200]}...")

    # 5. 总结学习路径
    print("\n5. 学习路径总结...")
    print("   ✓ 基础 → 进阶 → 实战")
    print(f"   ✓ 总计 {len(ai.list_checkpoints())} 个学习阶段")


def workflow_7_cli_usage():
    """工作流 7: CLI 使用演示"""
    print("\n" + "=" * 60)
    print("工作流 7: CLI 使用演示")
    print("=" * 60)

    print("""
完整 CLI 工作流演示
==================

场景: 使用命令行完成代码审查任务

1. 创建新的审查会话:
   $ bitwiseai session --new "代码审查"

2. 进入交互模式:
   $ bitwiseai chat

3. 加载相关 Skills:
   你: /skills
   你: /load asm_parser
   你: /load error-analyzer

4. 加载项目文档:
   你: /agent "加载项目文档到知识库"

5. 开始代码审查:
   你: /agent "审查 src/main.py 的代码质量"

6. 创建检查点:
   你: 这个版本不错，先保存
   AI: (创建检查点)

7. 继续优化:
   你: /agent "优化代码性能"

8. 如果不满意，回滚:
   你: /agent "回滚到上一个检查点"

9. 完成后保存:
   你: /agent "生成审查报告"

10. 查看所有会话:
    $ bitwiseai session --list

提示: 所有会话自动保存到 ~/.bitwiseai/sessions/
    """)


async def workflow_8_collaborative_debugging():
    """工作流 8: 协作调试"""
    print("\n" + "=" * 60)
    print("工作流 8: 协作调试")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 创建团队协作会话
    roles = [
        "前端开发",
        "后端开发",
        "测试工程师",
        "DevOps",
    ]

    sessions = {}
    print("\n1. 创建团队角色会话...")
    for role in roles:
        session = await ai.new_session(f"团队-{role}")
        sessions[role] = session
        print(f"   ✓ {role}")

    # 每个角色的任务
    print("\n2. 分配角色任务...")

    # 前端：UI 问题
    await ai.switch_session(sessions["前端开发"].info.session_id)
    frontend = await ai.chat_with_agent(
        "分析这个 React 组件的渲染性能问题",
        agent_config=AgentConfig(
            name="frontend_expert",
            max_steps=5,
        ),
    )
    print(f"   [前端] {frontend[:80]}...")

    # 后端：API 优化
    await ai.switch_session(sessions["后端开发"].info.session_id)
    backend = await ai.chat_with_agent(
        "优化这个 API 接口的响应时间",
        agent_config=AgentConfig(
            name="backend_expert",
            max_steps=5,
        ),
    )
    print(f"   [后端] {backend[:80]}...")

    # 测试：用例设计
    await ai.switch_session(sessions["测试工程师"].info.session_id)
    testing = ai.chat("设计 API 的测试用例", use_rag=True)
    print(f"   [测试] {testing[:80]}...")

    # DevOps：部署方案
    await ai.switch_session(sessions["DevOps"].info.session_id)
    devops = ai.chat("设计 CI/CD 流程", use_rag=True)
    print(f"   [DevOps] {devops[:80]}...")

    print("\n3. 团队协作完成!")
    print(f"   参与角色: {len(sessions)} 个")


async def main():
    """运行所有工作流示例"""
    print("\n" + "=" * 60)
    print("BitwiseAI 完整工作流示例")
    print("=" * 60 + "\n")

    workflows = [
        ("工作流 1: 代码审查项目", workflow_1_code_review_project),
        ("工作流 2: 学习硬件指令", workflow_2_learn_hardware_instructions),
        ("工作流 3: 使用检查点调试", workflow_3_debug_with_checkpoints),
        ("工作流 4: 多项目管理", workflow_4_multi_project_management),
        ("工作流 5: 文档生成", workflow_5_document_generation),
        ("工作流 6: 学习路径规划", workflow_6_learning_path),
        ("工作流 7: CLI 使用演示", workflow_7_cli_usage),
        ("工作流 8: 协作调试", workflow_8_collaborative_debugging),
    ]

    print("可用工作流:")
    for i, (name, _) in enumerate(workflows, 1):
        print(f"  {i}. {name}")
    print()

    import sys
    if len(sys.argv) > 1:
        try:
            idx = int(sys.argv[1]) - 1
            if 0 <= idx < len(workflows):
                _, func = workflows[idx]
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
            else:
                print(f"❌ 无效的工作流编号: {sys.argv[1]}")
        except ValueError:
            print("❌ 请输入数字编号")
    else:
        # 默认运行第一个工作流
        await workflow_1_code_review_project()


if __name__ == "__main__":
    asyncio.run(main())
