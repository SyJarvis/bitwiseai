# BitwiseAI 架构文档

## 设计原则

BitwiseAI 的设计遵循以下原则：

1. **可嵌入性**: 作为库而非工具，让用户在自己的项目中使用
2. **接口优先**: 提供清晰的接口，用户实现自己的逻辑
3. **灵活性**: 支持多种扩展方式（工具、任务、解析器）
4. **AI 增强**: 利用 LLM 和 RAG 提供智能分析能力

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│   │ 自定义解析器  │  │ 自定义验证器  │  │  自定义工具   │      │
│   │ (Parser)     │  │ (Verifier)   │  │  (Tools)     │      │
│   └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                                │
│   ┌──────────────────────────────────────────────────┐       │
│   │            自定义分析任务 (Tasks)                  │       │
│   │  - 定义工作流                                      │       │
│   │  - 组合解析器、验证器、工具                         │       │
│   │  - 调用 BitwiseAI 核心能力                         │       │
│   └──────────────────────────────────────────────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │ 接口调用
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    BitwiseAI 核心层                           │
│                                                                │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│   │   任务管理    │  │   工具管理    │  │   报告生成    │      │
│   │ TaskManager  │  │ToolRegistry  │  │   Reporter   │      │
│   └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                                │
│   ┌──────────────────────────────────────────────────┐       │
│   │              BitwiseAI 核心类                      │       │
│   │  - 协调各组件                                      │       │
│   │  - 提供统一 API                                    │       │
│   │  - 管理执行上下文                                   │       │
│   └──────────────────────────────────────────────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │ 调用
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      AI 能力层                                │
│                                                                │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│   │  LLM 引擎    │  │  RAG 引擎    │  │ 向量数据库    │      │
│   │ (LangChain)  │  │              │  │  (Milvus)    │      │
│   └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                                │
│   ┌──────────────┐  ┌──────────────┐                         │
│   │ Embedding    │  │ 文档加载器    │                         │
│   │   模型       │  │              │                         │
│   └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. BitwiseAI 核心类

**职责**:
- 初始化和管理所有子系统
- 提供统一的 API 接口
- 维护执行上下文

**关键属性**:
- `tool_registry`: 工具注册器
- `tasks`: 任务列表
- `llm`: LLM 引擎
- `vector_db`: 向量数据库
- `reporter`: 报告生成器

**关键方法**:
- 工具管理: `register_tool()`, `invoke_tool()`
- 任务管理: `register_task()`, `execute_task()`
- 日志分析: `load_log_file()`, `analyze_with_llm()`
- 规范查询: `load_specification()`, `query_specification()`

### 2. 接口层

#### LogParserInterface

用于解析日志文件，将非结构化文本转换为结构化数据。

```python
class LogParserInterface(ABC):
    @abstractmethod
    def parse_file(self, file_path: str) -> Any:
        """解析日志文件，返回结构化数据"""
        pass
    
    @abstractmethod
    def parse_text(self, text: str) -> Any:
        """解析日志文本"""
        pass
```

**使用场景**:
- PE 寄存器日志解析
- 编译器输出解析
- 测试日志解析

#### VerifierInterface

用于验证数据的正确性。

```python
class VerifierInterface(ABC):
    @abstractmethod
    def verify(self, data: Any) -> List[AnalysisResult]:
        """验证数据，返回验证结果列表"""
        pass
```

**使用场景**:
- 指令计算验证
- 协议一致性检查
- 性能指标验证

#### TaskInterface

定义完整的分析任务流程。

```python
class TaskInterface(ABC):
    @abstractmethod
    def execute(self, context: BitwiseAI) -> List[AnalysisResult]:
        """执行任务，返回分析结果"""
        pass
```

**使用场景**:
- 组合多个步骤的复杂分析
- 需要 LLM 辅助的分析任务
- 批量处理任务

### 3. 工具系统

**设计目标**:
- 让用户可以扩展 BitwiseAI 的功能
- 支持多种工具类型
- 与 LangChain Agents 集成

**支持的工具类型**:

1. **Python 函数**: 最简单的扩展方式
   ```python
   def my_tool(x, y):
       return x + y
   
   ai.register_tool(my_tool)
   ```

2. **Shell 命令**: 执行外部工具
   ```python
   ai.register_tool({
       "type": "shell_command",
       "name": "run_sim",
       "command": "./simulator {input}"
   })
   ```

3. **LangChain Tools**: 支持 Function Calling
   ```python
   from langchain.tools import Tool
   
   tool = Tool(name="search", func=search_func, description="搜索")
   ai.register_tool(tool)
   ```

