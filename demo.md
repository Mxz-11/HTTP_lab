**Demo**

This demo shows the principal features of the HTTP Lab

**HTTP Client**

- Send HTTP requests, in a way that:

    - It is possible to choose the URL to which the request will be sent
    - Use any available HTTP verb in the request (GET, HEAD, POST, PUT, DELETE)
    - Automatically add the necessary headers to the request so that it can be processed correctly
    - Add any other arbitrary header desired by the user
    - Specify the body of the request
- Receive and display on screen the response message of the sent request
- Inform about the request status
- Be able to send successive requests, i.e., to send a second request it is not necessary to restart the program

To send HTTP request we will have to create a mock server. For this part we decided to choose [beeceptor.com](https://beeceptor.com/)
With the mock server on Beeceptor we will be able to send resources, but not to obtain the 

We copy the URL: https://prueba.free.beeceptor.com and then we can use it to send requests to this URL

Examples:

Using put method with body

```
Enter host or URL (blank for 'localhost'): https://prueba.free.beeceptor.com
Enter server port (blank for 80): 
Enter base path (blank for ''):

Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': put
Enter the resource path (blank => use base_path): /
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.

Send from local file? (y/N): n
Enter body content in JSON format (end input with a blank line):
hola mundo
```

Using put method with a file:

```
Enter host or URL (blank for 'localhost'): https://prueba.free.beeceptor.com
Enter server port (blank for 80): 
Enter base path (blank for ''):

Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': put
Enter the resource path (blank => use base_path): /
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.

Send from local file? (y/N): y
Enter local filename (relative path): test1.html
```

Using get method:

```
Enter host or URL (blank for 'localhost'): https://prueba.free.beeceptor.com
Enter server port (blank for 80): 
Enter base path (blank for ''):

Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': get
Enter the resource path (blank => use base_path): 
Do you want to save the response to a file? (y/N): n
```

Using head method:

```
Enter host or URL (blank for 'localhost'): https://prueba.free.beeceptor.com
Enter server port (blank for 80): 
Enter base path (blank for ''):

Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': head
Enter the resource path (blank => use base_path): 
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.
X-Custom:123

```

Using post method:

```
Enter host or URL (blank for 'localhost'): https://prueba.free.beeceptor.com
Enter server port (blank for 80): 
Enter base path (blank for ''):

Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': put
Enter the resource path (blank => use base_path): /
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.

Send from local file? (y/N): n
Enter body content in JSON format (end input with a blank line):
hola mundo
```

Using delete method:

```
Enter host or URL (blank for 'localhost'): https://prueba.free.beeceptor.com
Enter server port (blank for 80): 
Enter base path (blank for ''):

Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': delete 
Enter the resource path (blank => use base_path): 
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.
```

So as we can see, the client is able to send requests to any URL, send any verb in the request, add the necessary headers and some desired
by the user, specify the body of the request, inform about the status with the corresponding code and send successive requests.

**HTTP Server**

- Support, at least, the following endpoints, when they are correctly called (correct verb, correct headers...):
    - An endpoint that returns static content (e.g., a static HTML file)
    - An endpoint that adds a new resource to the server according to the specified payload
    - An endpoint that allows viewing a list of resources
    - An endpoint that allows modifying a resource
    - An endpoint that allows deleting a resource
- Return the appropriate error codes if the endpoints are not invoked correctly
- Attend to multiple requests concurrently
- Offer minimal configuration that allows choosing on which port the server starts
- It is not necessary for the resources to be persisted; they can be managed in memory

We decided to save locally the information of the HTTP server. Therefore, the information will be located in the /Server directory.
We have decided to create an endpoint called resources, this endpoint will not be accesible manually (the file resources.json cannot be 
accessed by any user).
The endpoint can be found in /resources/{category}/{id}

However, the endpoint allows:

- An endpoint that returns static content (e.g., a static HTML file)

Example:

To launch any instance of the Client-Server pair we will need to use:
```bash
python3 nServer.py
```
```
Put the port to start the server (default 8080): 
HTTP Server listening on localhost:8080
```
```bash
python3 nClient.py
```

Once started the Server, the Client will be like this:

```
Enter host or URL (blank for 'localhost'): 
Enter server port (blank for 80): 8080
Enter base path (blank for ''): 

Using host=localhost, port=8080, base_path=
(No SSL). If the server needs HTTPS on port 443, this will fail.


Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': get
Enter the resource path (blank => use base_path): /resources 
Do you want to save the response to a file? (y/N): n
Connected (plain) to localhost:8080
```

- An endpoint that adds a new resource to the server according to the specified payload

```
Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': post
Enter the resource path (blank => use base_path): /resources/gatos
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.

Enter body content in JSON format (end input with a blank line):
{
    "name": "prueba",
    "origin": "España",
    "size": "Very big"
}
```

- An endpoint that allows viewing a list of resources

```
Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': get
Enter the resource path (blank => use base_path): /resources 
Do you want to save the response to a file? (y/N): n
```

- An endpoint that allows modifying a resource

```
Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': put
Enter the resource path (blank => use base_path): /resources/gatos/8
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.

Enter body content in JSON format (end input with a blank line):
{
"hola mundo": 3
}
```

- An endpoint that allows deleting a resource

```
Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': delete
Enter the resource path (blank => use base_path): /resources/gatos/8
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.
```

- Return the appropriate error codes if the endpoints are not invoked correctly
We can see the codes are shown on the terminal when the server respond the requests

- Attend to multiple requests concurrently
We can use 2 nClients at the same time to prove it.

- It is not necessary for the resources to be persisted; they can be managed in memory
In this case, the file resources.json located on the directory /Server/private/resources.json keep the information of the server in a json style.
Cannot be access using:

```
Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': get
Enter the resource path (blank => use base_path): /private/resources.json
Do you want to save the response to a file? (y/N): n
```

- Offer minimal configuration that allows choosing on which port the server starts

```bash
newgrp wireshark
```

```bash
wireshark
```

Chosing the loopback network
```wireshark
tcp.port == X || udp.port == X
```


**Optional features**

For the optional features, we decided to do: Sending and receiving multimedia files, Logging, Automated Testing, GUI for the client and CRUD persistency (asked by us)

**Sending and receiving multimedia files**

To prove the files are correctly send from the client to the server, first the client has to detect if the file must be send as a binary. If so, the is_binary flag is set to True and Content‑Type header will be set to the corresponding value.

Then, the server has to recieve correctly the binary and handle it. To do this, it looks at Content‑Type header and converts it.

In the oposite direction the workflow is the same.


- Example for get a mp3 from the server:
```
Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': get
Enter the resource path (blank => use base_path): a.mp3
Do you want to save the response to a file? (y/N): y
Enter filename to save response: a.mp3
```

- Example for post/put a gif to the server:
```
Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': post
Enter the resource path (blank => use base_path): a.gif
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.

Send from local file? (y/N): y
Enter local filename (relative path): a.gif
```
```
Enter HTTP method (GET/HEAD/POST/PUT/DELETE) or 'exit': put
Enter the resource path (blank => use base_path): a.gif
Enter any custom headers you want (e.g. 'X-Custom: 123'). Blank line to finish.

Send from local file? (y/N): y
Enter local filename (relative path): a.gif
```

**Logging**

We have added a function (log_full_request) and it's called after the request_data, headers and body have been processed. We store the IP addres, port of the client and the timestamp of when the request is received. We store all this data in a server.log file inside the private folder of the server, and it looks like this:
```
[2025-05-04 14:01:21] 127.0.0.1:13261 - Request received:
GET /a.gif HTTP/1.1
Host: localhost
Connection: close
Accept: */*
------------------------------------------------------------

============================================================
```

**Automated Testing**

To ensure the correct functionality of the HTTP server, we have implemented automated tests using the `unittest` framework in Python. These tests are located in the `test.py` file and cover various aspects of the server's behavior.

**How to execute `test.py`**

1. **Prerequisites**:
   - Ensure that the HTTP server (`nServer.py`) is running before executing the tests. The tests require the server to be active to validate its responses.
   - Verify that the server is running on the default port `8080`. If a different port is used, update the port in the `test.py` file.

2. **Steps to execute**:
   - Open a terminal.
   - Navigate to the directory where the `test.py` file is located.
   - Run the following command:
     ```bash
     python3 -m unittest test.py -v
     ```
   - This will execute all the tests defined in the file and display the results in the terminal.

**Tests included in [test.py](./test.py)**

- **Static content tests**:
  - test_html: Verifies that the server can serve a static HTML file (`index.html`).
  - test_mp3 and test_mp4: Check that the server can serve multimedia files (`a.mp3` and `a.mp4`).

- **JSON resource tests**:
  - test_get_resources: Ensures the server can return all resources in JSON format from the `/resources` endpoint.
  - test_get_cat: Validates that the server can return a specific category (`gatos`) from the `/resources/gatos` endpoint.
  - test_post_new_cat: Sends a `POST` request to create a new resource in the `gatos` category.
  - test_update_cat: Sends a `PUT` request to update an existing resource in the `gatos` category.
  - test_post_delete_cat: Creates a resource using `POST` and then deletes it using `DELETE`.

- **Multimedia file tests**:
  - test_post_a_txt: Sends a `POST` request to upload the `a.txt` file to the server.
  - test_post_a_gif: Sends a `POST` request to upload the `a.gif` file to the server.
  - test_post_a_jpg: Sends a `POST` request to upload the `a.jpg` file to the server.

- **Additional tests**:
  - test_6_external_get_and_save: Sends a `GET` request to an external server (`example.com`) and saves the response to a local file.
  - test_404_not_found: Verifies that the server returns a `404 Not Found` status for non-existent resources.

**Expected results**

- If all tests pass, the following message will be displayed:
  ```bash
  ----------------------------------------------------------------------
  Ran X tests in Y.YYYs

  OK
  ```

**GUI for the client**

We have done a GUI using the Gradio library on python.


**CRUD persistency**

As we saw before, the content can be accessible by every user if the resources are on the file /Server/private/resources.json

For example, adding this content:
```json
{
    "gatos": [
        {
            "id": 1,
            "nombre": "Maine Coon",
            "origen": "Estados Unidos",
            "tamaño": "Grande",
            "curiosidad": "Es una de las razas más grandes del mundo felino doméstico."
        },
        {
            "id": 2,
            "nombre": "Siamés",
            "origen": "Tailandia",
            "tamaño": "Mediano",
            "curiosidad": "Se le considera una raza real en su país de origen."
        },
        {
            "id": 3,
            "nombre": "Esfinge",
            "origen": "Canadá",
            "tamaño": "Mediano",
            "curiosidad": "A pesar de no tener pelo, necesita baños frecuentes por su piel grasa."
        },
        {
            "id": 4,
            "nombre": "Bengalí",
            "origen": "Estados Unidos",
            "tamaño": "Grande",
            "curiosidad": "Proviene del cruce entre gatos domésticos y gatos leopardo asiáticos."
        },
        {
            "id": 5,
            "nombre": "Juanlu",
            "origen": "Estados Afganos",
            "tamaño": "Standard"
        },
        {
            "id": 6,
            "nombre": "Siamés Actualizado",
            "origen": "Tailandia",
            "tamaño": "Mediano"
        },
        {
            "id": 7,
            "nombre": "Siamés gatuno",
            "origen": "Tailandia",
            "tamaño": "Mediano"
        }
    ],
    "perros": [
        {
            "id": 1,
            "nombre": "Labrador Retriever",
            "origen": "Canadá",
            "tamaño": "Grande",
            "curiosidad": "Es una de las razas más populares del mundo por su carácter amigable y entrenabilidad."
        },
        {
            "id": 2,
            "nombre": "Pastor Alemán",
            "origen": "Alemania",
            "tamaño": "Grande",
            "curiosidad": "Se destaca como perro policía y de trabajo por su inteligencia y obediencia."
        },
        {
            "id": 3,
            "nombre": "Chihuahua",
            "origen": "México",
            "tamaño": "Pequeño",
            "curiosidad": "Es una de las razas más pequeñas del mundo, pero con gran temperamento."
        },
        {
            "id": 4,
            "nombre": "Husky Siberiano",
            "origen": "Rusia",
            "tamaño": "Mediano",
            "curiosidad": "Famoso por su resistencia al frío y su capacidad para tirar trineos en largas distancias."
        },
        {
            "id": 5,
            "nombre": "Bulldog Inglés",
            "origen": "Reino Unido",
            "tamaño": "Mediano"
        },
        {
            "id": 6,
            "nombre": "Beagle",
            "origen": "Reino Unido",
            "tamaño": "Pequeño"
        },
        {
            "id": 7,
            "nombre": "Dálmata",
            "origen": "Croacia",
            "tamaño": "Mediano"
        }
    ],
    "dinos":[
        {
            "id": 1,
            "nombre": "Tyrannosaurus Rex",
            "periodo": "Cretácico tardío",
            "tamaño": "Muy grande",
            "curiosidad": "Tenía la mordida terrestre más potente jamás medida."
        },
        {
            "id": 2,
            "nombre": "Triceratops",
            "periodo": "Cretácico tardío",
            "tamaño": "Grande",
            "curiosidad": "Sus tres cuernos podían alcanzar 1 m de longitud."
        },
        {
            "id": 3,
            "nombre": "Velociraptor",
            "periodo": "Cretácico tardío",
            "tamaño": "Pequeño",
            "curiosidad": "Probablemente estaba cubierto de plumas."
        },
        {
            "id": 4,
            "nombre": "Brachiosaurus",
            "periodo": "Jurásico tardío",
            "tamaño": "Enorme",
            "curiosidad": "Su cuello levantaba la cabeza a 13 m de altura."
        },
        {
            "id": 5,
            "nombre": "Stegosaurus",
            "periodo": "Jurásico tardío",
            "tamaño": "Grande",
            "curiosidad": "Las placas de la espalda servían para termorregularse."
        }
    ]
}
```

Dinos (dinoraurs) will be added to the system and able to obtain with a request to the server.
