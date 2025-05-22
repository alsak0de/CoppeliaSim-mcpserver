# MCP Prompts - schema-compliant and reusable

from typing import List, Dict, Any, Optional
import copy

# Expanded, context-rich prompt definitions for all existing functionalities
PROMPTS = [
    {
        "name": "rotate_joint_prompt",
        "description": "Request to rotate a specific robot joint to a target angle. Users may use terms like 'move', 'set', or 'turn' and refer to joints by name or function.",
        "arguments": [
            {"name": "joint_name", "description": "Name or alias of the joint to rotate (e.g., 'base', 'elbow', 'wrist').", "required": True},
            {"name": "angle_deg", "description": "Target angle in degrees (can be positive or negative).", "required": True}
        ],
        "messages": [
            {
                "role": "system",
                "content": {
                    "type": "text",
                    "text": "You are controlling a simulated robot. The user may ask to move, rotate, or set a joint to a specific angle. Joints may be referred to by name, function, or alias."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Rotate the {joint_name} to {angle_deg} degrees."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Set the {joint_name} joint at {angle_deg}°."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Move {joint_name} by {angle_deg} degrees."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Can you turn the {joint_name} joint to {angle_deg} degrees?"
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Adjust the {joint_name} to {angle_deg} degrees."
                }
            }
        ]
    },
    {
        "name": "describe_scene",
        "description": "Request a description of all objects in the simulation scene, excluding robot joints. Users may ask about the workspace, environment, or objects present.",
        "messages": [
            {
                "role": "system",
                "content": {
                    "type": "text",
                    "text": "You are a robot simulation assistant. The user may ask about the environment, workspace, or objects in the scene. Exclude robot joints from the description."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Describe the scene."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "What objects are present in the workspace?"
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "List all non-robot objects in the simulation."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Show me the environment and items in the scene."
                }
            }
        ]
    },
    {
        "name": "list_joints",
        "description": "Request a list of all robot joints, their types, and limits. Users may ask for joint names, types, or movement ranges.",
        "messages": [
            {
                "role": "system",
                "content": {
                    "type": "text",
                    "text": "You are a robot simulation assistant. The user may ask for a list of joints, their types, or their movement limits."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "List all joints of the robot."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "What joints does the robot have?"
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Show me the types and limits of each joint."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Can you list the robot's joints and their movement ranges?"
                }
            }
        ]
    },
    {
        "name": "describe_robot",
        "description": "Request a detailed, hierarchical description of all robot elements, including base, links, joints, and sensors. Users may ask for a summary or a full breakdown of the robot's structure.",
        "messages": [
            {
                "role": "system",
                "content": {
                    "type": "text",
                    "text": "You are a robot simulation assistant. The user may ask for a detailed description of the robot, including its structure, components, and hierarchy."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Describe the robot."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Give me a breakdown of the robot's structure."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "What elements make up the robot?"
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Show me all the parts and sensors of the robot."
                }
            }
        ]
    },
    {
        "name": "robot_capabilities",
        "description": "Describes the robot's capabilities, including movement types, speed, and precision. Users may ask what the robot can do or what tasks it is suited for.",
        "messages": [
            {
                "role": "system",
                "content": {
                    "type": "text",
                    "text": "You are a robot simulation assistant. The user may ask about the robot's capabilities, such as movement, speed, and precision."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "What can this robot do?"
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Tell me about the robot's capabilities."
                }
            },
            {
                "role": "assistant",
                "content": {
                    "type": "text",
                    "text": "The robot can perform various movements such as rotating joints, moving along predefined paths, and adjusting its position with precision. It operates at a maximum speed of X units per second."
                }
            }
        ]
    },
    {
        "name": "robot_constraints",
        "description": "Describes the constraints and limitations of the robot, such as joint limits, workspace boundaries, and environmental factors.",
        "messages": [
            {
                "role": "system",
                "content": {
                    "type": "text",
                    "text": "You are a robot simulation assistant. The user may ask about the robot's constraints, such as joint limits, workspace boundaries, or environmental limitations."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "What are the robot's limitations?"
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Tell me about the constraints of the robot."
                }
            },
            {
                "role": "assistant",
                "content": {
                    "type": "text",
                    "text": "The robot has joint limits that restrict its range of motion. It cannot exceed certain angles or positions due to physical constraints. Environmental factors such as obstacles and boundaries also limit its operation."
                }
            }
        ]
    },
    {
        "name": "robot_use_cases",
        "description": "Provides example scenarios of how the robot is typically used, such as assembly, inspection, and material handling.",
        "messages": [
            {
                "role": "system",
                "content": {
                    "type": "text",
                    "text": "You are a robot simulation assistant. The user may ask for example use cases or typical applications of the robot."
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "What tasks is this robot good at?"
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Give me some example use cases for the robot."
                }
            },
            {
                "role": "assistant",
                "content": {
                    "type": "text",
                    "text": "The robot is commonly used for tasks such as assembly, inspection, and material handling. In an assembly line, it can precisely position components and perform repetitive tasks efficiently."
                }
            }
        ]
    }
]

def list_prompts_metadata() -> List[Dict[str, Any]]:
    """Return prompt metadata (name, description, arguments) for listing."""
    result = []
    for p in PROMPTS:
        meta = {"name": p["name"]}
        if "description" in p:
            meta["description"] = p["description"]
        if "arguments" in p:
            meta["arguments"] = p["arguments"]
        result.append(meta)
    return result

def get_prompt_by_name(name: str, arguments: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a prompt by name, optionally interpolating arguments."""
    for p in PROMPTS:
        if p["name"] == name:
            prompt = copy.deepcopy(p)
            # Interpolate arguments in messages if needed
            if arguments:
                for msg in prompt.get("messages", []):
                    if msg["content"]["type"] == "text":
                        msg["content"]["text"] = msg["content"]["text"].format(**arguments)
            return prompt
    return None 