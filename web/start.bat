@echo off
REM BitwiseAI Web 服务启动脚本 (Windows)

cd /d "%~dp0"

echo ================================
echo BitwiseAI Web 服务
echo ================================

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查依赖
echo 检查依赖...
python -c "import gradio" 2>nul
if errorlevel 1 (
    echo 安装 Gradio...
    pip install -r requirements.txt
)

REM 启动服务
echo 启动 Web 服务...
python app.py %*

pause
