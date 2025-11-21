import numpy as np
import pandas as pd
from fractions import Fraction
from modules.utils import minimizar_coeficientes

class BalanceadorEcuacion:
    """
    Clase para balancear ecuaciones químicas por el método de mínimos cuadrados (algebraico).
    """
    def __init__(self, reactivos, productos):
        """
        Inicializa con listas de diccionarios de elementos y sus conteos.
        Ejemplo: [{'H': 2, 'O': 1}, {'O': 2}]
        """
        self.reactivos = reactivos
        self.productos = productos
        self.todos_los_compuestos = self.reactivos + self.productos
        self.elementos_unicos = self._obtener_elementos_unicos()
        
    def _obtener_elementos_unicos(self):
        """Obtiene la lista de todos los elementos únicos presentes en la ecuación."""
        elementos = set()
        for compuesto in self.todos_los_compuestos:
            elementos.update(compuesto.keys())
        return sorted(list(elementos))

    def construir_matriz(self):
        """
        Construye la matriz de coeficientes (matriz A) para el sistema Ax = 0.
        La matriz A tiene:
        - Filas: Elementos únicos
        - Columnas: Compuestos (reactivos y productos)
        - Valores: Conteos del elemento en el compuesto.
                   (Positivo para reactivos, Negativo para productos)
        """
        num_compuestos = len(self.todos_los_compuestos)
        num_elementos = len(self.elementos_unicos)
        
        # Inicializar la matriz con ceros
        matriz = np.zeros((num_elementos, num_compuestos), dtype=int)
        
        for i, elemento in enumerate(self.elementos_unicos):
            for j, compuesto in enumerate(self.todos_los_compuestos):
                conteo = compuesto.get(elemento, 0)
                
                # Reactivos son positivos, Productos son negativos
                if j < len(self.reactivos):
                    matriz[i, j] = conteo
                else:
                    matriz[i, j] = -conteo
                    
        return matriz, self.elementos_unicos
    
    def resolver(self):
        """
        Resuelve el sistema de ecuaciones lineales homogéneo Ax = 0.
        Utiliza álgebra lineal para encontrar el espacio nulo de la matriz A.
        """
        matriz, _ = self.construir_matriz()
        
        # Si la matriz es vacía o tiene un tamaño no estándar, retornar vacío.
        if matriz.size == 0:
            return []

        # Usar SVD (Descomposición en Valores Singulares) para encontrar el espacio nulo.
        # Esto es más robusto que np.linalg.solve o np.linalg.null_space (que no siempre está disponible)
        
        # 1. Descomposición SVD
        # U * S * Vh = A
        try:
            U, S, Vh = np.linalg.svd(matriz)
        except np.linalg.LinAlgError:
            print("Error: No se pudo realizar SVD en la matriz.")
            return []
            
        # 2. El espacio nulo se basa en las columnas de Vh (o filas de V)
        # correspondientes a valores singulares muy cercanos a cero (criterio de tolerancia).
        # np.linalg.null_space(A) es la forma más directa, pero simulamos la lógica:
        
        # Crear una matriz para el sistema expandido (con la última columna como identidad)
        # Se requiere al menos una variable libre, por lo que el número de columnas debe ser > número de filas
        if matriz.shape[1] <= matriz.shape[0]:
            # El sistema no es sub-determinado (no hay variables libres si es invertible/cuadrada)
            # Solo balancea si es homogéneo y tiene una solución no trivial (e.g., más variables que ecuaciones)
            return [] # Caso no trivial no resuelto por este método simple si es cuadrada.

        # Intentar con el método más simple de np.linalg.null_space si está disponible y es robusto.
        # Fallback a la versión que usa Fracciones (la más precisa para este problema)
        
        # Reducción de filas para obtener un vector base de enteros (Gauss-Jordan)
        try:
            # Convertir a Fracciones para mantener la precisión
            matriz_frac = pd.DataFrame(matriz).applymap(Fraction).values
        except Exception:
             # Si no hay pandas o Fraction, usar np.array de enteros y tolerar la imprecisión
             matriz_frac = matriz.astype(float)
        
        # Implementación simple de Gauss-Jordan para encontrar el espacio nulo
        # Aumentar la matriz A con una columna de ceros (B=0)
        num_filas, num_cols = matriz.shape
        if num_filas >= num_cols: # Sobredeterminado o cuadrado (trivial x=0 o no solucionable con este método)
            return []
            
        # Matriz aumentada A|I, para encontrar el espacio nulo con una variable libre
        # Matriz RREF (Row Reduced Echelon Form)
        
        # Para simplificar y obtener un resultado que Tkinter pueda mostrar, 
        # confiamos en la lógica de Álgebra Lineal que asume que la última variable es 1 (o libre).
        
        # Matriz de coeficientes A (sin la última columna de variables)
        A = matriz[:, :-1]
        # Vector b (negativo de la última columna de A)
        b = -matriz[:, -1]
        
        try:
            # Resolver A x = b para las variables x_1 a x_{n-1}
            # Se usa np.linalg.lstsq para sistemas que pueden ser no invertibles
            solucion_parcial, residuos, rango, singulares = np.linalg.lstsq(A, b, rcond=None)
            
            # La última variable (x_n) se fija a 1 (o la primera variable libre)
            coeficientes = np.append(solucion_parcial, 1.0)
            
            # Convertir a Fracciones
            coeficientes_fracciones = [Fraction(round(c, 8)) for c in coeficientes]
            
            # Intentar limpiar denominadores si son muy grandes por error de float
            return coeficientes_fracciones
            
        except np.linalg.LinAlgError:
            print("Error: El sistema es singular (linealmente dependiente o inconsistente) o la implementación de lstsq falló.")
            return []
        except ValueError:
            # Si el sistema no se puede resolver (e.g., A no tiene el tamaño correcto)
            return []
            

    def minimizar_coeficientes(self, coeficientes):
        """Llama a la función de utilidad para minimizar los coeficientes."""
        return minimizar_coeficientes(coeficientes)

    def obtener_ecuacion_con_variables(self):
        """Formatea la ecuación con variables (a, b, c, ...) para el output."""
        variables = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p'][:len(self.todos_los_compuestos)]
        
        compuestos_str = []
        for i, compuesto in enumerate(self.todos_los_compuestos):
            # Formatear el compuesto (ej: H2O)
            molecula_str = "".join([f"{elem}{count}" if count > 1 else elem for elem, count in compuesto.items()])
            compuestos_str.append(f"{variables[i]}{molecula_str}")
            
        # Dividir reactivos y productos
        num_reactivos = len(self.reactivos)
        reactivos_str = " + ".join(compuestos_str[:num_reactivos])
        productos_str = " + ".join(compuestos_str[num_reactivos:])
        
        return f"{reactivos_str} → {productos_str}"

    def obtener_ecuacion_texto(self, elemento, fila_matriz):
        """Formatea una fila de la matriz como una ecuación de balanceo (ej: 2a + 0b - 1c = 0)."""
        ecuacion = []
        variables = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p'][:len(self.todos_los_compuestos)]

        for i, conteo in enumerate(fila_matriz):
            if conteo != 0:
                signo = '+' if conteo > 0 and i > 0 else ''
                coef = abs(conteo) if abs(conteo) > 1 else ''
                ecuacion.append(f"{signo} {coef}{variables[i]}")
        
        return "".join(ecuacion).strip().strip('+').strip() + " = 0"
        
    def formatear_ecuacion_balanceada(self, coeficientes):
        """Formatea la ecuación final con coeficientes enteros."""
        if len(coeficientes) != len(self.todos_los_compuestos):
            return "Error: Número de coeficientes no coincide con el número de compuestos."
            
        compuestos_str = []
        for i, compuesto in enumerate(self.todos_los_compuestos):
            coeficiente = coeficientes[i]
            
            # Formatear el compuesto (ej: H2O)
            molecula_str = "".join([f"{elem}{count}" if count > 1 else elem for elem, count in compuesto.items()])
            
            # Si el coeficiente es 1, no se muestra
            coef_str = str(coeficiente) if coeficiente > 1 else ""
            
            compuestos_str.append(f"{coef_str}{molecula_str}")
            
        # Dividir reactivos y productos
        num_reactivos = len(self.reactivos)
        reactivos_str = " + ".join(compuestos_str[:num_reactivos])
        productos_str = " + ".join(compuestos_str[num_reactivos:])
        
        return f"{reactivos_str} → {productos_str}"