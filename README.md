# CNT3004 – Socket-Based Networked File Sharing Cloud Server Project

This project implements a multithreaded, socket-based file sharing system using Python.

## 📁 Project File Structure

<code>
CNT3004_FileSharing/
│
├── README.md # Overview, setup instructions, and network guide
├── requirements.txt # Python dependencies
├── .gitignore # Files and folders to ignore in Git
│
├── docs/ # Project documentation and presentation
│ ├── Project_Report.docx
│ ├── Project_Report.pdf
│ ├── diagrams/
│ │ └── system_architecture.png
│ └── presentation/
│ └── project_demo.mp4
│
├── server/ # Server-side application
│ ├── server_main.py # Entry point for the server
│ ├── server_auth.py # Authentication and encryption
│ ├── server_threads.py # Multithreading for concurrent clients
│ ├── server_fileops.py # Upload, download, delete, dir, subfolder logic
│ ├── server_analysis.py # Logs performance metrics
│ └── storage/ # Server-side file storage
│ ├── text/
│ ├── audio/
│ └── video/
│
├── client/ # Client-side application
│ ├── client_main.py # Entry point for client UI/CLI
│ ├── client_auth.py # Handles authentication & encryption
│ ├── client_network.py # Socket communication logic
│ ├── client_commands.py # Upload/download/delete/dir commands
│ └── downloads/ # Folder for downloaded files
│
├── analysis/ # Network performance analysis
│ ├── network_analysis.py # Collects and analyzes metrics
│ └── results/
│ ├── performance_data.csv
│ └── graphs/
│ ├── upload_rate.png
│ └── transfer_time.png
│
└── tests/ # Testing scripts
├── test_server.py
├── test_client.py
└── test_analysis.py
</code>

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
