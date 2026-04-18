#!/bin/bash
# 德语学习助手 - 安卓APK一键打包脚本
# 适用于有正常网络连接的Linux/WSL2环境

set -e

echo "========================================"
echo "  德语学习助手 - 安卓APK打包"
echo "========================================"
echo ""

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查环境
check_env() {
    echo "检查环境..."
    
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        echo -e "${RED}错误: 请在Linux或WSL2中运行此脚本${NC}"
        echo "Windows用户请使用WSL2"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到Python3${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}环境检查通过${NC}"
}

# 安装依赖
install_deps() {
    echo ""
    echo "安装系统依赖..."
    
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        python3-pip python3-venv build-essential git zip unzip \
        openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev \
        libncurses5-dev libncursesw5-dev cmake libffi-dev libssl-dev
    
    echo -e "${GREEN}系统依赖安装完成${NC}"
    
    # Python虚拟环境
    echo ""
    echo "创建Python环境..."
    python3 -m venv venv
    source venv/bin/activate
    
    pip install -q buildozer cython==0.29.33
    
    echo -e "${GREEN}Python环境准备完成${NC}"
}

# 配置镜像
setup_mirrors() {
    echo ""
    echo "配置国内镜像..."
    
    # pip镜像
    mkdir -p ~/.pip
    cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

    # Git配置
    git config --global url."https://gitee.com/".insteadOf "https://github.com/"
    
    echo -e "${GREEN}镜像配置完成${NC}"
}

# 准备资源
prepare_resources() {
    echo ""
    echo "准备资源文件..."
    
    mkdir -p resources/icons
    
    # 创建简单图标
    if [ ! -f "resources/icons/app_icon.png" ]; then
        echo "创建默认图标..."
        if command -v convert &> /dev/null; then
            convert -size 512x512 xc:'#4CAF50' \
                -fill white -gravity center -pointsize 200 -annotate 0 "DE" \
                resources/icons/app_icon.png 2>/dev/null || true
        fi
    fi
    
    # 检查mobile目录
    if [ ! -f "mobile/main.py" ]; then
        echo -e "${RED}错误: 未找到 mobile/main.py${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}资源准备完成${NC}"
}

# 开始打包
build_apk() {
    echo ""
    echo "========================================"
    echo "  开始打包APK"
    echo "========================================"
    echo ""
    echo -e "${YELLOW}首次打包预计需要30-60分钟${NC}"
    echo ""
    
    source venv/bin/activate
    export BUILDOZER_WARN_ON_ROOT=0
    
    # 开始打包
    buildozer android debug
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  打包成功！${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "APK文件:"
        ls -lah bin/*.apk 2>/dev/null
        echo ""
        echo "安装方法:"
        echo "1. 将APK传输到手机"
        echo "2. 在手机上打开APK文件"
        echo "3. 允许安装未知来源应用"
    else
        echo ""
        echo -e "${RED}打包失败，请查看日志${NC}"
    fi
}

# 主函数
main() {
    check_env
    
    echo ""
    echo "选择操作:"
    echo "1) 完整打包 (首次使用)"
    echo "2) 仅打包 (依赖已安装)"
    echo "3) 退出"
    echo ""
    read -p "请选择 [1-3]: " choice
    
    case $choice in
        1)
            install_deps
            setup_mirrors
            prepare_resources
            build_apk
            ;;
        2)
            prepare_resources
            build_apk
            ;;
        3)
            exit 0
            ;;
        *)
            echo "无效选择"
            main
            ;;
    esac
}

main