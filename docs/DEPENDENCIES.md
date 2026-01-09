# BitwiseAI 依赖说明

## 核心依赖

### LangChain 生态

```bash
langchain>=0.1.0
langchain-openai>=0.0.5
```

**用途**：
- `langchain`: LangChain 核心框架
- `langchain-openai`: OpenAI 兼容的 LLM 和 Embedding 封装

**说明**：BitwiseAI 基于 LangChain 构建，使用其提供的 ChatOpenAI 和 OpenAIEmbeddings。这些组件支持任何 OpenAI 兼容的 API（包括 MiniMax、本地模型等）。

### 向量数据库

```bash
pymilvus>=2.3.0
```

**用途**：本地 Milvus 向量数据库，用于 RAG（检索增强生成）

**说明**：使用 Milvus 的本地文件模式（`MilvusClient`），无需启动独立服务。数据存储在 `~/.bitwiseai/milvus_data.db`。

### 数值计算

```bash
numpy>=1.20.0
```

**用途**：指令验证器（verifier.py）中的位运算和数值计算

**说明**：用于硬件指令的精确计算，如饱和运算、位移、类型转换等。

### 环境变量管理

```bash
python-dotenv>=1.0.0
```

**用途**：从 `.env` 文件加载 API 密钥和配置

**说明**：管理敏感信息（LLM_API_KEY、EMBEDDING_API_KEY 等），避免硬编码。

### 文档加载

```bash
PyPDF2>=3.0.0
```

**用途**：加载 PDF 格式的规范文档到向量库

**说明**：如果您不需要加载 PDF 规范文档，可以移除此依赖。只需要避免调用加载 PDF 的功能即可。

## 已移除的依赖

以下依赖在项目重构中已移除：

### Torch 生态（已移除）

```bash
# torch==2.2.2
# torchaudio==2.2.2
# torchvision==0.17.2
# transformers==4.44.2
```

**原因**：之前用于 `HFEmbedding` 类（Hugging Face 模型），现已删除。BitwiseAI 现在完全基于 OpenAI 兼容的 API，不再依赖本地模型。

**节省空间**：移除 torch 可以节省约 2-3 GB 的磁盘空间和内存。

### 其他已移除的依赖

```bash
# zhipuai - 智谱 AI SDK（之前的 ZhipuLLM 已删除）
# chromadb - 向量数据库（改用 pymilvus）
# unstructured - 文档解析（未使用）
# rapidocr_onnxruntime - OCR（未使用）
# pdf2image - PDF 转图片（未使用）
# pdfminer - PDF 解析（改用 PyPDF2）
# markdown - Markdown 解析（未使用）
```

## 依赖大小对比

### 重构前（包含 torch）
```
总大小: ~3.5 GB
- torch 生态: ~2.5 GB
- 其他依赖: ~1.0 GB
```

### 重构后（无 torch）
```
总大小: ~500 MB
- langchain 生态: ~200 MB
- pymilvus: ~100 MB
- numpy: ~50 MB
- 其他: ~150 MB
```

**节省：约 85% 的磁盘空间和内存！**

## 安装建议

### 完整安装

```bash
pip install -r requirements.txt
```

### 最小化安装（不含 PDF 支持）

```bash
pip install langchain langchain-openai pymilvus numpy python-dotenv
```

### 开发环境

```bash
pip install -e ".[dev]"
```

包含额外的开发工具：
- pytest - 单元测试
- black - 代码格式化
- flake8 - 代码检查

## 可选功能与依赖

| 功能 | 依赖 | 是否必需 |
|------|------|---------|
| LLM 对话 | langchain, langchain-openai | ✅ 必需 |
| RAG 规范查询 | pymilvus | ✅ 必需（如果使用 RAG） |
| 指令验证 | numpy | ✅ 必需（如果使用验证功能） |
| 加载 PDF 规范 | PyPDF2 | ⚠️ 可选 |
| 加载 txt/md 规范 | 无额外依赖 | - |

## 环境要求

- **Python**: >= 3.9
- **操作系统**: Linux, macOS, Windows
- **内存**: 建议 2GB+（如果使用大型 Embedding 模型可能需要更多）
- **磁盘空间**: ~1GB（安装后）

## 故障排查

### 问题：pymilvus 安装失败

**解决方案**：
```bash
# 更新 pip
pip install --upgrade pip

# 重新安装
pip install pymilvus
```

### 问题：langchain 版本冲突

**解决方案**：
```bash
# 卸载旧版本
pip uninstall langchain langchain-openai

# 重新安装
pip install langchain>=0.1.0 langchain-openai>=0.0.5
```

### 问题：numpy 导入错误

**解决方案**：
```bash
# 重新安装 numpy
pip install --force-reinstall numpy
```

## 总结

BitwiseAI 经过重构后，依赖更加**轻量化和聚焦**：

- ✅ **核心依赖少**：只有 5-6 个核心包
- ✅ **体积小**：从 3.5GB 降至 500MB
- ✅ **启动快**：无需加载大型本地模型
- ✅ **维护简单**：依赖关系清晰
- ✅ **灵活性高**：支持任何 OpenAI 兼容的 API

如有问题，请查看 [GitHub Issues](https://github.com/SyJarvis/BitwiseAI/issues)。

