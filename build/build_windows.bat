@echo off
chcp 65001 >nul
title 德语学习助手 - Windows打包
color 0A

echo ========================================
echo 德语学习助手 - Windows打包脚本
echo ========================================
echo.

REM 检查Python
echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python
    echo 请安装Python 3.8+: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [完成] Python检查通过
echo.

REM 检查/安装PyInstaller
echo [2/5] 检查PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
)
echo [完成] PyInstaller就绪
echo.

REM 安装项目依赖
echo [3/5] 安装项目依赖...
pip install -r requirements.txt --quiet
echo [完成] 依赖安装完成
echo.

REM 创建必要目录
echo [4/5] 准备打包环境...
if not exist "resources\icons" mkdir resources\icons
if not exist "dist" mkdir dist
if not exist "build\work" mkdir build\work
echo [完成] 环境准备完成
echo.

REM 执行打包
echo [5/5] 开始打包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller build/deutsch_lernen.spec ^
    --clean ^
    --noconfirm ^
    --distpath=dist ^
    --workpath=build/work ^
    --log-level=WARN

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    echo 请查看上方错误信息
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包成功完成！
echo ========================================
echo.
echo 输出文件: dist\DeutschLernenApp.exe
echo.

REM 显示文件信息
if exist "dist\DeutschLernenApp.exe" (
    echo 文件信息:
    dir "dist\DeutschLernenApp.exe"
    echo.
    
    REM 计算文件大小
    for %%A in ("dist\DeutschLernenApp.exe") do (
        set /a size=%%~zA/1024/1024
        echo 文件大小: 约 !size! MB
    )
)

echo.
echo 是否要创建安装程序？
echo (需要先安装Inno Setup: https://jrsoftware.org/isinfo.php)
echo.
set /p create_installer="输入 Y 创建安装程序，其他键跳过: "

if /i "%create_installer%"=="Y" (
    if exist "build\setup.iss" (
        echo.
        echo 正在创建安装程序...
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build\setup.iss
        if errorlevel 1 (
            echo [警告] 安装程序创建失败
            echo 请确认已安装Inno Setup
        ) else (
            echo [完成] 安装程序已创建: dist\DeutschLernenApp_Setup_0.1.0.exe
        )
    ) else (
        echo [警告] 未找到setup.iss配置文件
    )
)

echo.
echo ========================================
echo 打包流程结束
echo ========================================
echo.
echo 使用说明:
echo 1. 直接运行: dist\DeutschLernenApp.exe
echo 2. 或安装: dist\DeutschLernenApp_Setup_0.1.0.exe
echo.
pause