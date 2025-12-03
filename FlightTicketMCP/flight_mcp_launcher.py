#!/usr/bin/env python3
"""
FlightMCP 启动器
用于 PyInstaller 打包成独立 exe，启动 MCP 服务
"""

import os
import sys

# 确保当前目录在 Python 路径中
if getattr(sys, 'frozen', False):
    # 打包后的环境
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 开发环境
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 将 BASE_DIR 添加到 Python 路径
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 导入并启动 MCP 服务
from flight_ticket_mcp_server.main import main

if __name__ == "__main__":
    main()
