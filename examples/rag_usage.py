# -*- coding: utf-8 -*-
"""
BitwiseAI RAG 使用示例

展示如何使用 RAG（检索增强生成）功能：
1. 加载文档到向量数据库
2. 检索相关文档
3. 使用 RAG 模式进行对话
4. 混合检索
"""

import os
from bitwiseai import BitwiseAI


def main():
    """RAG 使用示例"""
    print("=" * 60)
    print("BitwiseAI RAG 使用示例")
    print("=" * 60)
    print()
    
    # 1. 初始化 BitwiseAI
    print("1. 初始化 BitwiseAI...")
    try:
        ai = BitwiseAI()
    except ValueError as e:
        print(f"❌ 初始化失败: {e}")
        print("💡 提示: 请先运行 'bitwiseai --generate-config' 生成配置文件")
        return
    print("✓ 初始化成功\n")
    
    # 2. 加载文档到向量数据库
    print("2. 加载文档到向量数据库")
    print("-" * 60)
    
    # 示例：创建一个临时文档目录
    docs_dir = "/tmp/bitwiseai_docs"
    os.makedirs(docs_dir, exist_ok=True)
    
    # 创建示例文档
    sample_doc1 = os.path.join(docs_dir, "pe_registers.md")
    with open(sample_doc1, 'w', encoding='utf-8') as f:
        f.write("""# PE 寄存器说明

PE (Processing Element) 寄存器是硬件处理单元的核心组件。

## 主要寄存器

1. **PE_ID**: 处理单元标识符，用于区分不同的处理单元
2. **PE_STATUS**: 处理单元状态寄存器，包含运行状态、错误标志等
3. **PE_CONFIG**: 配置寄存器，用于设置处理单元的工作模式

## 使用示例

```assembly
MOV PE_ID, 0x01
MOV PE_STATUS, 0x00
```

这些寄存器在硬件调试和日志分析中非常重要。
""")
    
    sample_doc2 = os.path.join(docs_dir, "mul_instruction.md")
    with open(sample_doc2, 'w', encoding='utf-8') as f:
        f.write("""# MUL 指令说明

MUL (Multiply) 指令用于执行乘法运算。

## 语法

```
MUL dest, src1, src2
```

## 参数

- **dest**: 目标寄存器，存储乘法结果
- **src1**: 源寄存器1，乘数1
- **src2**: 源寄存器2，乘数2

## 示例

```assembly
MUL R0, R1, R2  # R0 = R1 * R2
```

## 注意事项

- 结果可能溢出，需要检查状态寄存器
- 支持有符号和无符号乘法
""")
    
    print(f"示例文档已创建在: {docs_dir}")
    print("加载文档...")
    
    # 加载文档
    stats = ai.load_documents(docs_dir, skip_duplicates=True)
    print(f"✓ 文档加载完成:")
    print(f"  - 总片段数: {stats.get('total', 0)}")
    print(f"  - 插入片段数: {stats.get('inserted', 0)}")
    print(f"  - 跳过重复数: {stats.get('skipped', 0)}\n")
    
    # 3. 基本检索
    print("3. 基本文档检索")
    print("-" * 60)
    query = "什么是 PE 寄存器？"
    context = ai.rag_engine.search(query, top_k=3)
    print(f"查询: {query}")
    print(f"检索结果:\n{context}\n")
    
    # 4. 带元数据的检索
    print("4. 带元数据的检索")
    print("-" * 60)
    query = "MUL 指令的参数有哪些？"
    results = ai.rag_engine.search_with_metadata(query, top_k=3, use_hybrid=True)
    print(f"查询: {query}")
    print(f"检索结果 ({len(results)} 条):")
    for i, result in enumerate(results, 1):
        print(f"\n结果 {i}:")
        print(f"  文本: {result.get('text', '')[:100]}...")
        print(f"  来源: {result.get('source_file', 'unknown')}")
        print(f"  相似度: {result.get('score', 0.0):.3f}")
    print()
    
    # 5. 使用 RAG 模式进行对话
    print("5. RAG 模式对话")
    print("-" * 60)
    queries = [
        "请简要介绍一下 PE 寄存器的作用",
        "MUL 指令需要哪些参数？",
        "如何检查乘法运算是否溢出？"
    ]
    
    for query in queries:
        print(f"问题: {query}")
        response = ai.chat(query, use_rag=True, use_tools=False)
        print(f"回答: {response}\n")
    
    # 6. 查看文档统计信息
    print("6. 文档统计信息")
    print("-" * 60)
    stats = ai.rag_engine.get_document_stats()
    print(f"文档统计:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    print()
    
    # 7. 查询规范文档（使用 query_specification 方法）
    print("7. 查询规范文档")
    print("-" * 60)
    query = "PE 寄存器"
    context = ai.query_specification(query, top_k=2)
    print(f"查询: {query}")
    print(f"相关文档:\n{context}\n")
    
    print("=" * 60)
    print("RAG 使用示例完成！")
    print("=" * 60)
    
    # 清理临时文件（可选）
    import shutil
    if os.path.exists(docs_dir):
        shutil.rmtree(docs_dir)
        print(f"\n✓ 已清理临时文档目录: {docs_dir}")


if __name__ == "__main__":
    main()
