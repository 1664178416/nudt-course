"""
LangChain Tools for UAV Control
Wraps the UAV API client as LangChain tools using @tool decorator
All tools accept JSON string input for consistent parameter handling
"""
from langchain.tools import tool
from uav_api_client_new import UAVAPIClient
import json
import math
import logging

# Set up logger for search operations
logger = logging.getLogger(__name__)


def create_uav_tools(client: UAVAPIClient, environment_memory: dict = None, search_verbose: bool = False) -> list:
    """
    Create all UAV control tools for LangChain agent using @tool decorator
    All tools that require parameters accept a JSON string input
    
    Args:
        client: UAV API client instance
        environment_memory: Shared environment memory dictionary for storing discovered obstacles/targets
        search_verbose: Enable detailed search logging (default: True). Set to False to disable detailed step-by-step logs.
    """

    # ========== Information Gathering Tools (No Parameters) ==========

    @tool
    def list_drones() -> str:
        """List all available drones in the current session with their status, battery level, and position.
        Use this to see what drones are available before trying to control them.

        No input required."""
        try:
            drones = client.list_drones()
            return json.dumps(drones, indent=2)
        except Exception as e:
            return f"Error listing drones: {str(e)}"

    @tool
    def get_session_info() -> str:
        """Get current session information including task type, statistics, and status.
        Use this to understand what mission you need to complete.

        No input required."""
        try:
            session = client.get_current_session()
            return json.dumps(session, indent=2)
        except Exception as e:
            return f"Error getting session info: {str(e)}"

    @tool
    def get_task_progress() -> str:
        """Get mission task progress including completion percentage and status.
        Use this to track mission completion and see how close you are to finishing.

        No input required."""
        try:
            progress = client.get_task_progress()
            return json.dumps(progress, indent=2)
        except Exception as e:
            return f"Error getting task progress: {str(e)}"

    @tool
    def get_weather() -> str:
        """Get current weather conditions including wind speed, visibility, and weather type.
        Check this before takeoff to ensure safe flying conditions.

        No input required."""
        try:
            weather = client.get_weather()
            return json.dumps(weather, indent=2)
        except Exception as e:
            return f"Error getting weather: {str(e)}"

    @tool
    def find_target_by_name(input_json: str) -> str:
        """Find a target by name within a drone's nearby entities.

        Input should be a JSON string with:
        - name: Target name (required)
        - drone_id: The ID of the drone to scan nearby entities (required)

        Example: {"name": "Fixed Target 4", "drone_id": "drone-001"}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            name = params.get('name')
            drone_id = params.get('drone_id')
            if not name:
                return "Error: name is required"
            if not drone_id:
                return "Error: drone_id is required"

            nearby = client.get_nearby_entities(drone_id)
            targets = nearby.get('targets', []) if isinstance(nearby, dict) else []
            for tgt in targets:
                if str(tgt.get('name', '')).lower() == str(name).lower():
                    return json.dumps(tgt, indent=2)

            return f"Error: target not found: {name}"
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"name\": \"Fixed Target 4\", \"drone_id\": \"drone-001\"}}"
        except Exception as e:
            return f"Error finding target: {str(e)}"


    @tool
    def get_drone_status(input_json: str) -> str:
        """Get detailed status of a specific drone including position, battery, heading, and visited targets.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)

        Example: {{"drone_id": "drone-001"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')

            if not drone_id:
                return "Error: drone_id is required"

            status = client.get_drone_status(drone_id)
            return json.dumps(status, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\"}}"
        except Exception as e:
            return f"Error getting drone status: {str(e)}"

    @tool
    def get_nearby_entities(input_json: str) -> str:
        """Get drones, targets, and obstacles near a specific drone (within its perception radius).

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)

        Example: {{"drone_id": "drone-001"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')

            if not drone_id:
                return "Error: drone_id is required"

            nearby = client.get_nearby_entities(drone_id)
            return json.dumps(nearby, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\"}}"
        except Exception as e:
            return f"Error getting nearby entities: {str(e)}"

    @tool
    def land(input_json: str) -> str:
        """Command a drone to land at its current position.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)

        Example: {{"drone_id": "drone-001"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')

            if not drone_id:
                return "Error: drone_id is required"

            result = client.land(drone_id)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\"}}"
        except Exception as e:
            return f"Error during landing: {str(e)}"

    @tool
    def hover(input_json: str) -> str:
        """Command a drone to hover at its current position.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)
        - duration: Optional duration in seconds to hover (optional)

        Example: {{"drone_id": "drone-001", "duration": 5.0}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            duration = params.get('duration')

            if not drone_id:
                return "Error: drone_id is required"

            result = client.hover(drone_id, duration)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\"}}"
        except Exception as e:
            return f"Error hovering: {str(e)}"

    @tool
    def return_home(input_json: str) -> str:
        """Command a drone to return to its home position.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)

        Example: {{"drone_id": "drone-001"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')

            if not drone_id:
                return "Error: drone_id is required"

            result = client.return_home(drone_id)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\"}}"
        except Exception as e:
            return f"Error returning home: {str(e)}"

    @tool
    def set_home(input_json: str) -> str:
        """Set the drone's current position as its new home position.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)

        Example: {{"drone_id": "drone-001"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')

            if not drone_id:
                return "Error: drone_id is required"

            result = client.set_home(drone_id)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\"}}"
        except Exception as e:
            return f"Error setting home: {str(e)}"

    @tool
    def calibrate(input_json: str) -> str:
        """Calibrate the drone's sensors.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)

        Example: {{"drone_id": "drone-001"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')

            if not drone_id:
                return "Error: drone_id is required"

            result = client.calibrate(drone_id)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\"}}"
        except Exception as e:
            return f"Error calibrating: {str(e)}"

    @tool
    def take_photo(input_json: str) -> str:
        """Command a drone to take a photo.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)

        Example: {{"drone_id": "drone-001"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')

            if not drone_id:
                return "Error: drone_id is required"

            result = client.take_photo(drone_id)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\"}}"
        except Exception as e:
            return f"Error taking photo: {str(e)}"

    # ========== Two Parameter Tools ==========

    @tool
    def take_off(input_json: str) -> str:
        """Command a drone to take off to a specified altitude.
        Drone must be on ground (idle or ready status).

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)
        - altitude: Target altitude in meters (optional, default: 10.0)

        Example: {{"drone_id": "drone-001", "altitude": 15.0}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            altitude = params.get('altitude', 10.0)

            if not drone_id:
                return "Error: drone_id is required"

            result = client.take_off(drone_id, altitude)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\", \"altitude\": 15.0}}"
        except Exception as e:
            return f"Error during takeoff: {str(e)}"

    @tool
    def change_altitude(input_json: str) -> str:
        """Change a drone's altitude while maintaining X/Y position.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)
        - altitude: Target altitude in meters (required)

        Example: {{"drone_id": "drone-001", "altitude": 20.0}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            altitude = params.get('altitude')

            if not drone_id:
                return "Error: drone_id is required"
            if altitude is None:
                return "Error: altitude is required"

            result = client.change_altitude(drone_id, altitude)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\", \"altitude\": 20.0}}"
        except Exception as e:
            return f"Error changing altitude: {str(e)}"

    @tool
    def rotate(input_json: str) -> str:
        """Rotate a drone to face a specific direction.
        0=North, 90=East, 180=South, 270=West.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)
        - heading: Target heading in degrees 0-360 (required)

        Example: {{"drone_id": "drone-001", "heading": 90.0}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            heading = params.get('heading')

            if not drone_id:
                return "Error: drone_id is required"
            if heading is None:
                return "Error: heading is required"

            result = client.rotate(drone_id, heading)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\", \"heading\": 90.0}}"
        except Exception as e:
            return f"Error rotating: {str(e)}"

    @tool
    def send_message(input_json: str) -> str:
        """Send a message from one drone to another.

        Input should be a JSON string with:
        - drone_id: The ID of the sender drone (required)
        - target_drone_id: The ID of the recipient drone (required)
        - message: The message content (required)

        Example: {{"drone_id": "drone-001", "target_drone_id": "drone-002", "message": "Hello"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            target_drone_id = params.get('target_drone_id')
            message = params.get('message')

            if not drone_id:
                return "Error: drone_id is required"
            if not target_drone_id:
                return "Error: target_drone_id is required"
            if not message:
                return "Error: message is required"

            result = client.send_message(drone_id, target_drone_id, message)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\", \"target_drone_id\": \"drone-002\", \"message\": \"...\"}}"
        except Exception as e:
            return f"Error sending message: {str(e)}"

    @tool
    def broadcast(input_json: str) -> str:
        """Broadcast a message from one drone to all other drones.

        Input should be a JSON string with:
        - drone_id: The ID of the sender drone (required)
        - message: The message content (required)

        Example: {{"drone_id": "drone-001", "message": "Alert"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            message = params.get('message')

            if not drone_id:
                return "Error: drone_id is required"
            if not message:
                return "Error: message is required"

            result = client.broadcast(drone_id, message)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\", \"message\": \"...\"}}"
        except Exception as e:
            return f"Error broadcasting: {str(e)}"

    @tool
    def charge(input_json: str) -> str:
        """Command a drone to charge its battery.
        Drone must be landed at a charging station.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)
        - charge_amount: Amount to charge in percent (required)

        Example: {{"drone_id": "drone-001", "charge_amount": 25.0}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            charge_amount = params.get('charge_amount')

            if not drone_id:
                return "Error: drone_id is required"
            if charge_amount is None:
                return "Error: charge_amount is required"

            result = client.charge(drone_id, charge_amount)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\", \"charge_amount\": 25.0}}"
        except Exception as e:
            return f"Error charging: {str(e)}"

    @tool
    def move_towards(input_json: str) -> str:
        """Move a drone a specific distance in a direction (relative movement).
        
        WHEN TO USE (VERY LIMITED):
        - ONLY for obstacle detours when move_to is blocked (use 1-2 times max, then switch to move_to)
        - Small adjustments (<50m) when exact coordinates are unknown
        - DO NOT use for waypoint navigation - always use move_to for waypoints
        
        WHEN NOT TO USE:
        - DO NOT use for waypoint navigation - ALWAYS use move_to for waypoints
        - DO NOT use for movement to specific coordinates - use move_to instead
        - DO NOT use repeatedly - after 1-2 uses, MUST switch to move_to
        
        CRITICAL: For waypoint navigation tasks, NEVER use move_towards. Always use move_to.

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)
        - distance: Distance to move in meters (required)
        - heading: Heading direction in degrees 0-360 (optional, default: current heading)
        - dz: Vertical component in meters (optional)

        Example: {{"drone_id": "drone-001", "distance": 10.0, "heading": 90.0}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            distance = params.get('distance')
            heading = params.get('heading')
            dz = params.get('dz')

            if not drone_id:
                return "Error: drone_id is required"
            if distance is None:
                return "Error: distance is required"

            result = client.move_towards(drone_id, distance, heading, dz)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\", \"distance\": 10.0}}"
        except Exception as e:
            return f"Error moving towards: {str(e)}"

    # @tool
    # def move_along_path(input_json: str) -> str:
    #     """Move a drone along a path of waypoints.

    #     Input should be a JSON string with:
    #     - drone_id: The ID of the drone (required)
    #     - waypoints: List of points with x, y, z coordinates (required)

    #     Example: {{"drone_id": "drone-001", "waypoints": [{{"x": 10, "y": 10, "z": 10}}, {{"x": 20, "y": 20, "z": 10}}]}}
    #     """
    #     try:
    #         params = json.loads(input_json) if isinstance(input_json, str) else input_json
    #         drone_id = params.get('drone_id')
    #         waypoints = params.get('waypoints')

    #         if not drone_id:
    #             return "Error: drone_id is required"
    #         if not waypoints:
    #             return "Error: waypoints list is required"

    #         result = client.move_along_path(drone_id, waypoints)
    #         return json.dumps(result, indent=2)
    #     except json.JSONDecodeError as e:
    #         return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\", \"waypoints\": [...]}}"
    #     except Exception as e:
    #         return f"Error moving along path: {str(e)}"

    # ========== Multi-Parameter Tools ==========

    @tool
    def move_to(input_json: str) -> str:
        """Move a drone directly to specific 3D coordinates (x, y, z).
        
        NOTE: safe_move_to is now the RECOMMENDED tool - it automatically handles obstacles.
        Use move_to only if you are CERTAIN the path is clear and want maximum speed.
        
        WHEN TO USE:
        - Only if you are 100% certain the path is clear (no obstacles)
        - For very short movements (<10m) where obstacles are unlikely
        - When safe_move_to is not available (fallback)
        
        WHEN NOT TO USE:
        - If path might have obstacles - use safe_move_to instead (it's smarter)
        - For waypoint navigation - prefer safe_move_to for automatic obstacle avoidance
        - Do NOT use move_towards for waypoints - use safe_move_to or move_to

        Input should be a JSON string with:
        - drone_id: The ID of the drone (required)
        - x: Target X coordinate in meters (required)
        - y: Target Y coordinate in meters (required)
        - z: Target Z coordinate (altitude) in meters (required)

        Example: {{"drone_id": "drone-001", "x": 100.0, "y": 50.0, "z": 20.0}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            x = params.get('x')
            y = params.get('y')
            z = params.get('z')

            if not drone_id:
                return "Error: drone_id is required"
            if x is None or y is None or z is None:
                return "Error: x, y, and z coordinates are required"

            result = client.move_to(drone_id, x, y, z)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id\": \"drone-001\", \"x\": 100.0, \"y\": 50.0, \"z\": 20.0}}"
        except Exception as e:
            return f"Error moving drone: {str(e)}"

    @tool
    def check_path_collision(input_json: str) -> str:
        """Check whether a path between two points collides with obstacles.

        Input should be a JSON string with:
        - start_x: Start X coordinate (required)
        - start_y: Start Y coordinate (required)
        - start_z: Start Z coordinate (required)
        - end_x: End X coordinate (required)
        - end_y: End Y coordinate (required)
        - end_z: End Z coordinate (required)
        - safety_margin: Optional safety margin (default 0.0)

        Example: {"start_x":0,"start_y":0,"start_z":0,"end_x":100,"end_y":50,"end_z":20,"safety_margin":1.0}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            start_x = params.get('start_x')
            start_y = params.get('start_y')
            start_z = params.get('start_z')
            end_x = params.get('end_x')
            end_y = params.get('end_y')
            end_z = params.get('end_z')
            safety_margin = params.get('safety_margin', 0.0)

            if None in (start_x, start_y, start_z, end_x, end_y, end_z):
                return "Error: start_x, start_y, start_z, end_x, end_y, end_z are required"

            result = client.check_path_collision(start_x, start_y, start_z, end_x, end_y, end_z, safety_margin)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"start_x\":0,\"start_y\":0,\"start_z\":0,\"end_x\":100,\"end_y\":50,\"end_z\":20}}"
        except Exception as e:
            return f"Error checking path collision: {str(e)}"


    @tool
    def check_two_drones_distance(input_json: str) -> str:
        """Calculate the distance between two drones and verify if they maintain required formation distance.

        Input should be a JSON string with:
        - drone_id_1: ID of first drone (required)
        - drone_id_2: ID of second drone (required)
        - max_distance: Maximum acceptable distance in meters (optional, default: 100.0)

        Example: {{"drone_id_1": "drone-001", "drone_id_2": "drone-002", "max_distance": 50.0}}

        This tool gets the actual positions of both drones and calculates the Euclidean distance between them.
        Use this to verify formation control success.
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id_1 = params.get('drone_id_1')
            drone_id_2 = params.get('drone_id_2')
            max_distance = params.get('max_distance', 100.0)

            if not drone_id_1:
                return "Error: drone_id_1 is required"
            if not drone_id_2:
                return "Error: drone_id_2 is required"

            # Get positions of both drones
            status_1 = client.get_drone_status(drone_id_1)
            status_2 = client.get_drone_status(drone_id_2)
            
            if not status_1 or not status_2:
                return f"Error: Could not get status for one or both drones"
            
            # Extract positions
            pos_1 = status_1.get('position', {})
            pos_2 = status_2.get('position', {})
            
            x1, y1, z1 = pos_1.get('x', 0), pos_1.get('y', 0), pos_1.get('z', 0)
            x2, y2, z2 = pos_2.get('x', 0), pos_2.get('y', 0), pos_2.get('z', 0)
            
            # Calculate Euclidean distance
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
            within_range = distance <= max_distance
            status = "✓ PASS" if within_range else "✗ FAIL"
            
            return json.dumps({
                'status': status,
                'distance': round(distance, 2),
                'drone_1_id': drone_id_1,
                'drone_1_position': {'x': x1, 'y': y1, 'z': z1},
                'drone_2_id': drone_id_2,
                'drone_2_position': {'x': x2, 'y': y2, 'z': z2},
                'max_distance': max_distance,
                'within_range': within_range
            }, indent=2)
                
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_id_1\": \"drone-001\", \"drone_id_2\": \"drone-002\", \"max_distance\": 50.0}}"
        except Exception as e:
            return f"Error checking distance: {str(e)}"

    @tool
    def verify_formation(input_json: str) -> str:
        """Verify if a group of drones maintain a specified formation pattern by checking all pairwise distances.

        Input should be a JSON string with:
        - drone_ids: List of drone IDs (required, minimum 2)
        - formation_type: Type of formation - "line", "circle" (required)

        Example: {{"drone_ids": ["drone-001", "drone-002", "drone-003"], "formation_type": "line"}}

        This tool checks distances between consecutive drones for linear formation.
        Returns whether the drones successfully maintain the specified formation.
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_ids = params.get('drone_ids', [])
            formation_type = params.get('formation_type', 'line')

            if not drone_ids:
                return "Error: drone_ids list is required"
            if len(drone_ids) < 2:
                return "Error: At least 2 drones are required for formation control"
            if not formation_type:
                return "Error: formation_type is required"

            # Get all drone positions
            positions = {}
            for drone_id in drone_ids:
                try:
                    status = client.get_drone_status(drone_id)
                    pos = status.get('position', {})
                    positions[drone_id] = {
                        'x': pos.get('x', 0),
                        'y': pos.get('y', 0),
                        'z': pos.get('z', 0)
                    }
                except:
                    return f"Error: Could not get position for drone {drone_id}"
            
            # Calculate distances between consecutive drones
            distances = []
            for i in range(len(drone_ids) - 1):
                d1, d2 = drone_ids[i], drone_ids[i+1]
                p1, p2 = positions[d1], positions[d2]
                dist = math.sqrt((p2['x']-p1['x'])**2 + (p2['y']-p1['y'])**2 + (p2['z']-p1['z'])**2)
                distances.append({
                    'pair': f"{d1} to {d2}",
                    'distance': round(dist, 2)
                })
            
            # Check if formation is valid (all distances within 5m tolerance)
            valid = all(abs(d['distance'] - distances[0]['distance']) <= 5.0 for d in distances) if distances else False
            status = "✓ PASS" if valid else "✗ FAIL"
            
            return json.dumps({
                'status': status,
                'formation_type': formation_type,
                'num_drones': len(drone_ids),
                'drone_ids': drone_ids,
                'valid': valid,
                'pairwise_distances': distances
            }, indent=2)
                
        except json.JSONDecodeError as e:
            return f"Error parsing JSON input: {str(e)}. Expected format: {{\"drone_ids\": [\"drone-001\", \"drone-002\"], \"formation_type\": \"line\"}}"
        except Exception as e:
            return f"Error verifying formation: {str(e)}"

    @tool
    def search_target(input_json: str) -> str:
        """Intelligently search for a target using multiple strategies with automatic drone selection.
        
        THIS IS THE PRIMARY SEARCH TOOL - Use this for all target searches.
        It automatically:
        1. Selects best drone (prefers non-task drones to save battery)
        2. Uses get_nearby_entities with perceived_radius for efficient scanning
        3. Tries multiple search strategies: directional → spiral → grid
        4. Automatically records found targets to environment memory
        
        WHEN TO USE:
        - When target name is known but location is unknown
        - After estimate_target_location finds no hints
        - For comprehensive area search tasks
        
        Input JSON:
        - target_name: Target name to search for (required)
        - task_drone_id: ID of drone executing main task (optional, used to select other drones for search)
        - search_strategy: "directional", "spiral", "grid", or "auto" (default: "auto" tries all)
        - start_position: {"x": x, "y": y, "z": z} - starting position for search (optional, defaults to drone position)
        - max_search_area: Maximum area to search in meters (default: auto from map size)
        
        Returns: Target found with position, or search completed without finding target.
        
        Note: Detailed logging is controlled by the verbose parameter when creating tools, not in the JSON input.
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            target_name = params.get('target_name')
            task_drone_id = params.get('task_drone_id')
            search_strategy = params.get('search_strategy', 'auto')
            start_pos = params.get('start_position')
            max_search_area = params.get('max_search_area')
            # verbose is now a closure variable from create_uav_tools, not from JSON input
            
            if not target_name:
                return "Error: target_name is required"
            
            # Get map bounds and session info
            try:
                session = client.get_current_session()
                canvas_width = session.get('canvas_width', 1024)
                canvas_height = session.get('canvas_height', 768)
            except:
                canvas_width = 1024
                canvas_height = 768
            
            # Create conditional logger functions based on search_verbose setting
            def log_info(msg):
                if search_verbose:
                    logger.info(msg)
            
            def log_debug(msg):
                if search_verbose:
                    logger.debug(msg)
            
            def log_warning(msg):
                if search_verbose:
                    logger.warning(msg)
            
            def log_error(msg):
                # Always log errors, even if search_verbose is False
                logger.error(msg)
            
            # Step 1: Select best drone for search (prefer non-task drones)
            log_info(f"[SEARCH] ===== Starting search for target: '{target_name}' =====")
            log_info(f"[SEARCH] Task drone ID: {task_drone_id}, Verbose logging: {search_verbose}")
            search_drone_id = None
            search_drone = None
            
            try:
                drones = client.list_drones()
                log_info(f"[SEARCH] Available drones: {len(drones)}")
                # Prefer non-task drones (idle/landed) to save battery
                non_task_drones = [d for d in drones if d.get('id') != task_drone_id and 
                                  d.get('status') in ['idle', 'landed', 'hovering']]
                
                if non_task_drones:
                    # Select drone with highest battery and good perception radius
                    search_drone = max(non_task_drones, 
                                      key=lambda d: (d.get('battery_level', 0), d.get('perceived_radius', 0)))
                    search_drone_id = search_drone.get('id')
                    log_info(f"[SEARCH] Selected non-task drone: {search_drone.get('name')} (ID: {search_drone_id}), battery={search_drone.get('battery_level', 0):.1f}%, radius={search_drone.get('perceived_radius', 0):.1f}m")
                else:
                    # Fallback to task drone if no other drones available
                    if task_drone_id:
                        for d in drones:
                            if d.get('id') == task_drone_id:
                                search_drone = d
                                search_drone_id = task_drone_id
                                log_info(f"[SEARCH] Using task drone: {search_drone.get('name')} (ID: {search_drone_id}), battery={search_drone.get('battery_level', 0):.1f}%")
                                break
                    # If still no drone, use first available
                    if not search_drone_id and drones:
                        search_drone = drones[0]
                        search_drone_id = search_drone.get('id')
                        log_info(f"[SEARCH] Using first available drone: {search_drone.get('name')} (ID: {search_drone_id})")
            except Exception as e:
                log_error(f"[SEARCH] ERROR: Could not list drones: {str(e)}")
                return "Error: Could not list drones"
            
            if not search_drone_id:
                log_error("[SEARCH] ERROR: No available drones for search")
                return "Error: No available drones for search"
            
            # Get drone's perceived radius for optimal scan spacing
            perceived_radius = search_drone.get('perceived_radius', 100)
            # CRITICAL: Use VERY SMALL scan interval (30% of radius) to ensure NO targets are missed
            # Smaller interval = more thorough coverage, especially for small targets
            # For 100m radius, use 30m interval = 70% overlap to ensure complete coverage
            # This ensures even small targets at map edges are not missed
            scan_interval = perceived_radius * 0.3  # 30% = 30m for 100m radius, ensures 70% overlap
            log_info(f"[SEARCH] Search parameters: perceived_radius={perceived_radius:.1f}m, scan_interval={scan_interval:.1f}m, map_size=({canvas_width:.1f}, {canvas_height:.1f})")
            
            # Step 2: Prepare search drone (take off if needed)
            try:
                status = client.get_drone_status(search_drone_id)
                current_pos = status.get('position', {})
                curr_x = current_pos.get('x', 0)
                curr_y = current_pos.get('y', 0)
                curr_z = current_pos.get('z', 0)
                drone_status = status.get('status', 'idle')
                
                # Use provided start position, or default to map center for better coverage
                if start_pos:
                    start_x = start_pos.get('x', curr_x)
                    start_y = start_pos.get('y', curr_y)
                    start_z = start_pos.get('z', curr_z)
                else:
                    # Default to map center for systematic full-map search
                    start_x = canvas_width / 2
                    start_y = canvas_height / 2
                    # CRITICAL: Use MINIMUM altitude (2m) to detect ground targets (z=0)
                    # Most targets are on ground, so we need to be VERY close to ground level
                    start_z = 2.0  # Minimum safe altitude for better ground target detection
                
                # Take off if needed (to VERY LOW altitude for ground target detection)
                if drone_status == 'idle' or drone_status == 'landed':
                    # CRITICAL: Use MINIMUM altitude (2m) to detect ground targets (z=0)
                    # Ground targets are at z=0, so we need to be VERY close to ground level
                    # Lower altitude = better detection range for ground targets
                    search_altitude = 2.0  # Minimum safe altitude for ground target detection
                    try:
                        client.take_off(search_drone_id, search_altitude)
                        start_z = search_altitude
                    except:
                        pass
                elif drone_status == 'hovering' and curr_z > 5:
                    # If already hovering but too high, lower altitude for better detection
                    try:
                        client.change_altitude(search_drone_id, 2.0)
                        start_z = 2.0
                    except:
                        pass
                
                # Move to start position if different from current
                if abs(start_x - curr_x) > 1 or abs(start_y - curr_y) > 1 or abs(start_z - curr_z) > 1:
                    try:
                        client.move_to(search_drone_id, start_x, start_y, start_z)
                    except:
                        pass
            except Exception as e:
                return f"Error preparing search drone: {str(e)}"
            
            # Step 3: Quick scan - check all drones' nearby entities first (fastest method)
            # NOTE: get_targets() and get_obstacles() APIs are DISABLED - only use get_nearby_entities()
            log_info(f"[SEARCH] Step 3: Quick scan - checking all drones' nearby entities")
            try:
                drones = client.list_drones()
                log_info(f"[SEARCH] Checking {len(drones)} drones for nearby targets")
                for drone in drones:
                    drone_id = drone.get('id')
                    if drone_id:
                        try:
                            nearby = client.get_nearby_entities(drone_id)
                            targets = nearby.get('targets', [])
                            obstacles = nearby.get('obstacles', [])
                            
                            # Record obstacles to memory
                            if environment_memory and obstacles:
                                try:
                                    record_params = json.dumps({'obstacles': obstacles})
                                    record_environment_discovery(record_params)
                                except:
                                    pass
                            
                            for target in targets:
                                if target.get('name', '').lower() == target_name.lower():
                                    # Record to environment memory
                                    if environment_memory:
                                        try:
                                            record_params = json.dumps({'targets': [target], 'obstacles': obstacles})
                                            record_environment_discovery(record_params)
                                        except:
                                            pass
                                    
                                    return json.dumps({
                                        'found': True,
                                        'target': target,
                                        'drone_used': search_drone.get('name'),
                                        'found_by_drone': drone.get('name'),
                                        'strategy': 'quick_scan_all_drones',
                                        'message': f'Target found near {drone.get("name")}'
                                    }, ensure_ascii=False, indent=2)
                        except:
                            continue  # Skip this drone if error
            except:
                pass  # If scan fails, continue with systematic search
            
            # Third, check search drone's initial position
            log_info(f"[SEARCH] Step 4: Checking search drone's initial position")
            try:
                nearby = client.get_nearby_entities(search_drone_id)
                targets = nearby.get('targets', [])
                obstacles = nearby.get('obstacles', [])
                log_info(f"[SEARCH] Initial position scan: Found {len(targets)} targets, {len(obstacles)} obstacles")
                
                # Check if target found immediately
                for target in targets:
                    if target.get('name', '').lower() == target_name.lower():
                        log_info(f"[SEARCH] SUCCESS: Target '{target_name}' found at initial position!")
                        # Record to environment memory
                        if environment_memory:
                            try:
                                record_params = json.dumps({'targets': [target], 'obstacles': obstacles})
                                record_environment_discovery(record_params)
                            except:
                                pass
                        
                        return json.dumps({
                            'found': True,
                            'target': target,
                            'drone_used': search_drone.get('name'),
                            'strategy': 'initial_scan',
                            'message': 'Target found at search drone initial position'
                        }, ensure_ascii=False, indent=2)
            except Exception as e:
                pass  # Continue with search if scan fails
            
            # Step 4: Define helper functions for search strategies
            # Track searched areas to avoid repetition
            searched_areas = set()
            
            def directional_search(drone_id, target_name, start_x, start_y, start_z, direction, scan_interval, max_dist, canvas_width, canvas_height):
                """Helper: Search in one direction at VERY LOW altitude for ground targets"""
                log_info(f"[SEARCH] Starting directional search: target={target_name}, direction={direction}°, start=({start_x:.1f}, {start_y:.1f}, {start_z:.1f}), max_dist={max_dist:.1f}m, scan_interval={scan_interval:.1f}m")
                distance = 0
                current_x, current_y, current_z = start_x, start_y, start_z
                # CRITICAL: Use MINIMUM altitude (2m) for ground target detection (targets at z=0)
                # get_nearby_entities works in 3D, but being VERY close to ground improves detection
                # Lower altitude = better detection range for ground targets
                search_z = 2.0
                step_count = 0
                
                while distance < max_dist:
                    # Calculate next position
                    rad = math.radians(direction)
                    next_x = start_x + (distance + scan_interval) * math.sin(rad)
                    next_y = start_y + (distance + scan_interval) * math.cos(rad)
                    
                    # Check bounds - CRITICAL: Search up to AND INCLUDING boundaries
                    # Targets can be exactly at map edges (x=0, x=canvas_width, y=0, y=canvas_height)
                    # If outside bounds, clamp to boundary and check if we've reached the limit
                    reached_boundary = False
                    if next_x < 0:
                        next_x = 0
                        reached_boundary = True
                    elif next_x > canvas_width:
                        next_x = canvas_width
                        reached_boundary = True
                    
                    if next_y < 0:
                        next_y = 0
                        reached_boundary = True
                    elif next_y > canvas_height:
                        next_y = canvas_height
                        reached_boundary = True
                    
                    # If we've reached a boundary and already searched there, stop this direction
                    if reached_boundary:
                        area_key = (int(next_x // 50), int(next_y // 50))
                        if area_key in searched_areas:
                            log_info(f"[SEARCH] Reached boundary ({next_x:.1f}, {next_y:.1f}) already searched, stopping this direction")
                            break
                    
                    # Check if already searched this area (avoid repetition)
                    # Use smaller grid cells (25m) for better granularity to avoid missing targets
                    area_key = (int(next_x // 25), int(next_y // 25))  # 25m grid cells for finer tracking
                    if area_key in searched_areas:
                        log_debug(f"[SEARCH] Step {step_count}: Skipping already searched area ({next_x:.1f}, {next_y:.1f})")
                        distance += scan_interval
                        continue
                    searched_areas.add(area_key)
                    step_count += 1
                    
                    # Move using client.move_to directly (can't call tool functions from within tools)
                    log_info(f"[SEARCH] Step {step_count}: Moving to ({next_x:.1f}, {next_y:.1f}, {search_z:.1f}) - distance={distance:.1f}m")
                    try:
                        move_result = client.move_to(drone_id, next_x, next_y, search_z)
                        if isinstance(move_result, dict) and move_result.get('status') == 'success':
                            current_x, current_y = next_x, next_y
                            distance += scan_interval
                            log_info(f"[SEARCH] Step {step_count}: Moved successfully to ({current_x:.1f}, {current_y:.1f})")
                        else:
                            # If blocked, try to go around but continue searching
                            log_warning(f"[SEARCH] Step {step_count}: Movement blocked at ({next_x:.1f}, {next_y:.1f}), continuing search")
                            distance += scan_interval
                            continue
                    except Exception as e:
                        log_error(f"[SEARCH] Step {step_count}: Movement error at ({next_x:.1f}, {next_y:.1f}): {str(e)}")
                        distance += scan_interval
                        continue
                    
                    # Scan for target using get_nearby_entities
                    try:
                        log_info(f"[SEARCH] Step {step_count}: Scanning for targets at ({current_x:.1f}, {current_y:.1f}, {search_z:.1f})")
                        nearby = client.get_nearby_entities(drone_id)
                        targets = nearby.get('targets', [])
                        obstacles = nearby.get('obstacles', [])
                        log_info(f"[SEARCH] Step {step_count}: Found {len(targets)} targets, {len(obstacles)} obstacles nearby")
                        
                        # Log all found targets
                        for tgt in targets:
                            tgt_name = tgt.get('name', 'unknown')
                            tgt_pos = tgt.get('position', {})
                            log_info(f"[SEARCH] Step {step_count}: Found target '{tgt_name}' at ({tgt_pos.get('x', 0):.1f}, {tgt_pos.get('y', 0):.1f}, {tgt_pos.get('z', 0):.1f})")
                        
                        # Record obstacles to memory
                        if environment_memory and obstacles:
                            try:
                                record_params = json.dumps({'obstacles': obstacles})
                                record_environment_discovery(record_params)
                            except:
                                pass
                        for target in targets:
                            if target.get('name', '').lower() == target_name.lower():
                                log_info(f"[SEARCH] SUCCESS: Found target '{target_name}' at step {step_count}, distance={distance:.1f}m")
                                return {'found': True, 'target': target, 'distance': distance}
                    except Exception as e:
                        logger.error(f"[SEARCH] Step {step_count}: Error scanning for targets: {str(e)}")
                        pass
                
                log_info(f"[SEARCH] Directional search completed: {step_count} steps, {distance:.1f}m traveled, target not found")
                return {'found': False, 'distance': distance, 'steps': step_count}
            
            def spiral_search(drone_id, target_name, start_x, start_y, start_z, scan_interval, canvas_width, canvas_height, perceived_radius):
                """Helper: Square spiral search - covers FULL map at LOW altitude"""
                log_info(f"[SEARCH] Starting spiral search: target={target_name}, start=({start_x:.1f}, {start_y:.1f}, {start_z:.1f}), scan_interval={scan_interval:.1f}m")
                headings = [90, 0, 270, 180]  # E, N, W, S
                leg_lengths = []
                k = 1
                # Calculate enough legs to cover entire map (diagonal distance)
                map_diagonal = (canvas_width**2 + canvas_height**2)**0.5
                max_legs = int(map_diagonal / scan_interval) + 12  # Ensure full coverage with extra legs
                log_info(f"[SEARCH] Spiral search: map_diagonal={map_diagonal:.1f}m, max_legs={max_legs}")
                
                while len(leg_lengths) < max_legs:
                    leg_lengths.append(scan_interval * k)
                    if len(leg_lengths) < max_legs:
                        leg_lengths.append(scan_interval * k)
                    k += 1
                
                current_x, current_y, current_z = start_x, start_y, start_z
                total_distance = 0
                # CRITICAL: Use MINIMUM altitude (2m) for ground target detection (targets at z=0)
                search_z = 2.0
                step_count = 0
                
                for i, leg_len in enumerate(leg_lengths):
                    heading = headings[i % 4]
                    rad = math.radians(heading)
                    next_x = current_x + leg_len * math.sin(rad)
                    next_y = current_y + leg_len * math.cos(rad)
                    
                    # Allow searching up to map boundaries (targets can be at edges: x=0, x=canvas_width, y=0, y=canvas_height)
                    # Use small margin (-5 to +5) to allow searching near boundaries
                    if next_x < -5 or next_x > canvas_width + 5 or next_y < -5 or next_y > canvas_height + 5:
                        # If outside map, try to continue from a valid position
                        # Clamp to map boundaries and continue
                        next_x = max(0, min(canvas_width, next_x))
                        next_y = max(0, min(canvas_height, next_y))
                        # If still outside after clamping, skip this leg
                        if next_x < 0 or next_x > canvas_width or next_y < 0 or next_y > canvas_height:
                            continue
                    
                    # Check if already searched this area
                    # Use smaller grid cells (25m) for better granularity
                    area_key = (int(next_x // 25), int(next_y // 25))  # 25m grid cells
                    if area_key in searched_areas:
                        logger.debug(f"[SEARCH] Spiral step {i+1}: Skipping already searched area ({next_x:.1f}, {next_y:.1f})")
                        total_distance += leg_len
                        continue
                    searched_areas.add(area_key)
                    step_count += 1
                    
                    # Move using client.move_to directly (can't call tool functions from within tools)
                    log_info(f"[SEARCH] Spiral step {i+1} (leg {step_count}): Moving {leg_len:.1f}m at {heading}° to ({next_x:.1f}, {next_y:.1f}, {search_z:.1f})")
                    try:
                        move_result = client.move_to(drone_id, next_x, next_y, search_z)
                        if isinstance(move_result, dict) and move_result.get('status') == 'success':
                            current_x, current_y = next_x, next_y
                            total_distance += leg_len
                            log_info(f"[SEARCH] Spiral step {i+1}: Moved successfully to ({current_x:.1f}, {current_y:.1f}), total_distance={total_distance:.1f}m")
                        else:
                            # If blocked, continue searching
                            log_warning(f"[SEARCH] Spiral step {i+1}: Movement blocked, continuing")
                            total_distance += leg_len
                            continue
                    except Exception as e:
                        log_error(f"[SEARCH] Spiral step {i+1}: Movement error: {str(e)}")
                        total_distance += leg_len
                        continue
                    
                    # Scan for target using get_nearby_entities
                    try:
                        log_info(f"[SEARCH] Spiral step {i+1}: Scanning for targets at ({current_x:.1f}, {current_y:.1f}, {search_z:.1f})")
                        nearby = client.get_nearby_entities(drone_id)
                        targets = nearby.get('targets', [])
                        obstacles = nearby.get('obstacles', [])
                        log_info(f"[SEARCH] Spiral step {i+1}: Found {len(targets)} targets, {len(obstacles)} obstacles nearby")
                        
                        # Log all found targets
                        for tgt in targets:
                            tgt_name = tgt.get('name', 'unknown')
                            tgt_pos = tgt.get('position', {})
                            log_info(f"[SEARCH] Spiral step {i+1}: Found target '{tgt_name}' at ({tgt_pos.get('x', 0):.1f}, {tgt_pos.get('y', 0):.1f}, {tgt_pos.get('z', 0):.1f})")
                        
                        # Record obstacles to memory
                        if environment_memory and obstacles:
                            try:
                                record_params = json.dumps({'obstacles': obstacles})
                                record_environment_discovery(record_params)
                            except:
                                pass
                        for target in targets:
                            if target.get('name', '').lower() == target_name.lower():
                                logger.info(f"[SEARCH] SUCCESS: Found target '{target_name}' at spiral step {i+1}, total_distance={total_distance:.1f}m")
                                return {'found': True, 'target': target, 'distance': total_distance}
                    except Exception as e:
                        logger.error(f"[SEARCH] Spiral step {i+1}: Error scanning for targets: {str(e)}")
                        pass
                
                log_info(f"[SEARCH] Spiral search completed: {step_count} steps, {total_distance:.1f}m traveled, target not found")
                return {'found': False, 'distance': total_distance, 'steps': step_count}
            
            def grid_search(drone_id, target_name, start_x, start_y, start_z, scan_interval, canvas_width, canvas_height, perceived_radius):
                """Helper: Grid pattern search (serpentine) - covers FULL map at LOW altitude"""
                log_info(f"[SEARCH] Starting grid search: target={target_name}, start=({start_x:.1f}, {start_y:.1f}, {start_z:.1f}), scan_interval={scan_interval:.1f}m, map_size=({canvas_width:.1f}, {canvas_height:.1f})")
                current_x, current_y, current_z = start_x, start_y, start_z
                total_distance = 0
                # CRITICAL: Use MINIMUM altitude (2m) for ground target detection (targets at z=0)
                search_z = 2.0
                step_count = 0
                
                # Serpentine pattern covering ENTIRE map including boundaries
                # CRITICAL: Start from edge and ensure we search boundary positions (y=0, y=canvas_height, etc.)
                # Use smaller step to ensure we don't miss targets between scan points
                y_start = 0
                y_end = canvas_height
                x_start = 0
                x_end = canvas_width
                
                # CRITICAL: Ensure we search boundary positions by starting at exact boundaries
                # Also add intermediate points between scan_interval to catch targets in between
                y = y_start
                direction = 1  # 1 for east, -1 for west
                
                log_info(f"[SEARCH] Grid search: Covering area from ({x_start}, {y_start}) to ({x_end}, {y_end}) with scan_interval={scan_interval:.1f}m")
                
                # CRITICAL: Ensure we cover the entire map including edges
                # Use <= to include the boundary coordinates (targets can be at x=0, x=canvas_width, y=0, y=canvas_height)
                # Also search intermediate positions to ensure no targets are missed
                while y <= y_end:
                    # Generate x positions with scan_interval, but also include boundary positions
                    if direction == 1:
                        # East: from left edge (0) to right edge (canvas_width)
                        x_positions = list(range(int(x_start), int(x_end) + 1, int(scan_interval)))
                        # CRITICAL: Ensure we include the right boundary
                        if x_positions[-1] != int(x_end):
                            x_positions.append(int(x_end))
                    else:
                        # West: from right edge (canvas_width) to left edge (0)
                        x_positions = list(range(int(x_end), int(x_start) - 1, -int(scan_interval)))
                        # CRITICAL: Ensure we include the left boundary
                        if x_positions[-1] != int(x_start):
                            x_positions.append(int(x_start))
                    
                    for x in x_positions:
                        # CRITICAL: Include boundary coordinates (0 and canvas_width/height)
                        # Targets can be exactly at map edges, so we must search there
                        if x < 0 or x > canvas_width or y < 0 or y > canvas_height:
                            continue
                        
                        # Check if already searched this area
                        # Use smaller grid cells (25m) for better granularity
                        area_key = (int(x // 25), int(y // 25))  # 25m grid cells
                        if area_key in searched_areas:
                            logger.debug(f"[SEARCH] Grid: Skipping already searched area ({x:.1f}, {y:.1f})")
                            total_distance += scan_interval
                            continue
                        searched_areas.add(area_key)
                        step_count += 1
                        
                        # Move to grid point using client.move_to directly (can't call tool functions from within tools)
                        log_info(f"[SEARCH] Grid step {step_count}: Moving to ({x:.1f}, {y:.1f}, {search_z:.1f}) - row at y={y:.1f}, direction={'east' if direction == 1 else 'west'}")
                        try:
                            move_result = client.move_to(drone_id, float(x), float(y), search_z)
                            if isinstance(move_result, dict) and move_result.get('status') == 'success':
                                current_x, current_y = float(x), float(y)
                                total_distance += scan_interval
                                log_info(f"[SEARCH] Grid step {step_count}: Moved successfully to ({current_x:.1f}, {current_y:.1f}), total_distance={total_distance:.1f}m")
                            else:
                                # If blocked, continue searching
                                log_warning(f"[SEARCH] Grid step {step_count}: Movement blocked at ({x:.1f}, {y:.1f}), continuing")
                                total_distance += scan_interval
                                continue
                        except Exception as e:
                            log_error(f"[SEARCH] Grid step {step_count}: Movement error at ({x:.1f}, {y:.1f}): {str(e)}")
                            total_distance += scan_interval
                            continue
                        
                        # Scan for target using get_nearby_entities
                        try:
                            log_info(f"[SEARCH] Grid step {step_count}: Scanning for targets at ({current_x:.1f}, {current_y:.1f}, {search_z:.1f})")
                            nearby = client.get_nearby_entities(drone_id)
                            targets = nearby.get('targets', [])
                            obstacles = nearby.get('obstacles', [])
                            log_info(f"[SEARCH] Grid step {step_count}: Found {len(targets)} targets, {len(obstacles)} obstacles nearby")
                            
                            # Log all found targets
                            for tgt in targets:
                                tgt_name = tgt.get('name', 'unknown')
                                tgt_pos = tgt.get('position', {})
                                log_info(f"[SEARCH] Grid step {step_count}: Found target '{tgt_name}' at ({tgt_pos.get('x', 0):.1f}, {tgt_pos.get('y', 0):.1f}, {tgt_pos.get('z', 0):.1f})")
                            
                            # Record obstacles to memory
                            if environment_memory and obstacles:
                                try:
                                    record_params = json.dumps({'obstacles': obstacles})
                                    record_environment_discovery(record_params)
                                except:
                                    pass
                            for target in targets:
                                if target.get('name', '').lower() == target_name.lower():
                                    logger.info(f"[SEARCH] SUCCESS: Found target '{target_name}' at grid step {step_count}, total_distance={total_distance:.1f}m")
                                    return {'found': True, 'target': target, 'distance': total_distance}
                        except Exception as e:
                            logger.error(f"[SEARCH] Grid step {step_count}: Error scanning for targets: {str(e)}")
                            pass
                    
                    y += scan_interval
                    direction *= -1  # Reverse direction
                    log_info(f"[SEARCH] Grid: Completed row at y={y-scan_interval:.1f}, moving to next row at y={y:.1f}")
                
                log_info(f"[SEARCH] Grid search completed: {step_count} steps, {total_distance:.1f}m traveled, target not found")
                return {'found': False, 'distance': total_distance, 'steps': step_count}
            
            # Step 5: Execute search strategies - MULTIPLE ROUNDS for thorough coverage
            # Non-task drones can search until battery depleted - no battery limit
            log_info(f"[SEARCH] Step 5: Starting systematic search strategies")
            strategies_to_try = []
            if search_strategy == 'auto':
                # Try all strategies, and if all fail, try again with different starting positions
                strategies_to_try = ['directional', 'spiral', 'grid']
                log_info(f"[SEARCH] Strategy: auto - will try all strategies: {strategies_to_try}")
            else:
                strategies_to_try = [search_strategy]
                log_info(f"[SEARCH] Strategy: {search_strategy}")
            
            # Try multiple rounds of search if first round fails
            max_search_rounds = 2  # Allow 2 rounds of exhaustive search
            log_info(f"[SEARCH] Will perform {max_search_rounds} rounds of search")
            for round_num in range(max_search_rounds):
                log_info(f"[SEARCH] ===== ROUND {round_num + 1}/{max_search_rounds} =====")
                # If not first round, try different starting positions
                if round_num > 0:
                    # Try starting from different corners/edges
                    corner_positions = [
                        (0, 0),  # Southwest corner
                        (canvas_width, 0),  # Southeast corner
                        (0, canvas_height),  # Northwest corner
                        (canvas_width, canvas_height),  # Northeast corner
                        (canvas_width / 2, 0),  # South center
                        (canvas_width / 2, canvas_height),  # North center
                        (0, canvas_height / 2),  # West center
                        (canvas_width, canvas_height / 2),  # East center
                    ]
                    corner_idx = (round_num - 1) % len(corner_positions)
                    new_start_x, new_start_y = corner_positions[corner_idx]
                    new_start_z = 2.0
                    log_info(f"[SEARCH] Round {round_num + 1}: Starting from new position ({new_start_x:.1f}, {new_start_y:.1f}, {new_start_z:.1f})")
                    # Move to new starting position
                    try:
                        client.move_to(search_drone_id, new_start_x, new_start_y, new_start_z)
                        start_x, start_y, start_z = new_start_x, new_start_y, new_start_z
                        # Clear searched areas for new round
                        searched_areas.clear()
                        log_info(f"[SEARCH] Round {round_num + 1}: Moved to new starting position, cleared searched areas")
                    except Exception as e:
                        log_error(f"[SEARCH] Round {round_num + 1}: Failed to move to new position: {str(e)}")
                        pass
                
                for strategy in strategies_to_try:
                    log_info(f"[SEARCH] Round {round_num + 1}: Trying strategy '{strategy}'")
                    try:
                        if strategy == 'directional':
                            # Try 8 directions (4 cardinal + 4 diagonal) for better coverage
                            directions = [0, 45, 90, 135, 180, 225, 270, 315]  # N, NE, E, SE, S, SW, W, NW
                            # Search distance should cover ENTIRE map diagonal (100%+ to ensure full coverage)
                            map_diagonal = (canvas_width**2 + canvas_height**2)**0.5
                            max_dist = max_search_area or map_diagonal * 1.2  # 120% of diagonal ensures full coverage
                            log_info(f"[SEARCH] Directional search: Trying {len(directions)} directions, max_dist={max_dist:.1f}m")
                            
                            for direction in directions:
                                log_info(f"[SEARCH] Directional search: Trying direction {direction}°")
                                result = directional_search(search_drone_id, target_name, start_x, start_y, start_z,
                                                            direction, scan_interval, max_dist, canvas_width, canvas_height)
                                if result.get('found'):
                                    # Record to environment memory
                                    if environment_memory and result.get('target'):
                                        try:
                                            record_params = json.dumps({'targets': [result['target']]})
                                            record_environment_discovery(record_params)
                                        except:
                                            pass
                                    result['drone_used'] = search_drone.get('name')
                                    result['strategy'] = f'directional_{direction}'
                                    return json.dumps(result, ensure_ascii=False, indent=2)
                        
                        elif strategy == 'spiral':
                            # Square spiral search
                            log_info(f"[SEARCH] Round {round_num + 1}: Starting spiral search")
                            result = spiral_search(search_drone_id, target_name, start_x, start_y, start_z,
                                                   scan_interval, canvas_width, canvas_height, perceived_radius)
                            if result.get('found'):
                                # Record to environment memory
                                if environment_memory and result.get('target'):
                                    try:
                                        record_params = json.dumps({'targets': [result['target']]})
                                        record_environment_discovery(record_params)
                                    except:
                                        pass
                                result['drone_used'] = search_drone.get('name')
                                result['strategy'] = 'spiral'
                                return json.dumps(result, ensure_ascii=False, indent=2)
                        
                        elif strategy == 'grid':
                            # Grid pattern search
                            log_info(f"[SEARCH] Round {round_num + 1}: Starting grid search")
                            result = grid_search(search_drone_id, target_name, start_x, start_y, start_z,
                                                 scan_interval, canvas_width, canvas_height, perceived_radius)
                            if result.get('found'):
                                # Record to environment memory
                                if environment_memory and result.get('target'):
                                    try:
                                        record_params = json.dumps({'targets': [result['target']]})
                                        record_environment_discovery(record_params)
                                    except:
                                        pass
                                result['drone_used'] = search_drone.get('name')
                                result['strategy'] = 'grid'
                                return json.dumps(result, ensure_ascii=False, indent=2)
                    except Exception as e:
                        logger.error(f"[SEARCH] Round {round_num + 1}: Strategy '{strategy}' failed with error: {str(e)}")
                        continue  # Try next strategy
                
                # If any strategy found target in this round, return immediately
                # (The return statements inside each strategy will exit the function)
            
            # All strategies and rounds failed
            logger.error(f"[SEARCH] ===== SEARCH FAILED: Target '{target_name}' not found after {max_search_rounds} rounds with all strategies =====")
            return json.dumps({
                'found': False,
                'target_name': target_name,
                'drone_used': search_drone.get('name'),
                'strategies_tried': strategies_to_try,
                'search_rounds': max_search_rounds,
                'message': f'Target "{target_name}" not found after {max_search_rounds} rounds of exhaustive search with all strategies'
            }, ensure_ascii=False, indent=2)
            
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"
        except Exception as e:
            return f"Error in search: {str(e)}"
    

    @tool
    def estimate_target_location(input_json: str) -> str:
        """Estimate target location based on task description, known coordinates, or other drones' positions.
        
        WHEN TO USE (FIRST STEP IN TARGET SEARCH):
        - ALWAYS use this FIRST before searching for a target
        - When target name is known but location is unknown
        - To check if other drones have already found the target
        
        WHEN NOT TO USE:
        - If you already know exact target coordinates (use move_to directly)
        - After you've already found the target
        
        IMPORTANT: This tool checks other drones' positions and their nearby entities to infer 
        target locations. If another drone has found a target, use move_to to go directly to those coordinates.
        
        Input should be a JSON string with:
        - task_description: Full task description containing location hints (required)
        - target_name: Name of target to find (optional, but recommended)
        - known_locations: Dict of known location names to coordinates (optional)
        
        Returns: estimated coordinates or location clues. If target found near another drone, use move_to directly.
        """
        try:
            params = json.loads(input_json)
            task_desc = params.get('task_description', '')
            target_name = params.get('target_name', '')
            known_locs = params.get('known_locations', {})
            
            if not task_desc:
                return "Error: task_description is required"
            
            # Extract location hints from task description
            import re
            location_clues = []
            
            # Look for coordinate patterns: (x, y, z) or x=..., y=..., z=...
            coord_patterns = [
                r'(?:x|X)\s*=\s*(\d+(?:\.\d+)?)',
                r'(?:y|Y)\s*=\s*(\d+(?:\.\d+)?)',
                r'(?:z|Z)\s*=\s*(\d+(?:\.\d+)?)',
                r'\((\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\)'
            ]
            
            coords = {'x': None, 'y': None, 'z': None}
            for match in re.finditer(coord_patterns[0], task_desc):
                coords['x'] = float(match.group(1))
            for match in re.finditer(coord_patterns[1], task_desc):
                coords['y'] = float(match.group(1))
            for match in re.finditer(coord_patterns[2], task_desc):
                coords['z'] = float(match.group(1))
            
            # Look for known location names
            for loc_name in known_locs.keys():
                if loc_name.lower() in task_desc.lower():
                    location_clues.append({
                        'location': loc_name,
                        'coordinates': known_locs[loc_name]
                    })
            
            # Check other drones' nearby entities if target_name is provided
            other_drone_hints = []
            if target_name:
                try:
                    drones = client.list_drones()
                    for drone in drones:
                        drone_id = drone.get('id')
                        if drone_id:
                            try:
                                nearby = client.get_nearby_entities(drone_id)
                                targets = nearby.get('targets', [])
                                for t in targets:
                                    if t.get('name', '').lower() == target_name.lower():
                                        other_drone_hints.append({
                                            'drone_id': drone_id,
                                            'drone_name': drone.get('name'),
                                            'drone_position': drone.get('position'),
                                            'target_found': t,
                                            'message': f'Target found near {drone.get("name")} at {drone.get("position")}'
                                        })
                            except:
                                pass
                except:
                    pass
            
            # Look for directional hints
            direction_keywords = {
                'north': 0, 'south': 180, 'east': 90, 'west': 270,
                'forward': 0, 'backward': 180, 'right': 90, 'left': 270,
                '北': 0, '南': 180, '东': 90, '西': 270
            }
            
            directions_found = []
            for keyword, heading in direction_keywords.items():
                if keyword in task_desc.lower():
                    directions_found.append({'direction': keyword, 'heading': heading})
            
            recommendation = 'Use coordinates if available, otherwise use search_target'
            warning_msg = None
            if other_drone_hints:
                recommendation = f'Target found near other drone! Use move_to to go directly to coordinates: {other_drone_hints[0]["target_found"].get("position")}'
            elif target_name and not other_drone_hints:
                # Target not found, add warning to prevent repeated calls
                warning_msg = f'DO NOT call estimate_target_location again for "{target_name}" - it has already been checked. Proceed to search_target with task_drone_id parameter.'
            
            result = {
                'task_description': task_desc[:200],
                'estimated_coordinates': coords if any(coords.values()) else None,
                'location_clues': location_clues if location_clues else "No known locations found",
                'direction_hints': directions_found if directions_found else "No direction hints found",
                'other_drone_hints': other_drone_hints if other_drone_hints else "Target not found near other drones",
                'recommendation': recommendation
            }
            if warning_msg:
                result['warning'] = warning_msg
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"
        except Exception as e:
            return f"Error estimating location: {str(e)}"

    @tool
    def safe_move_to(input_json: str) -> str:
        """Intelligently move a drone to target coordinates with automatic obstacle avoidance.
        
        THIS IS THE PRIMARY MOVEMENT TOOL - Use this instead of move_to for all movements.
        It automatically handles obstacle avoidance with multiple strategies:
        1. Direct movement (if path is clear)
        2. Dimension-by-dimension movement (align X, then Y, then Z)
        3. Alternative dimension order (align Y first if X is blocked)
        4. Large detour around obstacles (300-500m)
        5. Multi-directional attempts
        
        WHEN TO USE:
        - ALWAYS use this for any movement to coordinates - it's smarter than move_to
        - Use for waypoint navigation, target reaching, formation positioning
        - Automatically handles obstacles and finds alternative paths

        Input JSON:
        - drone_id: ID of drone (required)
        - x, y, z: Target coordinates (required)
        - max_attempts: Maximum number of path attempts (default: 5)
        - detour_distance: Distance for large detours in meters (default: 400)
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            drone_id = params.get('drone_id')
            tx, ty, tz = params.get('x'), params.get('y'), params.get('z')
            max_attempts = params.get('max_attempts', 5)
            detour_distance = params.get('detour_distance', 400)

            if not drone_id or tx is None or ty is None or tz is None:
                return "Error: drone_id, x, y, z are required"

            # Get current position
            status = client.get_drone_status(drone_id)
            start = status.get('position', {})
            sx, sy, sz = start.get('x'), start.get('y'), start.get('z')
            if sx is None or sy is None or sz is None:
                return "Error: could not retrieve start position"

            # Calculate distances
            dx = tx - sx
            dy = ty - sy
            dz = tz - sz
            total_dist = math.sqrt(dx**2 + dy**2 + dz**2)

            # Strategy 1: Try direct movement first
            try:
                result = client.move_to(drone_id, tx, ty, tz)
                if isinstance(result, dict) and result.get('status') == 'success':
                    return json.dumps({
                        'success': True,
                        'strategy': 'direct',
                        'result': result,
                        'message': 'Direct movement successful'
                    }, ensure_ascii=False, indent=2)
            except Exception:
                pass

            # Strategy 2: Dimension-by-dimension (X → Y → Z)
            if abs(dx) > 1 or abs(dy) > 1 or abs(dz) > 1:
                try:
                    current_x, current_y, current_z = sx, sy, sz
                    success = True
                    
                    # Step 1: Align X coordinate
                    if abs(dx) > 1:
                        result1 = client.move_to(drone_id, tx, current_y, current_z)
                        if isinstance(result1, dict) and result1.get('status') == 'success':
                            new_status = client.get_drone_status(drone_id)
                            new_pos = new_status.get('position', {})
                            current_x = new_pos.get('x', tx)
                            current_y = new_pos.get('y', current_y)
                            current_z = new_pos.get('z', current_z)
                        else:
                            success = False
                    
                    # Step 2: Align Y coordinate (only if X step succeeded or was skipped)
                    if success and abs(dy) > 1:
                        result2 = client.move_to(drone_id, current_x, ty, current_z)
                        if isinstance(result2, dict) and result2.get('status') == 'success':
                            new_status = client.get_drone_status(drone_id)
                            new_pos = new_status.get('position', {})
                            current_x = new_pos.get('x', current_x)
                            current_y = new_pos.get('y', ty)
                            current_z = new_pos.get('z', current_z)
                        else:
                            success = False
                    
                    # Step 3: Align Z coordinate (only if previous steps succeeded)
                    if success and abs(dz) > 1:
                        result3 = client.move_to(drone_id, current_x, current_y, tz)
                        if isinstance(result3, dict) and result3.get('status') == 'success':
                            return json.dumps({
                                'success': True,
                                'strategy': 'dimension_by_dimension',
                                'result': result3,
                                'message': 'Dimension-by-dimension movement successful'
                            }, ensure_ascii=False, indent=2)
                except Exception:
                    pass

            # Strategy 3: Alternative dimension order (Y → X → Z) if X was blocked
            if abs(dx) > 1 and abs(dy) > 1:
                try:
                    # Try Y first, then X
                    result_y = client.move_to(drone_id, sx, ty, sz)
                    if isinstance(result_y, dict) and result_y.get('status') == 'success':
                        new_status = client.get_drone_status(drone_id)
                        new_pos = new_status.get('position', {})
                        sx = new_pos.get('x', sx)
                        sy = new_pos.get('y', ty)
                        sz = new_pos.get('z', sz)
                        
                        result_x = client.move_to(drone_id, tx, ty, sz)
                        if isinstance(result_x, dict) and result_x.get('status') == 'success':
                            result_z = client.move_to(drone_id, tx, ty, tz)
                            if isinstance(result_z, dict) and result_z.get('status') == 'success':
                                return json.dumps({
                                    'success': True,
                                    'strategy': 'alternative_dimension_order',
                                    'result': result_z,
                                    'message': 'Alternative dimension order successful'
                                }, ensure_ascii=False, indent=2)
                except Exception:
                    pass

            # Strategy 4: Large detour around obstacles
            # Try moving away from target first, then approach from different angle
            attempts = 0
            detour_strategies = [
                # Strategy 4a: Move north then approach
                (sx, sy + detour_distance, sz, tx, ty, tz),
                # Strategy 4b: Move south then approach
                (sx, sy - detour_distance, sz, tx, ty, tz),
                # Strategy 4c: Move east then approach
                (sx + detour_distance, sy, sz, tx, ty, tz),
                # Strategy 4d: Move west then approach
                (sx - detour_distance, sy, sz, tx, ty, tz),
                # Strategy 4e: Move northeast then approach
                (sx + detour_distance * 0.7, sy + detour_distance * 0.7, sz, tx, ty, tz),
                # Strategy 4f: Move northwest then approach
                (sx - detour_distance * 0.7, sy + detour_distance * 0.7, sz, tx, ty, tz),
            ]

            for detour_x, detour_y, detour_z, final_x, final_y, final_z in detour_strategies[:max_attempts]:
                attempts += 1
                try:
                    # Move to detour point
                    detour_result = client.move_to(drone_id, detour_x, detour_y, detour_z)
                    if isinstance(detour_result, dict) and detour_result.get('status') == 'success':
                        # Now try to reach target from detour point
                        final_result = client.move_to(drone_id, final_x, final_y, final_z)
                        if isinstance(final_result, dict) and final_result.get('status') == 'success':
                            return json.dumps({
                                'success': True,
                                'strategy': f'detour_attempt_{attempts}',
                                'detour_point': {'x': detour_x, 'y': detour_y, 'z': detour_z},
                                'result': final_result,
                                'message': f'Detour strategy {attempts} successful'
                            }, ensure_ascii=False, indent=2)
                except Exception:
                    continue

            # Strategy 5: Incremental approach with smaller steps
            # If all else fails, try moving in smaller increments
            if total_dist > 100:
                step_size = min(200, total_dist / 3)
                current_x, current_y, current_z = sx, sy, sz
                
                for step in range(1, 4):  # Try up to 3 steps
                    try:
                        # Calculate intermediate point
                        t = step / 3
                        inter_x = sx + (tx - sx) * t
                        inter_y = sy + (ty - sy) * t
                        inter_z = sz + (tz - sz) * t
                        
                        step_result = client.move_to(drone_id, inter_x, inter_y, inter_z)
                        if isinstance(step_result, dict) and step_result.get('status') == 'success':
                            current_x, current_y, current_z = inter_x, inter_y, inter_z
                            if step == 3:  # Last step reached target
                                return json.dumps({
                                    'success': True,
                                    'strategy': 'incremental',
                                    'result': step_result,
                                    'message': 'Incremental approach successful'
                                }, ensure_ascii=False, indent=2)
                        else:
                            break  # If step fails, stop incremental approach
                    except Exception:
                        break

            # All strategies failed
            return json.dumps({
                'success': False,
                'strategy': 'all_failed',
                'attempts': attempts,
                'message': 'All movement strategies failed. Target may be unreachable or blocked by obstacles.',
                'suggestion': 'Try using get_nearby_entities to identify obstacles, then plan a manual detour path.'
            }, ensure_ascii=False, indent=2)

        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"
        except Exception as e:
            return f"Error in safe move: {str(e)}"

    # ========== Environment Memory Tool ==========

    @tool
    def record_environment_discovery(input_json: str) -> str:
        """Record obstacles and targets discovered during task execution to environment memory.
        
        WHEN TO USE:
        - After calling get_nearby_entities and discovering new obstacles or targets
        - When you encounter obstacles during movement (from error messages)
        - To remember discovered locations for future path planning
        
        WHEN NOT TO USE:
        - If you haven't discovered anything new (don't call unnecessarily)
        - For obstacles/targets already recorded in environment memory
        
        This tool automatically records discovered obstacles and targets so you can use them
        for future path planning. After recording, these locations will be available in
        environment memory for subsequent actions.
        
        Input should be a JSON string with:
        - obstacles: List of obstacle objects (optional, from get_nearby_entities result)
        - targets: List of target objects (optional, from get_nearby_entities result)
        - error_message: Error message containing obstacle information (optional)
        
        Example 1 (from get_nearby_entities):
        {{"obstacles": [{{"name": "Obstacle 1", "position": {{"x": 100, "y": 200, "z": 0}}, "type": "circle"}}], "targets": [{{"name": "Target 1", "position": {{"x": 300, "y": 400, "z": 0}}}}]}}
        
        Example 2 (from error message):
        {{"error_message": "Path blocked by Polygon Obstacle 3"}}
        """
        try:
            params = json.loads(input_json) if isinstance(input_json, str) else input_json
            
            if not environment_memory:
                return "Error: Environment memory not available"
            
            recorded_items = []
            
            # 记录障碍物
            obstacles = params.get('obstacles', [])
            existing_obs_ids = {obs.get('id') or obs.get('name') for obs in environment_memory.get('obstacles', [])}
            
            for obstacle in obstacles:
                obs_id = obstacle.get('id') or obstacle.get('name')
                if obs_id and obs_id not in existing_obs_ids:
                    existing_obs_ids.add(obs_id)
                    environment_memory.setdefault('obstacles', []).append({
                        'name': obstacle.get('name', 'Unknown'),
                        'id': obs_id,
                        'position': obstacle.get('position', {}),
                        'type': obstacle.get('type', 'unknown'),
                        'radius': obstacle.get('radius'),
                        'vertices': obstacle.get('vertices', [])
                    })
                    recorded_items.append(f"obstacle: {obstacle.get('name')}")
            
            # 记录目标
            targets = params.get('targets', [])
            existing_tgt_ids = {tgt.get('id') or tgt.get('name') for tgt in environment_memory.get('targets', [])}
            
            for target in targets:
                tgt_id = target.get('id') or target.get('name')
                if tgt_id and tgt_id not in existing_tgt_ids:
                    existing_tgt_ids.add(tgt_id)
                    environment_memory.setdefault('targets', []).append({
                        'name': target.get('name', 'Unknown'),
                        'id': tgt_id,
                        'position': target.get('position', {}),
                        'type': target.get('type', 'unknown')
                    })
                    recorded_items.append(f"target: {target.get('name')}")
            
            # 从错误消息中提取障碍物
            error_message = params.get('error_message', '')
            if error_message:
                import re
                match = re.search(r"ObstacleType\.(\w+)\s+obstacle\s+'([^']+)'", error_message)
                if match:
                    obs_type = match.group(1).lower()
                    obs_name = match.group(2)
                    if obs_name not in existing_obs_ids:
                        environment_memory.setdefault('obstacles', []).append({
                            'name': obs_name,
                            'id': obs_name,
                            'type': obs_type,
                            'position': None,
                            'blocked_paths': []
                        })
                        recorded_items.append(f"obstacle from error: {obs_name}")
            
            if recorded_items:
                return json.dumps({
                    'success': True,
                    'recorded': recorded_items,
                    'message': f"Recorded {len(recorded_items)} items to environment memory"
                }, indent=2)
            else:
                return json.dumps({
                    'success': True,
                    'recorded': [],
                    'message': "No new items to record (all already in memory)"
                }, indent=2)
                
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {str(e)}"
        except Exception as e:
            return f"Error recording environment discovery: {str(e)}"

    # Return all tools
    return [
        list_drones,
        get_drone_status,
        get_session_info,
        get_task_progress,
        get_weather,
        get_nearby_entities,
        find_target_by_name,
        search_target,                # 统一智能搜索工具（自动选择无人机、多种策略、自动记录）
        safe_move_to,
        estimate_target_location,     # 位置估计工具
        record_environment_discovery, # 环境记忆记录工具
        take_off,
        land,
        move_to,
        # check_path_collision,  # Disabled: API endpoint may be unavailable
        move_towards,
        change_altitude,
        hover,
        rotate,
        return_home,
        set_home,
        calibrate,
        take_photo,
        send_message,
        broadcast,
        charge,
        check_two_drones_distance,  # 队形验证工具
        verify_formation,            # 队形验证工具
    ]
