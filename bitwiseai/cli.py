# -*- coding: utf-8 -*-
"""
BitwiseAI 命令行接口 v2.1

提供方便的命令行工具来使用 BitwiseAI 的所有功能
- 对话模式（支持 Agent 循环）
- 会话管理
- Skill 管理
- 工作流执行
"""
import argparse
import asyncio
import os
import sys
from typing import Optional, List

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from .bitwiseai import BitwiseAI


# 尝试导入 prompt_toolkit，如果不可用则使用简单模式
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.output import ColorDepth
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


# ============================================================================
# 对话模式
# ============================================================================


class ChatSession:
    """聊天会话管理"""

    def __init__(self, ai: BitwiseAI, use_rag: bool = True):
        self.ai = ai
        self.use_rag = use_rag
        self.messages: List[dict] = []  # 对话历史
        self.running = True

    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.messages.append({"role": role, "content": content})
        # 保留最近 20 条消息
        if len(self.messages) > 40:
            self.messages = self.messages[-40:]

    def get_history(self) -> List[dict]:
        """获取对话历史"""
        return self.messages.copy()

    def clear_history(self):
        """清空对话历史"""
        self.messages = []


def chat_mode(args):
    """对话模式"""
    try:
        ai = BitwiseAI(config_path=args.config)

        if args.query:
            # 单次查询（使用流式输出）
            print("AI: ", end="", flush=True)
            for token in ai.chat_stream(args.query, use_rag=args.use_rag):
                print(token, end="", flush=True)
            print()  # 换行
        else:
            # 交互模式
            if PROMPT_TOOLKIT_AVAILABLE:
                _interactive_mode_prompt_toolkit(ai, args)
            else:
                _interactive_mode_simple(ai, args)

    except Exception as e:
        print(f"初始化失败: {str(e)}", file=sys.stderr)
        sys.exit(1)


def _print_welcome():
    """打印欢迎信息"""
    print("=" * 60)
    print("BitwiseAI 对话模式")
    print("=" * 60)
    print("命令:")
    print("  /help           - 显示帮助")
    print("  /clear          - 清空上下文")
    print("  /sessions       - 列出所有会话")
    print("  /new <name>     - 创建新会话")
    print("  /switch <id>    - 切换会话")
    print("  /skills         - 列出所有 Skills")
    print("  /load <skill>   - 加载 Skill")
    print("  /unload <skill> - 卸载 Skill")
    print("  /skill-name     - 直接使用技能 (如 /asm-parser 解析这段代码)")
    print("  /agent          - 使用 Agent 模式")
    print("  /bye 或 /quit   - 退出 (也支持 Ctrl+C)")
    print("=" * 60)
    print()


def _show_help() -> str:
    """显示帮助信息"""
    return """
可用命令:
  /help           - 显示此帮助信息
  /clear          - 清空对话历史
  /sessions       - 列出所有会话
  /skills         - 列出所有 Skills
  /load <skill>   - 加载指定的 Skill
  /unload <skill> - 卸载指定的 Skill
  /skill-name     - 直接使用技能 (自动加载并使用技能上下文)
  /agent [query]  - 使用 Agent 模式执行任务
  /bye, /quit     - 退出对话 (也支持 Ctrl+C)

使用示例:
  /load asm-parser         # 加载汇编解析器技能
  /asm-parser 解析这段代码  # 直接使用技能 (自动加载)
  /agent 分析这段代码      # 使用 Agent 模式分析

输入技巧:
  - 直接输入文字即可开始对话
  - 使用 /skill-name <内容> 快速调用技能
  - 按 Ctrl+C 或输入 /bye 退出
"""


