---
name: error-analyzer
description: 分析两个数据文件的误差，包括绝对误差、相对误差等，并生成独立的图表。支持目录批量比对。使用场景：当需要比较两个浮点数数据文件、分析模型输出误差或验证数据一致性时。
license: MIT
metadata:
  author: BitwiseAI
  version: "1.1.0"
---

# 误差分析工具

## 功能概述

本技能提供数据误差分析功能，支持：
- 计算两个文件的绝对误差和相对误差
- 生成独立的误差分析图表（每个分析一张图）
- 提供详细的统计信息（保存为 JSON 文件）
- 支持多种误差指标分析
- 支持目录批量比对（对目录下所有文件进行两两比对）

## 工具说明

### analyze_errors

分析两个数据文件的误差，生成独立的图表文件，并将详细结果保存为 JSON 文件。

**参数**:
- `file1_path` (string): 第一个数据文件路径（参考文件）
- `file2_path` (string): 第二个数据文件路径（对比文件）
- `output_dir` (string): 输出目录，用于保存生成的图表和 JSON（可选，默认为当前目录）

**返回**:
返回简洁的中文摘要，包含：
- 比较的行数
- 绝对误差的平均值和最大值（及所在行号）
- 相对误差的平均值和最大值（及所在行号）
- JSON 文件路径

**输出文件**:
- `absolute_error.png` — 绝对误差折线图
- `relative_error.png` — 相对误差折线图
- `error_distribution.png` — 误差分布直方图
- `error_analysis_{timestamp}.json` — 详细的误差统计信息（JSON 格式）

**示例**:
```python
analyze_errors(
    "input_data/onnx_runner_output_data.txt",
    "input_data/validator_dequantized_output_data.txt",
    "outputs/error_analysis"
)
```

### analyze_errors_in_directory

分析目录下所有文件的误差（两两比对）。

扫描目录下所有文本文件（.txt, .dat），对文件进行两两组合比对，为每对文件生成独立的输出子目录，并返回批量比对的汇总摘要。

**参数**:
- `directory_path` (string): 包含要比较文件的目录路径
- `outputs_dir` (string): 输出目录，用于保存结果（可选，默认为 'outputs'）

**返回**:
批量比对的汇总摘要，包含：
- 找到的文件数
- 比对的对数
- 成功/失败统计
- 每对文件的比对结果和输出目录

**输出结构**:
对于每对文件（file_a vs file_b），创建独立的子目录：
- `{outputs_dir}/{file_a_name}_vs_{file_b_name}/` — 包含该对的图表和 JSON 文件

**示例**:
```python
analyze_errors_in_directory("input_data", "outputs")
```### plot_absolute_error

生成绝对误差图表（独立图表）。

**参数**:
- `file1_path` (string): 第一个数据文件路径
- `file2_path` (string): 第二个数据文件路径
- `output_path` (string): 输出文件路径（可选）

**返回**:
生成的图表文件路径

### plot_relative_error

生成相对误差图表（独立图表）。

**参数**:
- `file1_path` (string): 第一个数据文件路径
- `file2_path` (string): 第二个数据文件路径
- `output_path` (string): 输出文件路径（可选）

**返回**:
生成的图表文件路径

### plot_error_distribution

生成误差分布直方图（独立图表）。

**参数**:
- `file1_path` (string): 第一个数据文件路径
- `file2_path` (string): 第二个数据文件路径
- `output_path` (string): 输出文件路径（可选）

**返回**:
生成的图表文件路径

## 使用场景

- 模型输出验证和对比
- 数据一致性检查
- 量化误差分析
- 数值精度评估
- 目录下多个文件的批量比对分析

## 注意事项

- 数据文件每行应包含一个浮点数
- 文件开头的元数据行（以#开头）会被自动忽略
- 如果两个文件行数不同，将只比较前 N 行（N为较小文件的行数）
- 详细误差统计信息保存在 JSON 文件中，不会打印到控制台
- 目录批量比对会对所有找到的文件进行两两组合比对