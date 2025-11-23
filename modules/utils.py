import os
import pandas as pd
from fractions import Fraction
from math import gcd
from functools import reduce

# =============================================================================
# CONSTANTES Y DATOS
# =============================================================================

COLORES_GRUPOS = {
    "Metal Alcalino": "#EF5350",       # Rojo suave
    "Metal Alcalinotérreo": "#FFA726", # Naranja
    "Metal de Transición": "#FFEE58",     # Amarillo
    "Lantánido": "#AB47BC",      # Violeta
    "Actínido": "#EC407A",       # Rosa
    "Metal del Bloque p": "#9CCC65",          # Verde Lima
    "Metaloide": "#26A69A",      # Verde Azulado
    "No Metal": "#42A5F5",       # Azul Claro
    "Halógeno": "#29B6F6",       # Cian
    "Gas Noble": "#5C6BC0",      # Índigo
    "Desconocido": "#CFD8DC"     # Gris
}
# La tabla de POSICIONES es clave para el grid layout.
# Las coordenadas son (fila, columna)
# FIX: Se corrigieron las filas de los elementos de los Períodos 2 (B-Ne) y 3 (Al-Ar)
# para que se alineen correctamente con Li/Be (Fila 1) y Na/Mg (Fila 2) respectivamente.
POSICIONES = {
    # Periodo 1 (Fila 0)
    "H": (0, 0), "He": (0, 17), 
    # Periodo 2 (Fila 1)
    "Li": (1, 0), "Be": (1, 1), 
    "B": (1, 12), "C": (1, 13), "N": (1, 14), "O": (1, 15), "F": (1, 16), "Ne": (1, 17),
    # Periodo 3 (Fila 2)
    "Na": (2, 0), "Mg": (2, 1), 
    "Al": (2, 12), "Si": (2, 13), "P": (2, 14), "S": (2, 15), "Cl": (2, 16), "Ar": (2, 17),
    # Periodo 4 (Fila 4 - salta la Fila 3, manteniendo el espaciado original del usuario)
    "K": (4, 0), "Ca": (4, 1), "Sc": (4, 2), "Ti": (4, 3), "V": (4, 4), "Cr": (4, 5), "Mn": (4, 6), "Fe": (4, 7),
    "Co": (4, 8), "Ni": (4, 9), "Cu": (4, 10), "Zn": (4, 11), "Ga": (4, 12), "Ge": (4, 13), "As": (4, 14),
    "Se": (4, 15), "Br": (4, 16), "Kr": (4, 17), 
    # Periodo 5 (Fila 5)
    "Rb": (5, 0), "Sr": (5, 1), "Y": (5, 2), "Zr": (5, 3), "Nb": (5, 4),
    "Mo": (5, 5), "Tc": (5, 6), "Ru": (5, 7), "Rh": (5, 8), "Pd": (5, 9), "Ag": (5, 10), "Cd": (5, 11), "In": (5, 12),
    "Sn": (5, 13), "Sb": (5, 14), "Te": (5, 15), "I": (5, 16), "Xe": (5, 17), 
    # Periodo 6 (Fila 6)
    "Cs": (6, 0), "Ba": (6, 1), 
    # La/Ac: Se mantienen los huecos (6,2) y (7,2) en la tabla principal. La y Ac se definen en el bloque f.
    "Hf": (6, 3), "Ta": (6, 4), "W": (6, 5), "Re": (6, 6), "Os": (6, 7), "Ir": (6, 8), "Pt": (6, 9), "Au": (6, 10),
    "Hg": (6, 11), "Tl": (6, 12), "Pb": (6, 13), "Bi": (6, 14), "Po": (6, 15), "At": (6, 16), "Rn": (6, 17),
    # Periodo 7 (Fila 7)
    "Fr": (7, 0), "Ra": (7, 1), 
    "Rf": (7, 3), "Db": (7, 4), "Sg": (7, 5), "Bh": (7, 6), "Hs": (7, 7), "Mt": (7, 8),
    "Ds": (7, 9), "Rg": (7, 10), "Cn": (7, 11), "Nh": (7, 12), "Fl": (7, 13), "Mc": (7, 14), "Lv": (7, 15),
    "Ts": (7, 16), "Og": (7, 17),
    
    # Lantánidos (Bloque f - Fila 8)
    "La": (8, 2), "Ce": (8, 3), "Pr": (8, 4), "Nd": (8, 5), "Pm": (8, 6), "Sm": (8, 7), "Eu": (8, 8), "Gd": (8, 9),
    "Tb": (8, 10), "Dy": (8, 11), "Ho": (8, 12), "Er": (8, 13), "Tm": (8, 14), "Yb": (8, 15), "Lu": (8, 16),
    # Actínidos (Bloque f - Fila 9)
    "Ac": (9, 2), "Th": (9, 3), "Pa": (9, 4), "U": (9, 5), "Np": (9, 6), "Pu": (9, 7), "Am": (9, 8), "Cm": (9, 9), 
    "Bk": (9, 10), "Cf": (9, 11), "Es": (9, 12), "Fm": (9, 13), "Md": (9, 14), "No": (9, 15), "Lr": (9, 16)
}


