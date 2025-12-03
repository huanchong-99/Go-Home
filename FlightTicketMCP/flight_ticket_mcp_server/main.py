"""
Main entry point for the Flight Ticket MCP Server.
Acts as the central controller for the MCP server that handles flight ticket operations.
Supports multiple transports: stdio, sse, and streamable-http using standalone FastMCP.
"""

import os
import sys

# 检测是否作为子进程运行（无控制台）
# 当 stdin/stdout 不是 TTY 时（如被 GUI 程序作为子进程启动）
_is_subprocess = not sys.stdout.isatty() or not sys.stdin.isatty()
_is_frozen = getattr(sys, 'frozen', False)

if _is_subprocess and _is_frozen:
    # 在打包环境中作为子进程运行时，禁用所有终端相关功能
    os.environ['NO_COLOR'] = '1'
    os.environ['TERM'] = 'dumb'
    os.environ['FORCE_COLOR'] = '0'
    os.environ['COLORTERM'] = ''
    os.environ['RICH_FORCE_TERMINAL'] = ''

    # 关键修复：在导入 fastmcp 之前，先 patch rich.console.Console
    # 使其在 Windows 无控制台环境下不会崩溃
    import rich.console

    _original_console_init = rich.console.Console.__init__

    def _patched_console_init(self, *args, **kwargs):
        # 强制禁用所有特殊渲染功能
        kwargs['force_terminal'] = False
        kwargs['force_interactive'] = False
        kwargs['force_jupyter'] = False
        kwargs['no_color'] = True
        kwargs['color_system'] = None  # 完全禁用颜色系统
        kwargs['legacy_windows'] = False  # 禁用 legacy Windows 渲染
        _original_console_init(self, *args, **kwargs)

    rich.console.Console.__init__ = _patched_console_init

    # 同时 patch _write_buffer 方法来捕获任何遗漏的错误
    _original_write_buffer = rich.console.Console._write_buffer

    def _safe_write_buffer(self):
        try:
            _original_write_buffer(self)
        except OSError:
            # 忽略 Windows 控制台错误
            pass

    rich.console.Console._write_buffer = _safe_write_buffer

# Set required environment variable for FastMCP 2.8.1+
os.environ.setdefault('FASTMCP_LOG_LEVEL', 'INFO')


def load_env_file(env_file_path='.env'):
    """
    Load environment variables from .env file if it exists.
    
    Args:
        env_file_path (str): Path to the .env file
    """
    if os.path.exists(env_file_path):
        print(f"Loading environment variables from {env_file_path}")
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # Only set if not already set
                    if key not in os.environ:
                        os.environ[key] = value
        print("Environment variables loaded successfully")
    else:
        print(f"No .env file found at {env_file_path}, using system environment variables")


# Load environment variables from .env file
load_env_file()

from fastmcp import FastMCP
from .tools import flight_search_tools
from .tools import date_tools
from .tools import flight_transfer_tools
from .tools import weather_tools
from .tools import flight_info_tools
from .tools import simple_opensky_tools 


def get_transport_config():
    """
    Get transport configuration from environment variables.
    
    Returns:
        dict: Transport configuration with type, host, port, and other settings
    """
    # Default configuration
    config = {
        'transport': 'sse',  # Default to SSE mode
        'host': '127.0.0.1',
        'port': 8000,
        'path': '/mcp',
        'sse_path': '/sse'
    }
    
    # Override with environment variables if provided
    transport = os.getenv('MCP_TRANSPORT', 'stdio').lower()
    print(f"Transport: {transport}")
    
    # Validate transport type - 更新有效的传输协议列表
    valid_transports = ['stdio', 'sse', 'http', 'streamable-http']
    if transport not in valid_transports:
        print(f"Warning: Invalid transport '{transport}'. Falling back to 'stdio'.")
        transport = 'stdio'
    
    # 规范化传输协议名称
    if transport == 'streamable-http':
        transport = 'streamable-http'  # 保持原名称用于显示
    
    config['transport'] = transport
    config['host'] = os.getenv('MCP_HOST', config['host'])
    config['port'] = int(os.getenv('MCP_PORT', config['port']))
    config['path'] = os.getenv('MCP_PATH', config['path'])
    config['sse_path'] = os.getenv('MCP_SSE_PATH', config['sse_path'])
    
    return config


