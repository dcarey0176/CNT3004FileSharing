import socket
import time
import matplotlib.pyplot as plt

SERVER_HOST = "172.20.10.7"  
SERVER_PORT =  4450        

def measure_latency(client, num_pings=50):
    latencies = []
    for i in range(num_pings):
        try:
            start = time.time()
            client.sendall(b"ping")
            client.recv(1024)
            end = time.time()
            latencies.append((end - start) * 1000)  # ms
        except Exception:
            latencies.append(None)
    return latencies

def measure_throughput(client, size_kb=100, iterations=50):
    data = b"x" * (1024 * size_kb)
    start = time.time()
    for _ in range(iterations):
        client.sendall(data)
    end = time.time()
    total_mb = (size_kb * iterations) / 1024
    duration = end - start
    return total_mb / duration  # MB/s

def calculate_packet_loss(latencies):
    sent = len(latencies)
    received = len([l for l in latencies if l is not None])
    return ((sent - received) / sent) * 100

def run_tests():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_HOST, SERVER_PORT))

    print("Measuring latency...")
    latencies = measure_latency(client)

    print("Measuring throughput...")
    throughput = measure_throughput(client)

    packet_loss = calculate_packet_loss(latencies)
    avg_latency = sum([l for l in latencies if l]) / len([l for l in latencies if l])

    client.close()

    print(f"\n Results:")
    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"Throughput: {throughput:.2f} MB/s")
    print(f"Packet Loss: {packet_loss:.1f}%")

    # Plot latency
    plt.figure(figsize=(8, 4))
    plt.plot([i for i in range(len(latencies))], latencies, marker='o')
    plt.title("Network Latency Over Time")
    plt.xlabel("Ping #")
    plt.ylabel("Latency (ms)")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run_tests()
