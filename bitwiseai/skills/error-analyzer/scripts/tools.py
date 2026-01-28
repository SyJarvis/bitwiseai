# -*- coding: utf-8 -*-
"""
误差分析工具

分析两个数据文件的误差，生成独立的图表
"""
import os
import json
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any
import warnings

warnings.filterwarnings("ignore")


def _read_float_file(filepath: str) -> List[float]:
    """
    读取按行存储的浮点数文件（忽略以#开头的元数据行）
    
    Args:
        filepath: 文件路径
        
    Returns:
        浮点数列表
    """
    values = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):  # 忽略空行和元数据行
                try:
                    values.append(float(line))
                except ValueError:
                    # 忽略无法解析的行
                    continue
    return values


def _calculate_errors(file1_path: str, file2_path: str) -> Tuple[List[float], List[float], List[float], List[float]]:
    """
    计算两个文件对应行的误差
    
    Args:
        file1_path: 第一个文件路径
        file2_path: 第二个文件路径
        
    Returns:
        (绝对误差列表, 相对误差列表, 值1列表, 值2列表)
    """
    values1 = _read_float_file(file1_path)
    values2 = _read_float_file(file2_path)
    
    # 确保两个文件的行数相同
    min_len = min(len(values1), len(values2))
    
    values1 = values1[:min_len]
    values2 = values2[:min_len]
    
    # 计算绝对误差
    absolute_errors = [abs(v1 - v2) for v1, v2 in zip(values1, values2)]
    
    # 计算相对误差（避免除零）
    relative_errors = []
    for v1, v2 in zip(values1, values2):
        if abs(v1) > 1e-10:  # 避免除零
            rel_err = abs((v1 - v2) / v1) * 100  # 百分比
            relative_errors.append(rel_err)
        else:
            relative_errors.append(abs(v1 - v2))  # 如果原值接近0，使用绝对误差
    
    return absolute_errors, relative_errors, values1, values2


