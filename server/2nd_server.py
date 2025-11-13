#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
import threading
import struct
import time
from auth import authenticate

IP = "0.0.0.0"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
CHUNK_SIZE = 65536  # 64KB chunks 
SOCKET_BUFFER_SIZE = 65536  
FORMAT = "utf-8"
SERVER_PATH = "server\server_data"          



# ----------------------------------------------------------------
# Helper functions for length-prefixed messages (for THROUGHPUT)
# ----------------------------------------------------------------
def recv_length_prefixed(conn: socket.socket) -> bytes:
    """Receive length-prefixed data (4-byte length header + data)"""
    # Receive 4-byte length header
    length_data = b""
    while len(length_data) < 4:
        chunk = conn.recv(4 - len(length_data))
        if not chunk:
            raise ConnectionError("Connection closed while reading length")
        length_data += chunk
    
    length = struct.unpack("!I", length_data)[0]
    
    # Receive the actual data
    data = b""
    while len(data) < length:
        chunk = conn.recv(min(CHUNK_SIZE, length - len(data)))
        if not chunk:
            raise ConnectionError("Connection closed while reading data")
        data += chunk
    
    return data

def handle_client(conn: socket.socket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKET_BUFFER_SIZE)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFFER_SIZE)
    
    conn.send("OK@Welcome to the server. Please log in".encode(FORMAT))

    # Login
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

    # Main command loop
    while True:
        try:
            data = conn.recv(SIZE).decode(FORMAT).strip()
            if not data:
                break

            parts = data.split("@")
            cmd = parts[0].upper()

            # PING command - for latency testing
            if cmd == "PING":
                conn.send("PONG".encode(FORMAT))
                
            # THROUGHPUT command - for throughput testing
            elif cmd == "THROUGHPUT":
                if len(parts) < 3:
                    conn.send("ERR@Invalid THROUGHPUT format".encode(FORMAT))
                    continue
                
                try:
                    size_kb = int(parts[1])
                    iterations = int(parts[2])
                    total_bytes = size_kb * iterations * 1024
                    
                    print(f"[THROUGHPUT] Starting test: {size_kb}KB x {iterations} iterations = {total_bytes/1_048_576:.2f}MB from {addr}")
                    
                    # Signal ready to receive
                    conn.send("READY".encode(FORMAT))
                    
                    received_total = 0
                    start_time = time.time()
                    
                    for batch in range(1, iterations + 1):
                        batch_received = 0
                        
                        # Receive size_kb chunks (each 1KB)
                        for chunk_num in range(size_kb):
                            try:
                                chunk_data = recv_length_prefixed(conn)
                                batch_received += len(chunk_data)
                                received_total += len(chunk_data)
                            except Exception as e:
                                print(f"[THROUGHPUT ERROR] Batch {batch}, chunk {chunk_num}: {e}")
                                raise
                        
                        # Send ACK for this batch
                        conn.send(f"ACK_BATCH_{batch}".encode(FORMAT))
                    
                    duration = time.time() - start_time
                    mbps = (received_total / 1_048_576) / duration if duration > 0 else 0
                    
                    print(f"[THROUGHPUT] Complete: {received_total:,} bytes ({received_total/1_048_576:.2f}MB) "
                          f"in {duration:.2f}s = {mbps:.2f} MB/s")
                    
                except ValueError as e:
                    conn.send(f"ERR@Invalid parameters: {e}".encode(FORMAT))
                except Exception as e:
                    print(f"[THROUGHPUT ERROR] {addr}: {e}")
                    conn.send(f"ERR@Throughput test failed: {e}".encode(FORMAT))

            elif cmd == "LOGOUT":
                conn.send("OK@Disconnected from the server.".encode(FORMAT))
                break

            elif cmd == "HELP":
                msg = (
                    "OK@Available commands:\n"
                    "UPLOAD <filename>\nDOWNLOAD <filename>\n"
                    "DELETE <filename>\nDIR\nLOGOUT"
                )
                conn.send(msg.encode(FORMAT))

            elif cmd == "DIR":
                files = os.listdir(SERVER_PATH)
                if not files:
                    conn.send("OK@No files found.".encode(FORMAT))
                else:
                    file_list = []
                    for file in files:
                        file_type = os.path.splitext(file)[1]  # Gets the file extension
                        if file_type == "":
                            file_type = "(no extension)"
                        file_list.append(f"{file} — {file_type}")
                    formatted_list = "\n".join(file_list)
                    conn.send(f"Files on server:\n{formatted_list}".encode(FORMAT))

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
                conn.send("OK".encode(FORMAT))

                print(f"[RECV] Receiving '{filename}' ({filesize} bytes) from {addr}")

                received = 0
                with open(filepath, "wb") as f:
                    while received < filesize:
                        chunk_size = min(CHUNK_SIZE, filesize - received)
                        chunk = conn.recv(chunk_size)
                        if not chunk:
                            raise ConnectionError("Client disconnected mid-upload")
                        f.write(chunk)
                        received += len(chunk)

                print(f"[SAVED] '{filename}' uploaded successfully.")
                conn.send(f"OK@File '{filename}' uploaded successfully.".encode(FORMAT))

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
                conn.send(f"OK@{filesize}".encode(FORMAT))
                
                ack = conn.recv(SIZE).decode(FORMAT).strip()
                if ack != "READY":
                    print(f"[ERROR] Client not ready for download")
                    continue

                print(f"[SEND] Sending '{filename}' ({filesize} bytes) to {addr}")
                
                sent = 0
                with open(filepath, "rb") as f:
                    while sent < filesize:
                        remaining = filesize - sent
                        chunk_size = min(CHUNK_SIZE, remaining)
                        chunk = f.read(chunk_size)
                        
                        if not chunk:
                            break
                        
                        conn.sendall(chunk)
                        sent += len(chunk)

                print(f"[SENT] '{filename}' sent successfully to {addr} ({sent} bytes)")
                
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

            else:
                conn.send("ERR@Unknown command".encode(FORMAT))

        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    print(f"[DISCONNECTED] {addr} disconnected.")
    conn.close()


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