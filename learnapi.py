from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import logging

# Configure logging
logging.basicConfig(filename='api_logs.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# Connect to CoppeliaSim
client = RemoteAPIClient('127.0.0.1', 23000)
sim = client.getObject('sim')

# Example function to log API requests and responses
def log_api_request_response(request, response):
    logging.info(f"Request: {request}")
    logging.info(f"Response: {response}")

# Example usage
try:
    # Connect to CoppeliaSim and retrieve all joint handles
    request = 'sim.getObjects(sim.object_joint_type, -1)'
    joint_handles = sim.getObjects(sim.object_joint_type, -1)
    log_api_request_response(request, joint_handles)

    if isinstance(joint_handles, int) and joint_handles == -1:
        logging.error("Failed to retrieve joint handles. Check object type and scene setup.")
    else:
        for handle in joint_handles:
            # Retrieve joint details
            request = f'sim.getObjectAlias({handle})'
            alias = sim.getObjectAlias(handle)
            log_api_request_response(request, alias)

            request = f'sim.getJointInterval({handle})'
            interval_data = sim.getJointInterval(handle)
            if isinstance(interval_data, bool):
                logging.error(f"Unexpected boolean response for joint interval: {interval_data}")
            log_api_request_response(request, interval_data)

            request = f'sim.getJointType({handle})'
            joint_type = sim.getJointType(handle)
            if isinstance(joint_type, bool):
                logging.error(f"Unexpected boolean response for joint type: {joint_type}")
            log_api_request_response(request, joint_type)

            request = f'sim.getObjectPosition({handle}, -1)'
            position = sim.getObjectPosition(handle, -1)
            log_api_request_response(request, position)

            request = f'sim.getObjectOrientation({handle}, -1)'
            orientation = sim.getObjectOrientation(handle, -1)
            log_api_request_response(request, orientation)

    # Retrieve all objects in the scene
    request = 'sim.getObjectsInTree(sim.handle_scene)'
    scene_objects = sim.getObjectsInTree(sim.handle_scene)
    log_api_request_response(request, scene_objects)

    for obj_handle in scene_objects:
        request = f'sim.getObjectAlias({obj_handle})'
        obj_alias = sim.getObjectAlias(obj_handle)
        log_api_request_response(request, obj_alias)

        request = f'sim.getObjectType({obj_handle})'
        obj_type = sim.getObjectType(obj_handle)
        log_api_request_response(request, obj_type)

        request = f'sim.getObjectPosition({obj_handle}, -1)'
        obj_position = sim.getObjectPosition(obj_handle, -1)
        log_api_request_response(request, obj_position)

        request = f'sim.getObjectOrientation({obj_handle}, -1)'
        obj_orientation = sim.getObjectOrientation(obj_handle, -1)
        log_api_request_response(request, obj_orientation)

except Exception as e:
    logging.error(f"Error: {str(e)}") 