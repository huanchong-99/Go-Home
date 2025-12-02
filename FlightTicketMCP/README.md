# Flight Ticket MCP Server

一个基于模型上下文协议(MCP)的航空机票查询服务器。该服务器为AI助手提供标准化的航班实时动态查询功能接口。

## 概述

Flight Ticket MCP Server 实现了供航空机票相关查询操作的工具和资源。它作为AI助手与航空服务系统之间的桥梁，专注于航班实时动态查询功能。

该服务器采用模块化架构，将核心功能、工具和实用程序分离，使其具有高度的可维护性和可扩展性。

## 功能特性

### 航班路线查询
- 根据出发地、目的地和出发日期查询可用航班
- 支持282个国内城市和机场代码
- 智能城市名称解析（支持城市名、机场代码、完整格式）
- 实时航班价格和航班时刻信息
- 航空公司和机型信息
- 航站楼和登机口信息
- 价格统计和航空公司分布
- 格式化输出结果

### 航班中转路线查询
- 根据出发地、中转地、目的地查询联程航班
- 支持自定义最小和最大中转时间（默认2-5小时）
- 智能筛选符合中转时间要求的航班组合
- 提供完整的两段航程信息
- 支持国内外航线中转查询
- 详细的中转时间计算和验证

### 天气信息查询
- **按经纬度查询**：精确地理位置天气查询
- **按城市名查询**：支持主要城市直接查询
- 支持历史、当前和未来天气数据
- 提供温度、湿度、风速、天气状况等详细信息
- 自动处理时区和日期范围
- 支持武汉、北京、上海等主要城市预设

### 航班信息查询
- 根据航班号查询详细的航班信息
- 包含航班状态、座位配置、价格信息
- 提供天气信息（出发地和目的地）
- 显示航班基本信息（航空公司、机型、航线类型）
- 详细的航站楼、登机口信息
- 实时动态状态（准时、延误、登机、飞行中等）
- 座位价格和可用性信息
- 附加服务信息（餐食、WiFi、娱乐系统等）

### 实时航班跟踪
- **航班实时状态查询**：查询航班实时位置和状态
- **机场周边航班查询**：查询指定机场周边30公里范围内的所有航班
- **区域航班查询**：查询指定地理区域内的所有实时航班
- **批量航班跟踪**：同时跟踪多个航班的实时状态
- 支持中国主要机场代码（PEK、PVG、CAN等70+机场）
- 提供详细的航班位置、速度、高度、状态信息
- 无需认证的公开API，实时更新航班数据

### 日期时间工具  
- 获取当前系统日期（YYYY-MM-DD格式）
- 获取当前系统日期时间（YYYY-MM-DD HH:mm:ss格式）
- 为其他功能提供标准化的日期时间支持
- 自动处理时区和格式转换

### 数据处理与智能化
- **智能城市解析**：支持多种城市输入格式（城市名、机场代码、完整格式）
- **参数验证**：全面的输入参数验证和错误处理
- **结果格式化**：统一的JSON格式输出，便于AI助手解析
- **错误恢复**：完善的异常处理和降级机制
- **日志记录**：详细的操作日志和调试信息

## 技术架构

### 核心模块 (Core)
- 航班数据模型和结构定义
- 机场、航空公司、航班、价格等数据模型
- 航班中转和座位配置数据结构

### 工具模块 (Tools)
- **航班搜索工具** (`flight_search_tools.py`) - 航班路线查询功能
- **航班中转工具** (`flight_transfer_tools.py`) - 多段航程和中转查询  
- **航班信息工具** (`flight_info_tools.py`) - 根据航班号查询详细信息
- **实时航班跟踪工具** (`simple_opensky_tools.py`) - 基于OpenSky Network的实时航班跟踪
- **天气查询工具** (`weather_tools.py`) - 基于经纬度和城市的天气查询
- **日期时间工具** (`date_tools.py`) - 日期时间获取和处理

### 实用工具 (Utils)
- **城市字典** (`cities_dict.py`) - 282个城市和机场代码映射
- **数据验证器** (`validators.py`) - 输入参数验证和格式检查
- **日期工具** (`date_utils.py`) - 日期格式化和时区处理
- **API客户端** (`api_client.py`) - HTTP请求封装和错误处理

