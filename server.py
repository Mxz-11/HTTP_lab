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

class SimpleHTTPServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.resources = {}  # Diccionario en memoria para almacenar recursos dinámicos
        
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
            if method == "GET" and (path.endswith('.html') or path.endswith('.txt')):
                print(f"Serving file: {path}")  # Debug print
                file_name = path[1:] if path.startswith('/') else path
                response = self.serve_static(file_name)
            elif method == "DELETE":
                file_name = path[1:] if path.startswith('/') else path
                response = self.delete_file(file_name)
            elif path.startswith("/resource"):
                response = self.handle_resource(method, path, body)
            else:
                response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
            
            print(f"Sending response:\n{response}")  # Debug print
            client_socket.sendall(response.encode())
            
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
    
    def serve_static(self, file_path):
        try:
            print(f"Opening file: {file_path}")  # Debug print
            with open(file_path, "r") as file:
                content = file.read()
            
            # Determine content type based on file extension
            content_type = "text/html" if file_path.endswith('.html') else "text/plain"
            
            response = "HTTP/1.1 200 OK\r\n"
            response += f"Content-Type: {content_type}\r\n"
            response += f"Content-Length: {len(content)}\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            response += content
            
            return response
        except FileNotFoundError:
            print(f"File not found: {file_path}")  # Debug print
            return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
        except Exception as e:
            print(f"Error reading file: {e}")  # Debug print
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    
    def delete_file(self, file_path):
        try:
            print(f"Attempting to delete file: {file_path}")
            import os
            if os.path.exists(file_path):
                os.remove(file_path)
                response = "HTTP/1.1 200 OK\r\n"
                response += "Content-Type: text/plain\r\n"
                message = f"File {file_path} was successfully deleted"
                response += f"Content-Length: {len(message)}\r\n"
                response += "\r\n"
                response += message
                return response
            else:
                print(f"File not found: {file_path}")
                return "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 0\r\n\r\n"
        except Exception as e:
            print(f"Error deleting file: {e}")
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n"
    
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