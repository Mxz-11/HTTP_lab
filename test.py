# -*- coding: utf-8 -*-
import unittest
import socket
import json
import os
from datetime import datetime

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
        """Restaurar el archivo resources.json a su estado original"""
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
        """Test 1: GET para archivos existentes"""
        # Probar con index.html
        response = self.send_request("GET", "/index.html")
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn("Content-Type: text/html", response)
        print(response)
    def test_mp3(self):    
        # Probar con a.mp3 (binario)
        response = self.send_request("GET", "/a.mp3", is_binary=True)
        self.assertIn(b"HTTP/1.1 200 OK", response)
        self.assertIn(b"Content-Type: audio/mpeg", response)
        
    def test_mp4(self):
        response = self.send_request("GET", "/a.mp4", is_binary=True)
        self.assertIn(b"HTTP/1.1 200 OK", response)
        self.assertIn(b"Content-Type: video/mp4", response)

    def test_get_resources(self):
        """Test 2: GET para recursos JSON"""
        # Todos los recursos
        response = self.send_request("GET", "/resources")
        self.assertIn("HTTP/1.1 200 OK", response)
        self.assertIn('"gatos"', response)
        self.assertIn('"perros"', response)
        print(response)
        
    def test_get_cat(self):
        # Solo gatos
        response = self.send_request("GET", "/resources/gatos")
        self.assertIn("HTTP/1.1 200 OK", response)
        print(response)
        
    def test_get_dog(self):    
        # Gato específico
        response = self.send_request("GET", "/resources/gatos/1")
        self.assertIn("HTTP/1.1 200 OK", response)
        print(response)

    def test_post_new_cat(self):
        """Test 3: POST para crear nuevo gato"""
        new_cat = {
            "nombre": "Nuevo Gato",
            "origen": "España",
            "tamaño": "Mediano",
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
        
        # Verificar que se creó el nuevo gato
        response = self.send_request("GET", "/resources/gatos")
        print(response)

    def test_update_cat(self):
        """Test 4: PUT para actualizar el gato creado"""
        # Obtener todos los gatos
        response = self.send_request("GET", "/resources/gatos")
        data = json.loads(response.split("\r\n\r\n")[1])
        
        # Buscar el gato creado por nombre
        cat_id = None
        for cat in data:
            if cat["nombre"] == "Nuevo Gato":
                cat_id = cat["id"]
                break

        self.assertIsNotNone(cat_id, "No se encontró el gato creado")
        
        updated_cat = {
            "nombre": "Gato Actualizado",
            "origen": "España",
            "tamaño": "Grande",
            "curiosidad": "Información actualizada"
        }
        headers = {}
        response = self.send_request(
            "PUT", 
            f"/resources/gatos/{cat_id}", 
            body=json.dumps(updated_cat),
            headers=headers
        )
        self.assertIn("HTTP/1.1 200 OK", response)
        
        # Verificar que se actualizó
        response = self.send_request("GET", f"/resources/gatos/{cat_id}")
        print(response)
        
    def test_post_delete_cat(self):
        """Test 5: POST AND DELETE para crear y eliminar el gato"""
        # Obtener todos los gatos
        new_cat = {
            "nombre": "Nuevo Gato",
            "origen": "España",
            "tamaño": "Mediano",
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
        response = self.send_request("GET", "/resources/gatos")
        data = json.loads(response.split("\r\n\r\n")[1])
        
        # Buscar el gato creado
        cat_id = None
        for cat in data:
            if cat["nombre"] == "Nuevo Gato":
                cat_id = cat["id"]
                break

        self.assertIsNotNone(cat_id, "No se encontró el gato a eliminar")
        
        response = self.send_request("DELETE", f"/resources/gatos/{cat_id}")
        self.assertIn("HTTP/1.1 200 OK", response)
        
        # Verificar que ya no existe
        response = self.send_request("GET", f"/resources/gatos/{cat_id}")
        self.assertIn("HTTP/1.1 404 Not Found", response)


    def test_6_external_get_and_save(self):
        """Test 6: GET para archivo externo y guardar localmente"""
        # Cambiamos temporalmente el host y puerto
        original_host, original_port = self.host, self.port
        self.host, self.port = "example.com", 80
        
        try:
            # Intentar conectarse al host externo
            try:
                response = self.send_request("GET", "/")
            except Exception as e:
                self.fail(f"No se pudo conectar al host externo: {e}")
            
            # Validar la respuesta
            self.assertIn("HTTP/1.1 200 OK", response, "El servidor externo no respondió con 200 OK")
            
            # Guardar el contenido en un archivo
            save_filename = "example_home.html"
            try:
                content = response.split("\r\n\r\n", 1)[1]
                with open(save_filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                self.fail(f"Error al guardar el contenido en un archivo: {e}")
            
            # Verificar que el archivo se creó
            self.assertTrue(os.path.exists(save_filename), "El archivo no se creó correctamente")
            
            # Limpiar - eliminar el archivo de prueba
            os.remove(save_filename)
        finally:
            # Restaurar valores originales
            self.host, self.port = original_host, original_port

if __name__ == "__main__":
    unittest.main(verbosity=2)