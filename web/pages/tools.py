# -*- coding: utf-8 -*-
"""
Skill 管理模块
"""
import gradio as gr
from typing import List


def create_tools_interface(web_app):
    """
    创建 Skill 管理界面

    Args:
        web_app: BitwiseAIWeb 实例

    Returns:
        Skill 管理界面组件
    """
    ai = web_app.ai

    def list_skills(loaded_only: bool = False):
        """列出所有 skills"""
        if not ai:
            return "❌ BitwiseAI 未初始化"

        skills = ai.list_skills(loaded_only=loaded_only)
        if not skills:
            return "暂无可用的 skills"

        result = "| # | Skill 名称 | 状态 | 描述 |\n|---|---------|------|------|\n"
        for i, skill_name in enumerate(skills, 1):
            skill = ai.skill_manager.get_skill(skill_name)
            if skill:
                status = "✅ 已加载" if skill.loaded else "⏸️ 未加载"
                description = skill.description or "无描述"
                result += f"| {i} | `{skill_name}` | {status} | {description} |\n"
            else:
                result += f"| {i} | `{skill_name}` | ❓ 未知 | - |\n"

        return result

    def list_tools():
        """列出所有工具（从已加载的 skills）"""
        if not ai:
            return "❌ BitwiseAI 未初始化"

        tools = ai.list_tools()
        if not tools:
            return "暂无可用的工具（请先加载 skills）"

        result = "| # | 工具名称 | Skill |\n|---|---------|------|\n"
        tool_to_skill = {}
        
        # 构建工具到 skill 的映射
        for skill_name in ai.skill_manager.list_loaded_skills():
            skill = ai.skill_manager.get_skill(skill_name)
            if skill and skill.loaded:
                for tool_name in skill.tools.keys():
                    tool_to_skill[tool_name] = skill_name
        
        for i, tool_name in enumerate(tools, 1):
            skill_name = tool_to_skill.get(tool_name, "未知")
            result += f"| {i} | `{tool_name}` | {skill_name} |\n"

        return result

    def load_skill(skill_name: str):
        """加载 skill"""
        if not ai:
            return "❌ BitwiseAI 未初始化"

        if not skill_name:
            return "请选择 skill"

        try:
            success = ai.load_skill(skill_name)
            if success:
                return f"✅ Skill `{skill_name}` 加载成功"
            else:
                return f"❌ Skill `{skill_name}` 加载失败"
        except Exception as e:
            return f"❌ 加载失败: {str(e)}"

    def unload_skill(skill_name: str):
        """卸载 skill"""
        if not ai:
            return "❌ BitwiseAI 未初始化"

        if not skill_name:
            return "请选择 skill"

        try:
            success = ai.unload_skill(skill_name)
            if success:
                return f"✅ Skill `{skill_name}` 卸载成功"
            else:
                return f"❌ Skill `{skill_name}` 卸载失败"
        except Exception as e:
            return f"❌ 卸载失败: {str(e)}"

    def invoke_tool(tool_name: str, args_input: str):
        """调用工具"""
        if not ai:
            return "❌ BitwiseAI 未初始化"

        if not tool_name:
            return "请选择工具"

        try:
            # 简单的参数解析
            import json
            try:
                kwargs = json.loads(args_input) if args_input.strip() else {}
            except json.JSONDecodeError:
                # 如果不是 JSON，尝试作为单个参数
                kwargs = {"input": args_input}

            result = ai.invoke_tool(tool_name, **kwargs)
            return f"✅ 执行成功\n\n**结果:**\n```\n{result}\n```"
        except Exception as e:
            return f"❌ 执行失败: {str(e)}"

    def clear_vector_db():
        """清空向量数据库"""
        if not ai:
            return "❌ BitwiseAI 未初始化"

        try:
            ai.clear_vector_db()
            return "✅ 向量数据库已清空"
        except Exception as e:
            return f"❌ 清空失败: {str(e)}"

    # 创建 Skill 管理界面
    with gr.Row() as interface:
        with gr.Column(scale=2):
            # Skill 列表
            gr.Markdown("### 🎯 Skills 管理")

            with gr.Row():
                skills_list_output = gr.Markdown(
                    value=list_skills(loaded_only=False),
                    label="Skills 列表"
                )

            with gr.Row():
                refresh_skills_btn = gr.Button("刷新列表", size="sm")
                show_loaded_only = gr.Checkbox(
                    value=False,
                    label="仅显示已加载"
                )

            gr.Markdown("---")

            # Skill 操作
            gr.Markdown("### ⚙️ Skill 操作")

            with gr.Row():
                skill_dropdown = gr.Dropdown(
                    choices=ai.skill_manager.list_available_skills() if ai else [],
                    label="选择 Skill",
                    interactive=True
                )
                refresh_skills_dropdown_btn = gr.Button("刷新", size="sm")

            with gr.Row():
                load_skill_btn = gr.Button("加载 Skill", variant="primary")
                unload_skill_btn = gr.Button("卸载 Skill", variant="secondary")

            skill_result = gr.Markdown(
                label="操作结果"
            )

            gr.Markdown("---")

            # 工具列表
            gr.Markdown("### 🔧 工具列表（来自已加载的 Skills）")

            tools_list_output = gr.Markdown(
                value=list_tools(),
                label="工具列表"
            )

            refresh_tools_btn = gr.Button("刷新工具列表", size="sm")

            gr.Markdown("---")

            # 工具调用
            gr.Markdown("### ⚡ 调用工具")

            with gr.Row():
                tool_dropdown = gr.Dropdown(
                    choices=ai.list_tools() if ai else [],
                    label="选择工具",
                    interactive=True
                )
                refresh_tools_dropdown_btn = gr.Button("刷新", size="sm")

            tool_args = gr.Textbox(
                label="参数 (JSON 格式)",
                placeholder='{"param1": "value1"}',
                lines=3
            )

            invoke_btn = gr.Button("执行", variant="primary")

            tool_result = gr.Markdown(
                label="执行结果"
            )

        with gr.Column(scale=1):
            gr.Markdown("### 📖 使用说明")

            gr.Markdown("""
            **Skills 系统**

            - Skills 是按需加载的工具集合
            - 每个 Skill 包含多个工具函数
            - 只有加载的 Skill 的工具才能被使用

            **操作流程**

            1. 查看可用的 Skills
            2. 选择并加载需要的 Skill
            3. 查看该 Skill 提供的工具
            4. 在对话中使用这些工具
            """)

    # 事件绑定
    def refresh_skills_list(loaded_only: bool):
        """刷新 Skills 列表"""
        return list_skills(loaded_only=loaded_only)

    def refresh_skills_dropdown():
        """刷新 Skills 下拉列表"""
        if ai:
            skills = ai.skill_manager.list_available_skills()
            return gr.Dropdown(choices=skills, value=None)
        return gr.Dropdown(choices=[], value=None)

    def refresh_tools_dropdown():
        """刷新工具下拉列表"""
        if ai:
            tools = ai.list_tools()
            return gr.Dropdown(choices=tools, value=None), list_tools()
        return gr.Dropdown(choices=[], value=None), "❌ BitwiseAI 未初始化"

    refresh_skills_btn.click(
        fn=lambda loaded: refresh_skills_list(loaded),
        inputs=[show_loaded_only],
        outputs=skills_list_output
    )

    show_loaded_only.change(
        fn=lambda loaded: refresh_skills_list(loaded),
        inputs=[show_loaded_only],
        outputs=skills_list_output
    )

    refresh_skills_dropdown_btn.click(
        fn=refresh_skills_dropdown,
        outputs=skill_dropdown
    )

    load_skill_btn.click(
        fn=load_skill,
        inputs=[skill_dropdown],
        outputs=skill_result
    ).then(
        fn=refresh_tools_dropdown,
        outputs=[tool_dropdown, tools_list_output]
    ).then(
        fn=lambda loaded: refresh_skills_list(loaded),
        inputs=[show_loaded_only],
        outputs=skills_list_output
    )

    unload_skill_btn.click(
        fn=unload_skill,
        inputs=[skill_dropdown],
        outputs=skill_result
    ).then(
        fn=refresh_tools_dropdown,
        outputs=[tool_dropdown, tools_list_output]
    ).then(
        fn=lambda loaded: refresh_skills_list(loaded),
        inputs=[show_loaded_only],
        outputs=skills_list_output
    )

    refresh_tools_btn.click(
        fn=lambda: list_tools(),
        outputs=tools_list_output
    )

    refresh_tools_dropdown_btn.click(
        fn=refresh_tools_dropdown,
        outputs=[tool_dropdown, tools_list_output]
    )

    invoke_btn.click(
        fn=invoke_tool,
        inputs=[tool_dropdown, tool_args],
        outputs=tool_result
    )

    return interface
