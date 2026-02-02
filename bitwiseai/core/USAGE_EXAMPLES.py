# -*- coding: utf-8 -*-
"""
Slash 命令和 Ralph Loop 使用示例

演示如何使用新增的 Slash 命令系统和 Ralph Loop 自动迭代功能
"""

# ============================================================================
# 基础使用
# ============================================================================

from bitwiseai import LLM, SkillManager, RAGEngine
from bitwiseai.core import ChatEngine


# 创建 ChatEngine
def create_engine():
    llm = LLM()
    skill_manager = SkillManager()
    rag_engine = RAGEngine()

    engine = ChatEngine(
        llm=llm,
        rag_engine=rag_engine,
        skill_manager=skill_manager,
        system_prompt="你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。",
        # 启用 Slash 命令和 Ralph Loop
        enable_slash=True,
        enable_ralph_loop=True,
        ralph_max_iterations=10,
    )
    return engine


# ============================================================================
# Slash 命令使用
# ============================================================================


def demo_slash_commands():
    """演示 Slash 命令的使用"""
    engine = create_engine()

    # 查看帮助
    response = engine.chat("/help")
    print(response)

    # 查看特定命令帮助
    response = engine.chat("/help yolo")
    print(response)

    # 切换 YOLO 模式
    response = engine.chat("/yolo on")
    print(response)

    # 清空上下文
    response = engine.chat("/clear")
    print(response)

    # 压缩上下文
    response = engine.chat("/compact")
    print(response)

    # 分析当前项目
    response = engine.chat("/init")
    print(response)


# ============================================================================
# Ralph Loop 使用
# ============================================================================


def demo_ralph_loop():
    """演示 Ralph Loop 自动迭代的使用"""
    engine = create_engine()

    # 使用 Ralph Loop 自动执行任务
    response = engine.chat(
        "分析当前目录下的所有 Python 文件，找出所有未使用的导入并生成报告。",
        use_ralph_loop=True,  # 启用自动迭代
    )
    print(response)


# ============================================================================
# 自定义 Slash 命令
# ============================================================================


def demo_custom_slash_command():
    """演示如何添加自定义 Slash 命令"""
    engine = create_engine()

    # 添加自定义命令
    def my_custom_command(engine, args: str) -> str:
        return f"自定义命令执行！参数: {args}"

    engine._slash_registry.register(
        name="mycmd",
        func=my_custom_command,
        description="我的自定义命令",
        aliases=["mc"],
    )

    # 使用自定义命令
    response = engine.chat("/mycmd hello")
    print(response)

    # 使用别名
    response = engine.chat("/mc world")
    print(response)


# ============================================================================
# 自定义 Flow 工作流
# ============================================================================


def demo_custom_flow():
    """演示如何创建和使用自定义 Flow 工作流"""
    from bitwiseai.core.flow import Flow, FlowNode, FlowEdge, FlowRunner

    engine = create_engine()

    # 创建自定义 Flow
    nodes = {
        "START": FlowNode(id="START", label="", kind="begin"),
        "TASK1": FlowNode(id="TASK1", label="首先，分析项目结构", kind="task"),
        "TASK2": FlowNode(id="TASK2", label="然后，生成文档", kind="task"),
        "DECISION": FlowNode(
            id="DECISION",
            label="文档是否完整？",
            kind="decision",
        ),
        "END": FlowNode(id="END", label="", kind="end"),
    }

    outgoing = {
        "START": [FlowEdge(src="START", dst="TASK1", label=None)],
        "TASK1": [FlowEdge(src="TASK1", dst="TASK2", label=None)],
        "TASK2": [FlowEdge(src="TASK2", dst="DECISION", label=None)],
        "DECISION": [
            FlowEdge(src="DECISION", dst="TASK2", label="NO"),
            FlowEdge(src="DECISION", dst="END", label="YES"),
        ],
        "END": [],
    }

    flow = Flow(nodes=nodes, outgoing=outgoing, begin_id="START", end_id="END")

    # 运行 Flow
    import asyncio

    runner = FlowRunner(flow, engine, max_moves=100)
    result = asyncio.run(runner.run())

    print(f"执行完成，步数: {result.step_count}")
    print(f"最终消息: {result.final_message}")


# ============================================================================
# 配置选项
# ============================================================================


def demo_configuration():
    """演示各种配置选项"""
    # 创建不同配置的引擎

    # 最小配置（禁用高级功能）
    minimal_engine = ChatEngine(
        llm=LLM(),
        enable_slash=False,
        enable_ralph_loop=False,
    )

    # 完整配置
    full_engine = ChatEngine(
        llm=LLM(),
        rag_engine=RAGEngine(),
        skill_manager=SkillManager(),
        system_prompt="自定义系统提示词",
        enable_slash=True,
        enable_ralph_loop=True,
        ralph_max_iterations=20,  # 更多迭代次数
    )

    # 运行时修改 Ralph Loop 配置
    full_engine.ralph_config.max_iterations = 50
    full_engine.ralph_config.auto_stop = True
    full_engine.ralph_config.stop_keywords = ["完成", "done", "结束"]


if __name__ == "__main__":
    # 运行演示
    print("=" * 60)
    print("Slash 命令演示")
    print("=" * 60)
    demo_slash_commands()

    print("\n" + "=" * 60)
    print("Ralph Loop 演示")
    print("=" * 60)
    demo_ralph_loop()
