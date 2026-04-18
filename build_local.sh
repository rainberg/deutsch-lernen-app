#!/bin/bash
# 德语学习助手 - 本地安卓打包脚本
# 在本地Linux或WSL2中运行此脚本

echo "========================================"
echo "德语学习助手 - 本地安卓打包"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查系统
check_system() {
    echo "检查系统环境..."
    
    # 检查是否为Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        echo -e "${RED}错误: 此脚本需要在Linux或WSL2中运行${NC}"
        echo "如果是Windows，请使用WSL2"
        exit 1
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到Python3${NC}"
        echo "安装命令: sudo apt install python3 python3-pip python3-venv"
        exit 1
    fi
    
    # 检查Java
    if ! command -v java &> /dev/null; then
        echo -e "${YELLOW}警告: 未找到Java，将自动安装${NC}"
        sudo apt-get install -y openjdk-17-jdk
    fi
    
    echo -e "${GREEN}系统检查通过${NC}"
}

# 安装依赖
install_dependencies() {
    echo ""
    echo "安装系统依赖..."
    
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        build-essential \
        git \
        zip \
        unzip \
        openjdk-17-jdk \
        autoconf \
        libtool \
        pkg-config \
        zlib1g-dev \
        libncurses5-dev \
        libncursesw5-dev \
        cmake \
        libffi-dev \
        libssl-dev \
        lld
    
    echo -e "${GREEN}系统依赖安装完成${NC}"
    
    # 创建虚拟环境
    echo ""
    echo "创建Python虚拟环境..."
    python3 -m venv build_venv
    source build_venv/bin/activate
    
    # 安装Python依赖
    echo "安装Python依赖..."
    pip install buildozer cython==0.29.33 kivy
    
    echo -e "${GREEN}Python依赖安装完成${NC}"
}

# 下载项目
download_project() {
    echo ""
    echo "准备项目文件..."
    
    # 如果是从服务器下载
    if [ -n "$1" ]; then
        echo "从服务器下载项目..."
        # 这里可以添加下载逻辑
    fi
    
    # 检查项目文件
    if [ ! -f "buildozer.spec" ]; then
        echo -e "${RED}错误: 未找到buildozer.spec${NC}"
        echo "请确保在项目根目录中运行此脚本"
        exit 1
    fi
    
    echo -e "${GREEN}项目文件检查完成${NC}"
}

# 开始打包
build_apk() {
    echo ""
    echo "========================================"
    echo "开始打包APK"
    echo "========================================"
    echo ""
    echo -e "${YELLOW}首次打包预计需要30-60分钟${NC}"
    echo "将下载："
    echo "  - Android SDK (~500MB)"
    echo "  - Android NDK (~500MB)"
    echo "  - Python-for-Android (~100MB)"
    echo ""
    
    read -p "按Enter开始打包，或Ctrl+C取消..."
    
    # 激活虚拟环境
    source build_venv/bin/activate
    
    # 开始打包
    buildozer android debug
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}打包成功！${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "APK文件位置:"
        ls -la bin/*.apk 2>/dev/null
        echo ""
        echo "安装方法:"
        echo "1. 将APK传输到安卓手机"
        echo "2. 在手机上打开APK文件"
        echo "3. 允许安装未知来源应用"
    else
        echo ""
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}打包失败${NC}"
        echo -e "${RED}========================================${NC}"
        echo ""
        echo "请查看日志文件: .buildozer/android/platform/build-*/logs/"
    fi
}

# 主菜单
main() {
    echo "请选择操作:"
    echo "1) 完整安装并打包 (首次使用)"
    echo "2) 仅打包 (依赖已安装)"
    echo "3) 安装依赖 (不打包)"
    echo "4) 清理并重新打包"
    echo "5) 退出"
    echo ""
    read -p "请选择 [1-5]: " choice
    
    case $choice in
        1)
            check_system
            install_dependencies
            download_project
            build_apk
            ;;
        2)
            check_system
            download_project
            build_apk
            ;;
        3)
            check_system
            install_dependencies
            ;;
        4)
            echo "清理构建缓存..."
            rm -rf .buildozer bin
            build_apk
            ;;
        5)
            echo "退出"
            exit 0
            ;;
        *)
            echo "无效选择"
            main
            ;;
    esac
}

# 运行
main