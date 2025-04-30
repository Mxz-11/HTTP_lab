# -*- coding: utf-8 -*-
"""
Authors:
    - Author Mxz11
    - Añadir vuestros nombres aquí!

Description:
    Este script gestiona el servidor del sistema cliente-servidor HTTP.
    Se ha añadido lo siguiente:
      - Restricción para impedir el acceso a la carpeta "private" (excepto para el endpoint /resources).
      - Endpoint /resources que gestiona los recursos del servidor a partir del archivo:
          Server/private/resources.json.
        Para este endpoint:
          - GET a /resources devuelve todo el contenido.
          - GET a /resources/{categoria} devuelve la lista de objetos de esa categoría.
          - GET a /resources/{categoria}/{id} devuelve el objeto cuyo campo "id" coincide.
          - POST a /resources/{categoria} añade un nuevo objeto (se asigna un id nuevo).
          - PUT a /resources/{categoria} reemplaza toda la categoría (se espera un array JSON).
          - PUT a /resources/{categoria}/{id} actualiza el objeto con ese id.
          - DELETE a /resources/{categoria}/{id} elimina el objeto con ese id.

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
        self.resources = {}  # para el endpoint /resource (en memoria)
        self.server_dir = 'Server'  # Directorio base para operaciones del servidor
        
        # Crear el directorio del servidor si no existe
        os.makedirs(self.server_dir, exist_ok=True)
        
    def is_private(self, file_path):
        """
        Retorna True si file_path (camino relativo) apunta a la carpeta "private".
        Se considera privado si el camino normalizado es "private" o comienza con "private" + os.sep.
        """
        normalized_path = os.path.normpath(file_path)
        return normalized_path == "private" or normalized_path.startswith("private" + os.sep)
        
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
            # Leer headers primero
            request_data = b''
            while b'\r\n\r\n' not in request_data:
                chunk = client_socket.recv(4096)
                if not chunk:
                    return
                request_data += chunk

            # Separar headers y empezar a procesar el cuerpo
            header_end = request_data.find(b'\r\n\r\n')
            headers_raw = request_data[:header_end].decode('utf-8', errors='ignore')
            
            # Parsear la primera línea y headers
            request_lines = headers_raw.split('\r\n')
            request_line = request_lines[0]
            method, path, _ = request_line.split()
            
            # Parsear headers
            headers = {}
            for line in request_lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()

            # Si hay Content-Length, leer el cuerpo
            body = b''
            if 'Content-Length' in headers:
                content_length = int(headers['Content-Length'])
                body = request_data[header_end + 4:]  # Agregar lo que ya leímos después de los headers
                
                # Seguir leyendo hasta completar el content-length
                while len(body) < content_length:
                    chunk = client_socket.recv(min(4096, content_length - len(body)))
                    if not chunk:
                        break
                    body += chunk

            print(f"Method: {method}, Path: {path}")

            response = ""
            if path.startswith("/resources"):
                response = self.handle_resources(method, path, body, headers)
            elif path.startswith("/resource"):
                response = self.handle_resource(method, path, body)
            else:
                file_name = path[1:] if path.startswith('/') else path
                if self.is_private(file_name):
                    response = "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n"
                elif method == "GET":
                    response = self.serve_static(file_name, headers)
                elif method == "PUT":
                    response = self.handle_put(file_name, headers, body)
                elif method == "DELETE":
                    response = self.delete_file(file_name)
                else:
                    response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"

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
                client_socket.close()
            except:
                pass
    
    def get_content_type(self, file_path):
        extension = file_path.split('.')[-1].lower()
        content_types = {
            'txt': 'text/plain',
            'html': 'text/html',
            'css': 'text/css',
            'md': 'text/markdown',
            'json': 'application/json',
            'pdf': 'application/pdf',
            'xml': 'application/xml',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'webp': 'image/webp',
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo'
        }
        return content_types.get(extension, 'application/octet-stream')

    def serve_static(self, file_path, headers=None):
        try:
            # Bloquear acceso a carpeta "private"
            if self.is_private(file_path):
                return "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n".encode()
            full_path = os.path.join(self.server_dir, os.path.normpath(file_path))
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n".encode()
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
            if self.is_private(file_path):
                return "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n"
            full_path = os.path.join(self.server_dir, os.path.normpath(file_path))
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
            if self.is_private(file_path):
                return "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n".encode()
            
            full_path = os.path.join(self.server_dir, os.path.basename(file_path))
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.server_dir)):
                return "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n".encode()

            # Determinar si es contenido binario
            content_type = headers.get('Content-Type', '').lower()
            ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
            is_binary = (
                any(t in content_type for t in ['image/', 'audio/', 'video/', 'application/octet-stream']) or
                ext in ['png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'mp4', 'avi']
            )

            # Escribir el archivo
            mode = 'wb' if is_binary else 'w'
            encoding = None if is_binary else 'utf-8'
            
            with open(full_path, mode) as f:
                if isinstance(content, bytes) or is_binary:
                    f.write(content)
                else:
                    f.write(content.decode('utf-8'))

            was_existing = os.path.exists(full_path)
            status = "200 OK" if was_existing else "201 Created"
            
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
        """
        Manejador para el endpoint /resource (sin s) que opera con recursos en memoria.
        """
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
        json_data = json.dumps(data, indent=4, ensure_ascii=False)
        json_bytes = json_data.encode('utf-8')
        response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n"
        response += f"Content-Length: {len(json_bytes)}\r\n\r\n"
        return response.encode() + json_bytes

    def handle_resources(self, method, path, body, headers):
        """
        Manejador para el endpoint /resources.
        Se espera que la ruta siga la estructura:
        - /resources                             -> para GET se devuelve todo el contenido (todos los recursos)
        - /resources/{categoria}                 -> para GET se devuelve la lista completa de la categoría
        - /resources/{categoria}/{id}            -> para GET se devuelve el objeto cuyo "id" coincida
        - POST a /resources/{categoria}           -> se añade un nuevo objeto (se asigna un id nuevo)
        - PUT a /resources/{categoria}            -> reemplaza la lista completa para esa categoría (se espera array JSON)
        - PUT a /resources/{categoria}/{id}       -> actualiza el objeto que coincide con el id
        - DELETE a /resources/{categoria}/{id}    -> elimina el objeto que coincide con el id
        Los datos se gestionan en el archivo: Server/private/resources.json.
        """
        # Ruta del archivo de recursos
        res_file = os.path.join(self.server_dir, "private", "resources.json")
        # Cargar contenido existente (o vacío si no existe)
        if os.path.exists(res_file):
            try:
                with open(res_file, "r") as f:
                    resources_data = json.load(f)
            except Exception as e:
                print("Error leyendo resources.json:", e)
                resources_data = {}
        else:
            resources_data = {}

        segments = path.strip("/").split("/")
        # Si la ruta es exactamente "/resources"
        if len(segments) == 1:
            if method == "GET":
                json_data = json.dumps(resources_data, indent=4)  # Formato bonito
                return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(json_data)}\r\n\r\n{json_data}"
            else:
                return "HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n"

        # A partir de aquí, se espera que segments[1] sea la categoría (ej. "gatos")
        category = segments[1]
        # Si la categoría no existe y se trata de un POST se crea; para otros métodos se retorna 404.
        if category not in resources_data:
            if method == "POST":
                resources_data[category] = []
            else:
                return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
        category_data = resources_data.get(category, [])
        
        # Si la ruta es /resources/{categoria} (sin id)
        if len(segments) == 2:
            if method == "GET":
                json_data = json.dumps(category_data, indent=4, ensure_ascii=False)
                json_bytes = json_data.encode('utf-8')
                return (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: application/json; charset=utf-8\r\n"
                    + f"Content-Length: {len(json_bytes)}\r\n\r\n".encode()
                    + json_bytes
                )

            elif method == "POST":
                try:
                    new_obj = json.loads(body)
                    # Calcular nuevo ID
                    new_id = 1
                    if category_data:
                        new_id = max([obj.get("id", 0) for obj in category_data] or [0]) + 1
                    
                    # Crear nuevo objeto con ID al principio
                    ordered_obj = {"id": new_id}
                    ordered_obj.update(new_obj)  # Añadir el resto de campos después del ID
                    
                    category_data.append(ordered_obj)
                    resources_data[category] = category_data
                    self.write_resources_file(res_file, resources_data)
                    return "HTTP/1.1 201 Created\r\nContent-Length: 0\r\n\r\n"
                except Exception as e:
                    print("Error en POST /resources/{categoria}:", e)
                    return "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"
            elif method == "PUT":
                try:
                    new_data = json.loads(body)
                    if isinstance(new_data, list):
                        # Si es una lista, reemplaza toda la categoría
                        resources_data[category] = new_data
                    else:
                        # Si es un objeto individual, lo tratamos como POST
                        new_id = 1
                        if category_data:
                            new_id = max([obj.get("id", 0) for obj in category_data] or [0]) + 1
                        
                        # Crear nuevo objeto con ID al principio
                        ordered_obj = {"id": new_id}
                        ordered_obj.update(new_data)  # Añadir el resto de campos después del ID
                        
                        category_data.append(ordered_obj)
                        resources_data[category] = category_data
                    
                    self.write_resources_file(res_file, resources_data)
                    return "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
                except Exception as e:
                    print("Error en PUT /resources/{categoria}:", e)
                    return "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"
            else:
                # DELETE no es válido sin un id
                return "HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n"
        
        # Si se proporciona un id: /resources/{categoria}/{id}
        elif len(segments) == 3:
            resource_id = segments[2]
            if method == "GET":
                found = None
                for obj in category_data:
                    if str(obj.get("id")) == resource_id:
                        found = obj
                        break
                if found is None:
                    return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
                json_data = json.dumps(found, indent=4)
                return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(json_data)}\r\n\r\n{json_data}"
            elif method == "PUT":
                try:
                    # Cargar y validar el nuevo objeto
                    new_obj = json.loads(body)
                    
                    # Buscar el objeto con el ID especificado
                    updated = False
                    for i, obj in enumerate(category_data):
                        if str(obj.get("id")) == resource_id:
                            # Mantener el ID original y actualizar el resto de campos
                            ordered_obj = {"id": obj["id"]}
                            ordered_obj.update(new_obj)  # Añadir el resto de campos después del ID
                            
                            category_data[i] = ordered_obj
                            updated = True
                            break
                    
                    if not updated:
                        return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
                    
                    # Guardar los cambios
                    resources_data[category] = category_data
                    self.write_resources_file(res_file, resources_data)
                    return "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
                    
                except Exception as e:
                    print("Error en PUT /resources/{categoria}/{id}:", e)
                    return "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"
            elif method == "DELETE":
                initial_length = len(category_data)
                category_data = [obj for obj in category_data if str(obj.get("id")) != resource_id]
                if len(category_data) == initial_length:
                    return "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
                resources_data[category] = category_data
                self.write_resources_file(res_file, resources_data)
                return "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
            else:
                return "HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n"
        else:
            return "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"


    def write_resources_file(self, file_path, data):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Error escribiendo el archivo de recursos:", e)

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
