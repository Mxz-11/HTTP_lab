# -*- coding: utf-8 -*-
"""
Authors:
    - Author Mxz11
    - Jorge Giménez
    - Alex Langarita
    - Arkaitz Subías

Description:
    Este script gestiona el cliente del sistema cliente-servidor HTTP.

How to execute:
    1. Asegúrate de tener Python instalado (versión 3.12.4 o superior).
    2. Abre una terminal o línea de comandos.
    3. Navega hasta el directorio donde se encuentre este script.
    4. Ejecuta el script con:
           python3 nClient.py
    Se le solicitará al usuario el puerto para iniciar el servidor.

Creation Date:
    19/3/2025

Last Modified:
    19/3/2025
"""
import socket
from datetime import datetime

class HttpClient:
    def __init__(self, host="localhost", port=80, timeout=8):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        print(f"Connected (plain) to {self.host}:{self.port}")

    def send_request(self, message, is_binary=False):
        try:
            if isinstance(message, str):
                self.sock.sendall(message.encode('utf-8'))
            else:
                self.sock.sendall(message)
            response = b''
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            if not is_binary:
                return response.decode('utf-8', errors='replace')
            return response
        except Exception as e:
            print(f"Error sending/receiving data: {e}")
            return None

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

class HttpResponseUtils:
    @staticmethod
    def parse_response(response, is_binary=False):
        try:
            if isinstance(response, bytes):
                header_end = response.find(b'\r\n\r\n')
                if header_end == -1:
                    return None, None, None
                headers = response[:header_end].decode('utf-8', errors='replace')
                content = response[header_end + 4:]
            else:
                header_end = response.find('\r\n\r\n')
                if header_end == -1:
                    return None, None, None
                headers = response[:header_end]
                content = response[header_end + 4:]
                if is_binary:
                    content = content.encode('utf-8')
            content_type = None
            for line in headers.split('\r\n'):
                if line.lower().startswith('content-type:'):
                    content_type = line.split(':', 1)[1].strip()
                    break
            return headers, content_type, content
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None, None, None

    @staticmethod
    def save_content(content, filename, is_binary=False):
        try:
            mode = 'wb' if is_binary else 'w'
            encoding = None if is_binary else 'utf-8'
            with open(filename, mode, encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

def build_request(method, path, host, custom_headers=None, body=None, content_type=None, is_binary=False, boundary=None):
    if not path.startswith("/"):
        path = "/" + path
    headers = [
        f"{method} {path} HTTP/1.1",
        f"Host: {host}",
        "Connection: close"
    ]
    if content_type:
        if boundary:
            headers.append(f"Content-Type: multipart/form-data; boundary={boundary}")
        else:
            headers.append(f"Content-Type: {content_type}")
    if body is not None:
        if isinstance(body, bytes):
            headers.append(f"Content-Length: {len(body)}")
        else:
            headers.append(f"Content-Length: {len(body.encode('utf-8'))}")
    if custom_headers:
        headers.extend(custom_headers)
    headers.append("")
    if body is not None:
        if isinstance(body, bytes):
            request = "\r\n".join(headers).encode('utf-8') + b"\r\n" + body
        else:
            request = "\r\n".join(headers) + "\r\n" + body
    else:
        request = "\r\n".join(headers) + "\r\n"
    return request

def get_user_input():
    raw_host = input("Enter host or URL (blank for 'localhost'): ").strip() or "localhost"
    raw_port = input("Enter server port (blank for 80): ").strip()
    port = int(raw_port) if raw_port.isdigit() else 80
    base_path = input("Enter base path (blank for ''): ").strip()
    for prefix in ["http://", "https://"]:
        if raw_host.startswith(prefix):
            raw_host = raw_host[len(prefix):]
            break
    if "/" in raw_host:
        raw_host = raw_host.split("/", 1)[0]
    print(f"\nUsing host={raw_host}, port={port}, base_path={base_path}")
    print("(No SSL). If the server needs HTTPS on port 443, this will fail.\n")
    return raw_host, port, base_path

def get_custom_headers():
    headers = []
    print("Enter any custom headers (blank line to finish):")
    while True:
        h = input().strip()
        if not h:
            break
        headers.append(h)
    return headers

def get_body_from_input():
    print("Enter body content in JSON format (end input with a blank line):")
    lines = []
    while True:
        l = input()
        if not l.strip():
            break
        lines.append(l)
    return "\n".join(lines)

def get_body_for_post_put(path, method):
    skip_file = False
    content_type = None
    boundary = None
    body = None
    if path.startswith("/resources"):
        parts = path.strip("/").split("/")
        if method == "POST":
            if len(parts) == 1:
                cat = input("Enter resource category: ").strip()
                path = f"/resources/{cat}"
            elif len(parts) != 2:
                print("Invalid POST path. Format: /resources/{category}")
                return path, None, None, None, True
        elif method == "PUT":
            if len(parts) == 1:
                cat = input("Enter resource category: ").strip()
                path = f"/resources/{cat}"
            elif len(parts) != 3:
                print("Invalid PUT path. Format: /resources/{category}/{id}")
                return path, None, None, None, True
        body = get_body_from_input()
        content_type = "application/json"
        skip_file = True
    return path, body, content_type, boundary, skip_file

def get_body_from_file():
    filename = input("Enter local filename (relative path): ").strip()
    ext = filename.lower().split('.')[-1]
    is_binary = ext in ['png','jpg','jpeg','gif','mp3','wav','mp4','avi']
    content_type = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif',
        'mp3': 'audio/mpeg', 'wav': 'audio/wav'
    }.get(ext, 'application/octet-stream')
    if ext in ['txt','html','css','json']:
        content_type = 'text/plain'
        is_binary = False
    mode = 'rb' if is_binary else 'r'
    with open(filename, mode) as f:
        body = f.read()
    boundary = "----WebKitFormBoundary" + datetime.now().strftime("%Y%m%d%H%M%S") if is_binary else None
    return body, content_type, is_binary, boundary

