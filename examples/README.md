# BitwiseAI 使用示例

本目录包含 BitwiseAI 的完整使用示例，涵盖所有主要功能。

## 示例列表

### 基础示例
```bash
# 运行基础示例
python examples/basic_usage.py [1-7]

1. 最简单的对话
2. 流式对话
3. 使用 RAG 检索
4. 使用 Skills
5. 带历史记录的对话
6. 配置说明
7. 错误处理
```

### Agent 示例
```bash
# 运行 Agent 示例
python examples/agent_usage.py [1-10]

1. 基础 Agent 使用
2. 多轮对话 Agent
3. 流式 Agent 输出
4. 带工具的 Agent
5. 启用思考模式
6. Agent 配合检查点
7. 独立会话中使用 Agent
8. 各种 Agent 配置
9. CLI 使用 Agent
10. 完整工作流
```

### 会话管理示例
```bash
# 运行会话管理示例
python examples/session_usage.py [1-9]

1. 创建多个会话
2. 切换会话
3. 会话配合检查点
4. 会话生命周期管理
5. 会话持久化
6. 隔离不同上下文
7. CLI 会话管理
8. 在会话中使用 Agent
9. 完整工作流
```

### RAG 使用示例
```bash
# 运行 RAG 示例
python examples/rag_usage.py [1-11]

1. 加载文档
2. 基础 RAG 查询
3. 查看检索上下文
4. 带元数据的检索
5. RAG 配合历史
6. 批量添加文档
7. RAG 配合工具
8. 清空向量库
9. RAG 配置
10. 文档类型
11. 完整工作流
```

### Skill 使用示例
```bash
# 运行 Skill 示例
python examples/skill_usage.py [1-12]

1. 列出所有 Skills
2. 加载和卸载 Skills
3. 使用 Skill 工具
4. 搜索相关 Skills
5. 添加外部目录
6. Skill 配合 RAG
7. 创建自定义 Skill
8. 查看 Skill 元数据
9. Skill 配合 Agent
10. 内置 Skills 介绍
11. CLI Skill 管理
12. 完整工作流
```

### 完整工作流示例
```bash
# 运行完整工作流
python examples/complete_workflow.py [1-8]

1. 代码审查项目
2. 学习硬件指令
3. 使用检查点调试
4. 多项目管理
5. 文档生成
6. 学习路径规划
7. CLI 使用演示
8. 协作调试
```

## 快速开始

### 1. 配置环境

首先设置 API 密钥：

```bash
export LLM_API_KEY="sk-xxx"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"

export EMBEDDING_API_KEY="sk-xxx"
export EMBEDDING_BASE_URL="https://api.openai.com/v1"
export EMBEDDING_MODEL="text-embedding-3-small"
```

或使用配置文件：

```bash
bitwiseai config --force
```

### 2. 运行示例

```bash
# 查看所有可用示例
python examples/basic_usage.py

# 运行特定示例
python examples/basic_usage.py 1

# 使用 Agent
python examples/agent_usage.py 1

# 会话管理
python examples/session_usage.py 1

# RAG 检索
python examples/rag_usage.py 1

# Skill 管理
python examples/skill_usage.py 1

# 完整工作流
python examples/complete_workflow.py 1
```

### 3. 使用 CLI

```bash
# 基础对话
bitwiseai chat "你好"

# 交互模式
bitwiseai chat

# Agent 模式
bitwiseai agent "分析这段代码"

# Skill 管理
bitwiseai skill --list

# 会话管理
bitwiseai session --list
bitwiseai session --new "我的项目"
```

## 学习路径

建议按以下顺序学习：

1. **基础使用** (`basic_usage.py`)
   - 了解基本的对话功能
   - 学习配置方法
   - 掌握流式输出

2. **会话管理** (`session_usage.py`)
   - 学习多会话管理
   - 掌握检查点回滚
   - 理解会话持久化

3. **RAG 检索** (`rag_usage.py`)
   - 学习文档加载
   - 掌握向量检索
   - 理解混合检索

4. **Skill 系统** (`skill_usage.py`)
   - 了解内置 Skills
   - 学习使用工具
   - 掌握 Skill 搜索

5. **Agent 系统** (`agent_usage.py`)
   - 学习 Agent 循环
   - 掌握多轮对话
   - 理解 Agent 配置

6. **完整工作流** (`complete_workflow.py`)
   - 综合运用所有功能
   - 解决实际问题

## 常见问题

### Q: 如何加载自己的文档？

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()
ai.load_documents("~/Documents/my_docs", skip_duplicates=True)
```

### Q: 如何创建自定义 Skill？

参见 `skill_usage.py` 示例 7，或查看：
```bash
cat bitwiseai/skills/asm_parser/SKILL.md
```

### Q: 如何使用 Agent 进行复杂任务？

```python
from bitwiseai import BitwiseAI
from bitwiseai.core import AgentConfig, LoopConfig
import asyncio

ai = BitwiseAI(use_enhanced=True)

result = asyncio.run(ai.chat_with_agent(
    "你的复杂任务描述",
    agent_config=AgentConfig(
        name="my_agent",
        system_prompt="你是专家助手",
        max_steps=10,
    ),
))
```

### Q: 会话数据保存在哪里？

会话数据保存在 `~/.bitwiseai/sessions/` 目录，每个会话对应一个 `.jsonl` 文件。

### Q: 如何清空向量数据库？

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()
ai.clear_vector_db()
```

## 进阶技巧

### 1. 组合使用多种功能

```python
# 同时使用 RAG、工具和会话
ai = BitwiseAI(use_enhanced=True)
await ai.new_session("代码分析")
ai.load_documents("./docs")
ai.load_skill("code_analyzer")

result = await ai.chat_with_agent(
    "分析代码并参考文档",
    agent_config=AgentConfig(max_steps=10),
)
```

### 2. 使用检查点进行实验

```python
# 创建实验分支
cp = ai.create_checkpoint("实验开始")
# 尝试新方法
ai.chat("尝试方案 A")
# 不满意，回滚
ai.rollback_to_checkpoint(cp)
# 尝试方案 B
ai.chat("尝试方案 B")
```

### 3. 多项目隔离

```python
# 为每个项目创建独立会话
session_a = await ai.new_session("项目 A")
await ai.switch_session(session_a.info.session_id)
# 在项目 A 中工作...

session_b = await ai.new_session("项目 B")
await ai.switch_session(session_b.info.session_id)
# 在项目 B 中工作...
```

## 更多资源

- [主 README](../README.md) - 项目总览
- [CLI 指南](../bitwiseai/cli.py) - 命令行工具
- [核心模块](../bitwiseai/core/) - 核心实现
- [内置 Skills](../bitwiseai/skills/) - 可用技能

## 反馈与贡献

如有问题或建议，欢迎提交 Issue 或 Pull Request！
