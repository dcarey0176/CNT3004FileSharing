# CNT3004 – Socket-Based Networked File Sharing Cloud Server Project

This project implements a multithreaded, socket-based file sharing system using Python.

## How to Run

### Server (Computer #1)
```bash
python server/server_main.py
```

### Client (Computer #2 or #3)
```bash
python client/client_main.py
```

### Connect Command
In the client terminal:
```
connect <server_ip> <port>
```
Example:
```
connect 192.168.1.10 5000
```

## Features
- Authentication with encryption
- Upload, download, delete, directory, and subfolder operations
- Performance logging and analysis

## Network Setup Guide
1. Connect all computers to the same network (e.g., campus Wi-Fi or LAN).
2. Find the server computer’s IP address:
   - Windows: `ipconfig`
   - macOS/Linux: `ifconfig`
3. Clients use that IP when connecting (e.g., `connect 192.168.1.10 5000`).
4. Ensure firewall allows inbound connections on the selected port (default 5000).

## Authors
- Add team members here
