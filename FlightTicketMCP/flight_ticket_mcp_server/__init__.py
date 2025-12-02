"""
Flight Ticket MCP Server - 航空机票预订和管理服务器

一个基于模型上下文协议(MCP)的航空机票服务，提供:
- 航班搜索和查询
- 机票预订和管理  
- 订单处理和查询
- 乘客信息管理

版本: 1.0.0
作者: Your Name
"""

__version__ = "1.0.1"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from . import core, tools, utils

__all__ = ["core", "tools", "utils"]

def main():
    """MCP Flight Ticket Server: 航空机票查询和管理服务器"""
    import argparse
    import sys
    import os
    
    # 添加当前包的路径到sys.path以确保相对导入正常工作
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 导入主程序模块
    from .main import main as run_main
    
    parser = argparse.ArgumentParser(
        description="航空机票MCP服务器 - 提供航班查询、机票预订和管理功能"
    )
    parser.parse_args()
    
    # 运行主程序
    run_main() 