from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import asyncio
import math
from describe import describe_robot, list_joints, describe_scene
import logging
from prompts import list_prompts_metadata, get_prompt_by_name
import argparse
import os

app = FastAPI()

print("🚀 Starting MCP server...")

# Connect to CoppeliaSim
# Precedence: COPPELIASIM_HOST env var > --coppeliaHost arg (if __main__) > '127.0.0.1'
coppelia_host = os.environ.get("COPPELIASIM_HOST", "127.0.0.1")
try:
    client = RemoteAPIClient(coppelia_host, 23000)
    sim = client.getObject('sim')
    print(f"✅ Connected to CoppeliaSim at {coppelia_host}")
except Exception as e:
    print(f"⚠️ Could not connect to CoppeliaSim at {coppelia_host}:", e)
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

                elif tool_name == "describe_robot":
                    try:
                        result = describe_robot()
                        robots = result.get("robots", [])
                        type_map = {
                            0: "shape",
                            1: "joint",
                            2: "graph",
                            3: "camera",
                            4: "light",
                            5: "dummy",
                            6: "proximity sensor",
                            7: "octree",
                            8: "point cloud",
                            9: "vision sensor",
                            10: "force sensor",
                            11: "script"
                        }
                        if not robots:
                            text = "No robots found in the scene."
                        else:
                            text = ""
                            for robot in robots:
                                text += f"Robot base: {robot['base_name']} (handle: {robot['base_handle']})\n"
                                for elem in robot['elements']:
                                    type_name = type_map.get(elem['type'], f"unknown({elem['type']})")
                                    text += (
                                        f"  - {elem['name']} (type: {type_name}, handle: {elem['handle']}, "
                                        f"pos: {elem['position']}, orient: {elem['orientation']})\n"
                                    )
                                text += "\n"
                        return {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": text
                                    }
                                ]
                            }
                        }
                    except Exception as e:
                        logging.exception(f"Error in describe_robot: {str(e)}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "error": {
                                "code": -32603,
                                "message": f"Internal error in describe_robot: {str(e)}"
                            }
                        }
                        return error_response

                elif tool_name == "describe_scene":
                    try:
                        result = describe_scene()
                        return {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": (
                                            "Objects:\n" +
                                            "\n".join(
                                                f"{o.get('name', '')} (type: {o.get('type', '')}, pos: {o.get('position', '')}, orient: {o.get('orientation', '')})"
                                                for o in result.get('objects', [])
                                            )
                                        )
                                    }
                                ]
                            }
                        }
                    except Exception as e:
                        logging.exception(f"Error in describe_scene: {str(e)}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "error": {
                                "code": -32603,
                                "message": f"Internal error in describe_scene: {str(e)}"
                            }
                        }
                        return error_response

                elif tool_name == "list_joints":
                    try:
                        # Use sim.getObjectsInTree to retrieve joint handles
                        joint_handles = sim.getObjectsInTree(sim.handle_scene, sim.object_joint_type)
                        logging.info(f"Retrieved joint handles: {joint_handles}")
                        if isinstance(joint_handles, int) and joint_handles == -1:
                            raise Exception("Failed to retrieve joint handles. Check object type and scene setup.")

                        joints = []
                        for handle in joint_handles:
                            name = sim.getObjectAlias(handle)
                            logging.info(f"Joint handle {handle} has alias: {name}")
                            joint_type = sim.getJointType(handle)
                            logging.info(f"Joint handle {handle} has type: {joint_type}")
                            cyclic, interval = sim.getJointInterval(handle)
                            logging.info(f"Joint handle {handle} has interval data: cyclic={cyclic}, interval={interval}")
                            if cyclic:
                                limits_deg = ["Cyclic", "Cyclic"]
                            else:
                                min_value = interval[0]
                                range_value = interval[1]
                                limits_deg = [math.degrees(min_value), math.degrees(min_value + range_value)]
                            position = sim.getJointPosition(handle)  # Assuming this function exists to get the joint position
                            logging.info(f"Joint handle {handle} has position: {position}")
                            joints.append({
                                "id": handle,
                                "alias": name,
                                "position": position,
                                "type": joint_type,
                                "limits_deg": limits_deg
                            })

                        response = {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "\n".join(
                                            f"{j['alias']} (id: {j['id']}), pos: {j['position']}, type: {j['type']}, limits: {j['limits_deg']}"
                                            for j in joints
                                        )
                                    }
                                ]
                            }
                        }
                        logging.info(f"Responding with: {response}")
                        return response
                    except Exception as e:
                        logging.error(f"Error in list_joints: {str(e)}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "error": {
                                "code": -32603,
                                "message": f"Internal error: {str(e)}"
                            }
                        }
                        logging.info(f"Responding with error: {error_response}")
                        return error_response

                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found"
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

            elif tool_name == "describe_robot":
                try:
                    result = describe_robot()
                    robots = result.get("robots", [])
                    type_map = {
                        0: "shape",
                        1: "joint",
                        2: "graph",
                        3: "camera",
                        4: "light",
                        5: "dummy",
                        6: "proximity sensor",
                        7: "octree",
                        8: "point cloud",
                        9: "vision sensor",
                        10: "force sensor",
                        11: "script"
                    }
                    if not robots:
                        text = "No robots found in the scene."
                    else:
                        text = ""
                        for robot in robots:
                            text += f"Robot base: {robot['base_name']} (handle: {robot['base_handle']})\n"
                            for elem in robot['elements']:
                                type_name = type_map.get(elem['type'], f"unknown({elem['type']})")
                                text += (
                                    f"  - {elem['name']} (type: {type_name}, handle: {elem['handle']}, "
                                    f"pos: {elem['position']}, orient: {elem['orientation']})\n"
                                )
                            text += "\n"
                    return {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": text
                                }
                            ]
                        }
                    }
                except Exception as e:
                    logging.exception(f"Error in describe_robot: {str(e)}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error in describe_robot: {str(e)}"
                        }
                    }
                    return error_response

            elif tool_name == "describe_scene":
                try:
                    result = describe_scene()
                    return {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Objects:\n" +
                                        "\n".join(
                                            f"{o.get('name', '')} (type: {o.get('type', '')}, pos: {o.get('position', '')}, orient: {o.get('orientation', '')})"
                                            for o in result.get('objects', [])
                                        )
                                    )
                                }
                            ]
                        }
                    }
                except Exception as e:
                    logging.exception(f"Error in describe_scene: {str(e)}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error in describe_scene: {str(e)}"
                        }
                    }
                    return error_response

            elif tool_name == "list_joints":
                try:
                    # Use sim.getObjectsInTree to retrieve joint handles
                    joint_handles = sim.getObjectsInTree(sim.handle_scene, sim.object_joint_type)
                    logging.info(f"Retrieved joint handles: {joint_handles}")
                    if isinstance(joint_handles, int) and joint_handles == -1:
                        raise Exception("Failed to retrieve joint handles. Check object type and scene setup.")

                    joints = []
                    for handle in joint_handles:
                        name = sim.getObjectAlias(handle)
                        logging.info(f"Joint handle {handle} has alias: {name}")
                        joint_type = sim.getJointType(handle)
                        logging.info(f"Joint handle {handle} has type: {joint_type}")
                        cyclic, interval = sim.getJointInterval(handle)
                        logging.info(f"Joint handle {handle} has interval data: cyclic={cyclic}, interval={interval}")
                        if cyclic:
                            limits_deg = ["Cyclic", "Cyclic"]
                        else:
                            min_value = interval[0]
                            range_value = interval[1]
                            limits_deg = [math.degrees(min_value), math.degrees(min_value + range_value)]
                        position = sim.getJointPosition(handle)  # Assuming this function exists to get the joint position
                        logging.info(f"Joint handle {handle} has position: {position}")
                        joints.append({
                            "id": handle,
                            "alias": name,
                            "position": position,
                            "type": joint_type,
                            "limits_deg": limits_deg
                        })

                    response = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "\n".join(
                                        f"{j['alias']} (id: {j['id']}), pos: {j['position']}, type: {j['type']}, limits: {j['limits_deg']}"
                                        for j in joints
                                    )
                                }
                            ]
                        }
                    }
                    logging.info(f"Responding with: {response}")
                    return response
                except Exception as e:
                    logging.error(f"Error in list_joints: {str(e)}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    logging.info(f"Responding with error: {error_response}")
                    return error_response

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

    # If --coppeliaHost is provided, override env var and default
    coppelia_host = args.coppeliaHost or os.environ.get("COPPELIASIM_HOST", "127.0.0.1")
    try:
        client = RemoteAPIClient(coppelia_host, 23000)
        sim = client.getObject('sim')
        print(f"✅ Connected to CoppeliaSim at {coppelia_host}")
    except Exception as e:
        print(f"⚠️ Could not connect to CoppeliaSim at {coppelia_host}:", e)
        sim = None

    uvicorn.run(app, host=args.host, port=args.port)

