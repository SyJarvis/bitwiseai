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

### 方式1: 命令行工具（推荐）

```bash
# 1. 生成配置文件（交互式配置）
python -m bitwiseai --generate-config

# 2. 单次对话
python -m bitwiseai --chat "今天天气怎么样"

# 3. 交互式对话
python -m bitwiseai --interactive

# 4. 查看帮助
python -m bitwiseai --help

# 或者使用快捷脚本
bash bitwiseai_cli.sh --help
```

**首次使用必须配置**：

运行 `python -m bitwiseai --generate-config` 会交互式地收集以下信息并生成配置文件：
- LLM API Key 和 Base URL
- Embedding API Key 和 Base URL  
- 模型名称和参数
- 系统提示词

配置文件保存在 `~/.bitwiseai/config.json`

### 方式2: 使用 .env 文件

创建 `.env` 文件并配置 API 密钥：

```bash
# LLM 配置
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-api-endpoint/v1

# Embedding 配置
EMBEDDING_API_KEY=your-api-key
EMBEDDING_BASE_URL=https://your-api-endpoint/v1
```

### 2. 基本使用

```python
from bitwiseai import BitwiseAI

# 初始化
ai = BitwiseAI()

# 加载规范文档到知识库（可选）
ai.load_specification("./docs/hardware_spec.pdf")

# 使用 LLM 对话
response = ai.chat("什么是 MUL 指令？")
print(response)
```

### 3. 自定义分析任务

```python
from bitwiseai import BitwiseAI
from bitwiseai.interfaces import AnalysisTask, AnalysisResult

class MyLogAnalysisTask(AnalysisTask):
    """自定义日志分析任务"""
    
    def analyze(self, context: BitwiseAI, parsed_data):
        """实现你的分析逻辑"""
        results = []
        
        # 读取日志
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
```

### 4. 注册自定义工具

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 注册 Python 函数
def parse_hex(hex_str):
    return int(hex_str, 16)

ai.register_tool(parse_hex, description="解析十六进制")

# 使用工具
result = ai.invoke_tool("parse_hex", "0xFF")
print(f"结果: {result}")  # 255
```

## 📚 使用示例

### 示例 1: PE 寄存器指令验证

```python
# examples/pe_instruction_verification.py
from bitwiseai import BitwiseAI
from bitwiseai.log_parser import LogParser
from bitwiseai.verifier import InstructionVerifier
from bitwiseai.interfaces import AnalysisTask

class PEInstructionTask(AnalysisTask):
    def __init__(self):
        super().__init__(
            parser=LogParser(),        # 使用内置解析器
            verifier=InstructionVerifier()  # 使用内置验证器
        )
    
    def analyze(self, context, parsed_data):
        # 解析和验证 PE 指令
        instructions = self.parser.instructions
        verify_results = self.verifier.verify_all(instructions)
        return [AnalysisResult(status=r.status.value, message=str(r)) 
                for r in verify_results]

# 运行
ai = BitwiseAI()
ai.load_log_file("pe_register.log")
ai.register_task(PEInstructionTask())
ai.execute_all_tasks()
```

### 示例 2: 自定义工具

查看 `examples/custom_tool_example.py` 了解如何：
- 注册 Python 函数作为工具
- 注册 Shell 命令作为工具
- 在任务中调用工具

### 示例 3: RAG 规范查询

```python
ai = BitwiseAI()

# 加载硬件规范文档
ai.load_specification("./docs/hardware_manual/")

# 查询规范
context = ai.query_specification("MUL 指令的 func_sel 参数含义")
print(context)

# 使用 RAG 对话
response = ai.chat("如何验证 SHIFT 指令？", use_rag=True)
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

### 工具管理

- `register_tool(tool, name, description)` - 注册工具
- `invoke_tool(name, *args, **kwargs)` - 调用工具
- `list_tools()` - 列出所有工具

### 任务管理

- `register_task(task)` - 注册任务
- `execute_task(task)` - 执行单个任务
- `execute_all_tasks()` - 执行所有任务
- `list_tasks()` - 列出所有任务

### 日志分析

- `load_log_file(file_path)` - 加载日志文件
- `load_specification(spec_path)` - 加载规范文档
- `query_specification(query, top_k)` - 查询规范文档
- `ask_about_log(question)` - 询问关于日志的问题

### 报告生成

- `generate_report(format)` - 生成报告
- `save_report(file_path, format)` - 保存报告

### LLM 对话

- `chat(query, use_rag)` - 对话
- `analyze_with_llm(prompt, use_rag)` - AI 辅助分析

## 📁 项目结构

```
bitwiseai/
├── __init__.py           # 包入口
├── bitwiseai.py          # 核心类
├── interfaces.py         # 接口定义
├── tools.py              # 工具系统
├── reporter.py           # 报告生成器
├── llm.py                # LLM 封装
├── embedding.py          # Embedding 封装
├── vector_database.py    # 向量数据库
├── utils.py              # 工具函数
├── log_parser.py         # 示例：日志解析器
└── verifier.py           # 示例：指令验证器

examples/
├── custom_task_example.py           # 自定义任务示例
├── custom_tool_example.py           # 自定义工具示例
└── pe_instruction_verification.py   # PE 指令验证示例
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
