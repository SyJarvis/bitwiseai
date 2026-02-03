# BitwiseAI 持久化记忆系统设计文档

## 概述

本文档描述 BitwiseAI 新的持久化记忆系统架构，该系统完全替换了原有的 Milvus 向量数据库实现，采用 SQLite + Markdown 双层次存储架构。

## 设计目标

1. **存储后端** - 使用 SQLite 作为单一存储后端
2. **双层次记忆架构** - 短期记忆（每日日志）+ 长期记忆（精选持久记忆）
3. **混合搜索** - 向量相似度搜索 + BM25 关键词搜索
4. **文件监控** - 自动监控 Markdown 文件变化并重新索引
5. **零配置部署** - 无需外部服务，开箱即用

## 架构设计

### 1. 模块结构

```
bitwiseai/core/memory/
├── __init__.py              # 模块导出
├── types.py                 # 类型定义
├── schema.py                # 数据库 Schema
├── storage.py               # SQLite 存储后端
├── chunker.py               # Markdown 分块逻辑
├── indexer.py               # 内容索引器
├── searcher.py              # 混合搜索引擎
├── watcher.py               # 文件监控
├── manager.py               # 统一记忆管理器
└── embeddings/              # Embedding Provider
    ├── __init__.py
    ├── base.py              # 抽象基类
    └── openai_provider.py   # OpenAI/Zhipu 实现
```

### 2. 双层次记忆架构

#### 2.1 短期记忆 (Short-term Memory)
- **存储位置**: `~/.bitwiseai/memory/YYYY-MM-DD.md`
- **用途**: 每日日志，记录临时信息
- **保留策略**: 可配置保留天数（默认7天），过期后可压缩归档
- **自动索引**: 文件变更自动触发重新索引

#### 2.2 长期记忆 (Long-term Memory)
- **存储位置**: `~/.bitwiseai/MEMORY.md`
- **用途**: 精选持久记忆，重要信息长期保存
- **内容组织**: 按主题分类，支持手动编辑
- **优先检索**: 搜索时长期记忆优先级更高

### 3. 核心类设计

#### 3.1 SQLiteStorage - SQLite 存储后端
负责数据库连接管理和基础 CRUD 操作：

```python
class SQLiteStorage:
    def __init__(self, db_path: str, vector_enabled: bool = True)
    def initialize(self) -> None                    # 初始化 Schema
    def upsert_file(self, path, source, hash, mtime, size)
    def upsert_chunk(self, chunk: ChunkRecord)
    def search_vectors(self, query_vec, limit) -> List[VectorSearchResult]
    def search_fts(self, query, limit) -> List[FTSSearchResult]
    def cache_embedding(self, text_hash, provider_key, embedding)
```

**特性**:
- WAL 模式支持高并发
- 线程本地连接管理
- Embedding 缓存避免重复计算

#### 3.2 MemoryIndexer - 内容索引器
负责文档分块、Embedding 生成和存储：

```python
class MemoryIndexer:
    def __init__(self, storage, embedding_provider, chunk_config)
    def index_file(self, file_path, content, source) -> IndexResult
    def index_memory_file(self, abs_path, workspace_dir) -> IndexResult
    def delete_index(self, path, source)
    def _chunk_content(self, content) -> List[MemoryChunk]
    async def _embed_chunks(self, chunks) -> List[List[float]]
```

**分块策略**:
- 默认 400 tokens 每块
- 80 tokens 重叠保留上下文
- 保留行号信息用于溯源

#### 3.3 MemorySearcher - 混合搜索引擎
结合向量搜索和 BM25 关键词搜索：

```python
class MemorySearcher:
    def __init__(self, storage, embedding_provider, hybrid_config)
    async def search(self, query, max_results, min_score) -> List[SearchResult]
    def _merge_results(self, vector_results, keyword_results) -> List[SearchResult]
```

