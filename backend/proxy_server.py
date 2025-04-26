import socket
import threading
import time

request_history = []
response_history = []

def handle_client(client_socket):
    request = client_socket.recv(4096)
    request_line = request.decode(errors='ignore').split('\n')[0]
    
    if not request_line:
        client_socket.close()
        return

    method, path, _ = request_line.split()
    url = path.split("/")[2]
    target_host = url
    port = 80

    # Save request log
    request_history.append({
        "timestamp": time.time(),
        "method": method,
        "url": path
    })

    # Forward request
    try:
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((target_host, port))
        remote_socket.sendall(request)

        response = b""
        while True:
            data = remote_socket.recv(4096)
            if not data:
                break
            response += data
            client_socket.send(data)

        # Save response log
        response_history.append({
            "timestamp": time.time(),
            "status": response.split(b' ')[1].decode(errors='ignore'),
            "url": path
        })

        remote_socket.close()
    except Exception as e:
        print(f"Proxy error: {e}")
    
    client_socket.close()

def start_proxy():
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind(('0.0.0.0', 8888))
    proxy.listen(100)
    print("Proxy running on port 8888...")

    while True:
        client_socket, addr = proxy.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    start_proxy()
