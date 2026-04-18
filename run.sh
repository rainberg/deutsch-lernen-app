#!/bin/bash
# 德语学习助手启动脚本

echo "=========================================="
echo "德语学习助手 - Deutsch Lernen App"
echo "=========================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "检查依赖..."
pip install -q -r requirements.txt

# 运行应用程序
echo "启动应用程序..."
python main.py

# 如果退出，显示消息
echo ""
echo "应用程序已退出"
echo "=========================================="