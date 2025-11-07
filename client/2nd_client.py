import os
import socket
import sys
import type_effect

IP = "25.40.106.181"      # <-- change to your server's IP if needed
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
CHUNK_SIZE = 65536  # 64KB chunks to match server
FORMAT = "utf-8"


def receive_response(conn: socket.socket):
    """Receive a text response (expects a single UTF-8 message <= SIZE)."""
    try:
        return conn.recv(SIZE).decode(FORMAT).strip()
    except Exception:
        return "Failed to receive response."


# ----------------------- Upload (OPTIMIZED) -----------------------
def handle_upload(conn: socket.socket, filename: str):
    if not os.path.exists(filename):
        type_effect.type_print("File does not exist.")
        return

    conn.send(f"UPLOAD@{filename}".encode(FORMAT))

    if receive_response(conn) != "READY":
        type_effect.type_print("Server not ready for upload.")
        return

    filesize = os.path.getsize(filename)
    conn.send(str(filesize).encode(FORMAT))
    if receive_response(conn) != "OK":
        type_effect.type_print("Server rejected file size.")
        return

    # Send file in 64KB chunks for speed
    with open(filename, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            conn.sendall(chunk)

    type_effect.type_print(receive_response(conn))


# ----------------------- Download (OPTIMIZED) -----------------------
def handle_download(conn: socket.socket, filename: str):
    conn.send(f"DOWNLOAD@{filename}".encode(FORMAT))
    resp = receive_response(conn)

    if not resp.startswith("OK"):
        type_effect.type_print(resp)
        return

    # OK@<size>
    parts = resp.split("@", 2)
    if len(parts) < 2:
        type_effect.type_print("Malformed size response from server.")
        return
    try:
        filesize = int(parts[1])
    except ValueError:
        type_effect.type_print("Invalid file size received.")
        return

    # Send READY acknowledgment
    conn.send("READY".encode(FORMAT))

    # Receive file in 64KB chunks for speed
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


# ----------------------- Delete -----------------------
def handle_delete(conn: socket.socket, filename: str):
    conn.send(f"DELETE@{filename}".encode(FORMAT))
    type_effect.type_print(receive_response(conn))


# ----------------------- Main -----------------------
def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Optimize socket BEFORE connecting
    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm
    client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # 64KB receive buffer
    client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # 64KB send buffer
    
    client.connect(ADDR)

    # ----- Welcome -----
    welcome = client.recv(SIZE).decode(FORMAT)
    cmd, msg = welcome.split("@", 1)
    if cmd == "OK":
        type_effect.type_print(msg)

    # ----- Login -----
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

    # ----- Command Loop -----
    while True:
        cmd_line = input("> ").strip()
        type_effect.spacing()
        if not cmd_line:
            continue
        parts = cmd_line.split(maxsplit=1)
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
                type_effect.type_print("Usage: UPLOAD <filename>")
                continue
            handle_upload(client, parts[1])
            
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

        elif cmd == "LIST":
            client.send("LIST".encode(FORMAT))
            type_effect.type_print(receive_response(client))

        else:
            type_effect.type_print("Unknown command. Type HELP.")

    type_effect.type_print("Disconnected from the server.")
    client.close()


if __name__ == "__main__":
    main()