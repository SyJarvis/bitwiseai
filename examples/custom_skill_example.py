# -*- coding: utf-8 -*-
"""
BitwiseAI 自定义 Skill 示例

展示如何创建和使用自定义 Skill：
1. 创建自定义 Skill 目录结构
2. 定义 Skill 配置和工具
3. 加载和使用自定义 Skill
4. 在对话中使用自定义工具
"""

import os
import sys
import json
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bitwiseai import BitwiseAI


def create_custom_skill():
    """创建示例自定义 Skill"""
    skills_dir = project_root / "bitwiseai" / "skills"
    skill_name = "calculator"
    skill_dir = skills_dir / skill_name
    
    # 创建 Skill 目录
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 创建 __init__.py
    init_file = skill_dir / "__init__.py"
    init_file.write_text("# Calculator Skill\n", encoding='utf-8')
    
    # 2. 创建 skill.json
    skill_config = {
        "name": "calculator",
        "version": "1.0.0",
        "description": "简单的计算器工具，支持基本数学运算",
        "author": "BitwiseAI Examples",
        "tools": [
            {
                "name": "add",
                "module": "tools",
                "function": "add",
                "description": "执行加法运算，计算两个数的和",
                "parameters": {
                    "a": {
                        "type": "number",
                        "description": "第一个加数"
                    },
                    "b": {
                        "type": "number",
                        "description": "第二个加数"
                    }
                }
            },
            {
                "name": "multiply",
                "module": "tools",
                "function": "multiply",
                "description": "执行乘法运算，计算两个数的乘积",
                "parameters": {
                    "a": {
                        "type": "number",
                        "description": "第一个乘数"
                    },
                    "b": {
                        "type": "number",
                        "description": "第二个乘数"
                    }
                }
            },
            {
                "name": "power",
                "module": "tools",
                "function": "power",
                "description": "计算幂运算，计算 a 的 b 次方",
                "parameters": {
                    "a": {
                        "type": "number",
                        "description": "底数"
                    },
                    "b": {
                        "type": "number",
                        "description": "指数"
                    }
                }
            }
        ],
        "dependencies": [],
        "resources": [],
        "hooks": {
            "on_load": None,
            "on_unload": None
        }
    }
    
    skill_json = skill_dir / "skill.json"
    with open(skill_json, 'w', encoding='utf-8') as f:
        json.dump(skill_config, f, indent=2, ensure_ascii=False)
    
    # 3. 创建 tools.py
    tools_code = '''# -*- coding: utf-8 -*-
"""
Calculator Skill 工具实现
"""

def add(a: float, b: float) -> float:
    """
    执行加法运算
    
    Args:
        a: 第一个加数
        b: 第二个加数
    
    Returns:
        两个数的和
    """
    return a + b


def multiply(a: float, b: float) -> float:
    """
    执行乘法运算
    
    Args:
        a: 第一个乘数
        b: 第二个乘数
    
    Returns:
        两个数的乘积
    """
    return a * b


def power(a: float, b: float) -> float:
    """
    计算幂运算
    
    Args:
        a: 底数
        b: 指数
    
    Returns:
        a 的 b 次方
    """
    return a ** b
'''
    
    tools_file = skill_dir / "tools.py"
    tools_file.write_text(tools_code, encoding='utf-8')
    
    print(f"✓ 自定义 Skill '{skill_name}' 已创建在: {skill_dir}")
    return skill_name


def cleanup_custom_skill(skill_name: str):
    """清理自定义 Skill"""
    skills_dir = project_root / "bitwiseai" / "skills"
    skill_dir = skills_dir / skill_name
    if skill_dir.exists():
        shutil.rmtree(skill_dir)
        print(f"✓ 已清理 Skill: {skill_name}")


def main():
    """自定义 Skill 示例"""
    print("=" * 60)
    print("BitwiseAI 自定义 Skill 示例")
    print("=" * 60)
    print()
    
    # 1. 初始化 BitwiseAI
    print("1. 初始化 BitwiseAI...")
    try:
        ai = BitwiseAI()
    except ValueError as e:
        print(f"❌ 初始化失败: {e}")
        print("💡 提示: 请先运行 'bitwiseai --generate-config' 生成配置文件")
        return
    print("✓ 初始化成功\n")
    
    # 2. 创建自定义 Skill
    print("2. 创建自定义 Skill")
    print("-" * 60)
    skill_name = create_custom_skill()
    print()
    
    # 3. 重新扫描 Skills
    print("3. 重新扫描 Skills")
    print("-" * 60)
    ai.skill_manager.scan_skills()
    available_skills = ai.skill_manager.list_available_skills()
    print(f"可用 Skills ({len(available_skills)} 个):")
    for skill in available_skills:
        print(f"  - {skill}")
    print()
    
    # 4. 加载自定义 Skill
    print(f"4. 加载自定义 Skill: {skill_name}")
    print("-" * 60)
    success = ai.load_skill(skill_name)
    if success:
        print(f"✓ Skill '{skill_name}' 加载成功")
    else:
        print(f"❌ Skill '{skill_name}' 加载失败")
        return
    print()
    
    # 5. 查看 Skill 的工具
    print("5. 查看 Skill 的工具")
    print("-" * 60)
    skill = ai.skill_manager.get_skill(skill_name)
    if skill and skill.loaded:
        print(f"Skill '{skill_name}' 的工具:")
        for tool_name, tool_info in skill.tools.items():
            print(f"  - {tool_name}: {tool_info['config'].get('description', '无描述')}")
    print()
    
    # 6. 直接调用工具
    print("6. 直接调用工具")
    print("-" * 60)
    try:
        result1 = ai.invoke_tool("add", 10, 20)
        print(f"add(10, 20) = {result1}")
        
        result2 = ai.invoke_tool("multiply", 5, 6)
        print(f"multiply(5, 6) = {result2}")
        
        result3 = ai.invoke_tool("power", 2, 8)
        print(f"power(2, 8) = {result3}")
    except Exception as e:
        print(f"❌ 工具调用失败: {e}")
    print()
    
    # 7. 在对话中使用工具
    print("7. 在对话中使用工具")
    print("-" * 60)
    queries = [
        "请计算 15 加 25 等于多少",
        "帮我计算 7 乘以 8",
        "2 的 10 次方是多少？"
    ]
    
    for query in queries:
        print(f"问题: {query}")
        response = ai.chat(query, use_rag=False, use_tools=True)
        print(f"回答: {response}\n")
    
    # 8. 卸载 Skill
    print(f"8. 卸载 Skill: {skill_name}")
    print("-" * 60)
    success = ai.unload_skill(skill_name)
    if success:
        print(f"✓ Skill '{skill_name}' 卸载成功")
    else:
        print(f"❌ Skill '{skill_name}' 卸载失败")
    print()
    
    # 清理
    print("9. 清理自定义 Skill")
    print("-" * 60)
    cleanup_custom_skill(skill_name)
    print()
    
    print("=" * 60)
    print("自定义 Skill 示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
