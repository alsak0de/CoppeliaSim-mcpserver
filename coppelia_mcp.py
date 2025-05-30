from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import asyncio
import math
from tools import rotate_joint, list_joints, describe_robot, describe_scene
import logging
from prompts import list_prompts_metadata, get_prompt_by_name
import argparse
import os

app = FastAPI()

print("🚀 Starting MCP server...")

# Global variables
client = None
sim = None

# Define resources and prompts
resources = [
    {
        "uri": "local:///mcp/docs/rotate_joint_usage.txt",
        "name": "Rotate Joint Usage Guide",
        "description": "Explains how to use the rotate_joint tool and expected parameters.",
        "mime_type": "text/plain",
        "content": "Use the rotate_joint tool by specifying 'joint_name' and 'angle_deg'. The angle is in degrees."
    }
]

@app.on_event("startup")
def connect_to_coppeliasim():
    global client, sim
    coppelia_host = os.environ.get("COPPELIASIM_HOST", "127.0.0.1")
    print(f"Attempting to connect to CoppeliaSim at {coppelia_host}:23000")
    try:
        client = RemoteAPIClient(coppelia_host, 23000)
        print("RemoteAPIClient created, attempting to get 'sim' object...")
        sim = client.getObject('sim')
        print(f"✅ Connected to CoppeliaSim at {coppelia_host}:23000")
    except Exception as e:
        print(f"⚠️ Could not connect to CoppeliaSim at {coppelia_host}:23000")
        print(f"Error details: {str(e)}")
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
                            },
                            {
                                "name": "describe_robot",
                                "description": "Describes the robot's joints and their details.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                },
                                "resultSchema": {
                                    "type": "object",
                                    "properties": {
                                        "joint_count": {"type": "number"},
                                        "joints": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "type": {"type": "string"},
                                                    "limits": {"type": "array", "items": {"type": "number"}}
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "name": "describe_scene",
                                "description": "Describes the scene objects (excluding robot joints).",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                },
                                "resultSchema": {
                                    "type": "object",
                                    "properties": {
                                        "objects": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "type": {"type": "string"},
                                                    "position": {"type": "array", "items": {"type": "number"}},
                                                    "orientation": {"type": "array", "items": {"type": "number"}}
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            {
                                "name": "list_joints",
                                "description": "Lists all joints with their types and limits.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                },
                                "resultSchema": {
                                    "type": "object",
                                    "properties": {
                                        "joints": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "number"},
                                                    "alias": {"type": "string"},
                                                    "position": {"type": "array", "items": {"type": "number"}},
                                                    "type": {"type": "string"},
                                                    "limits_deg": {
                                                        "type": "array",
                                                        "items": {"type": "number"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                try:
                    if sim is None:
                        raise Exception("CoppeliaSim not connected (sim is None)")
                    if tool_name == "rotate_joint":
                        joint_name = arguments.get("joint_name")
                        angle_deg = arguments.get("angle_deg")
                        result = rotate_joint(sim, joint_name, angle_deg)
                        return {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "result": {
                                "content": [
                                    {"type": "text", "text": result}
                                ]
                            }
                        }
                    elif tool_name == "describe_robot":
                        text = describe_robot(sim)
                        return {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "result": {
                                "content": [
                                    {"type": "text", "text": text}
                                ]
                            }
                        }
                    elif tool_name == "describe_scene":
                        objects = describe_scene(sim)
                        return {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "result": {
                                "content": [
                                    {"type": "text", "text": (
                                        "Objects:\n" +
                                        "\n".join(
                                            f"{o.get('name', '')} (type: {o.get('type', '')}, pos: {o.get('position', '')}, orient: {o.get('orientation', '')})"
                                            for o in objects
                                        )
                                    )}
                                ]
                            }
                        }
                    elif tool_name == "list_joints":
                        joints = list_joints(sim)
                        return {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "result": {
                                "content": [
                                    {"type": "text", "text": "\n".join(
                                        f"{j['alias']} (id: {j['id']}), pos: {j['position']}, type: {j['type']}, limits: {j['limits_deg']}"
                                        for j in joints
                                    )}
                                ]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "error": {
                                "code": -32601,
                                "message": f"Tool '{tool_name}' not found"
                            }
                        }
                except Exception as e:
                    logging.exception(f"Error in tool '{tool_name}': {str(e)}")
                    return {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error in tool '{tool_name}': {str(e)}"
                        }
                    }

            elif method == "resources/list":
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "resources": resources
                    }
                }

            elif method == "prompts/list":
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "prompts": list_prompts_metadata()
                    }
                }
            elif method == "prompts/get":
                prompt_name = params.get("name")
                arguments = params.get("arguments", {})
                prompt = get_prompt_by_name(prompt_name, arguments)
                if prompt is None:
                    return {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {
                            "code": -32602,
                            "message": f"Prompt '{prompt_name}' not found"
                        }
                    }
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "description": prompt.get("description", ""),
                        "messages": prompt["messages"]
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
                        },
                        {
                            "name": "describe_robot",
                            "description": "Describes the robot's joints and their details.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            },
                            "resultSchema": {
                                "type": "object",
                                "properties": {
                                    "joint_count": {"type": "number"},
                                    "joints": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "type": {"type": "string"},
                                                "limits": {"type": "array", "items": {"type": "number"}}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        {
                            "name": "describe_scene",
                            "description": "Describes the scene objects (excluding robot joints).",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            },
                            "resultSchema": {
                                "type": "object",
                                "properties": {
                                    "objects": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "type": {"type": "string"},
                                                "position": {"type": "array", "items": {"type": "number"}},
                                                "orientation": {"type": "array", "items": {"type": "number"}}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        {
                            "name": "list_joints",
                            "description": "Lists all joints with their types and limits.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            },
                            "resultSchema": {
                                "type": "object",
                                "properties": {
                                    "joints": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "number"},
                                                "alias": {"type": "string"},
                                                "position": {"type": "array", "items": {"type": "number"}},
                                                "type": {"type": "string"},
                                                "limits_deg": {
                                                    "type": "array",
                                                    "items": {"type": "number"}
                                                }
                                            }
                                        }
                                    }
                                }
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

            try:
                if sim is None:
                    raise Exception("CoppeliaSim not connected (sim is None)")
                if tool_name == "rotate_joint":
                    joint_name = arguments.get("joint_name")
                    angle_deg = arguments.get("angle_deg")
                    result = rotate_joint(sim, joint_name, angle_deg)
                    response = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": {
                            "content": [
                                {"type": "text", "text": result}
                            ]
                        }
                    }
                    print("📤 Responding with:", response)
                    return response
                elif tool_name == "describe_robot":
                    text = describe_robot(sim)
                    response = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": {
                            "content": [
                                {"type": "text", "text": text}
                            ]
                        }
                    }
                    print("📤 Responding with:", response)
                    return response
                elif tool_name == "describe_scene":
                    objects = describe_scene(sim)
                    response = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": {
                            "content": [
                                {"type": "text", "text": (
                                    "Objects:\n" +
                                    "\n".join(
                                        f"{o.get('name', '')} (type: {o.get('type', '')}, pos: {o.get('position', '')}, orient: {o.get('orientation', '')})"
                                        for o in objects
                                    )
                                )}
                            ]
                        }
                    }
                    print("📤 Responding with:", response)
                    return response
                elif tool_name == "list_joints":
                    joints = list_joints(sim)
                    response = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": {
                            "content": [
                                {"type": "text", "text": "\n".join(
                                    f"{j['alias']} (id: {j['id']}), pos: {j['position']}, type: {j['type']}, limits: {j['limits_deg']}"
                                    for j in joints
                                )}
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
            except Exception as e:
                print(f"💥 Exception in tool '{tool_name}':", str(e))
                response = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error in tool '{tool_name}': {str(e)}"
                    }
                }
                print("📤 Responding with:", response)
                return response

        elif method == "resources/list":
            response = {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "resources": resources
                }
            }
            print("📤 Responding with:", response)
            return response

        elif method == "prompts/list":
            response = {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "prompts": list_prompts_metadata()
                }
            }
            print("📤 Responding with:", response)
            return response

        elif method == "prompts/get":
            prompt_name = params.get("name")
            arguments = params.get("arguments", {})
            prompt = get_prompt_by_name(prompt_name, arguments)
            if prompt is None:
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32602,
                        "message": f"Prompt '{prompt_name}' not found"
                    }
                }
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "description": prompt.get("description", ""),
                    "messages": prompt["messages"]
                }
            }

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

if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser(description="CoppeliaSim MCP Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--coppeliaHost", type=str, default=None, help="Host for CoppeliaSim ZeroMQ remote API")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)

