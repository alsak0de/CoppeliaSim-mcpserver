#!/bin/sh

# Default port
PORT=8000

# Check if first argument is a number (port)
if [ "$1" -eq "$1" ] 2>/dev/null; then
    PORT="$1"
    shift
fi

echo "Starting MCP server..."
echo "Running: python -u coppelia_mcp.py --host 0.0.0.0 --port $PORT $@"
echo "Attempting to connect to CoppeliaSim..."
echo "Note: CoppeliaSim must be running and accessible at the specified host on port 23000"
exec python -u coppelia_mcp.py --host 0.0.0.0 --port "$PORT" "$@" 