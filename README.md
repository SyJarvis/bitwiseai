# BitwiseAI

<div align="center">

**AI 驱动的智能助手，支持记忆系统、Skill 扩展和 RAG 检索**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.1.3-orange.svg)](bitwiseai/__init__.py)

</div>

BitwiseAI 是一个可扩展的 AI 助手框架，专注于提供智能对话、记忆管理、文档检索和 Skill 扩展能力。支持双层记忆系统（短期/长期）、向量检索增强生成（RAG）、以及灵活的 Skill 系统。

## ✨ 核心特性

### 基础能力
- 🧠 **AI 对话**: 支持多种 LLM 提供商（OpenAI、智谱、MiniMax 等）
- 💾 **双层记忆系统**: 短期记忆（自动清理）+ 长期记忆（持久化存储）
- 📚 **文档管理**: 支持 Markdown、TXT、PDF 文档加载和检索
- 🔧 **Skill 系统**: 模块化扩展，支持自定义工具集成
- 🔍 **RAG 检索**: 基于向量相似度的混合搜索（语义 + 关键词）

### 高级功能
- 🤖 **Agent 模式**: 自动执行复杂任务链
- 💬 **多会话管理**: 独立会话上下文，支持快速切换
- 🌊 **流式输出**: 实时流式对话体验
- 📦 **对话归档**: 一键归档重要对话到长期记忆
- 🎯 **Slash 命令**: 内置命令系统，快速执行常用操作

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/SyJarvis/BitwiseAI.git
cd BitwiseAI

# 安装
pip install -e .
```

## 🚀 快速开始

### 第一步：配置

使用 CLI 生成配置文件：

```bash
bitwiseai config --force
```

然后编辑 `~/.bitwiseai/config.json` 添加 API 密钥。

或使用环境变量：

```bash
export LLM_API_KEY="sk-xxx"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"

export EMBEDDING_API_KEY="sk-xxx"
export EMBEDDING_BASE_URL="https://api.openai.com/v1"
export EMBEDDING_MODEL="text-embedding-3-small"
```

### 第二步：开始使用

#### 方式 1: 命令行工具（推荐）

```bash
# 基础对话
bitwiseai chat "你好"

# 交互式对话
bitwiseai chat

# Agent 模式
bitwiseai agent "分析这段代码"

# Skill 管理
bitwiseai skill --list
bitwiseai skill --load asm-parser

# 会话管理
bitwiseai session --list
```

#### 方式 2: Python 代码

```python
from bitwiseai import BitwiseAI

# 初始化
ai = BitwiseAI()

# 基础对话
response = ai.chat("你好")
print(response)

# 流式对话
for token in ai.chat_stream("介绍一下你自己"):
    print(token, end="", flush=True)
```

## 🆕 v0.1.3 新功能详解

### 1. 双层记忆系统

BitwiseAI 提供强大的记忆管理能力：

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 搜索记忆
results = ai.remember("之前讨论的量化方案")
for r in results:
    print(f"[{r['source']}] {r['content'][:100]}...")

# 添加到长期记忆
ai.memorize("重要决策：使用 PyTorch 2.0 进行模型量化", category="决策")

# 查看记忆统计
stats = ai.get_memory_stats()
print(f"长期记忆条目: {stats['long_term_count']}")
```

### 2. 文档加载与检索

支持加载文件夹或单个文档：

```python
# 加载文件夹中的所有文档
result = ai.load_documents("~/docs/")
print(f"已加载 {result['inserted']} 个文档片段")

# 加载单个文档
result = ai.load_document("~/notes/meeting.md")
print(f"文档已索引: {result['file_path']}")

# 添加文本片段
ai.add_text("这是需要记住的重要内容", source="用户笔记")
```

### 3. 对话归档

在 CLI 中归档重要对话：

```bash
$ bitwiseai chat

你: /archive PyTorch量化讨论
✓ 对话已归档到长期记忆
  标题: PyTorch量化讨论
  消息数: 15
  存储位置: ~/.bitwiseai/MEMORY.md
```

### 4. Skill 系统

