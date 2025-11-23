#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
start_chatapp
~~~~~~~~~~~~~~~~~

This module implements a hybrid chat application using WeApRous framework.
It combines client-server paradigm (for peer tracking) and peer-to-peer
paradigm (for direct messaging).

The tracker server manages:
- User login and authentication
- Peer registration and tracking
- Channel management
- Peer discovery
"""

import json
import socket
import argparse
import threading
from daemon.weaprous import WeApRous

PORT = 8001  # Default port for chat tracker server

# Global data structures for tracking
peers_list = []  # List of active peers: [{"username": str, "ip": str, "port": int, "channels": []}]
channels_list = {}  # Dictionary of channels: {channel_name: [usernames]}
users_credentials = {"admin": "password"}  # Simple user database
peers_lock = threading.Lock()  # Thread-safe access to peers_list
channels_lock = threading.Lock()  # Thread-safe access to channels_list

app = WeApRous()

@app.route('/login', methods=['OPTIONS'])
def login_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS with credentials."""
    # Get origin from headers
    origin = None
    if isinstance(headers, dict):
        origin = headers.get('origin')
        
        # Fallback: try Referer header if Origin is not present
        if not origin:
            referer = headers.get('referer') or headers.get('Referer')
            if referer:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                    print("[ChatApp] OPTIONS - Extracted origin from Referer: {} -> {}".format(referer, origin))
                except:
                    pass
    elif isinstance(headers, str) and 'origin:' in headers.lower():
        for line in headers.split('\n'):
            if 'origin:' in line.lower():
                origin = line.split(':', 1)[1].strip()
                break
    
    # Use origin from request if available (required for credentials)
    # MUST return exact origin from request for CORS with credentials
    if origin:
        cors_origin = origin
        print("[ChatApp] OPTIONS - Using origin from request: {}".format(origin))
    else:
        # Fallback (should rarely happen)
        cors_origin = "http://localhost:8001"
        print("[ChatApp] OPTIONS - Warning: No origin, using default: {}".format(cors_origin))
    
    return ("200 OK", {
        "Access-Control-Allow-Origin": cors_origin,  # Specific origin for credentials
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/submit-info', methods=['OPTIONS'])
def submit_info_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/add-list', methods=['OPTIONS'])
def add_list_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/get-list', methods=['OPTIONS'])
def get_list_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/register', methods=['OPTIONS'])
def register_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.
    
    Supports TWO formats (Task 1 + Task 2):
    1. Form data: username=admin&password=password (Task 1 - Cookie session)
    2. JSON data: {"username":"admin","password":"password"} (Task 2 - RESTful API)
    
    :param headers (str): The request headers or user identifier.
    :param body (str): The request body containing login credentials.
    :return: HTML response with Set-Cookie (Task 1) OR JSON response (Task 2)
    """
    print("[ChatApp] Login request received")
    
    # Get origin from headers for CORS with credentials
    origin = None
    if isinstance(headers, dict):
        # Headers dict from httpadapter (CaseInsensitiveDict)
        # CaseInsensitiveDict stores keys in lowercase, so 'origin' should work
        origin = headers.get('origin')
        
        # Fallback: try Referer header if Origin is not present
        # Referer format: http://localhost:8002/chat.html -> extract http://localhost:8002
        if not origin:
            referer = headers.get('referer') or headers.get('Referer')
            if referer:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                    print("[ChatApp] ✓ Extracted origin from Referer: {} -> {}".format(referer, origin))
                except:
                    pass
        
        # Debug: print all headers to see what we have
        if not origin:
            print("[ChatApp] ⚠️ Origin not found in headers!")
            print("[ChatApp] Debug - Available headers keys: {}".format(list(headers.keys())[:20]))
            print("[ChatApp] Debug - Full headers dict (first 10): {}".format(dict(list(headers.items())[:10])))
            # Try to find origin in any case variation (shouldn't be needed with CaseInsensitiveDict)
            for key, value in headers.items():
                if key.lower() == 'origin':
                    origin = value
                    print("[ChatApp] ✓ Found origin via iteration: {} = {}".format(key, value))
                    break
        else:
            print("[ChatApp] ✓ Found origin in headers: origin = {}".format(origin))
    elif isinstance(headers, str):
        # String format - parse it
        print("[ChatApp] Debug - Headers is string, parsing...")
        if 'origin:' in headers.lower():
            for line in headers.split('\n'):
                if 'origin:' in line.lower():
                    origin = line.split(':', 1)[1].strip()
                    print("[ChatApp] ✓ Found origin in string headers: {}".format(origin))
                    break
    
    print("[ChatApp] Final origin from request: {} (type: {})".format(origin, type(headers)))
    
    # CRITICAL DEBUG: If origin is None, print ALL headers to debug
    if not origin and isinstance(headers, dict):
        print("[ChatApp] 🔴 CRITICAL DEBUG - Origin is None! Printing ALL headers:")
        for key, value in headers.items():
            print("[ChatApp]   Header: '{}' = '{}'".format(key, value))
    
    try:
        # Try to parse as JSON first (Task 2)
        is_json = False
        data = {}
        
        if body and body != "anonymous":
            # Ensure body is string (httpadapter already decodes bytes)
            if isinstance(body, bytes):
                body = body.decode("utf-8", "ignore")
            
            try:
                data = json.loads(body)
                is_json = True
            except:
                # If not JSON, parse as form data (Task 1)
                data = {}
                for pair in body.split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        # URL decode values
                        from urllib.parse import unquote
                        data[unquote(k)] = unquote(v)
                is_json = False
        
        username = data.get("username", "")
        password = data.get("password", "")
        
        print("[ChatApp] Login attempt: username={}, format={}".format(
            username, "JSON" if is_json else "FORM"))
        
        # Validate credentials
        if username in users_credentials and users_credentials[username] == password:
            if is_json:
                # Task 2: JSON response for RESTful API
                response = {
                    "status": "success",
                    "message": "Login successful",
                    "username": username,
                    "token": "token_{}".format(username)
                }
                print("[ChatApp] Login successful (JSON) for user: {}".format(username))
                return json.dumps(response)
            else:
                # Task 1: HTML response with Set-Cookie header
                # This will be handled by returning a tuple (status, headers, body)
                import os
                
                # Read index.html directly
                index_path = os.path.join("www", "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "rb") as f:
                        body_content = f.read()
                else:
                    # Fallback: simple HTML
                    body_content = b"<html><body><h1>Login Successful</h1><p>Welcome, " + username.encode("utf-8") + b"</p></body></html>"
                
                # Use origin from request if available
                # For credentials, we MUST return the exact origin from request
                # If Origin header is missing, try to get from Referer header
                if not origin and isinstance(headers, dict):
                    referer = headers.get('referer') or headers.get('Referer')
                    if referer:
                        try:
                            from urllib.parse import urlparse
                            parsed = urlparse(referer)
                            origin = f"{parsed.scheme}://{parsed.netloc}"
                            print("[ChatApp] ✓ Extracted origin from Referer: {} -> {}".format(referer, origin))
                        except Exception as e:
                            print("[ChatApp] ⚠️ Failed to parse Referer: {}".format(e))
                
                if origin:
                    cors_origin = origin
                    print("[ChatApp] Using origin: {}".format(origin))
                else:
                    # This should NOT happen - browser always sends Origin or Referer header
                    # For development, try to detect from Referer or use common port
                    print("[ChatApp] ⚠️ CRITICAL: No origin found! Trying to detect from Referer...")
                    if isinstance(headers, dict):
                        referer = headers.get('referer') or headers.get('Referer')
                        if referer:
                            # Try to extract origin from Referer
                            if '8080' in referer:
                                cors_origin = "http://localhost:8080"
                            elif '8002' in referer:
                                cors_origin = "http://localhost:8002"
                            elif '8001' in referer:
                                cors_origin = "http://localhost:8001"
                            else:
                                # Default to 8080 (most common for proxy)
                                cors_origin = "http://localhost:8080"
                        else:
                            # No referer either - default to 8080 (proxy port)
                            cors_origin = "http://localhost:8080"
                    else:
                        # Default to 8080 (proxy port)
                        cors_origin = "http://localhost:8080"
                    print("[ChatApp] ⚠️ Using fallback origin: {} (development only)".format(cors_origin))
                
                headers = {
                    "Content-Type": "text/html; charset=utf-8",
                    "Set-Cookie": "auth=true; Path=/",
                    "Access-Control-Allow-Origin": cors_origin,  # MUST match request origin exactly
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
                
                print("[ChatApp] CORS Origin set to: {} (for credentials)".format(cors_origin))
                
                print("[ChatApp] Login successful (FORM) for user: {}, Set-Cookie: auth=true, Origin: {}".format(username, origin))
                return ("200 OK", headers, body_content)
        else:
            # Wrong credentials
            if is_json:
                # Task 2: JSON error response
                response = {
                    "status": "failed",
                    "message": "Invalid username or password"
                }
                return json.dumps(response)
            else:
                # Task 1: HTML error response (401)
                from daemon.resp_template import RESP_TEMPLATES
                e = RESP_TEMPLATES["login_failed"]
                return (e["status"], {"Content-Type": e["content_type"], **e["headers"]}, e["body"])
    
    except Exception as e:
        print("[ChatApp] Error in login: {}".format(e))
        if is_json:
            return json.dumps({"status": "error", "message": str(e)})
        else:
            from daemon.resp_template import RESP_TEMPLATES
            e_tmpl = RESP_TEMPLATES["server_error"]
            return (e_tmpl["status"], {"Content-Type": e_tmpl["content_type"]}, e_tmpl["body"])


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


@app.route('/remove-list', methods=['OPTIONS'])
def remove_list_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/remove-list', methods=['POST'])
def remove_list(headers="guest", body="anonymous"):
    """
    Handle channel unsubscription (leave channel).
    
    Expected body format: {"username": str, "channel": str}
    Response: {"status": "success"/"failed", "message": str}
    
    :param headers (str): The request headers
    :param body (str): The request body containing channel information
    :return: JSON response with channel status
    """
    print("[ChatApp] Remove from channel request received")
    
    try:
        # Parse JSON body
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        channel = data.get("channel", "")
        
        print("[ChatApp] Removing user {} from channel {}".format(username, channel))
        
        if not username or not channel:
            return json.dumps({"status": "failed", "message": "Missing username or channel"})
        
        # Thread-safe channel update
        with channels_lock:
            if channel in channels_list:
                if username in channels_list[channel]:
                    channels_list[channel].remove(username)
                    message = "User removed from channel successfully"
                    
                    # Remove channel if empty
                    if len(channels_list[channel]) == 0:
                        del channels_list[channel]
                        print("[ChatApp] Channel '{}' deleted (no members)".format(channel))
                else:
                    message = "User not in channel"
            else:
                message = "Channel does not exist"
        
        # Update peer's channel list
        with peers_lock:
            for peer in peers_list:
                if peer["username"] == username:
                    if channel in peer["channels"]:
                        peer["channels"].remove(channel)
                    break
        
        response = {
            "status": "success",
            "message": message,
            "channel": channel
        }
        
        print("[ChatApp] User {} removed from channel '{}'".format(username, channel))
        return json.dumps(response)
    
    except Exception as e:
        print("[ChatApp] Error in remove-list: {}".format(e))
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


@app.route('/connect-peer', methods=['OPTIONS'])
def connect_peer_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")


@app.route('/connect-peer', methods=['POST'])
def connect_peer(headers="guest", body="anonymous"):
    """
    Get peer information for P2P connection setup.
    
    This API helps peers discover other peers' IP/port for direct P2P connections.
    In true P2P, peers connect directly after getting this info.
    
    Request body (JSON):
    {
        "username": "alice",
        "target_username": "bob"  # Optional: specific peer, or None for all in channel
        "channel": "general"      # Optional: filter by channel
    }
    
    Response (JSON):
    {
        "status": "success",
        "peers": [
            {"username": "bob", "ip": "127.0.0.1", "port": 9101},
            ...
        ]
    }
    
    :param headers (str): The request headers
    :param body (str): JSON request body
    :return: JSON response with peer connection info
    """
    print("[ChatApp] Connect-peer request received")
    
    try:
        if not body or body == "anonymous":
            return json.dumps({"status": "error", "message": "Missing request body"})
        
        data = json.loads(body)
        username = data.get("username", "")
        target_username = data.get("target_username", None)
        channel = data.get("channel", None)
        
        if not username:
            return json.dumps({"status": "error", "message": "Username required"})
        
        # Find peers to connect to
        peers_to_connect = []
        
        with peers_lock:
            for peer in peers_list:
                if peer["username"] == username:
                    continue  # Skip self
                
                # Filter by target username if specified
                if target_username and peer["username"] != target_username:
                    continue
                
                # Filter by channel if specified
                if channel:
                    if channel not in peer.get("channels", []):
                        continue
                
                peers_to_connect.append({
                    "username": peer["username"],
                    "ip": peer["ip"],
                    "port": peer["port"]
                })
        
        response = {
            "status": "success",
            "message": "Peer connection info retrieved",
            "peers": peers_to_connect
        }
        
        print("[ChatApp] Connect-peer: {} peers found for {}".format(
            len(peers_to_connect), username))
        
        return json.dumps(response)
    
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON"})
    except Exception as e:
        print("[ChatApp] Error in connect-peer: {}".format(e))
        return json.dumps({"status": "error", "message": str(e)})


@app.route('/broadcast-peer', methods=['OPTIONS'])
def broadcast_peer_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")


@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers="guest", body="anonymous"):
    """
    Broadcast message to all peers in a channel (via tracker notification).
    
    Note: In true P2P, broadcasting should be done directly between peers.
    This API can be used for:
    - Notification/coordination purposes
    - Web interface that cannot create TCP sockets directly
    
    Request body (JSON):
    {
        "username": "alice",
        "channel": "general",
        "message": "Hello everyone!"
    }
    
    Response (JSON):
    {
        "status": "success",
        "message": "Broadcast notification sent",
        "recipients": 3
    }
    
    :param headers (str): The request headers
    :param body (str): JSON request body
    :return: JSON response
    """
    print("[ChatApp] Broadcast-peer request received")
    
    try:
        if not body or body == "anonymous":
            return json.dumps({"status": "error", "message": "Missing request body"})
        
        data = json.loads(body)
        username = data.get("username", "")
        channel = data.get("channel", "")
        message = data.get("message", "")
        
        if not username or not channel:
            return json.dumps({"status": "error", "message": "Username and channel required"})
        
        # Count recipients in channel
        recipient_count = 0
        
        with peers_lock:
            for peer in peers_list:
                if peer["username"] == username:
                    continue  # Skip sender
                
                if channel in peer.get("channels", []):
                    recipient_count += 1
        
        # In true P2P, actual broadcasting happens directly between peers
        # This API just acknowledges the broadcast request
        response = {
            "status": "success",
            "message": "Broadcast notification acknowledged",
            "recipients": recipient_count,
            "note": "Actual P2P broadcast should be done directly between peers"
        }
        
        print("[ChatApp] Broadcast-peer: {} recipients in channel '{}'".format(
            recipient_count, channel))
        
        return json.dumps(response)
    
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON"})
    except Exception as e:
        print("[ChatApp] Error in broadcast-peer: {}".format(e))
        return json.dumps({"status": "error", "message": str(e)})


@app.route('/send-peer', methods=['OPTIONS'])
def send_peer_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")


@app.route('/send-peer', methods=['POST'])
def send_peer(headers="guest", body="anonymous"):
    """
    Send message to a specific peer (via tracker notification).
    
    Note: In true P2P, direct messaging should be done via TCP socket.
    This API can be used for:
    - Notification/coordination purposes
    - Web interface that cannot create TCP sockets directly
    
    Request body (JSON):
    {
        "from_username": "alice",
        "to_username": "bob",
        "message": "Hello Bob!"
    }
    
    Response (JSON):
    {
        "status": "success",
        "message": "Message notification sent",
        "target_peer": {"username": "bob", "ip": "127.0.0.1", "port": 9101}
    }
    
    :param headers (str): The request headers
    :param body (str): JSON request body
    :return: JSON response with target peer info
    """
    print("[ChatApp] Send-peer request received")
    
    try:
        if not body or body == "anonymous":
            return json.dumps({"status": "error", "message": "Missing request body"})
        
        data = json.loads(body)
        from_username = data.get("from_username", "")
        to_username = data.get("to_username", "")
        message = data.get("message", "")
        
        if not from_username or not to_username:
            return json.dumps({"status": "error", "message": "From and to usernames required"})
        
        # Find target peer
        target_peer = None
        
        with peers_lock:
            for peer in peers_list:
                if peer["username"] == to_username:
                    target_peer = {
                        "username": peer["username"],
                        "ip": peer["ip"],
                        "port": peer["port"]
                    }
                    break
        
        if not target_peer:
            return json.dumps({
                "status": "error",
                "message": "Target peer '{}' not found".format(to_username)
            })
        
        # In true P2P, actual message sending happens via direct TCP connection
        # This API just provides peer info for connection
        response = {
            "status": "success",
            "message": "Peer info retrieved for direct messaging",
            "target_peer": target_peer,
            "note": "Actual P2P messaging should be done via direct TCP socket connection"
        }
        
        print("[ChatApp] Send-peer: {} -> {} ({}:{})".format(
            from_username, to_username, target_peer["ip"], target_peer["port"]))
        
        return json.dumps(response)
    
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON"})
    except Exception as e:
        print("[ChatApp] Error in send-peer: {}".format(e))
        return json.dumps({"status": "error", "message": str(e)})


if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(
        prog='ChatApp Tracker Server',
        description='Hybrid Chat Application - Tracker Server',
        epilog='Manages peer registration and discovery'
    )
    parser.add_argument('--server-ip', default='0.0.0.0', help='IP address to bind')
    parser.add_argument('--server-port', type=int, default=PORT, help='Port number')
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    print("="*60)
    print("Starting Chat Tracker Server")
    print("IP: {}".format(ip))
    print("Port: {}".format(port))
    print("="*60)

    # Prepare and launch the chat tracker server
    app.prepare_address(ip, port)
    app.run()

