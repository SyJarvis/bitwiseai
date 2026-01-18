# BitwiseAI 示例代码

本目录包含 BitwiseAI 的各种使用示例，帮助您快速上手和了解系统功能。

## 示例列表

### 1. quick_start.py - 快速开始示例
**推荐首次使用**

展示 BitwiseAI 的核心功能：
- 初始化 BitwiseAI
- LLM 对话
- 注册和使用自定义工具
- 创建和执行自定义任务
- 生成分析报告

**运行方式：**
```bash
python examples/quick_start.py
```

### 2. document_management_example.py - 文档管理示例 ⭐ 新增
**文档加载、检索、导出完整流程**

展示如何使用 BitwiseAI 进行文档管理：
- 清理和初始化向量数据库
- 从文件夹加载文档（支持 .txt, .md, .pdf）
- 文档去重（基于嵌入向量相似度）
- 文档检索（混合检索：向量搜索 + 关键词搜索）
- RAG 模式聊天
- 文档导出为 Markdown 格式

**运行方式：**
```bash
python examples/document_management_example.py
```

**前置条件：**
- 确保 `./test_docs` 目录存在并包含文档文件
- 或修改脚本中的 `doc_folder` 变量指向您的文档目录

### 3. custom_task_example.py - 自定义任务示例
展示如何定义自己的日志分析任务：
- 继承 `AnalysisTask` 类
- 实现自定义分析逻辑
- 使用 LLM 进行辅助分析
- 返回分析结果

**运行方式：**
```bash
python examples/custom_task_example.py
```

### 4. custom_tool_example.py - 自定义工具示例
展示如何注册和使用自定义工具：
- 定义工具函数
- 注册工具到 BitwiseAI
- 在任务中调用工具
- LLM 自动调用工具

**运行方式：**
```bash
python examples/custom_tool_example.py
```

### 5. pe_instruction_verification.py - PE 指令验证完整示例
完整的 PE 指令验证案例：
- 使用内置的日志解析器
- 使用内置的指令验证器
- 执行完整的验证流程
- 生成验证报告

**运行方式：**
```bash
python examples/pe_instruction_verification.py
```

## 使用建议

1. **首次使用**：从 `quick_start.py` 开始，了解基本功能
2. **文档管理**：查看 `document_management_example.py`，学习如何管理知识库
3. **自定义开发**：参考 `custom_task_example.py` 和 `custom_tool_example.py` 进行扩展
4. **完整案例**：查看 `pe_instruction_verification.py` 了解实际应用场景

## 配置要求

所有示例都需要：
1. 配置文件：`~/.bitwiseai/config.json`
2. 环境变量：`.env` 文件（可选）
3. API 密钥：LLM 和 Embedding API 密钥

详细配置说明请参考：
- [使用指南](../docs/USAGE_GUIDE.md)
- [文档管理指南](../docs/DOCUMENT_MANAGEMENT_GUIDE.md)

## 注意事项

- 运行示例前请确保已正确配置 API 密钥
- 某些示例需要特定的数据文件（如日志文件、文档文件）
- 示例代码仅供参考，实际使用时请根据需求修改

## 相关文档

- [使用指南](../docs/USAGE_GUIDE.md)
- [文档管理指南](../docs/DOCUMENT_MANAGEMENT_GUIDE.md)
- [CLI 指南](../docs/CLI_GUIDE.md)
- [架构文档](../docs/ARCHITECTURE.md)
- [Skills 开发指南](../docs/SKILLS_GUIDE.md)

