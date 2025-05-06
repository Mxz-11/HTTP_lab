# -*- coding: utf-8 -*-
import unittest
import socket
import json
import os
from datetime import datetime

# python3 -m unittest test.py -v

class TestHTTPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        cls.host = "localhost"
        cls.port = 8080
        cls.base_path = ""
        cls.resources_file = "Server/private/resources.json"
        
        # Hacer una copia del archivo resources.json original
        if os.path.exists(cls.resources_file):
            with open(cls.resources_file, 'r', encoding='utf-8') as f:
                cls.original_resources = json.load(f)
        else:
            cls.original_resources = {"gatos": [], "perros": []}

    @classmethod
    def tearDownClass(cls):
        # Para Restaurar el archivo resources.json a su estado original
        with open(cls.resources_file, 'w', encoding='utf-8') as f:
            json.dump(cls.original_resources, f, indent=4, ensure_ascii=False)

    def send_request(self, method, path, body=None, headers=None, is_binary=False):
        """Envía una solicitud HTTP y devuelve la respuesta"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        
        # Construir la solicitud
        request = f"{method} {path} HTTP/1.1\r\n"
        request += f"Host: {self.host}\r\n"
        request += "Connection: close\r\n"
        
        if headers:
            for key, value in headers.items():
                request += f"{key}: {value}\r\n"
        
        if body is not None:
            if isinstance(body, str):
                body = body.encode('utf-8')
            request += f"Content-Length: {len(body)}\r\n\r\n"
            request = request.encode('utf-8') + body
        else:
            request += "\r\n"
            request = request.encode('utf-8')
        
        sock.sendall(request)
        
        # Recibir la respuesta
        response = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        
        sock.close()
        
        if not is_binary:
            return response.decode('utf-8')
        return response

    def test_html(self):
        """GET to a .html"""
        response = self.send_request("GET", "/index.html")
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn("Content-Type: text/html", response)
        
    def test_head_html(self):
        """HEAD to a .html"""
        response = self.send_request("HEAD", "/index.html")
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn("Content-Type: text/html", response)
        
    def test_mp3(self):    
        """GET to a binary (mp3)"""
        response = self.send_request("GET", "/a.mp3", is_binary=True)
        self.assertIn(b"HTTP/1.1 200 OK", response)
        self.assertIn(b"Content-Type: audio/mpeg", response)
    
    def test_head_mp3(self):    
        """HEAD to a binary (mp3)"""
        response = self.send_request("HEAD", "/a.mp3", is_binary=True)
        self.assertIn(b"HTTP/1.1 200 OK", response)
        self.assertIn(b"Content-Type: audio/mpeg", response)
            
    def test_mp4(self):
        """GET to a binary (mp4)"""
        response = self.send_request("GET", "/a.mp4", is_binary=True)
        self.assertIn(b"HTTP/1.1 200 OK", response)
        self.assertIn(b"Content-Type: video/mp4", response)
        
    def test_head_mp4(self):
        """HEAD to a binary (mp4)"""
        response = self.send_request("HEAD", "/a.mp4", is_binary=True)
        self.assertIn(b"HTTP/1.1 200 OK", response)
        self.assertIn(b"Content-Type: video/mp4", response)
        
    def test_get_resources(self):
        """GET to a JSON"""
        response = self.send_request("GET", "/resources")
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn('"gatos"', response)
        self.assertIn('"perros"', response)
        
    def test_head_resources(self):
        """HEAD to a JSON"""
        response = self.send_request("HEAD", "/resources")
        self.assertIn("HTTP/1.1 200 OK", response)
        
    def test_get_cat(self):
        """GET to gatos collection"""
        response = self.send_request("GET", "/resources/gatos")
        self.assertIn("HTTP/1.1 200 OK", response)
        
    def test_head_cat(self):
        """HEAD to gatos collection"""
        response = self.send_request("HEAD", "/resources/gatos")
        self.assertIn("HTTP/1.1 200 OK", response)
        
    def test_get_cat2(self):    
        """GET to gatos id 1"""
        response = self.send_request("GET", "/resources/gatos/1")
        self.assertIn("HTTP/1.1 200 OK", response)
    
    def test_head_cat2(self):    
        """HEAD to gatos id 2"""
        response = self.send_request("HEAD", "/resources/gatos/2")
        self.assertIn("HTTP/1.1 200 OK", response)

    def test_get_cat3(self):    
        """GET to inexistent id"""
        response = self.send_request("HEAD", "/resources/gatos/4252243")
        self.assertIn("HTTP/1.1 404 Not Found", response)
    
    
    def test_head_cat3(self):    
        """HEAD to inexistent id"""
        response = self.send_request("HEAD", "/resources/gatos/312412")
        self.assertIn("HTTP/1.1 404 Not Found", response)
    
    def test_post_new_cat(self):
        """POST to create a new cat"""
        new_cat = {
            "nombre": "Nuevo Gato",
            "origen": "Spain",
            "curiosidad": "Raza creada para pruebas"
        }
        headers = {}
        response = self.send_request(
            "POST", 
            "/resources/gatos", 
            body=json.dumps(new_cat),
            headers=headers
        )
        self.assertIn("HTTP/1.1 201 Created", response)
        


    def test_update_cat(self):
        """PUT to update a cat"""
        updated_cat = {
            "nombre": "Gato Actualizado",
            "origen": "Spain",
            "curiosidad": "Información actualizada"
        }
        headers = {}
        
        response = self.send_request(
            "PUT", 
            f"/resources/gatos/2", 
            body=json.dumps(updated_cat),
            headers=headers
        )
        self.assertIn("HTTP/1.1 200 OK", response)
        
        
    def test_delete_cat(self):
        """DELETE a cat""" 
        response = self.send_request("DELETE", f"/resources/gatos/4")
        self.assertIn("HTTP/1.1 200 OK", response)
        
        response = self.send_request("GET", f"/resources/gatos/4")
        self.assertIn("HTTP/1.1 404 Not Found", response)

    def test_404_not_found(self):
        """GET to an inexistent file"""
        response = self.send_request("GET", "/no_existe.txt")
        self.assertIn("404 Not Found", response)

    def test_post_a_gif(self):
        """POST to upload a.gif"""
        file_path = "a.gif"
        with open(file_path, "rb") as f:
            file_content = f.read()

        headers = {
            "Content-Type": "image/gif"
        }
        response = self.send_request(
            "POST",
            f"/{file_path}",
            body=file_content,
            headers=headers
        )
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn("Content-Type: text/plain", response)
        self.assertIn(f"File {file_path} was successfully updated", response)

    def test_post_a_txt(self):
        """POST to upload a.txt"""
        file_path = "a.txt"
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        headers = {
            "Content-Type": "text/plain"
        }
        response = self.send_request(
            "POST",
            f"/{file_path}",
            body=file_content,
            headers=headers
        )
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn("Content-Type: text/plain", response)
        
    def test_put_a_txt(self):
        """PUT to update b.txt with new content"""
        file_path = "b.txt"
        new_content = "Test PUT works"
        
        response = self.send_request(
            "PUT",
            f"/{file_path}",
            body=new_content,
            headers={}
        )
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn("Content-Type: text/plain", response)
        self.assertIn("File b.txt was successfully updated", response)
        
        # Verificar que el contenido se actualizó correctamente
        response = self.send_request("GET", f"/{file_path}")
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn(new_content, response.split("\r\n\r\n")[1])

    def test_post_a_jpg(self):
        """POST to upload a.jpg"""
        file_path = "a.jpg"
        with open(file_path, "rb") as f:
            file_content = f.read()

        headers = {
            "Content-Type": "image/jpeg"
        }
        response = self.send_request(
            "POST",
            f"/{file_path}",
            body=file_content,
            headers=headers
        )
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn("Content-Type: text/plain", response)
    
    def test_access_private_file(self):
        """GET a private file should return 403 Forbidden"""
        response = self.send_request("GET", "/private/server.log")
        self.assertIn("HTTP/1.1 403 Forbidden", response)

    def test_custom_header(self):
        """Send a custom header and check if the response still works"""
        headers = {"X-Test-Header": "abc123"}
        response = self.send_request("GET", "/index.html", headers=headers)
        self.assertIn("HTTP/1.1 200 OK", response)

    def test_put_empty_body(self):
        """PUT with empty body should return 400 or handle gracefully"""
        response = self.send_request("PUT", "/a.txt", body="")
        self.assertIn("200 OK", response)

    def test_delete_nonexistent_file(self):
        response = self.send_request("DELETE", "/no_such_file.txt")
        self.assertIn("404 Not Found", response)

    def test_directory_traversal_attack(self):
        response = self.send_request("GET", "/../nServer.py")
        self.assertIn("403 Forbidden", response)

    def test_invalid_path(self):
        response = self.send_request("GET", "//index.html")
        self.assertIn("HTTP/1.1 403 Forbidden", response)

    def test_post_without_body(self):
        response = self.send_request("POST", "/resources/gatos")
        self.assertIn("400 Bad Request", response)

    def test_log_contains_request(self):
        self.send_request("GET", "/index.html")
        with open("Server/private/server.log", "r", encoding="utf-8") as log:
            log_content = log.read()
        self.assertIn("GET /index.html HTTP/1.1", log_content)

if __name__ == "__main__":
    unittest.main(verbosity=2)
