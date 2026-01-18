# Skills 开发指南

本文档介绍如何在 BitwiseAI 中添加新的 Skills。

## 目录

- [什么是 Skills](#什么是-skills)
- [Skills 系统架构](#skills-系统架构)
- [创建新 Skill 的步骤](#创建新-skill-的步骤)
- [Skill 目录结构](#skill-目录结构)
- [skill.json 配置说明](#skilljson-配置说明)
- [tools.py 编写规范](#toolspy-编写规范)
- [完整示例](#完整示例)
- [测试 Skill](#测试-skill)
- [最佳实践](#最佳实践)

## 什么是 Skills

Skills 是 BitwiseAI 中的动态上下文模块，用于提供可复用的工具和工作流。与静态上下文（Rules）不同，Skills 是按需加载的，不会占用初始上下文。

**Skills 的特点：**
- ✅ 按需加载，不占用初始上下文
- ✅ 可复用、可分享
- ✅ 支持工具、脚本、资源文件
- ✅ 自动发现和注册
- ✅ 与 LLM Agent 无缝集成

## Skills 系统架构

```
bitwiseai/
  skills/
    ├── asm_parser/          # ASM 解析 skill
    │   ├── skill.json       # Skill 清单文件
    │   ├── tools.py         # 工具函数实现
    │   └── __init__.py      # Python 包标识
    └── builtin/             # 内置 skills
        └── hex_converter/   # 进制转换 skill
            ├── skill.json
            ├── tools.py
            └── __init__.py
```

## 创建新 Skill 的步骤

### 步骤 1: 创建 Skill 目录

在 `bitwiseai/skills/` 目录下创建新的 skill 目录：

```bash
mkdir -p bitwiseai/skills/my_skill
cd bitwiseai/skills/my_skill
```

### 步骤 2: 创建 `__init__.py`

创建空的 `__init__.py` 文件，使其成为一个 Python 包：

```python
# bitwiseai/skills/my_skill/__init__.py
# 空文件即可
```

### 步骤 3: 创建 `skill.json`

创建 skill 清单文件，定义 skill 的元数据和工具：

```json
{
  "name": "my_skill",
  "version": "1.0.0",
  "description": "我的 Skill 描述",
  "author": "Your Name",
  "tools": [
    {
      "name": "my_tool",
      "module": "tools",
      "function": "my_tool",
      "description": "工具的描述，LLM 会根据这个描述决定是否使用该工具",
      "parameters": {
        "param1": {
          "type": "string",
          "description": "参数1的描述"
        },
        "param2": {
          "type": "integer",
          "description": "参数2的描述"
        }
      }
    }
  ],
  "dependencies": [],
  "resources": [],
  "hooks": {
    "on_load": null,
    "on_unload": null
  }
}
```

### 步骤 4: 创建 `tools.py`

实现工具函数：

```python
# bitwiseai/skills/my_skill/tools.py
# -*- coding: utf-8 -*-
"""
我的 Skill 工具实现
"""

def my_tool(param1: str, param2: int) -> str:
    """
    工具函数的实现
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
    
    Returns:
        返回结果的描述
    """
    # 实现你的逻辑
    result = f"处理 {param1} 和 {param2}"
    return result
```

### 步骤 5: 测试 Skill

使用 CLI 测试你的 skill：

```bash
# 列出所有 skills
python -m bitwiseai.cli tool --list-skills

# 加载你的 skill
python -m bitwiseai.cli tool --load-skill my_skill

# 列出工具
python -m bitwiseai.cli tool --list-tools

# 测试工具调用
python -m bitwiseai.cli tool --invoke my_tool --args "value1" 123

# 在聊天中使用
python -m bitwiseai.cli chat "使用 my_tool 处理 value1 和 123"
```

## Skill 目录结构

一个完整的 skill 目录应该包含：

```
my_skill/
├── __init__.py          # Python 包标识（必需）
├── skill.json           # Skill 清单文件（必需）
├── tools.py             # 工具函数实现（必需）
├── README.md            # Skill 说明文档（可选）
└── resources/           # 资源文件（可选）
    └── data.json
```

## skill.json 配置说明

### 基本字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | Skill 名称，必须与目录名一致 |
| `version` | string | ✅ | 版本号，如 "1.0.0" |
| `description` | string | ✅ | Skill 的描述 |
| `author` | string | ✅ | 作者名称 |
| `tools` | array | ✅ | 工具列表 |
| `dependencies` | array | ❌ | 依赖列表（未来使用） |
| `resources` | array | ❌ | 资源文件列表（未来使用） |
| `hooks` | object | ❌ | 钩子函数（未来使用） |

### tools 字段详解

每个工具对象包含：

```json
{
  "name": "tool_name",           // 工具名称（必需）
  "module": "tools",              // 模块名，通常是 "tools"（必需）
  "function": "function_name",    // 函数名（必需）
  "description": "工具描述",      // 工具描述（必需，LLM 会根据这个决定是否使用）
  "parameters": {                 // 参数定义（可选，但推荐）
    "param_name": {
      "type": "string",           // 参数类型：string, integer, float, boolean
      "description": "参数描述"   // 参数描述
    }
  }
}
```

**重要提示：**
- `description` 字段非常重要，LLM 会根据这个描述决定是否调用该工具
- 描述应该清晰、具体，说明工具的功能和使用场景
- 参数定义可以帮助 LLM 更好地理解工具的使用方式

## tools.py 编写规范

### 函数签名

工具函数应该：
- 使用类型注解（Type Hints）
- 有清晰的文档字符串（Docstring）
- 返回类型明确

```python
def my_tool(param1: str, param2: int) -> str:
    """
    工具函数的描述
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
    
    Returns:
        返回值的描述
    """
    # 实现
    pass
```

### 错误处理

工具函数应该妥善处理错误：

```python
def my_tool(param: str) -> str:
    """
    处理参数的函数
    """
    try:
        # 处理逻辑
        result = process(param)
        return result
    except ValueError as e:
        return f"错误: {str(e)}"
    except Exception as e:
        return f"未知错误: {str(e)}"
```

### 返回格式

工具函数可以返回：
- 字符串（推荐）：简单直接
- JSON 字符串：复杂数据结构
- 字典/列表：会被自动序列化

```python
# 简单字符串
def simple_tool(x: int) -> str:
    return f"结果是 {x * 2}"

# JSON 字符串（复杂数据）
import json
def complex_tool(data: dict) -> str:
    result = {
        "status": "success",
        "data": data
    }
    return json.dumps(result, ensure_ascii=False, indent=2)
```

## 完整示例

### 示例 1: 简单计算工具

**目录结构：**
```
bitwiseai/skills/builtin/calculator/
├── __init__.py
├── skill.json
└── tools.py
```

**skill.json：**
```json
{
  "name": "calculator",
  "version": "1.0.0",
  "description": "基础计算器工具集",
  "author": "BitwiseAI",
  "tools": [
    {
      "name": "add",
      "module": "tools",
      "function": "add",
      "description": "计算两个数字的和",
      "parameters": {
        "a": {
          "type": "float",
          "description": "第一个数字"
        },
        "b": {
          "type": "float",
          "description": "第二个数字"
        }
      }
    },
    {
      "name": "multiply",
      "module": "tools",
      "function": "multiply",
      "description": "计算两个数字的乘积",
      "parameters": {
        "a": {
          "type": "float",
          "description": "第一个数字"
        },
        "b": {
          "type": "float",
          "description": "第二个数字"
        }
      }
    }
  ],
  "dependencies": [],
  "resources": [],
  "hooks": {
    "on_load": null,
    "on_unload": null
  }
}
```

**tools.py：**
```python
# -*- coding: utf-8 -*-
"""
计算器工具
"""

def add(a: float, b: float) -> float:
    """
    计算两个数字的和
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        两个数字的和
    """
    return a + b


def multiply(a: float, b: float) -> float:
    """
    计算两个数字的乘积
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        两个数字的乘积
    """
    return a * b
```

### 示例 2: 文件操作工具

**skill.json：**
```json
{
  "name": "file_operations",
  "version": "1.0.0",
  "description": "文件操作工具集，支持读取、写入文件",
  "author": "BitwiseAI",
  "tools": [
    {
      "name": "read_file",
      "module": "tools",
      "function": "read_file",
      "description": "读取文件内容。输入文件路径，返回文件内容。如果文件不存在或无法读取，返回错误信息。",
      "parameters": {
        "file_path": {
          "type": "string",
          "description": "文件的绝对路径或相对路径"
        }
      }
    },
    {
      "name": "write_file",
      "module": "tools",
      "function": "write_file",
      "description": "写入内容到文件。输入文件路径和内容，创建或覆盖文件。",
      "parameters": {
        "file_path": {
          "type": "string",
          "description": "文件的绝对路径或相对路径"
        },
        "content": {
          "type": "string",
          "description": "要写入的内容"
        }
      }
    }
  ],
  "dependencies": [],
  "resources": [],
  "hooks": {
    "on_load": null,
    "on_unload": null
  }
}
```

**tools.py：**
```python
# -*- coding: utf-8 -*-
"""
文件操作工具
"""
import os
from pathlib import Path


def read_file(file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件内容，如果出错则返回错误信息
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"错误: 文件不存在: {file_path}"
        
        if not path.is_file():
            return f"错误: 不是文件: {file_path}"
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    except PermissionError:
        return f"错误: 没有权限读取文件: {file_path}"
    except Exception as e:
        return f"错误: 读取文件失败: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """
    写入内容到文件
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
    
    Returns:
        成功信息或错误信息
    """
    try:
        path = Path(file_path)
        # 创建父目录（如果不存在）
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"成功写入文件: {file_path}"
    except PermissionError:
        return f"错误: 没有权限写入文件: {file_path}"
    except Exception as e:
        return f"错误: 写入文件失败: {str(e)}"
```

## 测试 Skill

### 1. 检查 Skill 是否被发现

```bash
python -m bitwiseai.cli tool --list-skills
```

应该能看到你的 skill 在列表中。

### 2. 加载 Skill

```bash
python -m bitwiseai.cli tool --load-skill my_skill
```

### 3. 列出工具

```bash
python -m bitwiseai.cli tool --list-tools
```

应该能看到你的工具在列表中。

### 4. 直接调用工具

```bash
python -m bitwiseai.cli tool --invoke my_tool --args "param1" 123
```

### 5. 在聊天中测试

```bash
python -m bitwiseai.cli chat "使用 my_tool 处理 param1 和 123"
```

LLM 应该能够识别并调用你的工具。

### 6. 使用 Python API 测试

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 列出 skills
print(ai.list_skills())

# 加载 skill
ai.load_skill("my_skill")

# 列出工具
print(ai.list_tools())

# 调用工具
result = ai.invoke_tool("my_tool", "param1", 123)
print(result)

# 在聊天中使用
response = ai.chat("使用 my_tool 处理 param1 和 123", use_tools=True)
print(response)
```

## 最佳实践

### 1. 工具描述要清晰

✅ **好的描述：**
```json
{
  "description": "解析一条64位 ASM 指令。输入为指令的十六进制、二进制或十进制值，输出为指令的详细解析信息，包括指令名称、操作码、各字段的值和含义。"
}
```

❌ **不好的描述：**
```json
{
  "description": "解析指令"
}
```

### 2. 使用类型注解

✅ **推荐：**
```python
def my_tool(param1: str, param2: int) -> str:
    pass
```

❌ **不推荐：**
```python
def my_tool(param1, param2):
    pass
```

### 3. 完善的错误处理

✅ **推荐：**
```python
def my_tool(param: str) -> str:
    try:
        # 处理逻辑
        result = process(param)
        return result
    except ValueError as e:
        return f"参数错误: {str(e)}"
    except Exception as e:
        return f"处理失败: {str(e)}"
```

### 4. 返回格式要一致

- 简单结果：返回字符串
- 复杂结果：返回 JSON 字符串
- 错误信息：统一格式

### 5. 工具命名要清晰

✅ **好的命名：**
- `parse_asm_instruction`
- `hex_to_decimal`
- `read_file`

❌ **不好的命名：**
- `tool1`
- `func`
- `do_something`

### 6. 参数验证

```python
def my_tool(param: str) -> str:
    if not param or not param.strip():
        return "错误: 参数不能为空"
    
    if len(param) > 100:
        return "错误: 参数长度不能超过100"
    
    # 处理逻辑
    pass
```

### 7. 文档字符串

每个工具函数都应该有清晰的文档字符串：

```python
def my_tool(param1: str, param2: int) -> str:
    """
    工具功能的简要描述（一行）
    
    更详细的描述，说明工具的使用场景和注意事项。
    
    Args:
        param1: 参数1的详细描述，包括格式要求、取值范围等
        param2: 参数2的详细描述
    
    Returns:
        返回值的详细描述，包括格式、可能的值等
    
    Raises:
        ValueError: 当参数无效时
    """
    pass
```

## 常见问题

### Q: Skill 没有被发现？

**A:** 检查以下几点：
1. 目录名是否与 `skill.json` 中的 `name` 字段一致
2. `skill.json` 文件是否存在且格式正确
3. 是否在 `bitwiseai/skills/` 目录下

### Q: 工具没有被加载？

**A:** 检查以下几点：
1. `tools.py` 文件是否存在
2. 函数名是否与 `skill.json` 中的 `function` 字段一致
3. 函数是否有语法错误

### Q: LLM 不调用我的工具？

**A:** 检查以下几点：
1. `description` 字段是否清晰描述了工具的功能
2. 用户的问题是否与工具描述匹配
3. 工具是否已正确加载（使用 `--list-tools` 检查）

### Q: 如何调试工具？

**A:** 
1. 先直接调用工具测试：`python -m bitwiseai.cli tool --invoke tool_name --args ...`
2. 在工具函数中添加 `print()` 语句
3. 检查错误信息

### Q: 可以导入其他模块吗？

**A:** 可以，但要注意：
1. 确保依赖已安装
2. 避免循环导入
3. 使用相对导入时要小心

## 参考资源

- [现有 Skills 示例](../bitwiseai/skills/)
  - `asm_parser`: ASM 指令解析
  - `hex_converter`: 进制转换工具
- [SkillManager 源码](../bitwiseai/core/skill_manager.py)
- [ChatEngine 源码](../bitwiseai/core/chat_engine.py)

## 总结

创建新 Skill 的步骤：
1. ✅ 创建目录和 `__init__.py`
2. ✅ 编写 `skill.json` 清单文件
3. ✅ 实现 `tools.py` 中的工具函数
4. ✅ 测试 Skill 是否正常工作
5. ✅ 完善文档和错误处理

记住：**清晰的描述是 LLM 正确使用工具的关键！**

