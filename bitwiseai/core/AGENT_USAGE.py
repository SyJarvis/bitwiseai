# -*- coding: utf-8 -*-
"""
Agent 循环系统使用示例

演示完整的对话 → 执行 → 反馈的正向循环
"""

import asyncio
from pathlib import Path


# ============================================================================
# 基础 Agent 使用
# ============================================================================


async def demo_basic_agent():
    """基础 Agent 使用示例"""
    from bitwiseai.core import (
        create_chat_engine,
        AgentConfig,
        LoopConfig,
    )

    # 创建引擎
    engine = create_chat_engine(
        model="gpt-4o-mini",
        system_prompt="你是一个专业的编程助手。",
    )
    await engine.initialize()

    # 使用 Agent 循环进行对话
    response = await engine.chat_with_agent(
        "帮我写一个 Python 函数，计算斐波那契数列的第 n 项。",
        agent_config=AgentConfig(
            name="coder",
            system_prompt="你是专业的 Python 开发者，擅长编写清晰高效的代码。",
            max_steps=5,
        ),
        loop_config=LoopConfig(
            max_turns=1,
            max_steps_per_turn=5,
        ),
    )

    print(f"AI 回答:\n{response}")


# ============================================================================
# 多 Agent 协作
# ============================================================================


async def demo_multi_agent():
    """多 Agent 协作示例"""
    from bitwiseai.core import (
        create_chat_engine,
        Agent,
        AgentConfig,
        AgentSpec,
        LoopConfig,
        MultiAgentOrchestrator,
    )
    from langchain_core.tools import tool

    # 创建引擎
    engine = await _create_engine()

    # 创建主 Agent
    main_config = AgentConfig(
        name="coordinator",
        system_prompt="你是任务协调者，负责将任务分派给合适的子 Agent。",
        max_steps=10,
    )
    main_agent = engine.create_agent(
        name="coordinator",
        system_prompt=main_config.system_prompt,
        max_steps=main_config.max_steps,
    )

    # 创建子 Agent - 代码分析专家
    code_agent_config = AgentConfig(
        name="code_analyzer",
        system_prompt="你是代码分析专家，擅长分析代码结构和找出问题。",
        max_steps=5,
    )
    code_agent = Agent(
        name="code_analyzer",
        spec=AgentSpec(name="code_analyzer", config=code_agent_config),
        llm_manager=engine.llm,
    )

    # 创建子 Agent - 文档生成专家
    doc_agent_config = AgentConfig(
        name="doc_generator",
        system_prompt="你是文档生成专家，擅长为代码生成清晰的文档。",
        max_steps=5,
    )
    doc_agent = Agent(
        name="doc_generator",
        spec=AgentSpec(name="doc_generator", config=doc_agent_config),
        llm_manager=engine.llm,
    )

    # 创建多 Agent 编排器
    orchestrator = MultiAgentOrchestrator(main_agent)
    orchestrator.add_subagent(code_agent, fixed=True)
    orchestrator.add_subagent(doc_agent, fixed=True)

    # 使用多 Agent 执行任务
    response = await engine.chat_with_agent(
        "分析当前目录的 Python 代码，生成结构报告和文档。",
        loop_config=LoopConfig(max_turns=1, max_steps_per_turn=10),
    )

    print(f"多 Agent 结果:\n{response}")


# ============================================================================
# 流式 Agent 执行
# ============================================================================


async def demo_agent_streaming():
    """流式 Agent 执行示例"""
    from bitwiseai.core import create_chat_engine, AgentConfig, LoopConfig

    engine = await _create_engine()

    print("AI 回答: ", end="", flush=True)

    # 流式输出
    async for token in engine.chat_with_agent_stream(
        "讲一个关于 AI 的有趣故事，不要太长。",
        agent_config=AgentConfig(
            name="storyteller",
            system_prompt="你是一个擅长讲故事的 AI。",
            max_steps=3,
        ),
    ):
        print(token, end="", flush=True)

    print()


# ============================================================================
# 带工具的 Agent
# ============================================================================


async def demo_agent_with_tools():
    """带工具的 Agent 示例"""
    from bitwiseai.core import create_chat_engine, AgentConfig
    from langchain_core.tools import tool

    # 定义工具
    @tool
    def search_files(query: str) -> str:
        """搜索文件"""
        return f"找到与 '{query}' 相关的 5 个文件"

    @tool
    def read_file(path: str) -> str:
        """读取文件内容"""
        return f"文件 {path} 的内容..."

    @tool
    def write_file(path: str, content: str) -> str:
        """写入文件"""
        return f"已写入文件 {path}"

    # 创建引擎
    engine = create_chat_engine(
        model="gpt-4o-mini",
        system_prompt="你是文件操作助手。",
    )
    await engine.initialize()

    # 创建带工具的 Agent
    response = await engine.chat_with_agent(
        "在当前目录搜索 Python 文件，读取第一个文件的内容，然后创建一个备份。",
        agent_config=AgentConfig(
            name="file_operator",
            system_prompt="你擅长文件操作，会使用工具完成任务。",
            max_steps=10,
        ),
    )

    print(f"带工具的 Agent 结果:\n{response}")


# ============================================================================
# 多轮对话 Agent
# ============================================================================


async def demo_multi_turn_agent():
    """多轮对话 Agent 示例"""
    from bitwiseai.core import create_chat_engine, AgentConfig, LoopConfig

    engine = await _create_engine()

    # 启用自动继续的多轮对话
    response = await engine.chat_with_agent(
        "分析一个复杂的项目结构，生成完整的文档。",
        loop_config=LoopConfig(
            max_turns=5,  # 最多 5 轮对话
            max_steps_per_turn=10,
            auto_continue=True,  # 自动继续
        ),
    )

    print(f"多轮对话结果:\n{response}")


