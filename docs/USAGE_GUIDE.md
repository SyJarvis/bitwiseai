# BitwiseAI 使用指南

本指南将帮助您快速上手 BitwiseAI，并展示如何将其嵌入到您的项目中。

## 目录

1. [快速开始](#快速开始)
2. [基本概念](#基本概念)
3. [集成到项目](#集成到项目)
4. [常见场景](#常见场景)
5. [FAQ](#faq)

## 快速开始

### 安装

```bash
git clone https://github.com/SyJarvis/BitwiseAI.git
cd BitwiseAI
pip install -r requirements.txt
```

### 配置

1. 复制配置文件：
```bash
cp bitwiseai/config.json.example ~/.bitwiseai/config.json
```

2. 创建 `.env` 文件：
```bash
# .env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-endpoint/v1
EMBEDDING_API_KEY=your-api-key
EMBEDDING_BASE_URL=https://your-endpoint/v1
```

### 第一个示例

```python
from bitwiseai import BitwiseAI

# 初始化
ai = BitwiseAI()

# 使用 LLM
response = ai.chat("你好，请介绍一下你自己")
print(response)
```

## 基本概念

### 1. BitwiseAI 核心

`BitwiseAI` 是主要的类，提供：
- LLM 对话
- RAG 规范查询
- 工具管理
- 任务执行

### 2. 三大接口

- **LogParserInterface**: 定义如何解析日志
- **VerifierInterface**: 定义如何验证数据
- **TaskInterface**: 定义完整的分析任务

### 3. 工具系统

注册自定义工具扩展功能：
- Python 函数
- Shell 命令
- LangChain Tools

### 4. 分析结果

所有任务返回 `AnalysisResult` 列表：
```python
AnalysisResult(
    status="pass",  # pass, fail, error, warning
    message="描述",
    data={"key": "value"}  # 可选的附加数据
)
```

## 集成到项目

### 场景1: 纯粹使用 LLM 和 RAG

如果您只需要 LLM 对话和规范查询：

```python
from bitwiseai import BitwiseAI

# 初始化
ai = BitwiseAI()

# 加载规范文档
ai.load_specification("./hardware_specs/")

# 查询规范
context = ai.query_specification("MUL 指令的参数")
print(context)

# 使用 RAG 对话
answer = ai.chat("如何使用 SHIFT 指令？", use_rag=True)
print(answer)
```

### 场景2: 自定义日志分析

如果您需要分析特定格式的日志：

#### 步骤1: 创建解析器

```python
# my_project/parsers.py
from bitwiseai.interfaces import LogParserInterface

class MyLogParser(LogParserInterface):
    def parse_file(self, file_path: str):
        with open(file_path, 'r') as f:
            content = f.read()
        return self.parse_text(content)
    
    def parse_text(self, text: str):
        # 实现您的解析逻辑
        lines = text.split('\n')
        events = []
        for line in lines:
            if "EVENT" in line:
                events.append(self._parse_event(line))
        return events
    
    def _parse_event(self, line):
        # 解析单个事件
        return {"type": "event", "line": line}
```

#### 步骤2: 创建验证器（可选）

```python
# my_project/verifiers.py
from bitwiseai.interfaces import VerifierInterface, AnalysisResult

class MyVerifier(VerifierInterface):
    def verify(self, data):
        results = []
        for event in data:
            # 验证每个事件
            if self._is_valid(event):
                results.append(AnalysisResult(
                    status="pass",
                    message=f"事件 {event['type']} 验证通过"
                ))
            else:
                results.append(AnalysisResult(
                    status="fail",
                    message=f"事件 {event['type']} 验证失败"
                ))
        return results
    
    def _is_valid(self, event):
        # 验证逻辑
        return True
```

#### 步骤3: 创建任务

```python
# my_project/tasks.py
from bitwiseai.interfaces import AnalysisTask
from .parsers import MyLogParser
from .verifiers import MyVerifier

class MyAnalysisTask(AnalysisTask):
    def __init__(self):
        super().__init__(
            name="MyLogAnalysis",
            description="分析我的日志文件",
            parser=MyLogParser(),
            verifier=MyVerifier()
        )
    
    def analyze(self, context, parsed_data):
        """额外的分析逻辑"""
        results = []
        
        # 使用 LLM 进行深度分析
        if parsed_data:
            summary = f"发现 {len(parsed_data)} 个事件"
            
            # 询问 LLM
            llm_analysis = context.analyze_with_llm(
                f"分析以下事件数据：{parsed_data[:5]}"
            )
            
            results.append(AnalysisResult(
                status="info",
                message="LLM 分析",
                data={"llm_response": llm_analysis}
            ))
        
        return results
```

#### 步骤4: 使用

```python
# my_project/main.py
from bitwiseai import BitwiseAI
from my_project.tasks import MyAnalysisTask

def main():
    # 初始化
    ai = BitwiseAI()
    
    # 加载日志
    ai.load_log_file("test.log")
    
    # 注册任务
    task = MyAnalysisTask()
    ai.register_task(task)
    
    # 执行
    results = ai.execute_task(task)
    
    # 查看结果
    for result in results:
        print(f"[{result.status}] {result.message}")
    
    # 生成报告
    report = ai.generate_report(format="markdown")
    ai.save_report("analysis_report.md", format="markdown")

if __name__ == "__main__":
    main()
```

### 场景3: 添加自定义工具

如果您需要调用外部工具或脚本：

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 注册 Python 函数
def calculate_crc(data: bytes) -> int:
    """计算 CRC 校验码"""
    # 实现 CRC 计算
    return crc_value

ai.register_tool(calculate_crc, description="CRC 校验码计算")

# 注册 Shell 命令
ai.register_tool({
    "type": "shell_command",
    "name": "run_verifier",
    "command": "./verify.sh {input_file}",
    "description": "运行外部验证脚本"
})

# 在任务中使用
class MyTask(AnalysisTask):
    def analyze(self, context, parsed_data):
        # 调用工具
        crc = context.invoke_tool("calculate_crc", data=b"...")
        verify_result = context.invoke_tool("run_verifier", input_file="data.bin")
        # ...
```

## 常见场景

### 场景: 硬件指令验证

```python
from bitwiseai import BitwiseAI
from bitwiseai.log_parser import LogParser
from bitwiseai.verifier import InstructionVerifier
from bitwiseai.interfaces import AnalysisTask

class InstructionVerificationTask(AnalysisTask):
    def __init__(self):
        super().__init__(
            parser=LogParser(),
            verifier=InstructionVerifier()
        )

ai = BitwiseAI()
ai.load_log_file("pe_instructions.log")
ai.register_task(InstructionVerificationTask())
ai.execute_all_tasks()

# 生成报告
ai.save_report("verification_report.md")
```

### 场景: 性能日志分析

```python
class PerformanceAnalysisTask(AnalysisTask):
    def analyze(self, context, parsed_data):
        results = []
        
        # 读取日志
        with open(context.log_file_path, 'r') as f:
            log = f.read()
        
        # 提取性能指标
        latencies = extract_latencies(log)
        
        # 统计分析
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        # 判断是否异常
        if max_latency > THRESHOLD:
            results.append(AnalysisResult(
                status="warning",
                message=f"检测到性能异常: 最大延迟 {max_latency}ms",
                data={"latencies": latencies}
            ))
        
        return results

# 使用
ai = BitwiseAI()
ai.load_log_file("performance.log")
ai.register_task(PerformanceAnalysisTask())
results = ai.execute_all_tasks()
```

### 场景: 协议一致性检查

```python
class ProtocolCheckTask(AnalysisTask):
    def __init__(self):
        super().__init__(
            parser=ProtocolLogParser(),
            verifier=ProtocolVerifier()
        )
    
    def analyze(self, context, parsed_data):
        results = []
        
        # 加载协议规范（使用 RAG）
        protocol_spec = context.query_specification(
            "通信协议规范",
            top_k=3
        )
        
        # 使用 LLM 辅助分析
        analysis_prompt = f"""
基于以下协议规范：
{protocol_spec}

检查以下日志是否符合规范：
{parsed_data[:100]}

请指出任何不一致之处。
"""
        llm_analysis = context.analyze_with_llm(analysis_prompt)
        
        results.append(AnalysisResult(
            status="info",
            message="协议一致性分析",
            data={"llm_analysis": llm_analysis}
        ))
        
        return results
```

## 高级技巧

### 1. 任务依赖

如果多个任务有依赖关系：

```python
class Task1(AnalysisTask):
    def analyze(self, context, parsed_data):
        # 第一个任务
        context.shared_data = {"result": "data"}
        return []

class Task2(AnalysisTask):
    def analyze(self, context, parsed_data):
        # 使用第一个任务的结果
        previous_result = context.shared_data.get("result")
        # ...

# 按顺序执行
ai.register_task(Task1())
ai.register_task(Task2())
ai.execute_all_tasks()
```

### 2. 增量分析

对于大型日志文件：

```python
class IncrementalTask(AnalysisTask):
    def analyze(self, context, parsed_data):
        results = []
        
        # 按块读取文件
        with open(context.log_file_path, 'r') as f:
            chunk_size = 1000
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                # 分析每个块
                chunk_results = self._analyze_chunk(chunk)
                results.extend(chunk_results)
        
        return results
```

### 3. 多文件分析

```python
log_files = ["log1.txt", "log2.txt", "log3.txt"]
task = MyAnalysisTask()

for log_file in log_files:
    ai.load_log_file(log_file)
    results = ai.execute_task(task)
    print(f"{log_file}: {len(results)} results")
```

## FAQ

### Q1: BitwiseAI 需要联网吗？

A: 是的，BitwiseAI 需要调用 LLM API（如 OpenAI、MiniMax 等）。但向量数据库（Milvus）是本地运行的。

### Q2: 可以使用本地 LLM 吗？

A: 可以！只要 LLM 提供兼容 OpenAI 的 API 接口，您可以将 `LLM_BASE_URL` 指向本地服务。

### Q3: 如何提高分析速度？

A: 建议：
1. 批量处理多个文件
2. 使用缓存避免重复计算
3. 减少 LLM 调用次数（只在需要时调用）
4. 优化解析器和验证器的性能

### Q4: 可以不使用 RAG 吗？

A: 可以！RAG 是可选的。如果您不需要规范查询功能，可以只使用纯 LLM 模式：

```python
response = ai.chat("问题", use_rag=False)
```

### Q5: 如何调试任务？

A: 建议：
1. 在 `analyze()` 方法中添加 `print()` 输出
2. 使用 Python 调试器（如 `pdb`）
3. 查看 `AnalysisResult` 的详细信息
4. 检查日志文件是否正确加载

### Q6: 支持哪些日志格式？

A: BitwiseAI 不限制日志格式！您通过实现 `LogParserInterface` 来支持任何格式。

内置提供了 PE 寄存器日志的解析器作为参考。

### Q7: 如何处理错误？

A: 在任务中捕获异常并返回 `AnalysisResult`：

```python
def analyze(self, context, parsed_data):
    try:
        # 分析逻辑
        pass
    except Exception as e:
        return [AnalysisResult(
            status="error",
            message=f"分析失败: {str(e)}"
        )]
```

## 最佳实践

1. **模块化设计**: 将解析器、验证器、任务分离到不同文件
2. **复用内置组件**: 使用 `LogParser`, `InstructionVerifier` 等参考实现
3. **利用 LLM**: 对于复杂的模式识别，让 AI 辅助
4. **结合 RAG**: 加载规范文档，在分析时引用
5. **工具化**: 将常用操作注册为工具，提高复用性
6. **文档化**: 为自定义组件编写清晰的文档
7. **测试**: 为关键逻辑编写单元测试

## 获取帮助

- GitHub Issues: https://github.com/SyJarvis/BitwiseAI/issues
- 文档: `docs/` 目录
- 示例: `examples/` 目录

---

开始使用 BitwiseAI，让 AI 成为您的调试助手！🚀

