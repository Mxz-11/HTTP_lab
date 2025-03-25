# NOTA ACTUAL: 3,9

# Tareas Pendientes

## Tareas sobre el sistema Cliente-Servidor

[ ] **Añadir POST 6 PTS**  

  - Implementar el metodo POST (Igual ya está bien... Ni idea xd)

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

  - Modificar el fichero prueba.ipynb para hacer la interfaz gráfica del cliente
