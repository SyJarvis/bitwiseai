# 工具系统文档

BitwiseAI 提供了灵活的工具系统，让用户可以扩展功能并集成外部工具。

## 工具类型

BitwiseAI 支持三种类型的工具：

### 1. Python 函数工具

最简单直接的扩展方式，将任何 Python 函数注册为工具。

**示例**:

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 定义工具函数
def hex_to_int(hex_str: str) -> int:
    """将十六进制字符串转换为整数"""
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return int(hex_str, 16)

# 注册工具
ai.register_tool(hex_to_int, description="十六进制转整数")

# 使用工具
result = ai.invoke_tool("hex_to_int", "0xFF")
print(result)  # 255
```

**特点**:
- ✅ 简单易用
- ✅ 自动提取函数签名
- ✅ 支持任意 Python 代码

### 2. Shell 命令工具

执行外部命令或脚本。

**示例**:

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()

# 注册 Shell 命令
ai.register_tool({
    "type": "shell_command",
    "name": "count_errors",
    "command": "grep -c ERROR {log_file}",
    "description": "统计日志中的错误数"
})

# 使用工具
result = ai.invoke_tool("count_errors", log_file="test.log")
print(f"错误数: {result}")
```

**占位符**:

在命令中使用 `{param}` 作为参数占位符：

```python
ai.register_tool({
    "type": "shell_command",
    "name": "run_test",
    "command": "python {script} --input {input_file} --output {output_file}",
    "description": "运行测试脚本"
})

# 使用时传入参数
result = ai.invoke_tool(
    "run_test",
    script="verify.py",
    input_file="data.txt",
    output_file="result.txt"
)
```

**安全提示**:
- ⚠️ 注意命令注入风险
- ⚠️ 验证用户输入
- ⚠️ 避免执行不可信的命令

### 3. LangChain Tools

支持 LangChain 生态的 Tools，可以与 Agents 集成。

**示例**:

```python
from bitwiseai import BitwiseAI
from langchain.tools import Tool

ai = BitwiseAI()

# 创建 LangChain Tool
def search_func(query: str) -> str:
    # 实现搜索逻辑
    return f"搜索结果: {query}"

langchain_tool = Tool(
    name="search",
    func=search_func,
    description="搜索规范文档"
)

# 注册到 BitwiseAI
ai.register_tool(langchain_tool)

# 使用工具
result = ai.invoke_tool("search", "MUL 指令")
```

## 配置化工具

工具可以在配置文件中定义，BitwiseAI 启动时自动加载。

### 配置格式

在 `~/.bitwiseai/config.json` 中添加：

```json
{
  "tools": [
    {
      "type": "python_function",
      "name": "saturate_add",
      "module": "my_tools.hardware",
      "function": "saturate_add_int8",
      "description": "计算饱和加法"
    },
    {
      "type": "shell_command",
      "name": "run_sim",
      "command": "./simulator --input {input} --output {output}",
      "description": "运行模拟器"
    }
  ]
}
```

### Python 模块工具

对于 `python_function` 类型，需要：

1. 创建 Python 模块（如 `my_tools/hardware.py`）
2. 实现工具函数
3. 确保模块在 Python 路径中

**示例模块** (`my_tools/hardware.py`):

```python
def saturate_add_int8(a: int, b: int) -> int:
    """
    int8 饱和加法
    
    Args:
        a: 第一个操作数
        b: 第二个操作数
        
    Returns:
        饱和后的结果
    """
    result = a + b
    if result > 127:
        return 127
    elif result < -128:
        return -128
    return result
```

然后在配置文件中引用：

```json
{
  "type": "python_function",
  "name": "saturate_add",
  "module": "my_tools.hardware",
  "function": "saturate_add_int8",
  "description": "int8 饱和加法"
}
```

## 工具管理

### 列出所有工具

```python
tools = ai.list_tools()
print("已注册的工具:", tools)
```

### 查看工具详情

```python
summary = ai.tool_registry.get_tools_summary()
print(summary)
```

输出示例：

```
已注册 5 个工具:

  [python_function] hex_to_int
    将十六进制字符串转换为整数
  
  [shell_command] count_errors
    统计日志中的错误数
  
  [python_function] saturate_add
    int8 饱和加法
```

### 获取单个工具

```python
tool = ai.tool_registry.get_tool("hex_to_int")
if tool:
    print(f"工具: {tool.name}")
    print(f"类型: {tool.tool_type.value}")
    print(f"描述: {tool.description}")
```

## 内置工具

BitwiseAI 提供了一些常用的内置工具：

### hex_to_decimal

```python
result = ai.invoke_tool("hex_to_decimal", "0xFF")
# 结果: 255
```

### decimal_to_hex

```python
result = ai.invoke_tool("decimal_to_hex", 255)
# 结果: "0xff"
```

### binary_to_decimal

```python
result = ai.invoke_tool("binary_to_decimal", "0b1010")
# 结果: 10
```

## 在任务中使用工具

工具可以在分析任务中调用：

