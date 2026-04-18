# Windows 安装指南

## 系统要求
- Windows 10/11 (64位)
- Python 3.8 或更高版本
- 至少 8GB 内存（推荐 16GB）
- 至少 10GB 可用磁盘空间

## 安装步骤

### 1. 安装 Python
1. 访问 Python 官网：https://www.python.org/downloads/
2. 下载 Python 3.11 或更高版本
3. **重要：安装时勾选 "Add Python to PATH"**
4. 验证安装：打开命令提示符，输入 `python --version`

### 2. 安装 FFmpeg
1. 访问 FFmpeg 官网：https://ffmpeg.org/download.html
2. 下载 Windows 版本（选择 "Windows builds from gyan.dev"）
3. 解压到 `C:\ffmpeg`
4. 添加 FFmpeg 到系统 PATH：
   - 右键"此电脑" → "属性" → "高级系统设置"
   - 点击"环境变量"
   - 在"系统变量"中找到"Path"，点击"编辑"
   - 添加 `C:\ffmpeg\bin`
   - 点击"确定"保存
5. 验证安装：打开命令提示符，输入 `ffmpeg -version`

### 3. 下载项目
1. 下载项目文件到本地，例如：`C:\deutsch-lernen-app`
2. 或者使用 Git：
   ```cmd
   git clone <项目地址> C:\deutsch-lernen-app
   ```

### 4. 创建虚拟环境
```cmd
cd C:\deutsch-lernen-app
python -m venv venv
venv\Scripts\activate
```

### 5. 安装依赖
```cmd
pip install -r requirements.txt
```

### 6. 处理 PyTorch 安装（重要）
由于 PyTorch 较大，可能需要特殊处理：

**方法一：使用 CPU 版本（推荐）**
```cmd
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**方法二：使用 GPU 版本（需要 NVIDIA 显卡）**
```cmd
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 7. 运行程序
```cmd
python main.py
```

## 常见问题解决

### 问题 1：PyQt5 安装失败
**解决方案：**
```cmd
pip install PyQt5 --config-settings --confirm-license=
```

### 问题 2：FFmpeg 找不到
**解决方案：**
1. 确保 FFmpeg 已正确安装并添加到 PATH
2. 重启命令提示符
3. 手动指定 FFmpeg 路径：在 `config.json` 中设置：
   ```json
   {
     "audio": {
       "ffmpeg_path": "C:\\ffmpeg\\bin\\ffmpeg.exe"
     }
   }
   ```

### 问题 3：PyTorch 安装失败
**解决方案：**
1. 确保有足够的磁盘空间
2. 使用管理员权限运行命令提示符
3. 尝试使用 CPU 版本：
   ```cmd
   pip install torch --no-cache-dir
   ```

### 问题 4：内存不足
**解决方案：**
1. 使用较小的 Whisper 模型（tiny 或 base）
2. 在 `config.json` 中设置：
   ```json
   {
     "transcription": {
       "model_size": "tiny"
     }
   }
   ```

### 问题 5：中文显示乱码
**解决方案：**
1. 确保系统安装了中文字体
2. 在 `config.json` 中设置：
   ```json
   {
     "app": {
       "font_family": "Microsoft YaHei"
     }
   }
   ```

## 性能优化建议

### 1. 使用 SSD
将项目安装在 SSD 上可以显著提高性能。

### 2. 增加虚拟内存
1. 右键"此电脑" → "属性" → "高级系统设置"
2. 点击"性能"区域的"设置"
3. 选择"高级"选项卡，点击"虚拟内存"的"更改"
4. 设置初始大小和最大大小（建议 8GB-16GB）

### 3. 关杀毒软件
某些杀毒软件可能会影响性能，可以暂时关闭或添加项目目录到白名单。

### 4. 使用较小的模型
- **tiny**：最快，准确率较低
- **base**：平衡速度和准确率
- **small**：较慢，准确率较高
- **medium**：慢，准确率高
- **large**：最慢，准确率最高

## Windows 特有功能

### 1. 创建桌面快捷方式
1. 右键桌面 → "新建" → "快捷方式"
2. 输入位置：`C:\deutsch-lernen-app\venv\Scripts\python.exe C:\deutsch-lernen-app\main.py`
3. 命名快捷方式："德语学习助手"

### 2. 创建批处理文件
创建 `run.bat` 文件：
```batch
@echo off
cd /d C:\deutsch-lernen-app
call venv\Scripts\activate
python main.py
pause
```

### 3. 开机自启动
1. 按 `Win + R`，输入 `shell:startup`
2. 将快捷方式复制到打开的文件夹中

## 卸载方法

1. 删除项目文件夹：`C:\deutsch-lernen-app`
2. 删除桌面快捷方式
3. 删除启动文件夹中的快捷方式（如果有）
4. 卸载 Python（如果不再需要）
5. 卸载 FFmpeg（如果不再需要）

## 技术支持

如果遇到问题：
1. 查看 `logs/app.log` 文件中的错误信息
2. 检查 `config.json` 配置是否正确
3. 确保所有依赖都已正确安装
4. 尝试使用 `python test_app.py` 运行测试

## 系统兼容性

| 功能 | Windows 10 | Windows 11 | 备注 |
|------|------------|------------|------|
| 图形界面 | ✅ | ✅ | 完全支持 |
| 音频播放 | ✅ | ✅ | 需要音频驱动 |
| 语音转写 | ✅ | ✅ | 需要足够内存 |
| 文件操作 | ✅ | ✅ | 完全支持 |
| 数据库 | ✅ | ✅ | SQLite 原生支持 |

## 最低配置 vs 推荐配置

### 最低配置
- CPU：Intel Core i3 或同等
- 内存：8GB RAM
- 存储：10GB 可用空间
- 显卡：集成显卡

### 推荐配置
- CPU：Intel Core i5 或更高
- 内存：16GB RAM
- 存储：20GB 可用空间（SSD）
- 显卡：NVIDIA GTX 1060 或更高（用于 GPU 加速）

## 更新说明

### 检查更新
1. 查看项目 README.md 中的版本信息
2. 比较本地版本和最新版本

### 更新步骤
1. 备份 `config.json` 和 `data/` 文件夹
2. 下载新版本
3. 替换文件（保留配置和数据）
4. 重新安装依赖：`pip install -r requirements.txt`

## 安全注意事项

1. **数据安全**：学习数据存储在本地 `data/` 文件夹中
2. **网络安全**：程序默认不连接网络（除非使用在线模型）
3. **隐私保护**：所有处理都在本地进行
4. **备份建议**：定期备份 `data/` 文件夹

## 总结

德语学习助手完全支持 Windows 系统，主要注意事项：
1. 正确安装 Python 和 FFmpeg
2. 使用虚拟环境管理依赖
3. 根据硬件配置选择合适的模型
4. 遇到问题时查看日志文件

按照本指南操作，您应该能够在 Windows 上成功运行德语学习助手。