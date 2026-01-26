---
name: error-analyzer
description: 分析两个数据文件的误差，包括绝对误差、相对误差等，并生成独立的图表。使用场景：当需要比较两个浮点数数据文件、分析模型输出误差或验证数据一致性时。
license: MIT
metadata:
  author: BitwiseAI
  version: "1.0.0"
---

# 误差分析工具

## 功能概述

本技能提供数据误差分析功能，支持：
- 计算两个文件的绝对误差和相对误差
- 生成独立的误差分析图表（每个分析一张图）
- 提供详细的统计信息
- 支持多种误差指标分析

## 工具说明

### analyze_errors

分析两个数据文件的误差，生成独立的图表文件。

**参数**:
- `file1_path` (string): 第一个数据文件路径（参考文件）
- `file2_path` (string): 第二个数据文件路径（对比文件）
- `output_dir` (string): 输出目录，用于保存生成的图表（可选，默认为当前目录）

**返回**:
返回 JSON 字符串，包含：
- 统计信息（最大值、最小值、平均值、标准差）
- 生成的图表文件路径列表
- 前10个最大误差的行号

**示例**:
analyze_errors(
    "input_data/onnx_runner_output_data.txt",
    "input_data/validator_dequantized_output_data.txt",
    "outputs/error_analysis"
)### plot_absolute_error

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

## 注意事项

- 数据文件每行应包含一个浮点数
- 文件开头的元数据行（以#开头）会被自动忽略
- 如果两个文件行数不同，将只比较前 N 行（N为较小文件的行数）