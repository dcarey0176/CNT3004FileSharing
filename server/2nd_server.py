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
CHUNK_SIZE = 1000000
FORMAT = "utf-8"
SERVER_PATH = "server\server_data"          # Folder where uploaded files are stored

# ----------------------------------------------------------------------
# Ensure the upload directory exists
# ----------------------------------------------------------------------
if not os.path.exists(SERVER_PATH):
    os.makedirs(SERVER_PATH)


def handle_client(conn: socket.socket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the server. Please log in".encode(FORMAT))

    # ----------------------- Login Phase -----------------------
    try:
        auth_data = conn.recv(SIZE).decode(FORMAT)
        parts = auth_data.split("@")
        if len(parts) != 3 or parts[0] != "LOGIN":
            conn.send("ERR@Bad login format".encode(FORMAT))
            conn.close()
            return

        _, username, password = parts
        if authenticate(username, password):
            conn.send(
                "OK@AUTH_SUCCESS@You can now enter commands. Type HELP to see options."
                .encode(FORMAT)
            )
            print(f"[AUTH_SUCCESS] {username} from {addr}")
        else:
            conn.send("ERR@AUTH_FAILED".encode(FORMAT))
            print(f"[AUTH_FAIL] {addr} failed authentication.")
            conn.close()
            return
    except Exception as e:
        print(f"[LOGIN ERROR] {addr}: {e}")
        conn.close()
        return

    # ----------------------- Main Command Loop -----------------------
    while True:
        try:
            data = conn.recv(SIZE).decode(FORMAT).strip()
            if not data:
                break

            parts = data.split("@")
            cmd = parts[0].upper()

            # ---------- LOGOUT ----------
            if cmd == "LOGOUT":
                conn.send("OK@Disconnected from the server.".encode(FORMAT))
                break

            # ---------- HELP ----------
            elif cmd == "HELP":
                msg = (
                    "OK@Available commands:\n"
                    "UPLOAD <filename>\nDOWNLOAD <filename>\n"
                    "DELETE <filename>\nLIST\nLOGOUT"
                )
                conn.send(msg.encode(FORMAT))

            # ---------- LIST ----------
            elif cmd == "LIST":
                files = os.listdir(SERVER_PATH)
                if not files:
                    conn.send("OK@No files found.".encode(FORMAT))
                else:
                    file_list = "\n".join(files)
                    conn.send(f"OK@Files on server:\n{file_list}".encode(FORMAT))

            # ---------- UPLOAD ----------
            elif cmd == "UPLOAD":
                if len(parts) < 2:
                    conn.send("ERR@Missing filename".encode(FORMAT))
                    continue
                filename = parts[1]
                filepath = os.path.join(SERVER_PATH, filename)

                # Tell client we are ready
                conn.send("READY".encode(FORMAT))

                # Receive file size
                size_str = conn.recv(SIZE).decode(FORMAT).strip()
                filesize = int(size_str)
                conn.send("OK".encode(FORMAT))          # confirm

                print(f"[RECV] Receiving '{filename}' ({filesize} bytes) from {addr}")

                received = 0
                with open(filepath, "wb") as f:
                    while received < filesize:
                        chunk_size = min(SIZE, filesize - received)
                        chunk = conn.recv(chunk_size)
                        if not chunk:
                            raise ConnectionError("Client disconnected mid-upload")
                        f.write(chunk)
                        received += len(chunk)

                print(f"[SAVED] '{filename}' uploaded successfully.")
                conn.send(f"OK@File '{filename}' uploaded successfully.".encode(FORMAT))

            # ---------- DOWNLOAD ----------
            
            # ---------- DOWNLOAD (IMPROVED FOR LARGE FILES) ----------
            elif cmd == "DOWNLOAD":
                if len(parts) < 2:
                    conn.send("ERR@Missing filename".encode(FORMAT))
                    continue
                filename = parts[1]
                filepath = os.path.join(SERVER_PATH, filename)

                if not os.path.exists(filepath):
                    conn.send("ERR@File not found.".encode(FORMAT))
                    continue

                filesize = os.path.getsize(filepath)
                # Send file size to client
                conn.send(f"OK@{filesize}".encode(FORMAT))
                
                # Wait for client acknowledgment
                ack = conn.recv(SIZE).decode(FORMAT).strip()
                if ack != "READY":
                    print(f"[ERROR] Client not ready for download")
                    continue

                print(f"[SEND] Sending '{filename}' ({filesize} bytes) to {addr}")
                
                sent = 0
                with open(filepath, "rb") as f:
                    while sent < filesize:
                        # Read chunk from file
                        chunk = f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        
                        # Send chunk
                        conn.sendall(chunk)
                        sent += len(chunk)
                        
                        # Optional: Print progress for very large files
                        if filesize > 1024 * 1024:  # > 1MB
                            progress = (sent / filesize) * 100
                            if sent % (CHUNK_SIZE * 100) == 0 or sent == filesize:
                                print(f"[PROGRESS] {filename}: {progress:.1f}% ({sent}/{filesize} bytes)")
                
            # ---------- DELETE ----------
            elif cmd == "DELETE":
                if len(parts) < 2:
                    conn.send("ERR@Missing filename".encode(FORMAT))
                    continue
                filename = parts[1]
                filepath = os.path.join(SERVER_PATH, filename)

                if os.path.exists(filepath):
                    os.remove(filepath)
                    conn.send(f"OK@File '{filename}' deleted successfully.".encode(FORMAT))
                    print(f"[DELETE] '{filename}' removed by {addr}")
                else:
                    conn.send("ERR@File not found.".encode(FORMAT))

            # ---------- UNKNOWN ----------
            else:
                conn.send("ERR@Unknown command".encode(FORMAT))

        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    print(f"[DISCONNECTED] {addr} disconnected.")
    conn.close()


# ----------------------------------------------------------------------
def main():
    print("Starting the server...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(ADDR)
    server.listen()
    print(f"Server is listening on {IP}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


if __name__ == "__main__":
    main()