def _handle_slash_command(session: ChatSession, command: str) -> Optional[str]:
    """
    处理斜杠命令，返回 None 表示退出

    首先检查是否是技能名称，如果不是则处理内置命令
    """
    parts = command[1:].split(' ', 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    # 退出命令
    if cmd in ['bye', 'quit', 'exit']:
        return None

    # 检查是否是技能名称
    available_skills = session.ai.list_skills()
    if cmd in available_skills:
        # 自动加载技能
        skill = session.ai.skill_manager.get_skill(cmd)
        if skill and not skill.loaded:
            session.ai.load_skill(cmd)

        # 使用技能上下文进行对话
        actual_query = args if args else f"使用 {cmd} 技能帮助我"
        return _chat_with_skill(session, cmd, actual_query)

    # 内置命令
    if cmd == 'help' or cmd == '?':
        return _show_help()
    elif cmd == 'clear':
        session.clear_history()
        session.ai.chat_engine.history.clear() if hasattr(session.ai.chat_engine, 'history') else None
        return "✓ 上下文已清空"
    elif cmd == 'sessions':
        sessions = session.ai.list_sessions() if hasattr(session.ai, 'list_sessions') else []
        return f"会话列表 ({len(sessions)} 个):\n" + "\n".join(f"  - {s}" for s in sessions)
    elif cmd == 'skills':
        skills = session.ai.list_skills()
        loaded = session.ai.skill_manager.list_loaded_skills() if hasattr(session.ai, 'skill_manager') else []
        result = f"可用 Skills ({len(skills)} 个):\n"
        for s in skills:
            status = "✅" if s in loaded else "⏸️ "
            result += f"  {status} {s}\n"
        return result.strip()
    elif cmd == 'load' and args:
        success = session.ai.load_skill(args)
        return f"✓ Skill '{args}' 已加载" if success else f"❌ Skill '{args}' 加载失败"
    elif cmd == 'unload' and args:
        success = session.ai.unload_skill(args)
        return f"✓ Skill '{args}' 已卸载" if success else f"❌ Skill '{args}' 卸载失败"
    elif cmd == 'agent':
        # 切换到 Agent 模式
        return _agent_mode(session.ai, args or "帮我分析当前问题")
    else:
        return f"未知命令或技能: /{cmd}\n使用 /help 查看可用命令，或 /skills 查看可用技能。"


def _chat_with_skill(session: ChatSession, skill_name: str, query: str) -> str:
    """
    使用技能上下文进行对话

    Args:
        session: 聊天会话
        skill_name: 技能名称
        query: 用户问题

    Returns:
        AI 回答
    """
    skill = session.ai.skill_manager.get_skill(skill_name)
    if not skill:
        return f"技能 {skill_name} 不存在"

    if not skill.loaded:
        if not session.ai.load_skill(skill_name):
            return f"加载技能 {skill_name} 失败"
        skill = session.ai.skill_manager.get_skill(skill_name)

    try:
        # 使用技能内容作为上下文
        response = session.ai.chat(
            query,
            use_rag=session.use_rag,
            use_tools=True,
            history=session.get_history(),
            skill_context=skill.content
        )
        return response
    except Exception as e:
        error_msg = str(e)
        # 如果是 API 错误，提供更有用的错误信息
        if '2013' in error_msg or 'invalid' in error_msg.lower():
            return f"⚠️ LLM API 配置错误 (2013): 当前 LLM 可能不支持工具调用。\n\n" \
                   f"建议:\n" \
                   f"1. 检查 LLM 配置是否支持 function calling\n" \
                   f"2. 或者直接使用技能工具:\n" \
                   f'   例如: python -c "from bitwiseai.skills.asm-parser.scripts.tools import parse_asm_instruction; print(parse_asm_instruction(\'0x<指令>\'))"'
        else:
            return f"❌ 调用技能失败: {error_msg}"


def _agent_mode(ai, query: str) -> str:
    """Agent 模式"""
    try:
        # 使用 Agent 循环执行
        if hasattr(ai, 'chat_with_agent'):
            result = asyncio.run(ai.chat_with_agent(query))
            return result
        else:
            # 降级到普通模式
            return ai.chat(query, use_rag=True)
    except Exception as e:
        return f"Agent 执行失败: {e}"


def _interactive_mode_prompt_toolkit(ai: BitwiseAI, args):
    """使用 prompt_toolkit 的交互模式"""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter

    session = ChatSession(ai, args.use_rag)
    prompt_session = PromptSession(history=InMemoryHistory())
    auto_suggest = AutoSuggestFromHistory()

    # 创建命令补全
    commands = ['/help', '/clear', '/skills', '/load', '/unload', '/agent', '/bye', '/quit']
    skills = ai.list_skills()
    skill_commands = [f'/{s}' for s in skills]
    all_completions = commands + skill_commands
    completer = WordCompleter(all_completions, ignore_case=True)

    _print_welcome()

    while session.running:
        try:
            # 获取用户输入
            user_input = prompt_session.prompt(
                HTML('<style fg="cyan">你</style>: '),
                completer=completer,
                auto_suggest=auto_suggest,
            )

            if not user_input.strip():
                continue

            # 处理斜杠命令
            if user_input.startswith('/'):
                result = _handle_slash_command(session, user_input)
                if result is None:
                    print("\n再见！")
                    break
                print(result)
                continue

            # 正常对话
            print()

            # 流式获取响应
            print(HTML('<style fg="green">AI</style>: '), end="", flush=True)
            response = ""
            for token in ai.chat_stream(user_input, use_rag=args.use_rag, history=session.get_history()):
                print(token, end="", flush=True)
                response += token
            print()  # 换行
            print()

            # 更新历史
            session.add_message("user", user_input)
            session.add_message("assistant", response)

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except EOFError:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"错误: {str(e)}")


