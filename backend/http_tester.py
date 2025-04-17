import socket
from urllib.parse import urlparse
import ssl

def send_http_request(url, method="GET", headers=None, body=None):
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path or "/"

    if ':' in host:
        host, port_str = host.split(':', 1)
        port = int(port_str)
    else:
        port = 443 if parsed.scheme == 'https' else 80

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)

        if parsed.scheme == 'https':
            context = ssl.create_default_context()
            s = context.wrap_socket(s, server_hostname=host)

        s.connect((host, port))

        header_lines = [
            f"{method} {path} HTTP/1.1",
            f"Host: {host}",
            "Connection: close"
        ]

        if headers:
            for key, value in headers.items():
                header_lines.append(f"{key}: {value}")

        if body:
            header_lines.append(f"Content-Length: {len(body)}")
            header_lines.append("Content-Type: application/x-www-form-urlencoded")

        header_lines.append("")  # blank line before body
        request = "\r\n".join(header_lines) + "\r\n"

        if body:
            request += body

        s.send(request.encode())

        response = b""
        while True:
            data = s.recv(4096)
            if not data:
                break
            response += data
        s.close()

        decoded = response.decode(errors='ignore')
        header_end = decoded.find("\r\n\r\n")
        headers_text = decoded[:header_end]
        body = decoded[header_end+4:] if header_end != -1 else decoded

        status_line = headers_text.splitlines()[0]
        parts = status_line.split()
        status_code = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0

        return {
            "status_code": status_code,
            "body": body
        }

    except Exception as e:
        return {
            "status_code": 0,
            "body": f"Error: {e}"
        }
