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
peer_client
~~~~~~~~~~~~~~~~~

This module implements the Peer-to-Peer client for the hybrid chat application.

Each peer can:
- Connect to the tracker server (client-server paradigm)
- Accept incoming P2P connections from other peers
- Initiate P2P connections to other peers
- Send/receive messages directly (P2P paradigm)
- Broadcast messages to all connected peers
"""

import socket
import json
import threading
import argparse
import time
from datetime import datetime


class PeerClient:
    """
    Peer client for hybrid chat application.
    
    Combines client-server communication (with tracker) and 
    peer-to-peer communication (with other peers).
    """
    
    def __init__(self, username, peer_ip, peer_port, tracker_ip, tracker_port):
        """
        Initialize a new peer client.
        
        :param username (str): Username of this peer
        :param peer_ip (str): IP address for P2P listening
        :param peer_port (int): Port for P2P listening
        :param tracker_ip (str): Tracker server IP
        :param tracker_port (int): Tracker server port
        """
        self.username = username
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.tracker_ip = tracker_ip
        self.tracker_port = tracker_port
        
        # P2P connections
        self.peer_connections = {}  # {username: socket}
        self.peer_info = {}  # {username: {"ip": str, "port": int}}
        
        # Channels this peer has joined
        self.channels = []
        
        # Message history
        self.messages = []  # [{"from": str, "channel": str, "message": str, "time": str}]
        
        # Thread locks
        self.connections_lock = threading.Lock()
        self.messages_lock = threading.Lock()
        
        # Server socket for accepting incoming P2P connections
        self.server_socket = None
        self.running = False
    
    
    def start(self):
        """Start the peer client - begin listening for P2P connections."""
        self.running = True
        
        # Start P2P server thread
        server_thread = threading.Thread(target=self._run_p2p_server)
        server_thread.daemon = True
        server_thread.start()
        
        print("[Peer] Started P2P server on {}:{}".format(self.peer_ip, self.peer_port))
    
    
    def stop(self):
        """Stop the peer client."""
        self.running = False
        
        # Close all peer connections
        with self.connections_lock:
            for username, conn in self.peer_connections.items():
                try:
                    conn.close()
                except:
                    pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("[Peer] Stopped")
    
    
    def _run_p2p_server(self):
        """Run P2P server to accept incoming connections from other peers."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.peer_ip, self.peer_port))
            self.server_socket.listen(10)
            
            print("[Peer] Listening for P2P connections on {}:{}".format(
                self.peer_ip, self.peer_port))
            
            while self.running:
                try:
                    # Set timeout to periodically check self.running
                    self.server_socket.settimeout(1.0)
                    conn, addr = self.server_socket.accept()
                    
                    # Handle new peer connection in separate thread
                    handler_thread = threading.Thread(
                        target=self._handle_peer_connection,
                        args=(conn, addr)
                    )
                    handler_thread.daemon = True
                    handler_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print("[Peer] Error accepting connection: {}".format(e))
        
        except Exception as e:
            print("[Peer] Error starting P2P server: {}".format(e))
    
    
    def _handle_peer_connection(self, conn, addr):
        """
        Handle incoming P2P connection from another peer.
        
        :param conn (socket): Connection socket
        :param addr (tuple): Address of the connecting peer
        """
        print("[Peer] New P2P connection from {}".format(addr))
        
        try:
            # Receive handshake message
            data = conn.recv(4096).decode('utf-8')
            
            if not data:
                conn.close()
                return
            
            message = json.loads(data)
            msg_type = message.get("type", "")
            
            if msg_type == "handshake":
                # Peer identification
                peer_username = message.get("username", "unknown")
                
                print("[Peer] Handshake from peer: {}".format(peer_username))
                
                # Store connection
                with self.connections_lock:
                    self.peer_connections[peer_username] = conn
                
                # Send handshake response
                response = {
                    "type": "handshake_ack",
                    "username": self.username,
                    "status": "connected"
                }
                conn.sendall(json.dumps(response).encode('utf-8'))
                
                # Continue listening for messages from this peer
                self._listen_to_peer(conn, peer_username)
            
            else:
                # Handle direct message
                self._process_peer_message(message)
                conn.close()
        
        except Exception as e:
            print("[Peer] Error handling peer connection: {}".format(e))
            try:
                conn.close()
            except:
                pass
    
    
    def _listen_to_peer(self, conn, peer_username):
        """
        Continuously listen for messages from a connected peer.
        
        :param conn (socket): Connection socket
        :param peer_username (str): Username of the peer
        """
        try:
            while self.running:
                conn.settimeout(1.0)
                try:
                    data = conn.recv(4096).decode('utf-8')
                    
                    if not data:
                        break
                    
                    message = json.loads(data)
                    self._process_peer_message(message)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    print("[Peer] Error receiving from {}: {}".format(peer_username, e))
                    break
        
        finally:
            # Remove connection
            with self.connections_lock:
                if peer_username in self.peer_connections:
                    del self.peer_connections[peer_username]
            
            try:
                conn.close()
            except:
                pass
            
            print("[Peer] Disconnected from peer: {}".format(peer_username))
    
    
    def _process_peer_message(self, message):
        """
        Process received message from peer.
        
        :param message (dict): Message data
        """
        msg_type = message.get("type", "")
        
        if msg_type == "chat":
            # Store message
            msg_data = {
                "from": message.get("from", "unknown"),
                "channel": message.get("channel", "direct"),
                "message": message.get("message", ""),
                "time": message.get("time", datetime.now().isoformat())
            }
            
            with self.messages_lock:
                self.messages.append(msg_data)
            
            print("[Peer] Message from {}: {}".format(
                msg_data["from"], msg_data["message"]))
        
        elif msg_type == "broadcast":
            # Handle broadcast message
            msg_data = {
                "from": message.get("from", "unknown"),
                "channel": message.get("channel", "broadcast"),
                "message": message.get("message", ""),
                "time": message.get("time", datetime.now().isoformat())
            }
            
            with self.messages_lock:
                self.messages.append(msg_data)
            
            print("[Peer] Broadcast from {}: {}".format(
                msg_data["from"], msg_data["message"]))
    
    
    def connect_peer(self, peer_username, peer_ip, peer_port):
        """
        Establish P2P connection to another peer.
        
        :param peer_username (str): Username of target peer
        :param peer_ip (str): IP address of target peer
        :param peer_port (int): Port of target peer
        :return: bool - True if connection successful
        """
        print("[Peer] Connecting to peer {} at {}:{}".format(
            peer_username, peer_ip, peer_port))
        
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_ip, peer_port))
            
            # Send handshake
            handshake = {
                "type": "handshake",
                "username": self.username
            }
            sock.sendall(json.dumps(handshake).encode('utf-8'))
            
            # Receive response
            response = sock.recv(4096).decode('utf-8')
            response_data = json.loads(response)
            
            if response_data.get("type") == "handshake_ack":
                # Store connection
                with self.connections_lock:
                    self.peer_connections[peer_username] = sock
                    self.peer_info[peer_username] = {
                        "ip": peer_ip,
                        "port": peer_port
                    }
                
                print("[Peer] Connected to peer: {}".format(peer_username))
                
                # Start listening thread for this peer
                listen_thread = threading.Thread(
                    target=self._listen_to_peer,
                    args=(sock, peer_username)
                )
                listen_thread.daemon = True
                listen_thread.start()
                
                return True
            else:
                sock.close()
                return False
        
        except Exception as e:
            print("[Peer] Failed to connect to {}: {}".format(peer_username, e))
            return False
    
    
    def send_peer(self, peer_username, message, channel="direct"):
        """
        Send message to a specific peer via P2P.
        
        :param peer_username (str): Target peer username
        :param message (str): Message content
        :param channel (str): Channel name (optional)
        :return: bool - True if sent successfully
        """
        with self.connections_lock:
            if peer_username not in self.peer_connections:
                print("[Peer] Not connected to peer: {}".format(peer_username))
                return False
            
            conn = self.peer_connections[peer_username]
        
        try:
            msg_data = {
                "type": "chat",
                "from": self.username,
                "channel": channel,
                "message": message,
                "time": datetime.now().isoformat()
            }
            
            conn.sendall(json.dumps(msg_data).encode('utf-8'))
            print("[Peer] Sent message to {}: {}".format(peer_username, message))
            return True
        
        except Exception as e:
            print("[Peer] Failed to send to {}: {}".format(peer_username, e))
            return False
    
    
    def broadcast_peer(self, message, channel="broadcast"):
        """
        Broadcast message to all connected peers.
        
        :param message (str): Message content
        :param channel (str): Channel name
        :return: int - Number of peers message was sent to
        """
        with self.connections_lock:
            peer_list = list(self.peer_connections.items())
        
        sent_count = 0
        
        for peer_username, conn in peer_list:
            try:
                msg_data = {
                    "type": "broadcast",
                    "from": self.username,
                    "channel": channel,
                    "message": message,
                    "time": datetime.now().isoformat()
                }
                
                conn.sendall(json.dumps(msg_data).encode('utf-8'))
                sent_count += 1
            
            except Exception as e:
                print("[Peer] Failed to broadcast to {}: {}".format(peer_username, e))
        
        print("[Peer] Broadcasted to {} peers: {}".format(sent_count, message))
        return sent_count
    
    
    def register_with_tracker(self):
        """
        Register this peer with the tracker server.
        
        :return: bool - True if registration successful
        """
        try:
            # Create HTTP POST request
            body = json.dumps({
                "username": self.username,
                "ip": self.peer_ip,
                "port": self.peer_port,
                "channels": self.channels
            })
            
            request = (
                "POST /submit-info HTTP/1.1\r\n"
                "Host: {}:{}\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: {}\r\n"
                "\r\n"
                "{}"
            ).format(self.tracker_ip, self.tracker_port, len(body), body)
            
            # Send to tracker
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.tracker_ip, self.tracker_port))
            sock.sendall(request.encode('utf-8'))
            
            # Receive response
            response = sock.recv(4096).decode('utf-8')
            sock.close()
            
            print("[Peer] Registered with tracker")
            print("[Peer] Response: {}".format(response[:200]))
            return True
        
        except Exception as e:
            print("[Peer] Failed to register with tracker: {}".format(e))
            return False
    
    
    def get_peer_list(self, channel=None):
        """
        Get list of peers from tracker.
        
        :param channel (str): Optional channel filter
        :return: list - List of peer information
        """
        try:
            # Create HTTP POST request
            body = json.dumps({
                "channel": channel
            }) if channel else "{}"
            
            request = (
                "POST /get-list HTTP/1.1\r\n"
                "Host: {}:{}\r\n"
                "Content-Type: application/json\r\n"
                "Content-Length: {}\r\n"
                "\r\n"
                "{}"
            ).format(self.tracker_ip, self.tracker_port, len(body), body)
            
            # Send to tracker
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.tracker_ip, self.tracker_port))
            sock.sendall(request.encode('utf-8'))
            
            # Receive response
            response = sock.recv(4096).decode('utf-8')
            sock.close()
            
            # Parse response
            if '\r\n\r\n' in response:
                body_part = response.split('\r\n\r\n', 1)[1]
                data = json.loads(body_part)
                
                if data.get("status") == "success":
                    peers = data.get("peers", [])
                    print("[Peer] Retrieved {} peers from tracker".format(len(peers)))
                    return peers
            
            return []
        
        except Exception as e:
            print("[Peer] Failed to get peer list: {}".format(e))
            return []
    
    
    def join_channel(self, channel):
        """
        Join a chat channel.
        
        :param channel (str): Channel name
        :return: bool - True if successful
        """
        try:
            # Create HTTP POST request
            body = json.dumps({
                "username": self.username,
                "channel": channel
            })
            
            request = (
                "POST /add-list HTTP/1.1\r\n"
                "Host: {}:{}\r\n"
                "Content-Type: application/json\r\n"
                "Content-Length: {}\r\n"
                "\r\n"
                "{}"
            ).format(self.tracker_ip, self.tracker_port, len(body), body)
            
            # Send to tracker
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.tracker_ip, self.tracker_port))
            sock.sendall(request.encode('utf-8'))
            
            # Receive response
            response = sock.recv(4096).decode('utf-8')
            sock.close()
            
            # Parse response
            if '\r\n\r\n' in response:
                body_part = response.split('\r\n\r\n', 1)[1]
                data = json.loads(body_part)
                
                if data.get("status") == "success":
                    if channel not in self.channels:
                        self.channels.append(channel)
                    print("[Peer] Joined channel: {}".format(channel))
                    return True
            
            return False
        
        except Exception as e:
            print("[Peer] Failed to join channel: {}".format(e))
            return False
    
    
    def get_messages(self, channel=None):
        """
        Get message history.
        
        :param channel (str): Optional channel filter
        :return: list - List of messages
        """
        with self.messages_lock:
            if channel:
                return [m for m in self.messages if m["channel"] == channel]
            else:
                return self.messages[:]


