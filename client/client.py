

import os
import socket


IP = "localhost"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"

def main():
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    # --- Login process ---
    data = client.recv(SIZE).decode(FORMAT)
    cmd, msg = data.split("@")
    if cmd == "OK":
        print(msg)

    username = input("Username: ")
    password = input("Password: ")

    login_data = f"LOGIN@{username}@{password}"
    client.send(login_data.encode(FORMAT))

    response = client.recv(SIZE).decode(FORMAT)
    cmd, msg = response.split("@")

    if cmd == "OK" and msg == "AUTH_SUCCESS":
        print("✅ Login successful! You are connected to the server.")
    else:
        print("❌ Authentication failed. Disconnecting.")
        client.close()
        return

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
