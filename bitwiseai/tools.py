# -*- coding: utf-8 -*-
"""
工具系统模块

支持自定义工具注册和管理，包括 Python 函数、LangChain Tools 和配置化工具
"""
import os
import json
import importlib
import subprocess
from typing import Callable, Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class ToolType(Enum):
    """工具类型"""
    PYTHON_FUNCTION = "python_function"
    LANGCHAIN_TOOL = "langchain_tool"
    SHELL_COMMAND = "shell_command"


@dataclass
class Tool:
    """工具定义"""
    name: str
    tool_type: ToolType
    description: str = ""
    function: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def invoke(self, *args, **kwargs) -> Any:
        """调用工具"""
        if self.tool_type == ToolType.PYTHON_FUNCTION and self.function:
            return self.function(*args, **kwargs)
        elif self.tool_type == ToolType.SHELL_COMMAND:
            return self._invoke_shell_command(kwargs)
        elif self.tool_type == ToolType.LANGCHAIN_TOOL:
            # LangChain Tool 通过 function 字段存储
            if self.function:
                return self.function(*args, **kwargs)
        else:
            raise ValueError(f"不支持的工具类型: {self.tool_type}")
    
    def _invoke_shell_command(self, kwargs: Dict[str, Any]) -> str:
        """执行 Shell 命令"""
        command = self.metadata.get("command", "")
        
        # 替换命令中的占位符
        for key, value in kwargs.items():
            command = command.replace(f"{{{key}}}", str(value))
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "命令执行超时"
        except Exception as e:
            return f"命令执行失败: {str(e)}"


