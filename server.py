# -*- coding: utf-8 -*-
"""
Authors:
    - Author Mxz11
    - Añadir vuestros nombres aquí!

Description:
    This script is used for handling the server of the HTTP client-server system.

How to compile:
    1. Make sure you have Python installed (version Python 3.12.4 or higher).
    2. Open a terminal or command prompt.
    3. Navigate to the directory where this script is located.
    4. Run the script with the following command:
        python3 server.py
    
    Note: If you're using a virtual environment, activate it before running the script.

Creation Date:
    19/3/2025

Last Modified:
    19/3/2025

"""

import socket
import json
import threading
import os
from datetime import datetime

class SimpleHTTPServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.resources = {}
        self.server_dir = 'Server'  # Base directory for all server operations
        
        # Create server directory if it doesn't exist
        os.makedirs(self.server_dir, exist_ok=True)
        
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Add these two lines to allow port reuse
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Servidor HTTP escuchando en {self.host}:{self.port}")
        
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Conexión entrante de {addr}")
            threading.Thread(target=self.handle_request, args=(client_socket,)).start()
    
    def handle_request(self, client_socket):
        try:
            request_data = client_socket.recv(1024).decode(errors='ignore')
            if not request_data:
                return
            
            print(f"Received request:\n{request_data}")  # Debug print
            
            request_lines = request_data.split("\r\n")
            request_line = request_lines[0]
            method, path, _ = request_line.split()
            
            print(f"Method: {method}, Path: {path}")  # Debug print
            
            headers = {}
            body = ""
            header_section = True
            for line in request_lines[1:]:
                if line == "":
                    header_section = False
                    continue
                if header_section:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()
                else:
                    body += line + "\n"
            
            response = ""
            if method == "GET":
                file_name = path[1:] if path.startswith('/') else path
                response = self.serve_static(file_name, headers)
            elif method == "PUT":
                file_name = path[1:] if path.startswith('/') else path
                response = self.handle_put(file_name, headers, body)
            elif method == "DELETE":
                file_name = path[1:] if path.startswith('/') else path
                response = self.delete_file(file_name)
            elif path.startswith("/resource"):
                response = self.handle_resource(method, path, body)
            else:
                response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
            
            print(f"Sending response...")  # Debug print
            if isinstance(response, str):
                client_socket.sendall(response.encode())
            else:
                client_socket.sendall(response)
            
        except Exception as e:
            print(f"Error handling request: {e}")
            error_response = "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n"
            try:
                client_socket.sendall(error_response.encode())
            except:
                pass
        finally:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            client_socket.close()
    
    def get_content_type(self, file_path):
        extension = file_path.split('.')[-1].lower()
        content_types = {
            # Text files
            'txt': 'text/plain',
            'html': 'text/html',
            'css': 'text/css',
            'md': 'text/markdown',
            # Application files
            'json': 'application/json',
            'pdf': 'application/pdf',
            'xml': 'application/xml',
            # Image files
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'webp': 'image/webp',
            # Audio files
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'mp4': 'audio/mp4',  # For audio MP4
            # Video files
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo'
        }
        return content_types.get(extension, 'application/octet-stream')

    def serve_static(self, file_path, headers=None):
        try:
            # Join with server directory and normalize path
            full_path = os.path.join(self.server_dir, os.path.normpath(file_path))
            
            # Ensure file is within server directory (prevent directory traversal)
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.server_dir)):
                print(f"Attempted directory traversal: {file_path}")
                return "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n".encode()
            
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                print(f"File not found or invalid: {full_path}")
                return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n".encode()
            
            # Get file's last modification time for If-Modified-Since
            if headers and 'If-Modified-Since' in headers:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
                try:
                    client_time = datetime.strptime(headers['If-Modified-Since'], '%Y-%m-%d %H:%M:%S')
                    if file_mtime <= client_time:
                        return "HTTP/1.1 304 Not Modified\r\nContent-Length: 0\r\n\r\n".encode()
                    else:
                        return "HTTP/1.1 200 OK\r\nContent-Length: 1\r\n\r\n1".encode()
                except ValueError as e:
                    print(f"Error parsing If-Modified-Since date: {e}")
            
            # Handle different content types
            content_type = self.get_content_type(full_path)
            
            # Read file in binary mode for all types
            with open(full_path, 'rb') as file:
                content = file.read()
            
            # Build response headers
            response_headers = "HTTP/1.1 200 OK\r\n"
            response_headers += f"Content-Type: {content_type}\r\n"
            response_headers += f"Content-Length: {len(content)}\r\n"
            response_headers += "Connection: close\r\n\r\n"
            
            # Return response headers + content as bytes
            return response_headers.encode() + content
                
        except Exception as e:
            print(f"Error serving file: {e}")
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n".encode()
    
    def delete_file(self, file_path):
        try:
            # Join with server directory and normalize path
            full_path = os.path.join(self.server_dir, os.path.normpath(file_path))
            
            # Ensure file is within server directory
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.server_dir)):
                print(f"Attempted directory traversal: {file_path}")
                return "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n"
            
            if os.path.exists(full_path):
                os.remove(full_path)
                response = "HTTP/1.1 200 OK\r\n"
                response += "Content-Type: text/plain\r\n"
                message = f"File {file_path} was successfully deleted"
                response += f"Content-Length: {len(message)}\r\n"
                response += "\r\n"
                response += message
                return response
            else:
                print(f"File not found: {full_path}")
                return "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 0\r\n\r\n"
        except Exception as e:
            print(f"Error deleting file: {e}")
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n"
    
    def handle_put(self, file_path, headers, content):
        try:
            # Normalize path and join with server directory
            full_path = os.path.join(self.server_dir, os.path.basename(file_path))
            
            # Ensure file path is within server directory
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.server_dir)):
                return "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n".encode()
            
            # Write content to file
            was_existing = os.path.exists(full_path)
            with open(full_path, 'w') as file:
                file.write(content)
            
            status = "200 OK" if was_existing else "201 Created"
            print(f"File {file_path} {'updated' if was_existing else 'created'} in Server directory")
            
            response = f"HTTP/1.1 {status}\r\n"
            response += "Content-Type: text/plain\r\n"
            message = f"File {file_path} was successfully {'updated' if was_existing else 'created'}"
            response += f"Content-Length: {len(message)}\r\n"
            response += "\r\n"
            response += message
            return response.encode()
            
        except Exception as e:
            print(f"Error handling PUT request: {e}")
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n".encode()
    
    def handle_resource(self, method, path, body):
        resource_id = path.split("/")[-1]
        
        if method == "GET":
            return self.respond_with_json(self.resources)
        elif method == "POST":
            try:
                resource = json.loads(body)
                self.resources[resource_id] = resource
                return "HTTP/1.1 201 Created\r\nContent-Length: 0\r\n\r\n"
            except json.JSONDecodeError:
                return "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"
        elif method == "PUT":
            if resource_id in self.resources:
                try:
                    updated_resource = json.loads(body)
                    self.resources[resource_id] = updated_resource
                    return "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
                except json.JSONDecodeError:
                    return "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"
            return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
        elif method == "DELETE":
            if resource_id in self.resources:
                del self.resources[resource_id]
                return "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
            return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
        return "HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n"
    
    def respond_with_json(self, data):
        json_data = json.dumps(data)
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(json_data)}\r\n\r\n{json_data}"
    
if __name__ == "__main__":
    server = SimpleHTTPServer()
    server.start()