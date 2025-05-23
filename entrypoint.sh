#!/bin/sh

# Default port
PORT=8000

# Check if first argument is a number (port)
if [ "$1" -eq "$1" ] 2>/dev/null; then
    PORT="$1"
    shift
fi

echo "Running: python coppelia_mcp.py --host 0.0.0.0 --port $PORT $@"
exec python coppelia_mcp.py --host 0.0.0.0 --port "$PORT" "$@" 