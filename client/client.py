

import os
import socket


IP = "localhost"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"

def main():
    
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)

    # ---- Receive welcome message ----
    data = client.recv(SIZE).decode(FORMAT)
    cmd, msg = data.split("@")
    if cmd == "OK":
        print(msg)

    # ---- Authentication ----
    username = input("Username: ")
    password = input("Password: ")

    login_msg = f"LOGIN@{username}@{password}"
    client.send(login_msg.encode(FORMAT))

    auth_response = client.recv(SIZE).decode(FORMAT)
    cmd, msg = auth_response.split("@")

    if cmd == "ERR":
        print("❌ Authentication failed. Disconnecting.")
        client.close()
        return
    
    elif cmd == "OK" and msg == "AUTH_SUCCESS":
        print("✅ Login successful!\n")
    while True:
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split("@")
        if cmd == "OK":
            print(f"{msg}")
        elif cmd == "DISCONNECTED":
            print(f"{msg}")
            break
        
        data = input("> ") 
        data = data.split(" ")
        cmd = data[0]

        if cmd == "HELP":
            client.send(cmd.encode(FORMAT))
        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break


    print("Disconnected from the server.")
    client.close() ## close the connection

if __name__ == "__main__":
    main()
