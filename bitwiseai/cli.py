# -*- coding: utf-8 -*-
"""
BitwiseAI 命令行接口

提供方便的命令行工具来使用 BitwiseAI
"""
import argparse
import sys
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from .bitwiseai import BitwiseAI
from .log_parser import LogParser
from .verifier import InstructionVerifier
from .interfaces import AnalysisTask


def chat_mode(args):
    """对话模式"""
    try:
        ai = BitwiseAI(config_path=args.config)
        
        if args.query:
            # 单次查询（默认启用工具调用）
            response = ai.chat(args.query, use_rag=args.use_rag, use_tools=True)
            print(response)
        else:
            # 交互模式
            print("=" * 60)
            print("BitwiseAI 对话模式")
            print("输入 'quit' 或 'exit' 退出")
            print("=" * 60)
            print()
            
            history = []
            while True:
                try:
                    user_input = input("你: ").strip()
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("再见！")
                        break
                    
                    response = ai.chat(user_input, use_rag=args.use_rag, use_tools=True, history=history)
                    print(f"\nAI: {response}\n")
                    
                    # 更新历史
                    history.append({"role": "user", "content": user_input})
                    history.append({"role": "assistant", "content": response})
                    
                except KeyboardInterrupt:
                    print("\n\n再见！")
                    break
                except Exception as e:
                    print(f"错误: {str(e)}")
    
    except Exception as e:
        print(f"初始化失败: {str(e)}", file=sys.stderr)
        sys.exit(1)


