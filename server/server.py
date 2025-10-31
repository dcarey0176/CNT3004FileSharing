#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
import threading
from auth import authenticate

IP = "0.0.0.0"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_PATH = "server_data"  # Folder for uploaded files

# Make sure upload directory exists
if not os.path.exists(SERVER_PATH):
    os.makedirs(SERVER_PATH)


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the server. Please log in".encode(FORMAT))

    # --- Login Phase ---
    auth_data = conn.recv(SIZE).decode(FORMAT)
    cmd, username, password = auth_data.split("@")
    if cmd == "LOGIN":
        if authenticate(username, password):
            conn.send("OK@AUTH_SUCCESS".encode(FORMAT))
            print(f"[AUTH_SUCCESS] {username} authenticated from {addr}")
            conn.send(
                "OK@You can now enter commands. Type HELP to see options.".encode(FORMAT))
        else:
            conn.send("ERR@AUTH_FAILED".encode(FORMAT))
            print(f"[AUTH_FAIL] {addr} failed authentication.")
            conn.close()
            return

    # --- Main Command Loop ---
    while True:
        try:
            data = conn.recv(SIZE).decode(FORMAT)
            if not data:
                break

            parts = data.split("@")
            cmd = parts[0]
            send_data = "OK@"

            # --- Handle LOGOUT ---
            if cmd == "LOGOUT":
                send_data += "Disconnected from the server."
                conn.send(f"DISCONNECTED@{send_data}".encode(FORMAT))
                break

            # --- Handle HELP ---
            elif cmd == "HELP":
                send_data += "Available commands:\nHELP, UPLOAD <filename>, LOGOUT"
                conn.send(send_data.encode(FORMAT))

            # --- Handle FILE UPLOAD ---
            elif cmd == "UPLOAD":
                if len(parts) < 2:
                    conn.send("ERR@Missing filename".encode(FORMAT))
                    continue

                filename = parts[1]
                filepath = os.path.join(SERVER_PATH, filename)
                # Tell client to start sending
                conn.send("READY".encode(FORMAT))

                # Receive file size
                filesize = int(conn.recv(SIZE).decode(FORMAT))
                conn.send("OK".encode(FORMAT))  # Confirm ready for data

                print(
                    f"[RECV] Receiving '{filename}' ({filesize} bytes) from {addr}")

                # Receive file data
                with open(filepath, "wb") as f:
                    while True:
                        data = conn.recv(SIZE)
                        if data == b"<END>":
                            break
                        f.write(data)

                print(f"[SAVED] File '{filename}' uploaded successfully.")
                conn.send(
                    f"OK@File '{filename}' uploaded successfully.".encode(FORMAT))
            elif cmd == "LIST":
                files = os.listdir(SERVER_PATH)
                if not files:
                    conn.send("OK@No files found.".encode(FORMAT))
                else:
                    file_list = "\n".join(files)
                    conn.send(
                        f"OK@Files on server:\n{file_list}".encode(FORMAT))
            elif cmd == "DOWNLOAD":
                filename = conn.recv(1024).decode(FORMAT)
                filepath = os.path.join(SERVER_PATH, filename)

                if os.path.exists(filepath):
                    conn.send("OK".encode(FORMAT))
                    with open(filepath, "rb") as f:
                        data = f.read()
                    conn.sendall(data)
                    conn.send(b"<END>")
                else:
                    conn.send("ERR@File not found.".encode(FORMAT))
            else:
                conn.send("ERR@Unknown command".encode(FORMAT))

        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    print(f"[DISCONNECTED] {addr} disconnected.")
    conn.close()


def main():
    print("🚀 Starting the server...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(ADDR)
    server.listen()
    print(f"✅ Server is listening on {IP}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


if __name__ == "__main__":
    main()
