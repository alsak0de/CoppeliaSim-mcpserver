# CoppeliaSlim MCP Server

A Python-based MCP (Motion Control Protocol) server implementation for CoppeliaSim (formerly V-REP) robotics simulation.

## Features

- JSON-RPC 2.0 protocol implementation
- Joint control and monitoring
- Real-time position and state tracking
- Comprehensive error handling and logging

## Requirements

- Python 3.x
- CoppeliaSim (formerly V-REP)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/alsak0de/CoppeliaSlim-mcpserver.git
cd CoppeliaSlim-mcpserver
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start CoppeliaSim and load your robot model
2. Run the MCP server:
```bash
python mcp_server.py
```

## API

The server implements the following JSON-RPC methods:

- `list_joints`: Returns a list of available joints with their properties
- `get_joint_position`: Gets the current position of a specified joint
- `set_joint_position`: Sets the position of a specified joint

## License

MIT License 