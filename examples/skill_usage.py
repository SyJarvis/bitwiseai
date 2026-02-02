#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BitwiseAI Skill 使用示例

演示如何使用和管理 Skills
"""
import os
from bitwiseai import BitwiseAI


def example_1_list_skills():
    """示例 1: 列出所有 Skills"""
    print("=" * 60)
    print("示例 1: 列出所有 Skills")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 列出所有可用的 Skills
    skills = ai.list_skills()
    print(f"可用 Skills ({len(skills)} 个):")
    for i, skill in enumerate(skills, 1):
        # 获取技能详细信息
        skill_obj = ai.skill_manager.get_skill(skill)
        if skill_obj:
            status = "✅" if skill_obj.loaded else "⏸️ "
            desc = skill_obj.description or "无描述"
            print(f"  {i}. {status} {skill} - {desc}")

    # 列出已加载的 Skills
    loaded = ai.list_skills(loaded_only=True)
    print(f"\n已加载: {len(loaded)} 个")


def example_2_load_unload_skills():
    """示例 2: 加载和卸载 Skills"""
    print("\n" + "=" * 60)
    print("示例 2: 加载和卸载 Skills")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 获取所有 Skills
    skills = ai.list_skills()
    if not skills:
        print("⚠️  没有可用的 Skills")
        return

    # 加载第一个 Skill
    skill_name = skills[0]
    print(f"加载 Skill: {skill_name}")
    success = ai.load_skill(skill_name)

    if success:
        print(f"✅ Skill '{skill_name}' 加载成功")

        # 查看技能的工具
        skill_obj = ai.skill_manager.get_skill(skill_name)
        if skill_obj and skill_obj.tools:
            print(f"\n可用工具 ({len(skill_obj.tools)} 个):")
            for tool_name in skill_obj.tools.keys():
                print(f"  - {tool_name}")

        # 卸载 Skill
        print(f"\n卸载 Skill: {skill_name}")
        ai.unload_skill(skill_name)
        print(f"✅ Skill '{skill_name}' 已卸载")
    else:
        print(f"❌ Skill '{skill_name}' 加载失败")


def example_3_use_skill_tools():
    """示例 3: 使用 Skill 工具"""
    print("\n" + "=" * 60)
    print("示例 3: 使用 Skill 工具")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 加载所有 Skills
    skills = ai.list_skills()
    for skill in skills:
        ai.load_skill(skill)

    print(f"已加载 {len(ai.list_skills(loaded_only=True))} 个 Skills")

    # 使用工具进行对话
    queries = [
        "将 0xFF 转换为十进制",
        "将 255 转换为十六进制",
        "计算 0x10 + 0x20",
    ]

    for query in queries:
        print(f"\n问题: {query}")
        response = ai.chat(query, use_tools=True)
        print(f"回答: {response[:100]}...")


def example_4_search_skills():
    """示例 4: 搜索相关 Skills"""
    print("\n" + "=" * 60)
    print("示例 4: 搜索相关 Skills")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 搜索不同的关键词
    keywords = ["代码", "转换", "分析"]

    for keyword in keywords:
        print(f"\n搜索 '{keyword}':")
        results = ai.search_skills(keyword, top_k=3)

        if results:
            for i, result in enumerate(results, 1):
                name = result.get("skill_name", "未知")
                score = result.get("score", 0.0)
                desc = result.get("description", "无描述")
                print(f"  {i}. {name} (相似度: {score:.4f})")
                print(f"     {desc}")
        else:
            print("  未找到相关 Skills")


def example_5_add_external_skills():
    """示例 5: 添加外部 Skills 目录"""
    print("\n" + "=" * 60)
    print("示例 5: 添加外部 Skills 目录")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 添加外部 Skills 目录
    external_dir = os.path.expanduser("~/.bitwiseai/skills")
    print(f"添加外部目录: {external_dir}")

    success = ai.add_skills_directory(external_dir)
    if success:
        print(f"✅ 已添加目录: {external_dir}")

        # 重新扫描 Skills
        ai.skill_manager.scan_skills()
        skills = ai.list_skills()
        print(f"现在有 {len(skills)} 个可用 Skills")
    else:
        print(f"❌ 添加目录失败: {external_dir}")


def example_6_skill_with_rag():
    """示例 6: Skill 配合 RAG 使用"""
    print("\n" + "=" * 60)
    print("示例 6: Skill 配合 RAG 使用")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 加载 Skills
    skills = ai.list_skills()
    for skill in skills[:2]:
        ai.load_skill(skill)

    print(f"已加载 Skills: {ai.list_skills(loaded_only=True)}")

    # 同时使用 RAG 和工具
    query = "根据指令文档解释 MUL，并计算 0x10 * 0x20"
    print(f"\n问题: {query}")

    response = ai.chat(query, use_rag=True, use_tools=True)
    print(f"回答:\n{response[:200]}...")


def example_7_create_custom_skill():
    """示例 7: 创建自定义 Skill"""
    print("\n" + "=" * 60)
    print("示例 7: 创建自定义 Skill")
    print("=" * 60)

    print("""
