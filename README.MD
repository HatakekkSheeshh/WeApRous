# Assignment 1 - HTTP Server and Chat Application

**HCMC University of Technology**  
**Faculty of Computer Science & Engineering**  
**Course: Computer Networks (CO3094)**  
**Date: October 2025**

---

## 📋 Mục lục

1. [Tổng quan](#tổng-quan)
2. [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
3. [Cài đặt](#cài-đặt)
4. [Hướng dẫn sử dụng](#hướng-dẫn-sử-dụng)
5. [Demo Scenarios](#demo-scenarios)
6. [API Documentation](#api-documentation)
7. [Testing](#testing)
8. [Kết quả đạt được](#kết-quả-đạt-được)

---

## 🎯 Tổng quan

Project này implement một **HTTP server** kết hợp **hybrid chat application**, bao gồm:

### **Task 1: HTTP Server with Cookie Session (3 điểm)**
- ✅ Cookie-based authentication
- ✅ Session management
- ✅ Access control cho protected resources

### **Task 2: Hybrid Chat Application (4 điểm)**
- ✅ **Client-Server paradigm**: Tracker server quản lý peers
- ✅ **Peer-to-Peer paradigm**: Direct messaging không qua server
- ✅ **Channel management**: Join channels, broadcast messages
- ✅ **Concurrency**: Thread-safe operations
- ✅ **Error handling**: Robust error recovery

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────┐
│          HTTP Server Layer                      │
│  ┌──────────┐        ┌─────────────┐           │
│  │  Proxy   │───────►│   Backend   │           │
│  │  :8080   │        │   :9000     │           │
│  └──────────┘        └─────────────┘           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│       Chat Application Layer                    │
│  ┌──────────────────────────────────┐           │
│  │   Chat Tracker Server :8001      │           │
│  │   - Peer registration            │           │
│  │   - Channel management           │           │
│  │   - Peer discovery               │           │
│  └──────────────┬───────────────────┘           │
│                 │                                │
│        ┌────────┴────────┐                      │
│        │                 │                      │
│  ┌─────▼─────┐     ┌─────▼─────┐               │
│  │  Peer A   │◄───►│  Peer B   │               │
│  │  :9101    │  P2P│  :9102    │               │
│  └───────────┘     └───────────┘               │
└─────────────────────────────────────────────────┘
```

---

## 📦 Cài đặt

### **Yêu cầu hệ thống:**
- Python 2.7 hoặc Python 3.x
- macOS, Linux, hoặc Windows
- Không cần cài thêm thư viện (chỉ dùng standard library)

### **Cấu trúc thư mục:**
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

## 🚀 Hướng dẫn sử dụng

### **1. Test Cookie Session (Task 1)**

#### **Bước 1: Start Backend Server**
```bash
cd /Users/vuhaituan/Downloads/CO3094-weaprous2
python start_backend.py --server-ip 0.0.0.0 --server-port 9000
```

#### **Bước 2: Start Proxy Server**
```bash
# Terminal mới
python start_proxy.py --server-ip 0.0.0.0 --server-port 8080
```

#### **Bước 3: Test với Browser**
1. Mở browser (Incognito mode khuyến nghị)
2. Truy cập: `http://127.0.0.1:8080/`
   - ❌ Kết quả: 401 Unauthorized (chưa có cookie)
3. Truy cập: `http://127.0.0.1:8080/login.html`
   - ✅ Hiển thị login form
4. Login với:
   - Username: `admin`
   - Password: `password`
   - ✅ Kết quả: Set cookie và redirect đến index.html
5. Truy cập lại: `http://127.0.0.1:8080/`
   - ✅ Kết quả: 200 OK (có cookie hợp lệ)

#### **Bước 4: Test với curl**
```bash
# Test 1: Truy cập không có cookie
curl -v http://127.0.0.1:8080/
# Expected: 401 Unauthorized

# Test 2: Login
curl -X POST http://127.0.0.1:8080/login \
  -d "username=admin&password=password" \
  -c cookies.txt -v
# Expected: 200 OK, Set-Cookie: auth=true

# Test 3: Truy cập với cookie
curl -b cookies.txt http://127.0.0.1:8080/
# Expected: 200 OK, hiển thị index.html
```

---

### **2. Test Chat Application (Task 2)**

#### **Bước 1: Start Chat Tracker Server**
```bash
python start_chatapp.py --server-ip 0.0.0.0 --server-port 8001
```

**Kết quả:**
```
============================================================
Starting Chat Tracker Server
IP: 0.0.0.0
Port: 8001
============================================================
[Backend] Listening on port 8001
```

#### **Bước 2: Test APIs**
```bash
# Test Login
curl -X POST http://127.0.0.1:8001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
# Expected: {"status": "success", "token": "token_admin"}

# Test Register
curl -X POST http://127.0.0.1:8001/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}'
# Expected: {"status": "success", "message": "User registered successfully"}

# Test Peer Registration
curl -X POST http://127.0.0.1:8001/submit-info \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","ip":"127.0.0.1","port":9101,"channels":["general"]}'
# Expected: {"status": "success", "peer_id": 0, "total_peers": 1}

# Test Join Channel
curl -X POST http://127.0.0.1:8001/add-list \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","channel":"tech-talk"}'
# Expected: {"status": "success", "channel": "tech-talk", "members": ["alice"]}

# Test Get Peer List
curl -X POST http://127.0.0.1:8001/get-list \
  -H "Content-Type: application/json" \
  -d '{}'
# Expected: {"status": "success", "peers": [...], "channels": {...}}

# Test Server Status
curl http://127.0.0.1:8001/status
# Expected: {"status": "online", "stats": {...}}
```

#### **Bước 3: Start Peer Clients**

**Terminal 1 - Alice:**
```bash
python peer_client.py --username alice --peer-port 9101 --tracker-ip 127.0.0.1 --tracker-port 8001
```

**Trong Alice terminal:**
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

**Terminal 2 - Bob:**
```bash
python peer_client.py --username bob --peer-port 9102 --tracker-ip 127.0.0.1 --tracker-port 8001
```

**Trong Bob terminal:**
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

**Quay lại Alice terminal (tự động hiển thị):**
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

#### **Bước 4: Test Broadcast**

**Terminal 3 - Charlie:**
```bash
python peer_client.py --username charlie --peer-port 9103 --tracker-ip 127.0.0.1 --tracker-port 8001
```

**Trong Alice terminal:**
```
> connect bob 127.0.0.1 9102
> connect charlie 127.0.0.1 9103
> broadcast Hello everyone! This is Alice
[Peer] Broadcasted to 2 peers: Hello everyone! This is Alice
```

**Kết quả:**
- Bob và Charlie đều nhận được broadcast message ✅
