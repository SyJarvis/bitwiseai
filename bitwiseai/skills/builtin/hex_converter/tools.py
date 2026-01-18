# -*- coding: utf-8 -*-
"""
十六进制/二进制转换工具
"""


def hex_to_decimal(hex_str: str) -> int:
    """
    将十六进制字符串转换为十进制
    
    Args:
        hex_str: 十六进制字符串，如 "0xFF" 或 "FF"
        
    Returns:
        十进制整数
    """
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return int(hex_str, 16)


def decimal_to_hex(dec_num: int) -> str:
    """
    将十进制整数转换为十六进制字符串
    
    Args:
        dec_num: 十进制整数
        
    Returns:
        十六进制字符串（带 0x 前缀）
    """
    return hex(dec_num)


def binary_to_decimal(bin_str: str) -> int:
    """
    将二进制字符串转换为十进制
    
    Args:
        bin_str: 二进制字符串，如 "0b1010" 或 "1010"
        
    Returns:
        十进制整数
    """
    if bin_str.startswith("0b"):
        bin_str = bin_str[2:]
    return int(bin_str, 2)


def decimal_to_binary(dec_num: int) -> str:
    """
    将十进制整数转换为二进制字符串
    
    Args:
        dec_num: 十进制整数
        
    Returns:
        二进制字符串（带 0b 前缀）
    """
    return bin(dec_num)


def hex_to_binary(hex_str: str) -> str:
    """
    将十六进制字符串转换为二进制字符串
    
    Args:
        hex_str: 十六进制字符串，如 "0xFF" 或 "FF"
        
    Returns:
        二进制字符串（带 0b 前缀）
    """
    dec = hex_to_decimal(hex_str)
    return decimal_to_binary(dec)


def binary_to_hex(bin_str: str) -> str:
    """
    将二进制字符串转换为十六进制字符串
    
    Args:
        bin_str: 二进制字符串，如 "0b1010" 或 "1010"
        
    Returns:
        十六进制字符串（带 0x 前缀）
    """
    dec = binary_to_decimal(bin_str)
    return decimal_to_hex(dec)

