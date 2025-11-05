import os
import socket

IP = "25.40.106.181"      # <-- change to your server's IP if needed
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"


def recv_exact(conn: socket.socket, nbytes: int) -> bytes:
    """Receive exactly *nbytes* from the socket."""
    data = b""
    while len(data) < nbytes:
        packet = conn.recv(nbytes - len(data))
        if not packet:
            raise ConnectionError("Socket closed while receiving")
        data += packet
    return data


def receive_response(conn: socket.socket) -> str:
    """Receive a text response (expects a single UTF-8 message <= SIZE)."""
    try:
        return conn.recv(SIZE).decode(FORMAT).strip()
    except Exception:
        return "Failed to receive response."


# ----------------------- Upload -----------------------
def handle_upload(conn: socket.socket, filename: str):
    if not os.path.exists(filename):
        print("File does not exist.")
        return

    conn.send(f"UPLOAD@{filename}".encode(FORMAT))

    if receive_response(conn) != "READY":
        print("Server not ready for upload.")
        return

    filesize = os.path.getsize(filename)
    conn.send(str(filesize).encode(FORMAT))
    if receive_response(conn) != "OK":
        print("Server rejected file size.")
        return

    with open(filename, "rb") as f:
        while chunk := f.read(SIZE):
            conn.send(chunk)

    print(receive_response(conn))


# ----------------------- Download -----------------------
def handle_download(conn: socket.socket, filename: str):
    conn.send(f"DOWNLOAD@{filename}".encode(FORMAT))
    resp = receive_response(conn)

    if not resp.startswith("OK"):
        print(resp)
        return

    # OK@<size>
    parts = resp.split("@", 2)
    if len(parts) < 2:
        print("Malformed size response from server.")
        return
    try:
        filesize = int(parts[1])
    except ValueError:
        print("Invalid file size received.")
        return

    received = 0
    with open(filename, "wb") as f:
        while received < filesize:
            chunk_size = min(SIZE, filesize - received)
            data = recv_exact(conn, chunk_size)
            f.write(data)
            received += len(data)

    print(f"Downloaded '{filename}' successfully!")


# ----------------------- Delete -----------------------
def handle_delete(conn: socket.socket, filename: str):
    conn.send(f"DELETE@{filename}".encode(FORMAT))
    print(receive_response(conn))


# ----------------------- Main -----------------------
def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    # ----- Welcome -----
    welcome = client.recv(SIZE).decode(FORMAT)
    cmd, msg = welcome.split("@", 1)
    if cmd == "OK":
        print(msg)

    # ----- Login -----
    username = input("Username: ")
    password = input("Password: ")
    client.send(f"LOGIN@{username}@{password}".encode(FORMAT))

    login_resp = client.recv(SIZE).decode(FORMAT)
    parts = login_resp.split("@")
    if len(parts) < 2 or parts[0] != "OK" or parts[1] != "AUTH_SUCCESS":
        print("Authentication failed.")
        client.close()
        return

    print("Login successful! You are connected to the server.")
    if len(parts) > 2:
        print("@".join(parts[2:]))      # any extra welcome text

    # ----- Command Loop -----
    while True:
        cmd_line = input("> ").strip()
        if not cmd_line:
            continue
        parts = cmd_line.split(maxsplit=1)
        cmd = parts[0].upper()

        if cmd == "HELP":
            client.send("HELP".encode(FORMAT))
            print(receive_response(client))

        elif cmd == "LOGOUT":
            client.send("LOGOUT".encode(FORMAT))
            print(receive_response(client))
            break

        elif cmd == "UPLOAD":
            if len(parts) < 2:
                print("Usage: UPLOAD <filename>")
                continue
            handle_upload(client, parts[1])

        elif cmd == "DOWNLOAD":
            if len(parts) < 2:
                print("Usage: DOWNLOAD <filename>")
                continue
            handle_download(client, parts[1])

        elif cmd == "DELETE":
            if len(parts) < 2:
                print("Usage: DELETE <filename>")
                continue
            handle_delete(client, parts[1])

        elif cmd == "LIST":
            client.send("LIST".encode(FORMAT))
            print(receive_response(client))

        else:
            print("Unknown command. Type HELP.")

    print("Disconnected from the server.")
    client.close()


if __name__ == "__main__":
    main()