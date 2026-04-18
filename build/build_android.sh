#!/bin/bash
# 德语学习助手 - 安卓打包脚本

echo "========================================"
echo "德语学习助手 - 安卓APK打包"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查系统
check_system() {
    echo "检查系统环境..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到Python3${NC}"
        exit 1
    fi
    
    # 检查Java
    if ! command -v java &> /dev/null; then
        echo -e "${YELLOW}警告: 未找到Java，将尝试安装${NC}"
        sudo apt-get install -y openjdk-17-jdk
    fi
    
    echo -e "${GREEN}系统检查通过${NC}"
}

# 安装依赖
install_dependencies() {
    echo ""
    echo "安装打包依赖..."
    
    # 系统依赖
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
        libtinfo5 \
        cmake \
        libffi-dev \
        libssl-dev \
        lld
    
    # Python依赖
    pip3 install --user buildozer
    pip3 install --user cython==0.29.33
    pip3 install --user kivy[base]
    
    echo -e "${GREEN}依赖安装完成${NC}"
}

# 准备资源
prepare_resources() {
    echo ""
    echo "准备资源文件..."
    
    # 创建图标目录
    mkdir -p resources/icons
    
    # 检查图标文件
    if [ ! -f "resources/icons/app_icon.png" ]; then
        echo -e "${YELLOW}提示: 请添加应用图标 (512x512 PNG)${NC}"
        echo "位置: resources/icons/app_icon.png"
    fi
    
    if [ ! -f "resources/icons/presplash.png" ]; then
        echo -e "${YELLOW}提示: 请添加启动画面 (建议1080x1920 PNG)${NC}"
        echo "位置: resources/icons/presplash.png"
    fi
    
    echo -e "${GREEN}资源准备完成${NC}"
}

# 编译APK
build_apk() {
    echo ""
    echo "开始编译APK..."
    echo "首次编译可能需要30-60分钟..."
    echo ""
    
    # 使用buildozer编译
    buildozer android debug
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}编译成功！${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "APK文件位于: bin/"
        ls -la bin/*.apk
    else
        echo ""
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}编译失败！${NC}"
        echo -e "${RED}========================================${NC}"
        echo ""
        echo "请查看日志: .buildozer/android/platform/build-*/logs/"
        exit 1
    fi
}

# 清理
clean_build() {
    echo ""
    echo "清理构建文件..."
    buildozer android clean
    echo -e "${GREEN}清理完成${NC}"
}

# 主菜单
main_menu() {
    echo ""
    echo "请选择操作:"
    echo "1) 完整打包 (安装依赖 + 编译)"
    echo "2) 仅编译APK"
    echo "3) 清理构建文件"
    echo "4) 生成发布版APK"
    echo "5) 退出"
    echo ""
    read -p "请选择 [1-5]: " choice
    
    case $choice in
        1)
            check_system
            install_dependencies
            prepare_resources
            build_apk
            ;;
        2)
            check_system
            prepare_resources
            build_apk
            ;;
        3)
            clean_build
            ;;
        4)
            echo "生成发布版APK..."
            echo "需要配置签名信息"
            buildozer android release
            ;;
        5)
            echo "退出"
            exit 0
            ;;
        *)
            echo "无效选择"
            main_menu
            ;;
    esac
}

# 运行
main_menu