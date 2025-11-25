import customtkinter as ctk

#Gente, si tienen mejores iconos simplemente los cambian

class VentanaNovedades(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#000000", **kwargs)
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.configure(fg_color="#000000") 
        self.frame_card = ctk.CTkFrame(
            self, 
            fg_color="#212121",       
            corner_radius=20,         
            border_width=2,
            border_color="#333333",
            width=500,              
            height=600               
        )
  
        self.frame_card.place(relx=0.5, rely=0.5, anchor="center")
        
  
        self.frame_card.pack_propagate(False)
        
        # TÍTULO
        self.lbl_titulo = ctk.CTkLabel(
            self.frame_card, 
            text="🚀 Novedades 1.0.0-alpha", 
            font=("Roboto", 26, "bold"),
            text_color="white"
        )
        self.lbl_titulo.pack(pady=(30, 10))
        
        # SUBTÍTULO
        self.lbl_sub = ctk.CTkLabel(
            self.frame_card,
            text="¡Bienvenido a la Alpha! Prueba nuestros inicios:",
            font=("Roboto", 14),
            text_color="#B0BEC5"
        )
        self.lbl_sub.pack(pady=(0, 20))

        # ÁREA DE TEXTO
        self.textbox = ctk.CTkTextbox(
            self.frame_card,
            corner_radius=15,
            fg_color="#121212",
            text_color="#E0E0E0",
            font=("Consolas", 13),
            border_spacing=15
        )
        self.textbox.pack(fill="both", expand=True, padx=30, pady=10)
        
        log_text = """
• 🎨 INTERFAZ INICIAL
  - Diseño estilo "App Web".
  - Tabla Periódica interactiva.
 

• ⚡ ESTABILIDAD
  - Carga fluida entre elementos.


• 🧪 FUNCIONES QUÍMICAS
  - Balanceo.
  - Colores por familia.
  - Estructura de lewis 2d y 3d.
        """
        self.textbox.insert("0.0", log_text)
        self.textbox.configure(state="disabled")

        # BOTÓN CERRAR
        self.btn_ok = ctk.CTkButton(
            self.frame_card,
            text="¡Entendido!",
            font=("Roboto", 14, "bold"),
            fg_color="#00C853",
            hover_color="#00E676",
            text_color="white",
            height=50,
            corner_radius=25,
            command=self.cerrar_overlay
        )
        self.btn_ok.pack(pady=30, padx=40, fill="x")

        # Animación de entrada simple (esto es opcional)
        self.frame_card.configure(width=0, height=0) 
        self.after(10, lambda: self.frame_card.configure(width=500, height=600)) 

    def cerrar_overlay(self):
        self.destroy()