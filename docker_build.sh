#!/bin/bash
# 德语学习助手 - Docker Android 编译脚本
set -e

echo "========================================"
echo "安装系统依赖..."
echo "========================================"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv python3-dev \
    build-essential git zip unzip \
    openjdk-17-jdk-headless autoconf libtool pkg-config zlib1g-dev \
    libncurses5-dev cmake libffi-dev libssl-dev \
    lld curl wget sudo

# 创建非root用户
useradd -m -s /bin/bash builder
echo "builder ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
chown -R builder:builder /app

echo "========================================"
echo "安装 Python 依赖..."
echo "========================================"
su - builder -c "cd /app && pip3 install buildozer cython==0.29.37 kivy pillow"

echo "========================================"
echo "开始编译 APK..."
echo "========================================"
su - builder -c "cd /app && buildozer android debug 2>&1"

echo "========================================"
echo "编译完成！"
echo "========================================"
ls -la /app/bin/*.apk 2>/dev/null || echo "未找到 APK 文件"
