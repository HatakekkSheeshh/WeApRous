# Example usage
import json
import threading
from daemon.weaprous import WeApRous
# from daemon.httpadapter import HttpAdapter
from daemon.resp_template import RESP_TEMPLATES
from daemon.utils import parse_form_or_json

# Initialize the WeApRous app
app = WeApRous()

# Global data structures for tracking
peers_list = []  # List of active peers: [{"username": str, "ip": str, "port": int, "channels": []}]
channels_list = {}  # Dictionary of channels: {channel_name: [usernames]}
users_credentials = {"admin": "password"}  # Simple user database
peers_lock = threading.Lock()  # Thread-safe access to peers_list
channels_lock = threading.Lock()  # Thread-safe access to channels_list

@app.route(path='/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    print("[SampleApp] Logging in {} to {}".format(headers, body))

    try:
        data = parse_form_or_json(body)

        print("[DATA] {}".format(data))

        username = data.get("username", "")
        password = data.get("password", "")
        
        print("[SampleApp] Login attempt: username={}".format(username))
        
        # Validate credentials
        if username in users_credentials and users_credentials[username] == password:
            e = RESP_TEMPLATES["api_ok"]
            response = (
                e["status"],
                {"Content-Type": e["content_type"], **e["headers"]},
                e["body"]
            )
            print("[SampleApp] Login successful for user: {}".format(username))
        else:
            e = RESP_TEMPLATES["login_failed"]
            response = (
                e["status"],
                {"Content-Type": e["content_type"]},
                e["body"]
            )
            print("[SampleApp] Login failed for user: {}".format(username))
        
        return response
    
    except Exception as e:
        print("[SampleApp] Error in login: {}".format(e))
        e = RESP_TEMPLATES["server_error"]
        return (
            e["status"],
            {"Content-Type": e["content_type"], **e["headers"]},
            e["body"]
        )

@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))

@app.route("/", methods=["GET"])
def home(headers=None, body=None):
    return {"message": "Welcome to the RESTful TCP WebApp"}

@app.route("/user", methods=["GET"])
def get_user(headers=None, body=None):
    return {"id": 1, "name": "Alice", "email": "alice@example.com"}

@app.route("/echo", methods=["POST"])
def echo(headers=None, body=None):
    try:
        data = json.loads(body)
        return {"received": data}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

@app.route('/submit-info', methods=['POST'])
def submit_info(headers="guest", body="anonymous"):
    """
    Handle peer registration - peers submit their info to the tracker.
    
    Expected body format: {"username": str, "ip": str, "port": int, "channels": [str]}
    Response: {"status": "success"/"failed", "message": str, "peer_id": int}
    
    :param headers (str): The request headers
    :param body (str): The request body containing peer information
    :return: JSON response with registration status
    """
    print("[ChatApp] Peer registration request received")
    
    try:
        # Parse JSON body
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        ip = data.get("ip", "")
        port = data.get("port", 0)
        channels = data.get("channels", [])
        
        print("[ChatApp] Registering peer: username={}, ip={}, port={}".format(username, ip, port))
        
        if not username or not ip or not port:
            return json.dumps({"status": "failed", "message": "Missing required fields"})
        
        # Thread-safe peer registration
        with peers_lock:
            # Check if peer already exists (update if exists)
            existing_peer = None
            for i, peer in enumerate(peers_list):
                if peer["username"] == username:
                    existing_peer = i
                    break
            
            peer_info = {
                "username": username,
                "ip": ip,
                "port": port,
                "channels": channels
            }
            
            if existing_peer is not None:
                peers_list[existing_peer] = peer_info
                peer_id = existing_peer
                print("[ChatApp] Updated existing peer: {}".format(username))
            else:
                peers_list.append(peer_info)
                peer_id = len(peers_list) - 1
                print("[ChatApp] Added new peer: {}".format(username))
        
        # Update channels
        with channels_lock:
            for channel in channels:
                if channel not in channels_list:
                    channels_list[channel] = []
                if username not in channels_list[channel]:
                    channels_list[channel].append(username)
        
        response = {
            "status": "success",
            "message": "Peer registered successfully",
            "peer_id": peer_id,
            "total_peers": len(peers_list)
        }
        
        print("[ChatApp] Peer registered: {} (total peers: {})".format(username, len(peers_list)))
        return json.dumps(response)
    
    except Exception as e:
        print("[ChatApp] Error in submit-info: {}".format(e))
        return json.dumps({"status": "error", "message": str(e)})


