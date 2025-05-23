#!/bin/sh

PORT="${1:-8000}"
shift || true
echo "Running: python coppelia_mcp.py --host 0.0.0.0 --port $PORT $@"
exec python coppelia_mcp.py --host 0.0.0.0 --port "$PORT" "$@" 