class ToolRegistry:
    """工具注册器"""
    
    def __init__(self):
        """初始化工具注册器"""
        self.tools: Dict[str, Tool] = {}
    
    def register_function(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: str = ""
    ) -> Tool:
        """
        注册 Python 函数为工具
        
        Args:
            func: Python 函数
            name: 工具名称（默认使用函数名）
            description: 工具描述（默认使用函数文档字符串）
            
        Returns:
            工具对象
        """
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or ""
        
        tool = Tool(
            name=tool_name,
            tool_type=ToolType.PYTHON_FUNCTION,
            description=tool_desc.strip(),
            function=func
        )
        
        self.tools[tool_name] = tool
        return tool
    
    def register_langchain_tool(self, tool: Any, name: Optional[str] = None) -> Tool:
        """
        注册 LangChain Tool
        
        Args:
            tool: LangChain Tool 对象
            name: 工具名称（可选，默认使用 tool.name）
            
        Returns:
            工具对象
        """
        try:
            # 尝试导入 LangChain
            from langchain.tools import BaseTool
            
            if not isinstance(tool, BaseTool):
                raise ValueError("提供的对象不是有效的 LangChain Tool")
            
            tool_name = name or tool.name
            
            wrapped_tool = Tool(
                name=tool_name,
                tool_type=ToolType.LANGCHAIN_TOOL,
                description=tool.description,
                function=tool.run,
                metadata={"langchain_tool": tool}
            )
            
            self.tools[tool_name] = wrapped_tool
            return wrapped_tool
        
        except ImportError:
            raise ImportError("需要安装 langchain 包才能使用 LangChain Tools")
    
    def register_shell_command(
        self,
        name: str,
        command: str,
        description: str = ""
    ) -> Tool:
        """
        注册 Shell 命令为工具
        
        Args:
            name: 工具名称
            command: Shell 命令（支持 {param} 占位符）
            description: 工具描述
            
        Returns:
            工具对象
        """
        tool = Tool(
            name=name,
            tool_type=ToolType.SHELL_COMMAND,
            description=description,
            metadata={"command": command}
        )
        
        self.tools[name] = tool
        return tool
    
    def register_from_config(self, config: Dict[str, Any]) -> Tool:
        """
        从配置字典注册工具
        
        Args:
            config: 工具配置字典
            
        Returns:
            工具对象
            
        配置格式示例:
        {
            "type": "python_function",
            "name": "calculate_saturate_add",
            "module": "custom_tools.hardware",
            "function": "saturate_add_int8",
            "description": "计算饱和加法"
        }
        
        或:
        {
            "type": "shell_command",
            "name": "run_simulator",
            "command": "./sim --verify {input_file}",
            "description": "运行模拟器"
        }
        """
        tool_type = config.get("type", "")
        
        if tool_type == "python_function":
            return self._register_python_function_from_config(config)
        elif tool_type == "shell_command":
            return self.register_shell_command(
                name=config.get("name", ""),
                command=config.get("command", ""),
                description=config.get("description", "")
            )
        else:
            raise ValueError(f"不支持的工具类型: {tool_type}")
    
    def _register_python_function_from_config(self, config: Dict[str, Any]) -> Tool:
        """从配置注册 Python 函数"""
        module_name = config.get("module")
        function_name = config.get("function")
        
        if not module_name or not function_name:
            raise ValueError("Python 函数工具需要 module 和 function 参数")
        
        try:
            # 动态导入模块
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            
            return self.register_function(
                func=func,
                name=config.get("name", function_name),
                description=config.get("description", "")
            )
        
        except (ImportError, AttributeError) as e:
            raise ValueError(f"无法加载函数 {module_name}.{function_name}: {str(e)}")
    
    def load_tools_from_config_file(self, config_path: str) -> List[Tool]:
        """
        从配置文件加载工具
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            工具列表
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        tools = config.get("tools", [])
        registered_tools = []
        
        for tool_config in tools:
            try:
                tool = self.register_from_config(tool_config)
                registered_tools.append(tool)
            except Exception as e:
                print(f"警告: 加载工具 {tool_config.get('name', 'unknown')} 失败: {str(e)}")
        
        return registered_tools
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具对象，如果不存在则返回 None
        """
        return self.tools.get(name)
    
    def invoke_tool(self, name: str, *args, **kwargs) -> Any:
        """
        调用工具
        
        Args:
            name: 工具名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            工具执行结果
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"工具不存在: {name}")
        
        return tool.invoke(*args, **kwargs)
    
    def list_tools(self) -> List[str]:
        """
        列出所有工具名称
        
        Returns:
            工具名称列表
        """
        return list(self.tools.keys())
    
    def get_tools_summary(self) -> str:
        """
        获取工具摘要
        
        Returns:
            工具摘要字符串
        """
        lines = [f"已注册 {len(self.tools)} 个工具:", ""]
        
        for name, tool in self.tools.items():
            lines.append(f"  [{tool.tool_type.value}] {name}")
            if tool.description:
                lines.append(f"    {tool.description}")
        
        return "\n".join(lines)
    
    def to_langchain_tools(self) -> List[Any]:
        """
        将注册的工具转换为 LangChain Tools
        
        Returns:
            LangChain Tool 列表
        """
        try:
            from langchain.tools import Tool as LangChainTool
            
            langchain_tools = []
            
            for name, tool in self.tools.items():
                # 如果本来就是 LangChain Tool，直接使用
                if tool.tool_type == ToolType.LANGCHAIN_TOOL:
                    langchain_tools.append(tool.metadata.get("langchain_tool"))
                else:
                    # 将其他类型的工具包装为 LangChain Tool
                    langchain_tool = LangChainTool(
                        name=tool.name,
                        description=tool.description or f"工具: {tool.name}",
                        func=lambda *args, t=tool, **kwargs: t.invoke(*args, **kwargs)
                    )
                    langchain_tools.append(langchain_tool)
            
            return langchain_tools
        
        except ImportError:
            raise ImportError("需要安装 langchain 包才能使用此功能")


# 内置工具函数示例

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


def register_builtin_tools(registry: ToolRegistry):
    """
    注册内置工具
    
    Args:
        registry: 工具注册器
    """
    registry.register_function(hex_to_decimal, description="将十六进制转换为十进制")
    registry.register_function(decimal_to_hex, description="将十进制转换为十六进制")
    registry.register_function(binary_to_decimal, description="将二进制转换为十进制")


__all__ = [
    "ToolRegistry",
    "Tool",
    "ToolType",
    "register_builtin_tools",
    "hex_to_decimal",
    "decimal_to_hex",
    "binary_to_decimal",
]

