# Go-home - 回家最优路线查询系统

一款整合机票和火车票查询的智能出行规划软件，帮助你找到回家的最优交通组合方案。

## 功能特性

- **智能中转推荐**：自动通过全国 44 个主要交通枢纽计算最优中转组合
- **跨模式组合**：支持 飞机→飞机、飞机→高铁、高铁→飞机、高铁→高铁 等多种组合
- **多策略优化**：省钱优先、省时优先、均衡推荐
- **住宿费用计算**：自动识别需要过夜的中转方案，计算真实成本
- **现代化 UI**：基于 CustomTkinter 的深色/浅色主题界面

## 数据来源说明

### 机票数据 - 携程 (Ctrip)

> **重要提示**

机票数据来源于携程网站，存在以下限制：

1. **验证码处理**：首次查询可能触发验证码，程序会弹出浏览器窗口，需要手动完成验证
2. **Cookie 复用**：验证完成后 Cookie 会保存在 `browser_data/` 目录，后续查询无需重复验证
3. **价格差异**：携程存在"杀熟"现象，不同账号看到的价格可能不同
4. **活动限制**：携程的优惠活动、会员折扣等无法体现在查询结果中
5. **平台限制**：仅能获取携程平台的机票数据，其他平台（飞猪、去哪儿等）的价格和活动无法查询
6. **反爬限制**：携程反爬较严格，机票查询采用串行方式执行，速度较慢

**建议**：查询结果仅供参考，实际购票时请多平台比价。

### 火车票数据 - 12306 官方

火车票数据直接来自 12306 官方 API：

- **数据准确**：价格、余票信息与官方一致
- **查询限制**：12306 仅支持查询 15 天内的车票
- **无需登录**：火车票查询不需要登录验证

## 快速开始

### 1. 环境准备

推荐使用 Conda 创建独立环境：

```bash
# 创建环境
conda create -n Go-home python=3.13

# 激活环境
conda activate Go-home

# 安装 Node.js (用于火车票服务)
conda install -c conda-forge nodejs
```

### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-username/Go-home.git
cd Go-home

# 安装 Python 依赖
pip install -r requirements.txt

# 安装机票 MCP 服务
pip install -e ./FlightTicketMCP

# 安装火车票 MCP 服务
cd 12306-mcp
npm install
npm run build
cd ..
```

### 3. 配置 API

复制配置文件并填入你的 API 信息：

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "api_base_url": "https://api.openai.com/v1",
  "api_key": "your-api-key-here",
  "model": "gpt-4",
  "theme": "dark",
  "window_size": "1200x800"
}
```

支持任何 OpenAI 兼容的 API 服务（如 Azure OpenAI、Claude API 代理等）。

### 4. 运行程序

```bash
python main.py
```

启动后：
1. 点击 **「一键启动服务」** 启动 MCP 服务
2. 填写出发地、目的地、日期
3. 选择偏好设置
4. 点击 **「开始查询」**

## 项目架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Go-home 主程序                          │
│              main.py (CustomTkinter UI + AI API)            │
│                                                             │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │  分段查询引擎    │  │         中转枢纽管理器            │  │
│  │ segment_query.py│  │       transfer_hubs.py           │  │
│  └────────┬────────┘  └──────────────────────────────────┘  │
└───────────┼─────────────────────────────────────────────────┘
            │
            │ MCP Protocol (stdio)
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌─────────────┐ ┌─────────────────┐
│ FlightMCP   │ │   12306-mcp     │
│  (Python)   │ │  (TypeScript)   │
│             │ │                 │
│ 航班路线查询 │ │ 火车票余票查询   │
│ 中转航班查询 │ │ 中转票查询      │
└──────┬──────┘ └────────┬────────┘
       │                 │
       ▼                 ▼
   携程网站           12306 官方
