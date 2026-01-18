# -*- coding: utf-8 -*-
"""
BitwiseAI 基础使用示例

展示 BitwiseAI 的基本功能：
1. 初始化 BitwiseAI
2. 基础对话（不使用 RAG）
3. 查看已加载的 Skills
4. 使用工具调用
"""

from bitwiseai import BitwiseAI


def main():
    """基础使用示例"""
    print("=" * 60)
    print("BitwiseAI 基础使用示例")
    print("=" * 60)
    print()
    
    # 1. 初始化 BitwiseAI
    # 默认使用 ~/.bitwiseai/config.json 配置文件
    # 如果配置文件不存在，请先运行: bitwiseai --generate-config
    print("1. 初始化 BitwiseAI...")
    try:
        ai = BitwiseAI()
    except ValueError as e:
        print(f"❌ 初始化失败: {e}")
        print("💡 提示: 请先运行 'bitwiseai --generate-config' 生成配置文件")
        return
    print("✓ 初始化成功\n")
    
    # 2. 基础对话（不使用 RAG）
    print("2. 基础对话示例（不使用 RAG）")
    print("-" * 60)
    query = "你好，请介绍一下你自己"
    response = ai.chat(query, use_rag=False, use_tools=False)
    print(f"问题: {query}")
    print(f"回答: {response}\n")
    
    # 3. 查看已加载的 Skills
    print("3. 查看已加载的 Skills")
    print("-" * 60)
    loaded_skills = ai.list_skills(loaded_only=True)
    print(f"已加载的 Skills ({len(loaded_skills)} 个):")
    for skill_name in loaded_skills:
        skill = ai.skill_manager.get_skill(skill_name)
        if skill:
            print(f"  - {skill_name}: {skill.description or '无描述'}")
    print()
    
    # 4. 查看可用工具
    print("4. 查看可用工具")
    print("-" * 60)
    tools = ai.list_tools()
    print(f"可用工具 ({len(tools)} 个):")
    for tool_name in tools:
        print(f"  - {tool_name}")
    print()
    
    # 5. 使用工具调用（如果工具可用）
    if tools:
        print("5. 工具调用示例")
        print("-" * 60)
        # 尝试使用工具进行对话
        query_with_tool = "将十六进制数 0xFF 转换为十进制"
        print(f"问题: {query_with_tool}")
        response = ai.chat(query_with_tool, use_rag=False, use_tools=True)
        print(f"回答: {response}\n")
    
    # 6. 流式对话示例
    print("6. 流式对话示例")
    print("-" * 60)
    query = "请用一句话介绍 BitwiseAI"
    print(f"问题: {query}")
    print("回答: ", end="", flush=True)
    for chunk in ai.chat_stream(query, use_rag=False, use_tools=False):
        print(chunk, end="", flush=True)
    print("\n")
    
    print("=" * 60)
    print("基础使用示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
