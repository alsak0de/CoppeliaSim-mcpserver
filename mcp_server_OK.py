from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import asyncio
import math

app = FastAPI()

print("🚀 Starting MCP server...")

# Connect to CoppeliaSim
try:
    client = RemoteAPIClient('127.0.0.1', 23000)
    sim = client.getObject('sim')
    print("✅ Connected to CoppeliaSim")
except Exception as e:
    print("⚠️ Could not connect to CoppeliaSim:", e)
    sim = None

# SSE endpoint
@app.api_route("/sse", methods=["GET", "POST"])
async def sse(request: Request):
    if request.method == "POST":
        try:
            body = await request.json()
            print("📦 JSON-RPC via POST /sse:", body)

            method = body.get("method")
            rpc_id = body.get("id")
            params = body.get("params", {})

            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "CoppeliaSim MCP",
                            "version": "1.0"
                        }
                    }
                }

            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "tools": [
                            {
                                "name": "rotate_joint",
                                "description": "Rotates a joint to a given angle.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "joint_name": {"type": "string"},
                                        "angle_deg": {"type": "number"}
                                    },
                                    "required": ["joint_name", "angle_deg"]
                                }
                            }
                        ]
                    }
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name == "rotate_joint":
                    joint_name = arguments.get("joint_name")
                    angle_deg = arguments.get("angle_deg")

                    if sim is None:
                        raise Exception("CoppeliaSim not connected")

                    joint_handle = sim.getObjectHandle(joint_name)
                    angle_rad = math.radians(angle_deg)
                    sim.setJointTargetPosition(joint_handle, angle_rad)

                    return {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Joint '{joint_name}' rotated to {angle_deg} degrees."
                                }
                            ]
                        }
                    }

                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found"
                    }
                }

            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                }
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Exception: {str(e)}"
                }
            }

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            yield {
                "event": "ping",
                "data": "heartbeat"
            }
            await asyncio.sleep(10)

    return EventSourceResponse(event_generator())

@app.post("/")
async def jsonrpc_handler(request: Request):
    print("📥 Received POST / request")

    try:
        body = await request.json()
        print("📦 Request JSON:", body)

        method = body.get("method")
        rpc_id = body.get("id")
        params = body.get("params", {})

        print(f"🔧 Handling method: {method} (id: {rpc_id})")

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "CoppeliaSim MCP",
                        "version": "1.0"
                    }
                }
            }
            print("📤 Responding with:", response)
            return response

        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "tools": [
                        {
                            "name": "rotate_joint",
                            "description": "Rotates a joint to a given angle.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "joint_name": {"type": "string"},
                                    "angle_deg": {"type": "number"}
                                },
                                "required": ["joint_name", "angle_deg"]
                            }
                        }
                    ]
                }
            }
            print("📤 Responding with:", response)
            return response

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "rotate_joint":
                joint_name = arguments.get("joint_name")
                angle_deg = arguments.get("angle_deg")

                if sim is None:
                    raise Exception("CoppeliaSim not connected")

                joint_handle = sim.getObjectHandle(joint_name)
                angle_rad = math.radians(angle_deg)
                sim.setJointTargetPosition(joint_handle, angle_rad)

                response = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Joint '{joint_name}' rotated to {angle_deg} degrees."
                            }
                        ]
                    }
                }
                print("📤 Responding with:", response)
                return response

            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found"
                    }
                }
                print("📤 Responding with:", response)
                return response

        response = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not supported"
            }
        }
        print("📤 Responding with:", response)
        return response

    except Exception as e:
        print("💥 Exception in handler:", str(e))
        response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
        print("📤 Responding with:", response)
        return response