def _interactive_mode_simple(ai: BitwiseAI, args):
    """简单的交互模式（不依赖 prompt_toolkit）"""
    session = ChatSession(ai, args.use_rag)

    _print_welcome()

    while session.running:
        try:
            # 获取用户输入
            user_input = _get_user_input_simple()
            if not user_input:
                continue

            # 处理斜杠命令
            if user_input.startswith('/'):
                result = _handle_slash_command(session, user_input)
                if result is None:
                    print("\n再见！")
                    break
                print(result)
                continue

            # 正常对话
            print()
            print("AI: ", end="", flush=True)

            # 流式获取响应
            response = ""
            for token in ai.chat_stream(user_input, use_rag=args.use_rag, history=session.get_history()):
                print(token, end="", flush=True)
                response += token
            print()  # 换行
            print()

            # 更新历史
            session.add_message("user", user_input)
            session.add_message("assistant", response)

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"错误: {str(e)}")


def _get_user_input_simple() -> str:
    """获取用户输入（简单模式）"""
    import sys

    # 显示提示符
    sys.stdout.write("\033[1;36m你\033[0m: ")
    sys.stdout.flush()

    lines = []
    try:
        while True:
            line = sys.stdin.readline()
            if not line:  # EOF
                break

            line = line.rstrip('\n')

            # 空行结束多行输入
            if line == "" and lines:
                break

            lines.append(line)

            # 如果以反斜杠结尾，继续多行输入
            if line.endswith('\\'):
                sys.stdout.write("\033[1;36m  ...\033[0m ")
                sys.stdout.flush()
                lines[-1] = line[:-1]
            else:
                break

    except KeyboardInterrupt:
        print()
        return ""

    return "\n".join(lines).strip()


# ============================================================================
# Skill 管理模式
# ============================================================================