def setup_logging(debug_mode):
    """
    Setup logging based on debug mode and environment variables.
    
    Args:
        debug_mode (bool): Whether to enable debug logging
    """
    import logging
    import logging.handlers
    import os
    from datetime import datetime
    
    # 从环境变量获取配置
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file_path = os.getenv('LOG_FILE_PATH', 'logs/flight_server.log')
    log_error_file_path = os.getenv('LOG_ERROR_FILE_PATH', 'logs/flight_server_error.log')
    log_debug_file_path = os.getenv('LOG_DEBUG_FILE_PATH', 'logs/flight_server_debug.log')
    log_max_size = int(os.getenv('LOG_MAX_SIZE', '10')) * 1024 * 1024  # Convert MB to bytes
    log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # 创建logs目录
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 设置日志级别
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = log_level_map.get(log_level_str, logging.INFO)
    
    # 如果debug_mode为True，覆盖为DEBUG级别
    if debug_mode:
        log_level = logging.DEBUG
    
    # 创建根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 日志格式
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter if not debug_mode else detailed_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器 - 一般日志
    info_file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=log_max_size,
        backupCount=log_backup_count,
        encoding='utf-8'
    )
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(info_file_handler)
    
    # 错误日志文件处理器
    error_file_handler = logging.handlers.RotatingFileHandler(
        log_error_file_path,
        maxBytes=log_max_size,
        backupCount=max(1, log_backup_count - 2),  # 错误日志保留较少备份
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # 调试模式下的额外配置
    if debug_mode or log_level == logging.DEBUG:
        debug_file_handler = logging.handlers.RotatingFileHandler(
            log_debug_file_path,
            maxBytes=log_max_size * 5,  # 调试日志文件更大
            backupCount=max(1, log_backup_count - 3),  # 调试日志保留更少备份
            encoding='utf-8'
        )
        debug_file_handler.setLevel(logging.DEBUG)
        debug_file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(debug_file_handler)
        
        print(f"Debug logging enabled - logs will be saved to {log_dir}/ directory")
    else:
        print(f"Logging enabled - logs will be saved to {log_dir}/ directory")
    
    # 为项目模块设置特定的日志级别
    project_logger = logging.getLogger('tools')
    project_logger.setLevel(log_level)
    
    # 记录启动信息
    logging.info(f"Flight Ticket MCP Server logging initialized - Level: {log_level_str}, Debug: {debug_mode}")
    logging.info(f"Log files location: {os.path.abspath(log_dir)}")
    logging.info(f"Log configuration - Max size: {log_max_size//1024//1024}MB, Backup count: {log_backup_count}")


# Initialize FastMCP server
mcp = FastMCP("Flight Ticket Server")


def register_tools():
    """Register all tools with the MCP server using FastMCP decorators."""
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("开始注册MCP工具...")
    
    # Flight route search tool
    @mcp.tool()
    def searchFlightRoutes(departure_city: str, destination_city: str, departure_date: str):
        """航班路线查询 - 根据出发地、目的地和出发日期查询可用航班信息"""
        logger.debug(f"调用航班路线查询工具: departure_city={departure_city}, destination_city={destination_city}, departure_date={departure_date}")
        return flight_search_tools.searchFlightRoutes(departure_city, destination_city, departure_date)
    
    # Date tools
    @mcp.tool()
    def getCurrentDate():
        """获取当前日期 - 返回格式为 yyyy-MM-dd 的当前日期字符串"""
        logger.debug("调用获取当前日期工具")
        return date_tools.getCurrentDate()

    # Flight transfer search tools
    @mcp.tool()
    def getTransferFlightsByThreePlace(from_place: str="北京", transfer_place: str="香港", to_place: str="纽约",min_transfer_time: float = 2.0, max_transfer_time: float = 5.0):
        """航班中转路线查询 - 根据出发地、中转地、目的地、最小转机时间、最大转机时间查询中转航班信息，最小转机时间默认为2小时，最大转机时间默认为5小时"""
        logger.debug(f"调用航班中转查询工具：: from_place={from_place}, transfer_place={transfer_place}, to_place={to_place}")
        logger.debug(f"最短换乘时间: min_transfer_time={from_place},默认2小时 最长换乘时间：max_transfer_time={max_transfer_time}, 默认5小时")
        return flight_transfer_tools.getTransferFlightsByThreePlace(from_place, transfer_place, to_place, min_transfer_time, max_transfer_time)

    # Weather query tools
    @mcp.tool()
    def getWeatherByLocation(latitude: float, longitude: float, start_date: str = None, end_date: str = None):
        """天气信息查询 - 根据经纬度查询天气信息，使用Open-Meteo API。如果不提供日期，默认查询今天和明天的天气数据"""
        logger.debug(f"调用天气查询工具: latitude={latitude}, longitude={longitude}, start_date={start_date}, end_date={end_date}")
        return weather_tools.getWeatherByLocation(latitude, longitude, start_date, end_date)

    @mcp.tool()
    def getWeatherByCity(city_name: str, start_date: str = None, end_date: str = None):
        """城市天气查询 - 根据城市名查询天气信息。支持武汉、北京、上海等主要城市。如果不提供日期，默认查询今天和明天的天气数据"""
        logger.debug(f"调用城市天气查询工具: city_name={city_name}, start_date={start_date}, end_date={end_date}")
        return weather_tools.getWeatherByCity(city_name, start_date, end_date)

    # Flight info query tool
    @mcp.tool()
    def getFlightInfo(flight_number: str):
        """航班信息查询 - 根据航班号查询详细的航班信息，包括航班状态、座位配置、价格、天气等"""
        logger.debug(f"调用航班信息查询工具: flight_number={flight_number}")
        return flight_info_tools.getFlightInfo(flight_number)

    # Simple OpenSky Network tools for real-time flight tracking
    @mcp.tool()
    def getFlightStatus(flight_number: str, date: str = None):
        """航班实时状态查询 - 使用OpenSky Network查询航班实时位置和状态。flight_number为航班呼号(如CCA1234)，date参数无效(仅支持实时数据)"""
        logger.debug(f"调用航班实时状态查询工具: flight_number={flight_number}, date={date}")
        return simple_opensky_tools.getFlightStatus(flight_number, date)

    @mcp.tool()
    def getAirportFlights(airport_code: str, flight_type: str = "departure"):
        """机场周边航班查询 - 查询指定机场周边30公里范围内的所有航班。支持主要机场代码如PEK、PVG、CAN等"""
        logger.debug(f"调用机场周边航班查询工具: airport_code={airport_code}, flight_type={flight_type}")
        return simple_opensky_tools.getAirportFlights(airport_code, flight_type)

    @mcp.tool()
    def getFlightsInArea(min_lat: float, max_lat: float, min_lon: float, max_lon: float):
        """区域航班查询 - 查询指定地理区域内的所有航班。参数为边界框坐标(最小纬度,最大纬度,最小经度,最大经度)"""
        logger.debug(f"调用区域航班查询工具: bbox=({min_lat}, {max_lat}, {min_lon}, {max_lon})")
        return simple_opensky_tools.getFlightsInArea(min_lat, max_lat, min_lon, max_lon)

    @mcp.tool()
    def trackMultipleFlights(flight_numbers: list, date: str = None):
        """批量航班跟踪 - 同时查询多个航班的实时状态。flight_numbers为航班呼号列表，如['CCA1234','CSN5678']"""
        logger.debug(f"调用批量航班跟踪工具: flight_numbers={flight_numbers}, date={date}")
        return simple_opensky_tools.trackMultipleFlights(flight_numbers, date)

    logger.info("MCP工具注册完成 - 已注册工具: searchFlightRoutes, getCurrentDate, getTransferFlightsByThreePlace, getWeatherByLocation, getWeatherByCity, getFlightInfo, getFlightStatus, getAirportFlights, getFlightsInArea, trackMultipleFlights")


def run_server():
    """
    Run the Flight Ticket MCP server.
    
    This function sets up the server configuration, registers all tools,
    and starts the server with the specified transport method.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get configuration
        config = get_transport_config()
        logger.info(f"服务器配置加载完成: {config}")
        
        # Setup logging
        debug_mode = os.getenv('MCP_DEBUG', 'false').lower() in ('true', '1', 'yes')
        setup_logging(debug_mode)
        
        print("Flight Ticket MCP Server starting...")
        print(f"Transport: {config['transport']}")
        logger.info(f"Flight Ticket MCP Server 启动中... 传输协议: {config['transport']}")
        
        # Register all tools
        register_tools()
        print("All tools registered successfully")
        logger.info("所有工具注册成功")
        
        # Start server based on transport type
        if config['transport'] == 'stdio':
            print("Starting stdio transport...")
            logger.info("启动stdio传输协议...")
            mcp.run()
        elif config['transport'] == 'sse':
            print(f"Starting SSE transport on {config['host']}:{config['port']}{config['sse_path']}")
            logger.info(f"启动SSE传输协议: {config['host']}:{config['port']}{config['sse_path']}")
            # 使用正确的FastMCP SSE启动方法
            mcp.run(
                transport="sse",
                host=config['host'],
                port=config['port'],
                path=config['sse_path']
            )
        elif config['transport'] == 'streamable-http':
            print(f"Starting HTTP transport on {config['host']}:{config['port']}{config['path']}")
            logger.info(f"启动HTTP传输协议: {config['host']}:{config['port']}{config['path']}")
            # 使用正确的FastMCP HTTP启动方法
            mcp.run(
                transport="http",
                host=config['host'],
                port=config['port'],
                path=config['path']
            )
        else:
            error_msg = f"Unsupported transport: {config['transport']}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    except KeyboardInterrupt:
        print("\nShutting down Flight Ticket MCP Server...")
        logger.info("用户中断，正在关闭Flight Ticket MCP Server...")
    except Exception as e:
        error_msg = f"Error starting server: {e}"
        print(error_msg)
        logger.error(f"服务器启动失败: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point for the application."""
    try:
        run_server()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 