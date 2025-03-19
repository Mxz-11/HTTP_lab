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
    client_socket.send(message.encode())
    response = client_socket.recv(1024).decode()
    return response

def main():
    client = create_client()
    connect_to_server(client)
    
    while True:
        # Get user input for HTTP method
        method = input("Enter HTTP method (GET/POST/PUT/DELETE) or 'exit' to quit: ").upper()
        
        if method == 'EXIT':
            break
            
        if method not in ['GET', 'POST', 'PUT', 'DELETE']:
            print("Invalid HTTP method. Please try again.")
            continue
            
        # Get path and optional data
        path = input("Enter path (e.g., /index.html): ")
        data = ""
        if method in ['POST', 'PUT']:
            data = input("Enter data: ")
            
        # Construct HTTP request
        request = f"{method} {path} HTTP/1.1\r\n"
        request += "Host: localhost\r\n"
        if data:
            request += f"Content-Length: {len(data)}\r\n"
            request += "\r\n"
            request += data
        else:
            request += "\r\n"
            
        # Send request and get response
        response = send_request(client, request)
        print(f"\nServer response:\n{response}\n")

    client.close()

if __name__ == "__main__":
    main()