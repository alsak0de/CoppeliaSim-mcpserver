from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import logging
import math

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to describe the robot

def describe_robot():
    logging.info("Executing describe_robot function")
    client = RemoteAPIClient()
    sim = client.getObject('sim')
    # Example data, replace with actual logic to fetch robot details
    robot_type = "Generic Robot"
    joint_count = len(sim.getObjects(sim.object_joint_type))
    naming_convention = "m1, m2, ..."
    description = "A generic robot with multiple joints."
    logging.info(f"Robot type: {robot_type}, Joint count: {joint_count}")
    return {
        "robot_type": robot_type,
        "joint_count": joint_count,
        "naming_convention": naming_convention,
        "description": description
    }

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

def describe_scene_and_robot():
    logging.info("Executing describe_scene_and_robot function")
    client = RemoteAPIClient()
    sim = client.getObject('sim')
    
    # Gather robot structure and components
    joint_handles = sim.getObjects(sim.object_joint_type)
    joints = []
    for handle in joint_handles:
        name = sim.getObjectName(handle)
        joint_type = sim.getJointType(handle)
        limits = sim.getJointInterval(handle)
        joints.append({
            "name": name,
            "type": joint_type,
            "limits": limits
        })
    logging.info(f"Joints collected: {len(joints)}")
    
    # Gather scene objects
    object_handles = sim.getObjectsInTree(sim.handle_scene)
    objects = []
    for handle in object_handles:
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
    logging.info(f"Objects collected: {len(objects)}")
    
    # Compile the comprehensive description
    description = {
        "joints": joints,
        "objects": objects
    }
    logging.info("Description compiled successfully")
    return description 