def save_and_preview(headers, content_type, content):
    is_binary_content = content_type and any(t in content_type.lower() for t in ['image/', 'audio/', 'video/', 'application/octet-stream'])
    if input("Do you want to save the response to a file? (y/N): ").strip().lower() == 'y':
        save_filename = input("Enter filename to save response: ").strip()
        if save_filename and content:
            if HttpResponseUtils.save_content(content, save_filename, is_binary_content):
                print(f"\nContent saved to: {save_filename}")
    if content and not is_binary_content:
        print("\n=== Content Preview ===\n")
        try:
            print(content.decode() if isinstance(content, bytes) else content)
        except:
            print("(Binary content)")

def main():
    raw_host, port, base_path = get_user_input()
    while True:
        try:
            method = input("\nEnter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': ").upper()
            if method == 'EXIT':
                break
            if method not in ["GET","HEAD","POST","PUT","DELETE"]:
                print("Invalid method.")
                continue
            path = input("Enter the resource path (blank => use base_path): ").strip() or base_path
            custom_headers = get_custom_headers()
            body = None
            is_binary = False
            content_type = None
            boundary = None
            if method == 'GET':
                ext = path.split('.')[-1].lower() if '.' in path else ''
                is_binary = ext in ['png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'mp4', 'avi']
            if method in ["POST","PUT"]:
                path, body, content_type, boundary, skip_file = get_body_for_post_put(path, method)
                if not skip_file:
                    if input("Send from local file? (y/N): ").strip().lower() == 'y':
                        try:
                            body, content_type, is_binary, boundary = get_body_from_file()
                        except Exception as e:
                            print(f"Error reading file: {e}")
                            continue
                    else:
                        body = get_body_from_input()
                        content_type = "application/json"
            request = build_request(
                method=method,
                path=path,
                host=raw_host,
                custom_headers=custom_headers,
                body=body,
                content_type=content_type,
                is_binary=is_binary,
                boundary=boundary
            )
            client = HttpClient(raw_host, port)
            client.connect()
            response = client.send_request(request, is_binary=is_binary)
            client.close()
            if response:
                headers, content_type, content = HttpResponseUtils.parse_response(response, is_binary)
                if headers:
                    print("\n=== Response Headers ===\n")
                    print(headers)
                    save_and_preview(headers, content_type, content)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()