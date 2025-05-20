from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import asyncio
import math
from robot.describe import describe_robot, list_joints, describe_scene_and_robot
import logging

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

prompts = [
    {
        "name": "rotate_joint_prompt",
        "description": "Prompt to rotate a specific joint to a desired angle.",
        "arguments": [
            {
                "name": "joint_name",
                "description": "Name of the joint to rotate.",
                "required": True
            },
            {
                "name": "angle_deg",
                "description": "Target angle in degrees.",
                "required": True
            }
        ]
    },
    {
        "name": "robot_capabilities",
        "description": "Describes the robot's capabilities, including movement types and speed.",
        "content": "The robot can perform various movements such as rotating joints, moving along predefined paths, and adjusting its position with precision. It operates at a maximum speed of X units per second."
    },
    {
        "name": "robot_constraints",
        "description": "Describes the constraints and limitations of the robot.",
        "content": "The robot has joint limits that restrict its range of motion. It cannot exceed certain angles or positions due to physical constraints. Environmental factors such as obstacles and boundaries also limit its operation."
    },
    {
        "name": "robot_use_cases",
        "description": "Provides example scenarios of how the robot is typically used.",
        "content": "The robot is commonly used for tasks such as assembly, inspection, and material handling. In an assembly line, it can precisely position components and perform repetitive tasks efficiently."
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
                                "description": "Describes the robot's type, joint count, and naming convention.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                },
                                "resultSchema": {
                                    "type": "object",
                                    "properties": {
                                        "robot_type": {"type": "string"},
                                        "joint_count": {"type": "number"},
                                        "naming_convention": {"type": "string"},
                                        "description": {"type": "string"}
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
                            },
                            {
                                "name": "describe_scene_and_robot",
                                "description": "Provides a comprehensive description of the robot and scene.",
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
                                                    "name": {"type": "string"},
                                                    "type": {"type": "string"},
                                                    "limits": {"type": "array", "items": {"type": "number"}}
                                                }
                                            }
                                        },
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
                    result = describe_robot()
                    return {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": result
                    }

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
                            "result": {"joints": joints}
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

                elif tool_name == "describe_scene_and_robot":
                    result = describe_scene_and_robot()
                    return {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": result
                    }

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
                        "prompts": prompts
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
                            "description": "Describes the robot's type, joint count, and naming convention.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            },
                            "resultSchema": {
                                "type": "object",
                                "properties": {
                                    "robot_type": {"type": "string"},
                                    "joint_count": {"type": "number"},
                                    "naming_convention": {"type": "string"},
                                    "description": {"type": "string"}
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
                        },
                        {
                            "name": "describe_scene_and_robot",
                            "description": "Provides a comprehensive description of the robot and scene.",
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
                                                "name": {"type": "string"},
                                                "type": {"type": "string"},
                                                "limits": {"type": "array", "items": {"type": "number"}}
                                            }
                                        }
                                    },
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
                result = describe_robot()
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": result
                }

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
                        "result": {"joints": joints}
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

            elif tool_name == "describe_scene_and_robot":
                result = describe_scene_and_robot()
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": result
                }

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
                    "prompts": prompts
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

