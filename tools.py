import math
import logging

def rotate_joint(sim, joint_name: str, angle_deg: float):
    if sim is None:
        raise Exception("CoppeliaSim not connected")
    joint_handle = sim.getObjectHandle(joint_name)
    angle_rad = math.radians(angle_deg)
    sim.setJointTargetPosition(joint_handle, angle_rad)
    return f"Joint '{joint_name}' rotated to {angle_deg} degrees."

def describe_robot(sim):
    try:
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

def list_joints(sim):
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
        return joints
    except Exception as e:
        logging.error(f"Error in list_joints: {str(e)}")
        raise Exception(f"Internal error: {str(e)}")

def describe_scene(sim):
    try:
        object_handles = sim.getObjectsInTree(sim.handle_scene)
        joint_handles = sim.getObjects(sim.object_joint_type, -1)
        if isinstance(joint_handles, int) and joint_handles == -1:
            joint_handles = []
        objects = []
        for handle in object_handles:
            if handle in joint_handles:
                continue  # Skip robot joints
            name = sim.getObjectAlias(handle)
            obj_type = sim.getObjectType(handle)
            position = sim.getObjectPosition(handle, -1)
            orientation = sim.getObjectOrientation(handle, -1)
            objects.append({
                "name": name,
                "type": obj_type,
                "position": position,
                "orientation": orientation
            })
        return objects
    except Exception as e:
        logging.exception(f"Error in describe_scene: {str(e)}")
        raise Exception(f"Internal error in describe_scene: {str(e)}") 