import logging
import re
from typing import List, Tuple, Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


def extract_bits(value: int, high_bit: int, low_bit: int) -> int:
    """
    从64位值中提取指定位范围的值
    
    Args:
        value: 64位整数值
        high_bit: 高位（包含）
        low_bit: 低位（包含）
    
    Returns:
        提取的位值
    """
    mask = ((1 << (high_bit - low_bit + 1)) - 1) << low_bit
    return (value & mask) >> low_bit


def parse_bit_range(bit_range_str: str) -> Tuple[int, int]:
    """
    解析位范围字符串，如 "[59:54]" 或 "[53]"
    
    Args:
        bit_range_str: 位范围字符串
    
    Returns:
        (high_bit, low_bit) 元组
    """
    # 匹配 [high:low] 或 [bit]
    match = re.match(r'\[(\d+)(?::(\d+))?\]', bit_range_str)
    if not match:
        raise ValueError(f"Invalid bit range format: {bit_range_str}")
    
    if match.group(2) is None:
        # 单个位
        bit = int(match.group(1))
        return (bit, bit)
    else:
        # 位范围
        high = int(match.group(1))
        low = int(match.group(2))
        return (high, low)


# 寄存器地址到名称的映射（根据 PEArray.h）
REGISTER_NAMES = {
    0b00000: "R0",
    0b00001: "R1",
    0b00010: "R2",
    0b00011: "R3",
    0b00100: "R4",
    0b00101: "R5",
    0b00110: "R6",
    0b00111: "R7",
    0b01000: "reserved0",
    0b01001: "reserved1",
    0b01010: "reserved2",
    0b01011: "RI0",
    0b01100: "RI1",
    0b01101: "RI2",
    0b01110: "RI3",
    0b01111: "RO0",
    0b10000: "RO1",
    0b10001: "Rm",
    0b10010: "reserved3",
}


def get_register_name(register_value: int) -> Optional[str]:
    """
    根据寄存器地址值获取寄存器名称
    
    Args:
        register_value: 寄存器地址值（5位）
    
    Returns:
        寄存器名称，如果未定义则返回 None
    """
    # 确保值在有效范围内（5位，0-31）
    if register_value > 31:
        return None
    return REGISTER_NAMES.get(register_value)


def is_register_field(field_name: str, field_width: int) -> bool:
    """
    判断字段是否为寄存器字段
    
    Args:
        field_name: 字段名
        field_width: 字段宽度
    
    Returns:
        是否为寄存器字段
    """
    # 寄存器字段通常是5位宽，字段名包含 r, rd, rs, ro 等
    register_keywords = ['rd', 'rs', 'ro', 'rd0', 'rd1', 'rd2', 'rd3', 'rd4', 'rd5',
                        'rs0', 'rs1', 'rs2', 'rs3', 'val_sel']
    return (field_width == 5 and 
            any(keyword in field_name.lower() for keyword in register_keywords))


