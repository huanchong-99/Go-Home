# -*- mode: python ; coding: utf-8 -*-
"""
Go-home 主程序 PyInstaller 打包配置
包含所有必需的 DLL 和依赖
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Conda 环境路径
CONDA_ENV = r'G:\conda environment\Go-home'
LIBRARY_BIN = os.path.join(CONDA_ENV, 'Library', 'bin')
DLLS_DIR = os.path.join(CONDA_ENV, 'DLLs')

# 收集完整第三方模块
all_datas = []
all_binaries = []
all_hiddenimports = []

modules_to_collect = [
    'customtkinter',
    'tkcalendar',
    'babel',
    'openai',
    'httpx',
    'httpcore',
    'anyio',
    'sniffio',
    'pydantic',
    'pydantic_core',
    'certifi',
    'charset_normalizer',
    'idna',
    'h11',
    'exceptiongroup',
    'typing_extensions',
    'annotated_types',
    'tiktoken',
    'regex',
    'distro',
    'jiter',
    'colorama',
    'platformdirs',
    'dateutil',
]

for mod in modules_to_collect:
    try:
        datas, binaries, hiddenimports = collect_all(mod)
        all_datas.extend(datas)
        all_binaries.extend(binaries)
        all_hiddenimports.extend(hiddenimports)
    except Exception as e:
        print(f"Warning: Failed to collect {mod}: {e}")

# mcp 需要特殊处理
mcp_hiddenimports = collect_submodules('mcp.client') + collect_submodules('mcp.types') + collect_submodules('mcp.shared')
all_hiddenimports.extend(mcp_hiddenimports)

# 关键 DLL 列表
critical_dlls = [
    'liblzma.dll',
    'libbz2.dll',
    'libmpdec-4.dll',
    'ffi.dll',
    'ffi-8.dll',
    'libexpat.dll',
    'libcrypto-3-x64.dll',
    'libssl-3-x64.dll',
    'sqlite3.dll',
    'tcl86t.dll',
    'tk86t.dll',
    'zlib.dll',
    'bzip2.dll',
    'msvcp140.dll',
    'msvcp140_1.dll',
    'msvcp140_2.dll',
    'vcruntime140.dll',
    'vcruntime140_1.dll',
    'ucrtbase.dll',
    'concrt140.dll',
]

binaries = []
for dll in critical_dlls:
    dll_path = os.path.join(LIBRARY_BIN, dll)
    if os.path.exists(dll_path):
        binaries.append((dll_path, '.'))

for f in os.listdir(LIBRARY_BIN):
    if f.startswith('api-ms-win-') and f.endswith('.dll'):
        binaries.append((os.path.join(LIBRARY_BIN, f), '.'))

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath('main.py'))

a = Analysis(
    ['main.py'],
    pathex=[PROJECT_ROOT, CONDA_ENV],
    binaries=binaries + all_binaries,
    datas=[
        ('transfer_hubs.py', '.'),
        ('segment_query.py', '.'),
    ] + all_datas,
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkcalendar',
        'babel.numbers',
        'babel.dates',
        'mcp',
        'mcp.client',
        'mcp.client.stdio',
        'mcp.types',
        'openai',
        'openai.resources',
        'httpx',
        'httpcore',
        'h11',
        'anyio',
        'sniffio',
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        'annotated_types',
        'certifi',
        'charset_normalizer',
        'idna',
        'exceptiongroup',
        'dateutil',
        'dateutil.parser',
        'dateutil.tz',
        'asyncio',
        'concurrent.futures',
        'threading',
        'queue',
        'json',
        'typing_extensions',
        'logging',
        'dataclasses',
        'enum',
        'subprocess',
        'signal',
        'transfer_hubs',
        'segment_query',
    ] + all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'test',
        'tests',
        'unittest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Go-home',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # [临时测试] 启用控制台输出调试日志 - 调通后改回 False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
