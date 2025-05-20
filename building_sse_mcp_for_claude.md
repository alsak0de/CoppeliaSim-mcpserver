# How to Build a Working SSE MCP Server for Claude (Using FastAPI)

This guide walks you through creating a working [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that Claude Desktop can connect to using SSE transport and JSON-RPC 2.0. The server is backed by a simple API (CoppeliaSim in this case).

---

## ✅ Prerequisites

- Python 3.8+
- FastAPI
- Uvicorn
- sse-starlette
- Claude Desktop with `mcp-remote` installed globally:
  ```bash
  npm install -g mcp-remote
  ```

---

## 🧱 Project Structure

```
mcp/
├── mcp_server.py   # Your FastAPI-based SSE MCP server
└── claude_desktop_config.json  # MCP server launcher config
```

---

## 🚀 Step-by-Step Instructions

### 1. Create the `mcp_server.py`

This Python server will:

- Open an SSE connection at `/sse` (for Claude to keep alive)
- Handle JSON-RPC 2.0 requests at both `/` and `/sse` (Claude uses both)
- Respond with valid MCP tool metadata and perform tool actions

See `mcp_server.py` in the project for full code.

---

### 2. Key Requirements for Compatibility

#### ✅ Correct JSON-RPC Responses

Claude expects all responses to conform to JSON-RPC 2.0:
```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": { ... }
}
```

No extra keys like `"status"` or missing `"id"` or `"jsonrpc"` fields.

#### ✅ Use `inputSchema` for tool definitions

Claude will not recognize tools if you return:
```json
"parameters": { ... }  ❌
```

It must be:
```json
"inputSchema": {
  "type": "object",
  "properties": {
    "joint_name": { "type": "string" },
    "angle_deg": { "type": "number" }
  },
  "required": ["joint_name", "angle_deg"]
}
```

---

### 3. Claude Desktop Configuration

In `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "CoppeliaSim MCP": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:8000"]
    }
  }
}
```

This makes Claude connect to your local HTTP FastAPI server via SSE and proxy requests through `mcp-remote`.

---

### 4. Start the MCP Server

```bash
uvicorn mcp_server:app --reload --port 8000
```

You should see logs like:

```
🚀 Starting MCP server...
✅ Connected to CoppeliaSim
📥 Received POST / request
📦 Request JSON: {'method': 'initialize', ...}
📤 Responding with: {...}
```

---

### 5. Start Claude Desktop

- Claude should now say “MCP connected”.
- Your tool (`rotate_joint`) should appear in the Claude UI.
- You can test it by saying:
  > Rotate joint m1 to 45 degrees

---

## 🧪 Debugging Tips

- Always `print()` your incoming JSON-RPC to see what Claude sends.
- Make sure you return `{"jsonrpc": "2.0", "id": ..., "result": ...}` always.
- Avoid returning just `{ "status": "ok" }` — this breaks Zod validation.

---

## ✅ You’re Done!

You now have:
- A FastAPI server compliant with JSON-RPC 2.0
- SSE endpoint Claude understands
- A tool (`rotate_joint`) discoverable and callable from Claude UI

---

## 🛠 Ready to Expand?

Add more tools like:

- `get_joint_position`
- `rotate_all`
- `move_to_target`
- or any other API backend method!

