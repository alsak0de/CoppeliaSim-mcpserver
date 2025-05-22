# MCP Resources - schema-compliant and reusable

import os
import base64
from typing import List, Dict, Any, Optional

# Only include real, available resources. Add more as needed.
RESOURCE_LIST = [
    {
        "uri": "local:///docs/rotate_joint_usage.txt",
        "name": "Rotate Joint Usage Guide",
        "description": "Explains how to use the rotate_joint tool and expected parameters.",
        "mimeType": "text/plain"
    }
    # Example for future expansion:
    # {
    #     "uri": "file://./robot_config.json",
    #     "name": "Robot Configuration",
    #     "description": "The main configuration file for the robot.",
    #     "mimeType": "application/json"
    # }
]

def list_resources() -> List[Dict[str, Any]]:
    """Return the list of available resources."""
    return RESOURCE_LIST

def read_resource(uri: str) -> Optional[Dict[str, Any]]:
    """Read the content of a resource by URI. Supports local files and file:// URIs."""
    # Handle local:/// URIs (example: usage guide)
    if uri.startswith("local:///"):
        local_path = uri.replace("local:///", "./")
        if not os.path.isfile(local_path):
            return None
        with open(local_path, "r", encoding="utf-8") as f:
            text = f.read()
        mimeType = "text/plain"
        for r in RESOURCE_LIST:
            if r["uri"] == uri:
                mimeType = r.get("mimeType", "text/plain")
        return {"uri": uri, "mimeType": mimeType, "text": text}
    # Handle file:// URIs
    elif uri.startswith("file://"):
        file_path = uri.replace("file://", "")
        if not os.path.isfile(file_path):
            return None
        # Guess mimeType from resource list or extension
        mimeType = "text/plain"
        for r in RESOURCE_LIST:
            if r["uri"] == uri:
                mimeType = r.get("mimeType", "text/plain")
        # For now, only support text files
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return {"uri": uri, "mimeType": mimeType, "text": text}
    # Could add support for other protocols (e.g., screen://, postgres://) here
    else:
        return None 