### MCP集成层
- **FastMCP服务器** - 基于FastMCP框架的MCP协议实现
- **多传输协议支持** - stdio、SSE、HTTP传输协议
- **工具注册管理** - 统一的工具注册和调用机制
- **环境配置管理** - 灵活的配置和环境变量支持

## 支持的传输协议

本服务器支持三种传输协议：

1. **sse** - Server-Sent Events（默认，适用于Web应用）
2. **stdio** - 标准输入输出（适用于Claude Desktop）
3. **streamable-http** - 可流式HTTP（适用于HTTP客户端）

## 安装

### 前置要求
- Python 3.11 或更高版本
- pip 包管理器（或 uvx 工具）

### 方式一：从PyPI安装（推荐）

```bash
# 使用pip安装
pip install flight-ticket-mcp-server

# 或使用uvx直接运行（无需安装）
uvx flight-ticket-mcp-server

# 或使用uvx安装后运行
uvx --install flight-ticket-mcp-server
```

### 方式二：本地开发安装
```bash
# 克隆或下载项目
cd FlightTicketMCP

# 安装依赖
pip install -r requirements.txt

# 或从本地源码安装
pip install -e .
```

### uvx 使用说明

uvx 是一个现代的Python包运行工具，可以直接运行PyPI包而无需先安装到系统环境：

```bash
# 安装uv（包含uvx工具）
pip install uv

# 直接运行MCP服务器（无需安装）
uvx flight-ticket-mcp-server

# 使用最新版本（推荐）
uvx flight-ticket-mcp-server@latest

# 带参数运行
uvx flight-ticket-mcp-server --help

# 指定版本运行
uvx flight-ticket-mcp-server==1.0.1

# 强制重新安装最新版本
uvx flight-ticket-mcp-server@latest --help
```

**uvx 的优势：**
- 🚀 无需污染全局Python环境
- 📦 自动管理虚拟环境
- 🔄 支持直接运行最新版本
- 🛡️ 隔离依赖，避免冲突

## 启动方式

### 1. 直接启动（默认SSE模式）

```bash
# 使用主启动文件（默认启动SSE模式，监听127.0.0.1:8000）
python flight_ticket_server.py

# 或者直接运行main.py
python main.py
```

### 2. 调试模式启动

```bash
# 启用调试模式，会输出详细日志
set MCP_DEBUG=true
python flight_ticket_server.py

# Linux/macOS
export MCP_DEBUG=true
python flight_ticket_server.py
```

### 3. 不同传输协议启动

#### SSE模式（默认）
```bash
# 直接启动，使用默认SSE配置（127.0.0.1:8000）
python flight_ticket_server.py
```

#### stdio模式
```bash
# Windows
set MCP_TRANSPORT=stdio
python flight_ticket_server.py

# Linux/macOS
export MCP_TRANSPORT=stdio
python flight_ticket_server.py
```

#### HTTP模式
```bash
# Windows
set MCP_TRANSPORT=streamable-http
set MCP_HOST=127.0.0.1
set MCP_PORT=8000
python flight_ticket_server.py

# Linux/macOS
export MCP_TRANSPORT=streamable-http
export MCP_HOST=127.0.0.1
export MCP_PORT=8000
python flight_ticket_server.py
```

### 4. 环境变量配置

#### 使用 .env 文件（推荐）

项目提供了 `.env.example` 文件作为配置模板：

1. **复制配置模板**：
   ```bash
   # 复制配置模板
   cp .env.example .env
   ```

2. **编辑配置文件**：
   打开 `.env` 文件，根据需要修改配置值：
   ```env
   # MCP服务器配置
   MCP_TRANSPORT=sse
   MCP_HOST=127.0.0.1
   MCP_PORT=8000
   MCP_SSE_PATH=/sse
   
   # 日志配置
   LOG_LEVEL=INFO
   LOG_FILE_PATH=logs/flight_server.log
   LOG_MAX_SIZE=10
   LOG_BACKUP_COUNT=5
   
   # 开发配置
   MCP_DEBUG=false
   ```

3. **配置说明**：
   - `.env` 文件包含敏感配置，不会被提交到版本控制
   - `.env.example` 是安全的模板文件，可以提交到Git
   - 环境变量优先级：系统环境变量 > .env文件 > 程序默认值

#### 直接设置环境变量

如果不使用 `.env` 文件，也可以直接设置环境变量：