# ============================================================================
# Agent 协作 - 工作流模式
# ============================================================================


async def demo_agent_workflow():
    """Agent 工作流示例"""
    from bitwiseai.core import (
        create_chat_engine,
        Agent,
        AgentConfig,
        AgentSpec,
        LoopConfig,
        MultiAgentOrchestrator,
    )

    engine = await _create_engine()

    # 创建专门的 Agent
    agents = {
        "analyzer": Agent(
            "analyzer",
            AgentSpec(
                name="analyzer",
                config=AgentConfig(
                    name="analyzer",
                    system_prompt="你是需求分析专家，负责理解用户需求。",
                ),
            ),
            engine.llm,
        ),
        "designer": Agent(
            "designer",
            AgentSpec(
                name="designer",
                config=AgentConfig(
                    name="designer",
                    system_prompt="你是架构设计专家，负责设计解决方案。",
                ),
            ),
            engine.llm,
        ),
        "implementer": Agent(
            "implementer",
            AgentSpec(
                name="implementer",
                config=AgentConfig(
                    name="implementer",
                    system_prompt="你是代码实现专家，负责编写代码。",
                ),
            ),
            engine.llm,
        ),
        "tester": Agent(
            "tester",
            AgentSpec(
                name="tester",
                config=AgentConfig(
                    name="tester",
                    system_prompt="你是测试专家，负责验证代码质量。",
                ),
            ),
            engine.llm,
        ),
    }

    # 创建编排器
    orchestrator = MultiAgentOrchestrator(agents["analyzer"])
    for agent_name, agent in agents.items():
        if agent_name != "analyzer":
            orchestrator.add_subagent(agent)

    # 执行工作流式任务
    response = await engine.chat_with_agent(
        "我需要一个用户认证系统，包含注册、登录和密码重置功能。",
        loop_config=LoopConfig(max_turns=3, max_steps_per_turn=15),
    )

    print(f"工作流结果:\n{response}")


# ============================================================================
# 带反馈的 Agent 循环
# ============================================================================


async def demo_agent_with_feedback():
    """带反馈的 Agent 循环示例"""
    from bitwiseai.core import create_chat_engine, AgentConfig, LoopConfig

    engine = await _create_engine()

    # 设置步骤回调来接收反馈
    class FeedbackCollector:
        def __init__(self):
            self.steps = []

        def on_step(self, step):
            self.steps.append(step)
            print(f"\n[步骤 {step.step_number}]")
            if hasattr(step, 'message'):
                print(f"消息: {step.message.content[:100]}...")
            if step.tool_calls:
                print(f"工具调用: {len(step.tool_calls)} 个")

    feedback = FeedbackCollector()

    # 创建 Agent 循环
    # 注意：需要在 AgentLoop 中暴露回调设置
    # 这里演示概念
    response = await engine.chat_with_agent(
        "创建一个待办事项管理应用，包含增删改查功能。",
        agent_config=AgentConfig(
            name="full_stack",
            system_prompt="你是全栈开发专家，能独立完成完整的应用开发。",
            max_steps=20,
        ),
        loop_config=LoopConfig(
            max_turns=3,
            max_steps_per_turn=20,
            enable_checkpoint=True,  # 启用检查点
            checkpoint_frequency=5,  # 每 5 步创建检查点
        ),
    )

    print(f"\n最终结果:\n{response}")
    print(f"\n执行统计: {len(feedback.steps)} 个步骤")


# ============================================================================
# 辅助函数
# ============================================================================


async def _create_engine():
    """创建测试引擎"""
    from bitwiseai.core import create_chat_engine

    engine = create_chat_engine(
        model="gpt-4o-mini",
        system_prompt="你是 BitwiseAI 助手，专注于提供专业的技术支持。",
    )
    await engine.initialize()
    return engine


# ============================================================================
# 配置示例
# ============================================================================


def demo_agent_configurations():
    """各种 Agent 配置示例"""
    from bitwiseai.core import AgentConfig, LoopConfig

    # 简单对话 Agent
    simple_config = AgentConfig(
        name="simple",
        system_prompt="你是一个友好的助手。",
        max_steps=3,
    )

    # 复杂任务 Agent
    complex_config = AgentConfig(
        name="complex",
        system_prompt="你是专家级 AI，能处理复杂的多步骤任务。",
        max_steps=50,
        max_execution_time=600,
        require_approval=True,  # 危险操作需要审批
        enable_thinking=True,  # 启用思考模式
        retry_on_error=True,
        max_retries=3,
    )

    # 循环配置
    single_turn = LoopConfig(max_turns=1)  # 单轮对话
    multi_turn = LoopConfig(
        max_turns=5,
        auto_continue=True,
        continue_threshold=0.8,
    )
    with_checkpoint = LoopConfig(
        max_turns=10,
        enable_checkpoint=True,
        checkpoint_frequency=5,
    )


if __name__ == "__main__":
    # 运行示例
    print("=" * 60)
    print("Agent 循环系统演示")
    print("=" * 60)

    # asyncio.run(demo_basic_agent())
    # asyncio.run(demo_multi_agent())
    # asyncio.run(demo_agent_streaming())
    # asyncio.run(demo_agent_with_tools())
    # asyncio.run(demo_multi_turn_agent())
    # asyncio.run(demo_agent_workflow())
    # asyncio.run(demo_agent_with_feedback())
    demo_agent_configurations()
