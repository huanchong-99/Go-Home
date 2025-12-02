# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MANDATORY: Conda Environment Requirement

**ALL operations in this project MUST be executed within the Conda environment `Go-home`.**

```bash
# Environment details
Name: Go-home
Path: G:\conda environment\Go-home
Python: 3.13.9

# Activate before ANY operation
conda activate Go-home
```

**This is non-negotiable.** Whether running Python, Node.js (npm/npx), or any other tool:
- If the project needs `npx`, Node.js must be installed in this Conda environment
- If the project needs any dependency, install it within this Conda environment
- Never use system-level interpreters or global installations

Example workflow:
```bash
conda activate Go-home
# Then run any command: python, npm, npx, pip, etc.
```

## Repository Overview

This is a monorepo containing two MCP (Model Context Protocol) servers for Chinese travel ticket search:

- **FlightTicketMCP** (Python) - Flight ticket search server using FastMCP
- **12306-mcp** (TypeScript) - China Railway 12306 train ticket search server

Both servers provide standardized API interfaces for AI assistants to query travel information.

## Build and Run Commands

**Important**: All commands use absolute paths to Conda environment executables.

### FlightTicketMCP (Python)

```bash
# Install dependencies
"G:/conda environment/Go-home/python.exe" -m pip install -r "f:/Go-home/Go-home/FlightTicketMCP/requirements.txt"

# Install as editable package (recommended)
"G:/conda environment/Go-home/python.exe" -m pip install -e "f:/Go-home/Go-home/FlightTicketMCP"

# Run server (stdio mode - default)
"G:/conda environment/Go-home/python.exe" -m flight_ticket_mcp_server

# Run tests
"G:/conda environment/Go-home/python.exe" -m pytest "f:/Go-home/Go-home/FlightTicketMCP/tests/" -v
```

### 12306-mcp (TypeScript)

```bash
# Install dependencies (skip prepare script to avoid PATH issues)
powershell -Command "Set-Location 'f:\Go-home\Go-home\12306-mcp'; & 'G:\conda environment\Go-home\node.exe' 'G:\conda environment\Go-home\node_modules\npm\bin\npm-cli.js' install --ignore-scripts"

# Build TypeScript
"G:/conda environment/Go-home/node.exe" "f:/Go-home/Go-home/12306-mcp/node_modules/typescript/bin/tsc" -p "f:/Go-home/Go-home/12306-mcp"

# Run server (stdio mode)
"G:/conda environment/Go-home/node.exe" "f:/Go-home/Go-home/12306-mcp/build/index.js"

# Run server (HTTP mode on port 8080)
"G:/conda environment/Go-home/node.exe" "f:/Go-home/Go-home/12306-mcp/build/index.js" --port 8080
```

## Architecture

### FlightTicketMCP Structure

```
FlightTicketMCP/
├── flight_ticket_mcp_server/
│   ├── main.py              # Server entry point, tool registration
│   ├── core/                # Data models (flights.py)
│   ├── tools/               # MCP tool implementations
│   │   ├── flight_search_tools.py    # Route search
│   │   ├── flight_transfer_tools.py  # Transfer flights
│   │   ├── flight_info_tools.py      # Flight details by number
│   │   ├── weather_tools.py          # Weather queries
│   │   ├── simple_opensky_tools.py   # Real-time tracking (OpenSky API)
│   │   └── date_tools.py             # Date utilities
│   └── utils/               # Utilities
│       ├── cities_dict.py   # 282 city/airport code mappings
│       ├── validators.py    # Input validation
│       └── api_client.py    # HTTP client
└── flight_ticket_server.py  # Main startup script
```

Key technologies: FastMCP, Pydantic, FastAPI, Selenium, geopy

### 12306-mcp Structure

```
12306-mcp/
├── src/
│   ├── index.ts    # Main server, all tools and data parsing logic
│   └── types.ts    # TypeScript type definitions
├── build/          # Compiled output
└── package.json
```

Key technologies: @modelcontextprotocol/sdk, axios, zod, date-fns

## MCP Tools Reference

### FlightTicketMCP Tools
- `searchFlightRoutes` - Search flights by route and date
- `getTransferFlightsByThreePlace` - Transfer flight queries
- `getFlightInfo` - Flight details by flight number
- `getWeatherByLocation` / `getWeatherByCity` - Weather queries
- `getFlightStatus` - Real-time flight tracking (OpenSky)
- `getAirportFlights` - Flights near an airport
- `getFlightsInArea` - Flights in geographic area
- `trackMultipleFlights` - Batch flight tracking
- `getCurrentDate` - Current date utility

### 12306-mcp Tools
- `get-tickets` - Query train tickets with filtering/sorting
- `get-interline-tickets` - Transfer train ticket queries
- `get-train-route-stations` - Train route stop information
- `get-station-code-of-citys` - City to station code lookup
- `get-station-code-by-names` - Station name to code lookup
- `get-stations-code-in-city` - All stations in a city
- `get-current-date` - Current date in Asia/Shanghai timezone

## Configuration

### FlightTicketMCP Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TRANSPORT` | Protocol: stdio, sse, streamable-http | sse |
| `MCP_HOST` | Server host | 127.0.0.1 |
| `MCP_PORT` | Server port | 8000 |
| `MCP_DEBUG` | Enable debug logging | false |
| `LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR | INFO |

### 12306-mcp Options
- `--port <port>` - Enable HTTP/SSE mode on specified port
- `--host <host>` - Bind to specific host (use 0.0.0.0 for all interfaces)

## Coding Conventions

### 12306-mcp (TypeScript)
- Variables use camelCase, constants use UPPER_SNAKE_CASE
- `*Data` suffix for raw API response data, `*Info` suffix for parsed/filtered data for model consumption
- Train filters: G(High-speed), D(EMU), Z(Direct), T(Express), K(Fast), O(Other), F(Fuxing), S(Smart EMU)
- Date format: "yyyy-MM-dd", timezone: Asia/Shanghai

### FlightTicketMCP (Python)
- Uses FastMCP decorator pattern for tool registration
- Supports multiple transport protocols (stdio, SSE, HTTP)
- Logs stored in `logs/` directory with rotation
