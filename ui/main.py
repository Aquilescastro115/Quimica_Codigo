from .interfaz import iniciar_interfaz # Importa interfaz.py desde la misma carpeta (ui)
import os
import sys

# Agregamos la carpeta raíz del proyecto al path (quimica_balanceo)
# Esto es necesario para que las importaciones absolutas como 'modules.algo' funcionen.
try:
    if __name__ == '__main__':
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..'))
        if project_root not in sys.path:
            sys.path.append(project_root)
except NameError:
    pass


if __name__ == "__main__":
    iniciar_interfaz()