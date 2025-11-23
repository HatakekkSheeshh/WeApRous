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
start_webpeer
~~~~~~~~~~~~~~~~~

This module implements a hybrid web-based peer service that bridges between
web interface (HTTP) and P2P communication (TCP sockets).

The service:
- Runs a WeApRous webapp to serve HTTP requests from web interface
- Manages a PeerClient instance for each user session
- Bridges HTTP API calls to P2P operations
- Allows web interface to participate in P2P messaging

This enables web interfaces to use P2P paradigm while maintaining
the client-server paradigm for API communication.
"""

import json
import socket
import argparse
import threading
from daemon.weaprous import WeApRous
from peer_client import PeerClient

PORT = 8002  # Default port for web peer service

# Global peer instances: {username: PeerClient}
peer_instances = {}
peer_instances_lock = threading.Lock()

app = WeApRous()

# CORS OPTIONS handlers
@app.route('/init-peer', methods=['OPTIONS'])
def init_peer_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/init-peer', methods=['POST'])
def init_peer(headers="guest", body="anonymous"):
    """
    Initialize a PeerClient instance for a user.
    
    Expected body: {
        "username": str,
        "peer_ip": str,
        "peer_port": int,
        "tracker_ip": str,
        "tracker_port": int
    }
    
    Response: {"status": "success"/"failed", "message": str}
    """
    print("[WebPeer] Init peer request received")
    
    try:
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        peer_ip = data.get("peer_ip", "0.0.0.0")
        peer_port = data.get("peer_port", 0)
        tracker_ip = data.get("tracker_ip", "127.0.0.1")
        tracker_port = data.get("tracker_port", 8001)
        
        if not username or not peer_port:
            return json.dumps({
                "status": "failed",
                "message": "Missing username or peer_port"
            })
        
        with peer_instances_lock:
            # Close existing instance if any
            if username in peer_instances:
                try:
                    peer_instances[username].stop()
                except:
                    pass
            
            # Create new PeerClient instance
            peer = PeerClient(
                username=username,
                peer_ip=peer_ip,
                peer_port=peer_port,
                tracker_ip=tracker_ip,
                tracker_port=tracker_port
            )
            
            # Start peer
            peer.start()
            
            # Register with tracker
            peer.register_with_tracker()
            
            # Store instance
            peer_instances[username] = peer
            
            print("[WebPeer] Initialized peer for user: {}".format(username))
        
        response = {
            "status": "success",
            "message": "Peer initialized successfully"
        }
        return ("200 OK", {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }, json.dumps(response))
    
    except Exception as e:
        print("[WebPeer] Error initializing peer: {}".format(e))
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@app.route('/connect-peer', methods=['OPTIONS'])
def connect_peer_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/connect-peer', methods=['POST'])
def connect_peer(headers="guest", body="anonymous"):
    """
    Connect to another peer via P2P.
    
    Expected body: {
        "username": str,
        "peer_username": str,
        "peer_ip": str,
        "peer_port": int
    }
    
    Response: {"status": "success"/"failed", "message": str}
    """
    print("[WebPeer] Connect peer request received")
    
    try:
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        peer_username = data.get("peer_username", "")
        peer_ip = data.get("peer_ip", "")
        peer_port = data.get("peer_port", 0)
        
        if not username or not peer_username or not peer_ip or not peer_port:
            return json.dumps({
                "status": "failed",
                "message": "Missing required fields"
            })
        
        with peer_instances_lock:
            if username not in peer_instances:
                return json.dumps({
                    "status": "failed",
                    "message": "Peer not initialized. Call /init-peer first"
                })
            
            peer = peer_instances[username]
        
        success = peer.connect_peer(peer_username, peer_ip, peer_port)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": "Connected to peer: {}".format(peer_username)
            })
        else:
            return json.dumps({
                "status": "failed",
                "message": "Failed to connect to peer: {}".format(peer_username)
            })
    
    except Exception as e:
        print("[WebPeer] Error connecting peer: {}".format(e))
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


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
    Send message to a peer via P2P.
    
    Expected body: {
        "username": str,
        "peer_username": str,
        "message": str,
        "channel": str (optional)
    }
    
    Response: {"status": "success"/"failed", "message": str}
    """
    print("[WebPeer] Send peer message request received")
    
    try:
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        peer_username = data.get("peer_username", "")
        message = data.get("message", "")
        channel = data.get("channel", "direct")
        
        if not username or not peer_username or not message:
            return json.dumps({
                "status": "failed",
                "message": "Missing required fields"
            })
        
        with peer_instances_lock:
            if username not in peer_instances:
                return json.dumps({
                    "status": "failed",
                    "message": "Peer not initialized"
                })
            
            peer = peer_instances[username]
        
        success = peer.send_peer(peer_username, message, channel)
        
        if success:
            return json.dumps({
                "status": "success",
                "message": "Message sent"
            })
        else:
            return json.dumps({
                "status": "failed",
                "message": "Failed to send message"
            })
    
    except Exception as e:
        print("[WebPeer] Error sending message: {}".format(e))
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


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
    Broadcast message to all connected peers.
    
    Expected body: {
        "username": str,
        "message": str,
        "channel": str (optional)
    }
    
    Response: {"status": "success", "sent_count": int}
    """
    print("[WebPeer] Broadcast peer message request received")
    
    try:
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        message = data.get("message", "")
        channel = data.get("channel", "broadcast")
        
        if not username or not message:
            return json.dumps({
                "status": "failed",
                "message": "Missing required fields"
            })
        
        with peer_instances_lock:
            if username not in peer_instances:
                return json.dumps({
                    "status": "failed",
                    "message": "Peer not initialized"
                })
            
            peer = peer_instances[username]
        
        sent_count = peer.broadcast_peer(message, channel)
        
        return json.dumps({
            "status": "success",
            "sent_count": sent_count,
            "message": "Broadcasted to {} peers".format(sent_count)
        })
    
    except Exception as e:
        print("[WebPeer] Error broadcasting: {}".format(e))
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@app.route('/get-messages', methods=['OPTIONS'])
def get_messages_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/get-messages', methods=['POST'])
def get_messages(headers="guest", body="anonymous"):
    """
    Get message history from peer.
    
    Expected body: {
        "username": str,
        "channel": str (optional)
    }
    
    Response: {"status": "success", "messages": [...]}
    """
    print("[WebPeer] Get messages request received")
    
    try:
        data = json.loads(body) if body and body != "anonymous" else {}
        username = data.get("username", "")
        channel = data.get("channel", None)
        
        if not username:
            return json.dumps({
                "status": "failed",
                "message": "Missing username"
            })
        
        with peer_instances_lock:
            if username not in peer_instances:
                return json.dumps({
                    "status": "success",
                    "messages": []
                })
            
            peer = peer_instances[username]
        
        messages = peer.get_messages(channel)
        
        return json.dumps({
            "status": "success",
            "messages": messages
        })
    
    except Exception as e:
        print("[WebPeer] Error getting messages: {}".format(e))
        return json.dumps({
            "status": "error",
            "message": str(e),
            "messages": []
        })


@app.route('/join-channel', methods=['OPTIONS'])
def join_channel_options(headers="guest", body="anonymous"):
    """Handle OPTIONS preflight request for CORS."""
    return ("200 OK", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400"
    }, "")

@app.route('/join-channel', methods=['POST'])
def join_channel(headers="guest", body="anonymous"):
    """
    Join a channel and auto-connect to peers.
    
    Expected body: {
        "username": str,
        "channel": str
    }
    
    Response: {"status": "success"/"failed", "message": str}
    """
    print("[WebPeer] Join channel request received")
    print("[WebPeer] Request body: {}".format(body))
    
    try:
        if not body or body == "anonymous":
            print("[WebPeer] Error: Empty body")
            return json.dumps({
                "status": "failed",
                "message": "Missing request body"
            })
        
        data = json.loads(body)
        username = data.get("username", "")
        channel = data.get("channel", "")
        
        print("[WebPeer] Parsed data - username: {}, channel: {}".format(username, channel))
        
        if not username or not channel:
            print("[WebPeer] Error: Missing username or channel")
            return json.dumps({
                "status": "failed",
                "message": "Missing username or channel"
            })
        
        with peer_instances_lock:
            if username not in peer_instances:
                print("[WebPeer] Error: Peer '{}' not initialized".format(username))
                return json.dumps({
                    "status": "failed",
                    "message": "Peer not initialized. Call /init-peer first"
                })
            
            peer = peer_instances[username]
        
        print("[WebPeer] Calling peer.join_channel('{}') for user '{}'...".format(channel, username))
        
        try:
            success = peer.join_channel(channel)
            print("[WebPeer] peer.join_channel returned: {}".format(success))
        except Exception as peer_error:
            print("[WebPeer] Exception in peer.join_channel: {}".format(peer_error))
            import traceback
            traceback.print_exc()
            return json.dumps({
                "status": "error",
                "message": "Error in peer.join_channel: {}".format(str(peer_error))
            })
        
        if success:
            print("[WebPeer] Successfully joined channel '{}' for user '{}'".format(channel, username))
            return json.dumps({
                "status": "success",
                "message": "Joined channel: {}".format(channel)
            })
        else:
            print("[WebPeer] Failed to join channel '{}' for user '{}'".format(channel, username))
            return json.dumps({
                "status": "failed",
                "message": "Failed to join channel. Check tracker connection and peer status."
            })
    
    except json.JSONDecodeError as e:
        print("[WebPeer] JSON decode error: {}".format(e))
        return json.dumps({
            "status": "error",
            "message": "Invalid JSON: {}".format(str(e))
        })
    except Exception as e:
        print("[WebPeer] Unexpected error joining channel: {}".format(e))
        import traceback
        traceback.print_exc()
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@app.route('/status', methods=['GET'])
def status(headers="guest", body="anonymous"):
    """Get service status."""
    with peer_instances_lock:
        active_peers = len(peer_instances)
    
    return json.dumps({
        "status": "online",
        "active_peer_instances": active_peers,
        "service": "WebPeer Bridge"
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='WebPeer Bridge Service',
        description='Bridges web interface to P2P communication',
        epilog='Manages PeerClient instances for web users'
    )
    parser.add_argument('--server-ip', default='0.0.0.0', help='IP address to bind')
    parser.add_argument('--server-port', type=int, default=PORT, help='Port number')
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    print("="*60)
    print("Starting WebPeer Bridge Service")
    print("IP: {}".format(ip))
    print("Port: {}".format(port))
    print("="*60)
    print("\nThis service bridges web interface to P2P communication.")
    print("Web interface can now use P2P messaging through HTTP API.\n")

    app.prepare_address(ip, port)
    app.run()

