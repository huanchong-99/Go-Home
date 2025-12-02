#!/usr/bin/env python3
"""
简化的发布脚本 - 避免编码问题
"""

import os
import sys
import subprocess
import shutil

def run_cmd(cmd):
    """简单运行命令"""
    print(f"Running: {cmd}")
    result = os.system(cmd)
    if result != 0:
        print(f"Command failed: {cmd}")
        sys.exit(1)
    print("Success!")

def main():
    print("Flight Ticket MCP Server 发布脚本")
    print("=" * 40)
    
    # 清理
    print("\n1. 清理构建目录...")
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('flight_ticket_mcp_server.egg-info'):
        shutil.rmtree('flight_ticket_mcp_server.egg-info')
    
    # 构建
    print("\n2. 构建包...")
    run_cmd("python -m build")
    
    # 检查
    print("\n3. 检查包...")
    run_cmd("twine check dist/*")
    
    print("\n4. 准备上传...")
    choice = input("选择上传目标 (1=测试PyPI, 2=正式PyPI): ")
    
    if choice == "1":
        print("上传到测试PyPI...")
        token = input("请输入TestPyPI API token: ")
        run_cmd(f'twine upload --repository testpypi dist/* -u __token__ -p "{token}"')
    elif choice == "2":
        print("上传到正式PyPI...")
        token = input("请输入PyPI API token: ")
        run_cmd(f'twine upload dist/* -u __token__ -p "{token}"')
    else:
        print("无效选择")

if __name__ == "__main__":
    main()
