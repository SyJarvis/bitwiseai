#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BitwiseAI RAG 使用示例

演示如何使用 RAG (检索增强生成) 功能
"""
import os
from pathlib import Path
from bitwiseai import BitwiseAI


def example_1_load_documents():
    """示例 1: 加载文档到向量数据库"""
    print("=" * 60)
    print("示例 1: 加载文档到向量数据库")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 方式 1: 加载整个文件夹
    docs_dir = os.path.expanduser("~/Documents/hardware_specs")
    if os.path.exists(docs_dir):
        result = ai.load_documents(docs_dir, skip_duplicates=True)
        print(f"✓ 已加载文档目录: {docs_dir}")
        print(f"  结果: {result}")
    else:
        print(f"⚠️  目录不存在: {docs_dir}")
        print("  请创建目录并添加一些文档")

    # 方式 2: 添加单个文本
    ai.add_text("""
    MUL 指令说明
    =============

    MUL 指令用于执行乘法运算。

    语法: MUL Rd, Rn, Rm
    - Rd: 目标寄存器
    - Rn: 第一个操作数寄存器
    - Rm: 第二个操作数寄存器

    约束:
    - Rd 和 Rn 不能是同一个寄存器
    - 所有寄存器必须是 32 位通用寄存器
    """)
    print("\n✓ 已添加 MUL 指令说明")


def example_2_basic_rag_query():
    """示例 2: 基础 RAG 查询"""
    print("\n" + "=" * 60)
    print("示例 2: 基础 RAG 查询")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 使用 RAG 模式对话
    query = "MUL 指令的寄存器约束是什么？"
    print(f"问题: {query}")

    response = ai.chat(query, use_rag=True)
    print(f"\nRAG 回答:\n{response}")


def example_3_rag_with_context():
    """示例 3: 查看 RAG 检索到的上下文"""
    print("\n" + "=" * 60)
    print("示例 3: 查看 RAG 检索到的上下文")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 直接查询向量数据库，获取检索结果
    query = "MUL 指令怎么用？"
    print(f"查询: {query}")

    # 使用 RAG 引擎的 search 方法
    context = ai.rag_engine.search(query, top_k=3)
    print(f"\n检索到的上下文:\n{context}")


def example_4_rag_with_metadata():
    """示例 4: 带元数据的 RAG 检索"""
    print("\n" + "=" * 60)
    print("示例 4: 带元数据的 RAG 检索")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 使用 search_with_metadata 获取详细信息
    query = "乘法指令"
    print(f"查询: {query}")

    results = ai.rag_engine.search_with_metadata(
        query,
        top_k=5,
        use_hybrid=True  # 使用混合检索（向量 + 关键词）
    )

    print(f"\n找到 {len(results)} 个相关片段:")
    for i, result in enumerate(results, 1):
        source = result.get('source_file', '未知')
        score = result.get('score', 0.0)
        text = result.get('text', '')[:100]
        print(f"\n{i}. 来源: {Path(source).name}")
        print(f"   相似度: {score:.4f}")
        print(f"   内容: {text}...")


def example_5_rag_with_history():
    """示例 5: RAG 配合对话历史"""
    print("\n" + "=" * 60)
    print("示例 5: RAG 配合对话历史")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 构建对话历史
    history = [
        {"role": "user", "content": "我想了解硬件指令"},
        {"role": "assistant", "content": "好的，我可以帮你了解各种硬件指令。"},
        {"role": "user", "content": "先介绍一下算术指令"},
        {"role": "assistant", "content": "算术指令包括 ADD、SUB、MUL、DIV 等，用于执行基本数学运算。"},
    ]

    # 基于 RAG 和历史继续对话
    query = "那 MUL 指令具体怎么用？"
    print(f"问题: {query}")

    response = ai.chat(query, use_rag=True, history=history)
    print(f"\n回答:\n{response}")


def example_6_batch_add_documents():
    """示例 6: 批量添加文档"""
    print("\n" + "=" * 60)
    print("示例 6: 批量添加文档")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 准备多个文档
    documents = {
        "ADD 指令": """
        ADD 指令说明
        =============

        ADD 指令用于执行加法运算。

        语法: ADD Rd, Rn, Rm
        - Rd: 目标寄存器
        - Rn: 第一个操作数寄存器
        - Rm: 第二个操作数寄存器或立即数
        """,

        "SUB 指令": """
        SUB 指令说明
        =============

        SUB 指令用于执行减法运算。

        语法: SUB Rd, Rn, Rm
        - Rd: 目标寄存器
        - Rn: 被减数寄存器
        - Rm: 减数寄存器或立即数
        """,

        "SHIFT 指令": """
        SHIFT 指令说明
        ==============

        SHIFT 指令用于执行位移操作。

        语法: SHIFT Rd, Rn, <shift_type>, <amount>
        - shift_type: LSL, LSR, ASR, ROR
        - amount: 位移量（0-31）
        """,
    }

    # 批量添加
    for title, content in documents.items():
        ai.add_text(content)
        print(f"✓ 已添加: {title}")

    print(f"\n总共添加了 {len(documents)} 个文档")


def example_7_rag_with_tools():
    """示例 7: RAG 配合工具使用"""
    print("\n" + "=" * 60)
    print("示例 7: RAG 配合工具使用")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 加载一些 Skills
    skills = ai.list_skills()
    for skill in skills[:2]:
        ai.load_skill(skill)

    print(f"已加载 Skills: {ai.list_skills(loaded_only=True)}")

    # 同时使用 RAG 和工具
    query = "计算 0x10 + 0x20，并解释 MUL 指令"
    print(f"问题: {query}")

    response = ai.chat(query, use_rag=True, use_tools=True)
    print(f"\n回答:\n{response}")


def example_8_clear_vector_db():
    """示例 8: 清空向量数据库"""
    print("\n" + "=" * 60)
    print("示例 8: 清空向量数据库")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    # 确认清空
    print("⚠️  即将清空向量数据库")
    print("这将删除所有已加载的文档")

    # ai.clear_vector_db()
    print("✓ 向量数据库已清空")

    print("\n提示: 取消注释 ai.clear_vector_db() 来执行清空操作")


def example_9_rag_configuration():
    """示例 9: RAG 配置说明"""
    print("\n" + "=" * 60)
    print("示例 9: RAG 配置说明")
    print("=" * 60)

    print("""
