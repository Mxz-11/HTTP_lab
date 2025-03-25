# -*- coding: utf-8 -*-
"""
Authors:
    - Author Mxz11
    - Añadir vuestros nombres aquí!

Description:
    This script is used for handling the client of the HTTP client-server system.

How to compile:
    1. Make sure you have Python installed (version Python 3.12.4 or higher).
    2. Open a terminal or command prompt.
    3. Navigate to the directory where this script is located.
    4. Run the script with the following command:
        python3 client.py
    
    Note: If you're using a virtual environment, activate it before running the script.

Creation Date:
    19/3/2025

Last Modified:
    19/3/2025

"""

import socket
import sys
from datetime import datetime
import os

CLIENT_DIR = 'Client'

# Add this class to store GET request information
class GetRequestInfo:
    def __init__(self, filename, content, timestamp):
        self.filename = filename
        self.content = content
        self.timestamp = timestamp
    
    def __str__(self):
        return f"File: {self.filename}\nTimestamp: {self.timestamp}\nContent:\n{self.content}\n"

class Cache:
    def __init__(self, filename, content, timestamp):
        self.filename = filename
        self.content = content
        self.timestamp = timestamp
    
    def __str__(self):
        return f"File: {self.filename}\nTimestamp: {self.timestamp}\nContent:\n{self.content}\n"

def find_in_cache(cache_list, filename):
    for cache_entry in cache_list:
        if cache_entry.filename == filename:
            return cache_entry
    return None

def create_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return client_socket

def connect_to_server(client_socket, host='localhost', port=8080):
    try:
        client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")
    except ConnectionRefusedError:
        print("Connection failed - server might be offline")
        sys.exit(1)

def handle_audio_response(response):
    """Handle binary audio data from response"""
    try:
        # Split headers and content
        header_end = response.find(b'\r\n\r\n')
        if header_end == -1:
            return None
        
        headers = response[:header_end].decode('utf-8')
        content = response[header_end + 4:]  # Skip \r\n\r\n
        
        # Check if response is OK
        if '200 OK' not in headers:
            print(f"Error in response: {headers}")
            return None
            
        return content
    except Exception as e:
        print(f"Error handling audio response: {e}")
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

def send_request(client_socket, message, is_binary=False):
    try:
        client_socket.send(message.encode('utf-8'))
        
        if not is_binary:
            # Lectura habitual de texto
            response = client_socket.recv(4096).decode('utf-8')
            return response

        # Cuando is_binary == True
        response = b""
        content_length = None
        header_end = None

        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response += chunk

            # Si todavía no parseamos cabeceras, búscalas
            if header_end is None:
                header_end = response.find(b"\r\n\r\n")
                if header_end != -1:
                    # Separamos las cabeceras
                    header_data = response[:header_end].decode('utf-8', errors='replace')
                    lines = header_data.split("\r\n")
                    # Buscamos Content-Length en todas las líneas
                    for line in lines:
                        if line.lower().startswith("content-length:"):
                            parts = line.split(":", 1)
                            content_length = int(parts[1].strip())
                            break

            # Si ya conocemos content_length, verificamos si ya recibimos todos los bytes del cuerpo
            if header_end is not None and content_length is not None:
                body_len = len(response) - (header_end + 4)  # 4 = len("\r\n\r\n")
                if body_len >= content_length:
                    break
        
        return response
    except Exception as e:
        print(f"Error sending/receiving data: {e}")
        return None

def send_head_request(client_socket, path):
    """Send HEAD request to check last modification date"""
    try:
        head_request = f"HEAD {path} HTTP/1.1\r\n"
        head_request += "Host: localhost\r\n\r\n"
        client_socket.send(head_request.encode('utf-8'))
        response = client_socket.recv(4096).decode('utf-8')
        return response
    except Exception as e:
        print(f"Error checking modification date: {e}")
        return None

def check_modification_time(filename, cached_entry, cache_list):
    try:
        client = create_client()
        connect_to_server(client)
        
        # Enviamos el GET con If-Modified-Since
        request = f"GET /{filename} HTTP/1.1\r\n"
        request += "Host: localhost\r\n"
        request += f"If-Modified-Since: {cached_entry.timestamp}\r\n"
        request += "\r\n"
        
        response = send_request(client, request)
        client.close()
        
        if response:
            # Separamos cabeceras y cuerpo
            header_part, _, body_part = response.partition('\r\n\r\n')
            
            status_line = header_part.split('\r\n')[0]
            # Ej: "HTTP/1.1 304 Not Modified"
            
            if '304 Not Modified' in status_line:
                # El archivo NO ha cambiado => seguimos usando la cache
                print("File not modified - Using cached version")
                print(cached_entry.content)
                return False  # No hay cambios
            elif '200 OK' in status_line:
                # Servidor envía el archivo nuevo dentro de la misma respuesta
                new_content = body_part
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Actualizamos la cache
                new_cache = Cache(filename, new_content, timestamp)
                cache_list.append(new_cache)
                
                print("File modified - Updated cache with new content:")
                print(new_content)
                return True
            else:
                # Si llega un 404 o un 500, etc., no lo encontramos
                print("Unexpected response:")
                print(response)
                return True
        else:
            print("No response from server")
            return True
    except Exception as e:
        print(f"Error checking modification time: {e}")
        return True


