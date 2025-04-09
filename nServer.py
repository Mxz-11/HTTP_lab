# -*- coding: utf-8 -*-
"""
Authors:
    - Author Mxz11
    - Añadir vuestros nombres aquí!

Description:
    Este script gestiona el servidor del sistema cliente-servidor HTTP.

How to execute:
    1. Asegúrate de tener Python instalado (versión 3.12.4 o superior).
    2. Abre una terminal o línea de comandos.
    3. Navega hasta el directorio donde se encuentre este script.
    4. Ejecuta el script con:
           python3 server.py
    Se le solicitará al usuario el puerto para iniciar el servidor.

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
        self.server_dir = 'Server'  # Directorio base para operaciones del servidor
        
        # Crear el directorio del servidor si no existe
        os.makedirs(self.server_dir, exist_ok=True)
        
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Permitir reutilización del puerto
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_socket.bind((self.host, self.port))
        except Exception as e:
            print(f"Error al enlazar el servidor en {self.host}:{self.port} -> {e}")
            return
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
            
            print(f"Received request:\n{request_data}")
            
            request_lines = request_data.split("\r\n")
            request_line = request_lines[0]
            method, path, _ = request_line.split()
            
            print(f"Method: {method}, Path: {path}")
            
            # Si se usa HEAD, la tratamos como GET para generar la respuesta y luego eliminamos el cuerpo.
            head_request = False
            if method.upper() == "HEAD":
                head_request = True
                method = "GET"
            
            headers = {}
            body = ""
            header_section = True
            for line in request_lines[1:]:
                if line == "":
                    header_section = False
                    continue
                if header_section:
                    if ':' in line:
                        key, value = line.split(":", 1)
                        headers[key.strip()] = value.strip()
                else:
                    body += line + "\n"
            
            response = ""
            # Si la ruta comienza con /resource se gestionan recursos en memoria
            if path.startswith("/resource"):
                response = self.handle_resource(method, path, body)
            elif method == "GET":
                file_name = path[1:] if path.startswith('/') else path
                response = self.serve_static(file_name, headers)
            elif method == "PUT":
                file_name = path[1:] if path.startswith('/') else path
                response = self.handle_put(file_name, headers, body)
            elif method == "DELETE":
                file_name = path[1:] if path.startswith('/') else path
                response = self.delete_file(file_name)
            else:
                response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
            
            # Si es una solicitud HEAD, eliminamos el cuerpo y dejamos solo los encabezados
            if head_request:
                if isinstance(response, str):
                    sep = "\r\n\r\n"
                    pos = response.find(sep)
                    if pos != -1:
                        response = response[:pos+len(sep)]
                else:  # Si es bytes
                    sep = b"\r\n\r\n"
                    pos = response.find(sep)
                    if pos != -1:
                        response = response[:pos+len(sep)]
            
            print("Sending response...")
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
            # Archivos de texto
            'txt': 'text/plain',
            'html': 'text/html',
            'css': 'text/css',
            'md': 'text/markdown',
            # Archivos de aplicación
            'json': 'application/json',
            'pdf': 'application/pdf',
            'xml': 'application/xml',
            # Imágenes
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'webp': 'image/webp',
            # Audio
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            # Vídeo
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo'
        }
        return content_types.get(extension, 'application/octet-stream')

    def serve_static(self, file_path, headers=None):
        try:
            full_path = os.path.join(self.server_dir, os.path.normpath(file_path))
            
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n".encode()
            
            # Verificar el header If-Modified-Since
            if headers and 'If-Modified-Since' in headers:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
                try:
                    client_time = datetime.strptime(headers['If-Modified-Since'], '%Y-%m-%d %H:%M:%S')
                    if file_mtime <= client_time:
                        response_headers = "HTTP/1.1 304 Not Modified\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
                        return response_headers.encode()
                except ValueError as e:
                    print(f"Error al parsear la fecha If-Modified-Since: {e}")
            
            content_type = self.get_content_type(full_path)
            with open(full_path, 'rb') as file:
                content = file.read()
            
            response_headers = "HTTP/1.1 200 OK\r\n"
            response_headers += f"Content-Type: {content_type}\r\n"
            response_headers += f"Content-Length: {len(content)}\r\n"
            response_headers += "Connection: close\r\n\r\n"
            
            return response_headers.encode() + content
        except Exception as e:
            print(f"Error serving file: {e}")
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n".encode()
    
    def delete_file(self, file_path):
        try:
            full_path = os.path.join(self.server_dir, os.path.normpath(file_path))
            
            # Asegurarse de que se esté operando dentro del directorio del servidor
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.server_dir)):
                print(f"Intento de traversal de directorios: {file_path}")
                return "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n"
            
            if os.path.exists(full_path):
                os.remove(full_path)
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
                message = f"File {file_path} was successfully deleted"
                response += f"Content-Length: {len(message)}\r\n\r\n"
                response += message
                return response
            else:
                print(f"Archivo no encontrado: {full_path}")
                return "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 0\r\n\r\n"
        except Exception as e:
            print(f"Error deleting file: {e}")
            return "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n"
    
    def handle_put(self, file_path, headers, content):
        try:
            full_path = os.path.join(self.server_dir, os.path.basename(file_path))
            
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.server_dir)):
                return "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n".encode()
            
            was_existing = os.path.exists(full_path)
            with open(full_path, 'w') as file:
                file.write(content)
            
            status = "200 OK" if was_existing else "201 Created"
            print(f"Archivo {file_path} {'actualizado' if was_existing else 'creado'} en el directorio del servidor")
            
            response = f"HTTP/1.1 {status}\r\n"
            response += "Content-Type: text/plain\r\n"
            message = f"File {file_path} was successfully {'updated' if was_existing else 'created'}"
            response += f"Content-Length: {len(message)}\r\n\r\n"
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
        response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
        response += f"Content-Length: {len(json_data)}\r\n\r\n"
        response += json_data
        return response

if __name__ == "__main__":
    try:
        port_input = input("Ingresa el puerto para iniciar el servidor (por defecto 8080): ").strip()
        if port_input == "":
            port = 8080
        else:
            try:
                port = int(port_input)
            except ValueError:
                print("Puerto inválido, se usará 8080")
                port = 8080
    except KeyboardInterrupt:
        print("\nEjecución cancelada por el usuario.")
        exit()

    server = SimpleHTTPServer(port=port)
    server.start()
