# -*- coding: utf-8 -*-
"""
BitwiseAI 文档导出示例

展示如何导出向量数据库中的文档：
1. 加载文档到向量数据库
2. 导出文档为 Markdown 格式
3. 查看导出结果
"""

import os
import shutil
from bitwiseai import BitwiseAI


def main():
    """文档导出示例"""
    print("=" * 60)
    print("BitwiseAI 文档导出示例")
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
    
    # 2. 准备示例文档
    print("2. 准备示例文档")
    print("-" * 60)
    docs_dir = "/tmp/bitwiseai_export_docs"
    output_dir = "/tmp/bitwiseai_export_output"
    
    # 清理旧目录
    if os.path.exists(docs_dir):
        shutil.rmtree(docs_dir)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    os.makedirs(docs_dir, exist_ok=True)
    
    # 创建示例文档
    doc1_path = os.path.join(docs_dir, "instruction_set.md")
    with open(doc1_path, 'w', encoding='utf-8') as f:
        f.write("""# 指令集架构说明

## 概述

本文档描述了处理单元的指令集架构。

## 算术指令

### ADD 指令

ADD 指令用于执行加法运算。

**语法**: `ADD dest, src1, src2`

**参数**:
- dest: 目标寄存器
- src1: 源寄存器1
- src2: 源寄存器2

**示例**:
```assembly
ADD R0, R1, R2  # R0 = R1 + R2
```

### SUB 指令

SUB 指令用于执行减法运算。

**语法**: `SUB dest, src1, src2`

**示例**:
```assembly
SUB R0, R1, R2  # R0 = R1 - R2
```

## 逻辑指令

### AND 指令

AND 指令执行按位与运算。

**语法**: `AND dest, src1, src2`

**示例**:
```assembly
AND R0, R1, R2  # R0 = R1 & R2
```
""")
    
    doc2_path = os.path.join(docs_dir, "register_reference.md")
    with open(doc2_path, 'w', encoding='utf-8') as f:
        f.write("""# 寄存器参考手册

## 通用寄存器

### R0 - R15

通用寄存器，用于存储临时数据和计算结果。

**特性**:
- 32 位宽度
- 可读写
- 支持所有算术和逻辑运算

## 特殊寄存器

### PC (Program Counter)

程序计数器，存储当前执行的指令地址。

**特性**:
- 只读（由硬件自动更新）
- 32 位宽度

### SP (Stack Pointer)

栈指针，指向当前栈顶位置。

**特性**:
- 可读写
- 32 位宽度
- 用于函数调用和局部变量存储
""")
    
    print(f"✓ 示例文档已创建在: {docs_dir}")
    print(f"  - {os.path.basename(doc1_path)}")
    print(f"  - {os.path.basename(doc2_path)}\n")
    
    # 3. 加载文档到向量数据库
    print("3. 加载文档到向量数据库")
    print("-" * 60)
    stats = ai.load_documents(docs_dir, skip_duplicates=True)
    print(f"✓ 文档加载完成:")
    print(f"  - 总片段数: {stats.get('total', 0)}")
    print(f"  - 插入片段数: {stats.get('inserted', 0)}")
    print(f"  - 跳过重复数: {stats.get('skipped', 0)}\n")
    
    # 4. 查看文档统计信息
    print("4. 查看文档统计信息")
    print("-" * 60)
    stats = ai.rag_engine.get_document_stats()
    print("文档统计:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    print()
    
    # 5. 导出文档
    print("5. 导出文档为 Markdown 格式")
    print("-" * 60)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        exported_count = ai.rag_engine.export_documents(
            output_dir,
            format="separate_md"
        )
        print(f"✓ 导出了 {exported_count} 个文档文件到: {output_dir}\n")
    except Exception as e:
        print(f"❌ 导出失败: {e}\n")
        return
    
    # 6. 查看导出结果
    print("6. 查看导出结果")
    print("-" * 60)
    if os.path.exists(output_dir):
        exported_files = [f for f in os.listdir(output_dir) if f.endswith('.md')]
        print(f"导出的文件 ({len(exported_files)} 个):")
        for file in sorted(exported_files):
            file_path = os.path.join(output_dir, file)
            size = os.path.getsize(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            print(f"  - {file} ({size} bytes, {lines} 行)")
            
            # 显示文件前几行
            with open(file_path, 'r', encoding='utf-8') as f:
                preview = ''.join(f.readlines()[:5])
                print(f"    预览: {preview[:80]}...")
        print()
    
    # 7. 验证导出内容
    print("7. 验证导出内容")
    print("-" * 60)
    # 读取一个导出的文件并显示部分内容
    if exported_files:
        sample_file = os.path.join(output_dir, exported_files[0])
        print(f"示例文件: {os.path.basename(sample_file)}")
        print("-" * 40)
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 显示前 500 个字符
            print(content[:500])
            if len(content) > 500:
                print("...")
        print()
    
    # 8. 清理临时文件（可选）
    print("8. 清理临时文件")
    print("-" * 60)
    cleanup = input("是否清理临时文件? (y/N): ").strip().lower()
    if cleanup == 'y':
        if os.path.exists(docs_dir):
            shutil.rmtree(docs_dir)
            print(f"✓ 已清理: {docs_dir}")
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print(f"✓ 已清理: {output_dir}")
    else:
        print(f"保留文件:")
        print(f"  - 文档目录: {docs_dir}")
        print(f"  - 导出目录: {output_dir}")
    print()
    
    print("=" * 60)
    print("文档导出示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