**混合搜索算法**:
1. 向量搜索: 基于余弦相似度的语义搜索
2. 关键词搜索: 基于 FTS5 + BM25 的精确匹配
3. 结果融合: 加权排序 (默认 70% 向量 + 30% 关键词)

#### 3.4 MemoryManager - 统一记忆管理器
双层次记忆的统一入口：

```python
class MemoryManager:
    def __init__(self, workspace_dir, db_path, embedding_provider)
    def initialize(self)

    # 双层次记忆 API
    def get_short_term_memory_path(self, date) -> Path
    def get_long_term_memory_path(self) -> Path
    def append_to_short_term(self, content, date, metadata)
    def promote_to_long_term(self, content, summary)
    def compact_short_term(self, days_to_keep) -> CompactResult

    # 搜索 API
    async def search(self, query, max_results) -> List[SearchResult]

    # 索引管理
    async def sync(self, force) -> SyncResult
    def index_skill(self, skill_path, skill_metadata)
    def index_document(self, doc_path, content)
```

#### 3.5 FileWatcher - 文件监控器
监控记忆文件变更：

```python
class FileWatcher:
    def __init__(self, watch_paths, on_change, debounce_ms=1000)
    def start(self) / def stop(self)
    def add_path(self, path) / def remove_path(self, path)

class PollingFileWatcher:
    # watchdog 不可用的轮询回退方案
```

**特性**:
- 基于 watchdog 的事件驱动监控
- 防抖处理 (默认 1 秒)
- 轮询回退方案 ( watchdog 不可用时)

### 4. 数据库 Schema

#### 4.1 核心表

```sql
-- 元数据表
CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 文件追踪表
CREATE TABLE files (
    path TEXT PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'memory',
    hash TEXT NOT NULL,
    mtime INTEGER NOT NULL,
    size INTEGER NOT NULL
);

-- 内容块表
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'memory',
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    hash TEXT NOT NULL,
    model TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding TEXT NOT NULL,  -- JSON 序列化
    updated_at INTEGER NOT NULL
);

-- Embedding 缓存表
CREATE TABLE embedding_cache (
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    provider_key TEXT NOT NULL,
    hash TEXT NOT NULL,
    embedding TEXT NOT NULL,
    dims INTEGER,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (provider, model, provider_key, hash)
);
```

#### 4.2 FTS5 全文搜索

```sql
-- 虚拟表用于 BM25 搜索
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    chunk_id, text, path, source, start_line, end_line,
    content='chunks', content_rowid='rowid'
);

-- 自动同步触发器
CREATE TRIGGER chunks_fts_insert AFTER INSERT ON chunks ...
CREATE TRIGGER chunks_fts_delete AFTER DELETE ON chunks ...
CREATE TRIGGER chunks_fts_update AFTER UPDATE ON chunks ...
```

### 5. Embedding Provider 抽象

支持多种 Embedding 服务：

```python
class EmbeddingProvider(ABC):
    @property @abstractmethod def id(self) -> str
    @property @abstractmethod def model(self) -> str
    @abstractmethod async def embed_query(self, text) -> List[float]
    @abstractmethod async def embed_batch(self, texts) -> List[List[float]]

class OpenAIEmbeddingProvider(EmbeddingProvider):
    # OpenAI API 兼容实现 (OpenAI, Zhipu, etc.)

class LocalEmbeddingProvider(EmbeddingProvider):
    # 本地模型实现 (如 sentence-transformers)
```

## 文件变更清单

### 新建文件 (13个)