# 定义所有指令格式
INSTRUCTION_FORMATS = {
    # 基础算术指令
    0b000000: {
        "name": "MOV",
        "fields": [
            ("opcode", [59, 54], 6),
            ("reserve", [53, 42], 12),  # [53:42] 保留位（文档未明确列出，但根据其他指令格式推断）
            ("reserve", [41, 40], 2),   # [41:40] 保留位
            ("ro", [39, 35], 5),
            ("rd", [34, 30], 5),
            ("reserve", [29, 5], 25),   # [29:5] 保留位（文档未明确列出，但根据其他指令格式推断）
            ("rs", [4, 0], 5),
        ]
    },
    0b000001: {
        "name": "ADD",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1", [52, 52], 1),
            ("bitwidth_rs0", [51, 50], 2),
            ("bitwidth_rs1", [49, 48], 2),
            ("cs", [47, 47], 1),
            ("addc_en", [46, 46], 1),
            ("bitwidth_output", [41, 40], 2),
            ("ro", [39, 35], 5),
            ("rd", [34, 30], 5),
            ("rs2", [14, 10], 5),
            ("rs1", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    0b000010: {
        "name": "SUB",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1", [52, 52], 1),
            ("bitwidth_rs0", [51, 50], 2),
            ("bitwidth_rs1", [49, 48], 2),
            ("reserve", [47, 42], 6),
            ("reserve", [41, 40], 2),
            ("ro", [39, 35], 5),
            ("rd", [34, 30], 5),
            ("rs1", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    0b000011: {
        "name": "MUL",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1", [52, 52], 1),
            ("bitwidth_rs0", [51, 50], 2),
            ("bitwidth_rs1", [49, 48], 2),
            ("shift_width", [47, 42], 6),
            ("bitwidth_output", [41, 40], 2),
            ("ro", [39, 35], 5),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("func_sel", [19, 15], 5),
            ("rs2", [14, 10], 5),
            ("rs1", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    # LUT系列指令
    0b000110: {
        "name": "LUT2",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1_z_p", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rd2", [24, 20], 5),
            ("rd3", [19, 15], 5),
            ("rd4", [14, 10], 5),
            ("rd5", [9, 5], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b000111: {
        "name": "LUT3",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1_z_p", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rd2", [24, 20], 5),
            ("rd3", [19, 15], 5),
            ("rd4", [14, 10], 5),
            ("rd5", [9, 5], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b001000: {
        "name": "LUT4",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1_z_p", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rd2", [24, 20], 5),
            ("rd3", [19, 15], 5),
            ("rd4", [14, 10], 5),
            ("rd5", [9, 5], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b001001: {
        "name": "ABS_LUT2",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("sign1_z_p", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rd2", [24, 20], 5),
            ("rd3", [19, 15], 5),
            ("rd4", [14, 10], 5),
            ("rd5", [9, 5], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b001010: {
        "name": "ABS_LUT3",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("sign1_z_p", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rd2", [24, 20], 5),
            ("rd3", [19, 15], 5),
            ("rd4", [14, 10], 5),
            ("rd5", [9, 5], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b001011: {
        "name": "ABS_LUT4",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("sign1_z_p", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rd2", [24, 20], 5),
            ("rd3", [19, 15], 5),
            ("rd4", [14, 10], 5),
            ("rd5", [9, 5], 5),
            ("rs", [4, 0], 5),
        ]
    },
    # 限幅与符号指令
    0b001100: {
        "name": "CLAMP",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("bitwidth", [51, 50], 2),
            ("ro", [39, 35], 5),
            ("rd", [34, 30], 5),
            ("val_sel", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    0b001101: {
        "name": "CLAMP_LUT2",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("sign1_z_p", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("shift_width", [47, 42], 6),
            ("bitwidth_output", [41, 40], 2),
            ("val_sel", [39, 35], 5),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rd2", [24, 20], 5),
            ("rd3", [19, 15], 5),
            ("rd4", [14, 10], 5),
            ("rd5", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    0b001110: {
        "name": "CLAMP_LUT3",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("sign1_z_p", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("shift_width", [47, 42], 6),
            ("bitwidth_output", [41, 40], 2),
            ("val_sel", [39, 35], 5),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rd2", [24, 20], 5),
            ("rd3", [19, 15], 5),
            ("rd4", [14, 10], 5),
            ("rd5", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    0b001111: {
        "name": "CLAMP_LUT4",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("sign1_z_p", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("shift_width", [47, 42], 6),
            ("bitwidth_output", [41, 40], 2),
            ("val_sel", [39, 35], 5),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rd2", [24, 20], 5),
            ("rd3", [19, 15], 5),
            ("rd4", [14, 10], 5),
            ("rd5", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    # 数学函数指令
    0b010000: {
        "name": "ABS",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("bitwidth", [51, 50], 2),
            ("ro", [39, 35], 5),
            ("rd", [34, 30], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b010001: {
        "name": "ACC",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("bitwidth_input", [51, 50], 2),
            ("rd", [34, 30], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b010010: {
        "name": "SHIFT",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("bitwidth_input", [51, 50], 2),
            ("SAT", [49, 49], 1),
            ("RND", [48, 47], 2),
            ("shift_width", [46, 42], 5),
            ("shift_mode", [16, 15], 2),
            ("rs2", [14, 10], 5),
            ("dir", [52, 52], 1),
            ("reserve", [41, 40], 2),
            ("ro", [39, 35], 5),
            ("rd", [34, 30], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b010011: {
        "name": "P_ABS_MUL1",
        "fields": [
            ("opcode", [59, 54], 6),
            ("bitwidth_input", [51, 50], 2),
            ("取符号", [49, 49], 1),
            ("shift_width", [47, 42], 6),
            ("bitwidth_output", [41, 40], 2),
            ("ro", [39, 35], 5),
            ("rd0", [34, 30], 5),
            ("rd1", [29, 25], 5),
            ("rs1", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    0b010100: {
        "name": "P_ABS_MUL2",
        "fields": [
            ("opcode", [59, 54], 6),
            ("shift_width", [47, 42], 6),
            ("bitwidth_output", [41, 40], 2),
            ("ro", [39, 35], 5),
            ("rd0", [34, 30], 5),
            ("rs2", [19, 15], 5),
            ("rs1", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    0b010101: {
        "name": "P_SIGN",
        "fields": [
            ("opcode", [59, 54], 6),
            ("bitwidth", [51, 50], 2),
            ("reserve", [47, 42], 6),
            ("reserve", [41, 40], 2),
            ("ro", [39, 35], 5),
            ("rd", [34, 30], 5),
            ("rs1", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    0b010110: {
        "name": "MUL_IMM",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("bitwidth_output", [49, 48], 2),
            ("shift_width", [47, 42], 6),
            ("rd", [41, 37], 5),
            ("rs1", [36, 32], 5),
            ("imm", [31, 0], 32),
        ]
    },
    0b010111: {
        "name": "ADD_IMM",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1", [52, 52], 1),
            ("bitwidth", [51, 50], 2),
            ("rd", [41, 37], 5),
            ("rs1", [36, 32], 5),
            ("imm", [31, 0], 32),
        ]
    },
    # 立即数指令
    0b011000: {
        "name": "MOV_IMM",
        "fields": [
            ("opcode", [59, 54], 6),
            ("rd", [41, 37], 5),
            ("imm", [31, 0], 32),
        ]
    },
    0b011001: {
        "name": "MULx_IMM",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("bitwidth_output", [49, 48], 2),
            ("shift_width", [47, 42], 6),
            ("rd", [41, 37], 5),
            ("rs1", [36, 32], 5),
            ("imm", [31, 0], 32),
        ]
    },
    0b011010: {
        "name": "SQRT",
        "fields": [
            ("opcode", [59, 54], 6),
            ("bitwidth_input", [51, 50], 2),
            ("rd", [34, 30], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b011011: {
        "name": "ADDx",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign0", [53, 53], 1),
            ("sign1", [52, 52], 1),
            ("bitwidth_rs0", [51, 50], 2),
            ("bitwidth_rs1", [49, 48], 2),
            ("bitwidth_output", [41, 40], 2),
            ("rd", [34, 30], 5),
            ("rs1", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
    0b011100: {
        "name": "SHIFTx",
        "fields": [
            ("opcode", [59, 54], 6),
            ("sign", [53, 53], 1),
            ("固定为0", [52, 52], 1),
            ("bitwidth_input", [51, 50], 2),
            ("RND", [48, 47], 2),
            ("shift_width", [46, 42], 5),
            ("rd", [34, 30], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b011101: {
        "name": "CLZ",
        "fields": [
            ("opcode", [59, 54], 6),
            ("bitwidth", [51, 50], 2),
            ("rd", [34, 30], 5),
            ("rs", [4, 0], 5),
        ]
    },
    0b011110: {
        "name": "CONCAT",
        "fields": [
            ("opcode", [59, 54], 6),
            ("bitwidth", [51, 50], 2),
            ("ro", [39, 35], 5),
            ("rd", [34, 30], 5),
            ("rs3", [19, 15], 5),
            ("rs2", [14, 10], 5),
            ("rs1", [9, 5], 5),
            ("rs0", [4, 0], 5),
        ]
    },
}


def parse_instruction(cmd: int) -> Dict[str, Any]:
    """
    解析一条64位指令
    
    Args:
        cmd: 64位指令值
    
    Returns:
        解析后的指令字典，包含：
        - instruction_name: 指令名称
        - opcode: 操作码（十进制和十六进制）
        - fields: 字段列表，每个字段包含：
          - name: 字段名
          - value: 字段值（二进制格式）
          - hex: 字段值（十六进制）
          - bits: 位范围字符串
          - register_name: 寄存器名称（如果是寄存器字段）
    """
    # 提取 opcode
    opcode = extract_bits(cmd, 59, 54)
    
    # 查找指令格式
    if opcode not in INSTRUCTION_FORMATS:
        return {
            "instruction_name": "UNKNOWN",
            "opcode": {
                "decimal": opcode,
                "hex": f"0x{opcode:02x}",
                "binary": f"0b{opcode:06b}"
            },
            "cmd_hex": f"0x{cmd:016x}",
            "cmd_binary": f"0b{cmd:064b}",
            "fields": [],
            "error": f"Unknown opcode: 0b{opcode:06b} (0x{opcode:02x})"
        }
    
    instr_format = INSTRUCTION_FORMATS[opcode]
    fields = []
    
    # 解析每个字段
    for field_name, (high_bit, low_bit), width in instr_format["fields"]:
        field_value = extract_bits(cmd, high_bit, low_bit)
        
        # 生成位范围字符串
        if high_bit == low_bit:
            bits_str = f"[{high_bit}]"
        else:
            bits_str = f"[{high_bit}:{low_bit}]"
        
        # 生成十六进制字符串（根据宽度）
        if width == 1:
            hex_str = f"0x{field_value:x}"
        elif width <= 8:
            hex_str = f"0x{field_value:02x}"
        elif width <= 16:
            hex_str = f"0x{field_value:04x}"
        elif width <= 32:
            hex_str = f"0x{field_value:08x}"
        else:
            hex_str = f"0x{field_value:016x}"
        
        field_dict = {
            "name": field_name,
            "value": hex_str,  # 使用十六进制格式
            "hex": hex_str,  # 保持一致性
            "bits": bits_str,
            "width": width
        }
        
        # 如果是寄存器字段，添加寄存器名称
        if is_register_field(field_name, width):
            register_name = get_register_name(field_value)
            if register_name:
                field_dict["register_name"] = register_name
        
        fields.append(field_dict)
    
    return {
        "instruction_name": instr_format["name"],
        "opcode": {
            "decimal": opcode,
            "hex": f"0x{opcode:02x}",
            "binary": f"0b{opcode:06b}"
        },
        "cmd_hex": f"0x{cmd:016x}",
        "cmd_binary": f"0b{cmd:064b}",
        "fields": fields
    }


def parse_asm_file_to_bytes(
    file_path: str,
    expected_len: int = 0,
    print_instruction_info: Optional[Callable[[int, int, str], None]] = None
) -> Tuple[bool, List[int]]:
    """
    解析 ASM 文件为字节数组
    
    Args:
        file_path: ASM 文件路径
        expected_len: 期望的长度（0 表示不限制）
        print_instruction_info: 可选的指令信息打印回调函数
                                (cmd: int, instr_idx: int, original_hex: str) -> None
    
    Returns:
        (success: bool, bytes: List[int])
        - success: 是否解析成功
        - bytes: 解析后的字节数组（每个元素是 0-255 的整数）
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # 读取所有行，去除空白字符
            lines = []
            for line in file:
                # 去除所有空白字符（包括空格、制表符、换行符等）
                cleaned_line = ''.join(line.split())
                if cleaned_line:
                    lines.append(cleaned_line)
    except IOError as e:
        logger.error(f"Failed to open ASM file: {file_path}, error: {e}")
        return False, []
    
    if not lines:
        logger.warning("ASM file is empty")
        return False, []
    
    logger.debug(f"ASM file: {len(lines)} lines")
    
    all_instructions = []  # List[List[int]]，每个指令是8个字节
    original_hex_strings = []  # List[str]，保存原始十六进制字符串
    
    # 解析每一行
    for line_content in lines:
        if len(line_content) < 16:
            continue
        
        # 计算该行包含多少个指令（每16个字符一个指令）
        num_instr_in_line = len(line_content) // 16
        
        # 从右到左解析指令（从行的末尾开始）
        for idx in range(num_instr_in_line):
            # 计算指令在行中的位置（从右到左）
            pos = len(line_content) - (idx + 1) * 16
            instr_hex = line_content[pos:pos + 16]
            
            # 将16个十六进制字符转换为8个字节
            instr_bytes = []
            for j in range(8):
                byte_str = instr_hex[j * 2:(j + 1) * 2]
                try:
                    byte_val = int(byte_str, 16)
                    instr_bytes.append(byte_val)
                except ValueError as e:
                    logger.warning(f"Failed to parse ASM byte: {byte_str} ({e})")
                    instr_bytes.append(0)
            
            all_instructions.append(instr_bytes)
            original_hex_strings.append(instr_hex)
    
    logger.debug(f"Found {len(all_instructions)} valid instructions")
    
    logger.info("==================== ASM 指令解析 (执行顺序) ====================")
    logger.info(f"文件: {file_path}")
    logger.info(f"总指令数: {len(all_instructions)}")
    
    # 构建最终的字节数组
    bytes_result = []
    
    for i, instr in enumerate(all_instructions):
        # 字节顺序反转：从 instr[7] 到 instr[0]
        for j in range(7, -1, -1):
            bytes_result.append(instr[j])
        
        # 计算指令的64位值（用于打印信息）
        cmd = 0
        for j in range(8):
            cmd |= (instr[7 - j] << (j * 8))
        
        # 打印指令信息（如果提供了回调函数）
        if print_instruction_info:
            print_instruction_info(cmd, i, original_hex_strings[i])
    
    logger.info("================================================================")
    
    # 如果指定了期望长度且结果超过期望长度，进行截断
    if expected_len > 0 and len(bytes_result) > expected_len:
        logger.debug(f"Truncating output from {len(bytes_result)} to {expected_len} bytes")
        bytes_result = bytes_result[:expected_len]
    
    logger.info(f"Loaded {len(bytes_result)} bytes ({len(bytes_result) // 8} instructions) from ASM file: {file_path}")
    
    success = len(bytes_result) > 0
    return success, bytes_result


def parse_asm_file_to_instructions(file_path: str) -> List[Dict[str, Any]]:
    """
    解析 ASM 文件为指令列表（每条指令包含详细解析信息）
    
    Args:
        file_path: ASM 文件路径
    
    Returns:
        指令列表，每个元素是一个包含完整解析信息的字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = []
            for line in file:
                cleaned_line = ''.join(line.split())
                if cleaned_line:
                    lines.append(cleaned_line)
    except IOError as e:
        logger.error(f"Failed to open ASM file: {file_path}, error: {e}")
        return []
    
    if not lines:
        logger.warning("ASM file is empty")
        return []
    
    instructions = []
    
    # 解析每一行
    for line_content in lines:
        if len(line_content) < 16:
            continue
        
        num_instr_in_line = len(line_content) // 16
        
        # 从右到左解析指令
        for idx in range(num_instr_in_line):
            pos = len(line_content) - (idx + 1) * 16
            instr_hex = line_content[pos:pos + 16]
            
            # 转换为8个字节
            instr_bytes = []
            for j in range(8):
                byte_str = instr_hex[j * 2:(j + 1) * 2]
                try:
                    byte_val = int(byte_str, 16)
                    instr_bytes.append(byte_val)
                except ValueError:
                    instr_bytes.append(0)
            
            # 计算64位指令值
            cmd = 0
            for j in range(8):
                cmd |= (instr_bytes[7 - j] << (j * 8))
            
            # 解析指令
            parsed = parse_instruction(cmd)
            parsed["original_hex"] = instr_hex
            parsed["instruction_index"] = len(instructions)
            
            instructions.append(parsed)
    
    return instructions


# Skill 工具包装函数（供 LLM 调用）

def parse_asm_instruction(cmd: str) -> str:
    """
    解析一条 ASM 指令（包装函数，供 LLM 调用）
    
    Args:
        cmd: 64位指令值，可以是：
            - 整数字符串（如 "1234567890"）
            - 十六进制字符串（如 "0x1234567890abcdef" 或 "1234567890abcdef"）
            - 二进制字符串（如 "0b1010..." 或 "1010..."）
    
    Returns:
        解析结果的 JSON 字符串
    """
    import json
    
    # 转换输入为整数
    cmd_str = str(cmd).strip()
    
    try:
        if cmd_str.startswith("0x"):
            # 十六进制（带 0x 前缀）
            cmd_int = int(cmd_str, 16)
        elif cmd_str.startswith("0b"):
            # 二进制（带 0b 前缀）
            cmd_int = int(cmd_str, 2)
        elif all(c in "0123456789abcdefABCDEF" for c in cmd_str) and len(cmd_str) >= 2:
            # 可能是十六进制（无前缀）
            try:
                cmd_int = int(cmd_str, 16)
            except ValueError:
                # 尝试作为十进制
                cmd_int = int(cmd_str)
        elif all(c in "01" for c in cmd_str):
            # 二进制（无前缀）
            cmd_int = int(cmd_str, 2)
        else:
            # 尝试作为十进制整数
            cmd_int = int(cmd_str)
    except ValueError:
        return json.dumps({
            "error": f"无法解析指令值: {cmd_str}。请提供整数、十六进制（0x...）或二进制（0b...）格式。"
        }, ensure_ascii=False, indent=2)
    
    # 解析指令
    try:
        result = parse_instruction(cmd_int)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"解析指令时出错: {str(e)}"
        }, ensure_ascii=False, indent=2)


def parse_asm_file(file_path: str) -> str:
    """
    解析 ASM 文件为指令列表（包装函数，供 LLM 调用）
    
    Args:
        file_path: ASM 文件路径
    
    Returns:
        解析结果的 JSON 字符串
    """
    import json
    from pathlib import Path
    
    # 检查文件是否存在
    path = Path(file_path)
    if not path.exists():
        return json.dumps({
            "error": f"文件不存在: {file_path}"
        }, ensure_ascii=False, indent=2)
    
    # 解析文件
    try:
        instructions = parse_asm_file_to_instructions(str(path))
        return json.dumps({
            "file_path": file_path,
            "instruction_count": len(instructions),
            "instructions": instructions
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"解析文件时出错: {str(e)}"
        }, ensure_ascii=False, indent=2)
