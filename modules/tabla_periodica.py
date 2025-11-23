
import customtkinter as ctk
from modules.utils import cargar_elementos, COLORES_GRUPOS, POSICIONES

class TablaPeriodica(ctk.CTkFrame):
    """
    Versión Modernizada de la Tabla Periódica usando CustomTkinter.
    """
    def __init__(self, master, elemento_callback=None):
        # fg_color="transparent" hace que se mezcle con el fondo de la ventana principal
        super().__init__(master, fg_color="transparent") 
        
        self.elementos_df = cargar_elementos()
        self.elemento_callback = elemento_callback
        
        self.crear_widgets()
        
    def crear_widgets(self):
        # 1. Configurar la expansión del grid
        num_cols = 18 
        num_rows = 10 

        # Configuración de columnas
        for i in range(num_cols):
            self.grid_columnconfigure(i, weight=1, minsize=0) # Un poco más ancho para estética
            
        # Configuración de filas
        for i in range(num_rows):
            if i in [7, 8, 9]: # Filas de separación y tierras raras
                 self.grid_rowconfigure(i, weight=1, minsize=0)
            else:
                 self.grid_rowconfigure(i, weight=1, minsize=0)

        # 2. Crear y colocar botones
        for index, row in self.elementos_df.iterrows():
            simbolo = row['Simbolo']
            
            if simbolo in POSICIONES:
                fila, columna = POSICIONES[simbolo]
                
                tipo_elemento = row['TipoElemento']
                color_fondo = COLORES_GRUPOS.get(tipo_elemento, "#CFD8DC")
                
                # Lógica de Contraste: Texto blanco para fondos oscuros, negro para claros
                color_texto = "white" if tipo_elemento in ["Gas Noble", "Lantanido", "Actinido", "Alcalino"] else "#1A1A1A"
                
                # Texto del botón
                texto_boton = f"{row['NumeroAtomico']}\n{simbolo}"
                
                # --- EL CAMBIO VISUAL PRINCIPAL ---
                btn = ctk.CTkButton(
                    master=self,
                    text=texto_boton,
                    fg_color=color_fondo,        # Color del grupo
                    text_color=color_texto,      # Color de letra dinámico
                    font=("Arial", 9, "bold"), # Fuente más limpia
                    
                    # Estilo Moderno
                    corner_radius=2,
                    width=32,
                    height=28,             # Bordes sutilmente redondeados (No muy redondos para grid)
                    border_width=0,              # Sin bordes negros duros
                    hover_color="#546E7A",       # Color al pasar el mouse (Gris azulado)
                    
                    # Callbacks
                    command=lambda s=simbolo: self.manejar_click_elemento(s)
                )
                
                # padx=2, pady=2 crea el espacio blanco entre las celdas
                btn.grid(row=fila, column=columna, sticky="nsew", padx=1, pady=1)

                # Etiquetas especiales (La, Ac) dentro de la tabla principal
                if simbolo == "La":
                    self.crear_etiqueta_rango(fila, 0, "57-71", "#AB47BC") # Color Lantanido
                elif simbolo == "Ac":
                    self.crear_etiqueta_rango(fila, 0, "89-103", "#EC407A") # Color Actinido
                
        # 3. Etiquetas de referencia en el cuerpo (Donde irían La y Ac)
        # Usamos CTkLabel con corner_radius para que parezcan "huecos" vacíos
        lbl_la = ctk.CTkLabel(self, text="57-71", fg_color="#E0E0E0", text_color="gray", corner_radius=2)
        lbl_la.configure(font=("Arial", 9, "bold"))
        lbl_la.grid(row=5, column=2, sticky="nsew", padx=1, pady=1)
        
        lbl_ac = ctk.CTkLabel(self, text="89-103", fg_color="#E0E0E0", text_color="gray", corner_radius=2)
        lbl_ac.configure(font=("Arial", 9, "bold"))
        lbl_ac.grid(row=6, column=2, sticky="nsew", padx=1, pady=1)

    def crear_etiqueta_rango(self, row, column, text, color):
        """Etiquetas laterales pequeñas"""
        # Hacemos que coincidan con el estilo de los botones pero sin ser clickeables
        lbl = ctk.CTkLabel(
            master=self, 
            text=text, 
            fg_color=color, 
            text_color="white", 
            font=("Arial", 10, "bold"),
            corner_radius=6
        )
        lbl.grid(row=row, column=column, sticky="nsew", padx=2, pady=2, columnspan=2)

    def manejar_click_elemento(self, simbolo):
        """Maneja el evento de click (Igual que antes)"""
        if self.elemento_callback:
            # Filtramos el dataframe (asegúrate que devuelve un Series o Dict válido)
            elemento_info = self.elementos_df[self.elementos_df['Simbolo'] == simbolo].iloc[0]
            self.elemento_callback(elemento_info)

# No incluimos la clase ElementoBoton ya que simplificamos la lógica en TablaPeriodica