| 文件路径 | 说明 |
|---------|------|
| `bitwiseai/core/memory/__init__.py` | 模块导出 |
| `bitwiseai/core/memory/types.py` | 类型定义 |
| `bitwiseai/core/memory/schema.py` | 数据库 Schema |
| `bitwiseai/core/memory/storage.py` | SQLiteStorage 实现 |
| `bitwiseai/core/memory/chunker.py` | MarkdownChunker |
| `bitwiseai/core/memory/indexer.py` | MemoryIndexer 实现 |
| `bitwiseai/core/memory/searcher.py` | MemorySearcher 实现 |
| `bitwiseai/core/memory/watcher.py` | FileWatcher 实现 |
| `bitwiseai/core/memory/manager.py` | MemoryManager 实现 |
| `bitwiseai/core/memory/embeddings/__init__.py` | Embedding 模块 |
| `bitwiseai/core/memory/embeddings/base.py` | 抽象基类 |
| `bitwiseai/core/memory/embeddings/openai_provider.py` | OpenAI Provider |
| `examples/memory_system_test.py` | 测试代码 |

### 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `bitwiseai/vector_database.py` | **删除** - 完全移除 MilvusDB |
| `bitwiseai/core/document_manager.py` | 重写 - 使用 MemoryManager |
| `bitwiseai/core/skill_indexer.py` | 重写 - 使用 MemoryManager |
| `bitwiseai/core/rag_engine.py` | 更新 - 使用 MemoryManager |
| `bitwiseai/core/__init__.py` | 添加 memory 模块导出 |
| `bitwiseai/bitwiseai.py` | 更新初始化，添加 `source` 参数 |
| `bitwiseai/config.json.example` | 新配置格式 |

### 依赖变更

```txt
# 移除
- pymilvus

# 添加
+ watchdog>=3.0.0    # 文件监控 (可选)
```

## 配置示例

```json
{
  "llm": {
    "model": "gpt-4o-mini",
    "api_key": "sk-..."
  },
  "embedding": {
    "model": "text-embedding-3-small",
    "api_key": "sk-..."
  },
  "memory": {
    "enabled": true,
    "workspace_dir": "~/.bitwiseai",
    "db_path": "~/.bitwiseai/memory.db",
    "vector_enabled": true,
    "chunking": {
      "tokens": 400,
      "overlap": 80
    },
    "hybrid_search": {
      "enabled": true,
      "vector_weight": 0.7,
      "text_weight": 0.3,
      "min_score": 0.5
    },
    "sync": {
      "watch": true,
      "watch_debounce_ms": 1000
    },
    "short_term": {
      "enabled": true,
      "retention_days": 7
    }
  }
}
```

## 使用示例

```python
from bitwiseai import BitwiseAI

# 初始化
ai = BitwiseAI()

# 写入短期记忆
ai.append_to_memory("今天学习了 ARM 指令", to_long_term=False)

# 写入长期记忆
ai.append_to_memory("ARM 乘法指令约束: Rd 和 Rm 不能相同", to_long_term=True)

# 搜索记忆
results = ai.search_memory("ARM 指令约束", max_results=5)

# 添加文档到知识库
ai.add_text("MUL 指令文档...", source="manual.md")

# 压缩短期记忆（归档过期内容）
ai.compact_memory(days_to_keep=7)

# 获取统计信息
stats = ai.get_memory_stats()
```

## 优势对比

| 特性 | 旧实现 (Milvus) | 新实现 (SQLite) |
|-----|----------------|----------------|
| 部署复杂度 | 需要独立服务 | 零配置，开箱即用 |
| 存储架构 | 单一向量存储 | 双层次记忆系统 |
| 搜索方式 | 纯向量搜索 | 向量 + BM25 混合 |
| 文件监控 | 无 | 自动监控 + 防抖 |
| 依赖数量 | 多 (pymilvus等) | 少 (仅 watchdog) |
| 可移植性 | 依赖外部服务 | 纯本地文件 |
| 编辑友好性 | 数据库二进制 | Markdown 可直接编辑 |

## 总结

新的持久化记忆系统通过 SQLite + Markdown 架构实现了：

1. **更简单的部署** - 无需外部服务，纯本地实现
2. **更智能的记忆** - 双层次架构区分临时和持久信息
3. **更强大的搜索** - 混合搜索结合语义和关键词匹配
4. **更好的可观测性** - Markdown 文件可直接查看和编辑
5. **更高的效率** - Embedding 缓存避免重复计算

