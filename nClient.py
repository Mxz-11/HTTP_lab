import socket
import sys
from datetime import datetime
import os

def create_socket():
    """Create a plain (non-SSL) TCP socket."""
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_socket(sock, host="localhost", port=80):
    """Connect the socket in plain text."""
    sock.connect((host, port))
    print(f"Connected (plain) to {host}:{port}")

def send_request(sock, message, is_binary=False):
    """Send HTTP request and read raw response bytes."""
    try:
        # Send the request
        if isinstance(message, str):
            sock.sendall(message.encode('utf-8'))
        else:
            sock.sendall(message)

        # Read full response as raw bytes
        response = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

        return response

    except Exception as e:
        print(f"Error sending/receiving data: {e}")
        return None


def handle_binary_file(response):
    """Handle any binary data from response (image, audio, video, etc.)"""
    try:
        header_end = response.find(b'\r\n\r\n')
        if header_end == -1:
            return None
        
        headers = response[:header_end].decode('utf-8')
        content = response[header_end + 4:]  # Skip \r\n\r\n

        if '200 OK' not in headers:
            print(f"Error in response: {headers}")
            return None

        # Extraemos Content-Type
        content_type = None
        for line in headers.split('\r\n'):
            if line.startswith('Content-Type:'):
                content_type = line.split(': ')[1].strip()
                break
        
        # Verificamos que al menos sea algo binario que no sea text/*
        if not content_type:
            print("No Content-Type found.")
            return None
        
        allowed_prefixes = ['image/', 'audio/', 'video/']
        if not any(content_type.startswith(prefix) for prefix in allowed_prefixes):
            print(f"Invalid content type for binary: {content_type}")
            return None

        return content
    except Exception as e:
        print(f"Error handling binary file: {e}")
        return None

def handle_response_content(response, is_binary=False):
    """Extract content and headers from response"""
    try:
        header_end = response.find(b'\r\n\r\n') if isinstance(response, bytes) else response.find('\r\n\r\n')
        if header_end == -1:
            return None, None, None

        # Split headers and content
        if isinstance(response, bytes):
            headers = response[:header_end].decode('utf-8')
            content = response[header_end + 4:]
        else:
            headers = response[:header_end]
            content = response[header_end + 4:]
            if is_binary:
                content = content.encode('utf-8')

        # Parse content type
        content_type = None
        for line in headers.split('\r\n'):
            if line.lower().startswith('content-type:'):
                content_type = line.split(':', 1)[1].strip()
                break

        return headers, content_type, content
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None, None, None

