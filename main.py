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
from datetime import datetime
from typing import Optional, List, Dict, Any
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


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

        # API 配置区
        self.api_frame = ctk.CTkFrame(self.sidebar)
        self.api_frame.grid(row=3, column=0, padx=15, pady=10, sticky="ew")

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

        # 连接测试按钮
        self.test_api_btn = ctk.CTkButton(
            self.api_frame,
            text="🔗 测试连接",
            command=self.test_api_connection,
            height=35,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        self.test_api_btn.grid(row=8, column=0, padx=10, pady=(0, 10), sticky="ew")

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
        self.main_frame.grid_rowconfigure(1, weight=3)  # 对话区占更多空间
        self.main_frame.grid_rowconfigure(2, weight=1)  # 日志区

        # 标题区
        self.title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        self.main_title = ctk.CTkLabel(
            self.title_frame,
            text="🤖 AI 智能助手",
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

        # 对话区域
        self.create_chat_area()

        # 日志区域
        self.create_log_area()

        # 初始日志
        self.log_message("=" * 50)
        self.log_message("Go-home - 回家最优路线查询系统")
        self.log_message("=" * 50)
        self.log_message(f"Python: {PYTHON_EXE}")
        self.log_message(f"Node.js: {NODE_EXE}")
        self.log_message("-" * 50)
        self.log_message("请先启动 MCP 服务，然后配置 AI API")

    def create_chat_area(self):
        """创建对话区域"""
        self.chat_frame = ctk.CTkFrame(self.main_frame)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(1, weight=1)

        # 对话标题
        self.chat_title = ctk.CTkLabel(
            self.chat_frame,
            text="💬 对话",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.chat_title.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        # 对话历史显示
        self.chat_history = ctk.CTkTextbox(
            self.chat_frame,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            wrap="word",
            state="disabled"
        )
        self.chat_history.grid(row=1, column=0, padx=15, pady=(5, 10), sticky="nsew")

        # 输入区域框架
        self.input_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        # 输入框
        self.chat_input = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="输入你的问题，例如：查询明天从北京到上海的机票和火车票...",
            font=ctk.CTkFont(size=13),
            height=40
        )
        self.chat_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.chat_input.bind("<Return>", self.on_send_message)

        # 发送按钮
        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="发送",
            command=self.send_message,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=80,
            height=40
        )
        self.send_btn.grid(row=0, column=1)

        # 清空对话按钮
        self.clear_chat_btn = ctk.CTkButton(
            self.input_frame,
            text="清空",
            command=self.clear_chat,
            font=ctk.CTkFont(size=14),
            width=60,
            height=40,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        self.clear_chat_btn.grid(row=0, column=2, padx=(10, 0))

        # 初始化对话历史
        self.conversation_history: List[Dict[str, str]] = []
        self.add_chat_message("assistant", "你好！我是 Go-home 智能助手 🏠\n\n我可以帮你查询机票和火车票信息，找到回家的最优路线。\n\n请先：\n1. 点击左侧 [一键启动服务] 启动 MCP 服务\n2. 配置 AI API 并保存\n3. 然后就可以开始对话了！\n\n示例问题：\n• 查询明天从北京到上海的机票\n• 帮我看看后天广州到武汉的高铁票\n• 我想从深圳回成都，有什么交通方案？")

    def create_log_area(self):
        """创建日志区域"""
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.log_frame.grid(row=2, column=0, sticky="nsew")
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
            height=120
        )
        self.log_textbox.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")

    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")

    def add_chat_message(self, role: str, content: str):
        """添加对话消息到显示区"""
        self.chat_history.configure(state="normal")

        if role == "user":
            prefix = "👤 你：\n"
            self.chat_history.insert("end", prefix, "user_prefix")
        else:
            prefix = "🤖 助手：\n"
            self.chat_history.insert("end", prefix, "assistant_prefix")

        self.chat_history.insert("end", f"{content}\n\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

    def on_send_message(self, event=None):
        """回车键发送消息"""
        self.send_message()

    def send_message(self):
        """发送消息并获取 AI 回复"""
        message = self.chat_input.get().strip()
        if not message:
            return

        # 检查 API 配置
        api_key = self.api_key_entry.get()
        if not api_key:
            self.add_chat_message("assistant", "⚠️ 请先在左侧配置 AI API Key，然后点击保存配置。")
            return

        # 清空输入框
        self.chat_input.delete(0, "end")

        # 显示用户消息
        self.add_chat_message("user", message)

        # 添加到对话历史
        self.conversation_history.append({"role": "user", "content": message})

        # 禁用发送按钮
        self.send_btn.configure(state="disabled", text="思考中...")
        self.log_message(f"[AI] 用户问题: {message[:50]}...")

        # 异步调用 AI
        thread = threading.Thread(target=self.call_ai_api, args=(message,), daemon=True)
        thread.start()

    def call_ai_api(self, user_message: str):
        """调用 AI API 获取回复，支持 Function Calling"""
        api_key = self.api_key_entry.get()
        base_url = self.api_url_entry.get()
        model = self.model_combobox.get()

        # 系统提示词
        system_prompt = """你是 Go-home 智能出行助手，专门帮助用户查询机票和火车票信息，规划回家的最优路线。

你可以使用可用的 MCP 工具来查询实时的机票和火车票信息。

使用工具时的注意事项：
1. 查询火车票时，需要先使用 train_get-station-code-of-citys 获取城市的 station_code，再用于查询
2. 查询机票时，城市名需要使用中文
3. 日期格式为 yyyy-MM-dd，如需获取当前日期可调用相应工具
4. 请根据查询结果为用户整理出清晰的票务信息和出行建议

请用友好的中文回复用户，并给出具体的票务信息和推荐方案。"""

        try:
            client = OpenAI(api_key=api_key, base_url=base_url)

            messages = [{"role": "system", "content": system_prompt}]
            # 只保留最近10轮对话
            messages.extend(self.conversation_history[-20:])

            # 获取可用的 MCP 工具
            tools = self.mcp_manager.get_all_tools()
            has_tools = len(tools) > 0

            if has_tools:
                self.after(0, lambda: self.log_message(f"[AI] 可用工具数量: {len(tools)}"))

            # 循环处理，直到 AI 不再调用工具
            max_iterations = 10  # 防止无限循环
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

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

                        self.after(0, lambda tn=tool_name: self.log_message(f"[MCP] 调用工具: {tn}"))

                        # 调用 MCP 工具
                        tool_result = self.mcp_manager.call_tool(tool_name, tool_args)

                        self.after(0, lambda: self.log_message(f"[MCP] 工具返回结果"))

                        # 将工具结果添加到消息列表
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result
                        })
                else:
                    # 没有工具调用，获取最终回复
                    final_content = assistant_message.content or "抱歉，我无法生成回复。"

                    # 添加到对话历史
                    self.conversation_history.append({"role": "assistant", "content": final_content})

                    # 在主线程更新 UI
                    self.after(0, lambda msg=final_content: self.add_chat_message("assistant", msg))
                    self.after(0, lambda: self.log_message("[AI] 回复已生成"))
                    break

            else:
                # 达到最大迭代次数
                self.after(0, lambda: self.add_chat_message("assistant", "⚠️ 处理请求时超过了最大工具调用次数，请尝试简化您的问题。"))
                self.after(0, lambda: self.log_message("[AI] 超过最大工具调用次数"))

        except Exception as e:
            error_str = str(e)
            # 检查是否是 thinking 模型的特殊错误
            if "thought_signature" in error_str:
                error_msg = "AI 请求失败: 模型限制\n\n当前使用的是 thinking 类型模型，该类型模型在多轮工具调用时需要特殊处理。\n\n解决方案：请在 API 设置中选择一个非 thinking 的普通模型"
            else:
                error_msg = f"AI 请求失败: {error_str}\n\n请检查：\n1. API Key 是否正确\n2. API Base URL 是否正确\n3. 网络连接是否正常\n4. MCP 服务是否已启动"
            self.after(0, lambda msg=error_msg: self.add_chat_message("assistant", msg))
            self.after(0, lambda err=error_str: self.log_message(f"[AI] 错误: {err}"))

        finally:
            # 恢复发送按钮
            self.after(0, lambda: self.send_btn.configure(state="normal", text="发送"))

    def clear_chat(self):
        """清空对话"""
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        self.chat_history.configure(state="disabled")
        self.conversation_history.clear()
        self.add_chat_message("assistant", "对话已清空。有什么可以帮你的吗？")
        self.log_message("[AI] 对话历史已清空")

    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.configure(text=current_time)
        self.after(1000, self.update_time)

    def start_all_services(self):
        """一键启动所有服务"""
        self.log_message("-" * 60)
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
        self.log_message("-" * 60)
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

    def test_api_connection(self):
        """测试 API 连接"""
        api_key = self.api_key_entry.get()
        base_url = self.api_url_entry.get()
        model = self.model_combobox.get()

        if not api_key:
            self.log_message("[错误] 请先填写 API Key")
            return

        self.log_message(f"正在测试 API 连接: {base_url}")

        def test_connection():
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                self.after(0, lambda: self.log_message(f"[成功] API 连接成功！模型: {model}"))
                self.openai_client = client
            except Exception as e:
                self.after(0, lambda: self.log_message(f"[失败] API 连接失败: {str(e)}"))

        thread = threading.Thread(target=test_connection, daemon=True)
        thread.start()

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
