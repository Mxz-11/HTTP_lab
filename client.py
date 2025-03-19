import socket
import sys

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

def send_request(client_socket, message):
    try:
        client_socket.send(message.encode('utf-8'))
        response = client_socket.recv(4096).decode('utf-8')  # Increased buffer size
        return response
    except Exception as e:
        print(f"Error sending/receiving data: {e}")
        return None

def main():
    client = create_client()
    connect_to_server(client)
    
    while True:
        try:
            # Get user input for HTTP method
            method = input("Enter HTTP method (GET/POST/PUT/DELETE) or 'exit' to quit: ").upper()
            
            if method == 'EXIT':
                break
                
            if method not in ['GET', 'POST', 'PUT', 'DELETE']:
                print("Invalid HTTP method. Please try again.")
                continue
            
            # Special handling for GET requests
            if method == 'GET':
                file_type = input("Enter request type (html/resource): ").lower()
                if file_type == 'html':
                    filename = input("Enter HTML file name (e.g., index.html): ")
                    path = f"/{filename}"
                else:
                    path = input("Enter resource path (e.g., /resource/1): ")
            else:
                path = input("Enter path (e.g., /resource/1): ")
            
            # Handle data for POST/PUT requests
            data = ""
            if method in ['POST', 'PUT']:
                data = input("Enter JSON data (e.g., {\"name\": \"value\"}): ")
            
            # Construct HTTP request
            request = f"{method} {path} HTTP/1.1\r\n"
            request += "Host: localhost\r\n"
            
            if data:
                request += "Content-Type: application/json\r\n"
                request += f"Content-Length: {len(data)}\r\n"
                request += "\r\n"
                request += data
            else:
                request += "\r\n"
            
            # Create new socket for each request
            client = create_client()
            connect_to_server(client)
            
            # Send request and get response
            response = send_request(client, request)
            if response:
                print(f"\nServer response:\n{response}\n")
            
            # Close the connection after each request
            client.close()
            
        except Exception as e:
            print(f"Error: {e}")
            # Create new connection on error
            client = create_client()
            connect_to_server(client)

    client.close()

if __name__ == "__main__":
    main()