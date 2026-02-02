#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BitwiseAI 基础使用示例

演示最简单的使用方式，适合初学者
"""
import os
from bitwiseai import BitwiseAI


def example_1_simple_chat():
    """示例 1: 最简单的对话"""
    print("=" * 60)
    print("示例 1: 最简单的对话")
    print("=" * 60)

    # 初始化（需要先设置环境变量）
    ai = BitwiseAI()

    # 简单对话
    response = ai.chat("什么是 MUL 指令？")
    print(f"AI 回答:\n{response}\n")


def example_2_stream_chat():
    """示例 2: 流式对话"""
    print("=" * 60)
    print("示例 2: 流式对话")
    print("=" * 60)

    ai = BitwiseAI()

    # 流式输出
    print("AI 回答: ", end="", flush=True)
    for token in ai.chat_stream("介绍一下你自己"):
        print(token, end="", flush=True)
    print("\n")


def example_3_with_rag():
    """示例 3: 使用 RAG 检索"""
    print("=" * 60)
    print("示例 3: 使用 RAG 检索")
    print("=" * 60)

    ai = BitwiseAI()

    # 首先加载一些文档
    docs_path = os.path.expanduser("~/Documents/hardware_specs")
    if os.path.exists(docs_path):
        ai.load_documents(docs_path, skip_duplicates=True)
        print(f"✓ 已加载文档: {docs_path}")
    else:
        print("⚠️  文档路径不存在，跳过加载")

    # 使用 RAG 模式对话
    response = ai.chat(
        "PE 指令有哪些寄存器约束？",
        use_rag=True
    )
    print(f"RAG 回答:\n{response}\n")


def example_4_with_skills():
    """示例 4: 使用 Skills"""
    print("=" * 60)
    print("示例 4: 使用 Skills")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 列出所有可用的 Skills
    skills = ai.list_skills()
    print(f"可用 Skills ({len(skills)} 个):")
    for skill in skills:
        print(f"  - {skill}")

    # 加载一个 Skill
    if skills:
        skill_name = skills[0]
        success = ai.load_skill(skill_name)
        if success:
            print(f"\n✓ 已加载: {skill_name}")

            # 使用工具进行对话
            response = ai.chat(
                "帮我转换 0xFF 到十进制",
                use_tools=True
            )
            print(f"回答:\n{response}\n")


def example_5_with_history():
    """示例 5: 带历史记录的对话"""
    print("=" * 60)
    print("示例 5: 带历史记录的对话")
    print("=" * 60)

    ai = BitwiseAI()

    # 构建对话历史
    history = [
        {"role": "user", "content": "我叫 Alice"},
        {"role": "assistant", "content": "你好 Alice！很高兴认识你。"},
        {"role": "user", "content": "我是一名 Python 开发者"},
        {"role": "assistant", "content": "太好了！Python 是一门很棒的语言。"},
    ]

    # 基于历史继续对话
    response = ai.chat(
        "我刚才说我叫什么名字？",
        history=history
    )
    print(f"回答:\n{response}\n")


def example_6_configuration():
    """示例 6: 使用自定义配置"""
    print("=" * 60)
    print("示例 6: 使用自定义配置")
    print("=" * 60)

    # 方式 1: 使用环境变量（推荐）
    print("""
方式 1: 使用环境变量（推荐）
--------------------------------
在 ~/.bashrc 或 ~/.zshrc 中添加:

    export LLM_API_KEY="sk-xxx"
    export LLM_BASE_URL="https://api.openai.com/v1"
    export LLM_MODEL="gpt-4o-mini"

    export EMBEDDING_API_KEY="sk-xxx"
    export EMBEDDING_BASE_URL="https://api.openai.com/v1"
    export EMBEDDING_MODEL="text-embedding-3-small"
    """)

    # 方式 2: 使用配置文件
    print("""
方式 2: 使用配置文件
--------------------------------
使用 CLI 生成配置:

    bitwiseai config --force

然后编辑 ~/.bitwiseai/config.json
    """)

    # 方式 3: 代码中指定配置路径
    print("""
方式 3: 代码中指定配置路径
--------------------------------
    ai = BitwiseAI(config_path="./my_config.json")
    """)


def example_7_error_handling():
    """示例 7: 错误处理"""
    print("=" * 60)
    print("示例 7: 错误处理")
    print("=" * 60)

    try:
        # 尝试初始化（可能缺少配置）
        ai = BitwiseAI()

        # 尝试对话
        response = ai.chat("你好")
        print(f"回答: {response}")

    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("\n请检查:")
        print("  1. 是否设置了 LLM_API_KEY 环境变量")
        print("  2. 是否设置了 LLM_BASE_URL 环境变量")
        print("  3. 或者运行: bitwiseai config --force")

    except Exception as e:
        print(f"❌ 其他错误: {e}")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("BitwiseAI 基础使用示例")
    print("=" * 60 + "\n")

    examples = [
        ("示例 1: 最简单的对话", example_1_simple_chat),
        ("示例 2: 流式对话", example_2_stream_chat),
        ("示例 3: 使用 RAG 检索", example_3_with_rag),
        ("示例 4: 使用 Skills", example_4_with_skills),
        ("示例 5: 带历史记录的对话", example_5_with_history),
        ("示例 6: 配置说明", example_6_configuration),
        ("示例 7: 错误处理", example_7_error_handling),
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
        # 默认运行配置说明
        example_6_configuration()


if __name__ == "__main__":
    main()
