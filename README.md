# CoppeliaSim MCP Server

A Python-based MCP (Motion Control Protocol) server implementation for CoppeliaSim robotics simulation, supporting both FastAPI and FastMCP backends.

## Features
- JSON-RPC 2.0 protocol
- Joint control and robot/scene description tools
- Supports both HTTP/SSE and stdio transports
- Flexible, LLM-friendly output

## Requirements
- Python 3.x
- CoppeliaSim (formerly V-REP)
- Required Python packages (see requirements.txt)

## Installation
```bash
git clone https://github.com/alsak0de/CoppeliaSlim-mcpserver.git
cd CoppeliaSlim-mcpserver
pip install -r requirements.txt
```

## Usage

### 1. Start CoppeliaSim and load your robot model

### 2. Run the MCP server

#### Option A: FastAPI-based server (`coppelia_mcp.py`)
- **Default:**
  ```bash
  uvicorn coppelia_mcp:app --host 0.0.0.0 --port 8000
  ```
- **Custom host/port:**
  ```bash
  uvicorn coppelia_mcp:app --host <your_host> --port <your_port>
  ```
- **Transports:**
  - HTTP POST (JSON-RPC)
  - SSE at `/sse` endpoint
  - Stdio (via npx mcp-remote bridge, see below)

#### Option B: FastMCP-based server (`coppelia_fastmcp.py`)
- **Default:**
  ```bash
  python coppelia_fastmcp.py --host 0.0.0.0 --port 8000
  ```
- **Custom host/port:**
  ```bash
  python coppelia_fastmcp.py --host <your_host> --port <your_port>
  ```
- **Transports:**
  - HTTP POST (JSON-RPC)
  - SSE at `/sse` endpoint
  - Stdio (native, or via npx mcp-remote if needed)

### 3. Connecting Clients
- **SSE/HTTP:**
  - Use the `/sse` endpoint for SSE clients (recommended for modern LLM/agent clients)
  - Example: `http://localhost:8000/sse`
- **Stdio:**
  - Use a bridge if your client only supports stdio:
    ```bash
    npx mcp-remote http://localhost:8000
    ```
  - Or configure your client to use stdio transport if supported natively by FastMCP

### 4. Auto-Approve Tool Calls
- In most clients (e.g., Cursor), enable "Auto Approve" in the server settings to avoid confirmation prompts for each tool call.

## API Tools
- `rotate_joint`: Rotates a joint to a given angle
- `list_joints`: Lists all joints with their types and limits
- `describe_robot`: Returns a detailed, LLM-friendly description of all robot elements
- `describe_scene`: Returns a description of all scene objects (excluding robot joints)

## Notes
- Both servers default to `0.0.0.0:8000` but you can override with `--host` and `--port`.
- Use the SSE endpoint for best compatibility with modern LLM/agent clients.
- For stdio-only clients, use the npx bridge or FastMCP's native stdio support.
- **Why/When uvicorn?**
  - For the FastAPI-based server (`coppelia_mcp.py`), you need `uvicorn` (or another ASGI server) to actually serve HTTP/SSE endpoints, because FastAPI is just a framework and does not include a web server.
  - For the FastMCP-based server (`coppelia_fastmcp.py`), you only need `uvicorn` if you want to serve HTTP/SSE endpoints. If you run FastMCP in stdio mode (for agent/CLI integration), you do **not** need `uvicorn` or any web server, since all communication is over stdin/stdout.

## License
MIT License 