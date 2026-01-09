# BitwiseAI 命令行工具指南

BitwiseAI 提供了友好的命令行接口，让您可以快速开始使用 AI 辅助调试功能。

## 安装

```bash
cd BitwiseAI
pip install -e .
```

## 命令概览

```bash
# 查看帮助
python -m bitwiseai --help

# 生成配置文件
python -m bitwiseai --generate-config

# 单次对话
python -m bitwiseai --chat "你好"

# 交互式对话
python -m bitwiseai --interactive

# 查看版本
python -m bitwiseai --version
```

## 详细使用

### 1. 生成配置文件

首次使用时，需要生成配置文件：

```bash
python -m bitwiseai --generate-config
```

这会启动交互式配置向导：

```
==============================================================
BitwiseAI 配置生成器
==============================================================

LLM 配置:
----------------------------------------
LLM API Key: sk-xxx
LLM Base URL (如 https://api.openai.com/v1): https://api.minimax.chat/v1
LLM 模型名称 (默认: MiniMax-M2.1): MiniMax-M2.1
LLM Temperature (默认: 0.7): 0.7

Embedding 配置:
----------------------------------------
Embedding API Key: sk-xxx
Embedding Base URL: https://api.minimax.chat/v1
Embedding 模型名称 (默认: Qwen/Qwen3-Embedding-8B): 

系统配置:
----------------------------------------
系统提示词 (默认: 使用内置提示词): 

==============================================================
✓ 配置文件已生成: /root/.bitwiseai/config.json
==============================================================
```

配置文件格式（`~/.bitwiseai/config.json`）：

```json
{
  "llm": {
    "api_key": "your-llm-api-key",
    "base_url": "https://api.minimax.chat/v1",
    "model": "MiniMax-M2.1",
    "temperature": 0.7
  },
  "embedding": {
    "api_key": "your-embedding-api-key",
    "base_url": "https://api.minimax.chat/v1",
    "model": "Qwen/Qwen3-Embedding-8B"
  },
  "vector_db": {
    "db_file": "~/.bitwiseai/milvus_data.db",
    "collection_name": "bitwiseai_specs",
    "embedding_dim": 4096
  },
  "system_prompt": "你是 BitwiseAI...",
  "tools": []
}
```

### 2. 单次对话

配置完成后，可以进行单次对话：

```bash
python -m bitwiseai --chat "今天天气怎么样"
```

输出：

```
初始化 BitwiseAI...
==================================================
BitwiseAI 初始化完成
  LLM 模型: MiniMax-M2.1
  Embedding 模型: Qwen/Qwen3-Embedding-8B
  向量库: /root/.bitwiseai/milvus_data.db
  集合: bitwiseai_specs
  已注册工具: 3
==================================================

============================================================
用户: 今天天气怎么样
------------------------------------------------------------
BitwiseAI: 抱歉，我无法获取实时天气信息...
============================================================
```

### 3. 交互式对话

启动交互式对话模式：

```bash
python -m bitwiseai --interactive
```

```
初始化 BitwiseAI...
==================================================
BitwiseAI 初始化完成
  ...
==================================================

============================================================
BitwiseAI 交互式对话
输入 'exit' 或 'quit' 退出
============================================================

用户: 你好
BitwiseAI: 你好！我是 BitwiseAI...

用户: 什么是 MUL 指令
BitwiseAI: MUL 指令是一种乘法指令...

用户: exit
再见！
```

### 4. 配合 Shell 脚本

可以在 Shell 脚本中使用：

```bash
#!/bin/bash
# analyze_log.sh

# 分析日志并生成报告
python -m bitwiseai --chat "分析这个日志文件：$(cat error.log)"
```

### 5. 管道使用

配合 Unix 管道：

```bash
# 分析命令输出
echo "ERROR: connection timeout" | python -m bitwiseai --chat "分析这个错误"

# 分析文件内容
cat debug.log | head -n 50 | python -m bitwiseai --chat "总结这些日志"
```

## 配置管理

### 查看配置

```bash
cat ~/.bitwiseai/config.json
```

### 编辑配置

```bash
# 使用你喜欢的编辑器
vim ~/.bitwiseai/config.json
nano ~/.bitwiseai/config.json
```

### 重新生成配置

```bash
# 会提示是否覆盖现有配置
python -m bitwiseai --generate-config
```

### 配置优先级

BitwiseAI 支持两种配置方式，优先级如下：

1. **配置文件** (`~/.bitwiseai/config.json`) - 优先
2. **环境变量** (`.env` 文件或系统环境变量) - 备选

这意味着：
- 如果配置文件中有 `api_key`，则使用配置文件的
- 如果配置文件中没有，则查找环境变量 `LLM_API_KEY`

## 便捷脚本

项目提供了便捷脚本 `bitwiseai_cli.sh`：

```bash
# 使脚本可执行
chmod +x bitwiseai_cli.sh

# 使用
./bitwiseai_cli.sh --help
./bitwiseai_cli.sh --chat "你好"
```

### 添加到 PATH（可选）

将脚本添加到系统 PATH：

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
alias bitwiseai='python -m bitwiseai'

# 重新加载配置
source ~/.bashrc
```

之后可以直接使用：

```bash
bitwiseai --chat "你好"
```

## 故障排除

### 问题：配置文件不存在

```
错误: 配置文件不存在: /root/.bitwiseai/config.json
请先运行: bitwiseai --generate-config
```

**解决**：运行 `python -m bitwiseai --generate-config` 生成配置文件。

### 问题：API 密钥无效

```
错误: 请在配置文件或 .env 文件中设置 LLM API Key
```

**解决**：
1. 检查 `~/.bitwiseai/config.json` 中的 `api_key` 是否正确
2. 或者在 `.env` 文件中设置 `LLM_API_KEY`

### 问题：模块未找到

```
ModuleNotFoundError: No module named 'bitwiseai'
```

**解决**：确保已正确安装：

```bash
cd BitwiseAI
pip install -e .
```

### 问题：命令未找到

```
bitwiseai: command not found
```

**解决**：使用完整命令 `python -m bitwiseai` 或使用便捷脚本。

## 高级用法

### 1. 自定义配置路径

BitwiseAI 默认使用 `~/.bitwiseai/config.json`，如果需要使用其他配置：

```python
# 在 Python 代码中
from bitwiseai import BitwiseAI

ai = BitwiseAI(config_path="/path/to/custom/config.json")
```

### 2. 程序化使用

命令行工具本质上是对 BitwiseAI Python API 的封装，复杂场景建议使用 Python API：

```python
from bitwiseai import BitwiseAI

ai = BitwiseAI()
response = ai.chat("你好")
print(response)
```

### 3. 集成到 CI/CD

在持续集成中使用：

```yaml
# .github/workflows/analyze.yml
- name: Analyze logs
  run: |
    python -m bitwiseai --chat "分析构建日志" < build.log
```

## 最佳实践

1. **首次使用**: 使用 `--generate-config` 交互式生成配置
2. **安全性**: 不要将包含 API Key 的配置文件提交到版本控制
3. **多环境**: 可以为不同环境创建不同的配置文件
4. **备份**: 定期备份 `~/.bitwiseai/` 目录
5. **权限**: 确保配置文件只有当前用户可读（`chmod 600`）

## 总结

BitwiseAI 命令行工具提供了：

- ✅ 交互式配置生成
- ✅ 单次对话和交互式对话
- ✅ 配置文件管理
- ✅ 与 Shell 脚本集成
- ✅ 支持环境变量

通过命令行工具，您可以快速体验 BitwiseAI 的 AI 对话功能，为后续的高级用法（自定义任务、工具等）做准备。

