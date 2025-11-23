# Quimica_Codigo

- Este proyecto utiliza un entorno virtual de Python para manejar sus dependencias.
La carpeta venv NO se incluye en el repositorio, ya que es un entorno específico de cada sistema operativo y de cada usuario.

A continuación se detalla el procedimiento recomendado para configurar el entorno en tu máquina.

- Este proyecto incluye un archivo:

requirements.txt

Este archivo lista todas las dependencias necesarias para ejecutar el proyecto. Cada desarrollador debe crear su propio entorno virtual local y luego instalar esas dependencias.

- Pasos para configurar el entorno virtual:

Sigue los siguientes pasos después de clonar el repositorio:

1. Clonar el repositorio de la forma que tu encuentres mas conveniente 

2. Crear un entorno virtual:
Ejecuta el siguiente comando dentro de la carpeta del proyecto:

python -m venv venv

Esto creará una carpeta llamada venv en tu máquina local.

3.  Activar el entorno virtual con los siguientes comandos:
En Windows:
venv\Scripts\activate

En Linux / MacOS:
source venv/bin/activate

Cuando el entorno esté activo, deberías ver el prefijo (venv) en la terminal, esto te aparecera al lado izquierdo de tu consola

4. Instalar las dependencias necesarias:
Con el entorno virtual activado, ejecuta:

pip install -r requirements.txt

Esto instalará todas las librerías que requiere el proyecto.