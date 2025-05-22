from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import logging
import math

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to describe the robot

def describe_robot():
    logging.info("Executing detailed describe_robot function")
    client = RemoteAPIClient()
    sim = client.getObject('sim')

    # Get all objects in the scene
    all_handles = sim.getObjectsInTree(sim.handle_scene, sim.handle_all)
    # Find top-level objects (parentless)
    top_level_handles = [h for h in all_handles if sim.getObjectParent(h) == -1]
    robots = []

    for base_handle in top_level_handles:
        # Check if this subtree contains joints (i.e., is a robot)
        joint_handles = sim.getObjectsInTree(base_handle, sim.object_joint_type)
        if isinstance(joint_handles, int) and joint_handles == -1:
            joint_handles = []
        if not joint_handles:
            continue  # Not a robot

        # Collect all elements in this robot
        subtree_handles = sim.getObjectsInTree(base_handle, sim.handle_all)
        elements = []
        for h in subtree_handles:
            obj_type = sim.getObjectType(h)
            name = sim.getObjectAlias(h)
            position = sim.getObjectPosition(h, -1)
            orientation = sim.getObjectOrientation(h, -1)
            elements.append({
                "handle": h,
                "name": name,
                "type": obj_type,
                "position": position,
                "orientation": orientation
            })
        robots.append({
            "base_handle": base_handle,
            "base_name": sim.getObjectAlias(base_handle),
            "elements": elements
        })

    logging.info(f"Found {len(robots)} robot(s) in the scene.")
    return {"robots": robots}

# Function to list joints

def list_joints():
    logging.info("Executing list_joints function")
    client = RemoteAPIClient()
    sim = client.getObject('sim')
    
    # Correct the call to sim.getObjects with the required arguments
    joint_handles = sim.getObjects(sim.object_joint_type, -1)
    joints = []
    for handle in joint_handles:
        name = sim.getObjectName(handle)
        joint_type = sim.getJointType(handle)
        interval_data = sim.getJointInterval(handle)
        logging.info(f"Joint {name} interval data: {interval_data}, type: {type(interval_data)}")
        if isinstance(interval_data, (tuple, list)):
            limits = interval_data[0]
        elif isinstance(interval_data, int):
            limits = (interval_data, interval_data)
        else:
            logging.error(f"Unexpected interval data type for joint {name}: {type(interval_data)}")
            continue
        joints.append({
            "name": name,
            "type": joint_type,
            "limits_deg": [math.degrees(limits[0]), math.degrees(limits[1])]
        })
    
    return {"joints": joints}

def describe_scene():
    logging.info("Executing describe_scene function")
    client = RemoteAPIClient()
    sim = client.getObject('sim')
    # Get all objects in the scene
    object_handles = sim.getObjectsInTree(sim.handle_scene)
    # Get robot joint handles to exclude them
    joint_handles = sim.getObjects(sim.object_joint_type, -1)
    if isinstance(joint_handles, int) and joint_handles == -1:
        joint_handles = []
    objects = []
    for handle in object_handles:
        if handle in joint_handles:
            continue  # Skip robot joints
        name = sim.getObjectName(handle)
        obj_type = sim.getObjectType(handle)
        position = sim.getObjectPosition(handle, -1)
        orientation = sim.getObjectOrientation(handle, -1)
        objects.append({
            "name": name,
            "type": obj_type,
            "position": position,
            "orientation": orientation
        })
    logging.info(f"Scene objects collected (excluding joints): {len(objects)}")
    return {"objects": objects} 