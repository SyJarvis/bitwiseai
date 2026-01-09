# -*- coding: utf-8 -*-
"""
PE 指令验证完整示例

展示如何使用 BitwiseAI 验证 PE 寄存器指令的计算正确性
"""
from dotenv import load_dotenv
load_dotenv()

from bitwiseai import BitwiseAI
from bitwiseai.interfaces import AnalysisTask, AnalysisResult, LogParserInterface, VerifierInterface
from bitwiseai.log_parser import LogParser, InstructionType
from bitwiseai.verifier import InstructionVerifier
from typing import List, Any


class PEInstructionAnalysisTask(AnalysisTask):
    """PE 指令分析任务"""
    
    def __init__(self):
        # 使用内置的解析器和验证器
        parser = LogParser()
        verifier = InstructionVerifier()
        
        super().__init__(
            name="PE_Instruction_Verification",
            description="验证 PE 寄存器指令的计算正确性",
            parser=parser,
            verifier=verifier
        )
    
    def analyze(self, context: BitwiseAI, parsed_data) -> List[AnalysisResult]:
        """自定义分析逻辑"""
        results = []
        
        if not parsed_data:
            return results
        
        # 使用解析器解析日志
        if isinstance(self.parser, LogParser):
            instructions = parsed_data if isinstance(parsed_data, list) else self.parser.instructions
            
            print(f"  解析到 {len(instructions)} 条指令")
            
            # 统计指令类型
            type_counts = {}
            for inst in instructions:
                type_counts[inst.instruction_type.value] = type_counts.get(inst.instruction_type.value, 0) + 1
            
            print(f"  指令类型分布: {type_counts}")
            
            # 验证每条指令
            verify_results = []
            if isinstance(self.verifier, InstructionVerifier):
                verify_results = self.verifier.verify_all(instructions)
            
            # 转换为 AnalysisResult
            for vr in verify_results:
                ar = AnalysisResult(
                    status=vr.status.value.lower(),
                    message=str(vr),
                    data={
                        "pe_id": vr.instruction.pe_id,
                        "instruction_type": vr.instruction.instruction_type.value
                    }
                )
                results.append(ar)
            
            # 生成摘要
            if isinstance(self.verifier, InstructionVerifier):
                summary = self.verifier.get_summary()
                results.append(AnalysisResult(
                    status="pass",
                    message="验证摘要",
                    data=summary
                ))
        
        return results


def main():
    print("=" * 60)
    print("BitwiseAI - PE 指令验证示例")
    print("=" * 60)
    print()
    
    # 初始化 BitwiseAI
    ai = BitwiseAI()
    print()
    
    # 创建示例 PE 日志（基于用户提供的格式）
    sample_pe_log = """[AFTER] PE[0-1] 寄存器:
    PE[0]:
      MUL寄存器映射: rs0=R0(x-zp), rs1=R3(q_b), rs2=R2(n_bx), rd0=R3, rd1=R7, func_sel=2
      rs0(x-z_p):     0x8D172E83 = [-115,  23,  46, -125] <- R0
      rs1(q_b):       0x0015FFCE = [    21,    -50] <- R3
      rs2(n_bx):      0x10101010 = [ 16,  16,  16,  16] <- R2
      rd0(结果):      0x0015FFCE = [    21,    -50] -> R3
      rd1(结果2):     0x00000000 = [     0,      0] -> R7
    PE[1]:
      MUL寄存器映射: rs0=R0(x-zp), rs1=R3(q_b), rs2=R2(n_bx), rd0=R3, rd1=R7, func_sel=2
      rs0(x-z_p):     0xAFC1B868 = [-81, -63, -72, 104] <- R0
      rs1(q_b):       0xFFDE002B = [   -34,     43] <- R3
      rs2(n_bx):      0x10101010 = [ 16,  16,  16,  16] <- R2
      rd0(结果):      0xFFDE002B = [   -34,     43] -> R3
      rd1(结果2):     0x00000000 = [     0,      0] -> R7

  [AFTER] PE[0-1] 寄存器:
    PE[0]:
      SHIFT寄存器映射: rs0=R0, rd0=R0, 方向=右移, 无符号, 不饱和, 舍入=floor, 移位宽度=16, 位宽=32bit×1
      rs0(输入):      0x00008D17 =       36119 <- R0
      rd0(结果):      0x00008D17 =       36119 -> R0
    PE[1]:
      SHIFT寄存器映射: rs0=R0, rd0=R0, 方向=右移, 无符号, 不饱和, 舍入=floor, 移位宽度=16, 位宽=32bit×1
      rs0(输入):      0x0000AFC1 =       44993 <- R0
      rd0(结果):      0x0000AFC1 =       44993 -> R0
"""
    
    # 保存示例日志
    log_file = "/tmp/pe_test_log.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(sample_pe_log)
    
    print(f"创建示例日志文件: {log_file}")
    print()
    
    # 加载日志文件
    ai.load_log_file(log_file)
    print()
    
    # 注册 PE 指令分析任务
    task = PEInstructionAnalysisTask()
    ai.register_task(task)
    print()
    
    # 执行任务
    print("执行 PE 指令验证...")
    print("-" * 60)
    results = ai.execute_task(task)
    print()
    
    # 打印结果
    print("验证结果:")
    print("-" * 60)
    
    pass_count = 0
    fail_count = 0
    
    for result in results:
        if result.status == "pass":
            pass_count += 1
        elif result.status == "fail":
            fail_count += 1
            print(f"[FAIL] {result.message}")
    
    print()
    print(f"总结: 通过 {pass_count} 条, 失败 {fail_count} 条")
    print()
    
    # 使用 LLM 询问关于日志的问题
    print("=" * 60)
    print("使用 LLM 分析日志...")
    print("=" * 60)
    
    question = "这个日志中的 MUL 指令 func_sel=2 是什么模式？"
    print(f"问题: {question}")
    print()
    
    answer = ai.ask_about_log(question)
    print(f"回答: {answer}")
    print()
    
    # 生成报告
    print("=" * 60)
    print("生成验证报告...")
    print("=" * 60)
    report = ai.generate_report(format="text")
    print(report)


if __name__ == "__main__":
    main()

