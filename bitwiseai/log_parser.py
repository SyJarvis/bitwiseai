# -*- coding: utf-8 -*-
"""
日志解析模块

支持解析硬件调试日志，特别是 PE 寄存器操作日志
"""
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class InstructionType(Enum):
    """指令类型枚举"""
    LUT2 = "LUT2"
    MUL = "MUL"
    SHIFT = "SHIFT"
    ADD = "ADD"
    UNKNOWN = "UNKNOWN"


@dataclass
class RegisterValue:
    """寄存器值"""
    name: str
    hex_value: str
    dec_values: List[int] = field(default_factory=list)
    raw_line: str = ""
    
    def __str__(self):
        if self.dec_values:
            return f"{self.name}: {self.hex_value} = {self.dec_values}"
        return f"{self.name}: {self.hex_value}"


@dataclass
class Instruction:
    """指令数据结构"""
    pe_id: int  # PE 编号（0 或 1）
    instruction_type: InstructionType
    register_mapping: Dict[str, str] = field(default_factory=dict)  # 寄存器映射，如 rs0=R0
    registers: Dict[str, RegisterValue] = field(default_factory=dict)  # 寄存器值
    metadata: Dict[str, Any] = field(default_factory=dict)  # 其他元数据
    raw_block: str = ""  # 原始日志块
    
    def get_register(self, name: str) -> Optional[RegisterValue]:
        """获取寄存器值"""
        return self.registers.get(name)
    
    def get_mapped_register(self, logical_name: str) -> Optional[RegisterValue]:
        """通过逻辑名（如 rs0）获取寄存器值"""
        physical_name = self.register_mapping.get(logical_name)
        if physical_name:
            return self.registers.get(physical_name)
        return None