# Tablas de traducción para subíndices
SUB_TO_NORMAL = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
NORMAL_TO_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def cargar_elementos():
    """
    Carga los datos de los elementos desde el archivo CSV.
    Si falla o el entorno de ejecución no permite la lectura de archivos,
    retorna un DataFrame completo con datos dummy (seguro y robusto).
    """
    
    # 1. Definir rutas de intento (se simplifica la lógica de path)
    ruta_csv = os.path.join("data", "elementos_completo.csv")

    df_elementos = None
    try:
        # Intento de cargar el archivo, útil si se ejecuta en un entorno con acceso a archivos
        if os.path.exists(ruta_csv):
            df_elementos = pd.read_csv(ruta_csv)
    except Exception as e:
        # En caso de error de lectura, se continúa usando los datos dummy
        print(f"Advertencia: Falló la lectura del CSV o no se encontró ({e}). Usando datos de ejemplo.")
    
    # 2. Si no se cargó o está vacío, usar el DataFrame dummy (completo)
    if df_elementos is None or df_elementos.empty:
        # Se asegura que este DataFrame contenga TODOS los elementos y las columnas necesarias.
        datos_dummy = {
            "Simbolo": ["H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"],
            "Nombre": ["Hidrógeno", "Helio", "Litio", "Berilio", "Boro", "Carbono", "Nitrógeno", "Oxígeno", "Flúor", "Neón", "Sodio", "Magnesio", "Aluminio", "Silicio", "Fósforo", "Azufre", "Cloro", "Argón", "Potasio", "Calcio", "Escandio", "Titanio", "Vanadio", "Cromo", "Manganeso", "Hierro", "Cobalto", "Níquel", "Cobre", "Zinc", "Galio", "Germanio", "Arsénico", "Selenio", "Bromo", "Kriptón", "Rubidio", "Estroncio", "Itrio", "Circonio", "Niobio", "Molibdeno", "Tecnecio", "Rutenio", "Rodio", "Paladio", "Plata", "Cadmio", "Indio", "Estaño", "Antimonio", "Telurio", "Yodo", "Xenón", "Cesio", "Bario", "Lantano", "Cerio", "Praseodimio", "Neodimio", "Prometio", "Samario", "Europio", "Gadolinio", "Terbio", "Disprosio", "Holmio", "Erbio", "Tulio", "Iterbio", "Lutecio", "Hafnio", "Tantalio", "Wolframio", "Rhenio", "Osmio", "Iridio", "Platino", "Oro", "Mercurio", "Talio", "Plomo", "Bismuto", "Polonio", "Astato", "Radón", "Francio", "Radio", "Actinio", "Torio", "Protactinio", "Uranio", "Neptunio", "Plutonio", "Americio", "Curio", "Berkelio", "Californio", "Einstenio", "Fermio", "Mendelevio", "Nobelio", "Lawrencio", "Rutherfordio", "Dubnio", "Seaborgio", "Bohrium", "Hassio", "Meitnerio", "Darmstadtio", "Roentgenio", "Copernicio", "Nihonio", "Flerovio", "Moscovio", "Livermorio", "Tenesino", "Oganesón"],
            "NumeroAtomico": list(range(1, 119)),
            "MasaAtomica": [1.008, 4.0026, 6.94, 9.0122, 10.81, 12.011, 14.007, 15.999, 18.998, 20.18, 22.99, 24.305, 26.982, 28.085, 30.974, 32.06, 35.45, 39.948, 39.098, 40.078, 44.955, 47.867, 50.942, 51.996, 54.938, 55.845, 58.933, 58.693, 63.546, 65.38, 69.723, 72.63, 74.922, 78.971, 79.904, 83.798, 85.468, 87.62, 88.906, 91.224, 92.906, 95.95, 98.0, 101.07, 102.91, 106.42, 107.87, 112.41, 114.82, 118.71, 121.76, 127.60, 126.90, 131.29, 132.91, 137.33, 138.91, 140.12, 140.91, 144.24, 145.0, 150.36, 151.96, 157.25, 158.93, 162.50, 164.93, 167.26, 168.93, 173.05, 174.97, 178.49, 180.95, 183.84, 186.21, 190.23, 192.22, 195.08, 196.97, 200.59, 204.38, 207.2, 208.98, 209.0, 210.0, 222.0, 223.0, 226.0, 227.0, 232.04, 231.04, 238.03, 237.0, 244.0, 243.0, 247.0, 247.0, 251.0, 252.0, 257.0, 258.0, 259.0, 262.0, 267.0, 270.0, 271.0, 270.0, 277.0, 278.0, 281.0, 282.0, 285.0, 286.0, 289.0, 290.0, 293.0, 294.0, 294.0],
            "Electronegatividad": [2.20, 0.0, 0.98, 1.57, 2.04, 2.55, 3.04, 3.44, 3.98, 0.0, 0.93, 1.31, 1.61, 1.90, 2.19, 2.58, 3.16, 0.0, 0.82, 1.00, 1.36, 1.54, 1.63, 1.66, 1.55, 1.83, 1.88, 1.91, 1.90, 1.65, 1.81, 2.01, 2.18, 2.55, 2.96, 0.0, 0.82, 0.95, 1.22, 1.33, 1.6, 2.16, 1.9, 2.2, 2.28, 2.20, 1.93, 1.69, 1.78, 1.96, 2.05, 2.1, 2.66, 0.0, 0.79, 0.89, 1.10, 1.12, 1.13, 1.14, 1.13, 1.17, 1.20, 1.20, 1.20, 1.22, 1.23, 1.24, 1.25, 1.10, 1.27, 1.3, 1.5, 2.36, 1.9, 2.2, 2.20, 2.28, 2.54, 2.00, 1.62, 2.33, 2.02, 2.0, 2.2, 0.0, 0.7, 0.9, 1.1, 1.3, 1.5, 1.38, 1.36, 1.28, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3],
            "Estado": ["Gas", "Gas", "Sólido", "Sólido", "Sólido", "Sólido", "Gas", "Gas", "Gas", "Gas", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Gas", "Gas", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Líquido", "Gas", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Gas", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Líquido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Gas", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Sólido", "Gas"],
            "TipoElemento": ["No Metal", "Gas Noble", "Metal Alcalino", "Metal Alcalinotérreo", "Metaloide", "No Metal", "No Metal", "No Metal", "No Metal", "Gas Noble", "Metal Alcalino", "Metal Alcalinotérreo", "Metal del Bloque p", "Metaloide", "No Metal", "No Metal", "No Metal", "Gas Noble", "Metal Alcalino", "Metal Alcalinotérreo", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal del Bloque p", "Metaloide", "Metaloide", "No Metal", "No Metal", "Gas Noble", "Metal Alcalino", "Metal Alcalinotérreo", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal del Bloque p", "Metal del Bloque p", "Metaloide", "Metaloide", "No Metal", "Gas Noble", "Metal Alcalino", "Metal Alcalinotérreo", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Lantánido", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal del Bloque p", "Metal del Bloque p", "Metal del Bloque p", "Metaloide", "No Metal", "Gas Noble", "Metal Alcalino", "Metal Alcalinotérreo", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Actínido", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal de Transición", "Metal del Bloque p", "Metal del Bloque p", "Metal del Bloque p", "Metal del Bloque p", "No Metal", "Gas Noble"]
        }
        df_elementos = pd.DataFrame(datos_dummy).sort_values(by='NumeroAtomico').reset_index(drop=True)
    
    return df_elementos

# Resto de funciones

def minimizar_coeficientes(coeficientes):
    """
    Minimiza los coeficientes de una lista de fracciones/enteros a la 
    relación de enteros más pequeña. Esto es útil para el balanceo de reacciones.
    """
    if not coeficientes:
        return []

    # 1. Convertir a fracciones (asegura que todos los coeficientes tengan numerador/denominador)
    # Se añade manejo de casos donde el input podría ser un string (aunque la lógica asume numéricos)
    fracciones = [Fraction(c) if isinstance(c, (int, float, str)) and str(c).replace('.', '', 1).isdigit() else Fraction(0) for c in coeficientes]
    
    # Si todos los coeficientes son cero, la forma mínima sigue siendo [0, 0, ...]
    if all(f.numerator == 0 for f in fracciones):
        return [0] * len(coeficientes)
    
    # 2. Encontrar el denominador común mínimo (MCM de los denominadores)
    denominadores = [f.denominator for f in fracciones if f.denominator != 0]
    if not denominadores:
         # Esto sólo ocurriría si todos son enteros (denominador 1) o la lista está vacía
        minimo_denominador = 1
    else:
        # Función para calcular el Mínimo Común Múltiplo (MCM) de dos números
        def mcm(a, b):
            # Asumiendo que a y b son positivos (denominadores de Fraction)
            return abs(a*b) // gcd(a, b)

        # Calcular el MCM de todos los denominadores
        minimo_denominador = reduce(mcm, denominadores)
            
    # 3. Multiplicar todas las fracciones por el MCM para obtener enteros (numeradores)
    enteros_numerador = [(f * minimo_denominador).numerator for f in fracciones]
    
    # 4. Encontrar el Máximo Común Divisor (MCD) de los numeradores enteros no-cero
    numeradores_no_cero = [abs(n) for n in enteros_numerador if n != 0]
    
    if not numeradores_no_cero:
        # Caso de todos ceros, manejado arriba, pero por si acaso.
        return [0] * len(coeficientes)
        
    def calcular_mcd(a, b):
        return gcd(a, b)

    mcd_total = reduce(calcular_mcd, numeradores_no_cero)
    
    # 5. Dividir todos los enteros por el MCD para obtener la forma mínima
    # mcd_total es garantizado no-cero aquí
    coeficientes_minimos = [n // mcd_total for n in enteros_numerador]
    
    # 6. Retorna la lista de enteros
    return coeficientes_minimos