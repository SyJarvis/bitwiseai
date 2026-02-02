# -*- coding: utf-8 -*-
"""
Skill 管理器

扫描、加载、缓存 skills，管理工具
支持 Claude Skills 标准格式（SKILL.md）
"""
import os
import inspect
import importlib
import importlib.util
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field

from .skill_parser import parse_skill_md, parse_skill_frontmatter_only, SkillParseError
from .skill_indexer import SkillIndexer


@dataclass
class Skill:
    """Skill 定义"""
    name: str
    description: str
    path: str
    metadata: Dict[str, Any]
    content: str = ""  # SKILL.md 的完整内容（激活时加载）
    tools: Dict[str, Any] = field(default_factory=dict)  # 工具字典 {tool_name: {function, description, ...}}
    loaded: bool = False  # 是否已加载完整内容
    metadata_loaded: bool = False  # 是否已加载元数据
    module: Any = None  # 工具模块


class SkillManager:
    """
    Skill 管理器
    
    负责扫描、加载、缓存 skills
    支持渐进式加载：发现阶段只加载元数据，激活阶段加载完整内容
    """

    def __init__(
        self,
        builtin_skills_dir: Optional[str] = None,
        skill_indexer: Optional[SkillIndexer] = None
    ):
        """
        初始化 Skill 管理器
        
        Args:
            builtin_skills_dir: 内置技能目录路径（默认：bitwiseai/skills）
            skill_indexer: 技能索引器（可选）
        """
        if builtin_skills_dir is None:
            # 默认使用 bitwiseai/skills 目录
            base_dir = Path(__file__).parent.parent
            builtin_skills_dir = str(base_dir / "skills")
        
        self.builtin_skills_dir = Path(builtin_skills_dir)
        self.external_skills_dirs: List[Path] = []  # 外部技能目录列表
        self.skills: Dict[str, Skill] = {}
        self.skill_indexer = skill_indexer
        self._scanned = False

    def add_skills_directory(self, path: str) -> bool:
        """
        添加外部技能目录
        
        Args:
            path: 技能目录路径（支持 ~ 扩展）
            
        Returns:
            是否添加成功
        """
        try:
            expanded_path = os.path.expanduser(path)
            skills_dir = Path(expanded_path)
            
            if not skills_dir.exists():
                skills_dir.mkdir(parents=True, exist_ok=True)
            
            if skills_dir not in self.external_skills_dirs:
                self.external_skills_dirs.append(skills_dir)
                print(f"✓ 已添加技能目录: {skills_dir}")
                # 如果已经扫描过，立即扫描新目录
                if self._scanned:
                    self._scan_directory(skills_dir)
            return True
        except Exception as e:
            print(f"⚠️  添加技能目录失败 {path}: {e}")
            return False

    def scan_skills(self) -> List[str]:
        """
        扫描所有技能目录，发现所有 skills（只加载元数据）
        
        Returns:
            Skill 名称列表
        """
        skill_names = []
        
        # 扫描内置技能目录
        if self.builtin_skills_dir.exists():
            skill_names.extend(self._scan_directory(self.builtin_skills_dir))
        
        # 扫描外部技能目录
        for ext_dir in self.external_skills_dirs:
            if ext_dir.exists():
                skill_names.extend(self._scan_directory(ext_dir))
        
        self._scanned = True
        return skill_names

    def _scan_directory(self, skills_dir: Path) -> List[str]:
        """
        扫描单个技能目录
        
        Args:
            skills_dir: 技能目录路径
            
        Returns:
            发现的技能名称列表
        """
        skill_names = []
        
        if not skills_dir.exists():
            return skill_names
        
        # 遍历技能目录
        for item in skills_dir.iterdir():
            if not item.is_dir():
                continue
            
            skill_path = item
            skill_md_path = skill_path / "SKILL.md"
            
            # 检查是否有 SKILL.md
            if not skill_md_path.exists():
                continue
            
            try:
                # 只解析 frontmatter（发现阶段）
                metadata = parse_skill_frontmatter_only(skill_path)
                
                skill_name = metadata.get("name", item.name)
                description = metadata.get("description", "")
                
                # 验证 name 与目录名一致
                if skill_name != item.name:
                    print(f"⚠️  技能名称 ({skill_name}) 与目录名 ({item.name}) 不一致，跳过")
                    continue
                
                # 创建或更新 Skill 对象
                if skill_name in self.skills:
                    # 更新现有技能
                    skill = self.skills[skill_name]
                    skill.metadata = metadata
                    skill.description = description
                    skill.path = str(skill_path)
                else:
                    # 创建新技能
                    skill = Skill(
                        name=skill_name,
                        description=description,
                        path=str(skill_path),
                        metadata=metadata,
                        metadata_loaded=True
                    )
                    self.skills[skill_name] = skill
                
                skill_names.append(skill_name)
                
                # 索引到向量数据库（如果启用）
                if self.skill_indexer:
                    try:
                        self.skill_indexer.index_skill(
                            skill_name=skill_name,
                            skill_metadata=metadata,
                            skill_path=str(skill_path),
                            content_summary=""  # 发现阶段不加载完整内容
                        )
                    except Exception as e:
                        print(f"⚠️  索引技能失败 {skill_name}: {e}")
                
            except SkillParseError as e:
                print(f"⚠️  解析技能失败 {skill_path}: {e}")
            except Exception as e:
                print(f"⚠️  加载技能元数据失败 {skill_path}: {e}")
                import traceback
                traceback.print_exc()
        
        return skill_names

    def load_skill(self, name: str) -> bool:
        """
        加载技能完整内容（激活阶段）
        包括：完整 SKILL.md 内容、scripts/tools.py 中的工具
        
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
            # 1. 加载完整 SKILL.md 内容
            skill_path = Path(skill.path)
            skill_data = parse_skill_md(skill_path)
            
            skill.metadata = skill_data["metadata"]
            skill.content = skill_data["content"]
            skill.description = skill.metadata.get("description", "")
            
            # 2. 加载工具（从 scripts/tools.py）
            self._load_skill_tools(skill)
            
            skill.loaded = True
            
            # 更新索引（包含内容摘要）
            if self.skill_indexer:
                content_summary = skill.content[:500]  # 前 500 字符作为摘要
                try:
                    self.skill_indexer.update_index(
                        skill_name=name,
                        skill_metadata=skill.metadata,
                        skill_path=skill.path,
                        content_summary=content_summary
                    )
                except Exception as e:
                    print(f"⚠️  更新技能索引失败 {name}: {e}")
            
            print(f"✓ Skill 已加载: {name}")
            return True
            
        except Exception as e:
            print(f"⚠️  加载 skill 失败 {name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _is_simple_type(self, type_annotation) -> bool:
        """
        判断类型注解是否简单（适合作为工具的参数或返回值）
        
        简单类型：str, int, float, bool, None, Optional[str/int/float/bool]
        复杂类型：List, Tuple, Dict, Callable, Iterator 等（会被跳过）
        
        Args:
            type_annotation: 类型注解对象
            
        Returns:
            是否为简单类型
        """
        if type_annotation == inspect.Signature.empty:
            return True  # 无类型注解，默认允许（向后兼容）
        
        type_str = str(type_annotation)
        
        # 检查是否是复杂类型
        complex_type_keywords = [
            'List[', 'Tuple[', 'Dict[', 'Callable', 
            'Iterator', 'Generator', 'AsyncGenerator',
            'Union[', 'Any'
        ]
        if any(keyword in type_str for keyword in complex_type_keywords):
            return False
        
        # 检查 Optional[简单类型] 的情况
        if 'Optional[' in type_str:
            # 提取 Optional 内的类型
            inner_type = type_str.replace('Optional[', '').rstrip(']')
            return self._is_simple_type_str(inner_type)
        
        # 检查简单类型
        return self._is_simple_type_str(type_str)
    
    def _is_simple_type_str(self, type_str: str) -> bool:
        """检查类型字符串是否为简单类型"""
        simple_types = ['str', 'int', 'float', 'bool', 'None', 'NoneType']
        return any(st in type_str for st in simple_types)
    
    def _load_skill_tools(self, skill: Skill):
        """
        从 scripts/tools.py 加载工具
        
        Args:
            skill: Skill 对象
        """
        skill_path = Path(skill.path)
        
        # 查找工具文件（优先 scripts/tools.py，其次 tools.py）
        tools_paths = [
            skill_path / "scripts" / "tools.py",
            skill_path / "tools.py"  # 向后兼容
        ]
        
        tools_path = None
        for path in tools_paths:
            if path.exists():
                tools_path = path
                break
        
        if not tools_path:
            # 某些技能可能没有工具文件，而是通过 SKILL.md 的内容来指导 AI 执行任务
            # 这是正常的，不需要警告
            return
        
        try:
            # 动态导入模块
            module_name = f"bitwiseai.skills.{skill.name}.tools"
            spec = importlib.util.spec_from_file_location(module_name, tools_path)
            if spec is None or spec.loader is None:
                print(f"⚠️  无法加载 skill 模块: {skill.name}")
                return
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            skill.module = module
            
            # 自动发现工具函数
            # 查找所有公共函数（不以 _ 开头）
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                if name.startswith("_"):
                    continue
                
                # 获取函数签名
                sig = inspect.signature(obj)
                
                # 检查返回类型
                return_type = sig.return_annotation
                if not self._is_simple_type(return_type):
                    # 跳过返回复杂类型的函数（避免 JSON Schema 错误）
                    continue
                
                # 检查参数类型（如果有 Callable 等复杂类型，也跳过）
                has_complex_param = False
                for param_name, param in sig.parameters.items():
                    if param.annotation != inspect.Parameter.empty:
                        if not self._is_simple_type(param.annotation):
                            has_complex_param = True
                            break
                
                if has_complex_param:
                    # 跳过有复杂参数类型的函数
                    continue
                
                # 获取文档字符串
                doc = inspect.getdoc(obj) or ""
                
                # 从文档字符串提取描述（第一行或前 200 字符）
                description = doc.split("\n")[0].strip() if doc else f"工具: {name}"
                if len(description) > 200:
                    description = description[:200] + "..."
                
                # 构建工具配置
                tool_config = {
                    "name": name,
                    "function": name,
                    "description": description,
                    "module": "tools"
                }
                
                # 从函数签名提取参数信息
                params = {}
                for param_name, param in sig.parameters.items():
                    param_type = "string"  # 默认类型
                    if param.annotation != inspect.Parameter.empty:
                        # 从类型注解推断类型
                        ann_str = str(param.annotation)
                        if "int" in ann_str and "Optional" not in ann_str:
                            param_type = "integer"
                        elif "float" in ann_str and "Optional" not in ann_str:
                            param_type = "float"
                        elif "bool" in ann_str and "Optional" not in ann_str:
                            param_type = "boolean"
                    
                    params[param_name] = {
                        "type": param_type,
                        "description": f"参数 {param_name}"
                    }
                
                tool_config["parameters"] = params
                
                # 注册工具
                skill.tools[name] = {
                    "function": obj,
                    "config": tool_config
                }
            
            # 执行 on_load hook（如果存在）
            if hasattr(module, "on_load"):
                module.on_load()
                
        except Exception as e:
            print(f"⚠️  加载技能工具失败 {skill.name}: {e}")
            import traceback
            traceback.print_exc()

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
            skill.content = ""  # 释放内容
            
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

    def get_skill_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取技能元数据（不加载完整内容）
        
        Args:
            name: Skill 名称
            
        Returns:
            元数据字典，如果不存在则返回 None
        """
        skill = self.get_skill(name)
        if skill:
            return skill.metadata
        return None

    def load_skill_content(self, name: str) -> bool:
        """
        加载技能的完整内容（激活时调用）
        
        Args:
            name: Skill 名称
            
        Returns:
            是否加载成功
        """
        return self.load_skill(name)

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

    def search_skills(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        使用向量检索查找相关技能
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            技能信息列表
        """
        if not self.skill_indexer:
            # 如果没有索引器，使用简单的关键词匹配
            results = []
            query_lower = query.lower()
            for skill_name, skill in self.skills.items():
                if query_lower in skill.description.lower() or query_lower in skill.name.lower():
                    results.append({
                        "skill_name": skill_name,
                        "description": skill.description,
                        "path": skill.path,
                        "score": 1.0
                    })
            return results[:top_k]
        
        return self.skill_indexer.search_skills(query, top_k)

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
