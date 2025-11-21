import tkinter as tk
from modules.utils import cargar_elementos, COLORES_GRUPOS, POSICIONES

class TablaPeriodica(tk.Frame):
    """
    Representa la Tabla Periódica como una cuadrícula de botones para la interfaz.
    """
    def __init__(self, master, elemento_callback=None):
        super().__init__(master, bg='#ECEFF1', padx=10, pady=10) # Fondo claro
        
        self.elementos_df = cargar_elementos()
        self.elemento_callback = elemento_callback # Función a llamar al presionar un botón
        
        self.crear_widgets()
        
    def crear_widgets(self):
        """Crea y coloca los botones de los elementos en la cuadrícula."""
        
        # 1. Configurar la expansión del grid (CRUCIAL para que los elementos se vean)
        # Aseguramos que las columnas y filas tengan peso para expandirse
        num_cols = 18 # 18 columnas estándar de la tabla
        num_rows = 10 # 7 filas + 3 de espacio/lantánidos/actínidos

        for i in range(num_cols):
            self.grid_columnconfigure(i, weight=1, minsize=50) 
        for i in range(num_rows):
            # Las filas de separación (7) y las de los elementos (8 y 9) necesitan peso
            if i in [7, 8, 9]:
                 self.grid_rowconfigure(i, weight=1, minsize=50)
            else:
                 self.grid_rowconfigure(i, weight=1, minsize=45)

        # 2. Crear y colocar botones
        for index, row in self.elementos_df.iterrows():
            simbolo = row['Simbolo']
            
            # Asegura que el símbolo esté en la lista de posiciones
            if simbolo in POSICIONES:
                fila, columna = POSICIONES[simbolo]
                
                # Obtener el color basado en el tipo de elemento
                tipo_elemento = row['TipoElemento']
                color_fondo = COLORES_GRUPOS.get(tipo_elemento, "#E0E0E0")
                
                # Crear el texto del botón: Símbolo grande y número atómico pequeño
                texto_boton = f"{row['NumeroAtomico']}\n{simbolo}"
                
                # Crear el botón
                btn = tk.Button(self,
                    text=texto_boton,
                    bg=color_fondo,
                    fg="#000000",
                    activebackground=color_fondo,
                    activeforeground="#000000",
                    relief=tk.RAISED,
                    borderwidth=1,
                    highlightthickness=1,
                    wraplength=50,
                    font=('Helvetica', 10, 'bold'),
                    command=lambda s=simbolo: self.manejar_click_elemento(s)
                )
                
                # Colocar el botón usando las coordenadas de POSICIONES
                # sticky="nsew" es crucial: hace que el widget llene la celda del grid
                btn.grid(row=fila, column=columna, sticky="nsew", padx=1, pady=1)

                # Si el elemento es La, Act, o el espacio de transición, añadir etiquetas
                if simbolo == "La":
                    self.crear_etiqueta_rango(row=fila, column=0, text="57-71", color="#FF8A65")
                elif simbolo == "Ac":
                    self.crear_etiqueta_rango(row=fila, column=0, text="89-103", color="#A1887F")
                
        # 3. Etiquetas de Lanthanoides/Actinoides en el cuerpo principal
        # Etiqueta que indica dónde van los Lantánidos
        tk.Label(self, text="57-71", bg='#EFEFEF', fg="#FF8A65", font=('Helvetica', 9, 'bold')).grid(row=5, column=2, sticky="nsew", padx=1, pady=1)
        # Etiqueta que indica dónde van los Actínidos
        tk.Label(self, text="89-103", bg='#EFEFEF', fg="#A1887F", font=('Helvetica', 9, 'bold')).grid(row=6, column=2, sticky="nsew", padx=1, pady=1)

    def crear_etiqueta_rango(self, row, column, text, color):
        """Crea etiquetas para los bloques de Lantánidos y Actínidos en el pie de página."""
        tk.Label(self, text=text, bg=color, fg="#FFFFFF", font=('Helvetica', 8, 'bold')).grid(row=row, column=column, sticky="nsew", padx=1, pady=1, columnspan=2)


    def manejar_click_elemento(self, simbolo):
        """Maneja el evento de click en un botón de elemento."""
        if self.elemento_callback:
            elemento_info = self.elementos_df[self.elementos_df['Simbolo'] == simbolo].iloc[0]
            self.elemento_callback(elemento_info)

# No incluimos la clase ElementoBoton ya que simplificamos la lógica en TablaPeriodica