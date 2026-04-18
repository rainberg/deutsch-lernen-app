# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec 文件 - 德语学习助手

import os
import sys
from pathlib import Path

# 项目根目录
project_root = os.path.abspath('.')

# 添加隐藏导入
hidden_imports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtMultimedia',
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    'openai',
    'transformers',
    'torch',
    'numpy',
    'pandas',
    'pydub',
    'ffmpeg',
    'genanki',
    'requests',
    'PIL',
    'pkg_resources.py2_warn',
]

# 数据文件
datas = [
    ('config.json', '.'),
    ('README.md', '.'),
    ('src', 'src'),
    ('resources', 'resources'),
]

# 分析
a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
    ],
    noarchive=False,
    optimize=0,
)

# 过滤不需要的文件
def filter_binaries():
    """过滤掉不需要的二进制文件"""
    exclude_patterns = [
        'api-ms-win-',
        'ucrtbase',
        'vcruntime',
    ]
    
    filtered = []
    for name, path, type_ in a.binaries:
        if not any(pattern in name for pattern in exclude_patterns):
            filtered.append((name, path, type_))
    return filtered

a.binaries = filter_binaries()

# PYZ
pyz = PYZ(a.pure)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DeutschLernenApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app_icon.ico',  # 应用图标
    version='version_info.txt',  # 版本信息
)

# COLLECT (如果需要生成文件夹而不是单个exe)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='DeutschLernenApp',
# )