RAG 配置选项
============

在 ~/.bitwiseai/config.json 中配置:

{
  "vector_db": {
    "db_file": "~/.bitwiseai/milvus_data.db",
    "collection_name": "bitwiseai",
    "embedding_dim": 1536,
    "similarity_threshold": 0.85,
    "save_chunks": false,
    "chunks_dir": "~/.bitwiseai/chunks"
  },
  "embedding": {
    "model": "text-embedding-3-small",
    "api_key": "sk-xxx",
    "base_url": "https://api.openai.com/v1"
  }
}

配置说明:
-----------
- db_file: 向量数据库文件路径
- collection_name: 集合名称（用于隔离不同数据）
- embedding_dim: 向量维度（需要与模型匹配）
- similarity_threshold: 相似度阈值（0-1，越高越严格）
- save_chunks: 是否保存切分后的文本块
- chunks_dir: 文本块保存目录

检索方式:
---------
- 向量检索: 基于语义相似度
- 混合检索: 向量 + 关键词 (use_hybrid=True)
- 文档名匹配: 基于文件名匹配
    """)


def example_10_document_types():
    """示例 10: 支持的文档类型"""
    print("\n" + "=" * 60)
    print("示例 10: 支持的文档类型")
    print("=" * 60)

    print("""
支持的文档类型
==============

1. 文本文件 (.txt, .md)
   - 直接读取内容
   - 自动切分

2. PDF 文件 (.pdf)
   - 需要 PyPDF2
   - 自动提取文本

3. Markdown 文件 (.md)
   - 保留格式
   - 支持代码块

4. 代码文件 (.py, .js, .java 等)
   - 语法高亮支持
   - 按函数/类切分

5. 纯文本
   - 使用 add_text() 方法
   - 直接添加到向量库

文档切分策略
============
- 默认按段落切分
- 保留上下文重叠
- 自动去除空白字符
- 支持自定义切分器

检索策略
========
- top_k: 返回前 k 个最相关的片段
- use_hybrid: 混合检索（向量 + BM25）
- similarity_threshold: 相似度过滤
- document_name_match: 文档名匹配
    """)


def example_11_complete_workflow():
    """示例 11: 完整 RAG 工作流"""
    print("\n" + "=" * 60)
    print("示例 11: 完整 RAG 工作流")
    print("=" * 60)

    ai = BitwiseAI(use_enhanced=True)

    print("步骤 1: 准备文档")
    # 准备技术文档
    docs = {
        "API 文档": "这是 API 接口的说明文档...",
        "用户手册": "这是用户操作手册...",
        "开发指南": "这是开发者指南...",
    }
    for title, content in docs.items():
        ai.add_text(f"{title}\n{'='*40}\n{content}")
        print(f"  ✓ {title}")

    print("\n步骤 2: 测试检索")
    # 测试检索效果
    query = "如何使用 API？"
    context = ai.rag_engine.search(query, top_k=3)
    print(f"  查询: {query}")
    print(f"  检索到 {len(context.split('---')) if context else 0} 个片段")

    print("\n步骤 3: RAG 对话")
    # 使用 RAG 回答问题
    response = ai.chat("API 的认证方式有哪些？", use_rag=True)
    print(f"  回答: {response[:100]}...")

    print("\n步骤 4: 持久化")
    # 数据自动保存在向量数据库中
    print(f"  ✓ 数据已保存到: ~/.bitwiseai/milvus_data.db")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("BitwiseAI RAG 使用示例")
    print("=" * 60 + "\n")

    examples = [
        ("示例 1: 加载文档", example_1_load_documents),
        ("示例 2: 基础 RAG 查询", example_2_basic_rag_query),
        ("示例 3: 查看检索上下文", example_3_rag_with_context),
        ("示例 4: 带元数据的检索", example_4_rag_with_metadata),
        ("示例 5: RAG 配合历史", example_5_rag_with_history),
        ("示例 6: 批量添加文档", example_6_batch_add_documents),
        ("示例 7: RAG 配合工具", example_7_rag_with_tools),
        ("示例 8: 清空向量库", example_8_clear_vector_db),
        ("示例 9: RAG 配置", example_9_rag_configuration),
        ("示例 10: 文档类型", example_10_document_types),
        ("示例 11: 完整工作流", example_11_complete_workflow),
    ]

    print("可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print()

    import sys
    if len(sys.argv) > 1:
        try:
            idx = int(sys.argv[1]) - 1
            if 0 <= idx < len(examples):
                _, func = examples[idx]
                func()
            else:
                print(f"❌ 无效的示例编号: {sys.argv[1]}")
        except ValueError:
            print("❌ 请输入数字编号")
    else:
        # 默认运行第一个示例
        example_1_load_documents()


if __name__ == "__main__":
    main()
