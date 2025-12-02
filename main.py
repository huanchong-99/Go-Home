#!/usr/bin/env python3
"""
Go-home - 回家最优路线查询系统
主程序入口，提供现代化 UI 界面
"""

import customtkinter as ctk
import threading
import asyncio
import json
import os
import queue
# ThreadPoolExecutor 已移至 segment_query.py
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from tkinter import messagebox

# 导入中转枢纽模块
from transfer_hubs import get_transfer_hub_prompt, hub_manager

# 导入分段查询引擎
from segment_query import (
    SegmentQueryEngine,
    calculate_adjusted_train_date
)



# Conda 环境配置
CONDA_ENV_PATH = r"G:\conda environment\Go-home"
PYTHON_EXE = os.path.join(CONDA_ENV_PATH, "python.exe")
NODE_EXE = os.path.join(CONDA_ENV_PATH, "node.exe")

# MCP 服务路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FLIGHT_MCP_MODULE = "flight_ticket_mcp_server"
TRAIN_MCP_SCRIPT = os.path.join(PROJECT_ROOT, "12306-mcp", "build", "index.js")

# 配置文件路径
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")


class MCPClientWorker:
    """
    MCP 客户端工作线程
    在独立线程中运行异步事件循环，保持 MCP 连接的完整生命周期
    """

    def __init__(self, name: str, command: List[str], cwd: str):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.tools: List[Dict] = []
        self._running = False
        self._connected = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._request_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._connect_event = threading.Event()
        self._connect_result = False
        self._connect_error = ""

    def start(self) -> bool:
        """启动工作线程并连接到 MCP 服务"""
        if self._running:
            return self._connected

        self._stop_event.clear()
        self._connect_event.clear()
        self._thread = threading.Thread(target=self._run_worker, daemon=True)
        self._thread.start()

        # 等待连接完成（最多30秒）
        self._connect_event.wait(timeout=30)
        return self._connect_result

    def _run_worker(self):
        """工作线程主函数"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._running = True

        try:
            self._loop.run_until_complete(self._async_worker())
        except Exception as e:
            print(f"[{self.name}] 工作线程异常: {e}")
        finally:
            self._running = False
            self._connected = False
            self._loop.close()

    async def _async_worker(self):
        """异步工作主循环"""
        server_params = StdioServerParameters(
            command=self.command[0],
            args=self.command[1:] if len(self.command) > 1 else [],
            cwd=self.cwd
        )

        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # 初始化会话
                    await session.initialize()

                    # 获取工具列表
                    tools_result = await session.list_tools()
                    self.tools = [
                        {
                            "type": "function",
                            "function": {
                                "name": f"{self.name}_{tool.name}",
                                "description": tool.description or "",
                                "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {"type": "object", "properties": {}}
                            }
                        }
                        for tool in tools_result.tools
                    ]

                    self._connected = True
                    self._connect_result = True
                    self._connect_event.set()

                    # 主循环：处理工具调用请求
                    while not self._stop_event.is_set():
                        try:
                            # 非阻塞检查请求队列
                            try:
                                request = self._request_queue.get_nowait()
                            except queue.Empty:
                                await asyncio.sleep(0.1)
                                continue

                            tool_name, arguments, result_queue = request

                            try:
                                # 移除服务名前缀
                                actual_tool_name = tool_name.replace(f"{self.name}_", "")
                                result = await session.call_tool(actual_tool_name, arguments)

                                # 提取结果内容
                                if result.content:
                                    contents = []
                                    for item in result.content:
                                        if hasattr(item, 'text'):
                                            contents.append(item.text)
                                    result_str = "\n".join(contents) if contents else "工具执行成功，无返回内容"
                                else:
                                    result_str = "工具执行成功，无返回内容"

                                result_queue.put(("success", result_str))
                            except Exception as e:
                                result_queue.put(("error", f"工具调用失败: {str(e)}"))

                        except Exception as e:
                            print(f"[{self.name}] 处理请求异常: {e}")

        except Exception as e:
            self._connect_error = str(e)
            self._connect_result = False
            self._connect_event.set()
            print(f"[{self.name}] 连接失败: {e}")

    def call_tool(self, tool_name: str, arguments: Dict, timeout: float = 60) -> str:
        """调用 MCP 工具（线程安全）"""
        if not self._connected:
            return f"错误: {self.name} 服务未连接"

        result_queue: queue.Queue = queue.Queue()
        self._request_queue.put((tool_name, arguments, result_queue))

        try:
            _, result = result_queue.get(timeout=timeout)
            return result
        except queue.Empty:
            return f"工具调用超时: {tool_name}"

    def stop(self):
        """停止工作线程"""
        self._stop_event.set()
        self._connected = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self.tools = []
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._connected

    @property
    def connect_error(self) -> str:
        return self._connect_error


class MCPServiceManager:
    """MCP 服务管理器"""

    def __init__(self):
        self.flight_client: Optional[MCPClientWorker] = None
        self.train_client: Optional[MCPClientWorker] = None

    def start_flight_mcp(self, log_callback=None) -> bool:
        """启动机票查询 MCP 服务"""
        if self.flight_client and self.flight_client.is_running:
            if log_callback:
                log_callback("[FlightMCP] 服务已在运行中")
            return True

        try:
            self.flight_client = MCPClientWorker(
                name="flight",
                command=[PYTHON_EXE, "-m", FLIGHT_MCP_MODULE],
                cwd=PROJECT_ROOT
            )

            success = self.flight_client.start()
            if success:
                if log_callback:
                    tool_count = len(self.flight_client.tools)
                    log_callback(f"[FlightMCP] 机票服务已连接，可用工具: {tool_count} 个")
                return True
            else:
                if log_callback:
                    error = self.flight_client.connect_error or "未知错误"
                    log_callback(f"[FlightMCP] 连接失败: {error}")
                self.flight_client = None
                return False
        except Exception as e:
            if log_callback:
                log_callback(f"[FlightMCP] 启动失败: {str(e)}")
            return False

    def start_train_mcp(self, log_callback=None) -> bool:
        """启动火车票查询 MCP 服务"""
        if self.train_client and self.train_client.is_running:
            if log_callback:
                log_callback("[12306-MCP] 服务已在运行中")
            return True

        try:
            self.train_client = MCPClientWorker(
                name="train",
                command=[NODE_EXE, TRAIN_MCP_SCRIPT],
                cwd=os.path.dirname(TRAIN_MCP_SCRIPT)
            )

            success = self.train_client.start()
            if success:
                if log_callback:
                    tool_count = len(self.train_client.tools)
                    log_callback(f"[12306-MCP] 火车票服务已连接，可用工具: {tool_count} 个")
                return True
            else:
                if log_callback:
                    error = self.train_client.connect_error or "未知错误"
                    log_callback(f"[12306-MCP] 连接失败: {error}")
                self.train_client = None
                return False
        except Exception as e:
            if log_callback:
                log_callback(f"[12306-MCP] 启动失败: {str(e)}")
            return False

    def stop_flight_mcp(self, log_callback=None):
        """停止机票查询服务"""
        if self.flight_client:
            self.flight_client.stop()
            self.flight_client = None
            if log_callback:
                log_callback("[FlightMCP] 服务已停止")

    def stop_train_mcp(self, log_callback=None):
        """停止火车票查询服务"""
        if self.train_client:
            self.train_client.stop()
            self.train_client = None
            if log_callback:
                log_callback("[12306-MCP] 服务已停止")

    def stop_all(self, log_callback=None):
        """停止所有服务"""
        self.stop_flight_mcp(log_callback)
        self.stop_train_mcp(log_callback)

    def get_all_tools(self) -> List[Dict]:
        """获取所有可用的工具列表（OpenAI function calling 格式）"""
        tools = []
        if self.flight_client and self.flight_client.is_running:
            tools.extend(self.flight_client.tools)
        if self.train_client and self.train_client.is_running:
            tools.extend(self.train_client.tools)
        return tools

    def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """调用工具"""
        try:
            if tool_name.startswith("flight_") and self.flight_client:
                return self.flight_client.call_tool(tool_name, arguments)
            elif tool_name.startswith("train_") and self.train_client:
                return self.train_client.call_tool(tool_name, arguments)
            else:
                return f"未知工具: {tool_name}"
        except Exception as e:
            return f"工具调用失败: {str(e)}"

    @property
    def flight_running(self) -> bool:
        return self.flight_client is not None and self.flight_client.is_running

    @property
    def train_running(self) -> bool:
        return self.train_client is not None and self.train_client.is_running


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> dict:
        """加载配置"""
        default_config = {
            "api_base_url": "https://api.openai.com/v1",
            "api_key": "",
            "model": "gpt-4",
            "theme": "dark",
            "window_size": "1200x800"
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except Exception:
                pass

        return default_config

    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def set(self, key: str, value):
        self.config[key] = value


class GoHomeApp(ctk.CTk):
    """Go-home 主应用程序"""

    def __init__(self):
        super().__init__()

        # 初始化管理器
        self.config_manager = ConfigManager(CONFIG_FILE)
        self.mcp_manager = MCPServiceManager()
        self.openai_client: Optional[OpenAI] = None

        # 设置主题
        ctk.set_appearance_mode(self.config_manager.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        # 窗口设置
        self.title("Go-home - 回家最优路线查询系统")
        window_size = self.config_manager.get("window_size", "1200x800")
        self.geometry(window_size)
        self.minsize(1000, 700)

        # 查询状态
        self.is_querying = False

        # 中转枢纽模式状态（默认关闭）
        self.transfer_hub_mode = False

        # 创建 UI
        self.create_ui()

        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_ui(self):
        """创建用户界面"""
        # 配置网格
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 创建侧边栏
        self.create_sidebar()

        # 创建主内容区
        self.create_main_content()

    def create_sidebar(self):
        """创建侧边栏"""
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo/标题
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="🏠 Go-home",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="回家最优路线查询",
            font=ctk.CTkFont(size=14)
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # MCP 服务控制区
        self.service_frame = ctk.CTkFrame(self.sidebar)
        self.service_frame.grid(row=2, column=0, padx=15, pady=10, sticky="ew")

        self.service_label = ctk.CTkLabel(
            self.service_frame,
            text="MCP 服务控制",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.service_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5))

        # 机票服务状态
        self.flight_status = ctk.CTkLabel(
            self.service_frame,
            text="● 机票服务",
            text_color="gray",
            font=ctk.CTkFont(size=13)
        )
        self.flight_status.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        # 火车票服务状态
        self.train_status = ctk.CTkLabel(
            self.service_frame,
            text="● 火车票服务",
            text_color="gray",
            font=ctk.CTkFont(size=13)
        )
        self.train_status.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        # 一键启动按钮
        self.start_all_btn = ctk.CTkButton(
            self.service_frame,
            text="🚀 一键启动服务",
            command=self.start_all_services,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        self.start_all_btn.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        # 停止按钮
        self.stop_all_btn = ctk.CTkButton(
            self.service_frame,
            text="⏹ 停止所有服务",
            command=self.stop_all_services,
            font=ctk.CTkFont(size=14),
            height=35,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        self.stop_all_btn.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

        # 中转枢纽模式切换区
        self.hub_mode_frame = ctk.CTkFrame(self.sidebar)
        self.hub_mode_frame.grid(row=3, column=0, padx=15, pady=10, sticky="ew")

        self.hub_mode_label = ctk.CTkLabel(
            self.hub_mode_frame,
            text="智能中转模式",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.hub_mode_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        # 中转模式开关
        self.hub_mode_switch_var = ctk.StringVar(value="off")
        self.hub_mode_switch = ctk.CTkSwitch(
            self.hub_mode_frame,
            text="启用中转枢纽",
            variable=self.hub_mode_switch_var,
            onvalue="on",
            offvalue="off",
            command=self.toggle_transfer_hub_mode,
            font=ctk.CTkFont(size=13)
        )
        self.hub_mode_switch.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        # 中转模式状态提示
        self.hub_mode_status = ctk.CTkLabel(
            self.hub_mode_frame,
            text="当前：标准模式（仅查直达）",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.hub_mode_status.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")

        # API 配置区
        self.api_frame = ctk.CTkFrame(self.sidebar)
        self.api_frame.grid(row=4, column=0, padx=15, pady=10, sticky="ew")

        self.api_label = ctk.CTkLabel(
            self.api_frame,
            text="AI API 配置",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.api_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # API Base URL
        self.api_url_label = ctk.CTkLabel(self.api_frame, text="API Base URL:")
        self.api_url_label.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")

        self.api_url_entry = ctk.CTkEntry(
            self.api_frame,
            placeholder_text="https://api.openai.com/v1",
            width=230
        )
        self.api_url_entry.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.api_url_entry.insert(0, self.config_manager.get("api_base_url", ""))

        # API Key
        self.api_key_label = ctk.CTkLabel(self.api_frame, text="API Key:")
        self.api_key_label.grid(row=3, column=0, padx=10, pady=(5, 0), sticky="w")

        self.api_key_entry = ctk.CTkEntry(
            self.api_frame,
            placeholder_text="sk-...",
            show="*",
            width=230
        )
        self.api_key_entry.grid(row=4, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.api_key_entry.insert(0, self.config_manager.get("api_key", ""))

        # Model 选择区域
        self.model_label = ctk.CTkLabel(self.api_frame, text="模型:")
        self.model_label.grid(row=5, column=0, padx=10, pady=(5, 0), sticky="w")

        # 模型选择框架
        self.model_select_frame = ctk.CTkFrame(self.api_frame, fg_color="transparent")
        self.model_select_frame.grid(row=6, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.model_select_frame.grid_columnconfigure(0, weight=1)

        # 模型下拉框
        self.available_models: List[str] = [self.config_manager.get("model", "gpt-4")]
        self.model_combobox = ctk.CTkComboBox(
            self.model_select_frame,
            values=self.available_models,
            width=160,
            state="readonly"
        )
        self.model_combobox.grid(row=0, column=0, sticky="ew")
        self.model_combobox.set(self.config_manager.get("model", "gpt-4"))

        # 获取模型列表按钮
        self.fetch_models_btn = ctk.CTkButton(
            self.model_select_frame,
            text="🔄",
            command=self.fetch_available_models,
            width=40,
            height=28
        )
        self.fetch_models_btn.grid(row=0, column=1, padx=(5, 0))

        # 保存配置按钮
        self.save_config_btn = ctk.CTkButton(
            self.api_frame,
            text="💾 保存配置",
            command=self.save_api_config,
            height=35
        )
        self.save_config_btn.grid(row=7, column=0, padx=10, pady=10, sticky="ew")

        # 主题切换
        self.theme_label = ctk.CTkLabel(self.sidebar, text="主题:", anchor="w")
        self.theme_label.grid(row=11, column=0, padx=20, pady=(10, 0), sticky="w")

        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["dark", "light", "system"],
            command=self.change_theme
        )
        self.theme_menu.grid(row=12, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.theme_menu.set(self.config_manager.get("theme", "dark"))

    def create_main_content(self):
        """创建主内容区"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)  # 查询选项区
        self.main_frame.grid_rowconfigure(2, weight=3)  # 结果区
        self.main_frame.grid_rowconfigure(3, weight=1)  # 日志区

        # 标题区
        self.title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        self.main_title = ctk.CTkLabel(
            self.title_frame,
            text="🚄 回家路线查询",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.main_title.pack(side="left")

        # 时间显示
        self.time_label = ctk.CTkLabel(
            self.title_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.time_label.pack(side="right")
        self.update_time()

        # 查询选项区域
        self.create_query_options()

        # 结果展示区域
        self.create_result_area()

        # 日志区域
        self.create_log_area()

        # 初始日志
        self.log_message("=" * 50)
        self.log_message("Go-home - 回家最优路线查询系统")
        self.log_message("=" * 50)
        self.log_message("请先启动 MCP 服务，然后填写查询选项开始查询")

    def create_query_options(self):
        """创建查询选项区域"""
        self.query_frame = ctk.CTkFrame(self.main_frame)
        self.query_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.query_frame.grid_columnconfigure((0, 1), weight=1)

        # 查询选项标题
        self.query_title = ctk.CTkLabel(
            self.query_frame,
            text="📝 查询选项",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.query_title.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        # 左侧：基本信息
        left_frame = ctk.CTkFrame(self.query_frame, fg_color="transparent")
        left_frame.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")

        # 出发地
        ctk.CTkLabel(left_frame, text="出发城市:", font=ctk.CTkFont(size=13)).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.from_city_entry = ctk.CTkEntry(left_frame, placeholder_text="例如：北京", width=200)
        self.from_city_entry.grid(row=0, column=1, padx=(10, 0), pady=(0, 5), sticky="w")

        # 目的地
        ctk.CTkLabel(left_frame, text="目的城市:", font=ctk.CTkFont(size=13)).grid(row=1, column=0, sticky="w", pady=5)
        self.to_city_entry = ctk.CTkEntry(left_frame, placeholder_text="例如：上海", width=200)
        self.to_city_entry.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="w")

        # 出发日期
        ctk.CTkLabel(left_frame, text="出发日期:", font=ctk.CTkFont(size=13)).grid(row=2, column=0, sticky="w", pady=5)
        date_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        date_frame.grid(row=2, column=1, padx=(10, 0), pady=5, sticky="w")

        # 默认日期为明天
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.date_entry = ctk.CTkEntry(date_frame, placeholder_text="YYYY-MM-DD", width=150)
        self.date_entry.insert(0, tomorrow)
        self.date_entry.grid(row=0, column=0)

        # 右侧：偏好设置
        right_frame = ctk.CTkFrame(self.query_frame, fg_color="transparent")
        right_frame.grid(row=1, column=1, padx=15, pady=5, sticky="nsew")

        # 优先策略
        ctk.CTkLabel(right_frame, text="优先策略:", font=ctk.CTkFont(size=13)).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.priority_var = ctk.StringVar(value="balanced")
        priority_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        priority_frame.grid(row=0, column=1, padx=(10, 0), pady=(0, 5), sticky="w")
        ctk.CTkRadioButton(priority_frame, text="💰 省钱", variable=self.priority_var, value="cheap", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(priority_frame, text="⏱️ 省时", variable=self.priority_var, value="fast", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(priority_frame, text="⚖️ 均衡", variable=self.priority_var, value="balanced", font=ctk.CTkFont(size=12)).pack(side="left")

        # 交通方式
        ctk.CTkLabel(right_frame, text="交通方式:", font=ctk.CTkFont(size=13)).grid(row=1, column=0, sticky="w", pady=5)
        self.transport_var = ctk.StringVar(value="all")
        transport_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        transport_frame.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="w")
        ctk.CTkRadioButton(transport_frame, text="✈️ 飞机", variable=self.transport_var, value="flight", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(transport_frame, text="🚄 火车", variable=self.transport_var, value="train", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(transport_frame, text="🔄 不限", variable=self.transport_var, value="all", font=ctk.CTkFont(size=12)).pack(side="left")

        # 行程时长接受度
        ctk.CTkLabel(right_frame, text="行程时长:", font=ctk.CTkFont(size=13)).grid(row=2, column=0, sticky="w", pady=5)
        self.duration_var = ctk.StringVar(value="normal")
        duration_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        duration_frame.grid(row=2, column=1, padx=(10, 0), pady=5, sticky="w")
        ctk.CTkRadioButton(duration_frame, text="⚡ 当天到", variable=self.duration_var, value="same_day", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(duration_frame, text="📅 可隔天", variable=self.duration_var, value="normal", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(duration_frame, text="🕐 接受长途", variable=self.duration_var, value="long", font=ctk.CTkFont(size=12)).pack(side="left")

        # 查询按钮
        btn_frame = ctk.CTkFrame(self.query_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=(10, 15))

        self.query_btn = ctk.CTkButton(
            btn_frame,
            text="🔍 开始查询",
            command=self.start_query,
            font=ctk.CTkFont(size=16, weight="bold"),
            width=200,
            height=45
        )
        self.query_btn.pack(side="left", padx=10)

        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ 清空结果",
            command=self.clear_results,
            font=ctk.CTkFont(size=14),
            width=120,
            height=45,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        self.clear_btn.pack(side="left", padx=10)

        # 进度条区域
        self.progress_frame = ctk.CTkFrame(self.query_frame, fg_color="transparent")
        self.progress_frame.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        self.progress_frame.grid_columnconfigure(1, weight=1)

        # 进度标签
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=13)
        )
        self.progress_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            height=15,
            corner_radius=5
        )
        self.progress_bar.grid(row=0, column=1, sticky="ew")
        self.progress_bar.set(0)

        # 初始隐藏进度条
        self.progress_frame.grid_remove()

    def show_progress(self, current: int, total: int, text: str = ""):
        """显示进度条"""
        self.progress_frame.grid()
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        if text:
            self.progress_label.configure(text=f"{text} ({current}/{total})")
        else:
            self.progress_label.configure(text=f"进度: {current}/{total}")

    def hide_progress(self):
        """隐藏进度条"""
        self.progress_frame.grid_remove()
        self.progress_bar.set(0)
        self.progress_label.configure(text="")

    def create_result_area(self):
        """创建结果展示区域"""
        self.result_frame = ctk.CTkFrame(self.main_frame)
        self.result_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(1, weight=1)

        # 结果标题
        self.result_title = ctk.CTkLabel(
            self.result_frame,
            text="📋 推荐方案",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.result_title.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        # 结果显示区
        self.result_textbox = ctk.CTkTextbox(
            self.result_frame,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            wrap="word",
            state="disabled"
        )
        self.result_textbox.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")

        # 初始提示
        self.show_result("欢迎使用 Go-home 回家路线查询系统！\n\n请按以下步骤操作：\n1. 点击左侧「一键启动服务」启动 MCP 服务\n2. 配置 AI API 并保存\n3. 填写出发地、目的地、日期\n4. 选择您的偏好（省钱/省时/交通方式等）\n5. 点击「开始查询」\n\n系统将为您智能推荐最优的回家路线！")

    def create_log_area(self):
        """创建日志区域"""
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.log_frame.grid(row=3, column=0, sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)

        self.log_title = ctk.CTkLabel(
            self.log_frame,
            text="📋 运行日志",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.log_title.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word",
            height=100
        )
        self.log_textbox.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")

    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")

    def show_result(self, content: str):
        """显示结果"""
        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", content)
        self.result_textbox.configure(state="disabled")

    def append_result(self, content: str):
        """追加结果"""
        self.result_textbox.configure(state="normal")
        self.result_textbox.insert("end", content)
        self.result_textbox.configure(state="disabled")
        self.result_textbox.see("end")

    def clear_results(self):
        """清空结果"""
        self.show_result("结果已清空，请开始新的查询。")
        self.log_message("结果已清空")

    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.configure(text=current_time)
        self.after(1000, self.update_time)

    def build_system_prompt(self) -> str:
        """根据用户选项构建系统提示词"""
        priority = self.priority_var.get()
        transport = self.transport_var.get()
        duration = self.duration_var.get()

        priority_text = {
            "cheap": "用户更看重价格，请优先推荐价格最低的方案，即使需要多花一些时间。",
            "fast": "用户更看重时间，请优先推荐最快到达的方案，价格可以适当高一些。",
            "balanced": "用户希望在价格和时间之间取得平衡，请综合考虑推荐性价比最高的方案。"
        }[priority]

        transport_text = {
            "flight": "用户只考虑飞机出行，请只查询和推荐航班信息。",
            "train": "用户只考虑火车出行，请只查询和推荐火车票信息（高铁、动车、普通列车等）。",
            "all": "用户对交通方式没有限制，请同时查询飞机和火车，比较后给出最佳推荐。"
        }[transport]

        duration_text = {
            "same_day": "用户希望当天到达目的地，请只推荐出发当天能够到达的方案，不要推荐需要过夜或次日到达的行程。",
            "normal": "用户可以接受隔天到达（24小时内），但不希望行程过长。",
            "long": "用户可以接受长途行程，即使需要超过24小时也可以接受，包括中转、换乘等复杂方案。"
        }[duration]

        # 获取当前日期用于12306查询限制计算
        from datetime import datetime, timedelta
        today = datetime.now()
        max_train_date = today + timedelta(days=14)  # 12306只能查15天内（含当天）
        today_str = today.strftime("%Y-%m-%d")
        max_train_date_str = max_train_date.strftime("%Y-%m-%d")

        # 获取中转枢纽模式的提示词补充
        transfer_hub_prompt = get_transfer_hub_prompt(transport, self.transfer_hub_mode)

        base_prompt = f"""你是 Go-home 智能出行助手，专门帮助用户查询机票和火车票信息，规划回家的最优路线。

【当前时间】
今天是 {today_str}

【重要：服务覆盖范围】
1. **机票服务（FlightTicketMCP）**：
   - ✅ 支持国际航班和国内航班
   - ✅ 覆盖全球主要城市（北京、上海、曼谷、新加坡、东京、纽约等）
   - ✅ 可查询任意日期的航班

2. **火车票服务（12306-MCP）**：
   - ✅ 仅支持中国国内火车票
   - ❌ 不支持国际城市（如曼谷、新加坡等无中国火车站）
   - ⚠️ 仅能查询15天内的车票

【国际出行规划策略】
当出发地或目的地包含国际城市时：
- 国际城市 → 国内城市：先查机票到达国内枢纽（如北京、上海、广州）
- 国内枢纽 → 最终目的地：可查机票或火车票
- 例如：曼谷→长治 = 曼谷✈️北京 + 北京🚄长治

【用户偏好】
{priority_text}
{transport_text}
{duration_text}

【12306火车票查询限制】
12306系统只能查询15天内（含当天）的火车票，即 {today_str} 至 {max_train_date_str}。
- 如果用户查询的日期超出此范围，请使用 {max_train_date_str} 作为查询日期
- 但在输出结果时，必须明确提示用户：
  "⚠️ 注意：12306仅支持查询15天内的车票。您查询的日期超出范围，以下展示的是 {max_train_date_str} 的班次信息作为参考。
  铁路班次时刻表通常固定不变，票价在非节假日期间也基本稳定，实际购票时请以12306官方为准。"
- 机票查询不受此限制，可以查询更远日期

【重要：工具调用参数格式】
调用工具时必须传递正确的参数，以下是具体示例：

1. 查询火车票城市代码（必须先调用）：
   工具: train_get-station-code-of-citys
   参数: {{"citys": "北京|上海"}}  // citys 参数必填，多个城市用 | 分隔

2. 查询火车票：
   工具: train_get-tickets
   参数: {{"date": "2025-01-15", "fromStation": "BJP", "toStation": "SHH"}}

3. 查询机票航线：
   工具: flight_searchFlightRoutes
   参数: {{"departCity": "北京", "arriveCity": "上海", "departDate": "2025-01-15"}}

4. 查询中转机票（需指定中转城市）：
   工具: flight_getTransferFlightsByThreePlace
   参数: {{"departCity": "北京", "transferCity": "郑州", "arriveCity": "上海", "departDate": "2025-01-15"}}

5. 查询火车票中转方案：
   工具: train_get-interline-tickets
   参数: {{"date": "2025-01-15", "fromStation": "BJP", "toStation": "CZH", "transferStation": "ZZF"}}

【工具使用流程】
- 火车票查询：先用 train_get-station-code-of-citys 获取站点代码，再用 train_get-tickets 查询
- 机票查询：直接用 flight_searchFlightRoutes，城市名使用中文
- 中转查询：需要指定中转城市/车站
{transfer_hub_prompt}
【输出要求】
1. 根据查询结果，整理出清晰的票务信息
2. 按照用户偏好排序推荐方案
3. 给出具体的推荐理由
4. 列出每个方案的关键信息：出发时间、到达时间、历时、价格
5. 使用友好的中文回复，格式清晰易读
6. 如果有多个好的选择，最多推荐3个最佳方案"""

        return base_prompt

    def start_query(self):
        """开始查询"""
        # 验证输入
        from_city = self.from_city_entry.get().strip()
        to_city = self.to_city_entry.get().strip()
        date = self.date_entry.get().strip()

        if not from_city:
            self.show_result("⚠️ 请输入出发城市")
            return
        if not to_city:
            self.show_result("⚠️ 请输入目的城市")
            return
        if not date:
            self.show_result("⚠️ 请输入出发日期")
            return

        # 检查 API 配置
        api_key = self.api_key_entry.get()
        if not api_key:
            self.show_result("⚠️ 请先在左侧配置 AI API Key，然后点击保存配置。")
            return

        # 检查 MCP 服务
        transport = self.transport_var.get()
        if transport == "flight" and not self.mcp_manager.flight_running:
            self.show_result("⚠️ 机票服务未启动，请先点击「一键启动服务」")
            return
        if transport == "train" and not self.mcp_manager.train_running:
            self.show_result("⚠️ 火车票服务未启动，请先点击「一键启动服务」")
            return
        if transport == "all" and not (self.mcp_manager.flight_running or self.mcp_manager.train_running):
            self.show_result("⚠️ MCP 服务未启动，请先点击「一键启动服务」")
            return

        # 禁用查询按钮
        self.query_btn.configure(state="disabled", text="⏳ 查询中...")
        self.is_querying = True

        # 构建查询消息
        user_message = f"请帮我查询 {date} 从 {from_city} 到 {to_city} 的出行方案。"

        self.show_result(f"🔍 正在查询 {from_city} → {to_city} ({date}) 的出行方案...\n\n请稍候，AI 正在为您分析最优路线...")
        self.log_message(f"[查询] {from_city} → {to_city}, 日期: {date}")

        # 异步调用 AI
        if self.transfer_hub_mode:
            # 中转枢纽模式：程序主动遍历枢纽查询
            thread = threading.Thread(
                target=self.call_ai_with_hub_query,
                args=(from_city, to_city, date),
                daemon=True
            )
        else:
            # 标准模式：让 AI 自己决定查询
            thread = threading.Thread(target=self.call_ai_api, args=(user_message,), daemon=True)
        thread.start()

    def call_ai_with_hub_query(self, from_city: str, to_city: str, date: str):
        """
        中转枢纽模式：使用分段查询引擎进行多线程并行查询

        新架构说明：
        - 每个线程只负责查询一段行程 (A→B)
        - 支持跨模式组合：✈️→✈️、✈️→🚄、🚄→✈️、🚄→🚄
        - 结果存储后由程序组合出所有可能的路线
        - 最后让 AI 分析推荐最优方案
        """
        transport = self.transport_var.get()

        # 获取推荐的中转枢纽城市
        hub_cities = hub_manager.get_recommended_transfer_cities(transport, max_count=8)
        hub_cities = [h for h in hub_cities if h != from_city and h != to_city]

        self.after(0, lambda: self.log_message(f"[分段查询] 准备查询，中转城市: {', '.join(hub_cities)}"))
        self.after(0, lambda: self.append_result(f"\n\n🚀 启动分段查询引擎...\n中转枢纽: {', '.join(hub_cities)}"))

        # 创建分段查询引擎
        def log_callback(msg):
            self.after(0, lambda m=msg: self.log_message(m))

        def progress_callback(current, total, desc):
            self.after(0, lambda c=current, t=total, d=desc: self.show_progress(c, t, f"🔍 {d}"))

        engine = SegmentQueryEngine(
            mcp_manager=self.mcp_manager,
            log_callback=log_callback,
            progress_callback=progress_callback
        )

        try:
            # 处理火车票日期限制
            train_date = calculate_adjusted_train_date(date)
            if train_date != date:
                self.after(0, lambda td=train_date: self.log_message(
                    f"[分段查询] 火车票日期调整为 {td}（12306 15天限制）"))

            # 构建所有分段查询请求
            queries = engine.build_segment_queries(
                origin=from_city,
                destination=to_city,
                date=date,
                hub_cities=hub_cities,
                include_direct=True,
                transport_filter=transport
            )

            self.after(0, lambda n=len(queries): self.log_message(f"[分段查询] 共 {n} 个分段查询任务"))
            self.after(0, lambda n=len(queries): self.append_result(f"\n📊 共 {n} 个分段查询任务，开始并行执行..."))

            # 并行执行所有查询
            results = engine.execute_parallel_queries(
                queries=queries,
                train_date=train_date,
                max_workers=15
            )

            # 组合所有可能的路线
            routes = engine.combine_routes(
                origin=from_city,
                destination=to_city,
                hub_cities=hub_cities,
                results=results
            )

            self.after(0, lambda n=len(routes): self.log_message(f"[分段查询] 组合出 {n} 条可行路线"))
            self.after(0, lambda n=len(routes): self.append_result(f"\n\n🛤️ 组合出 {n} 条可行路线，正在让 AI 分析..."))

            # 构建给 AI 的汇总消息
            summary_message = engine.build_summary_for_ai(
                origin=from_city,
                destination=to_city,
                date=date,
                routes=routes,
                results=results
            )

            # 调用 AI 分析
            self._call_ai_for_summary(summary_message)

        except Exception as e:
            error_msg = f"⚠️ 分段查询失败: {str(e)}"
            self.after(0, lambda msg=error_msg: self.show_result(msg))
            self.after(0, lambda err=str(e): self.log_message(f"[分段查询] 错误: {err}"))
        finally:
            self.after(0, self.hide_progress)
            self.after(0, lambda: self.query_btn.configure(state="normal", text="🔍 开始查询"))
            self.is_querying = False

    def _call_ai_for_summary(self, summary_message: str):
        """调用 AI 对查询结果进行汇总分析"""
        api_key = self.api_key_entry.get()
        base_url = self.api_url_entry.get()
        model = self.model_combobox.get()

        try:
            client = OpenAI(api_key=api_key, base_url=base_url)

            # 构建汇总分析的系统提示词
            system_prompt = """你是 Go-home 智能出行助手。用户已经通过程序查询了多个出行方案的数据，现在需要你分析这些数据并给出推荐。

请注意：
1. 仔细分析直达方案和中转方案的价格、时间对比
2. 中转方案支持跨模式组合（如：飞机+高铁、高铁+飞机等）
3. 中转方案要考虑换乘等待时间，建议预留 2-3 小时
4. 推荐时要给出具体的推荐理由
5. 使用清晰的格式，包含表格对比
6. 如果某些查询结果为空或报错，请忽略该方案
7. 国际城市（如曼谷）无法查询火车票，这是正常的

【12306查询限制说明】
火车票数据可能是15天内的参考数据，实际购票以12306为准。

【跨模式中转说明】
- ✈️→✈️：全程飞机中转
- ✈️→🚄：先飞机后高铁
- 🚄→✈️：先高铁后飞机
- 🚄→🚄：全程火车中转"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": summary_message}
            ]

            self.after(0, lambda: self.log_message("[AI] 正在分析汇总结果..."))

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7
            )

            final_content = response.choices[0].message.content or "抱歉，无法生成分析结果。"

            self.after(0, lambda msg=final_content: self.show_result(msg))
            self.after(0, lambda: self.log_message("[AI] 汇总分析完成"))

        except Exception as e:
            error_msg = f"⚠️ AI 分析失败: {str(e)}"
            self.after(0, lambda msg=error_msg: self.show_result(msg))
            self.after(0, lambda err=str(e): self.log_message(f"[AI] 汇总分析错误: {err}"))

    def call_ai_api(self, user_message: str):
        """调用 AI API 获取回复，支持 Function Calling"""
        api_key = self.api_key_entry.get()
        base_url = self.api_url_entry.get()
        model = self.model_combobox.get()

        # 构建系统提示词
        system_prompt = self.build_system_prompt()

        try:
            client = OpenAI(api_key=api_key, base_url=base_url)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            # 获取可用的 MCP 工具
            tools = self.mcp_manager.get_all_tools()

            # 根据用户选择过滤工具
            transport = self.transport_var.get()
            if transport == "flight":
                tools = [t for t in tools if t["function"]["name"].startswith("flight_")]
            elif transport == "train":
                tools = [t for t in tools if t["function"]["name"].startswith("train_")]

            has_tools = len(tools) > 0

            if has_tools:
                self.after(0, lambda: self.log_message(f"[AI] 可用工具数量: {len(tools)}"))

            # 循环处理，直到 AI 不再调用工具
            max_iterations = 10
            iteration = 0
            total_tool_calls = 0

            while iteration < max_iterations:
                iteration += 1
                self.after(0, lambda it=iteration: self.log_message(f"[AI] 第 {it} 轮对话"))
                self.after(0, lambda it=iteration, tc=total_tool_calls: self.show_progress(
                    it, max_iterations, f"🤖 AI对话中 (已调用{tc}个工具)"))

                # 调用 AI API
                if has_tools:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.7
                    )
                else:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.7
                    )

                assistant_message = response.choices[0].message

                # 检查是否有工具调用
                if assistant_message.tool_calls:
                    # 将助手消息添加到消息列表
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })

                    # 处理每个工具调用
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            tool_args = {}

                        total_tool_calls += 1
                        self.after(0, lambda tn=tool_name, ta=str(tool_args): self.log_message(f"[MCP] 调用工具: {tn}, 参数: {ta}"))
                        self.after(0, lambda it=iteration, tc=total_tool_calls: self.show_progress(
                            it, max_iterations, f"🤖 AI对话中 (已调用{tc}个工具)"))

                        # 调用 MCP 工具
                        tool_result = self.mcp_manager.call_tool(tool_name, tool_args)

                        # 截断过长的结果用于日志显示
                        log_result = tool_result[:200] + "..." if len(tool_result) > 200 else tool_result
                        self.after(0, lambda lr=log_result: self.log_message(f"[MCP] 返回: {lr}"))

                        # 将工具结果添加到消息列表
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result
                        })
                else:
                    # 没有工具调用，获取最终回复
                    final_content = assistant_message.content or "抱歉，我无法生成回复。"

                    # 在主线程更新 UI
                    self.after(0, lambda msg=final_content: self.show_result(msg))
                    self.after(0, lambda: self.log_message("[AI] 查询完成"))
                    break

            else:
                # 达到最大迭代次数
                self.after(0, lambda: self.show_result("⚠️ 处理请求时超过了最大工具调用次数，请尝试简化您的问题。"))
                self.after(0, lambda: self.log_message("[AI] 超过最大工具调用次数"))

        except Exception as e:
            error_str = str(e)
            if "thought_signature" in error_str:
                error_msg = "⚠️ AI 请求失败: 模型限制\n\n当前使用的是 thinking 类型模型，该类型模型在多轮工具调用时需要特殊处理。\n\n解决方案：请在 API 设置中选择一个非 thinking 的普通模型"
            else:
                error_msg = f"⚠️ AI 请求失败: {error_str}\n\n请检查：\n1. API Key 是否正确\n2. API Base URL 是否正确\n3. 网络连接是否正常\n4. MCP 服务是否已启动"
            self.after(0, lambda msg=error_msg: self.show_result(msg))
            self.after(0, lambda err=error_str: self.log_message(f"[AI] 错误: {err}"))

        finally:
            # 隐藏进度条并恢复查询按钮
            self.after(0, self.hide_progress)
            self.after(0, lambda: self.query_btn.configure(state="normal", text="🔍 开始查询"))
            self.is_querying = False

    def start_all_services(self):
        """一键启动所有服务"""
        self.log_message("-" * 50)
        self.log_message("正在启动 MCP 服务...")

        def start_services():
            # 启动机票服务
            if self.mcp_manager.start_flight_mcp(self.log_message):
                self.after(0, lambda: self.flight_status.configure(text_color="green"))
            else:
                self.after(0, lambda: self.flight_status.configure(text_color="red"))

            # 启动火车票服务
            if self.mcp_manager.start_train_mcp(self.log_message):
                self.after(0, lambda: self.train_status.configure(text_color="green"))
            else:
                self.after(0, lambda: self.train_status.configure(text_color="red"))

            self.after(0, lambda: self.log_message("服务启动完成！"))

        thread = threading.Thread(target=start_services, daemon=True)
        thread.start()

    def stop_all_services(self):
        """停止所有服务"""
        self.log_message("-" * 50)
        self.log_message("正在停止 MCP 服务...")
        self.mcp_manager.stop_all(self.log_message)
        self.flight_status.configure(text_color="gray")
        self.train_status.configure(text_color="gray")
        self.log_message("所有服务已停止")

    def save_api_config(self):
        """保存 API 配置"""
        self.config_manager.set("api_base_url", self.api_url_entry.get())
        self.config_manager.set("api_key", self.api_key_entry.get())
        self.config_manager.set("model", self.model_combobox.get())
        self.config_manager.save_config()
        self.log_message("API 配置已保存")

    def fetch_available_models(self):
        """获取可用模型列表"""
        api_key = self.api_key_entry.get()
        base_url = self.api_url_entry.get()

        if not api_key:
            self.log_message("[错误] 请先填写 API Key")
            return

        self.log_message(f"正在获取模型列表: {base_url}")
        self.fetch_models_btn.configure(state="disabled")

        def fetch_models():
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                models_response = client.models.list()

                # 提取模型ID列表
                model_ids = [model.id for model in models_response.data]
                model_ids.sort()

                if model_ids:
                    self.available_models = model_ids
                    current_model = self.model_combobox.get()

                    self.after(0, lambda: self.model_combobox.configure(values=model_ids))

                    # 如果当前选择的模型在列表中，保持选择
                    if current_model in model_ids:
                        self.after(0, lambda: self.model_combobox.set(current_model))
                    else:
                        self.after(0, lambda: self.model_combobox.set(model_ids[0]))

                    self.after(0, lambda: self.log_message(f"[成功] 获取到 {len(model_ids)} 个可用模型"))
                else:
                    self.after(0, lambda: self.log_message("[警告] 未获取到任何模型"))

            except Exception as e:
                self.after(0, lambda: self.log_message(f"[失败] 获取模型列表失败: {str(e)}"))

            finally:
                self.after(0, lambda: self.fetch_models_btn.configure(state="normal"))

        thread = threading.Thread(target=fetch_models, daemon=True)
        thread.start()

    def toggle_transfer_hub_mode(self):
        """切换中转枢纽模式"""
        new_mode = self.hub_mode_switch_var.get() == "on"

        if new_mode:
            # 显示确认弹窗
            result = messagebox.askyesno(
                "启用中转枢纽模式",
                "🚉 中转枢纽模式说明\n\n"
                "开启后，系统将自动通过主要交通枢纽查询中转方案：\n\n"
                "✅ 优点：\n"
                "  • 可能找到更便宜的组合票价\n"
                "  • 覆盖无直达线路的情况\n"
                "  • 智能推荐最优中转城市\n\n"
                "⚠️ 注意：\n"
                "  • API 调用次数将显著增加（约2-3倍）\n"
                "  • 查询时间会相应延长\n"
                "  • 会消耗更多的 API 费用\n\n"
                "是否确认启用？",
                icon="question"
            )

            if result:
                self.transfer_hub_mode = True
                self.hub_mode_status.configure(
                    text="当前：枢纽模式（查中转）",
                    text_color="green"
                )
                self.log_message("[模式] 已启用中转枢纽模式")
            else:
                # 用户取消，恢复开关状态
                self.hub_mode_switch_var.set("off")
                self.hub_mode_switch.deselect()
        else:
            self.transfer_hub_mode = False
            self.hub_mode_status.configure(
                text="当前：标准模式（仅查直达）",
                text_color="gray"
            )
            self.log_message("[模式] 已切换回标准模式")

    def change_theme(self, theme: str):
        """切换主题"""
        ctk.set_appearance_mode(theme)
        self.config_manager.set("theme", theme)
        self.config_manager.save_config()
        self.log_message(f"主题已切换为: {theme}")

    def on_closing(self):
        """关闭窗口时的处理"""
        self.log_message("正在关闭程序...")
        self.mcp_manager.stop_all()
        self.config_manager.save_config()
        self.destroy()


def main():
    """主函数"""
    app = GoHomeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
