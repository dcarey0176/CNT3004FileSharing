#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import socket
import threading
import struct
from auth import authenticate
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import client.type_effect as type_effect

IP = "0.0.0.0"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_PATH = "server/server_data"          # Folder where uploaded files are stored

# ==============================================================
#  MESSAGE HELPERS – put these here (after imports, before any function)
# ==============================================================
def _recv_exact(conn: socket.socket, n: int) -> bytes:
    """Receive exactly *n* bytes (with timeout)."""
    data = b""
    conn.settimeout(5.0)
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            raise ConnectionError("Socket closed")
        data += packet
    return data

def _recv_msg(conn: socket.socket) -> str:
    raw_len = _recv_exact(conn, 4)
    msg_len = struct.unpack("!I", raw_len)[0]
    return _recv_exact(conn, msg_len).decode(FORMAT)

def _send_msg(conn: socket.socket, msg: str):
    """Send a length-prefixed UTF-8 message."""
    payload = msg.encode(FORMAT)
    conn.sendall(struct.pack("!I", len(payload)) + payload)
# ==============================================================

# ----------------------------------------------------------------------
# Ensure the upload directory exists
# ----------------------------------------------------------------------
if not os.path.exists(SERVER_PATH):
    os.makedirs(SERVER_PATH)


def handle_client(conn: socket.socket, addr):
    type_effect.spacing()
    print(f"[NEW CONNECTION] {addr} connected.")
    _send_msg(conn, "OK@Welcome to the server. Please log in")    # ----------------------- Login Phase -----------------------
    try:
        auth_data = _recv_msg(conn)  # Use length-prefixed recv
        parts = auth_data.split("@")
        if len(parts) != 3 or parts[0] != "LOGIN":
            _send_msg(conn, "ERR@Bad login format")
            conn.close()
            return

        _, username, password = parts
        if username == "perf_test" and password == "perf_test":
            _send_msg(conn, "OK@AUTH_SUCCESS@You can now enter commands. Type HELP to see options.")
            print(f"[AUTH_SUCCESS] perf_test from {addr}")
        elif authenticate(username, password):
            _send_msg(conn, "OK@AUTH_SUCCESS@You can now enter commands. Type HELP to see options.")
            print(f"[AUTH_SUCCESS] {username} from {addr}")
        else:
            _send_msg(conn, "ERR@AUTH_FAILED")
            print(f"[AUTH_FAIL] {addr} failed authentication.")
            conn.close()
            return
    except Exception as e:
        print(f"[LOGIN ERROR] {addr}: {e}")
        conn.close()
        return
        
        # ----------------------- Main Command Loop -----------------------
    while True:
        type_effect.spacing()
        try:
            # Use length-prefixed recv for ALL commands
            data = _recv_msg(conn)
            if not data:
                break

            parts = data.split("@")
            cmd = parts[0].upper()

            # ---------- LOGOUT ----------
            if cmd == "LOGOUT":
                _send_msg(conn, "OK@Disconnected from the server.")
                break

            # ---------- HELP ----------
            elif cmd == "HELP":
                msg = (
                    "OK@Available commands:\n"
                    "UPLOAD <filename>\nDOWNLOAD <filename>\n"
                    "DELETE <filename>\nLIST\nLOGOUT"
                )
                _send_msg(conn, msg)

            # ---------- LIST ----------
            elif cmd == "LIST":
                files = os.listdir(SERVER_PATH)
                if not files:
                    _send_msg(conn, "OK@No files found.")
                else:
                    file_list = "\n".join(files)
                    _send_msg(conn, f"OK@Files on server:\n{file_list}")

            # ---------- UPLOAD ----------
            elif cmd == "UPLOAD":
                if len(parts) < 2:
                    _send_msg(conn, "ERR@Missing filename")
                    continue
                filename = parts[1]
                filepath = os.path.join(SERVER_PATH, filename)

                _send_msg(conn, "READY")

                try:
                    size_msg = _recv_msg(conn)
                    if not size_msg.startswith("SIZE@"):
                        raise ValueError("Bad size")
                    filesize = int(size_msg.split("@")[1])
                except Exception as e:
                    _send_msg(conn, "ERR@Bad size")
                    continue

                _send_msg(conn, "OK")
                print(f"[RECV] Receiving '{filename}' ({filesize} bytes) from {addr}")

                received = 0
                with open(filepath, "wb") as f:
                    while received < filesize:
                        chunk_len = struct.unpack("!I", _recv_exact(conn, 4))[0]
                        chunk = _recv_exact(conn, chunk_len)
                        f.write(chunk)
                        received += len(chunk)

                print(f"[SAVED] '{filename}' uploaded ({received} bytes).")
                _send_msg(conn, f"OK@File '{filename}' uploaded successfully.")

            # ---------- DOWNLOAD ----------
            elif cmd == "DOWNLOAD":
                if len(parts) < 2:
                    _send_msg(conn, "ERR@Missing filename")
                    continue
                filename = parts[1]
                filepath = os.path.join(SERVER_PATH, filename)

                if not os.path.exists(filepath):
                    _send_msg(conn, "ERR@File not found.")
                    continue

                filesize = os.path.getsize(filepath)
                _send_msg(conn, f"OK@{filesize}")

                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(SIZE)
                        if not chunk:
                            break
                        conn.sendall(struct.pack("!I", len(chunk)) + chunk)

                print(f"[SENT] '{filename}' sent to {addr}")

            # ---------- DELETE ----------
            elif cmd == "DELETE":
                if len(parts) < 2:
                    _send_msg(conn, "ERR@Missing filename")
                    continue
                filename = parts[1]
                filepath = os.path.join(SERVER_PATH, filename)

                if os.path.exists(filepath):
                    os.remove(filepath)
                    _send_msg(conn, f"OK@File '{filename}' deleted successfully.")
                    print(f"[DELETE] '{filename}' removed by {addr}")
                else:
                    _send_msg(conn, "ERR@File not found.")

            # ---------- PING ----------
            elif cmd == "PING":
                _send_msg(conn, "PONG")

            # ---------- THROUGHPUT ----------
            elif cmd == "THROUGHPUT":
                if len(parts) < 3:
                    _send_msg(conn, "ERR@Bad args")
                    continue
                try:
                    size_kb = int(parts[1])
                    iters = int(parts[2])
                    _send_msg(conn, "READY")

                    for _ in range(iters):
                        for _ in range(size_kb):
                            clen = struct.unpack("!I", _recv_exact(conn, 4))[0]
                            _recv_exact(conn, clen)
                        _send_msg(conn, "ACK")
                    print(f"[THROUGHPUT] Done.")
                except Exception as e:
                    print(f"[THROUGHPUT ERROR] {e}")

            # ---------- UNKNOWN ----------
            else:
                _send_msg(conn, "ERR@Unknown command")

        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    print(f"[DISCONNECTED] {addr} disconnected.")
    conn.close()


# ----------------------------------------------------------------------
def main():
    type_effect.spacing()
    print("Starting the server...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(ADDR)
    server.listen()
    print(f"Server is listening on {IP}:{PORT}")

    while True:
        type_effect.spacing()
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


if __name__ == "__main__":
    main()