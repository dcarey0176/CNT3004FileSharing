#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import socket
import threading
from auth import authenticate

IP = "0.0.0.0"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_PATH = "server"

### to handle the clients
def handle_client (conn,addr):


    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the server. Please log in".encode(FORMAT))
    auth_data = conn.recv(SIZE).decode(FORMAT)
    cmd, username, password = auth_data.split("@")

    if cmd == "LOGIN":
        if authenticate(username, password):
            conn.send("OK@AUTH_SUCCESS".encode(FORMAT))
            print(f"[AUTH_SUCCESS] {username} authenticated from {ADDR}")
        else:
            conn.send("ERR@AUTH_FAILED".encode(FORMAT))
            print(f"[AUTH_FAIL] {ADDR} failed authentication.")
            conn.close()
            return

    while True:
        data =  conn.recv(SIZE).decode(FORMAT)
        data = data.split("@")
        cmd = data[0]
       
        send_data = "OK@"

        if cmd == "LOGOUT":
            break

        elif cmd == "TASK": 
            send_data += "LOGOUT from the server.\n"

            conn.send(send_data.encode(FORMAT))



    print(f"{addr} disconnected")
    conn.close()


def main():
    print("Starting the server")
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) ## used IPV4 and TCP connection
    server.bind(ADDR) # bind the address
    server.listen() ## start listening
    print(f"server is listening on {IP}: {PORT}")
    while True:
        conn, addr = server.accept() ### accept a connection from a client
        thread = threading.Thread(target = handle_client, args = (conn, addr)) ## assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()

