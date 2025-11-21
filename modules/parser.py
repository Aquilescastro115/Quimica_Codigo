import re

def parsear_ecuacion(molecula_str):
    """
    Parsea una molécula química (ej: 'H2SO4') y devuelve un diccionario de
    elementos y sus conteos (ej: {'H': 2, 'S': 1, 'O': 4}).
    Maneja corchetes para iones o grupos funcionales como (OH)2.
    """
    conteo_elementos = {}
    
    # 1. Quitar los corchetes exteriores (útil para iones como [Fe(CN)6]4-)
    molecula_str = molecula_str.replace('[', '(').replace(']', ')')
    
    # 2. Manejar grupos entre paréntesis (ej: (OH)2)
    while '(' in molecula_str:
        # Buscar la última aparición de un grupo entre paréntesis y su coeficiente
        match = re.search(r'\((.*?)\)(\d*)', molecula_str)
        if not match:
            # Esto no debería pasar si hay un '(' pero no se cierra correctamente
            raise ValueError(f"Error de formato en paréntesis de la molécula: {molecula_str}")
            
        grupo_interno = match.group(1)
        coef_grupo_str = match.group(2) if match.group(2) else '1'
        coef_grupo = int(coef_grupo_str)
        
        # Reemplazar el grupo por marcadores temporales de sus elementos
        temp_conteo = {}
        for elem, count in _parsear_molecula_simple(grupo_interno).items():
            temp_conteo[elem] = count * coef_grupo
            
        # Reemplazar el grupo original por el patrón que lo representa: {H:2}
        # Nota: Usamos un formato interno temporal para reinsertarlo en la cadena.
        # Esto simplifica la lógica de parseo al final.
        reemplazo = "".join([f"§{elem}§{count}" for elem, count in temp_conteo.items()])
        molecula_str = molecula_str.replace(match.group(0), reemplazo, 1)

    # 3. Parsear la cadena resultante (con elementos simples y marcadores)
    return _parsear_molecula_simple(molecula_str)


def _parsear_molecula_simple(molecula_str):
    """
    Parsea una molécula simple (sin paréntesis) o una con marcadores temporales.
    Ej: 'H2SO4' o 'Fe§C§6§N§6'
    """
    conteo_elementos = {}
    
    # Expresión regular:
    # ([A-Z][a-z]?) : Captura el símbolo del elemento (una mayúscula seguida opcionalmente de una minúscula)
    # | (§[A-Z][a-z]?§\d+) : Captura un marcador temporal de elemento (ej: §Fe§1)
    # (\d*) : Captura el subíndice (cero o más dígitos)
    patron = r'([A-Z][a-z]?|\§[A-Z][a-z]?§\d*)(\d*)'
    
    # Encontrar todos los matches en la cadena
    matches = re.findall(patron, molecula_str)
    
    if not matches and molecula_str.strip():
         # Si no hay matches, es un error de símbolo (ej: 'XyZ')
         raise ValueError(f"Símbolo o formato de molécula inválido: {molecula_str}")
        
    for simbolo_match, subindice_str in matches:
        if simbolo_match.startswith('§'):
            # Es un marcador temporal: Ej: §H§2
            
            # En el flujo de parsear_ecuacion, esto no debería ocurrir.
            # Pero por robustez, si ocurriera, asumimos que el marcador es {SÍMBOLO} {CONTEO}
            
            # Dividimos por '§' para obtener los componentes
            # Ejemplo: '§H§2§O§2' se divide en ['', 'H', '2', 'O', '2']
            partes_temp = simbolo_match.split('§')[1:]
            
            # Parseamos en pares (símbolo, conteo)
            for i in range(0, len(partes_temp), 2):
                elem_temp = partes_temp[i]
                count_temp = int(partes_temp[i+1])
                conteo_elementos[elem_temp] = conteo_elementos.get(elem_temp, 0) + count_temp
            
        else:
            # Es un elemento simple: Ej: 'H' o 'Fe'
            
            simbolo = simbolo_match
            # Si el subíndice está vacío (ej: 'H'), es 1. Sino, es el número.
            subindice = int(subindice_str) if subindice_str else 1
            
            conteo_elementos[simbolo] = conteo_elementos.get(simbolo, 0) + subindice
            
    return conteo_elementos

# Ejemplo: parsear_ecuacion("Fe(OH)3") -> {'Fe': 1, 'O': 3, 'H': 3}