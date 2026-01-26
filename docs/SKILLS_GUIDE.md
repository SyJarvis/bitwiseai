# Skills 开发指南

本文档介绍如何在 BitwiseAI 中创建和使用 Skills（基于 Claude Skills 标准）。

## 目录

- [什么是 Skills](#什么是-skills)
- [Skills 系统架构](#skills-系统架构)
- [创建新 Skill 的步骤](#创建新-skill-的步骤)
- [SKILL.md 格式说明](#skillmd-格式说明)
- [工具函数编写规范](#工具函数编写规范)
- [完整示例](#完整示例)
- [测试 Skill](#测试-skill)
- [最佳实践](#最佳实践)

## 什么是 Skills

Skills 是 BitwiseAI 中的动态能力模块，基于 [Claude Skills 标准](https://agentskills.io/)。Skills 提供可复用的工具和工作流，采用渐进式加载机制，优化上下文使用。

**Skills 的特点：**
- ✅ 基于 Claude Skills 标准（SKILL.md 格式）
- ✅ 渐进式加载，不占用初始上下文
- ✅ 可复用、可分享
- ✅ 支持工具、脚本、资源文件
- ✅ 自动发现和注册
- ✅ 与 LLM Agent 无缝集成
- ✅ 向量索引支持智能搜索

## Skills 系统架构

```
bitwiseai/skills/                    # 内置技能
├── asm-parser/
│   ├── SKILL.md                      # 技能元数据和指令（必需）
│   ├── scripts/
│   │   └── tools.py                  # 工具函数实现
│   └── references/                   # 可选：参考文档
│       └── instruction_set.md
└── hex-converter/
    ├── SKILL.md
    └── scripts/
        └── tools.py

~/.bitwiseai/skills/                  # 外部技能（用户自定义）
└── custom-skill/
    ├── SKILL.md
    └── scripts/
        └── tools.py
```

## 创建新 Skill 的步骤

### 步骤 1: 创建 Skill 目录

在 `bitwiseai/skills/`（内置）或 `~/.bitwiseai/skills/`（外部）目录下创建新的 skill 目录：

```bash
mkdir -p ~/.bitwiseai/skills/my-skill
cd ~/.bitwiseai/skills/my-skill
```

**注意**：目录名必须使用连字符（kebab-case），如 `my-skill`，不能使用下划线。

### 步骤 2: 创建 `SKILL.md`

创建技能元数据和指令文件：

```markdown
---
name: my-skill
description: 我的技能描述，说明功能和使用场景。使用场景：当需要...时。
license: MIT
metadata:
  author: Your Name
  version: "1.0.0"
---

# My Skill

## 功能概述

本技能提供...功能。

## 工具说明

### my_tool

工具描述...

**参数**:
- `param1` (string): 参数1的描述
- `param2` (int): 参数2的描述

**示例**:
```python
my_tool("value1", 123)
```

## 使用场景

- 场景1
- 场景2
```

### 步骤 3: 创建 `scripts/tools.py`

实现工具函数：

```python
# -*- coding: utf-8 -*-
"""
我的 Skill 工具实现
"""

def my_tool(param1: str, param2: int) -> str:
    """
    工具函数的描述
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
    
    Returns:
        返回值的描述
    """
    # 实现你的逻辑
    result = f"处理 {param1} 和 {param2}"
    return result
```

### 步骤 4: 创建 `__init__.py` 文件

创建空的 `__init__.py` 文件，使其成为一个 Python 包：

```bash
touch __init__.py scripts/__init__.py
```

## SKILL.md 格式说明

### Frontmatter（必需）

SKILL.md 文件必须以 YAML frontmatter 开头：

```yaml
---
name: my-skill
description: 技能描述，说明功能和使用场景
license: MIT  # 可选
metadata:     # 可选
  author: Your Name
  version: "1.0.0"
---
```

**必需字段：**
- `name`: 技能名称（1-64 字符，小写字母、数字和连字符，不能以连字符开头或结尾）
- `description`: 技能描述（1-1024 字符，应说明功能和使用场景）

**可选字段：**
- `license`: 许可证信息
- `compatibility`: 环境要求（最多 500 字符）
- `metadata`: 自定义元数据（键值对）

### Markdown 正文

Frontmatter 之后是 Markdown 正文，包含技能指令。推荐结构：

- **功能概述**：简要说明技能功能
- **工具说明**：详细说明每个工具的使用方法
- **使用场景**：列出适用场景
- **注意事项**：重要提示

## 工具函数编写规范

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
bitwiseai/skills/calculator/
├── SKILL.md
├── scripts/
│   └── tools.py
└── __init__.py
```

**SKILL.md：**
```markdown
---
name: calculator
description: 基础计算器工具集。使用场景：当需要进行数学计算时。
license: MIT
metadata:
  author: BitwiseAI
  version: "1.0.0"
---

# 计算器

## 功能概述

本技能提供基础数学计算功能。

## 工具说明

### add

计算两个数字的和。

**参数**:
- `a` (float): 第一个数字
- `b` (float): 第二个数字

### multiply

计算两个数字的乘积。

**参数**:
- `a` (float): 第一个数字
- `b` (float): 第二个数字
```

**scripts/tools.py：**
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

## 测试 Skill

### 1. 检查 Skill 是否被发现

```bash
bitwiseai tool --list-skills
```

应该能看到你的 skill 在列表中。

### 2. 加载 Skill

```bash
bitwiseai tool --load-skill my-skill
```

### 3. 列出工具

```bash
bitwiseai tool --list-tools
```

应该能看到你的工具在列表中。

### 4. 搜索技能

```bash
bitwiseai tool --search "计算" --top-k 5
```

### 5. 在聊天中使用

```bash
bitwiseai chat "使用 my_tool 处理 value1 和 123"
```

LLM 应该能够识别并调用你的工具。

### 6. 使用 Python API 测试

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 列出 skills
print(ai.list_skills())

# 加载 skill
ai.load_skill("my-skill")

# 搜索技能
results = ai.search_skills("计算", top_k=5)
print(results)

# 列出工具
print(ai.list_tools())

# 在聊天中使用
response = ai.chat("使用 my_tool 处理 value1 和 123", use_tools=True)
print(response)
```

## 最佳实践

### 1. 技能描述要清晰

✅ **好的描述：**
```yaml
description: 解析64位 ASM 指令和文件，支持多种指令格式。使用场景：当需要解析硬件指令、分析 ASM 文件或验证指令正确性时。
```

❌ **不好的描述：**
```yaml
description: 解析指令
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
        result = process(param)
        return result
    except ValueError as e:
        return f"参数错误: {str(e)}"
    except Exception as e:
        return f"处理失败: {str(e)}"
```

### 4. 工具命名要清晰

✅ **好的命名：**
- `parse_asm_instruction`
- `hex_to_decimal`
- `read_file`

❌ **不好的命名：**
- `tool1`
- `func`
- `do_something`

### 5. 目录命名规范

- 使用连字符（kebab-case）：`asm-parser`、`hex-converter`
- 不能使用下划线：`asm_parser` ❌
- 不能以连字符开头或结尾：`-parser` ❌、`parser-` ❌

### 6. 渐进式加载

Skills 采用渐进式加载机制：
1. **发现阶段**：只加载 SKILL.md 的 frontmatter（~100 tokens）
2. **激活阶段**：加载完整 SKILL.md 内容（< 5000 tokens 推荐）
3. **执行阶段**：按需加载 scripts/ 和 references/ 文件

因此：
- 保持 SKILL.md 简洁（< 500 行）
- 详细文档放在 `references/` 目录
- 工具实现放在 `scripts/` 目录

## 常见问题

### Q: Skill 没有被发现？

**A:** 检查以下几点：
1. 目录名是否与 SKILL.md 中的 `name` 字段一致
2. SKILL.md 文件是否存在且格式正确
3. 是否在正确的目录下（内置：`bitwiseai/skills/`，外部：`~/.bitwiseai/skills/`）

### Q: 工具没有被加载？

**A:** 检查以下几点：
1. `scripts/tools.py` 文件是否存在
2. 函数是否有语法错误
3. 函数是否有清晰的类型注解和文档字符串

### Q: LLM 不调用我的工具？

**A:** 检查以下几点：
1. SKILL.md 中的工具描述是否清晰
2. 用户的问题是否与工具描述匹配
3. 工具是否已正确加载（使用 `--list-tools` 检查）

### Q: 如何添加外部技能目录？

**A:** 
1. 在配置文件中添加：
```json
{
  "skills": {
    "external_directories": ["~/.bitwiseai/skills", "/custom/path"]
  }
}
```

2. 或使用 CLI 命令：
```bash
bitwiseai tool --add-dir /custom/path
```

### Q: 如何搜索技能？

**A:** 使用向量检索搜索技能：
```bash
bitwiseai tool --search "解析指令" --top-k 5
```

## 参考资源

- [Claude Skills 规范](https://agentskills.io/specification)
- [现有 Skills 示例](../bitwiseai/skills/)
  - `asm-parser`: ASM 指令解析
  - `hex-converter`: 进制转换工具
- [SkillManager 源码](../bitwiseai/core/skill_manager.py)
- [ChatEngine 源码](../bitwiseai/core/chat_engine.py)

## 总结

创建新 Skill 的步骤：
1. ✅ 创建目录和 `__init__.py`
2. ✅ 编写 `SKILL.md` 文件（frontmatter + Markdown）
3. ✅ 实现 `scripts/tools.py` 中的工具函数
4. ✅ 测试 Skill 是否正常工作
5. ✅ 完善文档和错误处理

记住：**清晰的描述是 LLM 正确使用工具的关键！**
