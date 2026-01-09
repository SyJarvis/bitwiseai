# -*- coding: utf-8 -*-
"""
BitwiseAI 接口定义

提供抽象接口，让用户可以自定义解析器、验证器和任务
"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """分析结果基类"""
    status: str  # "pass", "fail", "error", "warning"
    message: str = ""
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


class LogParserInterface(ABC):
    """
    日志解析器接口
    
    用户实现此接口来定义自己的日志解析逻辑
    """
    
    @abstractmethod
    def parse_file(self, file_path: str) -> Any:
        """
        解析日志文件
        
        Args:
            file_path: 日志文件路径
            
        Returns:
            解析后的数据（格式由用户定义）
        """
        pass
    
    @abstractmethod
    def parse_text(self, text: str) -> Any:
        """
        解析日志文本
        
        Args:
            text: 日志文本
            
        Returns:
            解析后的数据（格式由用户定义）
        """
        pass


class VerifierInterface(ABC):
    """
    验证器接口
    
    用户实现此接口来定义自己的验证逻辑
    """
    
    @abstractmethod
    def verify(self, data: Any) -> List[AnalysisResult]:
        """
        验证数据
        
        Args:
            data: 待验证的数据
            
        Returns:
            验证结果列表
        """
        pass


class TaskInterface(ABC):
    """
    任务接口
    
    用户实现此接口来定义完整的分析任务
    """
    
    @abstractmethod
    def execute(self, context: 'BitwiseAI') -> List[AnalysisResult]:
        """
        执行任务
        
        Args:
            context: BitwiseAI 上下文，提供 LLM、RAG、工具等功能
            
        Returns:
            任务执行结果列表
        """
        pass
    
    def get_name(self) -> str:
        """
        获取任务名称
        
        Returns:
            任务名称
        """
        return self.__class__.__name__
    
    def get_description(self) -> str:
        """
        获取任务描述
        
        Returns:
            任务描述
        """
        return self.__doc__ or "无描述"


class AnalysisTask(TaskInterface):
    """
    分析任务基类
    
    提供常用的任务模板，用户可以继承并重写特定方法
    """
    
    def __init__(
        self,
        name: str = "",
        description: str = "",
        parser: Optional[LogParserInterface] = None,
        verifier: Optional[VerifierInterface] = None
    ):
        """
        初始化分析任务
        
        Args:
            name: 任务名称
            description: 任务描述
            parser: 日志解析器
            verifier: 验证器
        """
        self.name = name or self.get_name()
        self.description = description or self.get_description()
        self.parser = parser
        self.verifier = verifier
        self.results: List[AnalysisResult] = []
    
    def execute(self, context: 'BitwiseAI') -> List[AnalysisResult]:
        """
        执行任务的默认流程
        
        1. 加载日志
        2. 解析日志
        3. 验证数据
        4. 生成报告
        """
        self.results = []
        
        try:
            # 步骤1: 前置处理
            self.before_execute(context)
            
            # 步骤2: 解析日志（如果有解析器）
            parsed_data = None
            if self.parser and hasattr(context, 'log_file_path'):
                parsed_data = self.parser.parse_file(context.log_file_path)
            
            # 步骤3: 执行验证（如果有验证器）
            if self.verifier and parsed_data:
                verify_results = self.verifier.verify(parsed_data)
                self.results.extend(verify_results)
            
            # 步骤4: 自定义分析逻辑
            custom_results = self.analyze(context, parsed_data)
            if custom_results:
                self.results.extend(custom_results)
            
            # 步骤5: 后置处理
            self.after_execute(context)
            
        except Exception as e:
            error_result = AnalysisResult(
                status="error",
                message=f"任务执行失败: {str(e)}"
            )
            self.results.append(error_result)
        
        return self.results
    
    def before_execute(self, context: 'BitwiseAI'):
        """任务执行前的钩子"""
        pass
    
    def analyze(self, context: 'BitwiseAI', parsed_data: Any) -> List[AnalysisResult]:
        """
        自定义分析逻辑（由子类重写）
        
        Args:
            context: BitwiseAI 上下文
            parsed_data: 解析后的数据
            
        Returns:
            分析结果列表
        """
        return []
    
    def after_execute(self, context: 'BitwiseAI'):
        """任务执行后的钩子"""
        pass
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取任务执行摘要
        
        Returns:
            摘要字典
        """
        status_counts = {}
        for result in self.results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        return {
            "task_name": self.name,
            "total_results": len(self.results),
            "status_counts": status_counts
        }


__all__ = [
    "LogParserInterface",
    "VerifierInterface",
    "TaskInterface",
    "AnalysisTask",
    "AnalysisResult",
]

