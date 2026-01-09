# -*- coding: utf-8 -*-
"""
自定义任务示例

展示如何定义自己的日志分析任务并嵌入到 BitwiseAI 中
"""
from dotenv import load_dotenv
load_dotenv()

from bitwiseai import BitwiseAI
from bitwiseai.interfaces import AnalysisTask, AnalysisResult


class MyLogAnalysisTask(AnalysisTask):
    """
    自定义日志分析任务示例
    
    这个任务演示如何：
    1. 读取日志文件
    2. 执行自定义分析逻辑
    3. 使用 BitwiseAI 的 LLM 进行辅助分析
    4. 返回分析结果
    """
    
    def __init__(self):
        super().__init__(
            name="MyLogAnalysis",
            description="分析日志文件中的错误和警告"
        )
    
    def analyze(self, context: BitwiseAI, parsed_data):
        """执行自定义分析逻辑"""
        results = []
        
        # 步骤1: 读取日志文件
        if not context.log_file_path:
            results.append(AnalysisResult(
                status="error",
                message="未加载日志文件"
            ))
            return results
        
        with open(context.log_file_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 步骤2: 简单的模式匹配分析
        error_count = log_content.count("ERROR")
        warning_count = log_content.count("WARNING")
        
        results.append(AnalysisResult(
            status="pass",
            message=f"发现 {error_count} 个错误和 {warning_count} 个警告",
            data={
                "error_count": error_count,
                "warning_count": warning_count
            }
        ))
        
        # 步骤3: 如果发现错误，使用 LLM 进行深入分析
        if error_count > 0:
            # 提取错误行
            error_lines = [line for line in log_content.split('\n') if 'ERROR' in line]
            sample_errors = '\n'.join(error_lines[:5])  # 取前5个错误
            
            # 使用 LLM 分析
            analysis_prompt = f"""请分析以下错误日志，找出可能的问题原因：

{sample_errors}

请提供：
1. 错误类型分类
2. 可能的根本原因
3. 建议的解决方案
"""
            llm_analysis = context.analyze_with_llm(analysis_prompt, use_rag=False)
            
            results.append(AnalysisResult(
                status="warning",
                message="LLM 错误分析",
                data={"llm_analysis": llm_analysis}
            ))
        
        return results


def main():
    print("=" * 60)
    print("BitwiseAI - 自定义任务示例")
    print("=" * 60)
    print()
    
    # 初始化 BitwiseAI
    ai = BitwiseAI()
    print()
    
    # 创建示例日志文件（用于演示）
    sample_log = """
2024-01-09 10:00:01 INFO  系统启动
2024-01-09 10:00:02 INFO  初始化模块A
2024-01-09 10:00:03 ERROR 模块A初始化失败: 连接超时
2024-01-09 10:00:04 WARNING 尝试重新连接...
2024-01-09 10:00:05 ERROR 重连失败: 认证错误
2024-01-09 10:00:06 INFO  切换到备用模块B
2024-01-09 10:00:07 INFO  系统正常运行
"""
    
    # 保存示例日志
    log_file = "/tmp/test_log.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(sample_log)
    
    # 加载日志文件
    ai.load_log_file(log_file)
    print()
    
    # 注册自定义任务
    task = MyLogAnalysisTask()
    ai.register_task(task)
    print()
    
    # 执行任务
    results = ai.execute_task(task)
    print()
    
    # 打印结果
    print("分析结果:")
    print("-" * 40)
    for i, result in enumerate(results, 1):
        print(f"{i}. [{result.status.upper()}] {result.message}")
        if result.data:
            for key, value in result.data.items():
                print(f"   {key}: {value}")
        print()
    
    # 生成报告
    print("=" * 60)
    print("生成报告...")
    print("=" * 60)
    report = ai.generate_report(format="markdown")
    print(report)


if __name__ == "__main__":
    main()

