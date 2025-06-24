#!/bin/bash

# GPT-SoVITS TTS客户端运行脚本
echo "启动GPT-SoVITS TTS客户端..."
echo "========================================"

# 检查Python是否可用
if ! command -v python &> /dev/null; then
    echo "错误: Python未找到，请确保Python已安装"
    exit 1
fi

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "激活虚拟环境..."
    source .venv/bin/activate.csh
else
    echo "警告: 未找到虚拟环境，使用系统Python"
fi

# 检查依赖
echo "检查依赖包..."
python -c "import requests, pyaudio, wave, io" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装缺失的依赖包..."
    pip install requests pyaudio
fi

# 运行程序
echo "开始运行TTS客户端..."
echo "========================================"
cd "/Users/rick/Desktop/暑期科研/实操项目/FractFlow/倪校声色克隆gptsovits_ni_client"
python main.py

echo "========================================"
echo "程序执行完成" 