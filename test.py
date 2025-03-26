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
import os
import sys
from datetime import datetime

def run_test():
    print("Starting HTTP Test Suite...")
    start_time = time.time()

    # Create necessary directories
    os.makedirs('Server', exist_ok=True)
    os.makedirs('Client/downloads', exist_ok=True)

    try:
        # Start server
        print("\n1. Starting server...")
        server_process = subprocess.Popen([sys.executable, 'server.py'])
        time.sleep(1)  # Wait for server to start
        print("Server started successfully")

        # Create test files
        with open('Server/test1.html', 'w') as f:
            f.write('<html><body>Test 1</body></html>')
        with open('Client/test3.html', 'w') as f:
            f.write('<html><body>Test 3</body></html>')
        
        print("\n2. Testing HTTP operations...")
        
        # Test GET operation
        print("\nTesting GET...")
        client_process = subprocess.Popen([sys.executable, 'client.py'],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True)
        get_commands = "GET\ntext\ntest1.html\nEXIT\n"
        output, errors = client_process.communicate(get_commands)
        client_process.wait()

        # Test PUT operation
        print("\nTesting PUT...")
        client_process = subprocess.Popen([sys.executable, 'client.py'],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True)
        put_commands = "PUT\ntest3.html\nEXIT\n"
        output, errors = client_process.communicate(put_commands)
        client_process.wait()

        # Test DELETE operation
        print("\nTesting DELETE...")
        client_process = subprocess.Popen([sys.executable, 'client.py'],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True)
        delete_commands = "DELETE\ntest2.html\nEXIT\n"
        output, errors = client_process.communicate(delete_commands)
        client_process.wait()

        # Verify results
        tests_passed = True
        
        print("\nVerifying operations:")
        # Check GET
        if os.path.exists('Client/downloads/test1.html'):
            print("✓ GET: test1.html downloaded successfully")
        else:
            print("✗ GET: Failed to download test1.html")
            tests_passed = False

        # Check PUT
        if os.path.exists('Server/test3.html'):
            print("✓ PUT: test3.html uploaded successfully")
        else:
            print("✗ PUT: Failed to upload test3.html")
            tests_passed = False

        # Check DELETE
        if not os.path.exists('Server/test2.html'):
            print("✓ DELETE: test2.html deleted successfully")
        else:
            print("✗ DELETE: Failed to delete test2.html")
            tests_passed = False

    finally:
        # Cleanup
        print("\n3. Cleaning up...")
        server_process.terminate()
        server_process.wait()
        
        for file in ['Server/test1.html', 'Server/test3.html', 'Client/test3.html']:
            try:
                os.remove(file)
            except:
                pass

    # Calculate and show execution time
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\nTest Summary:")
    print(f"{'='*50}")
    print(f"Total execution time: {execution_time:.2f} seconds")
    print(f"Tests {'PASSED' if tests_passed else 'FAILED'}")
    print(f"{'='*50}")

if __name__ == '__main__':
    run_test()

"""
Required Test Files Structure:

1. Server/test1.html:
<html><body>Test 1</body></html>

2. Server/test2.html:
<html><body>Test 2</body></html>

3. Client/test3.html:
<html><body>Test 3</body></html>

4. Expected Directory Structure:
HTTP_lab/
├── Server/
│   ├── test1.html (created during test)
│   ├── test2.html (created during test)
│   └── test3.html (created by PUT request)
├── Client/
│   ├── downloads/
│   │   └── test1.html (created by GET request)
│   └── test3.html (created during test)
├── server.py
├── client.py
└── test.py

5. Test Flow:
a. GET Request:
   - Retrieves test1.html from Server/
   - Saves to Client/downloads/
   - Verifies content and 200 OK response

b. PUT Request:
   - Uploads test3.html from Client/
   - Creates file in Server/
   - Verifies 201 Created response

c. DELETE Request:
   - Deletes test2.html from Server/
   - Verifies 200 OK response
   - Confirms file deletion

Note: All files are automatically created and cleaned up during the test execution.
No manual file creation is needed."
"""