import socket
import time
from urllib.parse import urlparse

request_history = []
response_history = []

def handle_proxy_request(url, method="GET"):
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path or "/"
    port = 80

    request_line = f"{method} {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
    request_history.append({
        "timestamp": time.time(),
        "method": method,
        "url": url
    })

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(request_line.encode())

        response = b""
        while True:
            data = s.recv(4096)
            if not data:
                break
            response += data
        s.close()

        header_end = response.find(b"\r\n\r\n")
        body = response[header_end+4:] if header_end != -1 else b""

        response_history.append({
            "timestamp": time.time(),
            "status": response.split(b' ')[1].decode(errors='ignore'),
            "url": url
        })

        return {
            "status_code": int(response.split(b' ')[1]),
            "body": body.decode(errors='ignore')[:300]
        }
    except Exception as e:
        return {"error": str(e)}