class LogParser:
    """日志解析器"""
    
    # 正则表达式模式
    PE_HEADER_PATTERN = r'\[AFTER\] PE\[(\d+)-(\d+)\] 寄存器:'
    PE_BLOCK_PATTERN = r'PE\[(\d+)\]:'
    INSTRUCTION_TYPE_PATTERN = r'(LUT2|MUL|SHIFT|ADD)寄存器映射:'
    REGISTER_VALUE_PATTERN = r'(\w+)\(([^)]+)\):\s+(0x[0-9A-Fa-f]+)\s*=\s*\[([^\]]+)\]'
    REGISTER_MAPPING_PATTERN = r'(\w+)=(\w+)'
    
    def __init__(self):
        """初始化解析器"""
        self.instructions: List[Instruction] = []
    
    def parse_file(self, file_path: str) -> List[Instruction]:
        """
        解析日志文件
        
        Args:
            file_path: 日志文件路径
            
        Returns:
            指令列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_text(content)
    
    def parse_text(self, text: str) -> List[Instruction]:
        """
        解析日志文本
        
        Args:
            text: 日志文本内容
            
        Returns:
            指令列表
        """
        self.instructions = []
        
        # 按 [AFTER] PE[x-x] 分割成多个块
        blocks = re.split(self.PE_HEADER_PATTERN, text)
        
        # 跳过第一个元素（可能是空的或者是开头部分）
        i = 1
        while i < len(blocks):
            if i + 2 >= len(blocks):
                break
            
            pe_start = int(blocks[i])
            pe_end = int(blocks[i + 1])
            block_content = blocks[i + 2]
            
            # 解析这个块中的每个 PE
            for pe_id in range(pe_start, pe_end + 1):
                instruction = self._parse_pe_block(block_content, pe_id)
                if instruction:
                    self.instructions.append(instruction)
            
            i += 3
        
        return self.instructions
    
    def _parse_pe_block(self, block_content: str, pe_id: int) -> Optional[Instruction]:
        """
        解析单个 PE 块
        
        Args:
            block_content: PE 块内容
            pe_id: PE 编号
            
        Returns:
            指令对象
        """
        # 查找对应 PE 的内容
        pe_pattern = rf'PE\[{pe_id}\]:(.*?)(?=PE\[\d+\]:|$)'
        match = re.search(pe_pattern, block_content, re.DOTALL)
        
        if not match:
            return None
        
        pe_content = match.group(1)
        
        # 识别指令类型
        inst_type = self._extract_instruction_type(pe_content)
        
        # 创建指令对象
        instruction = Instruction(
            pe_id=pe_id,
            instruction_type=inst_type,
            raw_block=pe_content.strip()
        )
        
        # 提取寄存器映射
        instruction.register_mapping = self._extract_register_mapping(pe_content)
        
        # 提取寄存器值
        instruction.registers = self._extract_register_values(pe_content)
        
        # 提取元数据（方向、符号等）
        instruction.metadata = self._extract_metadata(pe_content, inst_type)
        
        return instruction
    
    def _extract_instruction_type(self, content: str) -> InstructionType:
        """提取指令类型"""
        match = re.search(self.INSTRUCTION_TYPE_PATTERN, content)
        if match:
            inst_type_str = match.group(1)
            try:
                return InstructionType[inst_type_str]
            except KeyError:
                return InstructionType.UNKNOWN
        return InstructionType.UNKNOWN
    
    def _extract_register_mapping(self, content: str) -> Dict[str, str]:
        """提取寄存器映射"""
        mapping = {}
        
        # 查找映射行
        mapping_line_match = re.search(r'寄存器映射:([^\n]+)', content)
        if mapping_line_match:
            mapping_line = mapping_line_match.group(1)
            # 提取所有映射对
            for match in re.finditer(self.REGISTER_MAPPING_PATTERN, mapping_line):
                logical = match.group(1)
                physical = match.group(2)
                mapping[logical] = physical
        
        return mapping
    
    def _extract_register_values(self, content: str) -> Dict[str, RegisterValue]:
        """提取寄存器值"""
        registers = {}
        
        # 查找所有寄存器值行
        for match in re.finditer(self.REGISTER_VALUE_PATTERN, content):
            reg_name = match.group(1)
            description = match.group(2)
            hex_value = match.group(3)
            dec_values_str = match.group(4)
            
            # 解析十进制值
            dec_values = []
            for val_str in dec_values_str.split(','):
                val_str = val_str.strip()
                try:
                    dec_values.append(int(val_str))
                except ValueError:
                    pass
            
            # 创建寄存器值对象
            reg_value = RegisterValue(
                name=f"{reg_name}({description})",
                hex_value=hex_value,
                dec_values=dec_values,
                raw_line=match.group(0)
            )
            
            # 使用描述中的物理寄存器名作为键（如果有）
            arrow_match = re.search(r'->|<-\s*(\w+)', match.group(0))
            if arrow_match:
                physical_reg = arrow_match.group(1)
                registers[physical_reg] = reg_value
            else:
                registers[reg_name] = reg_value
        
        return registers
    
    def _extract_metadata(self, content: str, inst_type: InstructionType) -> Dict[str, Any]:
        """提取元数据"""
        metadata = {}
        
        if inst_type == InstructionType.SHIFT:
            # 提取 SHIFT 指令的元数据
            direction_match = re.search(r'方向=(\S+)', content)
            if direction_match:
                metadata['direction'] = direction_match.group(1)
            
            signed_match = re.search(r'(有符号|无符号)', content)
            if signed_match:
                metadata['signed'] = signed_match.group(1) == '有符号'
            
            saturate_match = re.search(r'(饱和|不饱和)', content)
            if saturate_match:
                metadata['saturate'] = saturate_match.group(1) == '饱和'
            
            round_match = re.search(r'舍入=(\w+)', content)
            if round_match:
                metadata['round_mode'] = round_match.group(1)
            
            width_match = re.search(r'移位宽度=(\d+)', content)
            if width_match:
                metadata['shift_width'] = int(width_match.group(1))
            
            bitwidth_match = re.search(r'位宽=(\d+)bit', content)
            if bitwidth_match:
                metadata['bit_width'] = int(bitwidth_match.group(1))
        
        elif inst_type == InstructionType.ADD:
            # 提取 ADD 指令的元数据
            rs0_type_match = re.search(r'rs0=(有符号|无符号)\((\d+)bit', content)
            if rs0_type_match:
                metadata['rs0_signed'] = rs0_type_match.group(1) == '有符号'
                metadata['rs0_bit_width'] = int(rs0_type_match.group(2))
            
            rs1_type_match = re.search(r'rs1=(有符号|无符号)\((\d+)bit', content)
            if rs1_type_match:
                metadata['rs1_signed'] = rs1_type_match.group(1) == '有符号'
                metadata['rs1_bit_width'] = int(rs1_type_match.group(2))
            
            output_match = re.search(r'输出=(\d+)bit', content)
            if output_match:
                metadata['output_bit_width'] = int(output_match.group(1))
        
        elif inst_type == InstructionType.MUL:
            # 提取 MUL 指令的元数据
            func_sel_match = re.search(r'func_sel=(\d+)', content)
            if func_sel_match:
                metadata['func_sel'] = int(func_sel_match.group(1))
        
        return metadata
    
    def get_instructions_by_type(self, inst_type: InstructionType) -> List[Instruction]:
        """
        按类型获取指令
        
        Args:
            inst_type: 指令类型
            
        Returns:
            指定类型的指令列表
        """
        return [inst for inst in self.instructions if inst.instruction_type == inst_type]
    
    def get_instructions_by_pe(self, pe_id: int) -> List[Instruction]:
        """
        按 PE 编号获取指令
        
        Args:
            pe_id: PE 编号
            
        Returns:
            指定 PE 的指令列表
        """
        return [inst for inst in self.instructions if inst.pe_id == pe_id]
    
    def summary(self) -> str:
        """
        生成解析摘要
        
        Returns:
            摘要字符串
        """
        summary_lines = [
            f"总共解析了 {len(self.instructions)} 条指令",
            ""
        ]
        
        # 按类型统计
        type_counts = {}
        for inst in self.instructions:
            type_counts[inst.instruction_type] = type_counts.get(inst.instruction_type, 0) + 1
        
        summary_lines.append("指令类型分布:")
        for inst_type, count in type_counts.items():
            summary_lines.append(f"  {inst_type.value}: {count}")
        
        summary_lines.append("")
        
        # 按 PE 统计
        pe_counts = {}
        for inst in self.instructions:
            pe_counts[inst.pe_id] = pe_counts.get(inst.pe_id, 0) + 1
        
        summary_lines.append("PE 分布:")
        for pe_id, count in sorted(pe_counts.items()):
            summary_lines.append(f"  PE[{pe_id}]: {count}")
        
        return "\n".join(summary_lines)


__all__ = ["LogParser", "Instruction", "RegisterValue", "InstructionType"]

