# -*- coding: utf-8 -*-
"""
日志分析模块
"""
import gradio as gr
from pathlib import Path


def create_logs_interface(web_app):
    """
    创建日志分析界面

    Args:
        web_app: BitwiseAIWeb 实例

    Returns:
        日志分析界面组件
    """
    ai = web_app.ai

    def load_log_file(file_path: str):
        """加载日志文件"""
        if not ai:
            return "❌ BitwiseAI 未初始化", "", ""

        if not file_path or not file_path.strip():
            return "请输入日志文件路径", "", ""

        file_path = file_path.strip()

        if not Path(file_path).exists():
            return f"❌ 文件不存在: {file_path}", "", ""

        try:
            ai.load_log_file(file_path)

            # 读取文件内容预览
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            preview = content[:2000]
            if len(content) > 2000:
                preview += "\n\n... (文件较长，仅显示前 2000 字符)"

            msg = f"✅ 日志文件已加载\n\n**文件:** {file_path}\n**大小:** {len(content)} 字符"
            return msg, preview, file_path
        except Exception as e:
            return f"❌ 加载失败: {str(e)}", "", ""

    def analyze_log(question: str):
        """使用 AI 分析日志"""
        if not ai:
            return "❌ BitwiseAI 未初始化", ""

        if not ai.log_file_path:
            return "⚠️ 请先加载日志文件", ""

        if not question or not question.strip():
            return "请输入问题", ""

        try:
            response = ai.ask_about_log(question)
            return f"✅ 分析完成\n\n**问题:** {question}\n\n**回答:**\n\n{response}", ""
        except Exception as e:
            return f"❌ 分析失败: {str(e)}", ""

    def parse_and_verify():
        """解析和验证日志"""
        if not ai:
            return "❌ BitwiseAI 未初始化", ""

        if not ai.log_file_path:
            return "⚠️ 请先加载日志文件", ""

        try:
            from bitwiseai.log_parser import LogParser
            from bitwiseai.verifier import InstructionVerifier

            # 解析日志
            parser = LogParser()
            parser.parse_file(ai.log_file_path)

            instructions = parser.instructions
            msg = f"📊 解析结果\n\n找到 {len(instructions)} 条指令\n\n"

            # 验证指令
            verifier = InstructionVerifier()
            results = verifier.verify_all(instructions)

            # 统计结果
            passed = sum(1 for r in results if r.status.value == "pass")
            failed = sum(1 for r in results if r.status.value == "fail")
            warning = sum(1 for r in results if r.status.value == "warning")

            msg += f"| 状态 | 数量 |\n|------|------|\n"
            msg += f"| ✅ 通过 | {passed} |\n"
            msg += f"| ❌ 失败 | {failed} |\n"
            msg += f"| ⚠️ 警告 | {warning} |\n\n"

            # 显示详细信息
            if failed > 0 or warning > 0:
                msg += "**问题详情:**\n\n"
                for r in results:
                    if r.status.value in ["fail", "warning"]:
                        msg += f"- {r}\n"

            return msg, ""
        except Exception as e:
            return f"❌ 解析失败: {str(e)}", ""

    def generate_report(format_type: str):
        """生成分析报告"""
        if not ai:
            return "❌ BitwiseAI 未初始化", ""

        try:
            report = ai.generate_report(format=format_type)

            if format_type == "json":
                return f"```json\n{report}\n```", ""
            else:
                return report, ""
        except Exception as e:
            return f"❌ 生成报告失败: {str(e)}", ""

    # 创建日志分析界面
    with gr.Row() as interface:
        with gr.Column(scale=2):
            # 文件加载
            gr.Markdown("### 📁 加载日志文件")

            log_file_path = gr.Textbox(
                label="日志文件路径",
                placeholder="/path/to/logfile.log",
                value=""
            )

            load_log_btn = gr.Button("加载日志文件", variant="primary")

            load_result = gr.Markdown(
                label="加载结果"
            )

            gr.Markdown("---")

            # 日志预览
            gr.Markdown("### 👁️ 日志预览")

            log_preview = gr.Textbox(
                label="日志内容预览",
                lines=15,
                interactive=False
            )

            gr.Markdown("---")

            # AI 分析
            gr.Markdown("### 🤖 AI 日志分析")

            log_question = gr.Textbox(
                label="问题",
                placeholder="输入关于日志的问题，例如：找出所有的错误信息...",
                lines=2
            )

            analyze_btn = gr.Button("分析", variant="primary")

            analysis_result = gr.Markdown(
                label="分析结果"
            )

            with gr.Row():
                parse_verify_btn = gr.Button("解析并验证指令", variant="secondary")
                report_btn = gr.Button("生成报告", variant="secondary")

            report_format = gr.Radio(
                choices=["markdown", "json", "text"],
                value="markdown",
                label="报告格式"
            )

            operation_result = gr.Markdown(
                label="操作结果"
            )

        with gr.Column(scale=1):
            # 快捷操作
            gr.Markdown("### ⚡ 快捷操作")

            gr.Markdown("""
            **日志分析流程:**

            1. **加载文件** - 选择日志文件
            2. **预览内容** - 查看日志概览
            3. **AI 分析** - 提问获取洞察
            4. **指令验证** - 验证硬件指令
            5. **生成报告** - 导出分析结果
            """)

            gr.Markdown("---")

            # 常见问题
            gr.Markdown("### ❓ 常见问题")

            common_questions = gr.Radio(
                choices=[
                    "日志中有哪些错误？",
                    "找出所有的指令执行失败",
                    "统计指令类型分布",
                    "找出异常的寄存器值",
                    "分析执行时间"
                ],
                label="点击选择常见问题",
                value=None
            )

            ask_common_btn = gr.Button("提问", size="sm")

            gr.Markdown("---")

            # 统计信息
            gr.Markdown("### 📊 当前状态")

            log_status = gr.Markdown(
                """
| 项目 | 状态 |
|------|------|
| 日志文件 | 未加载 |
| 指令数量 | - |
| 已注册任务 | - |
                """,
                label="日志状态"
            )

            refresh_status_btn = gr.Button("刷新状态", size="sm")

    # 事件绑定
    load_log_btn.click(
        fn=load_log_file,
        inputs=[log_file_path],
        outputs=[load_result, log_preview, log_file_path]
    ).then(
        fn=lambda: get_log_status(ai),
        outputs=log_status
    )

    analyze_btn.click(
        fn=analyze_log,
        inputs=[log_question],
        outputs=[analysis_result, log_question]
    )

    parse_verify_btn.click(
        fn=parse_and_verify,
        outputs=[operation_result, gr.State()]
    )

    report_btn.click(
        fn=generate_report,
        inputs=[report_format],
        outputs=[operation_result, gr.State()]
    )

    ask_common_btn.click(
        fn=lambda q: analyze_log(q),
        inputs=[common_questions],
        outputs=[analysis_result, common_questions]
    )

    refresh_status_btn.click(
        fn=lambda: get_log_status(ai),
        outputs=log_status
    )

    return interface


def get_log_status(ai) -> str:
    """获取日志状态"""
    if not ai:
        return """
| 项目 | 状态 |
|------|------|
| BitwiseAI | ❌ 未初始化 |
        """

    if ai.log_file_path:
        try:
            from bitwiseai.log_parser import LogParser
            parser = LogParser()
            parser.parse_file(ai.log_file_path)
            instruction_count = len(parser.instructions)

            return f"""
| 项目 | 状态 |
|------|------|
| 日志文件 | ✅ 已加载 |
| 文件路径 | `{ai.log_file_path}` |
| 指令数量 | {instruction_count} |
| 已注册任务 | {len(ai.tasks)} 个 |
            """
        except:
            return f"""
| 项目 | 状态 |
|------|------|
| 日志文件 | ✅ 已加载 |
| 文件路径 | `{ai.log_file_path}` |
| 解析状态 | ⚠️ 无法解析 |
            """
    else:
        return """
| 项目 | 状态 |
|------|------|
| 日志文件 | ⚠️ 未加载 |
| 指令数量 | - |
| 已注册任务 | {0} 个 |
        """.format(len(ai.tasks))