def plot_absolute_error(file1_path: str, file2_path: str, output_path: str = None) -> str:
    """
    生成绝对误差图表（独立图表）
    
    Args:
        file1_path: 第一个数据文件路径
        file2_path: 第二个数据文件路径
        output_path: 输出文件路径（可选）
        
    Returns:
        生成的图表文件路径
    """
    absolute_errors, _, values1, values2 = _calculate_errors(file1_path, file2_path)
    
    if not output_path:
        output_path = 'absolute_error.png'
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
    os.makedirs(output_dir, exist_ok=True)
    
    line_numbers = list(range(1, len(absolute_errors) + 1))
    
    # 创建独立图表
    plt.figure(figsize=(12, 6))
    plt.plot(line_numbers, absolute_errors, 'b-', linewidth=0.8, alpha=0.7)
    plt.xlabel('Line Number', fontsize=12)
    plt.ylabel('Absolute Error', fontsize=12)
    plt.title('Absolute Error per Line (|value1 - value2|)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # 添加统计信息
    mean_abs_err = np.mean(absolute_errors)
    std_abs_err = np.std(absolute_errors)
    
    plt.axhline(y=mean_abs_err, color='r', linestyle='--', linewidth=1, 
                label=f'Mean Error: {mean_abs_err:.6f}')
    plt.axhline(y=mean_abs_err + std_abs_err, color='orange', linestyle=':', linewidth=1,
                label=f'Mean+Std: {mean_abs_err + std_abs_err:.6f}')
    plt.axhline(y=mean_abs_err - std_abs_err, color='orange', linestyle=':', linewidth=1,
                label=f'Mean-Std: {mean_abs_err - std_abs_err:.6f}')
    plt.legend()
    
    # plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_relative_error(file1_path: str, file2_path: str, output_path: str = None) -> str:
    """
    生成相对误差图表（独立图表）
    
    Args:
        file1_path: 第一个数据文件路径
        file2_path: 第二个数据文件路径
        output_path: 输出文件路径（可选）
        
    Returns:
        生成的图表文件路径
    """
    _, relative_errors, values1, values2 = _calculate_errors(file1_path, file2_path)
    
    if not output_path:
        output_path = 'relative_error.png'
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
    os.makedirs(output_dir, exist_ok=True)
    
    line_numbers = list(range(1, len(relative_errors) + 1))
    
    # 创建独立图表
    plt.figure(figsize=(12, 6))
    plt.plot(line_numbers, relative_errors, 'r-', linewidth=0.8, alpha=0.7)
    plt.xlabel('Line Number', fontsize=12)
    plt.ylabel('Relative Error (%)', fontsize=12)
    plt.title('Relative Error per Line (|value1 - value2| / |value1| × 100%)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # 添加统计信息
    mean_rel_err = np.mean(relative_errors)
    std_rel_err = np.std(relative_errors)
    
    plt.axhline(y=mean_rel_err, color='b', linestyle='--', linewidth=1,
                label=f'Mean Relative Error: {mean_rel_err:.4f}%')
    plt.axhline(y=mean_rel_err + std_rel_err, color='orange', linestyle=':', linewidth=1,
                label=f'Mean+Std: {mean_rel_err + std_rel_err:.4f}%')
    plt.axhline(y=mean_rel_err - std_rel_err, color='orange', linestyle=':', linewidth=1,
                label=f'Mean-Std: {mean_rel_err - std_rel_err:.4f}%')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_error_distribution(file1_path: str, file2_path: str, output_path: str = None) -> str:
    """
    生成误差分布直方图（独立图表）
    
    Args:
        file1_path: 第一个数据文件路径
        file2_path: 第二个数据文件路径
        output_path: 输出文件路径（可选）
        
    Returns:
        生成的图表文件路径
    """
    absolute_errors, relative_errors, _, _ = _calculate_errors(file1_path, file2_path)
    
    if not output_path:
        output_path = 'error_distribution.png'
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建独立图表（包含两个子图：绝对误差和相对误差的分布）
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 绝对误差分布
    ax1.hist(absolute_errors, bins=50, color='blue', alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Absolute Error', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title('Absolute Error Distribution', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 相对误差分布
    ax2.hist(relative_errors, bins=50, color='red', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Relative Error (%)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.set_title('Relative Error Distribution', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def analyze_errors(file1_path: str, file2_path: str, output_dir: str = None) -> str:
    """
    分析两个数据文件的误差，生成所有独立的图表文件
    
    Args:
        file1_path: 第一个数据文件路径（参考文件）
        file2_path: 第二个数据文件路径（对比文件）
        output_dir: 输出目录，用于保存生成的图表和JSON（可选，默认为当前目录）
        
    Returns:
        简洁的中文摘要，包含主要误差统计和JSON文件路径
    """
    from datetime import datetime
    
    if not output_dir:
        output_dir = '.'
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 计算误差
    absolute_errors, relative_errors, values1, values2 = _calculate_errors(file1_path, file2_path)
    
    # 生成所有图表
    abs_error_path = os.path.join(output_dir, 'absolute_error.png')
    rel_error_path = os.path.join(output_dir, 'relative_error.png')
    dist_path = os.path.join(output_dir, 'error_distribution.png')
    
    plot_absolute_error(file1_path, file2_path, abs_error_path)
    plot_relative_error(file1_path, file2_path, rel_error_path)
    plot_error_distribution(file1_path, file2_path, dist_path)
    
    # 计算统计信息
    max_abs_err = max(absolute_errors)
    min_abs_err = min(absolute_errors)
    mean_abs_err = np.mean(absolute_errors)
    std_abs_err = np.std(absolute_errors)
    max_abs_line = absolute_errors.index(max_abs_err) + 1
    
    max_rel_err = max(relative_errors)
    min_rel_err = min(relative_errors)
    mean_rel_err = np.mean(relative_errors)
    std_rel_err = np.std(relative_errors)
    max_rel_line = relative_errors.index(max_rel_err) + 1
    
    # 前10个最大误差的行
    sorted_indices = sorted(range(len(absolute_errors)), 
                           key=lambda i: absolute_errors[i], reverse=True)
    top_10_errors = []
    for idx in sorted_indices[:10]:
        top_10_errors.append({
            "line_number": idx + 1,
            "absolute_error": absolute_errors[idx],
            "relative_error": relative_errors[idx],
            "value1": values1[idx],
            "value2": values2[idx]
        })
    
    # 构建详细结果
    result = {
        "file1_path": file1_path,
        "file2_path": file2_path,
        "total_lines": len(absolute_errors),
        "absolute_error": {
            "max": float(max_abs_err),
            "min": float(min_abs_err),
            "mean": float(mean_abs_err),
            "std": float(std_abs_err),
            "max_line": max_abs_line
        },
        "relative_error": {
            "max": float(max_rel_err),
            "min": float(min_rel_err),
            "mean": float(mean_rel_err),
            "std": float(std_rel_err),
            "max_line": max_rel_line
        },
        "generated_charts": [
            abs_error_path,
            rel_error_path,
            dist_path
        ],
        "top_10_errors": top_10_errors,
        "timestamp": datetime.now().isoformat()
    }
    
    # 保存 JSON 到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(output_dir, f'error_analysis_{timestamp}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # 返回简洁的中文摘要
    summary = f"误差分析完成: 比较了 {len(absolute_errors)} 行数据\n"
    summary += f"绝对误差: 平均={mean_abs_err:.6g}, 最大={max_abs_err:.6g} (第{max_abs_line}行)\n"
    summary += f"相对误差: 平均={mean_rel_err:.4f}%, 最大={max_rel_err:.4f}% (第{max_rel_line}行)\n"
    summary += f"详细结果已保存到: {json_path}"
    
    return summary


def analyze_errors_in_directory(directory_path: str, outputs_dir: str = 'outputs') -> str:
    """
    分析目录下所有文件的误差（两两比对）
    
    - 扫描目录下所有文本文件（.txt, .dat）
    - 对文件进行两两组合比对
    - 为每对文件生成独立的输出子目录
    - 返回批量比对的汇总摘要
    
    Args:
        directory_path: 包含要比较文件的目录路径
        outputs_dir: 输出目录，用于保存结果（可选，默认为 'outputs'）
        
    Returns:
        批量比对的汇总摘要
    """
    from itertools import combinations
    
    dir_path = Path(directory_path)
    if not dir_path.exists() or not dir_path.is_dir():
        return f"错误: 目录不存在: {directory_path}"
    
    # 查找目录下所有文本文件
    txt_files = sorted([f for f in dir_path.iterdir() 
                       if f.is_file() and f.suffix.lower() in ['.txt', '.dat']])
    
    if len(txt_files) < 2:
        return f"错误: 目录中至少需要2个文件，找到 {len(txt_files)} 个文件"
    
    # 创建基础输出目录
    base_out_dir = Path(outputs_dir)
    base_out_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    successful = 0
    failed = 0
    
    # 对文件进行两两比对
    for file_a, file_b in combinations(txt_files, 2):
        file_a_name = file_a.stem
        file_b_name = file_b.stem
        
        # 为每对文件创建独立的输出子目录
        pair_dir = base_out_dir / f"{file_a_name}_vs_{file_b_name}"
        pair_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 使用 analyze_errors 进行比对
            result_summary = analyze_errors(str(file_a), str(file_b), str(pair_dir))
            
            results.append({
                "file_a": file_a_name,
                "file_b": file_b_name,
                "output_dir": str(pair_dir),
                "summary": result_summary,
                "status": "success"
            })
            successful += 1
        except Exception as e:
            results.append({
                "file_a": file_a_name,
                "file_b": file_b_name,
                "status": "failed",
                "error": str(e)
            })
            failed += 1
    
    # 生成汇总摘要
    summary_lines = []
    summary_lines.append(f"目录批量比对完成: {directory_path}")
    summary_lines.append(f"找到文件数: {len(txt_files)}")
    summary_lines.append(f"比对对数: {len(results)}")
    summary_lines.append(f"成功: {successful}, 失败: {failed}")
    summary_lines.append("")
    summary_lines.append("比对结果:")
    
    for result in results:
        if result["status"] == "success":
            summary_lines.append(f"  ✓ {result['file_a']} vs {result['file_b']}: {result['output_dir']}")
        else:
            summary_lines.append(f"  ✗ {result['file_a']} vs {result['file_b']}: {result.get('error', '未知错误')}")
    
    summary = "\n".join(summary_lines)
    return summary