支持的环境变量：

| 变量名 | 描述 | 默认值 | 可选值 |
|--------|------|--------|--------|
| `MCP_TRANSPORT` | 传输协议类型 | `sse` | `stdio`, `sse`, `streamable-http` |
| `MCP_HOST` | 服务器主机地址 | `127.0.0.1` | 任何有效IP地址 |
| `MCP_PORT` | 服务器端口 | `8000` | 1-65535 |
| `MCP_PATH` | HTTP路径 | `/mcp` | 任何有效路径 |
| `MCP_SSE_PATH` | SSE路径 | `/sse` | 任何有效路径 |
| `MCP_DEBUG` | 调试模式 | `false` | `true`, `false`, `1`, `0` |
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FILE_PATH` | 日志文件路径 | `logs/flight_server.log` | 任何有效路径 |
| `LOG_MAX_SIZE` | 日志文件最大大小(MB) | `10` | 正整数 |
| `LOG_BACKUP_COUNT` | 日志备份数量 | `5` | 正整数 |
| `FASTMCP_LOG_LEVEL` | FastMCP日志级别 | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### 5. 启动验证

启动成功后，您会看到类似输出：

```
Transport: sse
Logging enabled - logs will be saved to logs/ directory
Flight Ticket MCP Server starting...
Transport: sse
All tools registered successfully
Starting SSE transport on 127.0.0.1:8000/sse
```

### 6. 日志文件

服务器启动后会在 `logs/` 目录下生成以下日志文件：

- `flight_server.log` - 一般日志（INFO级别及以上）
- `flight_server_error.log` - 错误日志（ERROR级别）
- `flight_server_debug.log` - 调试日志（仅在调试模式下生成）

### 7. 停止服务器

- **stdio模式**: 按 `Ctrl+C` 停止
- **HTTP/SSE模式**: 按 `Ctrl+C` 或发送SIGTERM信号

## 使用方法

### MCP客户端配置

#### 方式一：使用uvx（推荐）

使用uvx运行MCP服务器，无需预先安装，简洁优雅：

```json
{
  "mcpServers": {
    "flight-ticket-server": {
      "command": "uvx",
      "args": ["flight-ticket-mcp-server@latest"]
    }
  }
}
```

**uvx配置的优势：**
- 🚀 无需预先安装包
- 📦 自动管理依赖和虚拟环境
- 🔄 始终运行最新版本
- 🛡️ 隔离环境，避免冲突

#### 方式二：使用pip安装后运行

如果已通过pip安装，可以直接使用命令行工具：

```json
{
  "mcpServers": {
    "flight-ticket-server": {
      "command": "flight-ticket-mcp-server"
    }
  }
}
```

#### 方式三：本地开发版本

对于本地开发或自定义版本：

```json
{
  "mcpServers": {
    "flight-ticket-server": {
      "command": "python",
      "args": ["D:\\FlightTicketMCP\\flight_ticket_server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

#### 配置文件位置

将上述配置添加到Claude Desktop配置文件中：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

#### 应用配置

1. 保存配置文件
2. 重启Claude Desktop
3. 在Claude Desktop中应该能看到flight-ticket-server连接成功

### 不同传输协议的配置

#### SSE模式（默认）
```json
{
  "mcpServers": {
    "flight-ticket-server": {
      "command": "python",
      "args": ["D:\\FlightTicketMCPServer\\flight_ticket_server.py"],
      "env": {
        "MCP_TRANSPORT": "sse",
        "MCP_HOST": "127.0.0.1",
        "MCP_PORT": "8000",
        "MCP_SSE_PATH": "/sse"
      }
    }
  }
}
```

#### stdio模式
```json
{
  "mcpServers": {
    "flight-ticket-server": {
      "command": "python",
      "args": ["D:\\FlightTicketMCPServer\\flight_ticket_server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

#### HTTP模式
```json
{
  "mcpServers": {
    "flight-ticket-server": {
      "command": "python",
      "args": ["D:\\FlightTicketMCPServer\\flight_ticket_server.py"],
      "env": {
        "MCP_TRANSPORT": "streamable-http",
        "MCP_HOST": "127.0.0.1",
        "MCP_PORT": "8000",
        "MCP_PATH": "/mcp"
      }
    }
  }
}
```

### MCP客户端测试

#### 测试连接

配置完成后，可以通过以下方式测试MCP服务器连接：

1. **Claude Desktop测试**：
   - 重启Claude Desktop
   - 检查状态栏是否显示"flight-ticket-server"连接成功
   - 在对话中尝试询问："你现在有哪些工具可用？"

2. **命令行测试**：
   ```bash
   # 使用uvx直接测试
   uvx flight-ticket-mcp-server --help
   
   # 或使用已安装的包测试
   flight-ticket-mcp-server --help
   
   # 测试模块化运行
   python -m flight_ticket_mcp_server --help
   ```

3. **MCP协议测试**：
   ```bash
   # 使用MCP inspector工具测试（如果安装了）
   npx @modelcontextprotocol/inspector uvx flight-ticket-mcp-server
   ```

#### 验证工具注册

成功连接后，您的Claude应该能够访问以下工具：

- ✈️ **searchFlightRoutes** - 航班路线查询
- 📅 **getCurrentDate** - 获取当前日期  
- 🔄 **getTransferFlightsByThreePlace** - 航班中转查询
- 🌤️ **getWeatherByLocation** - 经纬度天气查询
- 🏙️ **getWeatherByCity** - 城市天气查询
- ℹ️ **getFlightInfo** - 航班信息查询
- 📡 **getFlightStatus** - 航班实时状态查询
- 🛫 **getAirportFlights** - 机场周边航班查询
- 🗺️ **getFlightsInArea** - 区域航班查询
- 📊 **trackMultipleFlights** - 批量航班跟踪

#### 故障排除

如果连接失败，请检查：

1. **uvx配置**：
   ```bash
   # 检查uv/uvx是否安装
   uvx --version
   
   # 手动测试包运行
   uvx flight-ticket-mcp-server@latest
   ```

2. **包版本**：
   ```bash
   # 强制使用最新版本
   uvx flight-ticket-mcp-server@latest
   
   # 清除uvx缓存后重试
   uv cache clean
   uvx flight-ticket-mcp-server@latest
   ```

3. **配置文件语法**：
   - 确保JSON格式正确
   - 检查引号和括号匹配
   - 验证配置文件路径

4. **日志检查**：
   - 查看Claude Desktop的日志输出
   - 检查服务器启动日志

### 示例操作

配置完成后，您可以要求Claude执行以下操作：

#### 航班路线查询
- "查询重庆到广州明天的航班"
- "搜索上海到北京后天的所有航班"
- "查看深圳飞成都2024年7月20日的航班价格"
- "北京到三亚的航班有哪些选择"
- "帮我找一下成都到杭州下周二的航班信息"

#### 航班中转查询
- "查询北京经香港到纽约的中转航班"
- "搜索上海经迪拜到伦敦的联程航班，中转时间3-6小时"
- "查找广州经新加坡到悉尼的航班，最短中转2小时"
- "北京到洛杉矶，经东京中转的航班有哪些"

#### 天气信息查询
- "查询北京今天和明天的天气情况"
- "上海的天气怎么样"
- "查询纬度39.9042，经度116.4074的天气"（北京坐标）
- "武汉本周的天气预报"
- "查询重庆2024年7月15日到7月17日的天气"

#### 航班信息查询
- "查询航班CA1234的详细信息"
- "MU5678这个航班现在什么状态"
- "帮我查看航班HU7890的座位和价格信息"
- "CZ3691航班的登机口和航站楼信息"

#### 实时航班跟踪查询
- "查询航班CCA1234的实时状态和位置"
- "查看北京首都机场周边有哪些航班"
- "查询北京地区（纬度39-41，经度115-118）内的所有航班"
- "同时跟踪航班CCA1234、CSN5678、MU9876的实时状态"
- "查看浦东机场附近正在飞行的航班"
- "这架飞机现在在哪里？飞行高度和速度是多少？"

#### 日期时间查询
- "今天是几号"
- "现在的日期和时间是什么"
- "帮我获取当前日期"

#### 综合查询示例
- "我要从成都飞北京，明天出发，顺便告诉我北京的天气"
- "查询上海到广州的航班，还有广州的天气情况"
- "帮我规划从重庆到东京的行程，需要中转，并查看目的地天气"
- "查询CA1234航班信息，以及出发地和目的地的天气"
- "我的航班是MU5678，帮我查看航班状态和座位情况"
- "查询CCA1234航班的实时位置，同时告诉我目的地天气"
- "我想知道北京机场现在有哪些航班起飞，以及北京的天气状况"

## API参考

### 航班路线查询
```python
searchFlightRoutes(departure_city, destination_city, departure_date)  # 根据出发地、目的地和日期查询可用航班
```

输入参数：
- `departure_city`: 出发城市名称或机场代码 (如: "重庆", "CKG", "重庆(CKG)")
- `destination_city`: 目的地城市名称或机场代码 (如: "广州", "CAN", "广州(CAN)")
- `departure_date`: 出发日期 (YYYY-MM-DD格式)

输出信息：
- 航班列表（包含航班号、航空公司、起飞到达时间、机场、航站楼、价格）
- 价格统计（最低价、最高价、平均价）
- 航空公司分布统计
- 格式化的查询结果输出
- 支持的城市：282个国内城市和机场

支持的城市格式：
- 城市名：上海、北京、重庆、广州等
- 机场代码：SHA、BJS、CKG、CAN等
- 完整格式：上海(SHA)、北京(BJS)等

### 航班中转路线查询
```python
getTransferFlightsByThreePlace(from_place, transfer_place, to_place, min_transfer_time, max_transfer_time)
```

输入参数：
- `from_place`: 出发地城市名称或机场代码 (如: "北京", "BJS")
- `transfer_place`: 中转地城市名称或机场代码 (如: "香港", "HKG")  
- `to_place`: 目的地城市名称或机场代码 (如: "纽约", "NYC")
- `min_transfer_time`: 最小中转时间（小时），默认2.0小时
- `max_transfer_time`: 最大中转时间（小时），默认5.0小时

输出信息：
- 符合条件的中转航班组合列表
- 第一段航程详细信息（出发地到中转地）
- 第二段航程详细信息（中转地到目的地）
- 实际中转时间计算
- 航班号、时间、机场等详细信息

### 天气信息查询

#### 按经纬度查询
```python
getWeatherByLocation(latitude, longitude, start_date, end_date)
```

输入参数：
- `latitude`: 纬度 (如: 39.9042)
- `longitude`: 经度 (如: 116.4074)
- `start_date`: 开始日期 (YYYY-MM-DD格式)，可选
- `end_date`: 结束日期 (YYYY-MM-DD格式)，可选

#### 按城市名查询
```python
getWeatherByCity(city_name, start_date, end_date)
```

输入参数：
- `city_name`: 城市名称 (如: "北京", "上海", "武汉")
- `start_date`: 开始日期 (YYYY-MM-DD格式)，可选
- `end_date`: 结束日期 (YYYY-MM-DD格式)，可选

输出信息：
- 天气状况描述
- 温度信息（最高温、最低温、当前温度）
- 湿度、风速、风向
- 降水概率和降水量
- 日出日落时间
- 紫外线指数

### 航班信息查询
```python
getFlightInfo(flight_number)  # 根据航班号查询详细航班信息
```

输入参数：
- `flight_number`: 航班号 (如: "CA1234", "MU5678", "CZ3691")

输出信息：
- 航班基本信息（航空公司、机型、航线类型）
- 航线信息（出发和到达机场、航站楼、登机口）
- 实时状态（准时、延误、登机、飞行中、已到达等）
- 座位配置（经济舱、商务舱、头等舱座位数）
- 价格信息（各舱位价格和可用性）
- 天气信息（出发地和目的地当前天气）
- 附加服务（值机柜台、行李额度、餐食、WiFi等）

支持的航班号格式：
- 中国国际航空：CA1234、CA8901
- 中国东方航空：MU5678、MU2468
- 中国南方航空：CZ3691、CZ1357
- 海南航空：HU7890
- 厦门航空：MF8123
- 春秋航空：9C8765
- 吉祥航空：HO1288
- 国外航空：UA858、NH955 等

### 实时航班跟踪

#### 航班实时状态查询
```python
getFlightStatus(flight_number, date=None)  # 查询航班实时状态
```

输入参数：
- `flight_number`: 航班呼号 (如: "CCA1234", "CSN5678", "MU9876")
- `date`: 日期参数（OpenSky仅支持实时数据，此参数被忽略）

输出信息：
- 航班实时位置（经纬度、高度）
- 飞行速度（地面速度、垂直速度）
- 航班状态（飞行中、地面、滑行、静止）
- 航向角和高度信息
- 最后联系时间
- 起源国家信息

#### 机场周边航班查询
```python
getAirportFlights(airport_code, flight_type="departure")  # 查询机场周边航班
```

输入参数：
- `airport_code`: 机场代码 (如: "PEK", "PVG", "CAN", "CTU", "XIY")
- `flight_type`: 航班类型（此参数仅为兼容性，OpenSky返回所有航班）

输出信息：
- 机场周边30公里范围内的所有航班
- 每架航班的实时位置和状态
- 航班呼号、速度、高度信息
- 机场坐标和搜索范围

支持的机场代码（70+个）：
- 北京：PEK（首都）、PKX（大兴）
- 上海：PVG（浦东）、SHA（虹桥）
- 广州：CAN、深圳：SZX、成都：CTU/TFU
- 重庆：CKG、西安：XIY、昆明：KMG
- 杭州：HGH、南京：NKG、武汉：WUH
- 以及其他主要城市机场

#### 区域航班查询
```python
getFlightsInArea(min_lat, max_lat, min_lon, max_lon)  # 查询指定区域内航班
```

输入参数：
- `min_lat`: 最小纬度 (如: 39.0)
- `max_lat`: 最大纬度 (如: 41.0)
- `min_lon`: 最小经度 (如: 115.0)
- `max_lon`: 最大经度 (如: 118.0)

输出信息：
- 指定地理区域内的所有实时航班
- 航班位置、速度、高度等详细信息
- 边界框坐标和查询范围

#### 批量航班跟踪
```python
trackMultipleFlights(flight_numbers, date=None)  # 批量跟踪多个航班
```

输入参数：
- `flight_numbers`: 航班呼号列表 (如: ["CCA1234", "CSN5678", "MU9876"])
- `date`: 日期参数（OpenSky仅支持实时数据）

输出信息：
- 多个航班的实时状态汇总
- 每个航班的详细查询结果
- 成功查询数量统计
- 批量查询执行时间

注意事项：
- OpenSky Network仅提供实时数据，不支持历史航班查询
- API有频率限制，批量查询时会自动添加延时
- 部分航班可能无呼号信息或位置数据不完整
- 数据精度和可用性取决于ADS-B信号覆盖

### 日期时间工具
```python
getCurrentDate()  # 获取当前日期（YYYY-MM-DD格式）
```

输出信息：
- 当前系统日期字符串

## 开发

### 项目结构
```
FlightTicketMCPServer/
├── flight_ticket_server/
│   ├── core/              # 核心业务逻辑
│   ├── tools/             # MCP工具实现
│   ├── utils/             # 实用工具函数
│   └── main.py            # 服务器入口点
├── office_flight_ticket_server/  # 额外模块
├── tests/                 # 测试文件
├── logs/                  # 日志文件目录
├── pyproject.toml         # 项目配置
├── requirements.txt       # 项目依赖
├── flight_ticket_server.py # 主启动文件
├── mcp-config.json        # MCP配置示例
└── README.md              # 项目文档
```

### 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行基本功能测试
python -m pytest tests/test_basic.py -v

# 运行特定测试
python -m pytest tests/test_basic.py::TestFlightSearch::test_searchFlightsByNumber -v
```

### 日志和调试

- 日志文件位置：`logs/` 目录
- 启用调试模式：设置 `MCP_DEBUG=true`
- 查看实时日志：`tail -f logs/flight_server.log`

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 更改端口
   set MCP_PORT=8001
   python flight_ticket_server.py
   ```

2. **导入错误**
   ```bash
   # 确保在正确的目录
   cd FlightTicketMCPServer/flight_ticket_server
   python flight_ticket_server.py
   ```

3. **权限问题**
   ```bash
   # 检查文件权限
   ls -la flight_ticket_server.py
   chmod +x flight_ticket_server.py
   ```

### 日志分析

查看日志文件了解详细错误信息：
```bash
# 查看一般日志
cat logs/flight_server.log

# 查看错误日志
cat logs/flight_server_error.log

# 实时监控日志
tail -f logs/flight_server.log
```

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件获取详细信息。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 支持

如果您遇到问题或有功能建议，请在GitHub上创建Issue。
