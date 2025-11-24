import customtkinter as ctk
from modules.utils import cargar_elementos, COLORES_GRUPOS, POSICIONES

class TablaPeriodica(ctk.CTkFrame):
    """
    Versión Estabilizada: Efecto 'Pop-Up' visual sin romper la cuadrícula.
    """
    def __init__(self, master, click_callback=None, hover_callback=None):
        super().__init__(master, fg_color="transparent") 
        
        self.elementos_df = cargar_elementos()
        self.click_callback = click_callback
        self.hover_callback = hover_callback
        
        # Fuentes (Mantenemos el tamaño similar para evitar temblequeo)
        self.fuente_normal = ("Arial", 9, "bold")
        self.fuente_zoom = ("Arial", 11, "bold") 

        self.boton_fantasma = None# Solo un pelín más grande
        
        self.crear_widgets()
        
    def crear_widgets(self):
        # 1. Configuración del grid
        num_cols = 18 
        num_rows = 10 
        for i in range(num_cols):
            self.grid_columnconfigure(i, weight=1, minsize=0)
        for i in range(num_rows):
            self.grid_rowconfigure(i, weight=1, minsize=0)

        # 2. Crear botones
        for index, row in self.elementos_df.iterrows():
            simbolo = row['Simbolo']
            
            if simbolo in POSICIONES:
                fila, columna = POSICIONES[simbolo]
                tipo_elemento = row['TipoElemento']
                color_fondo = COLORES_GRUPOS.get(tipo_elemento, "#CFD8DC")
                
                # Lógica de color de texto original
                color_texto = "white" if tipo_elemento in ["Gas Noble", "Lantanido", "Actinido", "Alcalino"] else "#1A1A1A"
                
                texto_boton = f"{row['NumeroAtomico']}\n{simbolo}"
                
                # --- CREACIÓN DEL BOTÓN ---
                btn = ctk.CTkButton(
                    master=self,
                    text=texto_boton,
                    fg_color=color_fondo,
                    text_color=color_texto,
                    font=self.fuente_normal,
                    
                    corner_radius=2,
                    border_width=0,           # Color del borde al iluminarse
                    width=32, height=28,
                    hover_color=color_fondo,  # Color intermedio
                    
                    command=lambda s=simbolo: self.manejar_click(s)
                )

                # --- GUARDAMOS LOS ESTADOS ORIGINALES EN EL PR
                
                # --- EVENTOS ---
                # Usamos la técnica correcta para pasar los argumentos lambda
                btn.bind("<Enter>", lambda e, s=simbolo, b=btn, bg=color_fondo, fg=color_texto: 
                         self.crear_fantasma(b, s, bg, fg))
                
                btn.grid(row=fila, column=columna, sticky="nsew", padx=1, pady=1)

                if simbolo == "La": self.crear_etiqueta_rango(fila, 0, "57-71", "#AB47BC")
                elif simbolo == "Ac": self.crear_etiqueta_rango(fila, 0, "89-103", "#EC407A")
                
        # Etiquetas de huecos
        lbl_la = ctk.CTkLabel(self, text="57-71", fg_color="#E0E0E0", text_color="gray", corner_radius=2, font=self.fuente_normal)
        lbl_la.grid(row=5, column=2, sticky="nsew", padx=1, pady=1)
        lbl_ac = ctk.CTkLabel(self, text="89-103", fg_color="#E0E0E0", text_color="gray", corner_radius=2, font=self.fuente_normal)
        lbl_ac.grid(row=6, column=2, sticky="nsew", padx=1, pady=1)

    def crear_etiqueta_rango(self, row, column, text, color):
        lbl = ctk.CTkLabel(master=self, text=text, fg_color=color, text_color="white", font=self.fuente_normal, corner_radius=2)
        lbl.grid(row=row, column=column, sticky="nsew", padx=1, pady=1, columnspan=2)

    # --- LÓGICA DE ANIMACIÓN ESTABILIZADA ---

    def crear_fantasma(self, btn_origen, simbolo, bg_color, fg_color):
        """Crea una copia temporal más grande encima del botón original"""
        
        # 1. Limpieza preventiva
        self.destruir_fantasma()
        
        # 2. Notificar Hover (Mostrar datos en panel lateral)
        if self.hover_callback:
            try:
                info = self.elementos_df[self.elementos_df['Simbolo'] == simbolo].iloc[0]
                self.hover_callback(info)
            except: pass

        # 3. Calcular geometría expandida
        pad = 6 # Cuánto crece en píxeles
        try:
            x_pos = btn_origen.winfo_x() - (pad // 2)
            y_pos = btn_origen.winfo_y() - (pad // 2)
            ancho_nuevo = btn_origen.winfo_width() + pad
            alto_nuevo = btn_origen.winfo_height() + pad
        except:
            return # Si la ventana no está lista, abortar

        # 4. Crear el botón flotante
        self.boton_fantasma = ctk.CTkButton(
            master=self,
            text=btn_origen.cget("text"),
            fg_color=bg_color,
            hover_color=bg_color,
            text_color=fg_color,
            font=self.fuente_zoom, # FUENTE GRANDE
            
            corner_radius=4,
            border_width=2,
            border_color="grey", # Borde blanco brillante
            
            width=ancho_nuevo,
            height=alto_nuevo,
            
            # Si hacen click en el fantasma, funciona igual que el original
            command=lambda s=simbolo: self.manejar_click(s)
        )
        
        # 5. Colocar flotando (PLACE ignora el grid)
        self.boton_fantasma.place(x=x_pos, y=y_pos)
        
        # 6. Si el mouse sale del fantasma, se destruye
        self.boton_fantasma.bind("<Leave>", lambda e: self.destruir_fantasma())

    def destruir_fantasma(self):
        """Elimina el botón flotante"""
        if self.boton_fantasma:
            try:
                self.boton_fantasma.destroy()
            except: pass
            self.boton_fantasma = None

    # --- MANEJADOR DE CLICK (Esencial para que funcione) ---

    def manejar_click(self, simbolo):
        if self.click_callback:
            info = self.elementos_df[self.elementos_df['Simbolo'] == simbolo].iloc[0]
            self.click_callback(info)