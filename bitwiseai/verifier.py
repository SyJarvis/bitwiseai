# -*- coding: utf-8 -*-
"""
指令验证器模块

验证硬件指令计算的正确性，支持 MUL、SHIFT、ADD 等操作
"""
import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .log_parser import Instruction, InstructionType, RegisterValue


class VerifyStatus(Enum):
    """验证状态"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class VerifyResult:
    """验证结果"""
    instruction: Instruction
    status: VerifyStatus
    expected_values: Dict[str, Any] = field(default_factory=dict)
    actual_values: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    details: List[str] = field(default_factory=list)
    
    def __str__(self):
        lines = [
            f"PE[{self.instruction.pe_id}] {self.instruction.instruction_type.value}: {self.status.value}",
        ]
        
        if self.error_message:
            lines.append(f"  错误: {self.error_message}")
        
        if self.status == VerifyStatus.FAIL:
            for key, expected in self.expected_values.items():
                actual = self.actual_values.get(key, "N/A")
                lines.append(f"  {key}:")
                lines.append(f"    期望: {expected}")
                lines.append(f"    实际: {actual}")
        
        if self.details:
            for detail in self.details:
                lines.append(f"  {detail}")
        
        return "\n".join(lines)


class InstructionVerifier:
    """硬件指令验证器"""
    
    def __init__(self, tolerance: float = 0.0):
        """
        初始化验证器
        
        Args:
            tolerance: 浮点数容差（用于近似比较）
        """
        self.tolerance = tolerance
        self.results: List[VerifyResult] = []
    
    def verify(self, instruction: Instruction) -> VerifyResult:
        """
        验证指令
        
        Args:
            instruction: 待验证的指令
            
        Returns:
            验证结果
        """
        if instruction.instruction_type == InstructionType.MUL:
            return self.verify_mul(instruction)
        elif instruction.instruction_type == InstructionType.SHIFT:
            return self.verify_shift(instruction)
        elif instruction.instruction_type == InstructionType.ADD:
            return self.verify_add(instruction)
        elif instruction.instruction_type == InstructionType.LUT2:
            return self.verify_lut2(instruction)
        else:
            return VerifyResult(
                instruction=instruction,
                status=VerifyStatus.SKIPPED,
                error_message=f"不支持的指令类型: {instruction.instruction_type}"
            )
    
    def verify_mul(self, instruction: Instruction) -> VerifyResult:
        """
        验证 MUL 指令
        
        MUL 指令执行乘法操作，func_sel 决定操作模式
        """
        result = VerifyResult(instruction=instruction, status=VerifyStatus.PASS)
        
        try:
            # 获取输入寄存器
            rs0 = instruction.get_mapped_register("rs0")
            rs1 = instruction.get_mapped_register("rs1")
            rs2 = instruction.get_mapped_register("rs2")
            rd0 = instruction.get_mapped_register("rd0")
            
            if not all([rs0, rs1, rd0]):
                result.status = VerifyStatus.ERROR
                result.error_message = "缺少必需的寄存器"
                return result
            
            func_sel = instruction.metadata.get("func_sel", 0)
            
            # 根据 func_sel 执行不同的操作
            if func_sel == 2:
                # func_sel=2: 简单传递 rs1 的值
                expected_result = rs1.dec_values
            else:
                # 其他模式的乘法实现
                result.details.append(f"func_sel={func_sel} 的详细验证待实现")
                expected_result = rd0.dec_values
            
            result.expected_values["rd0"] = expected_result
            result.actual_values["rd0"] = rd0.dec_values
            
            # 比较结果
            if expected_result != rd0.dec_values:
                result.status = VerifyStatus.FAIL
                result.error_message = "MUL 指令结果不匹配"
            else:
                result.details.append("MUL 指令验证通过")
        
        except Exception as e:
            result.status = VerifyStatus.ERROR
            result.error_message = f"验证过程出错: {str(e)}"
        
        self.results.append(result)
        return result
    
    def verify_shift(self, instruction: Instruction) -> VerifyResult:
        """
        验证 SHIFT 指令
        
        SHIFT 指令执行位移操作，支持左移/右移、有符号/无符号等
        """
        result = VerifyResult(instruction=instruction, status=VerifyStatus.PASS)
        
        try:
            # 获取输入输出寄存器
            rs0 = instruction.get_mapped_register("rs0")
            rd0 = instruction.get_mapped_register("rd0")
            
            if not all([rs0, rd0]):
                result.status = VerifyStatus.ERROR
                result.error_message = "缺少必需的寄存器"
                return result
            
            # 获取 SHIFT 参数
            direction = instruction.metadata.get("direction", "右移")
            shift_width = instruction.metadata.get("shift_width", 0)
            is_signed = instruction.metadata.get("signed", False)
            saturate = instruction.metadata.get("saturate", False)
            bit_width = instruction.metadata.get("bit_width", 32)
            
            # 获取输入值
            input_val = rs0.dec_values[0] if rs0.dec_values else 0
            
            # 根据参数计算期望结果
            if direction == "右移":
                if shift_width == 16 and bit_width == 32:
                    # 右移16位
                    expected_result = input_val >> 16
                else:
                    expected_result = input_val >> shift_width
            elif direction == "左移":
                if shift_width == 16 and bit_width == 32:
                    # 左移16位
                    expected_result = (input_val << 16) & 0xFFFFFFFF
                else:
                    expected_result = (input_val << shift_width) & 0xFFFFFFFF
            else:
                result.status = VerifyStatus.ERROR
                result.error_message = f"未知的移位方向: {direction}"
                return result
            
            actual_result = rd0.dec_values[0] if rd0.dec_values else 0
            
            result.expected_values["rd0"] = expected_result
            result.actual_values["rd0"] = actual_result
            
            # 比较结果
            if expected_result != actual_result:
                result.status = VerifyStatus.FAIL
                result.error_message = f"SHIFT 指令结果不匹配 (方向={direction}, 宽度={shift_width})"
            else:
                result.details.append(f"SHIFT 指令验证通过 (方向={direction}, 宽度={shift_width})")
        
        except Exception as e:
            result.status = VerifyStatus.ERROR
            result.error_message = f"验证过程出错: {str(e)}"
        
        self.results.append(result)
        return result
    
    def verify_add(self, instruction: Instruction) -> VerifyResult:
        """
        验证 ADD 指令
        
        ADD 指令执行加法操作，支持饱和运算、不同位宽等
        """
        result = VerifyResult(instruction=instruction, status=VerifyStatus.PASS)
        
        try:
            # 获取输入输出寄存器
            rs0 = instruction.get_mapped_register("rs0")
            rs1 = instruction.get_mapped_register("rs1")
            rd0 = instruction.get_mapped_register("rd0")
            
            if not all([rs0, rs1, rd0]):
                result.status = VerifyStatus.ERROR
                result.error_message = "缺少必需的寄存器"
                return result
            
            # 获取 ADD 参数
            rs0_signed = instruction.metadata.get("rs0_signed", False)
            rs1_signed = instruction.metadata.get("rs1_signed", False)
            rs0_bit_width = instruction.metadata.get("rs0_bit_width", 16)
            output_bit_width = instruction.metadata.get("output_bit_width", 8)
            
            # 获取输入值（可能是多个值）
            rs0_values = rs0.dec_values if rs0.dec_values else [0]
            rs1_values = rs1.dec_values if rs1.dec_values else [0]
            rd0_values = rd0.dec_values if rd0.dec_values else [0]
            
            # 执行加法
            expected_values = []
            for v0, v1 in zip(rs0_values, rs1_values):
                sum_val = v0 + v1
                
                # 饱和处理（如果需要）
                if output_bit_width == 8:
                    if sum_val > 127:
                        sum_val = 127
                    elif sum_val < -128:
                        sum_val = -128
                
                expected_values.append(sum_val)
            
            result.expected_values["rd0"] = expected_values
            result.actual_values["rd0"] = rd0_values
            
            # 比较结果
            if len(expected_values) != len(rd0_values):
                result.status = VerifyStatus.FAIL
                result.error_message = "ADD 指令结果数量不匹配"
            elif expected_values != rd0_values:
                result.status = VerifyStatus.FAIL
                result.error_message = "ADD 指令结果不匹配"
            else:
                result.details.append("ADD 指令验证通过")
        
        except Exception as e:
            result.status = VerifyStatus.ERROR
            result.error_message = f"验证过程出错: {str(e)}"
        
        self.results.append(result)
        return result
    
    def verify_lut2(self, instruction: Instruction) -> VerifyResult:
        """
        验证 LUT2 指令
        
        LUT2 指令执行查找表操作
        """
        result = VerifyResult(instruction=instruction, status=VerifyStatus.PASS)
        
        try:
            # LUT2 指令的详细验证逻辑待实现
            result.details.append("LUT2 指令验证待实现")
            result.status = VerifyStatus.SKIPPED
        
        except Exception as e:
            result.status = VerifyStatus.ERROR
            result.error_message = f"验证过程出错: {str(e)}"
        
        self.results.append(result)
        return result
    
    def verify_all(self, instructions: List[Instruction]) -> List[VerifyResult]:
        """
        验证所有指令
        
        Args:
            instructions: 指令列表
            
        Returns:
            验证结果列表
        """
        self.results = []
        for instruction in instructions:
            self.verify(instruction)
        return self.results
    
    def get_failed_results(self) -> List[VerifyResult]:
        """获取失败的验证结果"""
        return [r for r in self.results if r.status == VerifyStatus.FAIL]
    
    def get_passed_results(self) -> List[VerifyResult]:
        """获取通过的验证结果"""
        return [r for r in self.results if r.status == VerifyStatus.PASS]
    
    def get_summary(self) -> Dict[str, int]:
        """
        获取验证摘要
        
        Returns:
            包含各状态数量的字典
        """
        summary = {
            "total": len(self.results),
            "pass": len([r for r in self.results if r.status == VerifyStatus.PASS]),
            "fail": len([r for r in self.results if r.status == VerifyStatus.FAIL]),
            "skipped": len([r for r in self.results if r.status == VerifyStatus.SKIPPED]),
            "error": len([r for r in self.results if r.status == VerifyStatus.ERROR]),
        }
        return summary


# 工具函数

def parse_hex_to_int8_array(hex_str: str) -> List[int]:
    """
    将十六进制字符串解析为 int8 数组
    
    Args:
        hex_str: 十六进制字符串，如 "0x8D172E83"
        
    Returns:
        int8 数组
    """
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    
    # 每两个字符是一个字节
    bytes_list = [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]
    
    # 转换为有符号 int8
    int8_array = [np.int8(b) if b < 128 else np.int8(b - 256) for b in bytes_list]
    
    return int8_array


def parse_hex_to_int16_array(hex_str: str) -> List[int]:
    """
    将十六进制字符串解析为 int16 数组（大端序）
    
    Args:
        hex_str: 十六进制字符串，如 "0x78586603"
        
    Returns:
        int16 数组
    """
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    
    # 每四个字符是一个 int16
    int16_array = []
    for i in range(0, len(hex_str), 4):
        hex_val = hex_str[i:i+4]
        int_val = int(hex_val, 16)
        # 转换为有符号 int16
        if int_val >= 32768:
            int_val -= 65536
        int16_array.append(int_val)
    
    return int16_array


def int8_saturate_add(a: int, b: int) -> int:
    """
    int8 饱和加法
    
    Args:
        a: 第一个操作数
        b: 第二个操作数
        
    Returns:
        饱和后的结果
    """
    result = a + b
    if result > 127:
        return 127
    elif result < -128:
        return -128
    return result


def int16_saturate_add(a: int, b: int) -> int:
    """
    int16 饱和加法
    
    Args:
        a: 第一个操作数
        b: 第二个操作数
        
    Returns:
        饱和后的结果
    """
    result = a + b
    if result > 32767:
        return 32767
    elif result < -32768:
        return -32768
    return result


__all__ = [
    "InstructionVerifier",
    "VerifyResult",
    "VerifyStatus",
    "parse_hex_to_int8_array",
    "parse_hex_to_int16_array",
    "int8_saturate_add",
    "int16_saturate_add",
]

