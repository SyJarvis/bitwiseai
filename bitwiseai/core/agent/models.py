# -*- coding: utf-8 -*-
"""
Agent 数据模型

定义 Agent、步骤、结果等核心数据结构
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from langchain_core.messages import BaseMessage


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    STOPPED = "stopped"
    NEED_APPROVAL = "need_approval"


class StopReason(str, Enum):
    """停止原因"""
    NO_TOOL_CALLS = "no_tool_calls"
    TOOL_REJECTED = "tool_rejected"
    MAX_STEPS = "max_steps"
    COMPLETED = "completed"
    ERROR = "error"
    USER_INTERRUPT = "user_interrupt"


@dataclass(slots=True)
class StepInput:
    """步骤输入"""
    query: str
    """用户查询"""

    messages: list[BaseMessage]
    """消息历史"""

    tools: list[Any]
    """可用工具列表"""

    context: dict[str, Any] = field(default_factory=dict)
    """额外上下文"""

    system_prompt: str | None = None
    """系统提示词"""


@dataclass(slots=True)
class ToolCall:
    """工具调用"""
    id: str
    """调用 ID"""

    name: str
    """工具名称"""

    arguments: dict[str, Any]
    """参数"""

    status: StepStatus = StepStatus.PENDING
    """状态"""

    result: Any = None
    """执行结果"""

    error: str | None = None
    """错误信息"""


@dataclass(slots=True)
class StepOutput:
    """步骤输出"""
    message: BaseMessage
    """AI 生成的消息"""

    tool_calls: list[ToolCall] = field(default_factory=list)
    """工具调用列表"""

    status: StepStatus = StepStatus.SUCCESS
    """步骤状态"""

    thinking: str | None = None
    """思考过程（如果有）"""

    usage: dict[str, int] = field(default_factory=dict)
    """Token 使用量"""

    step_number: int = 0
    """步骤编号"""

    execution_time: float = 0.0
    """执行时间（秒）"""


@dataclass(slots=True)
class TurnResult:
    """单轮执行结果"""
    stop_reason: StopReason
    """停止原因"""

    final_message: BaseMessage | None
    """最终消息"""

    steps: list[StepOutput] = field(default_factory=list)
    """所有步骤"""

    total_steps: int = 0
    """总步骤数"""

    total_time: float = 0.0
    """总执行时间"""

    final_output: str | None = None
    """最终输出文本"""


@dataclass(slots=True)
class AgentConfig:
    """Agent 配置"""
    name: str = "default"
    """Agent 名称"""

    description: str = ""
    """描述"""

    system_prompt: str = ""
    """系统提示词"""

    max_steps: int = 10
    """最大步骤数"""

    max_execution_time: float = 300.0
    """最大执行时间（秒）"""

    require_approval: bool = False
    """是否需要审批危险操作"""

    enable_thinking: bool = False
    """是否启用思考模式"""

    retry_on_error: bool = True
    """错误时是否重试"""

    max_retries: int = 3
    """最大重试次数"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """额外元数据"""


class AgentCapability(str, Enum):
    """Agent 能力"""
    CHAT = "chat"
    """对话能力"""

    TOOL_USE = "tool_use"
    """工具使用"""

    CODE_EXECUTION = "code_execution"
    """代码执行"""

    WEB_BROWSING = "web_browsing"
    """网页浏览"""

    FILE_OPERATION = "file_operation"
    """文件操作"""

    MULTI_AGENT = "multi_agent"
    """多 Agent 协作"""


@dataclass(slots=True)
class AgentSpec:
    """Agent 规格"""
    name: str
    """Agent 名称"""

    config: AgentConfig
    """配置"""

    capabilities: set[AgentCapability] = field(default_factory=set)
    """能力集合"""

    tools: list[Any] = field(default_factory=list)
    """工具列表"""

    sub_agents: dict[str, "AgentSpec"] = field(default_factory=dict)
    """子 Agent"""

    def add_capability(self, capability: AgentCapability) -> None:
        """添加能力"""
        self.capabilities.add(capability)

    def has_capability(self, capability: AgentCapability) -> bool:
        """检查是否有某个能力"""
        return capability in self.capabilities


@dataclass(slots=True)
class ExecutionContext:
    """执行上下文"""
    session_id: str
    """会话 ID"""

    turn_id: str
    """当前轮次 ID"""

    step_number: int = 0
    """当前步骤编号"""

    start_time: float = field(default_factory=lambda: datetime.now().timestamp())
    """开始时间"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """额外元数据"""

    checkpoints: dict[str, Any] = field(default_factory=dict)
    """检查点数据"""

    def elapsed_time(self) -> float:
        """获取已用时间"""
        return datetime.now().timestamp() - self.start_time

    def increment_step(self) -> int:
        """增加步骤编号"""
        self.step_number += 1
        return self.step_number


__all__ = [
    "StepStatus",
    "StopReason",
    "StepInput",
    "ToolCall",
    "StepOutput",
    "TurnResult",
    "AgentConfig",
    "AgentCapability",
    "AgentSpec",
    "ExecutionContext",
]
