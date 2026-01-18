# -*- coding: utf-8 -*-
"""
RAG 知识库管理模块
"""
import gradio as gr
from pathlib import Path
import time


def create_rag_interface(web_app):
    """
    创建 RAG 知识库管理界面

    Args:
        web_app: BitwiseAIWeb 实例

    Returns:
        RAG 管理界面组件
    """
    ai = web_app.ai

    def get_vector_db_info():
        """获取向量数据库信息"""
        if not ai:
            return "❌ BitwiseAI 未初始化"

        try:
            # 获取集合信息
            count = ai.vector_db.collection.num_entities
            info = f"""
| 项目 | 值 |
|------|-----|
| 集合名称 | `{ai.vector_db.collection_name}` |
| 文档数量 | {count} |
| 向量维度 | {ai.vector_db.embedding_dim} |
| 数据库文件 | `{ai.vector_db.db_file}` |
            """
            return info
        except Exception as e:
            return f"❌ 获取信息失败: {str(e)}"

    def load_folder(folder_path: str):
        """加载文件夹中的文档"""
        if not ai:
            return "❌ BitwiseAI 未初始化", "", ""

        if not folder_path or not folder_path.strip():
            return "请输入文件夹路径", "", ""

        folder_path = folder_path.strip()

        if not Path(folder_path).exists():
            return f"❌ 文件夹不存在: {folder_path}", "", ""

        try:
            result = ai.load_documents(folder_path)
            total = result.get("total", 0)
            inserted = result.get("inserted", 0)
            skipped = result.get("skipped", 0)
            msg = f"✅ 成功加载文件夹: {folder_path}\n\n"
            msg += f"- 总文档片段数: {total}\n"
            msg += f"- 插入片段数: {inserted}\n"
            if skipped > 0:
                msg += f"- 跳过重复片段数: {skipped}\n"
            return msg, "", ""
        except Exception as e:
            return f"❌ 加载失败: {str(e)}", "", ""

    def load_text(text_content: str):
        """加载文本内容"""
        if not ai:
            return "❌ BitwiseAI 未初始化", ""

        if not text_content or not text_content.strip():
            return "请输入文本内容", ""

        try:
            count = ai.add_text(text_content)
            msg = f"✅ 成功添加文本\n\n插入了 {count} 个文档片段到知识库"
            return msg, ""
        except Exception as e:
            return f"❌ 添加失败: {str(e)}", ""

    def query_knowledge(query: str, top_k: int):
        """查询知识库"""
        if not ai:
            return "❌ BitwiseAI 未初始化", "", ""

        if not query or not query.strip():
            return "请输入查询内容", "", ""

        try:
            results = ai.query_specification(query, top_k=top_k)

            if not results:
                return f"⚠️ 未找到相关内容\n\n查询: {query}", "", ""

            return f"✅ 查询成功\n\n**查询:** {query}\n\n**相关内容:**\n\n{results}", "", ""
        except Exception as e:
            return f"❌ 查询失败: {str(e)}", "", ""

    def clear_db():
        """清空知识库"""
        if not ai:
            return "❌ BitwiseAI 未初始化"

        try:
            ai.clear_vector_db()
            return "✅ 知识库已清空"
        except Exception as e:
            return f"❌ 清空失败: {str(e)}"

    # 创建 RAG 管理界面
    with gr.Row() as interface:
        with gr.Column(scale=2):
            # 知识库状态
            gr.Markdown("### 📚 知识库状态")

            db_info = gr.Markdown(
                value=get_vector_db_info(),
                label="向量数据库信息"
            )

            refresh_info_btn = gr.Button("刷新状态", size="sm")

            gr.Markdown("---")

            # 加载文档
            gr.Markdown("### 📄 加载文档")

            with gr.Tabs():
                # 从文件夹加载
                with gr.Tab("从文件夹加载"):
                    folder_path = gr.Textbox(
                        label="文件夹路径",
                        placeholder="/path/to/documents",
                        value=""
                    )

                    load_folder_btn = gr.Button("加载文件夹", variant="primary")

                    folder_result = gr.Markdown(
                        label="加载结果"
                    )

                # 添加文本
                with gr.Tab("添加文本"):
                    text_content = gr.Textbox(
                        label="文本内容",
                        placeholder="输入要添加到知识库的文本...",
                        lines=10
                    )

                    add_text_btn = gr.Button("添加文本", variant="primary")

                    text_result = gr.Markdown(
                        label="添加结果"
                    )

            gr.Markdown("---")

            # 查询知识库
            gr.Markdown("### 🔍 查询知识库")

            query_input = gr.Textbox(
                label="查询内容",
                placeholder="输入要查询的内容..."
            )

            with gr.Row():
                top_k = gr.Slider(
                    minimum=1,
                    maximum=20,
                    value=5,
                    step=1,
                    label="返回结果数量"
                )
                query_btn = gr.Button("查询", variant="primary")

            query_result = gr.Markdown(
                label="查询结果"
            )

        with gr.Column(scale=1):
            # 操作面板
            gr.Markdown("### ⚙️ 知识库操作")

            clear_db_btn = gr.Button("清空知识库", variant="stop")

            clear_result = gr.Markdown(
                label="操作结果"
            )

            gr.Markdown("---")

            # 支持的文件格式
            gr.Markdown("### 📋 支持的格式")

            gr.Markdown("""
            **支持的文件格式:**

            - 📄 `.txt` - 纯文本文件
            - 📑 `.pdf` - PDF 文档
            - 📝 `.md` - Markdown 文件
            - 📖 `.html` - HTML 文件

            **推荐用法:**

            1. 将硬件规格文档放入统一文件夹
            2. 使用 "从文件夹加载" 批量导入
            3. 使用 "查询知识库" 测试检索效果
            4. 在聊天中启用 RAG 模式使用
            """)

            # 示例
            gr.Markdown("---")
            gr.Markdown("### 💡 使用示例")

            gr.Examples(
                examples=[
                    ["什么是 PE 寄存器？"],
                    ["MUL 指令的参数有哪些？"],
                    ["SHIFT 指令如何使用？"],
                ],
                inputs=query_input,
                label="示例查询"
            )

    # 事件绑定
    refresh_info_btn.click(
        fn=lambda: get_vector_db_info(),
        outputs=db_info
    )

    load_folder_btn.click(
        fn=load_folder,
        inputs=[folder_path],
        outputs=[folder_result, folder_path, gr.State()]
    )

    add_text_btn.click(
        fn=load_text,
        inputs=[text_content],
        outputs=[text_result, text_content]
    )

    query_btn.click(
        fn=query_knowledge,
        inputs=[query_input, top_k],
        outputs=[query_result, query_input, gr.State()]
    )

    clear_db_btn.click(
        fn=clear_db,
        outputs=clear_result
    ).then(
        fn=lambda: get_vector_db_info(),
        outputs=db_info
    )

    # 初始加载信息（设置默认值）
    db_info.value = get_vector_db_info()

    return interface
