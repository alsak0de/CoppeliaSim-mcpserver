# Running the CoppeliaSim MCP Server in a Container

This guide explains how to build and run the MCP server using Docker. This is the recommended way to ensure a clean, isolated environment for deployment or testing.

---

## 1. Clone the Repository

```bash
git clone https://github.com/alsak0de/CoppeliaSlim-mcpserver.git
cd CoppeliaSlim-mcpserver
```

---

## 2. Build the Docker Image

```bash
docker build -t coppelia-mcp .
```

---

## 3. Run the MCP Server Container

**Important:**
- You **must** specify the CoppeliaSim host using the `--coppeliaHost` argument so the MCP server can connect to the CoppeliaSim instance running outside the container.
- The server always binds to `0.0.0.0` inside the container.
- The port can be set using the `MCP_PORT` environment variable (default: 8000). You **must** expose the server port to access the API from outside the container.
- The `--rm` flag is used so the container is automatically removed when stopped (no persistence is required).

### Example (replace `<coppelia_host>` with your CoppeliaSim host IP):

```bash
docker run --rm -p 8000:8000 coppelia-mcp \
  --coppeliaHost <coppelia_host>
```

- To use a different port, set the `MCP_PORT` environment variable and map the port:

```bash
docker run --rm -e MCP_PORT=9000 -p 9000:9000 coppelia-mcp \
  --coppeliaHost <coppelia_host>
```

- If CoppeliaSim is running on the same machine (but not in Docker), use `--coppeliaHost host.docker.internal` (on Mac/Windows) or your host's IP address (on Linux).
- If CoppeliaSim is running in another container, ensure both containers are on the same Docker network and use the appropriate service/container name or IP.

---

## 4. Accessing the Server

- The MCP server will be available at `http://localhost:8000` (or the port you mapped).
- Use the `/sse` endpoint for SSE clients, or POST to `/` for JSON-RPC.

---

## Troubleshooting

- **Cannot connect to CoppeliaSim:**
  - Make sure the `--coppeliaHost` value is correct and reachable from inside the container.
  - Check firewall and network settings.
- **Port already in use:**
  - Change the host port in the `-p` flag (e.g., `-p 8080:8000`).
- **Persistent data:**
  - This setup does not persist any data. If you need to persist logs or configs, mount a volume.

---

For advanced usage (e.g., FastMCP server, custom ports, or volumes), adjust the Docker command and arguments as needed. 