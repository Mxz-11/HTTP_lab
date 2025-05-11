# -*- coding: utf-8 -*-
"""
Authors:
    - Author Mxz11
    - Jorge Giménez
    - Alex Langarita
    - Arkaitz Subías

Description:
    Este script gestiona el servidor del sistema cliente-servidor HTTP.

How to execute:
    1. Asegúrate de tener Python instalado (versión 3.12.4 o superior).
    2. Abre una terminal o línea de comandos.
    3. Navega hasta el directorio donde se encuentre este script.
    4. Ejecuta el script con:
           python3 nServer.py
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
        self.server_dir = 'Server'
        os.makedirs(self.server_dir, exist_ok=True)

    def is_private(self, file_path):
        normalized_path = os.path.normpath(file_path)
        return normalized_path == "private" or normalized_path.startswith("private" + os.sep)

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_socket.bind((self.host, self.port))
        except Exception as e:
            print(f"Error al enlazar el servidor en {self.host}:{self.port} -> {e}")
            return
        server_socket.listen(5)
        print(f"HTTP Server listening on {self.host}:{self.port}")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"Conexión entrante de {addr}")
            threading.Thread(target=self.handle_request, args=(client_socket,)).start()

    def log_full_request(self, addr, headers_raw, body, content_type):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        ip, port = addr
        log_path = os.path.join(self.server_dir, "private","server.log")

        request_lines = [line.strip() for line in headers_raw.strip().splitlines() if line.strip()]
        request_line = request_lines[0] if request_lines else "<empty request>"

        headers_clean = "\n".join(request_lines[1:])
        body_display = body

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {ip}:{port} - Request received:\n")
            f.write(f"{request_line}\n")
            f.write(headers_clean + "\n")
            f.write("-" * 60 + "\n")
            try:
                json_obj = json.loads(body_display)
                formatted = json.dumps(json_obj, indent=4, ensure_ascii=False)
                f.write(formatted + "\n")
            except Exception:
                f.write(body_display + "\n")
            f.write("=" * 60 + "\n")

    def is_path_traversal(self, file_path):
        full_path = os.path.abspath(os.path.join(self.server_dir, os.path.normpath(file_path)))
        return not full_path.startswith(os.path.abspath(self.server_dir))

    def handle_request(self, client_socket):
        try:
            request_data = b''
            while b'\r\n\r\n' not in request_data:
                chunk = client_socket.recv(4096)
                if not chunk:
                    return
                request_data += chunk

            header_end = request_data.find(b'\r\n\r\n')
            headers_raw = request_data[:header_end].decode('utf-8', errors='ignore')

            request_lines = headers_raw.split('\r\n')
            request_line = request_lines[0]
            method, path, _ = request_line.split()

            headers = {}
            for line in request_lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()

            body = b''
            if 'Content-Length' in headers:
                content_length = int(headers['Content-Length'])
                body = request_data[header_end + 4:]

                while len(body) < content_length:
                    chunk = client_socket.recv(min(4096, content_length - len(body)))
                    if not chunk:
                        break
                    body += chunk

            bina_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.mp3', '.wav', '.mp4', '.avi')
            bina = method in ("POST", "PUT") and path.lower().endswith(bina_extensions)

            if method in ("POST", "PUT") and not bina:
                try:
                    body_str = body.decode('utf-8', errors='replace')
                except:
                    body_str = "[error decoding body]"
            else:
                body_str = ""

            self.log_full_request(
                client_socket.getpeername(),
                headers_raw,
                body_str,
                headers.get("Content-Type", "")
            )

            print(f"Method: {method}, Path: {path}")

            response = ""
            if path.startswith("/resources"):
                response = self.handle_resources(method, path, body, headers)
            else:
                file_name = path[1:] if path.startswith('/') else path
                if self.is_private(file_name):
                    if method == "HEAD" and file_name.startswith("/resources"):
                        response = "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
                    else:
                        response = "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n"
                elif method == "GET":
                    response = self.serve_static(file_name, headers)
                elif method in ("PUT", "POST"):
                    response = self.handle_put(file_name, headers, body)
                elif method == "DELETE":
                    response = self.delete_file(file_name)
                elif method == "HEAD":
                    response = self.serve_static(file_name, headers)
                    if isinstance(response, bytes):
                        response = response.split(b'\r\n\r\n')[0] + b'\r\n\r\n'
                    else:
                        response = response.split('\r\n\r\n')[0] + '\r\n\r\n'
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
            if self.is_private(file_path) or self.is_path_traversal(file_path):
                return self.build_response("403 Forbidden")
            full_path = os.path.join(self.server_dir, os.path.normpath(file_path))
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return self.build_response("404 Not Found")
            if headers and 'If-Modified-Since' in headers:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
                try:
                    client_time = datetime.strptime(headers['If-Modified-Since'], '%Y-%m-%d %H:%M:%S')
                    if file_mtime <= client_time:
                        return self.build_response("304 Not Modified", content="", content_length=0)
                except ValueError as e:
                    print(f"Error al parsear la fecha If-Modified-Since: {e}")
            content_type = self.get_content_type(full_path)
            with open(full_path, 'rb') as file:
                content = file.read()
            return self.build_response(
                "200 OK",
                content,
                content_type=content_type
            )
        except Exception as e:
            print(f"Error serving file: {e}")
            return self.build_response("500 Internal Server Error")

    def delete_file(self, file_path):
        try:
            if self.is_private(file_path):
                return self.build_response("403 Forbidden")
            full_path = os.path.join(self.server_dir, os.path.normpath(file_path))
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.server_dir)):
                print(f"Intento de traversal de directorios: {file_path}")
                return self.build_response("403 Forbidden")
            if os.path.exists(full_path):
                os.remove(full_path)
                message = f"File {file_path} was successfully deleted"
                return self.build_response("200 OK", message, content_type="text/plain")
            else:
                print(f"Archivo no encontrado: {full_path}")
                return self.build_response("404 Not Found", "", content_type="text/plain")
        except Exception as e:
            print(f"Error deleting file: {e}")
            return self.build_response("500 Internal Server Error")

    def handle_put(self, file_path, headers, content):
        try:
            if self.is_private(file_path):
                return self.build_response("403 Forbidden")
            full_path = os.path.join(self.server_dir, os.path.basename(file_path))
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.server_dir)):
                return self.build_response("403 Forbidden")

            content_type = headers.get('Content-Type', '').lower()
            ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
            is_binary = (
                any(t in content_type for t in ['image/', 'audio/', 'video/', 'application/octet-stream']) or
                ext in ['png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'mp4', 'avi']
            )

            mode = 'wb' if is_binary or isinstance(content, bytes) else 'w'
            encoding = None if is_binary or isinstance(content, bytes) else 'utf-8'

            with open(full_path, mode, encoding=encoding) as f:
                if isinstance(content, bytes) or is_binary:
                    f.write(content)
                else:
                    f.write(content.decode('utf-8'))

            was_existing = os.path.exists(full_path)
            status = "200 OK" if was_existing else "201 Created"
            message = f"File {file_path} was successfully {'updated' if was_existing else 'created'}"
            return self.build_response(status, message, content_type="text/plain")
        except Exception as e:
            print(f"Error handling PUT request: {e}")
            return self.build_response("500 Internal Server Error")

    def respond_json(self, data, head_only=False):
        json_data = json.dumps(data, indent=4, ensure_ascii=False)
        json_bytes = json_data.encode("utf-8")
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(json_bytes)}\r\n"
            "Connection: close\r\n\r\n"
        )
        return headers.encode() if head_only else headers.encode() + json_bytes

    def build_response(self, status_code, content="", content_type="text/plain", content_length=None):
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        actual_length = content_length if content_length is not None else len(content_bytes)

        headers = f"HTTP/1.1 {status_code}\r\n"
        headers += f"Content-Type: {content_type}\r\n"
        headers += f"Content-Length: {actual_length}\r\n"
        headers += "Connection: close\r\n\r\n"

        return headers.encode() + content_bytes

    def read_json_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def write_json_file(self, path, data):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Error writing JSON:", e)

    def handle_resources(self, method, path, body, headers):
        res_file = os.path.join(self.server_dir, "private", "resources.json")
        resources_data = self.read_json_file(res_file)

        segments = [s for s in path.strip("/").split("/") if s]
        if len(segments) == 1:
            if method == "GET":
                return self.respond_json(resources_data)
            elif method == "HEAD":
                return self.respond_json(resources_data, head_only=True)
            else:
                return self.build_response("405 Method Not Allowed")

        category = segments[1]
        if category not in resources_data:
            if method == "POST":
                resources_data[category] = []
            else:
                return self.build_response("404 Not Found")
        category_data = resources_data.get(category, [])

        if len(segments) == 2:
            if method == "GET":
                return self.respond_json(category_data)
            elif method == "HEAD":
                return self.respond_json(category_data, head_only=True)
            elif method == "POST":
                try:
                    new_obj = json.loads(body)
                    new_id = 1
                    if category_data:
                        new_id = max([obj.get("id", 0) for obj in category_data] or [0]) + 1

                    ordered_obj = {"id": new_id}
                    ordered_obj.update(new_obj)

                    category_data.append(ordered_obj)
                    resources_data[category] = category_data
                    self.write_json_file(res_file, resources_data)
                    return self.build_response("201 Created")
                except Exception as e:
                    print("Error en POST /resources/{categoria}:", e)
                    return self.build_response("400 Bad Request")
            elif method == "PUT":
                try:
                    new_data = json.loads(body)
                    if isinstance(new_data, list):
                        resources_data[category] = new_data
                    else:
                        new_id = 1
                        if category_data:
                            new_id = max([obj.get("id", 0) for obj in category_data] or [0]) + 1

                        ordered_obj = {"id": new_id}
                        ordered_obj.update(new_data)

                        category_data.append(ordered_obj)
                        resources_data[category] = category_data

                    self.write_json_file(res_file, resources_data)
                    return self.build_response("200 OK")
                except Exception as e:
                    print("Error en PUT /resources/{categoria}:", e)
                    return self.build_response("400 Bad Request")
            else:
                return self.build_response("405 Method Not Allowed")

        elif len(segments) == 3:
            resource_id = segments[2]
            if method == "HEAD":
                found = next((obj for obj in category_data if str(obj.get("id")) == resource_id), None)
                if found:
                    return self.respond_json(found, head_only=True)
                else:
                    return self.build_response("404 Not Found")
            elif method == "GET":
                found = next((obj for obj in category_data if str(obj.get("id")) == resource_id), None)
                if found is None:
                    return self.build_response("404 Not Found")
                return self.respond_json(found)
            elif method == "PUT":
                try:
                    new_obj = json.loads(body)
                    updated = False
                    for i, obj in enumerate(category_data):
                        if str(obj.get("id")) == resource_id:
                            ordered_obj = {"id": obj["id"]}
                            ordered_obj.update(new_obj)
                            category_data[i] = ordered_obj
                            updated = True
                            break

                    if not updated:
                        return self.build_response("404 Not Found")

                    resources_data[category] = category_data
                    self.write_json_file(res_file, resources_data)
                    return self.build_response("200 OK")

                except Exception as e:
                    print("Error en PUT /resources/{categoria}/{id}:", e)
                    return self.build_response("400 Bad Request")
            elif method == "DELETE":
                initial_length = len(category_data)
                category_data = [obj for obj in category_data if str(obj.get("id")) != resource_id]
                if len(category_data) == initial_length:
                    return self.build_response("404 Not Found")
                resources_data[category] = category_data
                self.write_json_file(res_file, resources_data)
                return self.build_response("200 OK")
            else:
                return self.build_response("405 Method Not Allowed")
        else:
            return self.build_response("400 Bad Request")

if __name__ == "__main__":
    try:
        port_input = input("Put the port to start the server (default 8080): ").strip()
        if port_input == "":
            port = 8080
        else:
            try:
                port = int(port_input)
            except ValueError:
                print("Not valid port, port 8080 will be used")
                port = 8080
    except KeyboardInterrupt:
        print("\nExecution canceled by the user.")
        exit()

    server = SimpleHTTPServer(port=port)
    server.start()