### 4. 任务系统

**任务生命周期**:

```
注册 → 等待执行 → 执行前钩子 → 解析 → 验证 → 自定义分析 → 执行后钩子 → 完成
```

**AnalysisTask 基类**:

提供通用的任务模板，用户只需重写 `analyze()` 方法：

```python
class MyTask(AnalysisTask):
    def analyze(self, context, parsed_data):
        # 自定义分析逻辑
        results = []
        # ...
        return results
```

### 5. AI 能力层

#### LLM 引擎

- 基于 LangChain 的 `ChatOpenAI`
- 支持多种模型（MiniMax、OpenAI 等）
- 提供对话和辅助分析功能

#### RAG 引擎

- 向量数据库: Milvus
- Embedding 模型: Qwen/Qwen3-Embedding-8B
- 支持规范文档检索和问答

**RAG 流程**:

```
用户查询 → Embedding → 向量检索 → 相关文档 → 构建提示词 → LLM 生成回答
```

## 数据流

### 典型的分析任务数据流

```
1. 用户加载日志文件
   ↓
2. 创建并注册任务
   ↓
3. 执行任务
   ↓
4. [任务内部]
   - 调用解析器解析日志
   - 调用验证器验证数据
   - 调用工具进行计算
   - 调用 LLM 进行分析
   - 调用 RAG 查询规范
   ↓
5. 收集分析结果
   ↓
6. 生成报告
   ↓
7. 输出给用户
```

## 扩展点

BitwiseAI 提供以下扩展点：

1. **解析器**: 实现 `LogParserInterface`
2. **验证器**: 实现 `VerifierInterface`
3. **任务**: 继承 `AnalysisTask` 或实现 `TaskInterface`
4. **工具**: 注册 Python 函数、Shell 命令或 LangChain Tools
5. **配置**: 通过 `config.json` 自定义模型、提示词等

## 最佳实践

### 1. 模块化设计

将解析、验证、分析分离到不同的模块：

```
my_project/
├── parsers/
│   └── my_log_parser.py
├── verifiers/
│   └── my_verifier.py
├── tasks/
│   └── my_task.py
└── main.py
```

### 2. 复用内置组件

BitwiseAI 提供了一些参考实现（如 `LogParser`, `InstructionVerifier`），可以直接使用或继承扩展。

### 3. 利用 LLM

对于复杂的模式识别和分析，使用 `context.analyze_with_llm()` 让 AI 辅助：

```python
def analyze(self, context, parsed_data):
    # 使用 LLM 分析异常模式
    prompt = f"分析以下数据，找出异常: {parsed_data}"
    analysis = context.analyze_with_llm(prompt)
    return [AnalysisResult(status="info", message=analysis)]
```

### 4. 结合 RAG

将规范文档加载到向量库，在分析时引用：

```python
# 初始化时加载规范
ai.load_specification("./specs/")

# 任务中查询规范
def analyze(self, context, parsed_data):
    # 查询相关规范
    spec = context.query_specification("MUL 指令规范")
    # ... 基于规范进行验证 ...
```

## 性能优化

### 1. 批量处理

对于大量日志，使用批量接口：

```python
# 一次性解析所有文件
files = ["log1.txt", "log2.txt", "log3.txt"]
for f in files:
    ai.load_log_file(f)
    ai.execute_all_tasks()
```

### 2. 缓存结果

对于重复的计算，使用 Python 的 `@lru_cache` 缓存：

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_calculation(data):
    # 耗时计算
    return result
```

### 3. 异步任务

对于独立的任务，可以使用 Python 的 `asyncio` 并行执行。

## 安全考虑

### 1. Shell 命令注入

使用 Shell 命令工具时，注意参数验证：

```python
# 危险：直接拼接用户输入
command = f"rm {user_input}"  # ❌

# 安全：使用参数化
command = ["rm", user_input]  # ✅
```

### 2. LLM 提示词注入

构建 LLM 提示词时，对用户输入进行清理。

### 3. API 密钥保护

API 密钥应存储在 `.env` 文件中，不要硬编码在代码里。

## 总结

BitwiseAI 的架构设计强调：

- ✅ **灵活性**: 通过接口和插件机制扩展
- ✅ **可组合性**: 组件可以独立使用或组合使用
- ✅ **AI 增强**: LLM 和 RAG 提供智能分析能力
- ✅ **易用性**: 清晰的 API 和丰富的示例

通过这种设计，BitwiseAI 既可以作为完整的分析框架使用，也可以只使用其中的部分组件。

