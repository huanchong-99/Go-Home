# Repository Guidelines

## Project Structure & Module Organization
This repository combines a desktop route planner with two MCP services. `main.py` is the desktop entry point; `segment_query.py`, `route_calculator.py`, and `transfer_hubs.py` hold the core routing and transfer logic. `FlightTicketMCP/flight_ticket_mcp_server/` contains the Python flight MCP server, organized into `core/`, `tools/`, and `utils/`. `12306-mcp/src/` contains the TypeScript train MCP server, with compiled output in `12306-mcp/build/`. Treat `dist/`, `build/`, `logs/`, and `browser_data/` as generated or runtime data, not source.

## Build, Test, and Development Commands
- `python main.py` — launch the desktop app from the repo root.
- `cd FlightTicketMCP && pip install -e .[dev]` — install the Python MCP server with dev tools.
- `cd FlightTicketMCP && python -m pytest tests/ -v` — run Python tests for the flight server.
- `cd 12306-mcp && npm install && npm run build` — install dependencies and compile the train MCP server.
- `cd 12306-mcp && npm test` — run the TypeScript compile + stdio smoke test.
- `pyinstaller Go-home.spec` — build the Windows portable package.

## Coding Style & Naming Conventions
Use 4-space indentation in Python and keep new public functions typed. Follow `snake_case` for functions/modules, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants such as runtime paths. For `FlightTicketMCP`, match the formatting settings in `FlightTicketMCP/pyproject.toml`: Black-compatible imports via `isort`, max line length `100`, and `mypy`-friendly signatures. In `12306-mcp`, keep ES module syntax, `camelCase` identifiers, and shared schemas in `src/types.ts`.

## Testing Guidelines
There is no repo-wide coverage gate yet, so add focused regression tests around the code you change. Put Python tests under `FlightTicketMCP/tests/test_*.py`. For `12306-mcp`, keep `npm test` passing; add extra tests only when new reusable logic appears. For root desktop changes, do a manual smoke run with `python main.py` and note the route-search scenario you verified.

## Commit & Pull Request Guidelines
Recent history uses short, imperative commit subjects in Chinese, for example `新增超时机制`, `修复导出的bug`, or `【新增】火车票查询失败自动重试机制`. Keep each commit single-purpose. PRs should include: affected module(s), validation commands you ran, config/schema changes, linked issues, and screenshots for UI changes. If you changed MCP behavior, include a sample request/response or a short reproduction note.

## Security & Configuration Tips
Never commit secrets or local state from `config.json`, `.env`, `browser_data/`, or `logs/`. Start from `config.example.json` for local setup, and scrub machine-specific paths or API keys before opening a PR.
