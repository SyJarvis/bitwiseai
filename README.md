# BitwiseAI

<div align="center">

**硬件调试和日志分析的 AI 工具**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

BitwiseAI 是一个专注于硬件指令验证和调试日志分析的 AI 工具库。它提供了灵活的接口，让用户可以轻松地将 AI 能力嵌入到自己的调试工作流中。

## ✨ 核心特性

- 🎯 **可嵌入式设计**: 提供清晰的接口，让用户在自己的项目中定义解析器、验证器和任务
- 🧠 **AI 辅助分析**: 基于 LangChain，支持 LLM 和 RAG 技术进行智能分析
- 🔧 **灵活的工具系统**: 支持注册 Python 函数、Shell 命令和 LangChain Tools
- 📊 **任务编排**: 定义和执行复杂的日志分析任务
- 📝 **自动报告生成**: 支持 Markdown、JSON 等多种格式的分析报告

## 🎨 设计理念

BitwiseAI **不是**一个提供现成解决方案的工具，而是一个**可扩展的框架**：

- ✅ 你定义如何解析日志（实现 `LogParserInterface`）
- ✅ 你定义如何验证数据（实现 `VerifierInterface`）
- ✅ 你定义分析任务流程（继承 `AnalysisTask`）
- ✅ BitwiseAI 提供 LLM、RAG、工具管理等基础能力

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/SyJarvis/BitwiseAI.git
cd BitwiseAI

# 安装
pip install -e .

# 或使用安装脚本
bash install.sh
```

## 🚀 快速开始

### 第一步：安装

```bash
# 克隆仓库
git clone https://github.com/SyJarvis/BitwiseAI.git
cd BitwiseAI

# 安装
pip install -e .
```

### 第二步：配置

首次使用需要生成配置文件：

```bash
# 交互式生成配置文件
bitwiseai --generate-config
```

这会引导你输入以下信息：
- **LLM API Key** 和 **Base URL**（如 OpenAI、MiniMax 等）
- **Embedding API Key** 和 **Base URL**
- **模型名称**和参数
- **向量数据库**配置
- **系统提示词**（可选）

配置文件保存在 `~/.bitwiseai/config.json`

> 💡 **提示**：也可以使用 `.env` 文件配置 API 密钥，详见下方说明。

### 第三步：开始使用

#### 方式 1: 命令行工具（推荐）

```bash
# 单次对话
bitwiseai chat "什么是 MUL 指令？"

# 交互式对话
bitwiseai chat

# 查看帮助
bitwiseai --help
```

#### 方式 2: Python 代码

```python
from bitwiseai import BitwiseAI

# 初始化
ai = BitwiseAI()

# 基础对话
response = ai.chat("什么是 MUL 指令？")
print(response)

# 加载规范文档到知识库（可选）
ai.load_specification("./docs/hardware_spec.pdf")

# 使用 RAG 模式对话
response = ai.chat("MUL 指令的参数有哪些？", use_rag=True)
print(response)
```

## 📋 工作流程

BitwiseAI 的典型工作流程如下：

```
┌─────────────────────────────────────────────────────────┐
│  1. 安装和配置                                            │
│     - 安装 BitwiseAI                                    │
│     - 运行 bitwiseai --generate-config 配置 API         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  2. 准备数据（可选）                                       │
│     - 加载规范文档到向量数据库（RAG）                      │
│     - 准备日志文件（如果需要分析）                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  3. 实现业务逻辑（在你的项目中）                           │
│     - 实现 LogParserInterface（解析日志）                 │
│     - 实现 VerifierInterface（验证数据）                  │
│     - 创建 AnalysisTask（定义分析任务）                   │
│     - 开发 Skills（扩展工具能力）                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  4. 使用 BitwiseAI                                       │
│     - 初始化 BitwiseAI                                   │
│     - 注册任务和工具                                      │
│     - 执行分析或对话                                      │
│     - 生成报告                                           │
└─────────────────────────────────────────────────────────┘
```

### 详细工作流程示例

#### 场景 1: 基础对话和 RAG 查询

```python
from bitwiseai import BitwiseAI

# 1. 初始化
ai = BitwiseAI()

# 2. 加载规范文档（可选）
ai.load_documents("./docs/hardware_spec/")

# 3. 使用 RAG 模式对话
response = ai.chat("MUL 指令的参数有哪些？", use_rag=True)
print(response)
```

#### 场景 2: 自定义分析任务

```python
from bitwiseai import BitwiseAI
from bitwiseai.interfaces import AnalysisTask, AnalysisResult