def main():
    client = create_client()
    connect_to_server(client)
    cache_list = []
    get_history = []
    
    while True:
        try:
            method = input("Enter HTTP method (GET/POST/PUT/DELETE) or 'exit' to quit: ").upper()
            
            if method == 'EXIT':
                if get_history:
                    # Save history to Client directory
                    history_path = os.path.join(CLIENT_DIR, 'history.txt')
                    with open(history_path, 'w') as f:
                        for req in get_history:
                            f.write("-" * 50 + "\n")
                            f.write(str(req) + "\n")
                    print(f"\nGET Request History saved to {history_path}")
                break
            
            if method == 'GET':
                # 1) Preguntamos por el filename
                filename = input("Enter filename with extension: ")
                path = f"/{filename}"
                
                # 2) Detectamos la extensión para decidir el Accept: (tú puedes ajustar)
                ext = filename.split('.')[-1].lower()
                if ext in ['png','jpg','jpeg','gif','svg','webp']:
                    accept_header = "image/*"
                    is_binary = True
                elif ext in ['mp3','wav','ogg','mp4']:
                    accept_header = "audio/*"
                    is_binary = True
                else:
                    # Por defecto lo tratamos como texto u otro
                    # (puedes refinar más si quieres application/pdf, etc.)
                    accept_header = "text/*"
                    is_binary = False

                # 3) Revisamos si está en la caché
                cached_entry = find_in_cache(cache_list, filename)
                if cached_entry:
                    print("Found in cache! Checking if modified...")
                    # Llamamos a check_modification_time, que hace GET If-Modified-Since
                    if not check_modification_time(filename, cached_entry, cache_list):
                        # => 304 Not Modified => el servidor indica que no hay cambios
                        print("Using cached version.")
                        # Si quieres reescribir la versión en disco (opcional):
                        save_mode = 'wb' if is_binary else 'w'
                        with open(os.path.join(CLIENT_DIR, filename), save_mode) as f:
                            f.write(cached_entry.content)
                        # No descargamos nada más, saltamos a pedir el siguiente método
                        continue
                    # Si llega aquí, es que el archivo cambió => seguimos y hacemos un GET normal

                # 4) Hacemos un GET normal (sin If-Modified-Since)
                new_socket = create_client()
                connect_to_server(new_socket)

                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: localhost\r\n"
                    f"Accept: {accept_header}\r\n"
                    "\r\n"
                )

                response = send_request(new_socket, request, is_binary=is_binary)
                new_socket.close()

                if response:
                    # 5) Si es binario, usamos handle_binary_response; si no, lo separamos como texto
                    if is_binary:
                        content = handle_binary_file(response)
                        if content:
                            # Guardamos .mp4, .avi, .png, .jpg... etc. 
                            save_path = os.path.join(CLIENT_DIR, filename)
                            with open(save_path, 'wb') as f:
                                f.write(content)
                            
                            # Guardamos en cache
                            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            new_cache = Cache(filename, content, timestamp_str)
                            if cached_entry:
                                cache_list.remove(cached_entry)
                            cache_list.append(new_cache)
                            
                            print(f"Binary file saved as {save_path} and cached.")
                        else:
                            print("Failed to process binary response.")
                    
                    else:
                        # Texto u otro
                        header_part, _, body_part = response.partition('\r\n\r\n')
                        status_line = header_part.split('\r\n')[0]
                        if '200 OK' in status_line:
                            save_path = os.path.join(CLIENT_DIR, filename)
                            with open(save_path, 'w') as f:
                                f.write(body_part)
                            
                            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            new_cache = Cache(filename, body_part, timestamp_str)
                            if cached_entry:
                                cache_list.remove(cached_entry)
                            cache_list.append(new_cache)
                            
                            print(f"Text file saved as {save_path} and cached.")
                        else:
                            print("Server returned:", status_line)
                continue

            
            if method == 'PUT':
                # Get file information
                filename = input("Enter filename to upload: ")
                path = f"/{filename}"
                
                try:
                    # Read file content
                    with open(filename, 'r') as f:
                        content = f.read()
                    
                    # Create PUT request
                    request = f"PUT {path} HTTP/1.1\r\n"
                    request += "Host: localhost\r\n"
                    request += "Content-Type: text/plain\r\n"
                    request += f"Content-Length: {len(content)}\r\n"
                    request += "\r\n"
                    request += content
                    
                    # Send request
                    client = create_client()
                    connect_to_server(client)
                    response = send_request(client, request)
                    
                    if response:
                        print(f"\nServer response:\n{response}")
                    
                    client.close()
                    
                except FileNotFoundError:
                    print(f"Error: File '{filename}' not found")
                except Exception as e:
                    print(f"Error uploading file: {e}")
                continue
            
            path = input("Enter path (e.g., /resource/1): ")
            
            data = ""
            if method in ['POST', 'PUT']:
                data = input("Enter JSON data (e.g., {\"name\": \"value\"}): ")
            else:
                data = ""

            # Construimos la request
            request = f"{method} {path} HTTP/1.1\r\n"
            request += "Host: localhost\r\n"

            if data:
                request += "Content-Type: application/json\r\n"
                request += f"Content-Length: {len(data)}\r\n"
                request += "\r\n"
                request += data
            else:
                request += "\r\n"

            # Mandamos la request usando un socket nuevo
            client = create_client()
            connect_to_server(client)

            response = send_request(client, request, is_binary=False)
            if response:
                print(f"\nServer response:\n{response}\n")

            client.close()
            
        except Exception as e:
            print(f"Error: {e}")
            client = create_client()
            connect_to_server(client)

    client.close()

if __name__ == "__main__":
    main()