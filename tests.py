import unittest
import threading
import time
import requests
import shutil
import os

from nServer import SimpleHTTPServer

HOST = 'localhost'
PORT = 8080
BASE_URL = f'http://{HOST}:{PORT}'

TEMPLATE = os.path.join(os.path.dirname(__file__), "resources_template.json")
TARGET   = os.path.join(os.path.dirname(__file__), "Server", "private", "resources.json")

def start_server():
    server = SimpleHTTPServer(host=HOST, port=PORT)
    threading.Thread(target=server.start, daemon=True).start()
    time.sleep(1)

def reset_resources_file():
    os.makedirs(os.path.dirname(TARGET), exist_ok=True)
    shutil.copyfile(TEMPLATE, TARGET)

def get_utf8(url, **kwargs):
    """
    Helper to GET and force utf-8 decoding before using .json() or .text.
    """
    r = requests.get(url, **kwargs)
    r.encoding = 'utf-8'
    return r

class TestHTTPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_resources_file()
        start_server()

    def test_01_get_all_categories(self):
        r = get_utf8(f"{BASE_URL}/resources")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("gatos", body)
        self.assertIn("perros", body)

    def test_02_verify_initial_counts(self):
        r = get_utf8(f"{BASE_URL}/resources/gatos")
        self.assertEqual(r.status_code, 200)
        gatos = r.json()
        self.assertEqual(len(gatos), 7)

        r = get_utf8(f"{BASE_URL}/resources/perros")
        self.assertEqual(r.status_code, 200)
        perros = r.json()
        self.assertEqual(len(perros), 8)

    def test_03_get_specific_gato(self):
        r = get_utf8(f"{BASE_URL}/resources/gatos/1")
        self.assertEqual(r.status_code, 200)
        gato = r.json()
        self.assertEqual(gato["nombre"], "Maine Coon")
        self.assertEqual(gato["id"], 1)

    def test_04_get_invalid_id(self):
        r = get_utf8(f"{BASE_URL}/resources/gatos/999")
        self.assertEqual(r.status_code, 404)

    def test_05_update_gato(self):
        payload = {"nombre": "Maine Moderno", "origen": "USA", "tamaño": "Gigante"}
        r = requests.put(f"{BASE_URL}/resources/gatos/1", json=payload)
        self.assertEqual(r.status_code, 200)

        r2 = get_utf8(f"{BASE_URL}/resources/gatos/1")
        self.assertEqual(r2.json()["nombre"], "Maine Moderno")

    def test_06_delete_perro(self):
        r = requests.delete(f"{BASE_URL}/resources/perros/1")
        self.assertEqual(r.status_code, 200)

        r2 = get_utf8(f"{BASE_URL}/resources/perros")
        self.assertEqual(len(r2.json()), 7)

    def test_07_create_new_gato(self):
        nuevo = {"nombre": "Angora", "origen": "Turquía", "tamaño": "Mediano"}
        r = requests.post(f"{BASE_URL}/resources/gatos", json=nuevo)
        self.assertEqual(r.status_code, 201)

        r2 = get_utf8(f"{BASE_URL}/resources/gatos")
        gatos = r2.json()
        self.assertEqual(len(gatos), 8)
        self.assertEqual(gatos[-1]["nombre"], "Angora")
        self.assertEqual(gatos[-1]["id"], max(g["id"] for g in gatos))

    def test_08_method_not_allowed(self):
        r = requests.patch(f"{BASE_URL}/resources/gatos/1", json={"foo":"bar"})
        self.assertEqual(r.status_code, 405)

    def test_09_nonexistent_category(self):
        r = get_utf8(f"{BASE_URL}/resources/pajaros")
        self.assertEqual(r.status_code, 404)

if __name__ == "__main__":
    unittest.main()