创建自定义 Skill 的步骤:

1. 创建 Skill 目录结构:

   ~/.bitwiseai/skills/my_skill/
   ├── SKILL.md          # Skill 定义文件
   └── scripts/
       └── tools.py      # 工具实现

2. 编写 SKILL.md:

   ---
   name: my_skill
   description: 我的自定义技能
   version: 1.0.0
   author: Your Name
   ---

   # My Skill

   这是一个自定义技能，可以...

   ## 使用方法

   直接告诉 AI 你需要什么，它会自动调用相关工具。

3. 编写 tools.py:

   from bitwiseai.core import tool

   @tool
   def my_tool(param: str) -> str:
       \"\"\"工具描述\"\"\"
       result = do_something(param)
       return result

4. 重新扫描并加载:

   ai = BitwiseAI(use_enhanced=True)
   ai.add_skills_directory("~/.bitwiseai/skills")
   ai.skill_manager.scan_skills()
   ai.load_skill("my_skill")

提示: 运行 python -m bitwiseai.core.skill_parser 来验证 Skill 定义
    """)


def example_8_skill_metadata():
    """示例 8: 查看 Skill 元数据"""
    print("\n" + "=" * 60)
    print("示例 8: 查看 Skill 元数据")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    skills = ai.list_skills()
    for skill_name in skills[:3]:
        metadata = ai.skill_manager.get_skill_metadata(skill_name)
        if metadata:
            print(f"\nSkill: {skill_name}")
            print(f"  描述: {metadata.get('description', '无')}")
            print(f"  版本: {metadata.get('version', '未知')}")
            print(f"  作者: {metadata.get('author', '未知')}")

            # 检查是否有工具
            skill_obj = ai.skill_manager.get_skill(skill_name)
            if skill_obj:
                n_tools = len(skill_obj.tools) if skill_obj.tools else 0
                print(f"  工具数: {n_tools}")


def example_9_skill_with_agent():
    """示例 9: Skill 配合 Agent 使用"""
    print("\n" + "=" * 60)
    print("示例 9: Skill 配合 Agent 使用")
    print("=" * 60)

    import asyncio
    from bitwiseai.core import AgentConfig

    async def run():
        ai = BitwiseAI(use_enhanced=True)

        # 加载 Skills
        skills = ai.list_skills()
        for skill in skills[:3]:
            ai.load_skill(skill)

        print(f"已加载 Skills: {ai.list_skills(loaded_only=True)}")

        # Agent 会自动使用可用的工具
        response = await ai.chat_with_agent(
            "帮我完成以下任务:\n"
            "1. 转换 0x100 到十进制\n"
            "2. 分析这段代码: print('hello')\n"
            "3. 计算结果加 1",
            agent_config=AgentConfig(
                name="multi_tool",
                system_prompt="你是工具使用专家，会熟练使用各种工具完成任务。",
                max_steps=10,
            ),
        )

        print(f"\nAgent 完成的任务:\n{response[:300]}...")

    asyncio.run(run())


def example_10_builtin_skills():
    """示例 10: 内置 Skills 介绍"""
    print("\n" + "=" * 60)
    print("示例 10: 内置 Skills 介绍")
    print("=" * 60)

    print("""
BitwiseAI 内置 Skills
====================

1. asm_parser - 汇编解析器
   - 功能: 解析汇编代码
   - 工具: parse_asm, extract_instructions

2. error-analyzer - 错误分析器
   - 功能: 分析错误日志
   - 工具: parse_error, analyze_error

3. hex_converter - 十六进制转换器
   - 功能: 十六进制/十进制转换
   - 工具: hex_to_dec, dec_to_hex

