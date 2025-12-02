#!/usr/bin/env python3
"""
Setup script for flight-ticket-mcp-server package
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_long_description():
    """读取README.md文件作为长描述"""
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "航空机票MCP服务器 - 基于模型上下文协议的航班查询和管理服务"

# 读取requirements文件
def read_requirements():
    """读取requirements.txt文件"""
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "fastmcp>=2.8.0",
            "pydantic>=2.0.0",
            "requests>=2.31.0",
            "python-dateutil>=2.8.0",
            "pytz>=2023.3",
            "uvicorn>=0.23.0",
            "fastapi>=0.100.0",
        ]

setup(
    name="flight-ticket-mcp-server",
    version="1.0.1",
    author="Your Name",
    author_email="your.email@example.com",
    description="一个基于模型上下文协议(MCP)的航空机票查询和管理服务器",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/flight-ticket-mcp-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.11",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flight-ticket-mcp-server=flight_ticket_mcp_server:main",
            "flight-ticket-server=flight_ticket_mcp_server:main",
        ],
    },
    include_package_data=True,
    keywords=["mcp", "flight", "ticket", "search", "ai", "fastmcp"],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/flight-ticket-mcp-server/issues",
        "Source": "https://github.com/yourusername/flight-ticket-mcp-server",
        "Documentation": "https://github.com/yourusername/flight-ticket-mcp-server#readme",
    },
)
