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
