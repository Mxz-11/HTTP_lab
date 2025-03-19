# -*- coding: utf-8 -*-
"""
Authors:
    - Author Mxz11
    - Añadir vuestros nombres aquí!

Description:
    This script is used for doing the Automated Testing over the HTTP client-server system.

How to compile:
    1. Make sure you have Python installed (version Python 3.12.4 or higher).
    2. Open a terminal or command prompt.
    3. Navigate to the directory where this script is located.
    4. Run the script with the following command:
        python3 test.py
    
    Note: If you're using a virtual environment, activate it before running the script.

Creation Date:
    19/3/2025

Last Modified:
    19/3/2025

"""

import unittest
import subprocess
import time
import socket
import os
import signal
import sys
from threading import Thread

class TestHTTPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start server in a separate process
        cls.server_process = subprocess.Popen([sys.executable, 'server.py'])
        # Wait for server to start
        time.sleep(2)
    
    @classmethod
    def tearDownClass(cls):
        # Kill the server process
        cls.server_process.kill()
        cls.server_process.wait()

    def test_get_and_delete(self):
        # Create test files
        os.makedirs('test', exist_ok=True)
        with open('test/test1.html', 'w') as f:
            f.write('<html><body>Test 1</body></html>')
        with open('test/test2.html', 'w') as f:
            f.write('<html><body>Test 2</body></html>')

        try:
            # Test GET request
            get_process = subprocess.Popen([sys.executable, 'client.py'],
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         text=True)
            
            # Send inputs for GET request
            inputs = "GET\nhtml\ntest/test1.html\nEXIT\n"
            output, error = get_process.communicate(inputs)
            
            # Check if GET was successful
            self.assertIn("200 OK", output)
            self.assertIn("Test 1", output)

            # Test DELETE request
            delete_process = subprocess.Popen([sys.executable, 'client.py'],
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True)
            
            # Send inputs for DELETE request
            inputs = "DELETE\ntest/test2.html\nEXIT\n"
            output, error = delete_process.communicate(inputs)
            
            # Check if DELETE was successful
            self.assertIn("200 OK", output)
            self.assertFalse(os.path.exists('test/test2.html'))

        finally:
            # Cleanup test files
            try:
                os.remove('test/test1.html')
                os.remove('test/test2.html')
                os.rmdir('test')
            except:
                pass

if __name__ == '__main__':
    unittest.main()