def analyze_mode(args):
    """分析模式"""
    try:
        ai = BitwiseAI(config_path=args.config)
        
        # 加载日志文件
        if not args.log_file or not os.path.exists(args.log_file):
            print(f"错误: 日志文件不存在: {args.log_file}", file=sys.stderr)
            sys.exit(1)
        
        print(f"加载日志文件: {args.log_file}")
        ai.load_log_file(args.log_file)
        
        # 加载规范文档（如果指定）
        if args.spec:
            print(f"加载规范文档: {args.spec}")
            ai.load_specification(args.spec)
        
        # 根据分析类型执行
        if args.type == "pe_instruction":
            # PE 指令验证
            print("\n执行 PE 指令验证...")
            
            from .interfaces import AnalysisTask
            
            class PEInstructionTask(AnalysisTask):
                def __init__(self):
                    super().__init__(
                        name="PE_Instruction_Verification",
                        parser=LogParser(),
                        verifier=InstructionVerifier()
                    )
                
                def analyze(self, context, parsed_data):
                    results = []
                    if isinstance(self.parser, LogParser):
                        instructions = self.parser.instructions
                        if isinstance(self.verifier, InstructionVerifier):
                            verify_results = self.verifier.verify_all(instructions)
                            from .interfaces import AnalysisResult
                            for vr in verify_results:
                                results.append(AnalysisResult(
                                    status=vr.status.value.lower(),
                                    message=str(vr),
                                    data={}
                                ))
                    return results
            
            task = PEInstructionTask()
            ai.register_task(task)
            results = ai.execute_task(task)
            
            # 打印结果
            print(f"\n分析完成，共 {len(results)} 条结果")
            
            fail_count = sum(1 for r in results if r.status == "fail")
            pass_count = sum(1 for r in results if r.status == "pass")
            
            print(f"  通过: {pass_count}")
            print(f"  失败: {fail_count}")
            
            if args.show_details:
                print("\n详细结果:")
                for i, result in enumerate(results, 1):
                    if result.status == "fail":
                        print(f"  [{i}] {result.message}")
        
        elif args.type == "custom":
            # 自定义分析
            if args.query:
                print(f"\n使用 LLM 分析日志...")
                response = ai.ask_about_log(args.query)
                print(f"\n分析结果:\n{response}")
            else:
                print("错误: 自定义分析需要 --query 参数", file=sys.stderr)
                sys.exit(1)
        
        # 生成报告
        if args.output:
            print(f"\n生成报告: {args.output}")
            ai.save_report(args.output, format=args.format)
    
    except Exception as e:
        print(f"分析失败: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def query_spec_mode(args):
    """查询规范模式"""
    try:
        ai = BitwiseAI(config_path=args.config)
        
        # 加载规范文档
        if args.spec:
            print(f"加载规范文档: {args.spec}")
            ai.load_specification(args.spec)
        
        # 查询
        if args.query:
            print(f"\n查询: {args.query}")
            context = ai.query_specification(args.query, top_k=args.top_k)
            print(f"\n相关文档:\n{context}")
            
            if args.use_llm:
                print("\n使用 LLM 生成回答...")
                response = ai.chat(args.query, use_rag=True)
                print(f"\n回答:\n{response}")
        else:
            print("错误: 需要 --query 参数", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(f"查询失败: {str(e)}", file=sys.stderr)
        sys.exit(1)


def tool_mode(args):
    """Skill 和工具管理模式"""
    try:
        ai = BitwiseAI(config_path=args.config)
        
        if args.list_skills:
            # 列出所有 skills
            skills = ai.list_skills(loaded_only=args.loaded_only)
            print(f"可用 Skills ({len(skills)} 个):")
            for i, skill_name in enumerate(skills, 1):
                skill = ai.skill_manager.get_skill(skill_name)
                if skill:
                    status = "✅ 已加载" if skill.loaded else "⏸️ 未加载"
                    print(f"  {i}. {skill_name} ({status}) - {skill.description or '无描述'}")
                else:
                    print(f"  {i}. {skill_name} (❓ 未知)")
        
        elif args.load_skill:
            # 加载 skill
            skill_name = args.load_skill
            print(f"加载 Skill: {skill_name}")
            success = ai.load_skill(skill_name)
            if success:
                print(f"✅ Skill '{skill_name}' 加载成功")
            else:
                print(f"❌ Skill '{skill_name}' 加载失败")
                sys.exit(1)
        
        elif args.unload_skill:
            # 卸载 skill
            skill_name = args.unload_skill
            print(f"卸载 Skill: {skill_name}")
            success = ai.unload_skill(skill_name)
            if success:
                print(f"✅ Skill '{skill_name}' 卸载成功")
            else:
                print(f"❌ Skill '{skill_name}' 卸载失败")
                sys.exit(1)
        
        elif args.list_tools:
            # 列出所有工具
            tools = ai.list_tools()
            print(f"可用工具 ({len(tools)} 个，来自已加载的 Skills):")
            for i, tool_name in enumerate(tools, 1):
                print(f"  {i}. {tool_name}")
        
        elif args.invoke:
            # 调用工具
            tool_name = args.invoke
            tool_args = args.args or []
            
            print(f"调用工具: {tool_name}")
            print(f"参数: {tool_args}")
            
            result = ai.invoke_tool(tool_name, *tool_args)
            print(f"\n结果: {result}")
        
        else:
            print("错误: 需要指定操作（--list-skills, --load-skill, --unload-skill, --list-tools, --invoke）", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(f"操作失败: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        prog="bitwiseai",
        description="BitwiseAI - 硬件调试和日志分析的 AI 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 对话模式
  bitwiseai --chat "什么是 MUL 指令？"
  bitwiseai --chat  # 交互模式
  
  # 分析 PE 指令日志
  bitwiseai --analyze --log pe_registers.log --type pe_instruction
  
  # 使用 LLM 分析日志
  bitwiseai --analyze --log debug.log --type custom --query "找出所有错误"
  
  # 查询规范文档
  bitwiseai --query-spec --spec ./docs/ --query "MUL 指令参数"
  
  # Skill 和工具管理
  bitwiseai --tool --list-skills
  bitwiseai --tool --load-skill asm_parser
  bitwiseai --tool --list-tools
  bitwiseai --tool --invoke parse_asm_instruction 0x0003000000000181
        """
    )
    
    # 全局参数
    parser.add_argument(
        "--config",
        default="~/.bitwiseai/config.json",
        help="配置文件路径 (默认: ~/.bitwiseai/config.json)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="BitwiseAI 2.0.0"
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest="mode", help="操作模式")
    
    # 对话模式
    chat_parser = subparsers.add_parser("chat", help="对话模式")
    chat_parser.add_argument(
        "query",
        nargs="?",
        help="查询内容（不提供则进入交互模式）"
    )
    chat_parser.add_argument(
        "--use-rag",
        action="store_true",
        help="使用 RAG 查询规范文档"
    )
    
    # 分析模式
    analyze_parser = subparsers.add_parser("analyze", help="日志分析模式")
    analyze_parser.add_argument(
        "--log",
        dest="log_file",
        required=True,
        help="日志文件路径"
    )
    analyze_parser.add_argument(
        "--type",
        choices=["pe_instruction", "custom"],
        default="custom",
        help="分析类型"
    )
    analyze_parser.add_argument(
        "--spec",
        help="规范文档路径（用于 RAG）"
    )
    analyze_parser.add_argument(
        "--query",
        help="分析查询（用于 custom 类型）"
    )
    analyze_parser.add_argument(
        "--output",
        help="报告输出路径"
    )
    analyze_parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="markdown",
        help="报告格式"
    )
    analyze_parser.add_argument(
        "--show-details",
        action="store_true",
        help="显示详细结果"
    )
    
    # 查询规范模式
    spec_parser = subparsers.add_parser("query-spec", help="查询规范文档")
    spec_parser.add_argument(
        "--spec",
        required=True,
        help="规范文档路径"
    )
    spec_parser.add_argument(
        "--query",
        required=True,
        help="查询内容"
    )
    spec_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="返回结果数量"
    )
    spec_parser.add_argument(
        "--use-llm",
        action="store_true",
        help="使用 LLM 生成回答"
    )
    
    # Skill 和工具模式
    tool_parser = subparsers.add_parser("tool", help="Skill 和工具管理")
    tool_parser.add_argument(
        "--list-skills",
        action="store_true",
        help="列出所有 Skills"
    )
    tool_parser.add_argument(
        "--loaded-only",
        action="store_true",
        help="仅显示已加载的 Skills（与 --list-skills 一起使用）"
    )
    tool_parser.add_argument(
        "--load-skill",
        help="加载指定的 Skill"
    )
    tool_parser.add_argument(
        "--unload-skill",
        help="卸载指定的 Skill"
    )
    tool_parser.add_argument(
        "--list-tools",
        action="store_true",
        help="列出所有工具（来自已加载的 Skills）"
    )
    tool_parser.add_argument(
        "--invoke",
        help="调用工具"
    )
    tool_parser.add_argument(
        "--args",
        nargs="*",
        help="工具参数"
    )
    
    # 兼容旧的命令行格式（直接使用 --chat）
    parser.add_argument(
        "--chat",
        dest="direct_chat",
        nargs="?",
        const="",
        help="对话模式（快捷方式）"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="分析模式（快捷方式）"
    )
    parser.add_argument(
        "--log",
        dest="direct_log_file",
        help="日志文件（快捷方式）"
    )
    parser.add_argument(
        "--query-spec",
        action="store_true",
        help="查询规范模式（快捷方式）"
    )
    parser.add_argument(
        "--tool",
        action="store_true",
        help="工具模式（快捷方式）"
    )
    
    args = parser.parse_args()
    
    # 处理快捷方式
    if args.direct_chat is not None:
        args.mode = "chat"
        args.query = args.direct_chat if args.direct_chat else None
        args.use_rag = False
    elif args.analyze:
        args.mode = "analyze"
        args.log_file = args.direct_log_file
        args.type = "custom"
        args.spec = None
        args.query = None
        args.output = None
        args.format = "markdown"
        args.show_details = False
    elif args.query_spec:
        args.mode = "query-spec"
    elif args.tool:
        args.mode = "tool"
    
    # 执行对应模式
    if args.mode == "chat":
        chat_mode(args)
    elif args.mode == "analyze":
        analyze_mode(args)
    elif args.mode == "query-spec":
        query_spec_mode(args)
    elif args.mode == "tool":
        tool_mode(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
