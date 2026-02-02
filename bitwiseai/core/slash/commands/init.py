# -*- coding: utf-8 -*-
"""
/init 命令

分析代码库并生成 SKILLS.md 或项目说明文档
"""
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...slash import SlashCommandRegistry


def register(registry: "SlashCommandRegistry") -> None:
    """
    注册 /init 命令

    Args:
        registry: 命令注册表
    """

    @registry.command(
        name="init",
        description="分析代码库结构，生成项目说明文档",
    )
    async def init(engine, args: str) -> str:
        """
        初始化项目分析

        Args:
            engine: ChatEngine 实例
            args: 命令参数（可选：目录路径）

        Returns:
            分析结果
        """
        import os
        from pathlib import Path

        # 获取工作目录
        work_dir = Path(args.strip()) if args.strip() else Path.cwd()

        if not work_dir.exists():
            return f"目录不存在: {work_dir}"

        # 扫描项目结构
        project_info = _scan_project(work_dir)

        # 生成项目摘要
        summary = f"""项目分析完成！

## 项目结构
{project_info['structure']}

## 统计信息
- Python 文件: {project_info['stats']['python_files']}
- 总文件数: {project_info['stats']['total_files']}
- 目录数: {project_info['stats']['directories']}

## 建议
建议创建 SKILLS.md 文件来描述项目功能和可用技能。
"""

        return summary


def _scan_project(root_dir: Path) -> dict:
    """
    扫描项目目录结构

    Args:
        root_dir: 项目根目录

    Returns:
        项目信息字典
    """
    structure = []
    stats = {"python_files": 0, "total_files": 0, "directories": 0}

    # 忽略的目录
    ignore_dirs = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        ".pytest_cache",
        "dist",
        "build",
        "*.egg-info",
    }

    # 忽略的文件
    ignore_files = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe"}

    def _scan_recursive(path: Path, prefix: str = ""):
        """递归扫描目录"""
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return

        for i, item in enumerate(items):
            # 跳过忽略的项
            if item.name in ignore_files:
                continue
            if item.is_dir() and item.name in ignore_dirs:
                continue

            # 构建 tree 前缀
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            if item.is_dir():
                stats["directories"] += 1
                structure.append(f"{prefix}{current_prefix}{item.name}/")
                _scan_recursive(item, prefix + child_prefix)
            else:
                stats["total_files"] += 1
                if item.suffix == ".py":
                    stats["python_files"] += 1
                structure.append(f"{prefix}{current_prefix}{item.name}")

    # 从根目录开始扫描
    structure.append(f"{root_dir.name}/")
    _scan_recursive(root_dir)

    return {
        "structure": "\n".join(structure),
        "stats": stats,
    }


__all__ = ["register"]
