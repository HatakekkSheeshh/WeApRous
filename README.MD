# Assignment 1 - HTTP Server and Chat Application

**HCMC University of Technology**  
**Faculty of Computer Science & Engineering**  
**Course: Computer Networks (CO3094)**  
**Date: October 2025**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation](#installation)
4. [Usage Guide](#usage-guide)
5. [Demo Scenarios](#demo-scenarios)
6. [API Documentation](#api-documentation)
7. [Testing](#testing)
8. [Results](#results)

---

## 🎯 Overview

This project implements an **HTTP server** combined with a **hybrid chat application**, including:

### Task 1: HTTP Server with Cookie Session (3 points)
- ✅ Cookie-based authentication
- ✅ Session management
- ✅ Access control for protected resources

### Task 2: Hybrid Chat Application (4 points)
- ✅ Client-Server paradigm: Tracker server manages peers
- ✅ Peer-to-Peer paradigm: Direct messaging without the server
- ✅ Channel management: Join channels, broadcast messages
- ✅ Concurrency: Thread-safe operations
- ✅ Error handling: Robust recovery

---

## 🏗️ System Architecture

```
┌───────────────────────────────────────┐
│          HTTP Server Layer            │
│  ┌──────────┐        ┌─────────────┐  │
│  │  Proxy   │───────►│   Backend   │  │
│  │  :8080   │        │   :9000     │  │
│  └──────────┘        └─────────────┘  │
└───────────────────────────────────────┘

┌─────────────────────────────────────┐
│       Chat Application Layer        │
│  ┌───────────────────────────────┐  │
│  │   Chat Tracker Server :8001   │  │
│  │   - Peer registration         │  │
│  │   - Channel management        │  │
│  │   - Peer discovery            │  │
│  └──────────────┬────────────────┘  │
│                 │                   │
│        ┌────────┴────────┐          │
│        │                 │          │
│  ┌─────▼─────┐     ┌─────▼─────┐    │
│  │  Peer A   │◄───►│  Peer B   │    │
│  │  :9101    │  P2P│  :9102    │    │
│  └───────────┘     └───────────┘    │
└─────────────────────────────────────┘
```

---

## 📦 Installation

### System Requirements
- Python 2.7 or Python 3.x
- macOS, Linux, or Windows
- No extra dependencies required (standard library only)

### Directory Structure
```
CO3094-weaprous2/
├── daemon/                    # Framework modules
│   ├── __init__.py
│   ├── backend.py            # Backend server
│   ├── proxy.py              # Proxy server
│   ├── request.py            # HTTP request handling
│   ├── response.py           # HTTP response building
│   ├── httpadapter.py        # HTTP adapter (Task 1 implementation)
│   ├── weaprous.py           # WeApRous framework
│   └── dictionary.py         # Case-insensitive dict
├── www/                      # Static HTML pages
│   ├── index.html           # Protected page
│   ├── login.html           # Login form
│   └── chat.html            # Chat UI (bonus)
├── static/                   # Static assets
│   ├── css/
│   ├── images/
│   └── js/
├── config/
│   └── proxy.conf           # Proxy configuration
├── start_proxy.py           # Start proxy server
├── start_backend.py         # Start backend server
├── start_chatapp.py         # ⭐ Chat Tracker Server (Task 2)
├── peer_client.py           # ⭐ P2P Peer Client (Task 2)
├── test_chat.py             # ⭐ Automated tests
└── README.md                # This file
```

---

## 🚀 Usage Guide

### 1. Test Cookie Session (Task 1)

#### Step 1: Start Backend Server
```bash
cd /Users/vuhaituan/Downloads/WeApRous-main
python start_backend.py --server-ip 127.0.0.1 --server-port 9000
```

**Expected Output:**
```
[Backend] Listening on port 9000
```

#### Step 2: Start Proxy Server
```bash
# New terminal
python start_proxy.py --server-ip 0.0.0.0 --server-port 8080
```

**Expected Output:**
```
[Proxy] Listening on port 8080
```

#### Step 3: Test with Browser
1. Open a browser (Incognito mode recommended to avoid cached cookies)
2. Visit: `http://localhost:8080/` or `http://127.0.0.1:8080/`
   - ❌ Expected: 401 Unauthorized (no cookie yet)
3. Visit: `http://localhost:8080/login.html`
   - ✅ Shows login form
4. Login with:
   - Username: `admin`
   - Password: `password`
   - ✅ Expected: Set cookie and redirect to index.html
5. Visit again: `http://localhost:8080/`
   - ✅ Expected: 200 OK (valid cookie)

#### Step 4: Test with curl
```bash
# Test 1: Without cookie
curl -v http://localhost:8080/
# Expected: 401 Unauthorized

# Test 2: Login
curl -X POST http://localhost:8080/login \
  -d "username=admin&password=password" \
  -c cookies.txt -v
# Expected: 200 OK, Set-Cookie: auth=true

# Test 3: With cookie
curl -b cookies.txt http://localhost:8080/
# Expected: 200 OK, shows index.html
```

---

### 2. Test Chat Application (Task 2)

#### Option A: Test via CLI (Command Line Interface)

##### Step 1: Start Chat Tracker Server
```bash
# Terminal 1
cd /Users/vuhaituan/Downloads/WeApRous-main
python start_chatapp.py --server-ip 0.0.0.0 --server-port 8001
```

**Expected Output:**
```
============================================================
Starting Chat Tracker Server
IP: 0.0.0.0
Port: 8001
============================================================
[Backend] Listening on port 8001
```

##### Step 2: Test APIs with curl
```bash
# Login
curl -X POST http://127.0.0.1:8001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
# Expected: {"status": "success", "token": "token_admin"}

# Register new user
curl -X POST http://127.0.0.1:8001/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}'
# Expected: {"status": "success", "message": "User registered successfully"}

# Peer Registration
curl -X POST http://127.0.0.1:8001/submit-info \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","ip":"127.0.0.1","port":9101,"channels":["general"]}'
# Expected: {"status": "success", "peer_id": 0, "total_peers": 1}

# Join Channel
curl -X POST http://127.0.0.1:8001/add-list \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","channel":"tech-talk"}'
# Expected: {"status": "success", "channel": "tech-talk", "members": ["alice"]}

# Get Peer List
curl -X POST http://127.0.0.1:8001/get-list \
  -H "Content-Type: application/json" \
  -d '{}'
# Expected: {"status": "success", "peers": [...], "channels": {...}}

# Server Status
curl http://127.0.0.1:8001/status
# Expected: {"status": "online", "stats": {...}}
```

##### Step 3: Start Peer Clients (CLI)

**Terminal 2 - Alice:**
```bash
python peer_client.py --username alice --peer-port 9101 --tracker-ip 127.0.0.1 --tracker-port 8001
```

**In Alice terminal:**
```
> join general
[Peer] Joined channel: general

> join tech
[Peer] Joined channel: tech

> list
[Peer] Retrieved X peers from tracker
Active peers:
  - bob (127.0.0.1:9102)
```

**Terminal 3 - Bob:**
```bash
python peer_client.py --username bob --peer-port 9102 --tracker-ip 127.0.0.1 --tracker-port 8001
```

**In Bob terminal:**
```
> join general

> list
Active peers:
  - alice (127.0.0.1:9101)

> connect alice 127.0.0.1 9101
[Peer] Connecting to peer alice at 127.0.0.1:9101
[Peer] Connected to peer: alice

> send alice Hello Alice! This is Bob
[Peer] Sent message to alice: Hello Alice! This is Bob
```

**Back to Alice terminal (auto display):**
```
[Peer] New P2P connection from ('127.0.0.1', xxxxx)
[Peer] Handshake from peer: bob
[Peer] Message from bob: Hello Alice! This is Bob
```

**Alice reply:**
```
> send bob Hi Bob! Nice to hear from you
[Peer] Sent message to bob: Hi Bob! Nice to hear from you

> messages
Message history:
  [direct from bob] Hello Alice! This is Bob
```

##### Step 4: Test Broadcast (CLI)

**Terminal 4 - Charlie:**
```bash
python peer_client.py --username charlie --peer-port 9103 --tracker-ip 127.0.0.1 --tracker-port 8001
```

**In Alice terminal:**
```
> connect bob 127.0.0.1 9102
> connect charlie 127.0.0.1 9103
> broadcast Hello everyone! This is Alice
[Peer] Broadcasted to 2 peers: Hello everyone! This is Alice
```

**Result:**
- Both Bob and Charlie receive the broadcast message ✅

---

#### Option B: Test via Web Interface

##### Step 1: Start All Services

**Terminal 1: Proxy Server**
```bash
python start_proxy.py --server-ip 0.0.0.0 --server-port 8080
```

**Terminal 2: Backend Server**
```bash
python start_backend.py --server-ip 127.0.0.1 --server-port 9000
```

**Terminal 3: Tracker Server**
```bash
python start_chatapp.py --server-ip 0.0.0.0 --server-port 8001
```

**Terminal 4: WebPeer Bridge Service**
```bash
python start_webpeer.py --server-ip 0.0.0.0 --server-port 8002
```

**Expected Output:**
```
[Proxy] Listening on port 8080
[Backend] Listening on port 9000
[ChatApp] Starting Chat Tracker Server on port 8001
[WebPeer] Starting WebPeer Bridge Service on port 8002
```

##### Step 2: Open Web Interface

1. **Open browser:** `http://localhost:8080/chat.html`

2. **Step 1: Session Login (Task 1)**
   - Username: `admin`
   - Password: `password`
   - Click "Login (Cookie Session)"
   - ✅ Expected: Cookie session login successful! Page reloads and shows Step 2.

3. **Step 2: Register Peer (Task 2)**
   - Your Username (for P2P): `alice` (this is your peer identity)
   - Tracker Server IP: `127.0.0.1`
   - Tracker Server Port: `8001`
   - Your P2P Port: `9100` (must be unique per peer)
   - WebPeer Service IP: `127.0.0.1`
   - WebPeer Service Port: `8002`
   - Click "Register Peer & Start Chat"
   - ✅ Expected: Peer registered successfully! Chat interface appears.

4. **Join Channel**
   - In the sidebar, go to "Channels" tab
   - Type channel name: `general` (or any name)
   - Click "Join Channel"
   - ✅ Expected: Channel joined, P2P connections established automatically

5. **Send Messages**
   - Select channel from sidebar (e.g., `#general`)
   - Type message in input field at bottom
   - Click "Send" or press Enter
   - ✅ Expected: Message appears in chat window

##### Step 3: Test with Multiple Users (2 Peers)

**Browser Window 1 - Alice:**
1. Open: `http://localhost:8080/chat.html`
2. Login: `admin` / `password`
3. Register peer: 
   - Username: `alice`
   - P2P Port: `9100`
   - Tracker: `127.0.0.1:8001`
   - WebPeer: `127.0.0.1:8002`
4. Join channel: `general`

**Browser Window 2 (Incognito) - Bob:**
1. Open: `http://localhost:8080/chat.html` (in Incognito or different browser)
2. Login: `admin` / `password`
3. Register peer:
   - Username: `bob`
   - P2P Port: `9200` ⚠️ **Must be different from Alice!**
   - Tracker: `127.0.0.1:8001`
   - WebPeer: `127.0.0.1:8002`
4. Join channel: `general`

**Result:**
- Both Alice and Bob see each other in peer list ✅
- Click "Peers" tab → Click "Refresh Peers" → See each other
- Messages sent in channel appear in both browsers ✅
- Direct peer-to-peer messages work ✅

##### Step 4: Features

**Channel Chat:**
- Join multiple channels
- Broadcast messages to all peers in a channel
- Messages are sent via P2P (not through tracker)

**Direct Peer Messaging:**
- Click on a peer in "Peers" tab
- Send direct messages to that peer
- Messages go peer-to-peer directly

**Peer Discovery:**
- Click "Refresh Peers" to see all active peers
- Automatically connects to peers in same channels

##### Step 5: Verify P2P Communication

**Check Terminal 4 (WebPeer Bridge):**
```
[WebPeer] Init peer request received for user: alice
[Peer] Started P2P server on 127.0.0.1:9100
[WebPeer] Join channel request received
[Peer] Joined channel: general
[Peer] Connecting to peers in channel...
[Peer] Connected to peer: bob
```

**Check Terminal 3 (Tracker Server):**
```
[ChatApp] Submit-info request received
[ChatApp] Peer registered: alice (127.0.0.1:9100)
[ChatApp] Add to channel request received
[ChatApp] Channel general now has 2 members
[ChatApp] Get-list request received
```

**Result:**
- P2P TCP connections established directly between peers ✅
- Messages go peer-to-peer, not through tracker ✅
- Tracker only manages peer discovery and channel membership ✅
