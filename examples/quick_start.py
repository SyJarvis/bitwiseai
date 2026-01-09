# -*- coding: utf-8 -*-
"""
BitwiseAI 快速开始示例

展示 BitwiseAI 的核心功能
"""
from dotenv import load_dotenv
load_dotenv()

from bitwiseai import BitwiseAI, AnalysisTask, AnalysisResult

print("=" * 60)
print("BitwiseAI - 快速开始")
print("=" * 60)
print()

# ========== 1. 初始化 ==========
print("1. 初始化 BitwiseAI")
print("-" * 40)
ai = BitwiseAI()
print()

# ========== 2. LLM 对话 ==========
print("2. LLM 对话（纯 LLM 模式）")
print("-" * 40)
response = ai.chat("你好，请用一句话介绍你自己", use_rag=False)
print(f"回答: {response}")
print()

# ========== 3. 注册工具 ==========
print("3. 注册自定义工具")
print("-" * 40)

def hex_to_int(hex_str: str) -> int:
    """十六进制转整数"""
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return int(hex_str, 16)

ai.register_tool(hex_to_int, description="十六进制转整数")
print(f"  已注册工具: {ai.list_tools()}")
print()

# 使用工具
result = ai.invoke_tool("hex_to_int", "0xFF")
print(f"  工具调用结果: hex_to_int('0xFF') = {result}")
print()

# ========== 4. 自定义分析任务 ==========
print("4. 创建并执行自定义任务")
print("-" * 40)

class QuickAnalysisTask(AnalysisTask):
    """快速分析任务示例"""
    
    def __init__(self):
        super().__init__(
            name="QuickAnalysis",
            description="快速分析示例任务"
        )
    
    def analyze(self, context, parsed_data):
        """执行分析"""
        results = []
        
        # 示例1: 使用工具
        hex_val = "0x8D17"
        decimal_val = context.invoke_tool("hex_to_int", hex_val)
        
        results.append(AnalysisResult(
            status="pass",
            message=f"工具调用: {hex_val} = {decimal_val}",
            data={"hex": hex_val, "decimal": decimal_val}
        ))
        
        # 示例2: 使用 LLM 分析
        llm_response = context.analyze_with_llm(
            "用一句话解释什么是 PE 寄存器",
            use_rag=False
        )
        
        results.append(AnalysisResult(
            status="pass",
            message="LLM 分析完成",
            data={"llm_response": llm_response}
        ))
        
        return results

# 注册任务
task = QuickAnalysisTask()
ai.register_task(task)
print(f"  已注册任务: {ai.list_tasks()}")
print()

# 执行任务
print("  执行任务...")
results = ai.execute_task(task)
print()

# 查看结果
print("  任务结果:")
for i, result in enumerate(results, 1):
    print(f"    {i}. [{result.status.upper()}] {result.message}")
    if result.data and "llm_response" in result.data:
        print(f"       LLM: {result.data['llm_response'][:100]}...")
print()

# ========== 5. 生成报告 ==========
print("5. 生成分析报告")
print("-" * 40)

report = ai.generate_report(format="text")
print(report)

print()
print("=" * 60)
print("快速开始完成！")
print("=" * 60)
print()
print("下一步:")
print("  - 查看 examples/custom_task_example.py 了解自定义任务")
print("  - 查看 examples/custom_tool_example.py 了解工具系统")
print("  - 查看 examples/pe_instruction_verification.py 了解完整案例")
print("  - 阅读 docs/ 目录下的文档获取更多信息")

