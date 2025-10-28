import os
import socket

IP = "25.52.223.162" # When using HAMACHI, set IP to the ethernet adapter, not wireless LAN
PORT = 4450
ADDR = (IP, PORT)
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
        parts = data.split(" ")
        cmd = parts[0].upper()

        # --- Handle HELP ---
        if cmd == "HELP":
            client.send(cmd.encode(FORMAT))

        # --- Handle LOGOUT ---
        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break

        # --- Handle UPLOAD ---
        elif cmd == "UPLOAD":
            if len(parts) < 2:
                print("⚠️ Usage: UPLOAD <filename>")
                continue

            filename = parts[1]

            if not os.path.exists(filename):
                print("❌ File does not exist.")
                continue

            # Send upload command to server
            client.send(f"UPLOAD@{filename}".encode(FORMAT))

            # Wait for server to acknowledge
            server_resp = client.recv(SIZE).decode(FORMAT)
            if server_resp != "READY":
                print("❌ Server not ready for upload.")
                continue

            # Send file size
            filesize = os.path.getsize(filename)
            client.send(str(filesize).encode(FORMAT))

            # Wait for confirmation
            client.recv(SIZE)

            # Start sending file data
            with open(filename, "rb") as f:
                data = f.read(SIZE)
                while data:
                    client.send(data)
                    data = f.read(SIZE)

            client.send(b"<END>")  # Mark end of file
            print(f"📤 Uploaded '{filename}' successfully.")
        elif cmd == "LIST":
            client.send(cmd.encode(FORMAT))

        else:
            print("❌ Unknown command. Try HELP")

    print("Disconnected from the server.")
    client.close()

if __name__ == "__main__":
    main()
