#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BitwiseAI 记忆系统测试示例

演示新的双层次记忆系统功能：
- 短期记忆：memory/YYYY-MM-DD.md 每日日志
- 长期记忆：MEMORY.md 精选持久记忆
- 混合搜索：向量相似度 + BM25 关键词搜索
- 文件监控：自动重新索引
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from bitwiseai import BitwiseAI


def test_1_memory_initialization():
    """测试 1: 记忆系统初始化"""
    print("=" * 60)
    print("测试 1: 记忆系统初始化")
    print("=" * 60)

    try:
        ai = BitwiseAI()

        # 获取记忆系统状态
        stats = ai.get_memory_stats()
        print(f"✓ 记忆系统已初始化")
        print(f"  - 初始化状态: {stats['initialized']}")
        print(f"  - 总文件数: {stats['total_files']}")
        print(f"  - 总块数: {stats['total_chunks']}")
        print(f"  - 向量数: {stats['total_vectors']}")
        print(f"  - 缓存条目: {stats['cache_entries']}")
        print(f"  - 数据库大小: {stats['db_size_bytes'] / 1024:.2f} KB")
        print(f"  - 文件监控: {'开启' if stats['watching'] else '关闭'}")

        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def test_2_short_term_memory():
    """测试 2: 短期记忆写入和读取"""
    print("\n" + "=" * 60)
    print("测试 2: 短期记忆写入和读取")
    print("=" * 60)

    try:
        ai = BitwiseAI()

        # 写入短期记忆
        print("\n1. 写入短期记忆...")
        ai.append_to_memory(
            content="今天分析了 ARM 指令验证失败的问题，发现是寄存器约束检查不完整导致的。",
            to_long_term=False
        )
        print("✓ 已写入短期记忆")

        # 再写入一条
        ai.append_to_memory(
            content="修复了 MUL 指令的边界情况处理，添加了负数支持。",
            to_long_term=False
        )
        print("✓ 已写入第二条短期记忆")

        # 搜索记忆
        print("\n2. 搜索短期记忆...")
        results = ai.search_memory("ARM 指令验证", max_results=3)
        print(f"✓ 找到 {len(results)} 条相关记忆")
        for i, r in enumerate(results, 1):
            print(f"  {i}. [score: {r['score']:.3f}] {r['text'][:60]}...")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_long_term_memory():
    """测试 3: 长期记忆写入和读取"""
    print("\n" + "=" * 60)
    print("测试 3: 长期记忆写入和读取")
    print("=" * 60)

    try:
        ai = BitwiseAI()

        # 写入长期记忆
        print("\n1. 写入长期记忆...")
        ai.append_to_memory(
            content="""
ARM 指令验证的关键检查点：
1. 寄存器约束检查 - 确保 Rd, Rn, Rm 符合规范
2. 立即数范围检查 - 验证立即数是否在有效范围内
3. 边界情况处理 - 处理负数、零、最大值等特殊情况
4. 指令编码验证 - 检查二进制编码是否正确
            """.strip(),
            to_long_term=True
        )
        print("✓ 已写入长期记忆")

        # 再写入一条
        ai.append_to_memory(
            content="""
MUL 指令验证要点：
- 结果寄存器不能与第一个操作数相同（ARMv7 限制）
- 支持 32x32=64 位结果的高低位存储
- 条件执行标志位的正确处理
            """.strip(),
            to_long_term=True
        )
        print("✓ 已写入第二条长期记忆")

        # 搜索长期记忆
        print("\n2. 搜索长期记忆...")
        results = ai.search_memory("MUL 指令验证", max_results=3)
        print(f"✓ 找到 {len(results)} 条相关记忆")
        for i, r in enumerate(results, 1):
            print(f"  {i}. [score: {r['score']:.3f}] {r['text'][:60]}...")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_hybrid_search():
    """测试 4: 混合搜索（向量 + BM25）"""
    print("\n" + "=" * 60)
    print("测试 4: 混合搜索（向量 + BM25）")
    print("=" * 60)

    try:
        ai = BitwiseAI()

        # 添加一些测试内容
        print("\n1. 添加测试内容...")
        test_docs = [
            "ADD 指令用于执行加法运算，将两个寄存器的值相加。",
            "SUB 指令用于执行减法运算，从第一个寄存器减去第二个寄存器。",
            "MUL 指令用于执行乘法运算，支持有符号和无符号乘法。",
            "DIV 指令用于执行除法运算，需要注意除零检查。",
            "AND 指令用于按位与运算，常用于掩码操作。",
            "ORR 指令用于按位或运算，常用于设置标志位。",
            "XOR 指令用于按位异或运算，常用于加密算法。",
        ]

        for doc in test_docs:
            ai.add_text(doc)
        print(f"✓ 已添加 {len(test_docs)} 个测试文档")

        # 测试不同查询
        print("\n2. 测试混合搜索...")
        queries = [
            "加法运算",
            "multiplication operation",
            "位运算",
            "除零检查",
        ]

        for query in queries:
            results = ai.search_memory(query, max_results=3)
            print(f"\n  查询: '{query}'")
            print(f"  找到 {len(results)} 条结果:")
            for i, r in enumerate(results, 1):
                print(f"    {i}. [{r['score']:.3f}] {r['text'][:50]}...")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_document_management():
    """测试 5: 文档管理和检索"""
    print("\n" + "=" * 60)
    print("测试 5: 文档管理和检索")
    print("=" * 60)

    try:
        ai = BitwiseAI()

        # 添加文档
        print("\n1. 添加文档到知识库...")
        doc_content = """
# 硬件调试指南

## 寄存器检查
- 检查寄存器值是否符合预期
- 验证标志位设置是否正确
- 注意溢出的处理

## 内存访问
- 验证地址对齐
- 检查访问权限
- 注意缓存一致性

## 指令解码
- 验证操作码
- 检查操作数类型
- 确认指令长度
        """
        ai.add_text(doc_content, source="debug_guide.md")
        print("✓ 已添加调试指南")

        # 检索文档
        print("\n2. 检索文档...")
        results = ai.search_memory("寄存器检查", max_results=2)
        print(f"✓ 找到 {len(results)} 条相关文档")
        for i, r in enumerate(results, 1):
            print(f"  {i}. 来源: {r['path']}")
            print(f"     行: {r['start_line']}-{r['end_line']}")
            print(f"     内容: {r['text'][:80]}...")

        # 获取统计信息
        print("\n3. 文档统计...")
        stats = ai.rag_engine.get_document_stats()
        print(f"  总块数: {stats['total_chunks']}")
        print(f"  总文件数: {stats['total_files']}")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_skill_indexing():
    """测试 6: 技能索引和搜索"""
    print("\n" + "=" * 60)
    print("测试 6: 技能索引和搜索")
    print("=" * 60)

    try:
        ai = BitwiseAI()

        # 列出可用技能
        print("\n1. 列出可用技能...")
        skills = ai.list_skills()
        print(f"✓ 找到 {len(skills)} 个可用技能")
        for skill in skills[:5]:  # 只显示前5个
            print(f"  - {skill}")
        if len(skills) > 5:
            print(f"  ... 还有 {len(skills) - 5} 个")

        # 搜索技能
        if skills:
            print("\n2. 搜索技能...")
            query = "hex" if "hex-converter" in skills else skills[0]
            results = ai.search_skills(query, top_k=3)
            print(f"✓ 搜索 '{query}' 找到 {len(results)} 个结果")
            for i, r in enumerate(results, 1):
                print(f"  {i}. {r.get('skill_name', 'Unknown')}")
                print(f"     描述: {r.get('description', 'N/A')[:50]}...")
                print(f"     相似度: {r.get('score', 0):.3f}")

        # 加载技能
        if skills:
            print("\n3. 加载技能...")
            skill_name = skills[0]
            success = ai.load_skill(skill_name)
            if success:
                print(f"✓ 已加载技能: {skill_name}")
                loaded = ai.list_skills(loaded_only=True)
                print(f"  当前已加载: {loaded}")
            else:
                print(f"⚠️  加载技能失败: {skill_name}")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_7_memory_compaction():
    """测试 7: 记忆压缩"""
    print("\n" + "=" * 60)
    print("测试 7: 记忆压缩")
    print("=" * 60)

    try:
        ai = BitwiseAI()

        # 获取压缩前状态
        print("\n1. 压缩前状态...")
        stats_before = ai.get_memory_stats()
        print(f"  文件数: {stats_before['total_files']}")
        print(f"  块数: {stats_before['total_chunks']}")

        # 执行压缩
        print("\n2. 执行记忆压缩...")
        result = ai.compact_memory(days_to_keep=0)  # 压缩所有短期记忆
        print(f"✓ 压缩完成")
        print(f"  压缩文件数: {result['files_compacted']}")
        print(f"  归档文件数: {result['files_archived']}")
        print(f"  生成摘要数: {result['summaries_generated']}")

        # 获取压缩后状态
        print("\n3. 压缩后状态...")
        stats_after = ai.get_memory_stats()
        print(f"  文件数: {stats_after['total_files']}")
        print(f"  块数: {stats_after['total_chunks']}")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_8_rag_integration():
    """测试 8: RAG 集成"""
    print("\n" + "=" * 60)
    print("测试 8: RAG 集成")
    print("=" * 60)

    try:
        ai = BitwiseAI()

        # 添加技术文档
        print("\n1. 添加技术文档...")
        tech_doc = """
# ARM 乘法指令详解

## MUL 指令
MUL (Multiply) 指令执行 32x32=32 位乘法。

语法: MUL{cond}{S} Rd, Rn, Rm
- Rd: 目标寄存器
- Rn: 第一个操作数寄存器
- Rm: 第二个操作数寄存器

约束:
- Rd 和 Rm 不能是同一个寄存器（ARMv7 之前）
- 结果只保留低 32 位

## MLA 指令
MLA (Multiply-Accumulate) 执行乘加运算。

语法: MLA{cond}{S} Rd, Rn, Rm, Ra
- 计算: Rd = (Rn × Rm) + Ra

## SMULL/UMULL
长乘法指令，产生 64 位结果。

语法: SMULL{cond}{S} RdLo, RdHi, Rn, Rm
- RdLo: 低 32 位
- RdHi: 高 32 位
        """
        ai.add_text(tech_doc)
        print("✓ 已添加技术文档")

        # 使用 RAG 查询
        print("\n2. 使用 RAG 查询...")
        query = "MUL 指令的约束是什么？"
        response = ai.query_specification(query)
        print(f"查询: {query}")
        print(f"回答:\n{response[:300]}...")

        # 带上下文的对话
        print("\n3. 带 RAG 的对话...")
        response = ai.chat(
            "解释一下 MLA 指令和 MUL 指令的区别",
            use_rag=True
        )
        print(f"回答:\n{response[:300]}...")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_9_memory_persistence():
    """测试 9: 记忆持久化"""
    print("\n" + "=" * 60)
    print("测试 9: 记忆持久化")
    print("=" * 60)

    try:
        ai = BitwiseAI()

        # 检查记忆文件
        print("\n1. 检查记忆文件...")
        workspace = Path.home() / ".bitwiseai"
        memory_file = workspace / "MEMORY.md"
        memory_dir = workspace / "memory"

        if memory_file.exists():
            content = memory_file.read_text(encoding='utf-8')
            print(f"✓ 长期记忆文件存在 ({len(content)} 字符)")
            print(f"  路径: {memory_file}")
        else:
            print(f"⚠️  长期记忆文件不存在")

        if memory_dir.exists():
            md_files = list(memory_dir.glob("*.md"))
            print(f"✓ 短期记忆目录存在 ({len(md_files)} 个文件)")
            print(f"  路径: {memory_dir}")
            for f in md_files[:3]:
                print(f"    - {f.name}")
            if len(md_files) > 3:
                print(f"    ... 还有 {len(md_files) - 3} 个")
        else:
            print(f"⚠️  短期记忆目录不存在")

        # 检查数据库
        print("\n2. 检查数据库...")
        db_file = workspace / "memory.db"
        if db_file.exists():
            size = db_file.stat().st_size
            print(f"✓ 数据库文件存在 ({size / 1024:.2f} KB)")
            print(f"  路径: {db_file}")
        else:
            print(f"⚠️  数据库文件不存在")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_10_performance():
    """测试 10: 性能测试"""
    print("\n" + "=" * 60)
    print("测试 10: 性能测试")
    print("=" * 60)

    try:
        import time
        ai = BitwiseAI()

        # 批量添加性能
        print("\n1. 批量添加性能...")
        start = time.time()
        for i in range(10):
            ai.add_text(f"测试文档 {i}: 这是用于性能测试的文档内容。")
        elapsed = time.time() - start
        print(f"✓ 添加 10 个文档耗时: {elapsed:.3f} 秒")
        print(f"  平均: {elapsed/10*1000:.1f} ms/文档")

        # 搜索性能
        print("\n2. 搜索性能...")
        start = time.time()
        for _ in range(10):
            ai.search_memory("测试文档", max_results=5)
        elapsed = time.time() - start
        print(f"✓ 10 次搜索耗时: {elapsed:.3f} 秒")
        print(f"  平均: {elapsed/10*1000:.1f} ms/次")

        # 获取统计
        print("\n3. 当前统计...")
        stats = ai.get_memory_stats()
        print(f"  总文件数: {stats['total_files']}")
        print(f"  总块数: {stats['total_chunks']}")
        print(f"  数据库大小: {stats['db_size_bytes'] / 1024:.2f} KB")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("BitwiseAI 记忆系统测试套件")
    print("=" * 60)
    print()

    tests = [
        ("记忆系统初始化", test_1_memory_initialization),
        ("短期记忆读写", test_2_short_term_memory),
        ("长期记忆读写", test_3_long_term_memory),
        ("混合搜索", test_4_hybrid_search),
        ("文档管理", test_5_document_management),
        ("技能索引", test_6_skill_indexing),
        ("记忆压缩", test_7_memory_compaction),
        ("RAG 集成", test_8_rag_integration),
        ("记忆持久化", test_9_memory_persistence),
        ("性能测试", test_10_performance),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            results.append((name, False))

    # 打印总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ 通过" if success else "❌ 失败"
        print(f"  {status}: {name}")

    print()
    print(f"总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")

    return passed == total


def main():
    """主函数"""
    import sys

    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        test_map = {
            "1": test_1_memory_initialization,
            "2": test_2_short_term_memory,
            "3": test_3_long_term_memory,
            "4": test_4_hybrid_search,
            "5": test_5_document_management,
            "6": test_6_skill_indexing,
            "7": test_7_memory_compaction,
            "8": test_8_rag_integration,
            "9": test_9_memory_persistence,
            "10": test_10_performance,
        }

        if test_name in test_map:
            success = test_map[test_name]()
            sys.exit(0 if success else 1)
        else:
            print(f"❌ 未知的测试编号: {test_name}")
            print("可用测试: 1-10")
            sys.exit(1)
    else:
        # 运行所有测试
        success = run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
