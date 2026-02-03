# BitwiseAI 使用指南

## 概述

BitwiseAI 是专注于硬件指令验证、日志解析和智能分析的 AI 工具库，支持 RAG 检索、Skill 系统、双层次记忆系统等高级功能。

## 目录

- [1. 配置文件](#1-配置文件)
- [2. 快速开始](#2-快速开始)
- [3. 加载文档](#3-加载文档)
- [4. 对话功能](#4-对话功能)
- [5. RAG 检索](#5-rag-检索)
- [6. Skill 系统](#6-skill-系统)
- [7. 记忆系统](#7-记忆系统)
- [8. API 参考](#8-api-参考)

---

## 1. 配置文件

### 1.1 配置文件位置

默认配置文件路径：`~/.bitwiseai/config.json`

### 1.2 配置文件格式

```json
{
    "llm": {
        "model": "glm-4.7",
        "temperature": 0.7,
        "api_key": "your-api-key",
        "base_url": "https://open.bigmodel.cn/api/paas/v4"
    },
    "embedding": {
        "model": "Qwen/Qwen3-Embedding-8B",
        "api_key": "your-api-key",
        "base_url": "https://api-inference.modelscope.cn/v1"
    },
    "memory": {
        "workspace_dir": "~/.bitwiseai",
        "db_path": "~/.bitwiseai/memory.db",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "auto_index": true
    },
    "rag": {
        "similarity_threshold": 0.85,
        "save_chunks": false,
        "chunks_dir": "~/.bitwiseai/chunks",
        "enable_document_name_matching": true,
        "document_name_match_threshold": 0.3
    },
    "system_prompt": "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。",
    "skills": {
        "auto_load": ["asm-parser"],
        "external_directories": ["~/.bitwiseai/skills"],
        "index_to_memory": true
    }
}
```

### 1.3 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `llm.model` | LLM 模型名称 | gpt-4o-mini |
| `llm.temperature` | 生成温度 | 0.7 |
| `llm.api_key` | LLM API 密钥 | - |
| `llm.base_url` | LLM API 地址 | - |
| `embedding.model` | 嵌入模型名称 | text-embedding-3-small |
| `embedding.api_key` | 嵌入 API 密钥 | - |
| `memory.workspace_dir` | 工作目录 | ~/.bitwiseai |
| `memory.db_path` | 数据库路径 | ~/.bitwiseai/memory.db |
| `rag.similarity_threshold` | 相似度阈值 | 0.85 |

---

## 2. 快速开始

### 2.1 安装与配置

```bash
# 生成默认配置文件
bitwiseai config --force

# 编辑配置文件，填入 API 密钥
vim ~/.bitwiseai/config.json
```

### 2.2 基础使用示例

```python
from bitwiseai import BitwiseAI

# 使用默认配置创建 Bot
ai = BitwiseAI()

# 简单对话
response = ai.chat("什么是 MUL 指令？")
print(response)
```

### 2.3 使用自定义配置

```python
from bitwiseai import BitwiseAI

# 指定自定义配置文件
ai = BitwiseAI(config_path="./my_config.json")

# 或使用增强版引擎（支持 Agent、会话等）
ai = BitwiseAI(use_enhanced=True)
```

---

## 3. 加载文档

### 3.1 加载文件夹文档

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 加载整个文件夹的文档
result = ai.load_documents("/path/to/docs", skip_duplicates=True)
print(f"加载结果: {result}")
```

### 3.2 添加单个文本

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 添加单个文本到知识库
ai.add_text("""
MUL 指令说明
============
语法: MUL Rd, Rn, Rm
- Rd: 目标寄存器
- Rn: 第一个操作数寄存器
- Rm: 第二个操作数寄存器

约束:
- Rd 和 Rn 不能是同一个寄存器
- 所有寄存器必须是 32 位通用寄存器
""", source="mul_instruction.txt")
```

### 3.3 加载规范文档

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 加载规范文档（支持文件或文件夹）
ai.load_specification("./hardware_specs.md")     # 单个文件
ai.load_specification("./specs_folder/")         # 整个文件夹
```

### 3.4 批量添加文档

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

documents = {
    "ADD 指令": """
    ADD 指令说明
    语法: ADD Rd, Rn, Rm
    用于执行加法运算
    """,
    "SUB 指令": """
    SUB 指令说明
    语法: SUB Rd, Rn, Rm
    用于执行减法运算
    """,
}

for title, content in documents.items():
    ai.add_text(content, source=title)
    print(f"已添加: {title}")
```

---

## 4. 对话功能

### 4.1 基础对话

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 非流式对话
response = ai.chat("什么是 MUL 指令？")
print(response)
```

### 4.2 流式对话

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 流式输出
print("AI 回答: ", end="", flush=True)
for token in ai.chat_stream("介绍一下你自己"):
    print(token, end="", flush=True)
print()
```

### 4.3 带历史记录的对话

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 构建对话历史
history = [
    {"role": "user", "content": "我叫 Alice"},
    {"role": "assistant", "content": "你好 Alice！很高兴认识你。"},
    {"role": "user", "content": "我是一名硬件工程师"},
    {"role": "assistant", "content": "太好了！我可以帮你分析硬件相关问题。"},
]

# 基于历史继续对话
response = ai.chat(
    "刚才我说我叫什么名字？",
    history=history
)
print(response)
```

### 4.4 控制 RAG 和工具

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 关闭 RAG 检索
response = ai.chat("你好", use_rag=False)

# 关闭工具调用
response = ai.chat("你好", use_tools=False)

# 同时关闭
response = ai.chat("你好", use_rag=False, use_tools=False)
```

---

## 5. RAG 检索

### 5.1 基础 RAG 对话

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 先加载文档
ai.load_documents("./hardware_specs")

# 使用 RAG 模式对话（自动检索相关文档）
response = ai.chat(
    "MUL 指令的寄存器约束是什么？",
    use_rag=True
)
print(response)
```

### 5.2 直接检索上下文

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 直接查询 RAG 引擎获取相关上下文
context = ai.rag_engine.search("MUL 指令用法", top_k=3)
print(context)
```

### 5.3 带元数据的检索

```python
from bitwiseai import BitwiseAI
from pathlib import Path

ai = BitwiseAI()

# 使用 search_with_metadata 获取详细信息
results = ai.rag_engine.search_with_metadata(
    "乘法指令",
    top_k=5,
    use_hybrid=True  # 使用混合检索（向量 + 关键词）
)

for i, result in enumerate(results, 1):
    source = result.get('source_file', '未知')
    score = result.get('score', 0.0)
    text = result.get('text', '')[:100]
    print(f"{i}. 来源: {Path(source).name}")
    print(f"   相似度: {score:.4f}")
    print(f"   内容: {text}...")
```

### 5.4 清空向量数据库

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 清空所有已加载的文档
ai.clear_memory_db()
```

---

## 6. Skill 系统

### 6.1 列出可用 Skills

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 列出所有可用 Skills
all_skills = ai.list_skills()
print(f"可用 Skills: {all_skills}")

# 只列出已加载的 Skills
loaded_skills = ai.list_skills(loaded_only=True)
print(f"已加载 Skills: {loaded_skills}")
```

### 6.2 加载和卸载 Skill

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 加载 Skill
success = ai.load_skill("asm-parser")
print(f"加载成功: {success}")

# 卸载 Skill
success = ai.unload_skill("asm-parser")
print(f"卸载成功: {success}")
```

### 6.3 搜索 Skills

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 搜索相关技能
results = ai.search_skills("汇编解析", top_k=5)
for skill in results:
    print(f"Skill: {skill['name']}, 相关度: {skill['score']}")
```

### 6.4 使用 Skill 进行对话

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 加载 Skill
ai.load_skill("asm-parser")

# 使用工具进行对话
response = ai.chat(
    "帮我解析这段汇编代码: MOV R0, #0x10",
    use_tools=True
)
print(response)
```

---

## 7. 记忆系统

### 7.1 追加到记忆

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 追加到短期记忆（默认）
ai.append_to_memory("今天分析了 MUL 指令的错误")

# 直接追加到长期记忆
ai.append_to_memory("重要的硬件设计规范", to_long_term=True)
```

### 7.2 搜索记忆

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 搜索记忆系统
results = ai.search_memory("MUL 指令", max_results=5)
for result in results:
    print(f"内容: {result['text'][:50]}...")
    print(f"来源: {result['path']}")
    print(f"分数: {result['score']}")
```

### 7.3 获取记忆统计

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 获取记忆系统统计
stats = ai.get_memory_stats()
print(f"总文件数: {stats['total_files']}")
print(f"总块数: {stats['total_chunks']}")
print(f"总向量数: {stats['total_vectors']}")
print(f"数据库大小: {stats['db_size_bytes']} bytes")
```

### 7.4 压缩记忆

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 压缩短期记忆（保留最近 7 天）
result = ai.compact_memory(days_to_keep=7)
print(f"压缩文件数: {result['files_compacted']}")
print(f"归档文件数: {result['files_archived']}")
```

---

## 8. API 参考

### 8.1 BitwiseAI 类

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `__init__` | `config_path`, `use_enhanced` | BitwiseAI | 初始化 Bot |
| `chat` | `query`, `use_rag`, `use_tools`, `history` | str | 非流式对话 |
| `chat_stream` | `query`, `use_rag`, `use_tools`, `history` | Iterator[str] | 流式对话 |
| `load_documents` | `folder_path`, `skip_duplicates` | Dict | 加载文件夹文档 |
| `add_text` | `text`, `source` | int | 添加单个文本 |
| `load_specification` | `spec_path` | None | 加载规范文档 |
| `clear_memory_db` | - | None | 清空向量数据库 |
| `load_skill` | `name` | bool | 加载 Skill |
| `unload_skill` | `name` | bool | 卸载 Skill |
| `list_skills` | `loaded_only` | List[str] | 列出 Skills |
| `search_skills` | `query`, `top_k` | List[Dict] | 搜索 Skills |
| `append_to_memory` | `content`, `to_long_term` | None | 追加到记忆 |
| `search_memory` | `query`, `max_results` | List[Dict] | 搜索记忆 |
| `get_memory_stats` | - | Dict | 记忆统计 |
| `compact_memory` | `days_to_keep` | Dict | 压缩记忆 |
| `close` | - | None | 释放资源 |

### 8.2 RAGEngine API

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `load_documents` | `folder_path`, `skip_duplicates` | Dict | 加载文档 |
| `add_text` | `text`, `source` | int | 添加文本 |
| `search` | `query`, `top_k` | str | 检索文本 |
| `search_with_metadata` | `query`, `top_k`, `use_hybrid` | List[Dict] | 带元数据检索 |
| `clear` | - | None | 清空数据库 |

### 8.3 配置参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `config_path` | str | 配置文件路径，默认 ~/.bitwiseai/config.json |
| `use_enhanced` | bool | 是否使用增强版引擎，默认 True |
| `use_rag` | bool | 是否启用 RAG 检索，默认 True |
| `use_tools` | bool | 是否启用工具调用，默认 True |
| `skip_duplicates` | bool | 是否跳过重复文档，默认 True |
| `top_k` | int | 返回最相关的 k 个结果 |
| `to_long_term` | bool | 是否写入长期记忆 |

---

## 9. 完整示例

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BitwiseAI 完整使用示例"""

from bitwiseai import BitwiseAI

def main():
    # 1. 创建 Bot
    ai = BitwiseAI(use_enhanced=True)

    # 2. 加载文档到知识库
    print("加载文档...")
    ai.load_documents("./docs")
    ai.add_text("额外的上下文信息", source="extra_context")

    # 3. 进行 RAG 对话
    print("\n进行对话...")
    response = ai.chat(
        "根据文档解释 MUL 指令的用法",
        use_rag=True
    )
    print(f"AI: {response}")

    # 4. 加载 Skill 并使用
    print("\n加载 Skill...")
    ai.load_skill("asm-parser")
    response = ai.chat(
        "解析 MOV R0, #0x10",
        use_tools=True
    )
    print(f"AI: {response}")

    # 5. 追加到记忆
    print("\n追加到记忆...")
    ai.append_to_memory("用户询问了 MUL 指令")

    # 6. 搜索记忆
    print("\n搜索记忆...")
    results = ai.search_memory("MUL")
    for r in results:
        print(f"  - {r['text'][:50]}...")

    # 7. 清理资源
    ai.close()
    print("\n完成!")

if __name__ == "__main__":
    main()
```

---

## 10. 常见问题

### Q: 配置文件不存在怎么办？

```bash
# 运行以下命令生成默认配置
bitwiseai config --force
```

### Q: 如何切换不同的 LLM 模型？

编辑 `~/.bitwiseai/config.json` 中的 `llm.model` 字段：

```json
{
    "llm": {
        "model": "gpt-4o",  // 或其他模型
        "api_key": "your-key",
        "base_url": "https://api.openai.com/v1"
    }
}
```

### Q: 如何查看已加载的文档？

```python
stats = ai.get_memory_stats()
print(f"已索引文件数: {stats['total_files']}")
print(f"已索引块数: {stats['total_chunks']}")
```

### Q: 流式对话如何处理？

```python
for token in ai.chat_stream("你的问题"):
    print(token, end="", flush=True)
print()  # 最后换行
```

---

*文档版本: 1.0*
*更新日期: 2026-02-03*
