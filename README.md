# Go-home - 回家最优路线查询系统

一款整合机票和火车票查询的智能出行规划软件，帮助你找到回家的最优交通组合方案。

## 项目愿景

本项目旨在开发一款软件，通过接入两个 MCP (Model Context Protocol) 服务，实现：
- 查询回家的机票价格和时刻
- 查询回家的火车票价格和时刻
- 智能组合机票+火车票的换乘方案
- 计算并推荐最优价格/时间的出行方案

## 当前进度

### 已完成

#### 1. Conda 环境配置
- 环境名称：`Go-home`
- 环境路径：`G:\conda environment\Go-home`
- Python 版本：3.13.9
- Node.js 版本：24.9.0 (通过 conda-forge 安装)
- npm 版本：11.6.0

#### 2. FlightTicketMCP (机票查询服务) - 已配置完成
- 语言：Python
- 框架：FastMCP
- 功能：航班路线查询、中转航班查询、航班实时跟踪、天气查询
- 状态：✅ 依赖已安装，服务可正常运行

安装命令：
```bash
"G:/conda environment/Go-home/python.exe" -m pip install -r "f:/Go-home/Go-home/FlightTicketMCP/requirements.txt"
"G:/conda environment/Go-home/python.exe" -m pip install -e "f:/Go-home/Go-home/FlightTicketMCP"
```

运行命令：
```bash
"G:/conda environment/Go-home/python.exe" -m flight_ticket_mcp_server
```

#### 3. 12306-mcp (火车票查询服务) - 已配置完成
- 语言：TypeScript
- 框架：@modelcontextprotocol/sdk
- 功能：12306 余票查询、中转票查询、车次经停站查询
- 状态：✅ 依赖已安装，TypeScript 已编译，服务可正常运行

安装命令：
```bash
powershell -Command "Set-Location 'f:\Go-home\Go-home\12306-mcp'; & 'G:\conda environment\Go-home\node.exe' 'G:\conda environment\Go-home\node_modules\npm\bin\npm-cli.js' install --ignore-scripts"
```

编译命令：
```bash
"G:/conda environment/Go-home/node.exe" "f:/Go-home/Go-home/12306-mcp/node_modules/typescript/bin/tsc" -p "f:/Go-home/Go-home/12306-mcp"
```

运行命令：
```bash
"G:/conda environment/Go-home/node.exe" "f:/Go-home/Go-home/12306-mcp/build/index.js"
```

#### 4. 主程序 (main.py) - 已完成
- 框架：CustomTkinter (现代化 UI)
- 功能：
  - ✅ 现代化深色/浅色主题 UI
  - ✅ 一键启动/停止两个 MCP 服务
  - ✅ OpenAI 标准格式 API 配置
  - ✅ 自动获取可用模型列表（下拉选择）
  - ✅ API 连接测试
  - ✅ 运行日志实时显示
  - ✅ 配置持久化存储
  - ✅ **MCP 工具调用集成**（AI 可直接调用 MCP 工具查询票务）
  - ✅ **AI Function Calling** 支持多轮工具调用

运行命令：
```bash
"G:/conda environment/Go-home/python.exe" "f:/Go-home/Go-home/main.py"
```

### 待开发

- [ ] 路线组合算法：计算机票+火车票的最优组合
- [ ] 价格比较模块：多方案价格对比
- [ ] 时间优化模块：换乘时间合理性检查
- [ ] 打包分发：制作独立安装包

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Go-home 主程序                        │
│         main.py (CustomTkinter UI + OpenAI API)         │
└─────────────────┬───────────────────┬───────────────────┘
                  │                   │
                  │ MCP Protocol      │ MCP Protocol
                  │ (stdio)           │ (stdio)
                  ▼                   ▼
┌─────────────────────────┐ ┌─────────────────────────────┐
│   FlightTicketMCP       │ │       12306-mcp             │
│   (Python/FastMCP)      │ │    (TypeScript/MCP SDK)     │
│                         │ │                             │
│ - 航班路线查询          │ │ - 火车票余票查询            │
│ - 中转航班查询          │ │ - 中转票查询                │
│ - 航班实时跟踪          │ │ - 车次经停站查询            │
│ - 天气查询              │ │ - 车站代码查询              │
└─────────────────────────┘ └─────────────────────────────┘
          │                           │
          ▼                           ▼
    航班数据API                   12306 官方API
    (OpenSky等)
```

## 项目结构

```
Go-home/
├── Go-home/
│   ├── main.py                   # 主程序入口 (CustomTkinter UI)
│   ├── config.json               # 配置文件 (API Key等)
│   │
│   ├── FlightTicketMCP/          # 机票查询 MCP 服务
│   │   ├── flight_ticket_mcp_server/
│   │   │   ├── main.py           # 服务入口
│   │   │   ├── tools/            # MCP 工具实现
│   │   │   └── utils/            # 工具函数
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── 12306-mcp/                # 火车票查询 MCP 服务
│   │   ├── src/
│   │   │   ├── index.ts          # 服务入口
│   │   │   └── types.ts          # 类型定义
│   │   ├── build/                # 编译输出
│   │   └── package.json
│   │
│   ├── CLAUDE.md                 # Claude Code 开发指南
│   └── README.md                 # 本文件
```

## 环境要求

**强制要求**：所有操作必须在 Conda 环境 `Go-home` 中执行。

```bash
# 环境信息
Name: Go-home
Path: G:\conda environment\Go-home
Python: 3.13.9
Node.js: 24.9.0
```

## 快速开始

### 方式一：使用主程序 (推荐)
```bash
"G:/conda environment/Go-home/python.exe" "f:/Go-home/Go-home/main.py"
```
启动后在 UI 界面点击 **[一键启动服务]** 即可同时启动两个 MCP 服务。

### 方式二：手动启动服务

#### 启动机票查询服务
```bash
"G:/conda environment/Go-home/python.exe" -m flight_ticket_mcp_server
```

#### 启动火车票查询服务
```bash
"G:/conda environment/Go-home/node.exe" "f:/Go-home/Go-home/12306-mcp/build/index.js"
```

两个服务都默认使用 **stdio 模式**运行，适合作为 MCP Server 被主程序调用。

## MCP 工具列表

### FlightTicketMCP 提供的工具
| 工具名 | 功能 |
|--------|------|
| `searchFlightRoutes` | 航班路线查询 |
| `getTransferFlightsByThreePlace` | 中转航班查询 |
| `getFlightInfo` | 航班详情查询 |
| `getWeatherByLocation` | 按经纬度查询天气 |
| `getWeatherByCity` | 按城市查询天气 |
| `getFlightStatus` | 航班实时状态 |
| `getAirportFlights` | 机场周边航班 |
| `getFlightsInArea` | 区域航班查询 |
| `trackMultipleFlights` | 批量航班跟踪 |
| `getCurrentDate` | 获取当前日期 |

### 12306-mcp 提供的工具
| 工具名 | 功能 |
|--------|------|
| `get-tickets` | 火车票余票查询 |
| `get-interline-tickets` | 中转票查询 |
| `get-train-route-stations` | 车次经停站查询 |
| `get-station-code-of-citys` | 城市站点代码查询 |
| `get-station-code-by-names` | 站名代码查询 |
| `get-stations-code-in-city` | 城市内所有站点查询 |
| `get-current-date` | 获取当前日期 |

## 开发文档

详细的开发指南请参阅 [CLAUDE.md](./CLAUDE.md)，包含：
- Conda 环境强制要求
- 完整的构建和运行命令
- 代码架构说明
- 编码规范

## License

MIT
