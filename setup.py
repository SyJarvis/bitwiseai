# -*- coding: utf-8 -*-
import setuptools
from setuptools import find_packages
from pathlib import Path

with open("README.md", mode="r", encoding="utf-8") as readme_file:
    readme = readme_file.read()

setuptools.setup(
    name="BitwiseAI",
    version="0.1.1",
    description="BitwiseAI - 硬件调试和日志分析的 AI 工具",
    long_description=readme,
    long_description_content_type="text/markdown",
    author_email="1755115828@qq.com",
    url="https://github.com/SyJarvis/BitwiseAI",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "pymilvus>=2.3.0",
        "numpy>=1.20.0",
        "python-dotenv>=1.0.0",
        "PyPDF2>=3.0.0"
    ],
    extras_require={
        "dev": ["pytest", "black", "flake8"]
    },
    entry_points={
        "console_scripts": [
            "bitwiseai=bitwiseai.cli:main",
        ],
    },
    python_requires=">=3.9"
)