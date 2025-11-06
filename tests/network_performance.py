# network_performance.py
import socket
import time
import struct
import matplotlib.pyplot as plt
import numpy as np

SERVER_HOST = "25.40.106.181"
SERVER_PORT = 4450
FORMAT = "utf-8"
SIZE = 1024

# ------------------------------------------------------------------
# Length-prefixed helpers (used for PING, THROUGHPUT, LOGOUT)
# ------------------------------------------------------------------
def _send_msg(conn: socket.socket, msg: str):
    payload = msg.encode(FORMAT)
    conn.sendall(struct.pack("!I", len(payload)) + payload)

def _recv_msg(conn: socket.socket) -> str:
    # Use the socket's existing timeout
    header = b""
    while len(header) < 4:
        chunk = conn.recv(4 - len(header))
        if not chunk:
            raise ConnectionError("Socket closed during header")
        header += chunk
    msg_len = struct.unpack("!I", header)[0]
    data = b""
    while len(data) < msg_len:
        chunk = conn.recv(msg_len - len(data))
        if not chunk:
            raise ConnectionError("Socket closed during payload")
        data += chunk
    return data.decode(FORMAT)

# ------------------------------------------------------------------
# 1. Latency (PING / PONG)
# ------------------------------------------------------------------
def measure_latency(conn, num_pings: int = 50):
    latencies = []
    for i in range(1, num_pings + 1):
        try:
            start = time.perf_counter()
            _send_msg(conn, "PING")
            resp = _recv_msg(conn)
            if resp != "PONG":
                raise ValueError(f"Expected PONG, got {resp}")
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
            print(f"  Ping {i:2d}: {elapsed:6.2f} ms")
        except Exception as e:
            print(f"  Ping {i:2d}: FAILED ({e})")
            latencies.append(None)
    return latencies

# ------------------------------------------------------------------
# 2. Throughput
# ------------------------------------------------------------------
def measure_throughput(conn, size_kb: int = 100, iterations: int = 20):
    chunk = b"x" * 1024
    total_kb = size_kb * iterations
    total_bytes = total_kb * 1024

    print(f"\nSending {total_kb} KB ({total_bytes/1_048_576:.2f} MB)...")
    _send_msg(conn, f"THROUGHPUT@{size_kb}@{iterations}")

    try:
        ready = _recv_msg(conn)
        if ready != "READY":
            raise ConnectionError(f"Server not ready: {ready}")
    except Exception as e:
        raise ConnectionError(f"Failed to get READY: {e}")

    start_time = time.perf_counter()
    for batch in range(1, iterations + 1):
        for _ in range(size_kb):
            conn.sendall(struct.pack("!I", len(chunk)) + chunk)
        ack = _recv_msg(conn)
        print(f"  Batch {batch}/{iterations} sent (ACK: {ack})")
        time.sleep(0.01)

    duration = time.perf_counter() - start_time
    mbps = total_bytes / (1_048_576 * duration) if duration > 0 else 0
    return mbps

# ------------------------------------------------------------------
# 3. Stats
# ------------------------------------------------------------------
def calculate_packet_loss(latencies):
    sent = len(latencies)
    received = sum(1 for l in latencies if l is not None)
    return ((sent - received) / sent) * 100 if sent else 0

# ------------------------------------------------------------------
# 4. Main
# ------------------------------------------------------------------
def main():
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.settimeout(12.0)

    # CONNECT
    try:
        print(f"Connecting to {SERVER_HOST}:{SERVER_PORT} ...")
        conn.connect((SERVER_HOST, SERVER_PORT))
        print("Connected.\n")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # WELCOME (raw)
    try:
        welcome = conn.recv(SIZE).decode(FORMAT).strip()
        print(f"[SERVER WELCOME] {welcome}")
    except Exception as e:
        print(f"[WARNING] No welcome: {e}")

    # LOGIN (raw send + raw recv)
    try:
        conn.sendall("LOGIN@perf_test@perf_test".encode(FORMAT))
        login_resp = conn.recv(SIZE).decode(FORMAT).strip()
        print(f"[LOGIN RESPONSE] {login_resp}")
        if not login_resp.startswith("OK@AUTH_SUCCESS"):
            print(f"[ERROR] Login failed: {login_resp}")
            conn.close()
            return
        print("[LOGIN] SUCCESS!\n")
    except Exception as e:
        print(f"[LOGIN ERROR] {e}")
        conn.close()
        return

    # LATENCY
    print("=== LATENCY TEST (50 pings) ===")
    latencies = measure_latency(conn, num_pings=50)

    # THROUGHPUT
    print("\n=== THROUGHPUT TEST ===")
    try:
        throughput = measure_throughput(conn, size_kb=100, iterations=20)
    except Exception as e:
        print(f"Throughput failed: {e}")
        throughput = 0.0

    # LOGOUT
    try:
        _send_msg(conn, "LOGOUT")
        _recv_msg(conn)
    except:
        pass
    conn.close()

    # RESULTS
    valid = [l for l in latencies if l is not None]
    avg_latency = sum(valid) / len(valid) if valid else float('inf')
    packet_loss = calculate_packet_loss(latencies)

    print("\n" + "="*60)
    print(" " * 20 + "NETWORK PERFORMANCE")
    print("="*60)
    print(f"Average Latency : {avg_latency:6.2f} ms")
    print(f"Throughput      : {throughput:6.2f} MB/s")
    print(f"Packet Loss     : {packet_loss:6.1f} %")
    print(f"Successful pings: {len(valid)} / {len(latencies)}")
    print("="*60)

    # PLOT
    if valid:
        plt.figure(figsize=(10, 5))
        idx = np.arange(len(latencies))
        good = [l for l in latencies if l is not None]
        bad  = [i for i, l in enumerate(latencies) if l is None]
        plt.plot(idx[:len(good)], good, 'go-', label='Success', markersize=4)
        if bad:
            plt.plot(bad, [avg_latency]*len(bad), 'rx', label='Failed', markersize=8)
        plt.axhline(avg_latency, color='orange', linestyle='--', label=f'Avg {avg_latency:.1f} ms')
        plt.title("Ping Latency Over Time")
        plt.xlabel("Ping #")
        plt.ylabel("Latency (ms)")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()