# 1. 定义自定义任务
class MyLogAnalysisTask(AnalysisTask):
    def analyze(self, context, parsed_data):
        # 实现你的分析逻辑
        results = []
        # ... 分析代码 ...
        return results

# 2. 使用任务
ai = BitwiseAI()
ai.load_log_file("test.log")
ai.register_task(MyLogAnalysisTask())
results = ai.execute_all_tasks()

# 3. 生成报告
ai.save_report("report.md")
```

#### 场景 3: 使用 Skills 扩展功能

```python
from bitwiseai import BitwiseAI

# 1. 初始化
ai = BitwiseAI()

# 2. 查看可用 Skills
skills = ai.list_skills()
print(f"可用 Skills: {skills}")

# 3. 加载 Skill（如果已创建）
ai.load_skill("my_custom_skill")

# 4. 在对话中使用工具
response = ai.chat("使用 my_tool 处理数据", use_tools=True)
print(response)
```

### 使用 .env 文件配置（可选）

除了交互式配置，你也可以使用 `.env` 文件：

```bash
# .env 文件
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-api-endpoint/v1

EMBEDDING_API_KEY=your-api-key
EMBEDDING_BASE_URL=https://your-api-endpoint/v1
```

BitwiseAI 会自动读取 `.env` 文件中的配置。


## 📚 使用示例

更多详细示例请查看 `examples/` 目录：

- **[基础使用示例](examples/basic_usage.py)** - 初始化、对话、工具调用
- **[RAG 使用示例](examples/rag_usage.py)** - 文档加载、检索、RAG 对话
- **[自定义 Skill 示例](examples/custom_skill_example.py)** - 创建和使用自定义 Skills
- **[文档导出示例](examples/document_export.py)** - 导出向量数据库中的文档

### 示例 1: RAG 规范查询

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 加载硬件规范文档
ai.load_documents("./docs/hardware_manual/")

# 查询规范
context = ai.query_specification("MUL 指令的 func_sel 参数含义", top_k=5)
print(context)

# 使用 RAG 模式对话
response = ai.chat("如何验证 SHIFT 指令？", use_rag=True)
print(response)
```

### 示例 2: 自定义分析任务

```python
from bitwiseai import BitwiseAI
from bitwiseai.interfaces import AnalysisTask, AnalysisResult

class MyLogAnalysisTask(AnalysisTask):
    """自定义日志分析任务"""
    
    def analyze(self, context, parsed_data):
        """实现你的分析逻辑"""
        results = []
        
        # 读取日志
        if context.log_file_path:
            with open(context.log_file_path, 'r') as f:
                log_content = f.read()
            
            # 执行分析
            error_count = log_content.count("ERROR")
            
            # 返回结果
            results.append(AnalysisResult(
                status="pass" if error_count == 0 else "fail",
                message=f"发现 {error_count} 个错误",
                data={"error_count": error_count}
            ))
        
        return results

# 使用任务
ai = BitwiseAI()
ai.load_log_file("test.log")
ai.register_task(MyLogAnalysisTask())
results = ai.execute_all_tasks()

# 生成报告
ai.save_report("report.md", format="markdown")
```

### 示例 3: 使用 Skills 扩展功能

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 查看可用 Skills
skills = ai.list_skills()
print(f"可用 Skills: {skills}")

# 加载 Skill
ai.load_skill("hex_converter")

# 在对话中使用工具（自动调用）
response = ai.chat("将十六进制 0xFF 转换为十进制", use_tools=True)
print(response)
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────┐
│                   你的项目                        │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ 自定义解析器  │  │ 自定义验证器  │             │
│  └──────────────┘  └──────────────┘             │
│  ┌──────────────────────────────────┐            │
│  │      自定义分析任务                │            │
│  └──────────────────────────────────┘            │
└─────────────────┬───────────────────────────────┘
                  │ 调用
                  ▼
┌─────────────────────────────────────────────────┐
│               BitwiseAI 核心                      │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │  LLM 引擎  │  │  RAG 引擎  │  │ 工具系统  │  │
│  └────────────┘  └────────────┘  └──────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │  任务管理  │  │ 报告生成   │  │ 向量数据库│  │
│  └────────────┘  └────────────┘  └──────────┘  │
└─────────────────────────────────────────────────┘
```

## 📖 核心接口

### LogParserInterface

```python
class LogParserInterface(ABC):
    @abstractmethod
    def parse_file(self, file_path: str) -> Any:
        """解析日志文件"""
        pass
    
    @abstractmethod
    def parse_text(self, text: str) -> Any:
        """解析日志文本"""
        pass
