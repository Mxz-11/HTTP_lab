import socket
import sys
from datetime import datetime
import os

CLIENT_DIR = 'Client'

def create_socket():
    """Create a plain (non-SSL) TCP socket."""
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_socket(sock, host="localhost", port=80):
    """Connect the socket in plain text."""
    sock.connect((host, port))
    print(f"Connected (plain) to {host}:{port}")

def send_request(sock, message, is_binary=False):
    """
    Send an HTTP request (message) via sock and read the full response.
    If is_binary=False, we read until the server closes and decode as text.
    If is_binary=True, we attempt to parse Content-Length. 
    """
    try:
        # Send the request
        sock.sendall(message.encode('utf-8'))

        if not is_binary:
            # We'll read all data until the server closes
            data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            return data.decode('utf-8', errors='replace')

        # If is_binary=True, parse Content-Length (if present)
        response = b''
        content_length = None
        header_end = None

        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

            if header_end is None:
                header_end = response.find(b"\r\n\r\n")
                if header_end != -1:
                    header_data = response[:header_end].decode('utf-8', errors='replace')
                    for line in header_data.split("\r\n"):
                        if line.lower().startswith("content-length:"):
                            parts = line.split(":", 1)
                            try:
                                content_length = int(parts[1].strip())
                            except:
                                content_length = None
                            break

            if header_end is not None and content_length is not None:
                body_len = len(response) - (header_end + 4)
                if body_len >= content_length:
                    break

        return response

    except Exception as e:
        print(f"Error sending/receiving data: {e}")
        return None

def main():
    """
    1) Pide host/URL, puerto (por defecto 80),
    2) Permite GET, HEAD, POST, PUT, DELETE,
    3) Para POST/PUT, pregunta si quieres “enviar archivo” o meter body manual.
    4) Permite meter headers personalizados. 
    5) Conexión en texto claro (no SSL).
    """

    # 1. Host / URL
    raw_host = input("Enter host or URL (blank for 'localhost'): ").strip()
    if not raw_host:
        raw_host = "localhost"

    # 2. Puerto
    raw_port = input("Enter server port (blank for 80): ").strip()
    if not raw_port:
        port = 80
    else:
        try:
            port = int(raw_port)
        except:
            port = 80

    # 3. Base path (por si quieres un prefijo, no es obligatorio)
    base_path = input("Enter base path (blank for ''): ").strip()

    # Quitamos "http://" o "https://" del host si el usuario lo puso
    for prefix in ["http://", "https://"]:
        if raw_host.startswith(prefix):
            raw_host = raw_host[len(prefix):]
            break
    # Si hay '/', la quitamos (caso “ejemplo.com/test”)
    if "/" in raw_host:
        raw_host = raw_host.split("/", 1)[0]

    print(f"\nUsing host={raw_host}, port={port}, base_path={base_path}")
    print("(No SSL). If the server needs HTTPS on port 443, this will fail.\n")

    while True:
        method = input("Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': ").upper()
        if method == 'EXIT':
            break
        if method not in ["GET","HEAD","POST","PUT","DELETE"]:
            print("Invalid method.")
            continue

        # Resource path
        path = input("Enter the resource path (blank => use base_path): ").strip()
        if not path:
            path = base_path
        if not path.startswith("/"):
            path = "/"+path

        # =========== HEADERS PERSONALIZADOS ============
        # Pedimos tantos headers como quiera el usuario.
        # Ejemplo de header: "Authorization: Bearer 12345"
        # Dejar en blanco => termina.
        custom_headers = []
        print("Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.")
        while True:
            hline = input()
            if not hline.strip():
                break
            custom_headers.append(hline)

        # =========== CUERPO (POST/PUT) O NO ============
        body = ""
        if method in ["POST", "PUT"]:
            choice = input("Send from local file? (y/N): ").strip().lower()
            if choice == 'y':
                # Pedimos el nombre de archivo local
                filename = input("Enter local filename (relative path): ").strip()
                try:
                    with open(filename, 'r') as f:
                        body = f.read()
                except Exception as e:
                    print(f"Error reading file: {e}")
                    body = ""
            else:
                # Body manual
                body = input("Enter the body content (blank if none): ")

        # =========== CONSTRUIR REQUEST ===============
        # 1) Línea de petición
        request = f"{method} {path} HTTP/1.1\r\n"
        # 2) Cabecera Host
        request += f"Host: {raw_host}\r\n"
        # 3) Cabecera Connection
        request += "Connection: close\r\n"
        
        # 4) Si es POST/PUT => Content-Type, Content-Length
        #    Ojo, si el usuario quiere meter sus propios content-type,
        #    puede hacerlo en custom_headers (y sobrescribir lo que pongamos).
        if method in ["POST","PUT"]:
            request += f"Content-Length: {len(body)}\r\n"
            # Añadimos Content-Type por defecto. El user puede meter otro header si desea.
            request += "Content-Type: text/plain\r\n"

        # 5) Ahora inyectamos los headers personalizados
        for h in custom_headers:
            request += h + "\r\n"

        # 6) Línea en blanco
        request += "\r\n"

        # 7) Si hay body, lo concatenamos
        if body:
            request += body

        # =========== ENVIAR REQUEST ===============
        sock = create_socket()
        try:
            connect_socket(sock, raw_host, port)
        except Exception as e:
            print(f"Could not connect: {e}")
            sock.close()
            continue

        # Para HEAD => normal, leemos la respuesta en texto
        is_binary = False

        response = send_request(sock, request, is_binary=is_binary)
        sock.close()

        if response:
            print("\n=== Response ===\n")
            print(response)
        else:
            print("No response or error.")

if __name__ == "__main__":
    main()
