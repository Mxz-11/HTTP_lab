import socket
import threading
import json
import os
from datetime import datetime
from http import HTTPStatus
from urllib.parse import unquote, urlparse
from pathlib import Path

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8080
SERVER_DIR = Path('Server')
PRIVATE_DIR = SERVER_DIR / 'private'
BUFFER_SIZE = 4096


class SimpleHTTPServer:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.resources_file = PRIVATE_DIR / 'resources.json'
        self.log_file = PRIVATE_DIR / 'server.log'
        self.resources_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_resources()

    def _load_resources(self):
        if self.resources_file.exists():
            try:
                self.resources = json.loads(self.resources_file.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                self.resources = {}
        else:
            self.resources = {}

    def _write_resources(self):
        self.resources_file.write_text(
            json.dumps(self.resources, indent=4, ensure_ascii=False),
            encoding='utf-8'
        )

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(5)
            print(f"Listening on {self.host}:{self.port}...")
            while True:
                client, addr = srv.accept()
                print(f"Incoming connection from {addr[0]}:{addr[1]}")
                threading.Thread(
                    target=self._handle_client,
                    args=(client, addr),
                    daemon=True
                ).start()

    def _handle_client(self, client, addr):
        try:
            data = self._recv_all(client)
            request_line, headers, body = self._parse_request(data)
            method, raw_path, _ = request_line.split()
            path = unquote(urlparse(raw_path).path)
            self._log_request(addr, request_line, headers, body)

            if path.startswith('/resources'):
                resp = self._route_resources(method, path, body)
            else:
                resp = self._route_file(method, path, headers, body)

            client.sendall(resp)
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
            client.sendall(self._response(HTTPStatus.INTERNAL_SERVER_ERROR))
        finally:
            client.close()

    def _recv_all(self, sock):
        data = bytearray()
        while True:
            chunk = sock.recv(BUFFER_SIZE)
            if not chunk:
                break
            data.extend(chunk)
            if b'\r\n\r\n' in data:
                break
        headers_end = data.find(b"\r\n\r\n") + 4
        headers = data[:headers_end]
        cl = self._get_content_length(headers)
        if cl:
            to_read = cl - (len(data) - headers_end)
            while to_read > 0:
                chunk = sock.recv(min(BUFFER_SIZE, to_read))
                if not chunk:
                    break
                data.extend(chunk)
                to_read -= len(chunk)
        return bytes(data)

    def _parse_request(self, raw):
        header_end = raw.find(b"\r\n\r\n")
        header_bytes = raw[:header_end]
        body = raw[header_end+4:]
        lines = header_bytes.decode('utf-8', errors='ignore').split('\r\n')
        request_line = lines[0]
        headers = {k: v for k, v in (
            ln.split(':', 1) for ln in lines[1:] if ':' in ln
        )}
        return request_line, headers, body

    def _get_content_length(self, header_bytes):
        try:
            text = header_bytes.decode('utf-8', errors='ignore')
            for line in text.split('\r\n'):
                if line.lower().startswith('content-length'):
                    return int(line.split(':', 1)[1].strip())
        except Exception:
            pass
        return 0

    def _log_request(self, addr, request_line, headers, body):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = [f"[{ts}] {addr[0]}:{addr[1]} {request_line}"]
        for k, v in headers.items():
            entry.append(f"{k}: {v}")
        if body:
            try:
                j = json.loads(body.decode('utf-8', errors='ignore'))
                entry.append(json.dumps(j, indent=4, ensure_ascii=False))
            except:
                entry.append(body.decode('utf-8', errors='ignore'))
        with open(self.log_file, 'a', encoding='utf-8') as log:
            log.write('\n'.join(entry) + '\n' + '='*60 + '\n')

    def _route_file(self, method, path, headers, body):
        filepath = (SERVER_DIR / path.lstrip('/')).resolve()
        if not str(filepath).startswith(str(SERVER_DIR.resolve())):
            return self._response(HTTPStatus.FORBIDDEN)
        if method in ('GET', 'HEAD'):
            if not filepath.exists() or not filepath.is_file():
                return self._response(HTTPStatus.NOT_FOUND)
            ims = headers.get('If-Modified-Since')
            if ims:
                mtime = datetime.utcfromtimestamp(filepath.stat().st_mtime)
                try:
                    ims_dt = datetime.strptime(ims, '%a, %d %b %Y %H:%M:%S GMT')
                    if mtime <= ims_dt:
                        return self._response(HTTPStatus.NOT_MODIFIED)
                except:
                    pass
            data = filepath.read_bytes()
            return self._response(
                HTTPStatus.OK, data,
                content_type=self._content_type(filepath)
            )
        if method in ('PUT', 'POST'):
            filepath.parent.mkdir(parents=True, exist_ok=True)
            mode = 'wb' if body else 'w'
            with open(filepath, mode) as f:
                f.write(body if body else '')
            status = HTTPStatus.OK if filepath.exists() else HTTPStatus.CREATED
            return self._response(status, f"File {'updated' if status==HTTPStatus.OK else 'created'}".encode())
        if method == 'DELETE':
            if filepath.exists():
                filepath.unlink()
                return self._response(HTTPStatus.OK, b'Deleted')
            return self._response(HTTPStatus.NOT_FOUND)
        return self._response(HTTPStatus.METHOD_NOT_ALLOWED)

    def _route_resources(self, method, path, body):
        segments = path.strip('/').split('/')
        _, cat, *rest = segments + [None]*3
        if not cat:
            return self._response_json(self.resources)
        cat_list = self.resources.setdefault(cat, [])
        if not rest[0]:
            return self._handle_cat(method, cat, cat_list, body)
        return self._handle_item(method, cat, cat_list, rest[0], body)

    def _handle_cat(self, method, cat, cat_list, body):
        if method == 'GET':
            return self._response_json(cat_list)
        if method == 'POST':
            obj = json.loads(body)
            obj_id = max((o.get('id', 0) for o in cat_list), default=0) + 1
            new = {'id': obj_id, **obj}
            cat_list.append(new)
            self._write_resources()
            return self._response(HTTPStatus.CREATED)
        if method == 'PUT':
            data = json.loads(body)
            self.resources[cat] = (
                data if isinstance(data, list)
                else [ {'id': max((o.get('id', 0) for o in cat_list), default=0)+1, **data} ]
            )
            self._write_resources()
            return self._response(HTTPStatus.OK)
        return self._response(HTTPStatus.METHOD_NOT_ALLOWED)

    def _handle_item(self, method, cat, cat_list, item_id, body):
        item = next((o for o in cat_list if str(o.get('id')) == item_id), None)
        if method == 'GET':
            return (
                self._response_json(item)
                if item else self._response(HTTPStatus.NOT_FOUND)
            )
        if method == 'PUT' and item:
            item.update(json.loads(body))
            self._write_resources()
            return self._response(HTTPStatus.OK)
        if method == 'DELETE' and item:
            cat_list.remove(item)
            self._write_resources()
            return self._response(HTTPStatus.OK)
        return self._response(
            HTTPStatus.NOT_FOUND if not item else HTTPStatus.METHOD_NOT_ALLOWED
        )

    def _response(self, status: HTTPStatus, body: bytes = b'', content_type: str = 'text/plain') -> bytes:
        lines = [
            f"HTTP/1.1 {status.value} {status.phrase}",
            f"Content-Type: {content_type}",
            f"Content-Length: {len(body)}",
            "Connection: close",
            ""
        ]
        return ("\r\n".join(lines) + "\r\n").encode('utf-8') + body

    def _response_json(self, data) -> bytes:
        js = json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')
        return self._response(
            HTTPStatus.OK, js,
            content_type='application/json; charset=utf-8'
        )

    def _content_type(self, path: Path) -> str:
        return {
            '.html': 'text/html',
            '.txt': 'text/plain',
            '.json': 'application/json',
        }.get(path.suffix.lower(), 'application/octet-stream')


if __name__ == '__main__':
    try:
        port = int(
            input(f"Port (blank for {DEFAULT_PORT}): ").strip() or DEFAULT_PORT
        )
    except ValueError:
        port = DEFAULT_PORT
    server = SimpleHTTPServer(port=port)
    server.start()