```

### VerifierInterface

```python
class VerifierInterface(ABC):
    @abstractmethod
    def verify(self, data: Any) -> List[AnalysisResult]:
        """验证数据"""
        pass
```

### TaskInterface

```python
class TaskInterface(ABC):
    @abstractmethod
    def execute(self, context: BitwiseAI) -> List[AnalysisResult]:
        """执行任务"""
        pass
```

## 🛠️ API 参考

### Skills 管理

- `load_skill(name)` - 加载 Skill
- `unload_skill(name)` - 卸载 Skill
- `list_skills(loaded_only=False)` - 列出所有 Skills
- `invoke_tool(name, *args, **kwargs)` - 调用工具（来自已加载的 Skills）
- `list_tools()` - 列出所有可用工具

### 任务管理

- `register_task(task)` - 注册任务
- `execute_task(task)` - 执行单个任务
- `execute_all_tasks()` - 执行所有任务
- `list_tasks()` - 列出所有任务

### 文档和 RAG

- `load_documents(folder_path, skip_duplicates=True)` - 加载文档到向量数据库
- `load_specification(spec_path)` - 加载规范文档（文件或目录）
- `query_specification(query, top_k=5)` - 查询规范文档
- `load_log_file(file_path)` - 加载日志文件（用于任务分析）
- `ask_about_log(question)` - 询问关于日志的问题

### 报告生成

- `generate_report(format)` - 生成报告
- `save_report(file_path, format)` - 保存报告

### LLM 对话

- `chat(query, use_rag=True, use_tools=True)` - 对话（支持 RAG 和工具调用）
- `chat_stream(query, use_rag=True, use_tools=True)` - 流式对话
- `analyze_with_llm(prompt, use_rag=True)` - AI 辅助分析

## 📁 项目结构

```
bitwiseai/
├── __init__.py              # 包入口
├── bitwiseai.py             # 核心类
├── cli.py                   # 命令行接口
├── interfaces.py            # 接口定义（LogParserInterface, VerifierInterface, TaskInterface）
├── llm.py                   # LLM 封装
├── embedding.py             # Embedding 封装
├── vector_database.py       # 向量数据库（Milvus）
├── utils.py                 # 工具函数
├── core/                    # 核心模块
│   ├── chat_engine.py       # 聊天引擎
│   ├── rag_engine.py        # RAG 引擎
│   ├── skill_manager.py     # Skill 管理器
│   └── document_manager.py  # 文档管理器
└── skills/                  # Skills 目录
    ├── asm_parser/          # ASM 解析 Skill
    └── builtin/             # 内置 Skills
        └── hex_converter/   # 十六进制转换 Skill

examples/
├── basic_usage.py           # 基础使用示例
├── rag_usage.py             # RAG 使用示例
├── custom_skill_example.py  # 自定义 Skill 示例
└── document_export.py      # 文档导出示例
```

## ⚙️ 配置

配置文件位于 `~/.bitwiseai/config.json`:

```json
{
  "llm": {
    "model": "MiniMax-M2.1",
    "temperature": 0.7
  },
  "embedding": {
    "model": "Qwen/Qwen3-Embedding-8B"
  },
  "vector_db": {
    "db_file": "~/.bitwiseai/milvus_data.db",
    "collection_name": "bitwiseai_specs",
    "embedding_dim": 4096
  },
  "system_prompt": "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。",
  "tools": []
}
```

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

## 📄 许可证

MIT License

## 📚 文档

详细的文档和指南：

- [使用指南](docs/USAGE_GUIDE.md) - 基本使用方法和示例
- [**文档管理指南**](docs/DOCUMENT_MANAGEMENT_GUIDE.md) - 文档加载、切分、检索、导出完整指南 ⭐
- [CLI 指南](docs/CLI_GUIDE.md) - 命令行工具使用说明
- [架构文档](docs/ARCHITECTURE.md) - 系统架构和设计理念
- [依赖说明](docs/DEPENDENCIES.md) - 依赖包和版本要求
- [**Skills 开发指南**](docs/SKILLS_GUIDE.md) - 如何创建和添加新的 Skills ⭐

## 🔗 相关资源

- [LangChain 文档](https://python.langchain.com/)
- [Milvus 文档](https://milvus.io/docs)

---

**BitwiseAI** - 让 AI 成为你的调试助手 🚀
