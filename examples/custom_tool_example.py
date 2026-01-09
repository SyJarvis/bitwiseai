# -*- coding: utf-8 -*-
"""
自定义工具示例

展示如何注册和使用自定义工具
"""
from dotenv import load_dotenv
load_dotenv()

from bitwiseai import BitwiseAI


# ========== 定义自定义工具函数 ==========

def parse_register_value(hex_str: str) -> dict:
    """
    解析寄存器十六进制值
    
    Args:
        hex_str: 十六进制字符串，如 "0x8D172E83"
        
    Returns:
        解析结果字典
    """
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    
    # 解析为字节数组
    bytes_list = [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]
    
    # 转换为有符号整数
    signed_bytes = []
    for b in bytes_list:
        if b >= 128:
            signed_bytes.append(b - 256)
        else:
            signed_bytes.append(b)
    
    return {
        "hex": "0x" + hex_str,
        "bytes": bytes_list,
        "signed_bytes": signed_bytes,
        "decimal": int(hex_str, 16)
    }


def verify_add_instruction(a: int, b: int, expected: int, saturate: bool = False) -> dict:
    """
    验证加法指令
    
    Args:
        a: 第一个操作数
        b: 第二个操作数
        expected: 期望结果
        saturate: 是否使用饱和运算
        
    Returns:
        验证结果
    """
    result = a + b
    
    if saturate:
        if result > 127:
            result = 127
        elif result < -128:
            result = -128
    
    is_correct = (result == expected)
    
    return {
        "operand_a": a,
        "operand_b": b,
        "calculated_result": result,
        "expected_result": expected,
        "is_correct": is_correct,
        "error": result - expected if not is_correct else 0
    }


def main():
    print("=" * 60)
    print("BitwiseAI - 自定义工具示例")
    print("=" * 60)
    print()
    
    # 初始化 BitwiseAI
    ai = BitwiseAI()
    print()
    
    # ========== 方式1: 注册 Python 函数 ==========
    print("方式1: 注册 Python 函数")
    print("-" * 40)
    
    ai.register_tool(
        parse_register_value,
        name="parse_register",
        description="解析寄存器十六进制值"
    )
    
    ai.register_tool(
        verify_add_instruction,
        name="verify_add",
        description="验证加法指令计算"
    )
    
    print()
    
    # ========== 方式2: 注册 Shell 命令工具 ==========
    print("方式2: 注册 Shell 命令工具")
    print("-" * 40)
    
    ai.register_tool({
        "type": "shell_command",
        "name": "count_lines",
        "command": "wc -l {file_path}",
        "description": "统计文件行数"
    })
    
    print()
    
    # ========== 列出所有工具 ==========
    print("已注册的工具:")
    print("-" * 40)
    tools = ai.list_tools()
    for i, tool_name in enumerate(tools, 1):
        print(f"  {i}. {tool_name}")
    print()
    
    # ========== 使用工具 ==========
    print("使用工具:")
    print("-" * 40)
    
    # 使用寄存器解析工具
    print("1. 解析寄存器值 0x8D172E83:")
    result1 = ai.invoke_tool("parse_register", "0x8D172E83")
    for key, value in result1.items():
        print(f"   {key}: {value}")
    print()
    
    # 使用加法验证工具
    print("2. 验证加法: 100 + 50 = 127 (饱和)")
    result2 = ai.invoke_tool("verify_add", 100, 50, 127, saturate=True)
    print(f"   正确: {result2['is_correct']}")
    print(f"   计算结果: {result2['calculated_result']}")
    print(f"   期望结果: {result2['expected_result']}")
    print()
    
    # 使用 Shell 命令工具
    print("3. 统计配置文件行数:")
    config_file = "/root/.bitwiseai/config.json"
    result3 = ai.invoke_tool("count_lines", file_path=config_file)
    print(f"   {result3.strip()}")
    print()
    
    print("=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