```

## 中转枢纽策略

系统内置全国 44 个主要交通枢纽，支持智能中转推荐：

### 枢纽等级

| 等级 | 城市 |
|------|------|
| 一级 | 北京、上海、广州 |
| 二级 | 深圳、成都、重庆、西安、武汉、郑州 |
| 三级 | 南京、杭州、长沙、昆明、沈阳、哈尔滨 |
| 四级 | 其他省会及重要城市 |

### 空铁联运枢纽

支持飞机转高铁零换乘或快速换乘的城市：
- **一体化换乘**（60-90分钟）：上海虹桥、北京大兴、郑州新郑、成都双流/天府、海口美兰
- **轨道交通连接**（120分钟）：长沙黄花、深圳宝安

## 项目结构

```
Go-home/
├── main.py                      # 主程序入口
├── segment_query.py             # 分段查询引擎
├── transfer_hubs.py             # 中转枢纽配置
├── config.json                  # 用户配置 (不要提交到 Git)
├── config.example.json          # 配置示例
├── requirements.txt             # Python 依赖
│
├── FlightTicketMCP/             # 机票查询 MCP 服务
│   ├── flight_ticket_mcp_server/
│   │   ├── tools/               # 查询工具实现
│   │   └── utils/               # 城市字典等
│   └── browser_data/            # 浏览器 Cookie 缓存
│
├── 12306-mcp/                   # 火车票查询 MCP 服务
│   ├── src/                     # TypeScript 源码
│   └── build/                   # 编译输出
│
└── 中转枢纽.md                   # 枢纽配置文档
```

## MCP 工具列表

### 机票服务 (FlightTicketMCP)

| 工具名 | 功能 |
|--------|------|
| `searchFlightRoutes` | 航班路线查询 |
| `getTransferFlightsByThreePlace` | 中转航班查询 |
| `getFlightInfo` | 航班详情查询 |
| `getWeatherByCity` | 城市天气查询 |

### 火车票服务 (12306-mcp)

| 工具名 | 功能 |
|--------|------|
| `get-tickets` | 火车票余票查询 |
| `get-interline-tickets` | 中转票查询 |
| `get-train-route-stations` | 车次经停站查询 |
| `get-station-code-of-citys` | 城市站点代码查询 |

## 国际航线支持

机票服务支持查询国际航班，覆盖全球主要城市：

| 地区 | 主要城市 |
|------|----------|
| 东南亚 | 曼谷、新加坡、吉隆坡、雅加达、马尼拉、普吉岛、巴厘岛 |
| 东亚 | 东京、大阪、首尔、釜山 |
| 欧洲 | 伦敦、巴黎、法兰克福、阿姆斯特丹、莫斯科 |
| 北美 | 纽约、洛杉矶、旧金山、温哥华、多伦多 |
| 大洋洲 | 悉尼、墨尔本、奥克兰 |

**注意**：火车票仅支持中国国内线路。

## 常见问题

### Q: 机票查询弹出浏览器窗口怎么办？

A: 这是验证码检测机制。请在弹出的浏览器中完成验证（滑块/点选），完成后程序会自动继续。验证通过后 Cookie 会保存，后续查询不需要再验证。

### Q: 为什么机票价格和我看到的不一样？

A: 携程对不同用户展示不同价格（俗称"杀熟"）。程序获取的是未登录状态的价格，可能与你登录后看到的价格不同。此外，会员折扣、平台活动等也不会体现在查询结果中。

### Q: 火车票查询显示"日期调整"是什么意思？

A: 12306 只能查询 15 天内的车票。如果你查询的日期超出范围，系统会自动调整到最远可查日期，并在结果中提示。

### Q: 查询很慢怎么办？

A:
- 机票查询采用串行方式（避免触发反爬），每个查询约需 10-30 秒
- 火车票查询采用并行方式，速度较快
- 选择更少的中转枢纽数量（8个）可以加快查询速度

## 技术栈

- **前端**：CustomTkinter (现代化 Tkinter)
- **AI**：OpenAI API (支持任何兼容接口)
- **机票服务**：Python + FastMCP + DrissionPage (浏览器自动化)
- **火车票服务**：TypeScript + MCP SDK
- **协议**：Model Context Protocol (MCP)

## 致谢

- [12306-mcp](https://github.com/xingkong2053/12306-mcp) - 火车票查询 MCP 服务
- [DrissionPage](https://github.com/g1879/DrissionPage) - 浏览器自动化工具
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - 现代化 UI 框架

## License

MIT