4. interactive-fiction-learning - 互动小说学习
   - 功能: 互动式学习体验
   - 工具: 多种交互工具

查看所有可用 Skills:
  python -c "from bitwiseai import BitwiseAI; ai = BitwiseAI(); print(ai.list_skills())"

查看 Skill 详情:
  cat bitwiseai/skills/<skill_name>/SKILL.md
    """)


def example_11_cli_skill_management():
    """示例 11: CLI Skill 管理"""
    print("\n" + "=" * 60)
    print("示例 11: CLI Skill 管理")
    print("=" * 60)

    print("""
使用 CLI 管理 Skills:

1. 列出所有 Skills:
   $ bitwiseai skill --list

2. 显示详细信息:
   $ bitwiseai skill --list --verbose

3. 只显示已加载的:
   $ bitwiseai skill --list --loaded-only

4. 加载 Skill:
   $ bitwiseai skill --load hex_converter

5. 卸载 Skill:
   $ bitwiseai skill --unload hex_converter

6. 搜索 Skills:
   $ bitwiseai skill --search "转换" --top-k 5

7. 添加外部目录:
   $ bitwiseai skill --add-dir ~/.bitwiseai/skills

8. 在交互模式中使用:
   $ bitwiseai chat
   你: /skills         # 列出 Skills
   你: /load <skill>   # 加载 Skill
   你: /unload <skill> # 卸载 Skill
    """)


def example_12_complete_workflow():
    """示例 12: 完整 Skill 工作流"""
    print("\n" + "=" * 60)
    print("示例 12: 完整 Skill 工作流")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    print("场景: 设置开发环境并使用相关工具\n")

    # 1. 添加外部 Skills
    print("1. 添加外部 Skills 目录")
    external_dir = os.path.expanduser("~/.bitwiseai/skills")
    ai.add_skills_directory(external_dir)
    print(f"   ✓ 已添加: {external_dir}")

    # 2. 扫描所有 Skills
    print("\n2. 扫描所有 Skills")
    ai.skill_manager.scan_skills()
    skills = ai.list_skills()
    print(f"   ✓ 发现 {len(skills)} 个 Skills")

    # 3. 加载相关 Skills
    print("\n3. 加载开发相关 Skills")
    dev_skills = [s for s in skills if any(
        keyword in s.lower()
        for keyword in ['asm', 'error', 'hex', 'code']
    )]
    for skill in dev_skills[:3]:
        ai.load_skill(skill)
        print(f"   ✓ 已加载: {skill}")

    # 4. 使用工具完成任务
    print("\n4. 使用工具完成任务")
    task = "解析汇编代码 'ADD R1, R2, R3' 并转换结果到十六进制"
    print(f"   任务: {task}")

    response = ai.chat(task, use_tools=True)
    print(f"   结果: {response[:150]}...")

    # 5. 搜索更多相关 Skills
    print("\n5. 搜索相关 Skills")
    results = ai.search_skills("分析", top_k=3)
    print(f"   找到 {len(results)} 个相关 Skills")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("BitwiseAI Skill 使用示例")
    print("=" * 60 + "\n")

    examples = [
        ("示例 1: 列出所有 Skills", example_1_list_skills),
        ("示例 2: 加载和卸载 Skills", example_2_load_unload_skills),
        ("示例 3: 使用 Skill 工具", example_3_use_skill_tools),
        ("示例 4: 搜索相关 Skills", example_4_search_skills),
        ("示例 5: 添加外部目录", example_5_add_external_skills),
        ("示例 6: Skill 配合 RAG", example_6_skill_with_rag),
        ("示例 7: 创建自定义 Skill", example_7_create_custom_skill),
        ("示例 8: 查看 Skill 元数据", example_8_skill_metadata),
        ("示例 9: Skill 配合 Agent", example_9_skill_with_agent),
        ("示例 10: 内置 Skills 介绍", example_10_builtin_skills),
        ("示例 11: CLI Skill 管理", example_11_cli_skill_management),
        ("示例 12: 完整工作流", example_12_complete_workflow),
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
                func()
            else:
                print(f"❌ 无效的示例编号: {sys.argv[1]}")
        except ValueError:
            print("❌ 请输入数字编号")
    else:
        # 默认运行第一个示例
        example_1_list_skills()


if __name__ == "__main__":
    main()
