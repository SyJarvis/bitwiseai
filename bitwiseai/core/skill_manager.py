# -*- coding: utf-8 -*-
"""
Skill 管理器

扫描、加载、缓存 skills，管理工具
"""
import os
import json
import importlib
import importlib.util
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Skill:
    """Skill 定义"""
    name: str
    version: str
    description: str
    path: str
    manifest: Dict[str, Any]
    tools: Dict[str, Any] = field(default_factory=dict)
    loaded: bool = False
    module: Any = None


class SkillManager:
    """
    Skill 管理器

    负责扫描、加载、缓存 skills
    """

    def __init__(self, skills_dir: Optional[str] = None):
        """
        初始化 Skill 管理器

        Args:
            skills_dir: Skills 目录路径（默认：bitwiseai/skills）
        """
        if skills_dir is None:
            # 默认使用 bitwiseai/skills 目录
            base_dir = Path(__file__).parent.parent
            skills_dir = str(base_dir / "skills")

        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Skill] = {}
        self._scanned = False

    def scan_skills(self) -> List[str]:
        """
        扫描 skills 目录，发现所有 skills

        Returns:
            Skill 名称列表
        """
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return []

        skill_names = []

        # 遍历 skills 目录
        for item in self.skills_dir.iterdir():
            if not item.is_dir():
                continue

            skill_path = item
            manifest_path = skill_path / "skill.json"

            # 检查是否有 skill.json
            if not manifest_path.exists():
                continue

            try:
                # 加载 manifest
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)

                skill_name = manifest.get("name", item.name)
                version = manifest.get("version", "1.0.0")
                description = manifest.get("description", "")

                # 创建 Skill 对象
                skill = Skill(
                    name=skill_name,
                    version=version,
                    description=description,
                    path=str(skill_path),
                    manifest=manifest
                )

                self.skills[skill_name] = skill
                skill_names.append(skill_name)

            except Exception as e:
                print(f"⚠️  加载 skill manifest 失败 {manifest_path}: {e}")

        self._scanned = True
        return skill_names

    def load_skill(self, name: str) -> bool:
        """
        懒加载 skill（导入模块、注册工具）

        Args:
            name: Skill 名称

        Returns:
            是否加载成功
        """
        if name not in self.skills:
            if not self._scanned:
                self.scan_skills()
            if name not in self.skills:
                print(f"⚠️  Skill 不存在: {name}")
                return False

        skill = self.skills[name]

        if skill.loaded:
            return True

        try:
            # 获取工具模块路径
            tools_module_name = skill.manifest.get("tools_module", "tools")
            tools_path = Path(skill.path) / f"{tools_module_name}.py"

            if not tools_path.exists():
                print(f"⚠️  Skill {name} 的工具模块不存在: {tools_path}")
                return False

            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                f"bitwiseai.skills.{name}.{tools_module_name}",
                tools_path
            )
            if spec is None or spec.loader is None:
                print(f"⚠️  无法加载 skill 模块: {name}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 加载工具
            tools_config = skill.manifest.get("tools", [])
            for tool_config in tools_config:
                tool_name = tool_config.get("name")
                function_name = tool_config.get("function")

                if not tool_name or not function_name:
                    continue

                # 获取函数
                if hasattr(module, function_name):
                    func = getattr(module, function_name)
                    skill.tools[tool_name] = {
                        "function": func,
                        "config": tool_config
                    }

            skill.module = module
            skill.loaded = True

            # 执行 on_load hook
            if hasattr(module, "on_load"):
                module.on_load()

            print(f"✓ Skill 已加载: {name}")
            return True

        except Exception as e:
            print(f"⚠️  加载 skill 失败 {name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def unload_skill(self, name: str) -> bool:
        """
        卸载 skill

        Args:
            name: Skill 名称

        Returns:
            是否卸载成功
        """
        if name not in self.skills:
            return False

        skill = self.skills[name]

        if not skill.loaded:
            return True

        try:
            # 执行 on_unload hook
            if skill.module and hasattr(skill.module, "on_unload"):
                skill.module.on_unload()

            skill.tools.clear()
            skill.module = None
            skill.loaded = False

            print(f"✓ Skill 已卸载: {name}")
            return True

        except Exception as e:
            print(f"⚠️  卸载 skill 失败 {name}: {e}")
            return False

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        获取 skill

        Args:
            name: Skill 名称

        Returns:
            Skill 对象，如果不存在则返回 None
        """
        if name not in self.skills:
            if not self._scanned:
                self.scan_skills()
            if name not in self.skills:
                return None

        return self.skills[name]

    def list_available_skills(self) -> List[str]:
        """
        列出所有可用的 skills

        Returns:
            Skill 名称列表
        """
        if not self._scanned:
            self.scan_skills()
        return list(self.skills.keys())

    def list_loaded_skills(self) -> List[str]:
        """
        列出已加载的 skills

        Returns:
            已加载的 Skill 名称列表
        """
        return [name for name, skill in self.skills.items() if skill.loaded]

    def get_tools(self) -> List[Any]:
        """
        获取所有已加载 skills 的工具（转换为 LangChain Tools）

        Returns:
            LangChain Tool 列表
        """
        try:
            from langchain_core.tools import StructuredTool, tool
        except ImportError:
            raise ImportError("需要安装 langchain 包才能使用此功能")

        langchain_tools = []

        for skill_name, skill in self.skills.items():
            if not skill.loaded:
                continue

            for tool_name, tool_info in skill.tools.items():
                func = tool_info["function"]
                config = tool_info["config"]

                try:
                    # 使用 StructuredTool 以支持更好的 function calling
                    langchain_tool = StructuredTool.from_function(
                        func=func,
                        name=tool_name,
                        description=config.get("description", f"工具: {tool_name}"),
                    )
                    langchain_tools.append(langchain_tool)
                except Exception as e:
                    print(f"⚠️  转换工具失败 {tool_name}: {e}")
                    # 如果 StructuredTool 失败，尝试使用 @tool 装饰器包装
                    try:
                        # 动态创建工具函数
                        @tool
                        def wrapped_tool(*args, **kwargs):
                            return func(*args, **kwargs)
                        
                        wrapped_tool.name = tool_name
                        wrapped_tool.description = config.get("description", f"工具: {tool_name}")
                        langchain_tools.append(wrapped_tool)
                    except Exception as e2:
                        print(f"⚠️  使用 @tool 装饰器也失败 {tool_name}: {e2}")

        return langchain_tools


__all__ = ["SkillManager", "Skill"]

