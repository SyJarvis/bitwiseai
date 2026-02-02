# BitwiseAI CLI 快速参考卡

## 🚀 快速开始

```bash
# 1. 配置 API
export LLM_API_KEY="sk-xxx"
export LLM_BASE_URL="https://api.openai.com/v1"

# 2. 测试对话
bitwiseai chat "你好"

# 3. 查看帮助
bitwiseai --help
```

## 📱 主要命令

### 对话模式
```bash
bitwiseai chat [query]           # 单次对话或交互模式
bitwiseai chat "你好"            # 直接提问
bitwiseai chat                   # 进入交互模式
```

### Agent 模式
```bash
bitwiseai agent <task>           # Agent 自动执行任务
bitwiseai agent --stream <task>  # 流式输出
```

### Skill 管理
```bash
bitwiseai skill --list           # 列出所有 Skills
bitwiseai skill --load <name>    # 加载 Skill
bitwiseai skill --unload <name>  # 卸载 Skill
bitwiseai skill --search <kw>    # 搜索 Skills
```

### 会话管理
```bash
bitwiseai session --list         # 列出会话
bitwiseai session --new <name>   # 创建会话
bitwiseai session --switch <id>  # 切换会话
```

### 配置
```bash
bitwiseai config                 # 生成配置
bitwiseai config --force         # 强制覆盖
```

## 💬 交互模式 Slash 命令

```bash
你: /help           # 帮助
你: /skills         # 列出 Skills
你: /load <skill>   # 加载 Skill
你: /unload <skill> # 卸载 Skill
你: /agent          # Agent 模式
你: /sessions       # 列出会话
你: /new <name>     # 新建会话
你: /switch <id>    # 切换会话
你: /clear          # 清空上下文
你: /quit           # 退出
```

## 🛠️ Skills 使用流程

```bash
# 1. 查看可用 Skills
bitwiseai skill --list

# 2. 加载需要的 Skill
bitwiseai skill --load hex_converter

# 3. 使用工具对话
bitwiseai chat "将 0xFF 转换为十进制"

# 或在交互模式中
bitwiseai chat
你: /load hex_converter
你: 转换 0xFF
```

## 📝 常用工作流

### 代码审查
```bash
bitwiseai session --new "代码审查"
bitwiseai skill --load asm_parser
bitwiseai chat
you: 分析这段代码: [代码]
```

### 学习指令
```bash
bitwiseai chat
you: /load asm_parser
you: MUL 指令怎么用？
you: 给我一个例子
```

### 调试问题
```bash
bitwiseai chat
you: 这段代码有bug: [代码]
you: /agent "找出问题并修复"
```

## 📂 文件位置

```
~/.bitwiseai/
├── config.json          # 配置文件
├── milvus_data.db       # 向量数据库
├── sessions/            # 会话数据
│   ├── *.jsonl
│   └── ...
└── skills/              # 自定义 Skills
```

## 🔧 环境变量

```bash
# LLM 配置
LLM_API_KEY              # API 密钥
LLM_BASE_URL            # API 端点
LLM_MODEL               # 模型名称

# Embedding 配置
EMBEDDING_API_KEY       # Embedding API 密钥
EMBEDDING_BASE_URL      # Embedding API 端点
EMBEDDING_MODEL         # Embedding 模型
```

## 📚 更多文档

- [完整 CLI 指南](CLI_USAGE_GUIDE.md)
- [示例代码](../examples/)
- [主 README](../README.md)

## ⚡ 快速演示

```bash
# 运行交互式演示
./bitwiseai-cli-demo.sh
```
