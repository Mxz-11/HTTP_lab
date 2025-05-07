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
import sys
from datetime import datetime
import os

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 80
BUFFER_SIZE = 4096
SOCKET_TIMEOUT = 8


def create_socket(timeout=SOCKET_TIMEOUT):
    """Create a TCP socket with a timeout."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    return sock


def connect_socket(sock, host, port):
    """Connect the socket to the specified host and port."""
    sock.connect((host, port))
    print(f"Connected to {host}:{port}")


def send_request(sock, request_data, is_binary=False):
    """Send raw request data and receive response."""
    try:
        sock.sendall(request_data if isinstance(request_data, bytes) else request_data.encode('utf-8'))
        response = bytearray()
        while True:
            chunk = sock.recv(BUFFER_SIZE)
            if not chunk:
                break
            response.extend(chunk)
        return bytes(response)
    except Exception as e:
        print(f"Error during send/receive: {e}")
        return None


def parse_response(raw_response, is_binary=False):
    """Split raw response into headers string, content-type, and body bytes."""
    if raw_response is None:
        return None, None, None

    header_end = raw_response.find(b"\r\n\r\n")
    if header_end == -1:
        return None, None, None

    header_bytes = raw_response[:header_end]
    body = raw_response[header_end + 4:]
    headers = header_bytes.decode('utf-8', errors='replace')

    content_type = None
    for line in headers.split('\r\n'):
        if line.lower().startswith('content-type:'):
            content_type = line.split(':', 1)[1].strip()
            break
    return headers, content_type, body


def save_content(body, filename, is_binary=False):
    """Save body to file in binary or text mode."""
    mode = 'wb' if is_binary else 'w'
    encoding = None if is_binary else 'utf-8'
    try:
        with open(filename, mode, encoding=encoding) as f:
            f.write(body)
        print(f"Saved content to {filename}")
    except Exception as e:
        print(f"Failed to save file: {e}")


def prompt_custom_headers():
    """Collect custom headers from user until blank line."""
    headers = []
    print("Custom headers (blank to finish):")
    while True:
        line = input().strip()
        if not line:
            break
        headers.append(line)
    return headers


def build_request(method, path, host, custom_headers, content_type=None, body=None):
    """Construct full HTTP/1.1 request as bytes."""
    lines = [f"{method} {path} HTTP/1.1",
             f"Host: {host}",
             "Connection: close"]
    if content_type:
        lines.append(f"Content-Type: {content_type}")
    if body is not None:
        length = len(body) if isinstance(body, (bytes, bytearray)) else len(body.encode('utf-8'))
        lines.append(f"Content-Length: {length}")
    lines.extend(custom_headers)
    header_section = "\r\n".join(lines) + "\r\n\r\n"

    if body is not None:
        if isinstance(body, (bytes, bytearray)):
            return header_section.encode('utf-8') + body
        else:
            return header_section + body
    return header_section


def main():
    host = input(f"Host or URL (blank for '{DEFAULT_HOST}'): ").strip() or DEFAULT_HOST
    port_input = input(f"Port (blank for {DEFAULT_PORT}): ").strip()
    try:
        port = int(port_input) if port_input else DEFAULT_PORT
    except ValueError:
        port = DEFAULT_PORT

    base_path = input("Base path (blank for ''): ").strip()

    for prefix in ("http://", "https://"):
        if host.startswith(prefix):
            host = host[len(prefix):]
    host = host.split('/', 1)[0]

    print(f"\nUsing: host={host}, port={port}, base_path={base_path}\n")

    while True:
        method = input("HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': ").upper().strip()
        if method == 'EXIT':
            print("Exiting.")
            break
        if method not in ("GET","HEAD","POST","PUT","DELETE"):
            print("Invalid method.")
            continue

        path = input("Resource path (blank uses base_path): ").strip() or base_path
        if not path.startswith('/'):
            path = '/' + path

        custom_headers = prompt_custom_headers()

        if method == 'GET':
            ext = os.path.splitext(path)[1].lower().strip('.')
            is_binary = ext in ['png','jpg','jpeg','gif','mp3','wav','mp4','avi']

            save = input("Save response to file? (y/N): ").lower() == 'y'
            filename = None
            if save:
                filename = input("Filename: ").strip() or None

            raw_request = build_request(method, path, host, custom_headers)
            sock = create_socket()
            connect_socket(sock, host, port)
            raw_resp = send_request(sock, raw_request, is_binary)
            sock.close()

            headers, content_type, body = parse_response(raw_resp, is_binary)
            if headers:
                print("\n=== Response Headers ===\n", headers)
                if save and filename and body is not None:
                    save_content(body, filename, is_binary)
                if body and not (content_type and content_type.startswith(('image/','audio/','video/','application/octet-stream'))):
                    print("\n=== Body ===\n", body.decode('utf-8', errors='replace'))
            continue

        body = None
        is_binary = False
        content_type = None

        if method in ('POST','PUT'):
            use_file = input("Send from local file? (y/N): ").lower() == 'y'
            if use_file:
                fname = input("Local filename: ").strip()
                try:
                    is_binary = not fname.lower().endswith(('.txt','.json','.html','.css'))
                    mode = 'rb' if is_binary else 'r'
                    with open(fname, mode) as f:
                        body = f.read()

                    content_type = 'application/octet-stream' if is_binary else 'text/plain'
                except Exception as e:
                    print(f"Cannot read file: {e}")
                    continue
            else:
                lines = []
                print("Enter body (end with blank line):")
                while True:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                body = '\n'.join(lines)
                content_type = 'application/json'

        raw_request = build_request(method, path, host, custom_headers, content_type, body)
        sock = create_socket()
        connect_socket(sock, host, port)
        raw_resp = send_request(sock, raw_request, is_binary)
        sock.close()

        if raw_resp:
            print("\n=== Response ===\n", raw_resp.decode('utf-8', errors='replace'))


if __name__ == '__main__':
    main()
