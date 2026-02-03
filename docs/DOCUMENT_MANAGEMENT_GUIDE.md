# BitwiseAI 文档管理使用指南

本指南详细介绍如何使用 BitwiseAI 进行文档的加载、切分、去重、检索和导出操作。

## 目录

1. [快速开始](#快速开始)
2. [文档加载](#文档加载)
3. [保存临时切分文档](#保存临时切分文档)
4. [文档检索](#文档检索)
5. [文档导出](#文档导出)
6. [高级功能](#高级功能)
7. [完整示例](#完整示例)
8. [常见问题](#常见问题)

## 快速开始

### 1. 初始化 BitwiseAI

```python
from bitwiseai import BitwiseAI

# 使用默认配置文件
ai = BitwiseAI()

# 或指定配置文件路径
ai = BitwiseAI(config_path="~/.bitwiseai/config.json")
```

### 2. 清理向量数据库（可选）

如果需要重新开始，可以先清理现有的向量数据库：

```python
# 清理向量数据库（删除集合并重新创建）
ai.clear_vector_db()
print("✓ 向量数据库已清理")
```

## 文档加载

### 从文件夹加载文档

BitwiseAI 支持从文件夹批量加载文档，支持的文件格式包括：
- `.txt` - 纯文本文件
- `.md` - Markdown 文件
- `.pdf` - PDF 文档

```python
# 加载文件夹中的所有文档
folder_path = "/path/to/your/documents"
result = ai.load_documents(folder_path, skip_duplicates=True)

# 查看加载结果
print(f"总文档片段数: {result['total']}")
print(f"插入片段数: {result['inserted']}")
print(f"跳过重复片段数: {result['skipped']}")
```

**参数说明：**
- `folder_path`: 文档文件夹路径
- `skip_duplicates`: 是否跳过重复文档（默认 `True`）
  - `True`: 使用嵌入向量相似度检测重复文档，相似度超过阈值（默认0.85）的文档会被跳过
  - `False`: 不进行去重，所有文档都会被加载

**返回结果：**
```python
{
    "total": 100,      # 总文档片段数
    "inserted": 95,    # 实际插入的片段数
    "skipped": 5       # 跳过的重复片段数
}
```

### 添加单个文本

如果需要添加单个文本内容到向量数据库：

```python
text = """
这是要添加的文档内容...
可以包含多行文本。
"""

# 添加文本
count = ai.add_text(text)
print(f"✓ 添加了 {count} 个文档片段")
```

### 加载特定文件

如果需要加载单个文件，可以使用 `DocumentLoader`：

```python
from bitwiseai.utils import DocumentLoader

loader = DocumentLoader()
content = loader.load_file("/path/to/document.md")

# 然后使用 add_text 添加
ai.add_text(content)
```

## 保存临时切分文档

BitwiseAI 支持将文档切分结果保存到本地文件，便于调试和查看。

### 配置保存切分结果

在配置文件中启用切分结果保存：

```json
{
  "vector_db": {
    "save_chunks": true,
    "chunks_dir": "~/.bitwiseai/chunks"
  }
}
```

或者在代码中配置：

```python
from bitwiseai import BitwiseAI
from bitwiseai.core.document_manager import DocumentManager
from bitwiseai.vector_database import MilvusDB
from bitwiseai.utils import DocumentLoader, TextSplitter

# 初始化向量数据库
vector_db = MilvusDB(...)

# 配置文档管理器
doc_manager_config = {
    "save_chunks": True,  # 启用保存切分结果
    "chunks_dir": "~/.bitwiseai/chunks"  # 保存目录
}

document_manager = DocumentManager(
    vector_db=vector_db,
    config=doc_manager_config
)

# 加载文档（会自动保存切分结果）
result = document_manager.load_documents("/path/to/documents")
```

### 查看保存的切分结果

切分结果会以 JSON 格式保存，按源文件分组：

```
~/.bitwiseai/chunks/
├── document1_chunks.json
├── document2_chunks.json
└── ...
```

每个 JSON 文件包含该文档的所有切分片段：

```json
[
  {
    "text": "第一个文档片段的内容...",
    "source_file": "/path/to/document1.md",
    "file_hash": "abc123...",
    "chunk_index": 0,
    "chunk_total": 10,
    "timestamp": 1234567890.0,
    "text_length": 500
  },
  {
    "text": "第二个文档片段的内容...",
    "source_file": "/path/to/document1.md",
    "file_hash": "abc123...",
    "chunk_index": 1,
    "chunk_total": 10,
    "timestamp": 1234567890.0,
    "text_length": 600
  }
]
```

## 文档检索

BitwiseAI 提供多种文档检索方式，支持向量搜索和混合检索。

### 基本检索

使用 RAG 引擎进行检索：

```python
# 基本检索（返回文本内容）
query = "什么是 PE 寄存器？"
context = ai.rag_engine.search(query, top_k=5)
print(context)
```

### 混合检索（推荐）

混合检索结合了向量搜索和关键词搜索，通常能获得更好的检索效果：

```python
# 混合检索（向量搜索 + 关键词搜索）
query = "MUL 指令的参数有哪些？"
results = ai.rag_engine.search_with_metadata(
    query, 
    top_k=5, 
    use_hybrid=True
)

# 查看结果
for i, result in enumerate(results, 1):
    print(f"\n结果 {i}:")
    print(f"  文本: {result['text'][:100]}...")
    print(f"  来源: {result['source_file']}")
    print(f"  相似度: {result.get('score', 0.0):.3f}")
```

### 仅向量检索

如果只需要向量相似度搜索：

```python
# 仅向量检索
results = ai.rag_engine.search_with_metadata(
    query, 
    top_k=5, 
    use_hybrid=False
)
```

### 在聊天中使用检索

在聊天对话中，RAG 模式会自动使用文档检索：

```python
# 启用 RAG 模式的聊天
response = ai.chat(
    "请解释一下 PE 寄存器的作用",
    use_rag=True  # 启用 RAG 模式
)
print(response)
```

## 文档导出

BitwiseAI 支持将向量数据库中的文档导出为 Markdown 格式。

### 导出所有文档

```python
# 导出所有文档到指定目录
output_dir = "/path/to/output"
exported_count = ai.rag_engine.export_documents(
    output_dir, 
    format="separate_md"
)

print(f"✓ 导出了 {exported_count} 个文档文件")
```

**导出格式：**
- `separate_md`: 按源文件分别导出为多个 MD 文件（默认）

导出的文件结构：
```
output_dir/
├── document1.md
├── document2.md
└── ...
```

每个 MD 文件包含该源文档的所有切分片段，按原始顺序重组。

### 查看导出结果

```python
import os

output_dir = "/path/to/output"
exported_files = os.listdir(output_dir)

print(f"导出的文件:")
for file in exported_files:
    if file.endswith('.md'):
        file_path = os.path.join(output_dir, file)
        size = os.path.getsize(file_path)
        print(f"  - {file} ({size} bytes)")
```

## 高级功能

### 自定义相似度阈值

在配置文件中设置相似度阈值：

```json
{
  "vector_db": {
    "similarity_threshold": 0.90
  }
}
```

或在代码中设置：

```python
from bitwiseai.core.document_manager import DocumentManager

doc_manager_config = {
    "similarity_threshold": 0.90  # 更高的阈值，更严格的去重
}

document_manager = DocumentManager(
    vector_db=ai.vector_db,
    config=doc_manager_config
)
```

### 自定义文本切分参数

```python
from bitwiseai.utils import TextSplitter

# 自定义切分参数
text_splitter = TextSplitter(
    chunk_size=2000,    # 每个片段最大字符数
    chunk_overlap=300   # 片段之间的重叠字符数
)

# 使用自定义切分器
ai.text_splitter = text_splitter
```

### 检查文档是否重复

在添加文档前检查是否重复：

```python
from bitwiseai.core.document_manager import DocumentManager

document_manager = ai.document_manager

# 检查文本列表中的重复项
texts = ["文本1", "文本2", "文本3"]
is_duplicate = document_manager.check_duplicates(texts)

for i, (text, duplicate) in enumerate(zip(texts, is_duplicate)):
    if duplicate:
        print(f"文本 {i+1} 是重复的")
    else:
        print(f"文本 {i+1} 是新的")
```

### 获取文档统计信息

```python
# 获取向量数据库中的文档数量
count = ai.rag_engine.count()
print(f"当前文档片段数: {count}")

# 获取详细统计信息
stats = ai.rag_engine.get_document_stats()
print(f"统计信息: {stats}")
```

### 混合检索权重配置

在配置文件中设置混合检索的权重：

```json
{
  "vector_db": {
    "hybrid_search_weights": {
      "vector": 0.7,
      "keyword": 0.3
    }
  }
}
```

## 完整示例

以下是一个完整的使用示例，展示从加载到检索的完整流程：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BitwiseAI 文档管理完整示例
"""
from bitwiseai import BitwiseAI
import os

def main():
    # 1. 初始化 BitwiseAI
    print("=" * 50)
    print("初始化 BitwiseAI...")
    ai = BitwiseAI()
    print("✓ 初始化完成\n")

    # 2. 清理向量数据库（可选）
    print("清理向量数据库...")
    ai.clear_vector_db()
    print("✓ 清理完成\n")

    # 3. 加载文档
    print("加载文档...")
    doc_folder = "/path/to/your/documents"  # 替换为你的文档路径
    
    if not os.path.exists(doc_folder):
        print(f"⚠️  文档文件夹不存在: {doc_folder}")
        return
    
    result = ai.load_documents(doc_folder, skip_duplicates=True)
    print(f"✓ 加载完成:")
    print(f"  - 总文档片段数: {result['total']}")
    print(f"  - 插入片段数: {result['inserted']}")
    print(f"  - 跳过重复片段数: {result['skipped']}\n")

    # 4. 查看统计信息
    count = ai.rag_engine.count()
    print(f"当前数据库中的文档片段数: {count}\n")

    # 5. 检索文档
    print("=" * 50)
    print("文档检索示例\n")
    
    queries = [
        "什么是 PE 寄存器？",
        "MUL 指令如何使用？",
        "SHIFT 指令的参数有哪些？"
    ]
    
    for query in queries:
        print(f"查询: {query}")
        print("-" * 50)
        
        # 使用混合检索
        results = ai.rag_engine.search_with_metadata(
            query, 
            top_k=3, 
            use_hybrid=True
        )
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n结果 {i}:")
                print(f"  来源: {os.path.basename(result['source_file'])}")
                print(f"  内容: {result['text'][:150]}...")
                print(f"  相似度: {result.get('score', 0.0):.3f}")
        else:
            print("  未找到相关内容")
        
        print("\n")

    # 6. 导出文档（可选）
    print("=" * 50)
    print("导出文档...")
    output_dir = "/tmp/bitwiseai_export"
    os.makedirs(output_dir, exist_ok=True)
    
    exported_count = ai.rag_engine.export_documents(output_dir)
    print(f"✓ 导出了 {exported_count} 个文档文件到: {output_dir}\n")

    # 7. 在聊天中使用 RAG
    print("=" * 50)
    print("RAG 聊天示例\n")
    
    response = ai.chat(
        "请简要介绍一下 PE 寄存器的作用",
        use_rag=True
    )
    print(f"问题: 请简要介绍一下 PE 寄存器的作用")
    print(f"回答: {response}\n")

if __name__ == "__main__":
    main()
```

## 常见问题

### Q1: 如何清理向量数据库？

**A:** 使用 `clear_vector_db()` 方法：

```python
ai.clear_vector_db()
```

这会删除集合中的所有数据，但不会删除数据库文件本身。如果需要完全删除数据库文件：

```python
import os
db_file = ai.vector_db.db_file
if os.path.exists(db_file):
    os.remove(db_file)
    # 重新初始化
    ai = BitwiseAI()
```

### Q2: 如何调整文档切分的大小？

**A:** 自定义 `TextSplitter` 参数：

```python
from bitwiseai.utils import TextSplitter

ai.text_splitter = TextSplitter(
    chunk_size=2000,    # 增大或减小片段大小
    chunk_overlap=300   # 调整重叠大小
)
```

### Q3: 如何调整去重的相似度阈值？

**A:** 在配置文件中设置：

```json
{
  "vector_db": {
    "similarity_threshold": 0.90
  }
}
```

或在代码中配置 `DocumentManager`。

### Q4: 为什么有些文档没有被加载？

**A:** 可能的原因：
1. 文档格式不支持（仅支持 `.txt`, `.md`, `.pdf`）
2. 文档内容为空
3. 文档被识别为重复（如果启用了去重）
4. 文件读取失败（检查文件权限和编码）

### Q5: 如何查看切分后的文档片段？

**A:** 启用切分结果保存功能：

```json
{
  "vector_db": {
    "save_chunks": true,
    "chunks_dir": "~/.bitwiseai/chunks"
  }
}
```

切分结果会以 JSON 格式保存在指定目录。

### Q6: 检索结果不准确怎么办？

**A:** 可以尝试：
1. 使用混合检索（`use_hybrid=True`）
2. 调整 `top_k` 参数，增加返回结果数量
3. 优化查询语句，使用更具体的关键词
4. 检查文档切分是否合理，可能需要调整 `chunk_size`

### Q7: 如何导出特定来源的文档？

**A:** 目前导出功能会导出所有文档。如果需要导出特定文档，可以：
1. 先导出所有文档
2. 根据文件名或内容筛选需要的文档

### Q8: 支持哪些文档格式？

**A:** 目前支持：
- `.txt` - 纯文本文件
- `.md` - Markdown 文件
- `.pdf` - PDF 文档

### Q9: 如何批量加载多个文件夹？

**A:** 循环加载多个文件夹：

```python
folders = [
    "/path/to/folder1",
    "/path/to/folder2",
    "/path/to/folder3"
]

total_inserted = 0
for folder in folders:
    result = ai.load_documents(folder, skip_duplicates=True)
    total_inserted += result['inserted']
    print(f"✓ {folder}: 插入 {result['inserted']} 个片段")

print(f"\n总计插入: {total_inserted} 个片段")
```

### Q10: 如何检查文档是否已加载？

**A:** 使用统计信息：

```python
# 获取文档数量
count = ai.rag_engine.count()
print(f"当前文档片段数: {count}")

# 获取详细统计
stats = ai.rag_engine.get_document_stats()
print(stats)
```

## 最佳实践

1. **文档组织**: 将相关文档放在同一文件夹中，便于批量加载
2. **去重设置**: 首次加载时建议启用去重（`skip_duplicates=True`）
3. **切分大小**: 根据文档类型调整 `chunk_size`，技术文档建议 1000-2000 字符
4. **检索策略**: 优先使用混合检索（`use_hybrid=True`）以获得更好的结果
5. **定期备份**: 定期导出文档，作为备份
6. **性能优化**: 大批量文档加载时，可以分批处理

## 相关文档

- [使用指南](USAGE_GUIDE.md) - BitwiseAI 基本使用
- [架构文档](ARCHITECTURE.md) - 系统架构说明
- [CLI 使用指南](CLI_USAGE_GUIDE.md) - 命令行工具使用

## 技术支持

如有问题，请查看：
- GitHub Issues: [项目地址]
- 文档: [文档地址]

