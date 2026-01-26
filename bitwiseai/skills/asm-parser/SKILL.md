---
name: asm-parser
description: 解析64位 ASM 指令和文件，支持多种指令格式。使用场景：当需要解析硬件指令、分析 ASM 文件或验证指令正确性时。
license: MIT
metadata:
  author: BitwiseAI
  version: "1.0.0"
---

# ASM 指令解析器

## 功能概述

本技能提供 ASM 指令解析功能，支持：
- 解析单条64位 ASM 指令
- 解析 ASM 文件中的所有指令
- 支持多种指令格式（MOV, ADD, SUB, MUL, LUT2/3/4, SHIFT, CLAMP, ABS 等）

## 工具说明

### parse_asm_instruction

解析一条64位 ASM 指令。输入为指令的十六进制、二进制或十进制值，输出为指令的详细解析信息，包括指令名称、操作码、各字段的值和含义。

**参数**:
- `cmd` (string): 64位指令值，可以是整数、十六进制（0x...）或二进制（0b...）格式

**示例**:
```python
parse_asm_instruction("0x1234567890abcdef")
```

**返回格式**:
返回 JSON 字符串，包含：
- 指令名称
- 操作码
- 各字段的值和含义
- 寄存器信息

### parse_asm_file

解析 ASM 文件中的所有指令。输入为 ASM 文件路径，输出为文件中所有指令的详细解析信息。ASM 文件格式为每行包含一条或多条指令的十六进制表示（每条指令16个字符）。

**参数**:
- `file_path` (string): ASM 文件的路径（绝对路径或相对路径）

**示例**:
```python
parse_asm_file("/path/to/instructions.asm")
```

**返回格式**:
返回 JSON 字符串，包含：
- 文件路径
- 指令数量
- 所有指令的详细解析信息列表

## 使用场景

- 硬件调试和指令验证
- ASM 文件分析和处理
- 指令格式转换和解析
- 指令正确性验证

## 支持的指令类型

- MOV: 数据移动指令
- ADD/SUB/MUL: 算术运算指令
- LUT2/LUT3/LUT4: 查找表指令
- SHIFT: 移位指令
- CLAMP: 限幅指令
- ABS: 绝对值指令

## 注意事项

- 指令值必须是64位整数
- 支持十六进制（0x...）、二进制（0b...）和十进制格式
- ASM 文件每行应包含完整的指令十六进制表示

