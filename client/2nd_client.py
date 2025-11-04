import os
import socket
import time

IP = "25.40.106.181"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"


def receive_response(client):
    """Receive and decode a server response."""
    try:
        data = client.recv(SIZE).decode(FORMAT)
        return data
    except Exception as e:
        print(f"[ERROR] Failed to receive response: {e}")
        return ""


def handle_upload(client, filename):
    """Handles uploading a file to the server."""
    if not os.path.exists(filename):
        print("❌ File does not exist.")
        return

    # Send upload request
    client.send(f"UPLOAD@{filename}".encode(FORMAT))
    server_resp = client.recv(SIZE).decode(FORMAT)

    if server_resp != "READY":
        print("❌ Server not ready for upload.")
        return

    filesize = os.path.getsize(filename)
    client.send(str(filesize).encode(FORMAT))
    client.recv(SIZE)  # Wait for confirmation

    print(f"⬆️ Uploading '{filename}' ({filesize} bytes)...")
    start = time.time()

    with open(filename, "rb") as f:
        while True:
            data = f.read(SIZE)
            if not data:
                break
            client.send(data)

    client.send(b"<END>")

    elapsed = time.time() - start
    speed = filesize / elapsed / 1024
    print(f"✅ Upload complete in {elapsed:.2f}s ({speed:.1f} KB/s)")

    response = receive_response(client)
    if response:
        print(response.replace("OK@", ""))


def handle_download(client, filename):
    """Handles downloading a file from the server."""
    client.send(f"DOWNLOAD@{filename}".encode(FORMAT))
    response = client.recv(SIZE).decode(FORMAT)

    if not response.startswith("OK"):
        print(response)
        return

    local_name = f"downloaded_{filename}"
    print(f"⬇️ Downloading '{filename}'...")

    start = time.time()
    with open(local_name, "wb") as f:
        while True:
            data = client.recv(SIZE)
            if data == b"<END>":
                break
            f.write(data)

    elapsed = time.time() - start
    file_size = os.path.getsize(local_name)
    speed = file_size / elapsed / 1024
    print(f"✅ Downloaded '{local_name}' in {elapsed:.2f}s ({speed:.1f} KB/s)")


def handle_list(client):
    """Request and display the list of files on the server."""
    client.send("LIST".encode(FORMAT))
    response = receive_response(client)
    print(response.replace("OK@", ""))


def handle_delete(client, filename):
    """Send request to delete a file from the server."""
    client.send("DELETE".encode(FORMAT))
    client.send(filename.encode(FORMAT))
    response = receive_response(client)
    print(response)


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    # --- Login Phase ---
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
        data = input("\n> ").strip()
        if not data:
            continue

        parts = data.split(" ")
        cmd = parts[0].upper()

        if cmd == "HELP":
            client.send(cmd.encode(FORMAT))
            print(receive_response(client).replace("OK@", ""))

        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break

        elif cmd == "UPLOAD":
            if len(parts) < 2:
                print("⚠️ Usage: UPLOAD <filename>")
                continue
            handle_upload(client, parts[1])

        elif cmd == "LIST":
            handle_list(client)

        elif cmd == "DOWNLOAD":
            if len(parts) < 2:
                print("⚠️ Usage: DOWNLOAD <filename>")
                continue
            handle_download(client, parts[1])

        elif cmd == "DELETE":
            if len(parts) < 2:
                print("⚠️ Usage: DELETE <filename>")
                continue
            handle_delete(client, parts[1])

        else:
            print("❌ Unknown command. Try HELP.")

    print("🔌 Disconnected from the server.")
    client.close()


if __name__ == "__main__":
    main()
