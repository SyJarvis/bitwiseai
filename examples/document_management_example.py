#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BitwiseAI 文档管理示例

展示如何使用 BitwiseAI 进行文档的加载、切分、检索和导出操作
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from bitwiseai import BitwiseAI

def main():
    print("=" * 60)
    print("BitwiseAI - 文档管理示例")
    print("=" * 60)
    print()

    # ========== 1. 初始化 ==========
    print("[1/6] 初始化 BitwiseAI")
    print("-" * 60)
    try:
        ai = BitwiseAI()
        print("✓ 初始化完成\n")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print("\n请确保已正确配置 API 密钥和配置文件")
        sys.exit(1)

    # ========== 2. 清理向量数据库（可选）==========
    print("[2/6] 清理向量数据库（可选）")
    print("-" * 60)
    try:
        ai.clear_vector_db()
        print("✓ 向量数据库已清理\n")
    except Exception as e:
        print(f"⚠️  清理失败: {e}\n")

    # ========== 3. 加载文档 ==========
    print("[3/6] 加载文档")
    print("-" * 60)
    
    # 检查文档目录
    doc_folder = "./test_docs"
    if not os.path.exists(doc_folder):
        print(f"⚠️  文档目录不存在: {doc_folder}")
        print("   请创建 test_docs 目录并放入文档文件（.txt, .md, .pdf）")
        print("   或修改 doc_folder 变量指向您的文档目录\n")
    else:
        files = [f for f in os.listdir(doc_folder) 
                 if f.endswith(('.txt', '.md', '.pdf'))]
        print(f"   找到 {len(files)} 个文档文件: {files}")
        
        try:
            # 加载文档（启用去重）
            result = ai.load_documents(doc_folder, skip_duplicates=True)
            
            print(f"\n✓ 加载完成:")
            print(f"  - 总文档片段数: {result['total']}")
            print(f"  - 插入片段数: {result['inserted']}")
            print(f"  - 跳过重复片段数: {result['skipped']}")
            
            # 验证
            count = ai.rag_engine.count()
            print(f"\n  当前数据库中的文档片段数: {count}\n")
        except Exception as e:
            print(f"❌ 加载失败: {e}\n")
            import traceback
            traceback.print_exc()

    # ========== 4. 文档检索 ==========
    print("[4/6] 文档检索示例")
    print("-" * 60)
    
    queries = [
        "PE 寄存器",
        "MUL 指令",
        "SHIFT 指令"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        print("-" * 40)
        
        try:
            # 使用混合检索（向量搜索 + 关键词搜索）
            results = ai.rag_engine.search_with_metadata(
                query, 
                top_k=3, 
                use_hybrid=True
            )
            
            if results:
                for i, result in enumerate(results, 1):
                    source_file = result.get('source_file', 'unknown')
                    file_name = os.path.basename(source_file) if source_file else 'unknown'
                    print(f"\n  结果 {i}:")
                    print(f"    来源: {file_name}")
                    print(f"    内容: {result['text'][:150]}...")
                    print(f"    相似度: {result.get('score', 0.0):.3f}")
            else:
                print("  ⚠️  未找到相关内容")
        except Exception as e:
            print(f"  ❌ 检索失败: {e}")

    print("\n")

    # ========== 5. 在聊天中使用 RAG ==========
    print("[5/6] RAG 聊天示例")
    print("-" * 60)
    
    try:
        query = "请简要介绍一下 PE 寄存器的作用"
        print(f"问题: {query}")
        print("-" * 40)
        
        response = ai.chat(query, use_rag=True)
        print(f"回答: {response}\n")
    except Exception as e:
        print(f"❌ 聊天失败: {e}\n")

    # ========== 6. 导出文档（可选）==========
    print("[6/6] 导出文档（可选）")
    print("-" * 60)
    
    try:
        output_dir = "/tmp/bitwiseai_export"
        os.makedirs(output_dir, exist_ok=True)
        
        exported_count = ai.rag_engine.export_documents(
            output_dir, 
            format="separate_md"
        )
        
        print(f"✓ 导出了 {exported_count} 个文档文件到: {output_dir}")
        
        # 列出导出的文件
        if exported_count > 0:
            exported_files = [f for f in os.listdir(output_dir) if f.endswith('.md')]
            print(f"\n  导出的文件:")
            for file in exported_files[:5]:  # 只显示前5个
                file_path = os.path.join(output_dir, file)
                size = os.path.getsize(file_path)
                print(f"    - {file} ({size} bytes)")
            if len(exported_files) > 5:
                print(f"    ... 还有 {len(exported_files) - 5} 个文件")
        print()
    except Exception as e:
        print(f"⚠️  导出失败: {e}\n")

    # ========== 总结 ==========
    print("=" * 60)
    print("文档管理示例完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("  - 查看 docs/DOCUMENT_MANAGEMENT_GUIDE.md 了解详细用法")
    print("  - 尝试加载您自己的文档目录")
    print("  - 使用 RAG 模式进行智能问答")
    print("  - 导出文档进行备份或查看")
    print()

if __name__ == "__main__":
    main()

