from fastmcp.server import FastMCP
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import math
import logging
from describe import describe_robot, list_joints, describe_scene_and_robot
from fastmcp.server.http import create_sse_app
import argparse
from prompts import list_prompts_metadata, get_prompt_by_name
from fastapi import Request
from fastapi.responses import JSONResponse

server = FastMCP()

print("🚀 Starting MCP server (fastmcp)...")

# Connect to CoppeliaSim
try:
    client = RemoteAPIClient('127.0.0.1', 23000)
    sim = client.getObject('sim')
    print("✅ Connected to CoppeliaSim")
except Exception as e:
    print("⚠️ Could not connect to CoppeliaSim:", e)
    sim = None

@server.tool()
def rotate_joint(joint_name: str, angle_deg: float):
    if sim is None:
        raise Exception("CoppeliaSim not connected")
    joint_handle = sim.getObjectHandle(joint_name)
    angle_rad = math.radians(angle_deg)
    sim.setJointTargetPosition(joint_handle, angle_rad)
    return f"Joint '{joint_name}' rotated to {angle_deg} degrees."

@server.tool()
def describe_robot():
    try:
        result = describe_robot_orig()
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
        return text
    except Exception as e:
        logging.exception(f"Error in describe_robot: {str(e)}")
        raise Exception(f"Internal error in describe_robot: {str(e)}")

@server.tool()
def list_joints():
    try:
        joint_handles = sim.getObjectsInTree(sim.handle_scene, sim.object_joint_type)
        if isinstance(joint_handles, int) and joint_handles == -1:
            raise Exception("Failed to retrieve joint handles. Check object type and scene setup.")
        joints = []
        for handle in joint_handles:
            name = sim.getObjectAlias(handle)
            joint_type = sim.getJointType(handle)
            cyclic, interval = sim.getJointInterval(handle)
            if cyclic:
                limits_deg = ["Cyclic", "Cyclic"]
            else:
                min_value = interval[0]
                range_value = interval[1]
                limits_deg = [math.degrees(min_value), math.degrees(min_value + range_value)]
            position = sim.getJointPosition(handle)
            joints.append({
                "id": handle,
                "alias": name,
                "position": position,
                "type": joint_type,
                "limits_deg": limits_deg
            })
        return {"joints": joints}
    except Exception as e:
        logging.error(f"Error in list_joints: {str(e)}")
        raise Exception(f"Internal error: {str(e)}")

@server.tool()
def describe_scene_and_robot():
    try:
        return describe_scene_and_robot()
    except Exception as e:
        logging.exception(f"Error in describe_scene_and_robot: {str(e)}")
        raise Exception(f"Internal error in describe_scene_and_robot: {str(e)}")

app = create_sse_app(server, message_path="/", sse_path="/sse")

@app.api_route("/prompts/list", methods=["GET", "POST"])
async def prompts_list(request: Request):
    return JSONResponse({"prompts": list_prompts_metadata()})

@app.api_route("/prompts/get", methods=["POST"])
async def prompts_get(request: Request):
    body = await request.json()
    name = body.get("name")
    arguments = body.get("arguments", {})
    prompt = get_prompt_by_name(name, arguments)
    if prompt is None:
        return JSONResponse({"error": f"Prompt '{name}' not found"}, status_code=404)
    return JSONResponse({
        "description": prompt.get("description", ""),
        "messages": prompt["messages"]
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoppeliaSim FastMCP Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)

