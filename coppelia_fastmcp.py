from fastmcp.server import FastMCP
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import math
import logging
from tools import rotate_joint, list_joints, describe_robot, describe_scene
from fastmcp.server.http import create_sse_app
import argparse
from prompts import list_prompts_metadata, get_prompt_by_name
from fastapi import Request
from starlette.responses import JSONResponse

server = FastMCP()

print("🚀 Starting MCP server (fastmcp)...")

client = None
sim = None

def connect_to_coppeliasim(host="127.0.0.1"):
    global client, sim
    print(f"Attempting to connect to CoppeliaSim at {host}:23000")
    try:
        client = RemoteAPIClient(host, 23000)
        sim = client.getObject('sim')
        print(f"✅ Connected to CoppeliaSim at {host}:23000")
    except Exception as e:
        print(f"⚠️ Could not connect to CoppeliaSim at {host}:23000")
        print(f"Error details: {str(e)}")
        sim = None

# Call at import time for default host
connect_to_coppeliasim()

@server.tool()
def rotate_joint_tool(joint_name: str, angle_deg: float):
    if sim is None:
        raise Exception("CoppeliaSim not connected (sim is None)")
    return rotate_joint(sim, joint_name, angle_deg)

@server.tool()
def describe_robot_tool():
    if sim is None:
        raise Exception("CoppeliaSim not connected (sim is None)")
    return describe_robot(sim)

@server.tool()
def list_joints_tool():
    if sim is None:
        raise Exception("CoppeliaSim not connected (sim is None)")
    return list_joints(sim)

@server.tool()
def describe_scene_tool():
    if sim is None:
        raise Exception("CoppeliaSim not connected (sim is None)")
    return describe_scene(sim)

app = create_sse_app(server, message_path="/", sse_path="/sse")

async def prompts_list(request):
    return JSONResponse({"prompts": list_prompts_metadata()})

async def prompts_get(request):
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

app.add_route("/prompts/list", prompts_list, methods=["GET", "POST"])
app.add_route("/prompts/get", prompts_get, methods=["POST"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoppeliaSim FastMCP Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--coppeliaHost", type=str, default="127.0.0.1", help="Host for CoppeliaSim ZeroMQ remote API")
    args = parser.parse_args()

    # Connect to CoppeliaSim with the specified host
    connect_to_coppeliasim(args.coppeliaHost)

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