BitwiseAI 支持通过 Skill 扩展功能：

```bash
# 列出可用 Skills
bitwiseai skill --list

# 加载 Skill
bitwiseai skill --load asm-parser

# 使用 Skill（在交互模式中）
你: /asm-parser 解析 0x1234567890abcdef
```

内置 Skills：
- `asm-parser`: 汇编指令解析
- `error-analyzer`: 误差分析工具
- `memory-archiver`: 对话归档（自动加载）
- `hex-converter`: 进制转换工具

### 5. Agent 模式

自动执行复杂任务：

```bash
# 使用 Agent
bitwiseai agent "分析项目代码，找出潜在问题"

# 流式输出
bitwiseai agent "生成项目文档" --stream
```

## 📚 使用示例

### 完整工作流示例

```python
import asyncio
from bitwiseai import BitwiseAI

async def complete_workflow():
    # 1. 初始化
    ai = BitwiseAI()

    # 2. 加载 Skills
    ai.load_skill("asm-parser")
    ai.load_skill("error-analyzer")

    # 3. 加载文档到知识库
    ai.load_documents("~/project-docs/")

    # 4. 对话并检索相关知识
    response = ai.chat(
        "解释 MUL 指令的用法",
        use_rag=True  # 使用知识库
    )
    print(response)

    # 5. 保存重要信息到长期记忆
    ai.memorize("MUL 指令用于乘法运算，格式为 MUL Rd, Rn, Rm")

asyncio.run(complete_workflow())
```

### 记忆系统示例

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 短期记忆（7天自动清理）会自动记录对话

# 主动添加到长期记忆
ai.memorize(
    "项目架构决策：使用微服务架构",
    category="架构",
    tags=["决策", "架构", "微服务"]
)

# 搜索记忆
results = ai.remember("微服务架构", max_results=5)
for r in results:
    print(f"来源: {r['source']}, 相关度: {r['score']:.2f}")
```

更多示例请查看：
- **[docs/CLI_USAGE_GUIDE.md](docs/CLI_USAGE_GUIDE.md)** - CLI 完整使用指南
- **[docs/MEMORY_SYSTEM_DESIGN.md](docs/MEMORY_SYSTEM_DESIGN.md)** - 记忆系统设计文档
- **[docs/SKILLS_GUIDE.md](docs/SKILLS_GUIDE.md)** - Skill 开发指南

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    用户交互层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   CLI 工具   │  │  Python API  │  │   Skill 系统 │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                  BitwiseAI 核心层                       │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │  LLM 管理  │  │  RAG 引擎  │  │   Skill 管理器   │  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ 记忆管理器 │  │ 文档管理器 │  │   对话引擎       │  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                  数据存储层                             │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │
│  │ SQLite DB  │  │ 向量索引   │  │   记忆文件       │  │
│  │ (metadata) │  │ (semantic) │  │ (MEMORY.md)      │  │
│  └────────────┘  └────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🛠️ CLI 命令参考

### chat - 对话模式

```bash
# 单次查询
bitwiseai chat "你的问题"

# 交互模式
bitwiseai chat

# 使用 RAG 检索
bitwiseai chat --use-rag "根据文档回答..."
```

**交互模式命令：**
```
/help              - 显示帮助
/clear             - 清空上下文
/archive [标题]    - 归档当前对话到长期记忆
/skills            - 列出所有 Skills
/load <skill>      - 加载 Skill
/unload <skill>    - 卸载 Skill
/agent             - 使用 Agent 模式
/quit              - 退出
```

### agent - Agent 模式

```bash
# 自动执行任务
bitwiseai agent "任务描述"

# 流式输出
bitwiseai agent "任务描述" --stream
```

### skill - Skill 管理

```bash
# 列出所有 Skills
bitwiseai skill --list
bitwiseai skill --list --loaded-only

# 加载/卸载 Skill
bitwiseai skill --load <skill-name>
bitwiseai skill --unload <skill-name>

# 搜索 Skills
bitwiseai skill --search "关键词"

