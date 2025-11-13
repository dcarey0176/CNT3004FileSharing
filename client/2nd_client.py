import os
import socket
import sys
import type_effect

IP = "172.20.10.6"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
CHUNK_SIZE = 65536  # 64KB chunks
FORMAT = "utf-8"


def receive_response(conn: socket.socket):
    try:
        return conn.recv(SIZE).decode(FORMAT).strip()
    except Exception:
        return "Failed to receive response."


#upload
def handle_upload(conn: socket.socket, path: str, sub: str = None):
    """Upload a file or folder to the server."""
    if not os.path.exists(path):
        type_effect.type_print("⚠️ File or folder does not exist.")
        return

    if os.path.isdir(path):
        # Check if folder is empty
        if not any(os.scandir(path)):
            # Send empty folder command
            folder_name = os.path.basename(path) if not sub else sub
            conn.send(f"UPLOAD_EMPTY@{folder_name}".encode(FORMAT))
            type_effect.type_print(f"✅ Empty folder '{folder_name}' created on server.")
            return

        # Upload non-empty folder
        for root, _, files in os.walk(path):
            rel_path = os.path.relpath(root, path)
            if rel_path == ".":
                rel_path = ""
            for file in files:
                file_path = os.path.join(root, file)
                sub_folder = os.path.join(sub or os.path.basename(path), rel_path)
                upload_single_file(conn, file_path, sub_folder)
        type_effect.type_print("✅ Folder uploaded successfully.")
    else:
        upload_single_file(conn, path, sub)


def upload_single_file(conn: socket.socket, filename: str, sub: str = None):
    """Send a single file to the server."""
    base_name = os.path.basename(filename)
    if sub:
        conn.send(f"UPLOAD@{base_name}@{sub}".encode(FORMAT))
    else:
        conn.send(f"UPLOAD@{base_name}".encode(FORMAT))

    if receive_response(conn) != "READY":
        type_effect.type_print("Server not ready for upload.")
        return

    filesize = os.path.getsize(filename)
    conn.send(str(filesize).encode(FORMAT))

    if receive_response(conn) != "OK":
        type_effect.type_print("Server rejected file size.")
        return

    with open(filename, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            conn.sendall(chunk)

    type_effect.type_print(receive_response(conn))

#Download
def handle_download(conn: socket.socket, filename: str):
    conn.send(f"DOWNLOAD@{filename}".encode(FORMAT))
    resp = receive_response(conn)

    if not resp.startswith("OK"):
        type_effect.type_print(resp)
        return

    parts = resp.split("@", 2)
    if len(parts) < 2:
        type_effect.type_print("Malformed size response from server.")
        return
    try:
        filesize = int(parts[1])
    except ValueError:
        type_effect.type_print("Invalid file size received.")
        return

    conn.send("READY".encode(FORMAT))

    received = 0
    with open(filename, "wb") as f:
        while received < filesize:
            chunk_size = min(CHUNK_SIZE, filesize - received)
            chunk = conn.recv(chunk_size)
            if not chunk:
                raise ConnectionError("Connection lost during download")
            f.write(chunk)
            received += len(chunk)

    type_effect.type_print(f"Downloaded '{filename}' successfully!")


#Delete
def handle_delete(conn: socket.socket, filename: str):
    conn.send(f"DELETE@{filename}".encode(FORMAT))
    type_effect.type_print(receive_response(conn))


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Optimize socket BEFORE connecting
    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm
    client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # 64KB receive buffer
    client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # 64KB send buffer

    client.connect(ADDR)

    #Greeting
    welcome = client.recv(SIZE).decode(FORMAT)
    cmd, msg = welcome.split("@", 1)
    if cmd == "OK":
        type_effect.type_print(msg)

    #Login
    username = input("Username: ")
    password = input("Password: ")
    client.send(f"LOGIN@{username}@{password}".encode(FORMAT))

    login_resp = client.recv(SIZE).decode(FORMAT)
    parts = login_resp.split("@")
    if len(parts) < 2 or parts[0] != "OK" or parts[1] != "AUTH_SUCCESS":
        type_effect.type_print("Authentication failed.")
        client.close()
        return
    type_effect.spacing()
    type_effect.type_print("Login successful! You are connected to the server.")
    type_effect.spacing()
    if len(parts) > 2:
        type_effect.type_print("@".join(parts[2:]))      # any extra welcome text

    #Commands
    while True:
        cmd_line = input("> ").strip()
        type_effect.spacing()
        if not cmd_line:
            continue
        parts = cmd_line.split(maxsplit=2)
        cmd = parts[0].upper()

        if cmd == "HELP":
            client.send("HELP".encode(FORMAT))
            type_effect.type_print(receive_response(client))

        elif cmd == "LOGOUT":
            client.send("LOGOUT".encode(FORMAT))
            type_effect.type_print(receive_response(client))
            break

        elif cmd == "UPLOAD":
            if len(parts) < 2:
                type_effect.type_print("Usage: UPLOAD <filename> [subfolder]")
                continue
            filename = parts[1]
            subfolder = parts[2] if len(parts) >= 3 else None
            handle_upload(client, filename, subfolder)


        elif cmd == "DOWNLOAD":
            if len(parts) < 2:
                type_effect.type_print("Usage: DOWNLOAD <filename>")
                continue
            handle_download(client, parts[1])

        elif cmd == "DELETE":
            if len(parts) < 2:
                type_effect.type_print("Usage: DELETE <filename>")
                continue
            handle_delete(client, parts[1])

        elif cmd == "DIR":
            client.send("DIR".encode(FORMAT))
            type_effect.type_print(receive_response(client))

        else:
            type_effect.type_print("Unknown command. Type HELP.")

    type_effect.type_print("Disconnected from the server.")
    client.close()


if __name__ == "__main__":
    main()
