# -*- coding: utf-8 -*-
"""
BitwiseAI Web Server
基于 Gradio 的 Web 服务
"""
import os
import sys
import gradio as gr
from pathlib import Path

# 添加父目录到路径以导入 bitwiseai
sys.path.insert(0, str(Path(__file__).parent.parent))

from bitwiseai import BitwiseAI
from pages.chat import create_chat_interface
from pages.tools import create_tools_interface
from pages.rag import create_rag_interface


class BitwiseAIWeb:
    """BitwiseAI Web 应用"""

    def __init__(self):
        """初始化 Web 应用"""
        self.ai = None
        self.chat_history = []
        self._init_ai()

    def _init_ai(self):
        """初始化 BitwiseAI 实例"""
        try:
            self.ai = BitwiseAI()
            print("✓ BitwiseAI 初始化成功")
        except Exception as e:
            print(f"⚠️ BitwiseAI 初始化失败: {e}")
            print("请先运行: bitwiseai --generate-config")
            self.ai = None

    def create_app(self):
        """创建 Gradio 应用"""
        if not self.ai:
            # 如果 AI 未初始化，显示错误页面
            with gr.Blocks(
                title="BitwiseAI - 硬件调试 AI 助手",
                theme=gr.themes.Soft(),
                css=self._get_custom_css()
            ) as app:
                gr.Markdown("# ⚠️ BitwiseAI 未初始化")
                gr.Markdown("请先配置 API 密钥：")
                gr.Code("bitwiseai --generate-config", language="bash")
            return app

        # 创建多标签页应用
        with gr.Blocks(
            title="BitwiseAI - 硬件调试 AI 助手",
            theme=gr.themes.Soft(),
            css=self._get_custom_css()
        ) as app:
            # 标题栏
            gr.HTML("""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0;">🔧 BitwiseAI</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">硬件指令验证和调试日志分析的 AI 助手</p>
            </div>
            """)

            # 主要功能区域
            with gr.Tabs() as tabs:
                # 聊天对话页
                with gr.Tab("💬 AI 对话"):
                    chat_interface = create_chat_interface(self)
                    self.chat_interface = chat_interface

                # 工具管理页
                with gr.Tab("🔧 工具管理"):
                    tools_interface = create_tools_interface(self)

                # RAG 文档管理页
                with gr.Tab("📚 知识库"):
                    rag_interface = create_rag_interface(self)

            # 页脚
            gr.HTML("""
            <div style="text-align: center; padding: 10px; color: #666; font-size: 0.9em;">
                <p>BitwiseAI - 让 AI 成为你的调试助手 🚀</p>
            </div>
            """)

        return app

    @staticmethod
    def _get_custom_css():
        """获取自定义 CSS 样式"""
        return """
        /* 聊天气泡样式 */
        .message.user {
            background-color: #667eea !important;
            color: white !important;
        }
        .message.bot {
            background-color: #f3f4f6 !important;
        }

        /* 工具卡片样式 */
        .tool-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            background-color: #f9fafb;
        }

        /* 状态标签样式 */
        .status-pass {
            color: #10b981;
            font-weight: bold;
        }
        .status-fail {
            color: #ef4444;
            font-weight: bold;
        }
        .status-warning {
            color: #f59e0b;
            font-weight: bold;
        }

        /* 标题样式 */
        h1, h2, h3 {
            color: #1f2937;
        }

        /* 按钮样式 */
        .gr-button-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        }
        """


def main():
    """启动 Web 服务"""
    import argparse

    parser = argparse.ArgumentParser(description="BitwiseAI Web Server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="服务器监听地址"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="服务器监听端口"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="创建公共链接（通过 Gradio 隧道）"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )

    args = parser.parse_args()

    # 创建应用
    web_app = BitwiseAIWeb()
    app = web_app.create_app()

    # 启动服务
    print("=" * 50)
    print("BitwiseAI Web 服务启动中...")
    print(f"访问地址: http://{args.host}:{args.port}")
    print("=" * 50)

    app.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        debug=args.debug,
        show_error=True
    )


if __name__ == "__main__":
    main()