def skill_mode(args):
    """Skill 管理模式"""
    try:
        ai = BitwiseAI(config_path=args.config)

        if args.list:
            # 列出所有 Skills
            skills = ai.list_skills(loaded_only=args.loaded_only)
            print(f"可用 Skills ({len(skills)} 个):")
            for i, skill_name in enumerate(skills, 1):
                skill = ai.skill_manager.get_skill(skill_name)
                if skill:
                    status = "✅ 已加载" if skill.loaded else "⏸️ 未加载"
                    print(f"  {i}. {skill_name} ({status})")
                    if args.verbose:
                        print(f"     描述: {skill.description or '无描述'}")
                        n_tools = len(skill.tools) if skill.tools else 0
                        print(f"     工具: {n_tools} 个")

        elif args.load:
            # 加载 Skill
            success = ai.load_skill(args.load)
            if success:
                print(f"✅ Skill '{args.load}' 加载成功")
            else:
                print(f"❌ Skill '{args.load}' 加载失败")
                sys.exit(1)

        elif args.unload:
            # 卸载 Skill
            success = ai.unload_skill(args.unload)
            if success:
                print(f"✅ Skill '{args.unload}' 卸载成功")
            else:
                print(f"❌ Skill '{args.unload}' 卸载失败")
                sys.exit(1)

        elif args.search:
            # 搜索 Skills
            results = ai.search_skills(args.search, top_k=args.top_k)
            if results:
                print(f"找到 {len(results)} 个相关 Skills:")
                for i, result in enumerate(results, 1):
                    skill_name = result.get("skill_name", "未知")
                    description = result.get("description", "无描述")
                    score = result.get("score", 0.0)
                    print(f"  {i}. {skill_name} (相似度: {score:.4f})")
                    print(f"     {description}")
            else:
                print("未找到相关 Skills")

        elif args.add_dir:
            # 添加外部目录
            success = ai.add_skills_directory(args.add_dir)
            if success:
                print(f"✅ 已添加目录: {args.add_dir}")
            else:
                print(f"❌ 添加目录失败: {args.add_dir}")
                sys.exit(1)

        else:
            print("请指定操作。使用 --help 查看帮助。")

    except Exception as e:
        print(f"操作失败: {str(e)}", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# Agent 模式
# ============================================================================


def agent_mode(args):
    """Agent 模式"""
    try:
        ai = BitwiseAI(config_path=args.config)

        # 使用 Agent 循环执行
        if hasattr(ai, 'chat_with_agent'):
            if args.stream:
                # 流式输出
                print("AI: ", end="", flush=True)
                async def run_stream():
                    async for token in ai.chat_with_agent_stream(args.query):
                        print(token, end="", flush=True)
                    print()  # 换行

                asyncio.run(run_stream())
            else:
                # 非流式
                response = asyncio.run(ai.chat_with_agent(args.query))
                print(response)
        else:
            # 降级到普通模式
            print("⚠️ Agent 模式不可用，使用普通对话模式")
            response = ai.chat(args.query, use_rag=args.use_rag)
            print(response)

    except Exception as e:
        print(f"Agent 执行失败: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ============================================================================
# 会话管理模式
# ============================================================================


def session_mode(args):
    """会话管理模式"""
    try:
        ai = BitwiseAI(config_path=args.config)

        if args.list:
            # 列出所有会话
            if hasattr(ai, 'list_sessions'):
                sessions = ai.list_sessions()
                print(f"会话列表 ({len(sessions)} 个):")
                for i, session_info in enumerate(sessions, 1):
                    print(f"  {i}. {session_info.get('name', '未命名')}")
                    print(f"     ID: {session_info.get('session_id', '未知')[:16]}...")
                    print(f"     消息数: {session_info.get('message_count', 0)}")
            else:
                print("❌ 会话功能不可用")

        elif args.new:
            # 创建新会话
            if hasattr(ai, 'new_session'):
                session = asyncio.run(ai.new_session(args.new))
                print(f"✅ 已创建新会话: {session.info.name}")
                print(f"   ID: {session.info.session_id}")
            else:
                print("❌ 会话功能不可用")

        elif args.switch:
            # 切换会话
            if hasattr(ai, 'switch_session'):
                session = asyncio.run(ai.switch_session(args.switch))
                if session:
                    print(f"✅ 已切换到会话: {session.info.name}")
                else:
                    print(f"❌ 会话不存在: {args.switch}")
            else:
                print("❌ 会话功能不可用")

        elif args.delete:
            # 删除会话
            if hasattr(ai, 'delete_session'):
                success = asyncio.run(ai.delete_session(args.delete))
                if success:
                    print(f"✅ 已删除会话: {args.delete}")
                else:
                    print(f"❌ 删除失败: {args.delete}")
            else:
                print("❌ 会话功能不可用")

        else:
            print("请指定操作。使用 --help 查看帮助。")

    except Exception as e:
        print(f"操作失败: {str(e)}", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# 配置生成模式
# ============================================================================


def config_mode(args):
    """配置生成模式"""
    import json

    config_path = os.path.expanduser(args.config)
    config_dir = os.path.dirname(config_path)
    os.makedirs(config_dir, exist_ok=True)

    if os.path.exists(config_path) and not args.force:
        print(f"配置文件已存在: {config_path}")
        print("使用 --force 覆盖现有配置")
        return

    # 生成默认配置
    config = {
        "_comment": "BitwiseAI 配置文件",
        "_note": "请编辑此文件配置 API 密钥和模型参数",
        "llm": {
            "model": "glm-4-flash",
            "api_key": "your-api-key-here",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "temperature": 0.7,
            "_llm_examples": {
                "GLM-4": {"model": "glm-4-flash", "base_url": "https://open.bigmodel.cn/api/paas/v4"},
                "MiniMax": {"model": "MiniMax-M2.1", "base_url": "https://api.minimaxi.com/v1"},
                "OpenAI": {"model": "gpt-4o-mini", "base_url": "https://api.openai.com/v1"}
            }
        },
        "embedding": {
            "model": "text-embedding-3-small",
            "api_key": "your-embedding-api-key-here",
            "base_url": "https://api.openai.com/v1",
        },
        "vector_db": {
            "db_file": "~/.bitwiseai/milvus_data.db",
            "collection_name": "bitwiseai",
            "embedding_dim": 1536,
            "similarity_threshold": 0.85,
        },
        "system_prompt": "你是 BitwiseAI，专注于硬件指令验证和调试日志分析的 AI 助手。",
        "skills": {
            "auto_load": [],
            "external_directories": ["~/.bitwiseai/skills"],
        },
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"✅ 配置文件已生成: {config_path}")
    print(f"\n请编辑配置文件，设置以下参数：")
    print(f"  llm.api_key - LLM API 密钥")
    print(f"  llm.base_url - LLM API 地址")
    print(f"  llm.model - 模型名称")
    print(f"\n配置示例：")
    print(f"  GLM-4:")
    print(f"    model: glm-4-flash")
    print(f"    base_url: https://open.bigmodel.cn/api/paas/v4")
    print(f"  MiniMax:")
    print(f"    model: MiniMax-M2.1")
    print(f"    base_url: https://api.minimaxi.com/v1")


# ============================================================================
# 主函数
# ============================================================================


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        prog="bitwiseai",
        description="BitwiseAI - AI 驱动的硬件调试和日志分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 对话模式
  bitwiseai chat "什么是 MUL 指令？"
  bitwiseai chat  # 交互模式，支持 /skill-name 语法

  # Agent 模式（自动执行任务）
  bitwiseai agent "分析代码并生成报告"

  # Skill 管理
  bitwiseai skill --list
  bitwiseai skill --load asm-parser
  bitwiseai skill --search "代码分析"

  # 会话管理
  bitwiseai session --list
  bitwiseai session --new "项目讨论"
  bitwiseai session --switch <session-id>

  # 生成配置文件
  bitwiseai config --force
        """,
    )

    # 全局参数
    parser.add_argument(
        "--config",
        default="~/.bitwiseai/config.json",
        help="配置文件路径 (默认: ~/.bitwiseai/config.json)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="BitwiseAI 2.1.0",
    )

    # 子命令
    subparsers = parser.add_subparsers(dest="mode", help="操作模式")

    # 对话模式
    chat_parser = subparsers.add_parser("chat", help="对话模式")
    chat_parser.add_argument("query", nargs="?", help="查询内容（不提供则进入交互模式）")
    chat_parser.add_argument("--use-rag", action="store_true", help="使用 RAG 查询文档")

    # Agent 模式
    agent_parser = subparsers.add_parser("agent", help="Agent 模式（自动执行任务）")
    agent_parser.add_argument("query", help="任务描述")
    agent_parser.add_argument("--stream", action="store_true", help="流式输出")
    agent_parser.add_argument("--use-rag", action="store_true", help="使用 RAG")

    # Skill 管理模式
    skill_parser = subparsers.add_parser("skill", help="Skill 管理")
    skill_parser.add_argument("--list", action="store_true", help="列出所有 Skills")
    skill_parser.add_argument("--loaded-only", action="store_true", help="仅显示已加载的")
    skill_parser.add_argument("--verbose", action="store_true", help="显示详细信息")
    skill_parser.add_argument("--load", help="加载指定的 Skill")
    skill_parser.add_argument("--unload", help="卸载指定的 Skill")
    skill_parser.add_argument("--search", help="搜索 Skills")
    skill_parser.add_argument("--top-k", type=int, default=5, help="搜索返回数量")
    skill_parser.add_argument("--add-dir", help="添加外部技能目录")

    # 会话管理模式
    session_parser = subparsers.add_parser("session", help="会话管理")
    session_parser.add_argument("--list", action="store_true", help="列出所有会话")
    session_parser.add_argument("--new", help="创建新会话（指定名称）")
    session_parser.add_argument("--switch", help="切换到指定会话")
    session_parser.add_argument("--delete", help="删除指定会话")

    # 配置生成模式
    config_parser = subparsers.add_parser("config", help="生成配置文件")
    config_parser.add_argument("--force", action="store_true", help="覆盖现有配置")

    args = parser.parse_args()

    # 执行对应模式
    if args.mode == "chat":
        chat_mode(args)
    elif args.mode == "agent":
        agent_mode(args)
    elif args.mode == "skill":
        skill_mode(args)
    elif args.mode == "session":
        session_mode(args)
    elif args.mode == "config":
        config_mode(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
