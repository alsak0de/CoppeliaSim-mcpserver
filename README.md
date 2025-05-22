# CoppeliaSim MCP Server

A Python-based MCP (Motion Control Protocol) server implementation for CoppeliaSim robotics simulation, supporting both FastAPI and FastMCP backends.

## Features
- JSON-RPC 2.0 protocol
- Joint control and robot/scene description tools
- Supports both HTTP/SSE and stdio transports
- Flexible, LLM-friendly output

## Requirements
- Python 3.x
- CoppeliaSim (formerly V-REP) **version 4.3 or newer** (ZeroMQ remote API required)
- Required Python packages (see requirements.txt)

## Installation

### 0. (Recommended) Create a Conda Environment

It is highly recommended to use a conda environment to avoid dependency conflicts:

```bash
conda create -n coppelia-mcp python=3.10
conda activate coppelia-mcp
```

You can then proceed with the steps below.

### 1. Clone the repository and install requirements

```bash
git clone https://github.com/alsak0de/CoppeliaSlim-mcpserver.git
cd CoppeliaSlim-mcpserver
pip install -r requirements.txt
```

## Usage

### 1. Start CoppeliaSim and load your robot model

### 2. Run the MCP server

#### Option A: FastAPI-based server (`coppelia_mcp.py`)
- **Option 1: Development or custom CoppeliaSim host:**
  ```bash
  python coppelia_mcp.py --host 0.0.0.0 --port 8000 --coppeliaHost <coppelia_host>
  ```
  - This allows you to specify the CoppeliaSim host (default: 127.0.0.1) using `--coppeliaHost`.
  - The server will launch using the built-in uvicorn runner.
- **Option 2: Production (recommended):**
  ```bash
  uvicorn coppelia_mcp:app --host 0.0.0.0 --port 8000
  ```
  - This is the standard way to run FastAPI apps in production.
  - **Note:** In this mode, you cannot set `--coppeliaHost` via the command line. To specify the CoppeliaSim host, set the `COPPELIASIM_HOST` environment variable:
    ```bash
    COPPELIASIM_HOST=192.168.1.100 uvicorn coppelia_mcp:app --host 0.0.0.0 --port 8000
    ```
  - **Precedence:**
    1. `--coppeliaHost` (if running with `python coppelia_mcp.py ...`)
    2. `COPPELIASIM_HOST` environment variable (if set)
    3. Default: `127.0.0.1`
- **Transports:**
  - HTTP POST (JSON-RPC)
  - SSE at `/sse` endpoint
  - Stdio (via npx mcp-remote bridge, see below)

#### Option B: FastMCP-based server (`coppelia_fastmcp.py`)
- **Default:**
  ```bash
  python coppelia_fastmcp.py --host 0.0.0.0 --port 8000 --coppeliaHost <coppelia_host>
  ```
  - You can specify the CoppeliaSim host with `--coppeliaHost` (default: 127.0.0.1).
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