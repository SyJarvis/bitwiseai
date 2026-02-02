# BitwiseAI CLI 使用指南

完整的命令行工具使用说明，重点介绍如何在 CLI 中使用 Skills。

## 📋 目录

1. [快速开始](#快速开始)
2. [配置](#配置)
3. [对话模式](#对话模式)
4. [Skill 管理](#skill-管理)
5. [交互模式中的 Slash 命令](#交互模式中的-slash-命令)
6. [完整示例](#完整示例)

## 快速开始

### 1. 配置 API 密钥

```bash
# 方式 1: 环境变量（推荐）
export LLM_API_KEY="sk-xxx"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"

export EMBEDDING_API_KEY="sk-xxx"
export EMBEDDING_BASE_URL="https://api.openai.com/v1"
export EMBEDDING_MODEL="text-embedding-3-small"
```

```bash
# 方式 2: 生成配置文件
bitwiseai config --force
# 然后编辑 ~/.bitwiseai/config.json
```

### 2. 测试基础对话

```bash
# 单次对话
bitwiseai chat "你好"

# 查看帮助
bitwiseai --help
```

## 配置

### 生成配置文件

```bash
# 生成配置文件（如果已存在会提示）
bitwiseai config

# 强制覆盖现有配置
bitwiseai config --force
```

配置文件位置: `~/.bitwiseai/config.json`

```json
{
  "llm": {
    "api_key": "sk-xxx",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "temperature": 0.7
  },
  "embedding": {
    "api_key": "sk-xxx",
    "base_url": "https://api.openai.com/v1",
    "model": "text-embedding-3-small"
  },
  "vector_db": {
    "db_file": "~/.bitwiseai/milvus_data.db",
    "collection_name": "bitwiseai",
    "embedding_dim": 1536
  },
  "system_prompt": "你是 BitwiseAI 助手",
  "skills": {
    "auto_load": [],
    "external_directories": ["~/.bitwiseai/skills"]
  }
}
```

## 对话模式

### 单次对话

```bash
# 基础对话
bitwiseai chat "什么是 MUL 指令？"

# 使用 RAG 检索
bitwiseai chat --use-rag "PE 指令有哪些约束？"
```

### 交互模式

```bash
# 进入交互模式
bitwiseai chat

# 在交互模式中
你: /help           # 查看帮助
你: /skills         # 列出所有 Skills
你: /load asm-parser  # 加载 Skill
你: 你好            # 正常对话
你: /quit           # 退出
```

## Skill 管理

### 1. 列出所有 Skills

```bash
# 列出所有可用的 Skills
bitwiseai skill --list

# 显示详细信息
bitwiseai skill --list --verbose

# 只显示已加载的
bitwiseai skill --list --loaded-only
```

**输出示例:**
```
可用 Skills (5 个):
  1. asm-parser ✅ 已加载
     描述: 汇编代码解析器
     工具: 2 个
  2. error-analyzer ⏸️  未加载
     描述: 错误日志分析器
     工具: 3 个
  3. hex_converter ⏸️  未加载
     描述: 十六进制转换工具
     工具: 2 个
```

### 2. 加载 Skill

```bash
# 加载指定的 Skill
bitwiseai skill --load asm-parser

# 加载后立即使用
bitwiseai chat "解析这段汇编代码" --use-rag
```

### 3. 卸载 Skill

```bash
# 卸载指定的 Skill
bitwiseai skill --unload asm-parser
```

### 4. 搜索 Skills

```bash
# 搜索相关 Skills
bitwiseai skill --search "代码" --top-k 5

# 搜索 "转换" 相关
bitwiseai skill --search "转换" --top-k 3
```

**输出示例:**
```
找到 2 个相关 Skills:
  1. hex_converter (相似度: 0.8500)
     十六进制转换工具
  2. asm_parser (相似度: 0.7200)
     汇编代码解析器
```

### 5. 添加外部 Skill 目录

```bash
# 添加自定义 Skills 目录
bitwiseai skill --add-dir ~/.bitwiseai/skills

# 添加项目特定 Skills
bitwiseai skill --add-dir ./my_skills
```

## 交互模式中的 Slash 命令

进入交互模式后，可以使用以下 Slash 命令管理 Skills：

```bash
$ bitwiseai chat
============================================================
BitwiseAI 对话模式
命令:
  /help           - 显示帮助
  /clear          - 清空上下文
  /sessions       - 列出所有会话
  /new <name>     - 创建新会话
  /switch <id>    - 切换会话
  /skills         - 列出所有 Skills
  /load <skill>   - 加载 Skill
  /unload <skill> - 卸载 Skill
  /agent          - 使用 Agent 模式
  /quit 或 exit   - 退出
============================================================

你: /skills
可用 Skills (5 个):
  - asm_parser
  - error_analyzer
  - hex_converter
  - builtin/hex_converter
  - builtin/asm_parser

你: /load hex_converter
✓ Skill 'hex_converter' 已加载

你: 将 0xFF 转换为十进制
AI: 0xFF 的十进制值是 255

你: /unload hex_converter
✓ Skill 'hex_converter' 已卸载

你: /quit
再见！
```

## Agent 模式

### 基础 Agent 使用

```bash
# 使用 Agent 自动执行任务
bitwiseai agent "分析这段代码并生成报告"

# 流式输出
bitwiseai agent "讲一个故事" --stream
```

### Agent 配合 Skills

```bash
# 1. 先加载需要的 Skills
bitwiseai skill --load asm_parser
bitwiseai skill --load error_analyzer

# 2. 使用 Agent（会自动使用已加载的工具）
bitwiseai agent "解析这段汇编代码并分析可能的错误"
```

## 会话管理

### 列出会话

```bash
bitwiseai session --list
```

**输出示例:**
```
会话列表 (3 个):
  1. 代码审查
     ID: a1b2c3d4e5f6...
     消息数: 15
  2. 项目讨论
     ID: f6e5d4c3b2a1...
     消息数: 8
  3. 学习笔记
     ID: 1a2b3c4d5e6f...
     消息数: 23
```

### 创建新会话

```bash
# 创建新会话
bitwiseai session --new "我的项目"

# 在交互模式中创建
你: /new 新项目讨论
✓ 创建会话: 新项目讨论
```

### 切换会话

```bash
# 切换到指定会话（可以使用部分 ID）
bitwiseai session --switch a1b2c3

# 在交互模式中切换
你: /switch a1b2c3
✓ 已切换到会话: 代码审查
```

### 删除会话

```bash
# 删除指定会话
bitwiseai session --delete a1b2c3
```

## 完整示例

### 示例 1: 代码审查工作流

```bash
# 1. 创建专门的审查会话
bitwiseai session --new "代码审查"

# 2. 加载相关 Skills
bitwiseai skill --load asm_parser
bitwiseai skill --load error_analyzer

# 3. 进入交互模式
bitwiseai chat

# 4. 在交互模式中
你: /load asm_parser
✓ Skill 'asm_parser' 已加载

你: 分析这段代码:
    ADD R1, R2, R3
    MUL R1, R1, R4

AI: [使用 Skill 解析代码并分析...]

你: /agent "生成代码审查报告"
AI: [使用 Agent 生成完整报告...]

你: /quit
```

### 示例 2: 学习硬件指令

```bash
# 1. 创建学习会话
bitwiseai session --new "指令学习"

# 2. 加载文档
# (假设已有文档在 ~/docs/hardware)

# 3. 交互模式学习
bitwiseai chat

you: /load asm_parser
you: MUL 指令的格式是什么？
AI: MUL 指令用于执行乘法运算...
    格式: MUL Rd, Rn, Rm

you: 给我一个例子
AI: 例如: MUL R3, R1, R2
    这将 R1 和 R2 相乘，结果存入 R3

you: 使用工具验证 "MUL R5, R5, R5"
AI: [使用 asm_parser Skill 验证...]
    这个指令是有效的，将 R5 的值与自身相乘。

you: /quit
```

### 示例 3: 多项目管理

```bash
# 项目 A: 前端开发
bitwiseai session --new "前端项目"
bitwiseai chat
you: /load html-validator
you: 我们使用 React 框架
you: /quit

# 项目 B: 后端开发
bitwiseai session --new "后端项目"
bitwiseai chat
you: /load api-tester
you: 我们使用 FastAPI
you: /quit

# 查看所有项目
bitwiseai session --list
```

### 示例 4: 调试工作流

```bash
bitwiseai chat

# 开始调试
you: 我需要调试这段代码
    def foo(x):
        return x + y

you: /agent "找出代码中的问题"
AI: [Agent 分析...]
    问题: 变量 y 未定义

you: 好的，修复它
    def foo(x, y):
        return x + y

you: /checkpoint "修复完成"
✓ 创建检查点: 1

you: 再优化一下性能
AI: [优化建议...]

you: 不满意，回滚
you: /rollback 1
✓ 已回滚到检查点 1

you: /quit
```

## 高级用法

### 1. 批量加载 Skills

```bash
# 在 shell 中批量加载
for skill in asm_parser error_analyzer hex_converter; do
    bitwiseai skill --load $skill
done
```

### 2. 配合管道使用

```bash
# 从文件读取问题
echo "什么是 MUL 指令？" | bitwiseai chat

# 将结果保存到文件
bitwiseai chat "生成 API 文档" > api_doc.md
```

### 3. 自动加载常用 Skills

在 `~/.bitwiseai/config.json` 中配置：

```json
{
  "skills": {
    "auto_load": ["asm_parser", "hex_converter"],
    "external_directories": ["~/.bitwiseai/skills"]
  }
}
```

### 4. 创建自定义 Skill

```bash
# 1. 创建 Skill 目录
mkdir -p ~/.bitwiseai/skills/my_tool

# 2. 创建 SKILL.md
cat > ~/.bitwiseai/skills/my_tool/SKILL.md << 'EOF'
---
name: my_tool
description: 我的自定义工具
version: 1.0.0
---

# My Tool

这是一个自定义工具...
EOF

# 3. 创建工具脚本
mkdir -p ~/.bitwiseai/skills/my_tool/scripts
cat > ~/.bitwiseai/skills/my_tool/scripts/tools.py << 'EOF'
from bitwiseai.core import tool

@tool
def my_function(text: str) -> str:
    """处理文本"""
    return text.upper()
EOF

# 4. 添加并使用
bitwiseai skill --add-dir ~/.bitwiseai/skills
bitwiseai chat
you: /skills
you: /load my_tool
you: 使用 my_tool 处理 hello
```

## 常见问题

### Q: 如何查看已加载的 Skills？

```bash
bitwiseai skill --list --loaded-only
# 或在交互模式中
you: /skills
```

### Q: 如何在对话中使用工具？

```bash
# 方式 1: 先加载 Skill，再对话
bitwiseai skill --load hex_converter
bitwiseai chat "转换 0xFF"

# 方式 2: 在交互模式中加载
you: /load hex_converter
you: 转换 0xFF
```

### Q: Agent 会自动使用 Skills 吗？

是的！Agent 会自动使用所有已加载的 Skills 中的工具。

```bash
bitwiseai skill --load asm_parser
bitwiseai agent "解析并分析这段代码"
# Agent 会自动调用 asm_parser 的工具
```

### Q: 如何创建检查点？

```bash
# 在交互模式中
you: /checkpoint "重要节点"
✓ 创建检查点: 1

# 或使用 Python API
```

### Q: 会话数据保存在哪里？

```
~/.bitwiseai/sessions/
├── <session-id-1>.jsonl
├── <session-id-2>.jsonl
└── ...
```

## 更多帮助

```bash
# 查看主帮助
bitwiseai --help

# 查看各模式帮助
bitwiseai chat --help
bitwiseai agent --help
bitwiseai skill --help
bitwiseai session --help
bitwiseai config --help
```
