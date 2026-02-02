---
name: hex-converter
description: 十六进制、二进制、十进制转换工具集。使用场景：当需要在不同进制之间转换数值时，如调试硬件指令、分析内存地址或处理数值格式转换。
license: MIT
metadata:
  author: BitwiseAI
  version: "1.0.0"
---

# 进制转换工具

## 功能概述

本技能提供完整的进制转换功能，支持：
- 十六进制 ↔ 十进制
- 二进制 ↔ 十进制
- 十六进制 ↔ 二进制

## 工具说明

### hex_to_decimal

将十六进制字符串转换为十进制整数。

**参数**:
- `hex_str` (string): 十六进制字符串，如 "0xFF" 或 "FF"

**示例**:
```python
hex_to_decimal("0xFF")  # 返回 255
hex_to_decimal("FF")    # 返回 255
```

### decimal_to_hex

将十进制整数转换为十六进制字符串。

**参数**:
- `dec_num` (int): 十进制整数

**示例**:
```python
decimal_to_hex(255)  # 返回 "0xff"
```

### binary_to_decimal

将二进制字符串转换为十进制整数。

**参数**:
- `bin_str` (string): 二进制字符串，如 "0b1010" 或 "1010"

**示例**:
```python
binary_to_decimal("0b1010")  # 返回 10
binary_to_decimal("1010")    # 返回 10
```

### decimal_to_binary

将十进制整数转换为二进制字符串。

**参数**:
- `dec_num` (int): 十进制整数

**示例**:
```python
decimal_to_binary(10)  # 返回 "0b1010"
```

### hex_to_binary

将十六进制字符串转换为二进制字符串。

**参数**:
- `hex_str` (string): 十六进制字符串，如 "0xFF" 或 "FF"

**示例**:
```python
hex_to_binary("0xFF")  # 返回 "0b11111111"
```

### binary_to_hex

将二进制字符串转换为十六进制字符串。

**参数**:
- `bin_str` (string): 二进制字符串，如 "0b1010" 或 "1010"

**示例**:
```python
binary_to_hex("0b1010")  # 返回 "0xa"
```

## 使用场景

- 硬件调试和数值分析
- 内存地址转换
- 指令编码/解码
- 数值格式转换

## 注意事项

- 十六进制字符串可以带或不带 "0x" 前缀
- 二进制字符串可以带或不带 "0b" 前缀
- 所有转换函数都返回标准格式（带前缀）


