# BitwiseAI 示例代码

本目录包含 BitwiseAI 的使用示例，帮助你快速上手。

## 示例列表

### 1. basic_usage.py - 基础使用示例

展示 BitwiseAI 的基本功能：
- 初始化 BitwiseAI
- 基础对话（不使用 RAG）
- 查看已加载的 Skills
- 使用工具调用
- 流式对话

**运行方式**:
```bash
python examples/basic_usage.py
```

### 2. rag_usage.py - RAG 使用示例

展示如何使用 RAG（检索增强生成）功能：
- 加载文档到向量数据库
- 检索相关文档
- 使用 RAG 模式进行对话
- 混合检索
- 查看文档统计信息

**运行方式**:
```bash
python examples/rag_usage.py
```

### 3. custom_skill_example.py - 自定义 Skill 示例

展示如何创建和使用自定义 Skill：
- 创建自定义 Skill 目录结构
- 定义 Skill 配置和工具
- 加载和使用自定义 Skill
- 在对话中使用自定义工具

**运行方式**:
```bash
python examples/custom_skill_example.py
```

### 4. document_export.py - 文档导出示例

展示如何导出向量数据库中的文档：
- 加载文档到向量数据库
- 导出文档为 Markdown 格式
- 查看导出结果
- 验证导出内容

**运行方式**:
```bash
python examples/document_export.py
```

## 运行前准备

在运行示例之前，请确保：

1. **已安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **已生成配置文件**:
   ```bash
   bitwiseai --generate-config
   ```
   或
   ```bash
   python -m bitwiseai --generate-config
   ```

3. **配置文件已正确设置**:
   确保 `~/.bitwiseai/config.json` 中包含正确的 API Key 和 Base URL。

## 注意事项

- 所有示例都会在运行时输出详细的执行信息
- 某些示例会创建临时文件，运行完成后可以选择清理
- 如果遇到错误，请检查配置文件是否正确设置
- 确保有足够的磁盘空间用于向量数据库存储

## 更多信息

更多使用说明请参考：
- [使用指南](../docs/USAGE_GUIDE.md)
- [CLI 指南](../docs/CLI_GUIDE.md)
- [Skills 指南](../docs/SKILLS_GUIDE.md)
- [文档管理指南](../docs/DOCUMENT_MANAGEMENT_GUIDE.md)
