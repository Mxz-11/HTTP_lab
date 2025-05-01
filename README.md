# HTTP_lab

## Description
This project implements an HTTP client-server system that supports basic HTTP protocol operations such as `GET`, `POST`, `PUT`, `DELETE`, and `HEAD`. It includes advanced features like resource management, multimedia file transfer, and a graphical interface for the client.

## Completed Features
- **HTTP Client with GUI:** A graphical interface built with `Gradio` to send HTTP requests interactively.
- **Multimedia File Transfer:** Support for transferring images, audio, and video between client and server.
- **CRUD Persistence:** Resource management with CRUD operations stored in a JSON file.
- **Functional HTTP Server:** Implementation of a server supporting multiple HTTP methods and restricted access to private folders.

## 📂 Project Structure

HTTP_lab/

- [nServer.py](./nServer.py)          # HTTP main server
- [nClient.py](./nClient.py)          # HTTP interactive client
- [Server/](./Server)             # Folder with server files
- └── [private/resources.json](./Server/private/resources.json)
-  a.jpg, a.gif, a.txt, index.html, test1.html  # Test files
- [prueba.ipynb](./prueba.ipynb)       # Grafical version
- [README.md](./README.md)

## 💻 How to Run
1. **Server:**
   - Run `nServer.py` to start the server.
   - You can specify the port when starting.

   ```bash
   python nServer.py
    ```
2. **Client:**
    - Run `nClient.py` to start the client on another terminal.
    
    ```bash
    python nClient.py
     ```

3. **GUI Version:**
    - Run `prueba.ipynb` to start the GUI version of the client.

## 📜 Requirements
- Python 3.x
- Gradio

## Authors
- [@Mxz11](https://github.com/Mxz-11)
- [@Arksuga02](https://github.com/Arksuga02)
- [@jrgim](https://github.com/jrgim)
- TODO!! [@Alex]