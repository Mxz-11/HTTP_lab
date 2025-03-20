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
DOWNLOADS_DIR = os.path.join(CLIENT_DIR, 'downloads')
CACHE_DIR = os.path.join(CLIENT_DIR, 'cache')

# Create necessary directories
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

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

def handle_binary_response(response):
    """Handle binary data from response"""
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
            
        # Extract Content-Type from headers
        content_type = None
        for line in headers.split('\r\n'):
            if line.startswith('Content-Type:'):
                content_type = line.split(': ')[1].strip()
                break
        
        if not content_type or not content_type.startswith('image/'):
            print(f"Invalid content type: {content_type}")
            return None
            
        return content
    except Exception as e:
        print(f"Error handling binary response: {e}")
        return None

def send_request(client_socket, message, is_binary=False):
    try:
        client_socket.send(message.encode('utf-8'))
        if is_binary:
            # For binary data, receive in chunks
            response = b''
            while True:
                chunk = client_socket.recv(8192)
                if not chunk:
                    break
                response += chunk
                # Check if we've received the complete response
                if b'\r\n\r\n' in response and len(response) >= int(response.split(b'\r\n')[1].split(b': ')[1]):
                    break
            return response
        else:
            response = client_socket.recv(4096).decode('utf-8')
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
        
        # Send If-Modified-Since request
        request = f"GET /{filename} HTTP/1.1\r\n"
        request += "Host: localhost\r\n"
        request += f"If-Modified-Since: {cached_entry.timestamp}\r\n"
        request += "\r\n"
        
        response = send_request(client, request)
        client.close()
        
        if response:
            # Check if the response contains "1" at the end of the body
            response_parts = response.split('\r\n\r\n')
            if len(response_parts) > 1 and response_parts[1].strip() == '1':
                # Make a new GET request to get current content
                client = create_client()
                connect_to_server(client)
                request = f"GET /{filename} HTTP/1.1\r\n"
                request += "Host: localhost\r\n\r\n"
                
                response = send_request(client, request)
                client.close()
                
                if response and '200 OK' in response:
                    content = response.split('\r\n\r\n')[-1]
                    timestamp = datetime.now()
                    
                    # Update cache
                    new_cache = Cache(filename, content, timestamp)
                    cache_list.remove(cached_entry)
                    cache_list.append(new_cache)
                    
                    print("File modified - Updated cache with new content:")
                    print(new_cache.content)
                    return True
                    
        return False
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
                content_type = input("Enter content type (text/application/image/audio/video): ").lower()
                if content_type not in ['text', 'application', 'image', 'audio', 'video']:
                    print("Invalid content type")
                    continue
                
                filename = input("Enter filename with extension: ")
                path = f"/{filename}"
                
                if content_type == 'image':
                    # Handle image files
                    if not any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
                        print("Invalid image format. Supported formats: png, jpg, jpeg, gif, svg, webp")
                        continue
                    
                    request = f"GET {path} HTTP/1.1\r\n"
                    request += "Host: localhost\r\n"
                    request += "Accept: image/*\r\n\r\n"
                    
                    response = send_request(client, request, is_binary=True)
                    if response:
                        try:
                            content = handle_binary_response(response)
                            if content:
                                # Save in Client/downloads directory
                                save_path = os.path.join(DOWNLOADS_DIR, os.path.basename(filename))
                                with open(save_path, 'wb') as f:
                                    f.write(content)
                                print(f"Image saved successfully as: {save_path}")
                            else:
                                print("Failed to process image response")
                        except Exception as e:
                            print(f"Error saving image: {e}")
                    continue
                
                elif content_type == 'audio':
                    # Handle audio files
                    if not any(filename.endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.mp4']):
                        print("Invalid audio file format. Supported formats: mp3, wav, ogg, mp4")
                        continue
                    
                    request = f"GET {path} HTTP/1.1\r\n"
                    request += "Host: localhost\r\n"
                    request += "Accept: audio/*\r\n\r\n"
                    
                    response = send_request(client, request, is_binary=True)
                    if response:
                        content = handle_audio_response(response)
                        if content:
                            # Save in Client/downloads directory
                            save_path = os.path.join(DOWNLOADS_DIR, f"downloaded_{filename}")
                            with open(save_path, 'wb') as f:
                                f.write(content)
                            print(f"Audio file saved as: {save_path}")
                    continue
                
                elif content_type == 'text':
                    # Handle text files with cache
                    cached_entry = find_in_cache(cache_list, filename)
                    if cached_entry:
                        print("Found in cache! Checking if modified...")
                        if not check_modification_time(filename, cached_entry, cache_list):
                            print("File not modified - Using cached version")
                            print(cached_entry.content)
                            # Save cached content to downloads directory
                            save_path = os.path.join(DOWNLOADS_DIR, filename)
                            with open(save_path, 'w') as f:
                                f.write(cached_entry.content)
                            print(f"File saved from cache as: {save_path}")
                            continue
                        continue
                
                request = f"GET {path} HTTP/1.1\r\n"
                request += "Host: localhost\r\n"
                request += f"Accept: {content_type}/*\r\n\r\n"
                
                client = create_client()
                connect_to_server(client)
                
                response = send_request(client, request)
                if response:
                    if content_type == 'text':
                        response_lines = response.split('\r\n')
                        status_line = response_lines[0]
                        
                        if '200 OK' in status_line:
                            content = response.split('\r\n\r\n')[-1]
                            timestamp = datetime.now()
                            
                            # Save content to downloads directory
                            save_path = os.path.join(DOWNLOADS_DIR, filename)
                            with open(save_path, 'w') as f:
                                f.write(content)
                            print(f"File saved as: {save_path}")
                            
                            new_cache = Cache(filename, content, timestamp)
                            if cached_entry:
                                cache_list.remove(cached_entry)
                            cache_list.append(new_cache)
                            get_history.append(new_cache)
                            print("Content cached and added to history")
                    
                    print(f"\nServer response:\n{response}\n")
                
                client.close()
            
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
            
            if not (method == 'GET' and content_type == 'text' and cached_entry):
                request = f"{method} {path} HTTP/1.1\r\n"
                request += "Host: localhost\r\n"
            
            if data:
                request += "Content-Type: application/json\r\n"
                request += f"Content-Length: {len(data)}\r\n"
                request += "\r\n"
                request += data
            else:
                request += "\r\n"
            
            client = create_client()
            connect_to_server(client)
            
            response = send_request(client, request)
            if response:
                if method == 'GET' and content_type == 'text':
                    response_lines = response.split('\r\n')
                    status_line = response_lines[0]
                    
                    if '200 OK' in status_line:
                        content = response.split('\r\n\r\n')[-1]
                        timestamp = datetime.now()
                        
                        new_cache = Cache(filename, content, timestamp)
                        if cached_entry:
                            cache_list.remove(cached_entry)
                        cache_list.append(new_cache)
                        
                        get_history.append(new_cache)
                        print("Content cached and added to history")
                
                print(f"\nServer response:\n{response}\n")
            
            client.close()
            
        except Exception as e:
            print(f"Error: {e}")
            client = create_client()
            connect_to_server(client)

    client.close()

if __name__ == "__main__":
    main()