# -*- coding: utf-8 -*-
"""
Skill 解析器

解析 Claude Skills 标准格式的 SKILL.md 文件
"""
import re
import yaml
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class SkillParseError(Exception):
    """技能解析错误"""
    pass


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    从 SKILL.md 内容中提取 YAML frontmatter 和 Markdown 正文
    
    Args:
        content: SKILL.md 文件内容
        
    Returns:
        (frontmatter_dict, markdown_body) 元组
    """
    # 匹配 YAML frontmatter（以 --- 开头和结尾）
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if not match:
        raise SkillParseError("SKILL.md 文件必须包含 YAML frontmatter（以 --- 开头和结尾）")
    
    frontmatter_str = match.group(1)
    markdown_body = match.group(2)
    
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        if frontmatter is None:
            frontmatter = {}
        return frontmatter, markdown_body
    except yaml.YAMLError as e:
        raise SkillParseError(f"YAML frontmatter 解析失败: {e}")


def validate_skill(metadata: Dict[str, Any], skill_path: Path) -> None:
    """
    验证技能元数据格式
    
    Args:
        metadata: 技能元数据字典
        skill_path: 技能目录路径
        
    Raises:
        SkillParseError: 如果验证失败
    """
    # 验证必需字段
    if "name" not in metadata:
        raise SkillParseError("SKILL.md 必须包含 'name' 字段")
    
    if "description" not in metadata:
        raise SkillParseError("SKILL.md 必须包含 'description' 字段")
    
    name = metadata["name"]
    description = metadata["description"]
    
    # 验证 name 字段格式
    if not isinstance(name, str):
        raise SkillParseError("'name' 字段必须是字符串")
    
    if len(name) == 0 or len(name) > 64:
        raise SkillParseError("'name' 字段长度必须在 1-64 字符之间")
    
    # 验证 name 格式（小写字母、数字、连字符，不能以连字符开头或结尾）
    if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', name):
        raise SkillParseError(
            "'name' 字段只能包含小写字母、数字和连字符，不能以连字符开头或结尾，不能有连续连字符"
        )
    
    # 验证 name 与目录名一致
    if name != skill_path.name:
        raise SkillParseError(
            f"'name' 字段 ({name}) 必须与技能目录名 ({skill_path.name}) 一致"
        )
    
    # 验证 description 字段
    if not isinstance(description, str):
        raise SkillParseError("'description' 字段必须是字符串")
    
    if len(description) == 0 or len(description) > 1024:
        raise SkillParseError("'description' 字段长度必须在 1-1024 字符之间")
    
    # 验证可选字段
    if "compatibility" in metadata:
        compat = metadata["compatibility"]
        if not isinstance(compat, str):
            raise SkillParseError("'compatibility' 字段必须是字符串")
        if len(compat) > 500:
            raise SkillParseError("'compatibility' 字段长度不能超过 500 字符")


def parse_skill_md(skill_path: Path) -> Dict[str, Any]:
    """
    解析 SKILL.md 文件
    
    Args:
        skill_path: 技能目录路径（包含 SKILL.md 的目录）
        
    Returns:
        包含以下键的字典：
        - metadata: 元数据字典（frontmatter）
        - content: Markdown 正文内容
        - path: 技能路径
        
    Raises:
        SkillParseError: 如果解析失败
    """
    skill_md_path = skill_path / "SKILL.md"
    
    if not skill_md_path.exists():
        raise SkillParseError(f"SKILL.md 文件不存在: {skill_md_path}")
    
    try:
        content = skill_md_path.read_text(encoding='utf-8')
    except Exception as e:
        raise SkillParseError(f"读取 SKILL.md 文件失败: {e}")
    
    # 提取 frontmatter 和正文
    try:
        frontmatter, markdown_body = extract_frontmatter(content)
    except SkillParseError as e:
        raise SkillParseError(f"解析 SKILL.md frontmatter 失败: {e}")
    
    # 验证元数据
    try:
        validate_skill(frontmatter, skill_path)
    except SkillParseError as e:
        raise SkillParseError(f"验证技能元数据失败: {e}")
    
    return {
        "metadata": frontmatter,
        "content": markdown_body,
        "path": str(skill_path)
    }


def parse_skill_frontmatter_only(skill_path: Path) -> Dict[str, Any]:
    """
    只解析 SKILL.md 的 frontmatter（用于发现阶段，节省资源）
    
    Args:
        skill_path: 技能目录路径
        
    Returns:
        元数据字典
        
    Raises:
        SkillParseError: 如果解析失败
    """
    skill_md_path = skill_path / "SKILL.md"
    
    if not skill_md_path.exists():
        raise SkillParseError(f"SKILL.md 文件不存在: {skill_md_path}")
    
    try:
        # 只读取前 2KB（足够包含 frontmatter）
        content = skill_md_path.read_text(encoding='utf-8', errors='ignore')[:2048]
    except Exception as e:
        raise SkillParseError(f"读取 SKILL.md 文件失败: {e}")
    
    # 提取 frontmatter（只解析到第一个 --- 结束）
    frontmatter_pattern = r'^---\s*\n(.*?)\n---'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if not match:
        raise SkillParseError("SKILL.md 文件必须包含 YAML frontmatter（以 --- 开头和结尾）")
    
    frontmatter_str = match.group(1)
    
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as e:
        raise SkillParseError(f"YAML frontmatter 解析失败: {e}")
    
    # 验证必需字段
    if "name" not in frontmatter or "description" not in frontmatter:
        raise SkillParseError("SKILL.md frontmatter 必须包含 'name' 和 'description' 字段")
    
    # 基本验证（不验证目录名一致性，因为可能还没扫描完）
    name = frontmatter["name"]
    if not isinstance(name, str) or len(name) == 0 or len(name) > 64:
        raise SkillParseError("'name' 字段必须是 1-64 字符的字符串")
    
    return frontmatter


__all__ = [
    "SkillParseError",
    "parse_skill_md",
    "parse_skill_frontmatter_only",
    "extract_frontmatter",
    "validate_skill"
]