def main():
    """Example usage of PeerClient."""
    parser = argparse.ArgumentParser(
        prog='Peer Client',
        description='Hybrid Chat Application - Peer Client',
        epilog='P2P chat client'
    )
    parser.add_argument('--username', required=True, help='Your username')
    parser.add_argument('--peer-ip', default='0.0.0.0', help='Your IP for P2P')
    parser.add_argument('--peer-port', type=int, required=True, help='Your port for P2P')
    parser.add_argument('--tracker-ip', default='127.0.0.1', help='Tracker server IP')
    parser.add_argument('--tracker-port', type=int, default=8001, help='Tracker server port')
    
    args = parser.parse_args()
    
    # Create peer client
    peer = PeerClient(
        username=args.username,
        peer_ip=args.peer_ip,
        peer_port=args.peer_port,
        tracker_ip=args.tracker_ip,
        tracker_port=args.tracker_port
    )
    
    # Start peer
    peer.start()
    
    # Register with tracker
    peer.register_with_tracker()
    
    print("\n" + "="*60)
    print("Peer Client Started")
    print("Username: {}".format(args.username))
    print("P2P Address: {}:{}".format(args.peer_ip, args.peer_port))
    print("Tracker: {}:{}".format(args.tracker_ip, args.tracker_port))
    print("="*60)
    print("\nCommands:")
    print("  list - Get peer list")
    print("  join <channel> - Join a channel")
    print("  connect <username> <ip> <port> - Connect to a peer")
    print("  send <username> <message> - Send message to peer")
    print("  broadcast <message> - Broadcast to all peers")
    print("  messages - Show message history")
    print("  quit - Exit")
    print("="*60 + "\n")
    
    # Simple command loop
    try:
        while True:
            cmd = input("> ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            command = parts[0].lower()
            
            if command == "quit":
                break
            
            elif command == "list":
                peers = peer.get_peer_list()
                print("\nActive peers:")
                for p in peers:
                    print("  - {} ({}:{})".format(
                        p["username"], p["ip"], p["port"]))
                print("")
            
            elif command == "join" and len(parts) >= 2:
                channel = parts[1]
                peer.join_channel(channel)
            
            elif command == "connect" and len(parts) >= 4:
                username = parts[1]
                ip = parts[2]
                port = int(parts[3])
                peer.connect_peer(username, ip, port)
            
            elif command == "send" and len(parts) >= 3:
                username = parts[1]
                message = " ".join(parts[2:])
                peer.send_peer(username, message)
            
            elif command == "broadcast" and len(parts) >= 2:
                message = " ".join(parts[1:])
                peer.broadcast_peer(message)
            
            elif command == "messages":
                msgs = peer.get_messages()
                print("\nMessage history:")
                for m in msgs:
                    print("  [{} from {}] {}".format(
                        m["channel"], m["from"], m["message"]))
                print("")
            
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    
    finally:
        peer.stop()


if __name__ == "__main__":
    main()

