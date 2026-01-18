#!/bin/bash
# BitwiseAI Web 服务启动脚本

cd "$(dirname "$0")"

echo "================================"
echo "BitwiseAI Web 服务"
echo "================================"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
python3 -c "import gradio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装 Gradio..."
    pip install -r requirements.txt
fi

# 启动服务
echo "启动 Web 服务..."
python3 app.py "$@"
