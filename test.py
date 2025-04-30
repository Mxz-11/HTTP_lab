import os
import socket
tempfile = None
import json
import pytest
from nServer import SimpleHTTPServer

# pytest test.py


def make_server(tmp_path):
    # Instantiate server and point its directory to a temp folder
    server = SimpleHTTPServer(host='localhost', port=0)
    server.server_dir = str(tmp_path / "Server")
    # Create structure including private subfolder
    os.makedirs(os.path.join(server.server_dir, "private"), exist_ok=True)
    return server


def send_request(server, request_bytes):
    # Use socketpair to simulate client-server connection
    client_sock, server_sock = socket.socketpair()
    try:
        # Write request into server end
        client_sock.sendall(request_bytes)
        # Process single request
        server.handle_request(server_sock)
        # Read all response bytes
        response = b""
        while True:
            chunk = client_sock.recv(4096)
            if not chunk:
                break
            response += chunk
        return response
    finally:
        client_sock.close()
        server_sock.close()

def extract_body(resp_bytes):
    # Split headers and body
    parts = resp_bytes.split(b"\r\n\r\n", 1)
    return parts[1] if len(parts) > 1 else b""

def test_get_nonexistent_file(tmp_path):
    server = make_server(tmp_path)
    req = b"GET /noexist.txt HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp = send_request(server, req)
    assert b"404 Not Found" in resp

def test_head_method(tmp_path):
    server = make_server(tmp_path)
    # Create a file
    file_path = os.path.join(server.server_dir, "page.html")
    with open(file_path, "w", encoding='utf-8') as f:
        f.write("<h1>Title</h1>")

    # HEAD request
    req = b"HEAD /page.html HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp = send_request(server, req)
    body = extract_body(resp)
    assert b"200 OK" in resp
    assert b"<h1>Title</h1>" not in body  # No body for HEAD


def test_unsupported_method(tmp_path):
    server = make_server(tmp_path)
    req = b"PATCH / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp = send_request(server, req)
    assert b"405 Method Not Allowed" in resp

def test_directory_traversal(tmp_path):
    server = make_server(tmp_path)
    # Create sensitive file outside
    parent = tmp_path / "Secret"
    parent.mkdir()
    secret_file = parent / "hidden.txt"
    secret_file.write_text("oops")

    # Attempt traversal
    req = b"GET /../Secret/hidden.txt HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp = send_request(server, req)
    # Should not allow traversal
    assert b"403 Forbidden" in resp or b"404 Not Found" in resp


def test_put_and_update_file(tmp_path):
    server = make_server(tmp_path)
    body1 = b"First"
    headers1 = (
        b"PUT /update.txt HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Content-Type: application/octet-stream\r\n"
        b"Content-Length: 5\r\n\r\n"
    )
    resp1 = send_request(server, headers1 + body1)
    assert b"200 OK" in resp1

    # Update same file
    body2 = b"Second"
    headers2 = (
        b"PUT /update.txt HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Content-Type: application/octet-stream\r\n"
        b"Content-Length: 6\r\n\r\n"
    )
    resp2 = send_request(server, headers2 + body2)
    assert b"200 OK" in resp2
    # Check content
    resp_get = send_request(server, b"GET /update.txt HTTP/1.1\r\nHost: localhost\r\n\r\n")
    assert b"Second" in resp_get

def test_delete_nonexistent(tmp_path):
    server = make_server(tmp_path)
    req = b"DELETE /nofile HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp = send_request(server, req)
    assert b"404 Not Found" in resp

def test_put_in_private_forbidden(tmp_path):
    server = make_server(tmp_path)
    body = b"Secret"
    headers = (
        b"PUT /private/secret2.txt HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Content-Type: application/octet-stream\r\n"
        b"Content-Length: 6\r\n\r\n"
    )
    resp = send_request(server, headers + body)
    assert b"403 Forbidden" in resp

def test_resources_multiple_posts(tmp_path):
    server = make_server(tmp_path)
    # Post two items
    for name in [b'{"name":"A"}', b'{"name":"B"}']:
        hdr = (
            b"POST /resources/list HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: " + str(len(name)).encode() + b"\r\n\r\n"
        )
        resp_post = send_request(server, hdr + name)
        assert b"201 Created" in resp_post

    # GET list and verify two ids
    resp_list = send_request(server, b"GET /resources/list HTTP/1.1\r\nHost: localhost\r\n\r\n")
    body = extract_body(resp_list)
    arr = json.loads(body.decode())
    ids = [item.get('id') for item in arr]
    assert ids == [1, 2]
    

def test_resources_invalid_json(tmp_path):
    server = make_server(tmp_path)
    bad = b"{name:NoQuotes}"
    headers = (
        b"POST /resources/test HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: " + str(len(bad)).encode() + b"\r\n\r\n"
    )
    resp = send_request(server, headers + bad)
    assert b"400 Bad Request" in resp

def test_get_static_file(tmp_path):
    server = make_server(tmp_path)
    # Create a text file under Server directory
    file_path = os.path.join(server.server_dir, "hello.txt")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write("Hello, Test!")

    req = b"GET /hello.txt HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp = send_request(server, req)
    assert b"200 OK" in resp
    assert b"Hello, Test!" in resp


def test_403_on_private(tmp_path):
    server = make_server(tmp_path)
    # Create a private file
    priv = os.path.join(server.server_dir, "private", "secret.txt")
    with open(priv, "w") as f:
        f.write("Top Secret")

    req = b"GET /private/secret.txt HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp = send_request(server, req)
    assert b"403 Forbidden" in resp


def test_put_then_get_and_delete(tmp_path):
    server = make_server(tmp_path)
    # PUT to create new file
    body = b"Data123"
    headers = (
        b"PUT /data.txt HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Content-Type: application/octet-stream\r\n"
        b"Content-Length: 7\r\n\r\n"
    )
    req_put = headers + body
    resp_put = send_request(server, req_put)
    assert b"200 OK" in resp_put

    # GET the created file
    req_get = b"GET /data.txt HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp_get = send_request(server, req_get)
    assert b"200 OK" in resp_get
    assert b"Data123" in resp_get

    # DELETE the file
    req_del = b"DELETE /data.txt HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp_del = send_request(server, req_del)
    assert b"200 OK" in resp_del

    # GET after delete -> 404
    resp_404 = send_request(server, req_get)
    assert b"404 Not Found" in resp_404


def test_resources_crud(tmp_path):
    server = make_server(tmp_path)
    # POST a new resource in category 'items'
    new_obj = b'{"name":"ItemA"}'
    headers = (
        b"POST /resources/items HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: " + str(len(new_obj)).encode() + b"\r\n\r\n"
    )
    req_post = headers + new_obj
    resp_post = send_request(server, req_post)
    assert b"201 Created" in resp_post

    # GET the category list
    req_get_list = b"GET /resources/items HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp_list = send_request(server, req_get_list)
    assert b"\"name\": \"ItemA\"" in resp_list

    # GET single object by id=1
    req_get_one = b"GET /resources/items/1 HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp_one = send_request(server, req_get_one)
    assert b"ItemA" in resp_one

    # DELETE the object
    req_del = b"DELETE /resources/items/1 HTTP/1.1\r\nHost: localhost\r\n\r\n"
    resp_del = send_request(server, req_del)
    assert b"200 OK" in resp_del

    # GET list again -> empty array
    resp_empty = send_request(server, req_get_list)
    assert b"[]" in resp_empty
