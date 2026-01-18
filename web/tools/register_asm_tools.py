# -*- coding: utf-8 -*-
"""
注册 ASM 解析工具到 BitwiseAI 工具系统
"""
import json
from typing import Dict, Any, List, Union
from pathlib import Path

# 导入 ASM 解析函数
from .parse_asm import parse_instruction, parse_asm_file_to_instructions


def parse_asm_instruction(cmd: str) -> str:
    """
    解析一条 ASM 指令（包装函数，供 LLM 调用）
    
    Args:
        cmd: 64位指令值，可以是：
            - 整数字符串（如 "1234567890"）
            - 十六进制字符串（如 "0x1234567890abcdef" 或 "1234567890abcdef"）
            - 二进制字符串（如 "0b1010..." 或 "1010..."）
    
    Returns:
        解析结果的 JSON 字符串
    """
    # 转换输入为整数
    cmd_str = str(cmd).strip()
    
    try:
        if cmd_str.startswith("0x"):
            # 十六进制（带 0x 前缀）
            cmd_int = int(cmd_str, 16)
        elif cmd_str.startswith("0b"):
            # 二进制（带 0b 前缀）
            cmd_int = int(cmd_str, 2)
        elif all(c in "0123456789abcdefABCDEF" for c in cmd_str) and len(cmd_str) >= 2:
            # 可能是十六进制（无前缀）
            try:
                cmd_int = int(cmd_str, 16)
            except ValueError:
                # 尝试作为十进制
                cmd_int = int(cmd_str)
        elif all(c in "01" for c in cmd_str):
            # 二进制（无前缀）
            cmd_int = int(cmd_str, 2)
        else:
            # 尝试作为十进制整数
            cmd_int = int(cmd_str)
    except ValueError:
        return json.dumps({
            "error": f"无法解析指令值: {cmd_str}。请提供整数、十六进制（0x...）或二进制（0b...）格式。"
        }, ensure_ascii=False, indent=2)
    
    # 解析指令
    try:
        result = parse_instruction(cmd_int)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"解析指令时出错: {str(e)}"
        }, ensure_ascii=False, indent=2)


def parse_asm_file(file_path: str) -> str:
    """
    解析 ASM 文件为指令列表（包装函数，供 LLM 调用）
    
    Args:
        file_path: ASM 文件路径
    
    Returns:
        解析结果的 JSON 字符串
    """
    # 检查文件是否存在
    path = Path(file_path)
    if not path.exists():
        return json.dumps({
            "error": f"文件不存在: {file_path}"
        }, ensure_ascii=False, indent=2)
    
    # 解析文件
    try:
        instructions = parse_asm_file_to_instructions(str(path))
        return json.dumps({
            "file_path": file_path,
            "instruction_count": len(instructions),
            "instructions": instructions
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"解析文件时出错: {str(e)}"
        }, ensure_ascii=False, indent=2)


def register_asm_tools(tool_registry):
    """
    注册 ASM 解析工具到工具注册器
    
    Args:
        tool_registry: BitwiseAI 的工具注册器实例
    """
    # 注册单条指令解析工具
    tool_registry.register_function(
        parse_asm_instruction,
        name="parse_asm_instruction",
        description="""解析一条64位 ASM 指令。
        
参数:
- cmd: 64位指令值，可以是：
  - 整数（如 1234567890）
  - 十六进制字符串（如 "0x1234567890abcdef"）
  - 二进制字符串（如 "0b1010..."）

返回:
解析后的指令信息，包括：
- instruction_name: 指令名称（如 MOV, ADD, SUB 等）
- opcode: 操作码（十进制、十六进制、二进制）
- cmd_hex: 完整指令的十六进制表示
- cmd_binary: 完整指令的二进制表示
- fields: 字段列表，每个字段包含：
  - name: 字段名
  - value: 字段值（十六进制）
  - bits: 位范围
  - register_name: 寄存器名称（如果是寄存器字段）

示例:
- parse_asm_instruction("0x0000000000000001")  # 解析十六进制指令
- parse_asm_instruction(1)  # 解析整数指令
"""
    )
    
    # 注册文件解析工具
    tool_registry.register_function(
        parse_asm_file,
        name="parse_asm_file",
        description="""解析 ASM 文件为指令列表。
        
参数:
- file_path: ASM 文件路径（绝对路径或相对路径）

返回:
解析结果，包括：
- file_path: 文件路径
- instruction_count: 指令数量
- instructions: 指令列表，每个指令包含完整的解析信息

示例:
- parse_asm_file("/path/to/instructions.asm")
- parse_asm_file("instructions.asm")
"""
    )
    
    print("✓ ASM 解析工具已注册: parse_asm_instruction, parse_asm_file")

