# NOTA ACTUAL: 3,9

# Tareas Pendientes

## Tareas sobre el sistema Cliente-Servidor

[ ] **Obligatorio 6 PTS**  
  - 🚢 HTTP Client
    - Send HTTP requests, in a way that:
        - It is possible to choose the URL to which the request will be sent ✅
        - Use any available HTTP verb in the request (GET, HEAD, POST, PUT, DELETE) ✅
        - Automatically add the necessary headers to the request so that it can be processed correctly ✅
        - Add any other arbitrary header desired by the user 
        - Specify the body of the request ✅
    - Receive and display on screen the response message of the sent request ✅
    - Inform about the request status ✅
    - Be able to send successive requests, i.e., to send a second request it is not necessary to restart the program ✅

  - HTTP Server
    - The HTTP server must be able to do the following:

        - Support, at least, the following endpoints, when they are correctly called (correct verb, correct headers...):
            - An endpoint that returns static content (e.g., a static HTML file) ✅ (get)
            - An endpoint that adds a new resource to the server according to the specified payload ✅ (put)
            - An endpoint that allows viewing a list of resources
            - An endpoint that allows modifying a resource
            - An endpoint that allows deleting a resource ✅ (delete)
        - Return the appropriate error codes if the endpoints are not invoked correctly ✅
        - Attend to multiple requests concurrently ✅
        - Offer minimal configuration that allows choosing on which port the server starts
        - It is not necessary for the resources to be persisted; they can be managed in memory 


[ ] **Automated Testing 1.3 PTS** 

  - Corregir lo que está hecho con PUT, GET y DELETE
  - Hacerlo con POST cuando se implemente

[ ] **Gestión de loggin 2.3 PTS**

  - Preguntarle a Pedro si se puede hacer de la siguiente manera
    - El server pregunta las credenciales al establecer la conexión
    - Guardamos en un fichero .txt nombre y pass de los usuarios
    - El server recibe la entrada y en caso de ser correcta le da un token que será hecho con numRandom y hash
    - El token se va pasando en la cabecera, haciendo que la comunicación funcione SIEMPRE y cuando el token sea correcto
    - El server sabe cual es el token porque para cada conexión lo guarda en un vector/diccionario siendo que guarda el par: addr (Es la IP y el puerto del cliente), token

[X] **Sending and receiving multimedia files 1.3 PTS**

[X] **Conditional GET with cache 1.3 PTS**

[X] **GUI for the client 1.3 PTS**

  - Modificar el fichero prueba.ipynb para actualizar la interfaz gráfica del cliente
