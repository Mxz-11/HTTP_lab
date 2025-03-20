# Tareas Pendientes

## Tareas sobre el sistema Cliente-Servidor

[ ] **Añadir POST y PUT 6 PTS**  

  - Entender bien que hacen tanto PUT como POST
  - Modificar la parte del cliente para que gestione bien las requests
  - Modificar la parte del servidor para que ejecute como debería

[ ] **Automated Testing 1.3 PTS** 

  - Hecho y funciona correctamente sobre los comandos GET y DELETE
  - Hacerlo con POST y PUT

[ ] **Gestión de loggin 2.3 PTS**

  - Preguntarle a Pedro si se puede hacer de la siguiente manera
    - El server pregunta las credenciales al establecer la conexión
    - Guardamos en un fichero .txt nombre y pass de los usuarios
    - El server recibe la entrada y en caso de ser correcta le da un token que será hecho con numRandom y hash
    - El token se va pasando en la cabecera, haciendo que la comunicación funcione SIEMPRE y cuando el token sea correcto
    - El server sabe cual es el token porque para cada conexión lo guarda en un vector/diccionario siendo que guarda el par: addr (Es la IP y el puerto del cliente), token

[ ] **Sending and receiving multimedia files 1.3 PTS**

  - Corregir para que en vez de html/txt ponga text/plain (Es lo mismo mandar un html que un txt)
  - Hacer que mande imagenes (JPEG, PNG, JPG...), audio, videos...


[ ] **Conditional GET with cache 1.3 PTS**

  - Guardar en el cliente en un vector los archivos simulando una CACHE (Y la fecha en la que se guarda cuando se hace el GET)
  - En caso de pedir un archivo y que If-Modified-Since da true entonces se pasa el archivo en caso de que no se busca en "cache" y saca de "cache"