```python
from bitwiseai.interfaces import AnalysisTask, AnalysisResult

class MyTask(AnalysisTask):
    def analyze(self, context, parsed_data):
        results = []
        
        # 调用工具
        hex_value = "0x8D17"
        decimal_value = context.invoke_tool("hex_to_decimal", hex_value)
        
        results.append(AnalysisResult(
            status="pass",
            message=f"{hex_value} = {decimal_value}",
            data={"hex": hex_value, "decimal": decimal_value}
        ))
        
        return results
```

## 与 LangChain Agents 集成

BitwiseAI 的工具可以转换为 LangChain Tools，供 Agent 使用：

```python
from bitwiseai import BitwiseAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# 初始化 BitwiseAI 并注册工具
ai = BitwiseAI()
ai.register_tool(hex_to_int)
ai.register_tool(verify_calculation)

# 转换为 LangChain Tools
langchain_tools = ai.tool_registry.to_langchain_tools()

# 创建 Agent
llm = ChatOpenAI(model="gpt-4")
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个硬件调试助手"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

agent = create_openai_functions_agent(llm, langchain_tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=langchain_tools)

# 使用 Agent
result = agent_executor.invoke({
    "input": "将十六进制 0xFF 转换为十进制"
})
print(result)
```

## 高级用法

### 1. 工具链

组合多个工具形成工具链：

```python
class ToolChainTask(AnalysisTask):
    def analyze(self, context, parsed_data):
        # 步骤1: 解析十六进制
        hex_val = "0x8D17"
        decimal_val = context.invoke_tool("hex_to_decimal", hex_val)
        
        # 步骤2: 执行计算
        result = context.invoke_tool("saturate_add", decimal_val, 100)
        
        # 步骤3: 转回十六进制
        hex_result = context.invoke_tool("decimal_to_hex", result)
        
        return [AnalysisResult(
            status="pass",
            message=f"计算结果: {hex_result}"
        )]
```

### 2. 条件工具调用

根据条件选择不同的工具：

```python
def analyze(self, context, parsed_data):
    # 根据数据类型选择工具
    if data_type == "hex":
        value = context.invoke_tool("hex_to_decimal", data)
    elif data_type == "binary":
        value = context.invoke_tool("binary_to_decimal", data)
    else:
        value = int(data)
    
    # 继续处理...
```

### 3. 动态工具注册

在任务执行过程中动态注册工具：

```python
class DynamicToolTask(AnalysisTask):
    def before_execute(self, context):
        # 动态创建工具
        def custom_parser(data):
            # 基于配置的解析逻辑
            return parse_logic(data)
        
        # 注册工具
        context.register_tool(custom_parser, name="dynamic_parser")
    
    def analyze(self, context, parsed_data):
        # 使用动态注册的工具
        result = context.invoke_tool("dynamic_parser", parsed_data)
        return [AnalysisResult(status="pass", message=str(result))]
```

## 最佳实践

### 1. 工具命名

使用清晰、描述性的名称：

```python
# ✅ 好的命名
"parse_register_value"
"verify_add_instruction"
"calculate_saturate"

# ❌ 不好的命名
"tool1"
"func"
"helper"
```

### 2. 提供描述

为工具添加详细的描述：

```python
ai.register_tool(
    my_func,
    description="解析寄存器十六进制值，支持多种格式：0xFF, FF, 0XFF"
)
```

### 3. 错误处理

在工具函数中处理错误：

```python
def safe_hex_to_int(hex_str: str) -> int:
    """安全的十六进制转换"""
    try:
        if hex_str.startswith("0x"):
            hex_str = hex_str[2:]
        return int(hex_str, 16)
    except ValueError:
        raise ValueError(f"无效的十六进制字符串: {hex_str}")
```

### 4. 文档化

为工具函数编写文档字符串：

```python
def verify_mul_instruction(rs0, rs1, rd0, func_sel):
    """
    验证 MUL 指令计算
    
    Args:
        rs0: 第一个源寄存器值
        rs1: 第二个源寄存器值
        rd0: 目标寄存器值
        func_sel: 功能选择器
        
    Returns:
        验证结果字典，包含 is_correct, expected, actual 等字段
        
    Raises:
        ValueError: 如果参数无效
    """
    # 实现...
```

## 故障排除

### 工具未找到

```python
# 错误: ValueError: 工具不存在: my_tool

# 解决: 检查工具是否已注册
print(ai.list_tools())
```

### 配置化工具加载失败

```python
# 检查模块是否在 Python 路径中
import sys
print(sys.path)

# 添加模块路径
sys.path.insert(0, "/path/to/your/module")
```

### Shell 命令执行超时

```python
# 默认超时时间是 30 秒
# 对于长时间运行的命令，考虑使用后台任务或异步执行
```

## 总结

BitwiseAI 的工具系统提供了：

- ✅ 三种工具类型（Python、Shell、LangChain）
- ✅ 配置化工具定义
- ✅ 动态工具注册
- ✅ 与 LangChain Agents 集成
- ✅ 内置常用工具

通过工具系统，用户可以灵活地扩展 BitwiseAI 的功能，集成外部工具和自定义逻辑。