@app.route('/add-list', methods=['POST'])
def add_list(headers="guest", body="anonymous"):
    """
    Handle channel creation/subscription.
    
    Expected body format: {"username": str, "channel": str}
    Response: {"status": "success"/"failed", "message": str, "members": [str]}
    
    :param headers (str): The request headers
    :param body (str): The request body containing channel information
    :return: JSON response with channel status
    """
    print("[ChatApp] Add to channel request received")
    
    try:
        # Parse JSON body
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        channel = data.get("channel", "")
        
        print("[ChatApp] Adding user {} to channel {}".format(username, channel))
        
        if not username or not channel:
            return json.dumps({"status": "failed", "message": "Missing username or channel"})
        
        # Thread-safe channel update
        with channels_lock:
            if channel not in channels_list:
                channels_list[channel] = []
            
            if username not in channels_list[channel]:
                channels_list[channel].append(username)
                message = "User added to channel successfully"
            else:
                message = "User already in channel"
            
            members = channels_list[channel][:]
        
        # Update peer's channel list
        with peers_lock:
            for peer in peers_list:
                if peer["username"] == username:
                    if channel not in peer["channels"]:
                        peer["channels"].append(channel)
                    break
        
        response = {
            "status": "success",
            "message": message,
            "channel": channel,
            "members": members,
            "member_count": len(members)
        }
        
        print("[ChatApp] Channel {} now has {} members".format(channel, len(members)))
        return json.dumps(response)
    
    except Exception as e:
        print("[ChatApp] Error in add-list: {}".format(e))
        return json.dumps({"status": "error", "message": str(e)})


@app.route('/get-list', methods=['GET', 'POST'])
def get_list(headers="guest", body="anonymous"):
    """
    Get list of active peers or channel members.
    
    Expected body format: {"channel": str (optional), "username": str (optional)}
    Response: {"status": "success", "peers": [...], "channels": {...}}
    
    :param headers (str): The request headers
    :param body (str): Optional filter parameters
    :return: JSON response with peer/channel list
    """
    print("[ChatApp] Get list request received")
    
    try:
        # Parse JSON body if provided
        data = {}
        if body and body != "anonymous":
            try:
                data = json.loads(body)
            except:
                pass
        
        channel_filter = data.get("channel", None)
        username_filter = data.get("username", None)
        
        # Thread-safe read
        with peers_lock:
            peers_copy = [peer.copy() for peer in peers_list]
        
        with channels_lock:
            channels_copy = {k: v[:] for k, v in channels_list.items()}
        
        # Apply filters
        if channel_filter and channel_filter in channels_copy:
            # Get peers in specific channel
            channel_members = channels_copy[channel_filter]
            filtered_peers = [p for p in peers_copy if p["username"] in channel_members]
            response = {
                "status": "success",
                "channel": channel_filter,
                "peers": filtered_peers,
                "peer_count": len(filtered_peers)
            }
        elif username_filter:
            # Get specific user's info
            user_peer = [p for p in peers_copy if p["username"] == username_filter]
            user_channels = channels_copy
            response = {
                "status": "success",
                "peers": user_peer,
                "channels": user_channels
            }
        else:
            # Get all peers and channels
            response = {
                "status": "success",
                "peers": peers_copy,
                "channels": channels_copy,
                "total_peers": len(peers_copy),
                "total_channels": len(channels_copy)
            }
        
        print("[ChatApp] Returned list: {} peers, {} channels".format(
            len(peers_copy), len(channels_copy)))
        return json.dumps(response)
    
    except Exception as e:
        print("[ChatApp] Error in get-list: {}".format(e))
        return json.dumps({"status": "error", "message": str(e)})


@app.route('/register', methods=['POST'])
def register(headers="guest", body="anonymous"):
    """
    Register new user account.
    
    Expected body format: {"username": str, "password": str}
    Response: {"status": "success"/"failed", "message": str}
    
    :param headers (str): The request headers
    :param body (str): The request body containing registration info
    :return: JSON response with registration status
    """
    print("[ChatApp] User registration request received")
    
    try:
        # Parse JSON body
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        password = data.get("password", "")
        
        print("[ChatApp] Registration attempt: username={}".format(username))
        
        if not username or not password:
            return json.dumps({"status": "failed", "message": "Missing username or password"})
        
        if username in users_credentials:
            return json.dumps({"status": "failed", "message": "Username already exists"})
        
        # Register new user
        users_credentials[username] = password
        
        response = {
            "status": "success",
            "message": "User registered successfully",
            "username": username
        }
        
        print("[ChatApp] User registered: {}".format(username))
        return json.dumps(response)
    
    except Exception as e:
        print("[ChatApp] Error in register: {}".format(e))
        return json.dumps({"status": "error", "message": str(e)})


@app.route('/status', methods=['GET'])
def status(headers="guest", body="anonymous"):
    """
    Get server status and statistics.
    
    Response: {"status": "online", "stats": {...}}
    
    :param headers (str): The request headers
    :param body (str): Not used
    :return: JSON response with server status
    """
    with peers_lock:
        peer_count = len(peers_list)
    
    with channels_lock:
        channel_count = len(channels_list)
    
    response = {
        "status": "online",
        "stats": {
            "total_peers": peer_count,
            "total_channels": channel_count,
            "total_users": len(users_credentials)
        }
    }
    
    return json.dumps(response)