def save_response_content(content, filename, is_binary=False):
    """Save content to file in appropriate mode"""
    try:
        mode = 'wb' if is_binary else 'w'
        encoding = None if is_binary else 'utf-8'
        with open(filename, mode, encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

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
        try:
            method = input("\nEnter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': ").upper()
            if method == 'EXIT':
                break
            if method not in ["GET","HEAD","POST","PUT","DELETE"]:
                print("Invalid method.")
                continue

            if method == 'GET':
                path = input("Enter the resource path (blank => use base_path): ").strip()
                if not path:
                    path = base_path
                if not path.startswith("/"):
                    path = "/"+path

                # Detect binary content by extension
                ext = path.split('.')[-1].lower() if '.' in path else ''
                is_binary = ext in ['png','jpg','jpeg','gif','mp3','wav','mp4','avi']

                # Ask if they want to save the response
                save_response = input("Do you want to save the response to a file? (y/N): ").strip().lower() == 'y'
                if save_response:
                    save_filename = input("Enter filename to save response: ").strip()
                    if not save_filename:
                        print("Invalid filename, will only show response")
                        save_response = False

                # Construct and send request
                request = f"GET {path} HTTP/1.1\r\n"
                request += f"Host: {raw_host}\r\n"
                if is_binary:
                    request += "Accept: */*\r\n"
                request += "\r\n"

                sock = create_socket()
                connect_socket(sock, raw_host, port)
                response = send_request(sock, request, is_binary=is_binary)
                sock.close()

                if response:
                    headers, content_type, content = handle_response_content(response, is_binary)
                    if headers:
                        print("\n=== Response Headers ===\n")
                        print(headers)
                        
                        if save_response and content:
                            is_binary_content = content_type and any(t in content_type.lower() 
                                for t in ['image/', 'audio/', 'video/', 'application/octet-stream'])
                            if save_response_content(content, save_filename, is_binary_content):
                                print(f"\nContent saved to: {save_filename}")
                                if not is_binary_content:
                                    print("\n=== Content Preview ===\n")
                                    try:
                                        print(content.decode() if isinstance(content, bytes) else content)
                                    except:
                                        print("(Binary content)")
                continue  # Skip the extra path prompt after GET

            path = input("Enter the resource path (blank => use base_path): ").strip()
            if not path:
                path = base_path
            if not path.startswith("/"):
                path = "/"+path

            # Headers personalizados
            custom_headers = []
            print("Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.")
            while True:
                hline = input()
                if not hline.strip():
                    break
                custom_headers.append(hline)

            # Body handling
            body = None  # Can be str or bytes
            is_binary = False
            content_type = 'text/plain'  # default

            if method in ["POST", "PUT"]:
                choice = input("Send from local file? (y/N): ").strip().lower()
                if choice == 'y':
                    filename = input("Enter local filename (relative path): ").strip()
                    try:
                        # Detect binary by extension
                        ext = filename.lower().split('.')[-1]
                        is_binary = ext in ['png','jpg','jpeg','gif','mp3','wav','mp4','avi']
                        
                        # Set appropriate content type
                        content_type = 'application/octet-stream'  # default binary
                        if ext in ['jpg', 'jpeg']:
                            content_type = 'image/jpeg'
                        elif ext == 'png':
                            content_type = 'image/png'
                        elif ext == 'gif':
                            content_type = 'image/gif'
                        elif ext == 'mp3':
                            content_type = 'audio/mpeg'
                        elif ext == 'wav':
                            content_type = 'audio/wav'
                        elif ext in ['txt', 'html', 'css', 'json']:
                            content_type = 'text/plain'
                            is_binary = False
                        
                        # Read file in appropriate mode
                        mode = 'rb' if is_binary else 'r'
                        with open(filename, mode) as f:
                            body = f.read()
                            
                        # Construct multipart request if binary
                        if is_binary:
                            boundary = "----WebKitFormBoundary" + datetime.now().strftime("%Y%m%d%H%M%S")
                            request_parts = []
                            request_parts.append(f"{method} {path} HTTP/1.1")
                            request_parts.append(f"Host: {raw_host}")
                            request_parts.append(f"Content-Type: multipart/form-data; boundary={boundary}")
                            request_parts.append(f"Content-Length: {len(body)}")
                            request_parts.extend(custom_headers)
                            request_parts.append("")
                            request = "\r\n".join(request_parts).encode('utf-8')
                            request += b"\r\n" + body
                        else:
                            # Text content handling remains the same
                            request_parts = []
                            request_parts.append(f"{method} {path} HTTP/1.1")
                            request_parts.append(f"Host: {raw_host}")
                            request_parts.append(f"Content-Type: {content_type}")
                            request_parts.append(f"Content-Length: {len(body)}")
                            request_parts.extend(custom_headers)
                            request_parts.append("")
                            request = "\r\n".join(request_parts)
                            if isinstance(body, bytes):
                                request = request.encode('utf-8') + b"\r\n" + body
                            else:
                                request = request + "\r\n" + body
                                
                    except Exception as e:
                        print(f"Error reading file: {e}")
                        continue

            # Construct request
            request_parts = []
            request_parts.append(f"{method} {path} HTTP/1.1")
            request_parts.append(f"Host: {raw_host}")
            request_parts.append(f"Content-Type: {content_type}")
            
            if body is not None:
                request_parts.append(f"Content-Length: {len(body)}")
            
            # Add custom headers
            request_parts.extend(custom_headers)
            
            # Add blank line to separate headers
            request_parts.append("")
            
            # Join headers
            headers = "\r\n".join(request_parts)
            
            # Construct final request
            if body is not None:
                if isinstance(body, bytes):
                    request = headers.encode('utf-8') + b"\r\n" + body
                else:
                    request = headers + "\r\n" + body
            else:
                request = headers + "\r\n"

            # Send request
            sock = create_socket()
            connect_socket(sock, raw_host, port)
            response = send_request(sock, request, is_binary=is_binary)
            sock.close()

            if response:
                print("\n=== Response ===\n")
                print(response)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
