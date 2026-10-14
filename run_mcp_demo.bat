@echo off
REM MCP bonus demo: tools server in one window, agent app in another.
start "MCP server" cmd /k .venv\Scripts\python.exe mcp_server.py
timeout /t 6 /nobreak >nul
start "Agent app (tools fetched at runtime)" cmd /k .venv\Scripts\python.exe app.py --mcp