# 添加外部技能目录
bitwiseai skill --add-dir ~/.bitwiseai/skills
```

### session - 会话管理

```bash
# 列出所有会话
bitwiseai session --list

# 创建新会话
bitwiseai session --new "项目名称"

# 切换会话
bitwiseai session --switch <session-id>

# 删除会话
bitwiseai session --delete <session-id>
```

### memory - 记忆管理（交互模式）

```bash
# 在交互模式中使用
你: /archive 重要讨论    # 归档当前对话
```

## 📖 Python API 参考

### 基础对话

```python
# 非流式对话
ai.chat(query, use_rag=True)

# 流式对话
for token in ai.chat_stream(query):
    print(token, end="")
```

### 记忆系统

```python
# 搜索记忆
ai.remember(query, max_results=5)

# 添加到长期记忆
ai.memorize(content, category="一般", tags=[])

# 查看记忆统计
ai.get_memory_stats()

# 整理短期记忆（归档过期内容）
ai.compact_short_term()
```

### 文档管理

```python
# 加载文件夹
ai.load_documents(folder_path, skip_duplicates=True)

# 加载单个文档（仅支持 .md, .txt）
ai.load_document(file_path)

# 添加文本
ai.add_text(text, source="自定义")

# 清空知识库
ai.clear_memory_db()
```

### Skill 管理

```python
# 加载 Skill
ai.load_skill(name)

# 卸载 Skill
ai.unload_skill(name)

# 列出 Skills
ai.list_skills(loaded_only=False)

# 搜索 Skills
ai.search_skills(query, top_k=5)
```

### Agent 模式

```python
import asyncio

# Agent 模式
response = await ai.chat_with_agent(query)

# 流式 Agent
async for token in ai.chat_with_agent_stream(query):
    print(token, end="")
```

## 📁 项目结构

```
bitwiseai/
├── __init__.py                  # 包入口
├── bitwiseai.py                 # 核心类
├── cli.py                       # 命令行接口
├── core/                        # 核心模块
│   ├── chat_engine.py           # 聊天引擎
│   ├── enhanced_chat.py         # 增强版聊天引擎
│   ├── rag_engine.py            # RAG 引擎
│   ├── skill_manager.py         # Skill 管理器
│   ├── document_manager.py      # 文档管理器
│   ├── memory/                  # 记忆系统
│   │   ├── manager.py           # 记忆管理器
│   │   ├── indexer.py           # 文档索引器
│   │   ├── searcher.py          # 记忆搜索器
│   │   └── storage.py           # SQLite 存储
│   ├── llm/                     # LLM 管理
│   │   └── llm_manager.py       # LLM 管理器
│   └── agent/                   # Agent 系统
│       ├── executor.py          # 步骤执行器
│       └── loop.py              # Agent 主循环
└── skills/                      # Skills 目录
    ├── asm-parser/              # ASM 解析 Skill
    ├── error-analyzer/          # 错误分析 Skill
    ├── memory-archiver/         # 对话归档 Skill
    └── builtin/                 # 内置 Skills
```

## ⚙️ 配置

配置文件位于 `~/.bitwiseai/config.json`：

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
  "memory": {
    "enabled": true,
    "db_path": "~/.bitwiseai/memory.db",
    "vector_enabled": true,
    "chunking": {
      "tokens": 400,
      "overlap": 80
    },
    "hybrid_search": {
      "enabled": true,
      "vector_weight": 0.7,
      "text_weight": 0.3
    },
    "sync": {
      "watch": true,
      "watch_debounce_ms": 1000
    },
    "short_term": {
      "enabled": true,
      "retention_days": 7
    }
  },
  "skills": {
    "auto_load": [],
    "external_directories": ["~/.bitwiseai/skills"]
  }
}
```

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

## 📄 许可证

MIT License

## 🔗 相关资源

- [CLI 使用指南](docs/CLI_USAGE_GUIDE.md)
- [记忆系统设计](docs/MEMORY_SYSTEM_DESIGN.md)
- [Skill 开发指南](docs/SKILLS_GUIDE.md)

---

**BitwiseAI v0.1.3** - 让 AI 记住每一次对话 🚀
