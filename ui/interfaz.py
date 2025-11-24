import tkinter as tk
from tkinter import scrolledtext, messagebox
import pandas as pd
import customtkinter as ctk
import re # Necesario para buscar números al inicio de la cadena

# Importaciones absolutas.
from modules.tabla_periodica import TablaPeriodica 
from modules.parser import parsear_ecuacion
from modules.balanceo import BalanceadorEcuacion
# Asumo que estas constantes y función existen en modules/utils.py
from modules.utils import NORMAL_TO_SUB, cargar_elementos, SUB_TO_NORMAL 

class Interfaz(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Balanceador de Ecuaciones Químicas (por Mínimos Cuadrados)")
        self.geometry("1100x800")
        self.state('zoomed')
        
        # Cargar datos para el tooltip
        self.df_elementos = cargar_elementos()
        
        self.crear_layout()

    def crear_layout(self):
        """Configura el layout principal usando grid."""
        
        # Configuración principal del grid (reorganizada para evitar solapamientos)
        # Filas: 0 = tabla periódica (grande), 1 = entrada (fija), 2 = resultado, 3 = lewis (grande al final)
        self.grid_rowconfigure(0, weight=0, minsize=210)
        self.grid_rowconfigure(1, weight=0, minsize=160)
        self.grid_rowconfigure(2, weight=1, minsize=300)
        self.grid_columnconfigure(0, weight=1)

        # --- Frame Principal de la Tabla (Fila 0) ---
        self.frame_top = tk.Frame(self, bg='#CFD8DC')
        self.frame_top.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5,1))

        self.frame_middle = tk.Frame(self) # Frame invisible contenedor
        self.frame_middle.grid(row=1, column=0, sticky="nsew", padx=5, pady=1)
        self.frame_middle.grid_columnconfigure(0, weight=3) 
        self.frame_middle.grid_columnconfigure(1, weight=2)
        self.frame_middle.grid_rowconfigure(0, weight=1)
        
        # Dentro de frame_top la columna 0 es el panel de info y la 1 la tabla (expandible)
        self.frame_top.grid_columnconfigure(0, weight=0, minsize=160) # panel información ancho fijo
        self.frame_top.grid_columnconfigure(1, weight=1) # tabla ocupa el resto
        self.frame_top.grid_rowconfigure(0, weight=1) 
        
        # Tooltip para info de elemento (Columna 0)
        self.frame_info = tk.Label(self.frame_top, text="Clic en un elemento\npara ver detalles.", 
                                 bg='#EFEFEF', bd=1, relief=tk.SOLID, justify=tk.LEFT,
                                 font=('Helvetica', 10), anchor='nw', width=28, height=8, 
                                 padx=8, pady=8)
        self.frame_info.grid(row=0, column=0, sticky="nsw", padx=10, pady=10)

        # --- Tabla Periódica --- (Columna 1)
        self.tabla_periodica = TablaPeriodica(self.frame_top, click_callback=self.evento_click_elemento, hover_callback=self.actualizar_panel_info)
        self.tabla_periodica.grid(row=0, column=1, sticky="nsew", padx=6, pady=6) 

        # --- Frame de Entrada de Ecuación (Fila 1) CustomTKinter---
        self.frame_input = ctk.CTkFrame(
            master=self.frame_middle,
            fg_color='#B0BEC5',    # Reemplaza a 'bg'. Es el color de fondo del frame.
            corner_radius=20,      # <--- ¡LA MAGIA! Bordes redondeados. # Opcional: color del borde un poco más oscuro.
            )

# La colocación (grid) funciona casi igual, pero se ve mejor
        self.frame_input.grid(
            row=0, 
            column=0, 
            sticky="nsew", # "ew" hace que se estire de Este a Oeste (ancho completo)
            padx=(0, 5),     # Margen externo (separación de los bordes de la ventana)
            pady=0      # Margen vertical
            )

# Esto se mantiene igual (es para centrar o expandir elementos dentro)
        self.frame_input.grid_columnconfigure(0, weight=1)
        
        lbl_EcuacionQ=ctk.CTkLabel(
            master=self.frame_input,
            corner_radius=20,
            text="Ecuación Química",
            text_color="#000000",
            font=("Roboto Bold",24)
        )
        lbl_EcuacionQ.grid(row=0, column=0, columnspan=10, pady=2)

# Recuerden gente, todo eso de arriba solo con Custom TKinter --Sgt.Aldea---

        # Campo de entrada de la ecuación
        self.ecuacion_var = tk.StringVar(value="") 
        self.entry_ecuacion = tk.Entry(self.frame_input, textvariable=self.ecuacion_var, font=('Helvetica', 12), width=35, bd=2, relief=tk.SUNKEN)
        self.entry_ecuacion.grid(row=1, column=0, columnspan=10, padx=5, pady=5, sticky="ew")
        
        # Frame para el constructor de la ecuación
        self.frame_constructor = tk.Frame(self.frame_input, bg='#B0BEC5')
        self.frame_constructor.grid(row=2, column=0, columnspan=10, pady=5, sticky="ew")
        self.frame_constructor.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        lbl_mol = tk.Label(self.frame_constructor, text="Molécula:", font=('Helvetica', 11), bg='#B0BEC5')
        lbl_mol.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.molecula_var = tk.StringVar(value="") 
        self.molecula_var.trace_add('write', self.convertir_a_subindices)
        self.entry_molecula = tk.Entry(self.frame_constructor, textvariable=self.molecula_var, font=('Helvetica', 11), width=12, bd=1)
        self.entry_molecula.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- AÑADIR RASTREO (TRACE) AL CAMPO DE LA MOLÉCULA ---
        self.molecula_var.trace_add('write', self.convertir_a_subindices)
        
        # --- BOTONES DE OPERACIÓN | Los cambie de Tkinter a CustomTkinter --Sgt.Aldea---
        btn_agregar = ctk.CTkButton(
            master=self.frame_constructor, text="Agregar (+)",
            fg_color="#1E88E5", hover_color="#1565C0",
            corner_radius=15, height=30, width=100, # Un poco más compactos
            command=self.agregar_molecula
        )
        btn_agregar.grid(row=0, column=2, padx=5, pady=5)

        btn_flecha = ctk.CTkButton(
            master=self.frame_constructor, text="Flecha (→)",
            fg_color="#FFC107", hover_color="#C09000",
            corner_radius=15, height=30, width=100,
            command=self.agregar_flecha
        )
        btn_flecha.grid(row=0, column=3, padx=5, pady=5)

        btn_limpiar = ctk.CTkButton(
            master=self.frame_constructor, text="Limpiar",
            fg_color="#E34234", hover_color="#BE3A2E",
            corner_radius=15, height=32, width=110,
            command=self.limpiar_ecuacion
        )
        btn_limpiar.grid(row=1, column=1, padx=5, pady=(2,5))
        
        btn_balancear = ctk.CTkButton(
            master=self.frame_constructor, text="Balancear",
            fg_color="#00A86B", hover_color="#027E50",
            corner_radius=15, height=32, width=110, font=("Roboto", 13, "bold"),
            command=self.balancear_ecuacion
        )
        btn_balancear.grid(row=1, column=2, padx=5, pady=(2,5))
        btn_lewis = ctk.CTkButton(
            master=self.frame_constructor, text="Ver Lewis", # Texto más corto
            fg_color="#9C27B0", hover_color="#751E85",
            corner_radius=15, height=32, width=110,
            command=self.mostrar_lewis_actual
        )
        btn_lewis.grid(row=1, column=3, padx=5, pady=(2,5))

        # --- Frame de Resultado (Fila 2) ---
        self.frame_bottom = tk.Frame(self.frame_middle, bg='#ECEFF1', padx=10, pady=10)
        self.frame_bottom.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        self.frame_bottom.grid_columnconfigure(0, weight=1)
        self.frame_bottom.grid_rowconfigure(1, weight=1)

        tk.Label(self.frame_bottom, text="Procedimiento y Resultado", font=('Helvetica', 14, 'bold'), bg='#ECEFF1').grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.output_text = scrolledtext.ScrolledText(self.frame_bottom, wrap=tk.WORD, height=6, font=('Consolas', 11), bd=2, relief=tk.SUNKEN)
        self.output_text.grid(row=1, column=0, sticky="nsew")

        # --- NUEVO FRAME PARA ESTRUCTURA DE LEWIS (Fila 3, al final) ---
        self.frame_lewis = tk.Frame(self, bg='#DDE3E8', padx=5, pady=5)
        self.frame_lewis.grid(row=2, column=0, sticky="nsew", padx=5, pady=(1,5))

        # Configuración de columnas y filas internas (más espacio para 3D)
        self.frame_lewis.grid_columnconfigure(0, weight=1)
        self.frame_lewis.grid_columnconfigure(1, weight=2)
        self.frame_lewis.grid_rowconfigure(0, weight=0, minsize=30) 
        # Fila 1: Contenido (peso 1 = ocupa todo el resto del espacio)
        self.frame_lewis.grid_rowconfigure(1, weight=1)

        # --- Título del panel de Lewis ---
        self.label_lewis_title = tk.Label(
            self.frame_lewis,
            text="Estructura de Lewis (2D) y Modelo (3D)",
            font=('Helvetica', 12, 'bold'),
            bg='#DDE3E8'
        )
        self.label_lewis_title.grid(row=0, column=0, columnspan=2, pady=(2,5), sticky="n")

        # --- Canvas 2D de Lewis (expandible) ---
        self.canvas_2d = tk.Canvas(
            self.frame_lewis,
            bg="white",
            highlightthickness=1,
            highlightbackground="#AAAAAA"
        )
        self.canvas_2d.grid(row=1, column=0, sticky="nsew", padx=5, pady=0)

        # --- Frame donde irá el modelo 3D (VTK) ---
        self.frame_3d = tk.Frame(self.frame_lewis, bg="black")
        self.frame_3d.grid(row=1, column=1, sticky="nsew", padx=2, pady=0)

    # --- Generador simple de geometría a partir de fórmula (heurístico) ---
    def formula_a_atoms_bonds(self, formula_norm):
        """
        Entrada: formula_norm tipo 'H2O' (sin subíndices unicode).
        Salida:
          atoms_2d: [{'elem': 'O', 'x':..., 'y':...}, ...]
          atoms_3d: [{'elem':'O', 'pos':(x,y,z)}, ...]
          bonds: [(i,j,order), ...]
        Este generador es heurístico y funciona bien para moléculas sencillas.
        """
        import re, math
        tokens = re.findall(r'([A-Z][a-z]?)(\d*)', formula_norm)
        atoms = []
        for sym, num in tokens:
            n = int(num) if num else 1
            for _ in range(n):
                atoms.append(sym.capitalize())
        if 'C' in atoms:
            central_idx = atoms.index('C')
        else:
            non_h = [i for i,a in enumerate(atoms) if a != 'H']
            central_idx = non_h[0] if non_h else 0

        bonds = []
        for i in range(len(atoms)):
            if i == central_idx:
                continue
            bonds.append((central_idx, i, 1))

        atoms_2d = []
        radius = 120
        cx, cy = 200, 150
        n_subs = len(atoms) - 1
        for i, elem in enumerate(atoms):
            if i == central_idx:
                atoms_2d.append({'elem': elem, 'x': cx, 'y': cy})
            else:
                idx = i if i < central_idx else i-1
                theta = 2*math.pi * (idx / max(1, n_subs))
                x = cx + radius * math.cos(theta)
                y = cy + radius * math.sin(theta)
                atoms_2d.append({'elem': elem, 'x': x, 'y': y})

        atoms_3d = []
        for i, elem in enumerate(atoms):
            if i == central_idx:
                atoms_3d.append({'elem': elem, 'pos': (0.0, 0.0, 0.0)})
            else:
                angle = 2*math.pi*(i / max(1, len(atoms)))
                r = 1.2
                z = 0.0 if len(atoms) <= 3 else (0.2 * ( (i%2)*2 -1 ))
                atoms_3d.append({'elem': elem, 'pos': (r*math.cos(angle), r*math.sin(angle), z)})
        return atoms_2d, atoms_3d, bonds

    # --- Dibujar en Canvas 2D ---
    def dibujar_2d_en_canvas(self, atoms_2d, bonds):
        self.canvas_2d.delete("all")
        # Dibujar enlaces
        for i,j,order in bonds:
            a = atoms_2d[i]; b = atoms_2d[j]
            self.canvas_2d.create_line(a['x'], a['y'], b['x'], b['y'], width=2*order)
        # Dibujar átomos (círculos + texto)
        for a in atoms_2d:
            x = a['x']; y = a['y']
            r = 18
            self.canvas_2d.create_oval(x-r, y-r, x+r, y+r, fill="#F8F8F8", outline="black")
            self.canvas_2d.create_text(x, y+2, text=a['elem'], font=("Helvetica", 12, "bold"))

    # --- INICIALIZAR VTK EN self.frame_3d ---
    def init_vtk_3d(self):
        try:
            from vtkmodules.vtkRenderingCore import vtkRenderer
            from vtkmodules.vtkCommonTransforms import vtkTransform
            from vtkmodules.vtkFiltersSources import vtkSphereSource, vtkCylinderSource
            from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper
            from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
            from vtkmodules.tk.vtkTkRenderWindowInteractor import vtkTkRenderWindowInteractor
        except Exception as e:
            messagebox.showerror("VTK no disponible", f"Error importando VTK: {e}")
            return

        self.vtk_renderer = vtkRenderer()
        self.vtk_renderer.SetBackground(1.0, 1.0, 1.0)

        self.vtk_widget = vtkTkRenderWindowInteractor(self.frame_3d, width=400, height=300)
        self.vtk_widget.pack(fill="both", expand=True)
        self.vtk_widget.GetRenderWindow().AddRenderer(self.vtk_renderer)

        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        style = vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

        self._vtk_actors = []
        

    # --- Limpiar escena VTK ---
    def clear_vtk_scene(self):
        for actor in getattr(self, "_vtk_actors", []):
            self.vtk_renderer.RemoveActor(actor)
        self._vtk_actors = []
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.GetRenderWindow().Render()

    # --- Render Ball-and-stick 3D con VTK ---
    def render_molecule_3d(self, atoms3d, bonds):
        from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper
        from vtkmodules.vtkFiltersSources import vtkSphereSource, vtkCylinderSource
        from vtkmodules.vtkCommonTransforms import vtkTransform
        import math
        import numpy as _np

        self.clear_vtk_scene()

        radius_map = {"H":0.2, "C":0.35, "O":0.33, "N":0.33, "S":0.4}
        color_map = {"H":(1,1,1), "C":(0.2,0.2,0.2), "O":(1,0,0), "N":(0,0,1), "S":(1,1,0)}

        for a in atoms3d:
            elem = a.get("elem","X"); pos = a.get("pos",(0,0,0))
            r = radius_map.get(elem, 0.3)
            sphere = vtkSphereSource()
            sphere.SetCenter(pos)
            sphere.SetRadius(r)
            sphere.SetThetaResolution(24); sphere.SetPhiResolution(24)
            sphere.Update()

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(color_map.get(elem, (0.5,0.5,0.5)))
            self.vtk_renderer.AddActor(actor)
            self._vtk_actors.append(actor)

        for i,j,order in bonds:
            p1 = _np.array(atoms3d[i]['pos']); p2 = _np.array(atoms3d[j]['pos'])
            v = p2 - p1
            length = _np.linalg.norm(v)
            if length == 0: continue
            center = tuple((p1 + p2) / 2.0)
            cyl = vtkCylinderSource()
            cyl.SetResolution(24)
            cyl.SetRadius(0.08 * order)
            cyl.SetHeight(length)
            cyl.Update()

            transform = vtkTransform()
            transform.Translate(center)
            v1 = _np.array([0.0, 1.0, 0.0])
            v2 = v / length
            axis = _np.cross(v1, v2)
            if _np.linalg.norm(axis) > 1e-6:
                angle = math.degrees(math.acos(max(-1.0, min(1.0, float(_np.dot(v1, v2))))))
                transform.RotateWXYZ(angle, axis[0], axis[1], axis[2])

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(cyl.GetOutputPort())
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.SetUserTransform(transform)
            actor.GetProperty().SetColor(0.7,0.7,0.7)

            self.vtk_renderer.AddActor(actor)
            self._vtk_actors.append(actor)

        self.vtk_widget.GetRenderWindow().Render()

    # --- Botón / función que conecta todo: obtiene la molécula del entry y dibuja ---
    def mostrar_lewis_actual(self):
        mol_unicode = self.molecula_var.get().strip()
        mol_norm = mol_unicode.translate(SUB_TO_NORMAL)
        if not mol_norm:
            messagebox.showinfo("Info", "Escribe una molécula en el campo 'Molécula' (ej: H2O) y pulsa Mostrar Lewis.")
            return

        atoms_2d, atoms_3d, bonds = self.formula_a_atoms_bonds(mol_norm)
        self.dibujar_2d_en_canvas(atoms_2d, bonds)

        if not hasattr(self, 'vtk_widget'):
            self.init_vtk_3d()

        self.render_molecule_3d(atoms_3d, bonds)
        self.output_text.insert(tk.END, f"Mostrar Lewis: {mol_norm} | átomos: {len(atoms_2d)} | enlaces: {len(bonds)}\n")

    
    def convertir_a_subindices(self, *args):
        """
        Función de rastreo (trace) que se llama cada vez que cambia self.molecula_var.
        Busca números y aplica subíndices, pero protege los coeficientes al inicio.
        """
        current_value_unicode = self.molecula_var.get()
        
        # 1. Revertir cualquier subíndice Unicode a número normal para poder procesarlo
        current_value_normal = current_value_unicode.translate(SUB_TO_NORMAL)
        
        # 2. Intentar separar el Coeficiente (inicio) de la Molécula (resto)
        # ^(\d*) busca 0 o más dígitos al inicio (el coeficiente)
        match = re.match(r'^(\d*)(.*)$', current_value_normal)
        
        new_value_unicode = current_value_unicode # Inicializamos con el valor actual

        if match:
            coef = match.group(1) # Coeficiente (se mantiene normal)
            mol = match.group(2)  # Molécula (aquí aplicamos subíndices)
            
            # Convertir los dígitos de la molécula a subíndices
            mol_subscripted = mol.translate(NORMAL_TO_SUB)
            
            # Recomponer el valor: Coeficiente Normal + Molécula Subíndice
            new_value_unicode = coef + mol_subscripted
        else:
             # Caso de seguridad: si no hay un match claro, solo intenta convertir todo (como antes)
             new_value_unicode = current_value_normal.translate(NORMAL_TO_SUB) 

        # 3. Quitar el rastreador temporalmente para evitar un bucle infinito
        # Obtenemos el ID del rastreador actual para removerlo
        try:
             # Esto obtiene el ID del primer rastreador 'write'
             trace_id = self.molecula_var.trace_info()[0][1]
        except IndexError:
            # A veces trace_info está vacío al inicio, lo ignoramos y seguimos
            trace_id = None
            
        if trace_id:
            self.molecula_var.trace_remove('write', trace_id)
        
        # 4. Actualizar la variable si hay un cambio
        if new_value_unicode != current_value_unicode:
            self.molecula_var.set(new_value_unicode)
            
            # Mover el cursor al final
            self.entry_molecula.icursor(tk.END)

        # 5. Volver a añadir el rastreador
        if trace_id:
            self.molecula_var.trace_add('write', self.convertir_a_subindices)
        
    
    def actualizar_panel_info(self, elemento_info):
        """
        Actualiza el tooltip con la información detallada del elemento
        Y añade el SÍMBOLO al campo de la molécula, manteniendo la lógica de subíndices.
        """
        simbolo = elemento_info['Simbolo']
    
        nombre = elemento_info['Nombre']
        numero_atomico = elemento_info['NumeroAtomico']
        masa_atomica = elemento_info['MasaAtomica']
        tipo = elemento_info['TipoElemento']
        
        info = (
            f"{nombre} ({simbolo})\n"
            f"Z: {numero_atomico} | Masa: {masa_atomica}\n"
            f"Tipo: {tipo}"
        )
        self.frame_info.config(text=info)

    def evento_click_elemento(self, elemento_info):

        # 1. Actualizamos info
        self.actualizar_panel_info(elemento_info)

        # 2. Escribimos en el input
        simbolo = elemento_info['Simbolo']
        current_molecula = self.molecula_var.get()
        current_molecula_normal = current_molecula.translate(SUB_TO_NORMAL)
        new_normal = current_molecula_normal + simbolo
        
        # Usamos la lógica de conversión
        self.molecula_var.set(new_normal.translate(NORMAL_TO_SUB))
        self.entry_molecula.focus_set()


    def agregar_molecula(self):
        """
        Añade la molécula del entry al campo de la ecuación, seguida de un '+'.
        *** AQUÍ APLICAMOS SUBÍNDICES AL CAMPO DE LA ECUACIÓN ***
        """
        molecula_unicode = self.molecula_var.get().strip()
        
        # Para el motor de balanceo, necesitamos la versión NORMAL (ej. H2O)
        molecula_normal = molecula_unicode.translate(SUB_TO_NORMAL) 
        
        # Para mostrar al usuario, necesitamos el unicode (ej. H₂O)
        ecuacion_actual_unicode = self.ecuacion_var.get().strip()
        
        # Revertir la ecuación actual a normal para el proceso de construcción.
        # Esto es clave para trabajar con el string y luego formatear todo de una vez.
        ecuacion_actual_normal = ecuacion_actual_unicode.translate(SUB_TO_NORMAL)
        
        if molecula_normal:
            
            # --- CONSTRUYENDO LA NUEVA ECUACIÓN EN FORMATO NORMAL ---
            if not ecuacion_actual_normal or ecuacion_actual_normal.endswith('→'):
                nueva_ecuacion_normal = ecuacion_actual_normal + " " + molecula_normal
            elif ecuacion_actual_normal.endswith('+ '):
                # Esto maneja casos donde '→' fue agregado y había un '+' sobrante
                nueva_ecuacion_normal = ecuacion_actual_normal[:-2] + " + " + molecula_normal
            else:
                nueva_ecuacion_normal = ecuacion_actual_normal + " + " + molecula_normal
            
            # --- APLICAR SUBÍNDICES AL RESULTADO PARA MOSTRARLO ---
            # Usamos self.aplicar_subindices para formatear correctamente la ecuación completa
            ecuacion_a_mostrar = self.aplicar_subindices(nueva_ecuacion_normal.strip())
            
            # Actualizamos el Entry de la Ecuación con el formato Unicode
            self.ecuacion_var.set(ecuacion_a_mostrar)
            
            # Limpiamos el campo de la molécula para la siguiente entrada
            self.molecula_var.set("")
            
    def agregar_flecha(self):
        """
        Añade la flecha '→' al campo de la ecuación.
        *** Mantiene los subíndices en la parte existente. ***
        """
        ecuacion_actual_unicode = self.ecuacion_var.get().strip()
        
        if not ecuacion_actual_unicode.endswith('→'):
            # Revertir temporalmente a normal para la lógica de limpieza de '+'
            ecuacion_actual_normal = ecuacion_actual_unicode.translate(SUB_TO_NORMAL)
            
            if ecuacion_actual_normal.endswith('+'):
                 ecuacion_actual_normal = ecuacion_actual_normal[:-1]
            elif ecuacion_actual_normal.endswith('+ '):
                 ecuacion_actual_normal = ecuacion_actual_normal[:-2]
                 
            # Reaplicar subíndices y añadir la flecha
            parte_limpia_unicode = self.aplicar_subindices(ecuacion_actual_normal.strip())
            
            self.ecuacion_var.set(parte_limpia_unicode + " → ")
            self.molecula_var.set("")

    def limpiar_ecuacion(self):
        """Limpia el campo de la ecuación."""
        self.ecuacion_var.set("")
        self.molecula_var.set("") # Limpiar también el campo de molécula
        self.output_text.delete(1.0, tk.END)

    def balancear_ecuacion(self):
        """Llama al motor de balanceo y muestra el resultado."""
        # Para balancear, usamos el texto del Entry, pero lo convertimos a NORMAL
        ecuacion_unicode_str = self.ecuacion_var.get().strip()
        ecuacion_str = ecuacion_unicode_str.translate(SUB_TO_NORMAL)
        
        self.output_text.delete(1.0, tk.END)
        
        if not ecuacion_str or '→' not in ecuacion_str:
            messagebox.showerror("Error de Formato", "Por favor, introduce una ecuación química válida con reactivos, flecha (→) y productos.")
            return

        try:
            # 1. Parsear la ecuación
            reactivos_str, productos_str = [s.strip() for s in ecuacion_str.split('→')]
            # El parseo utiliza la versión NORMAL de la molécula
            reactivos = [parsear_ecuacion(s.strip()) for s in reactivos_str.split('+')]
            productos = [parsear_ecuacion(s.strip()) for s in productos_str.split('+')]

            # 2. Inicializar el balanceador
            balanceador = BalanceadorEcuacion(reactivos, productos)
            
            # 3. Mostrar el procedimiento inicial
            self.output_text.insert(tk.END, "1. Asignamos variables:\n")
            ecuacion_con_variables = balanceador.obtener_ecuacion_con_variables()
            # Muestra el procedimiento con subíndices
            self.output_text.insert(tk.END, self.aplicar_subindices(ecuacion_con_variables) + "\n\n")

            # 4. Obtener la matriz de coeficientes y los sistemas de ecuaciones
            matriz, elementos = balanceador.construir_matriz()
            
            self.output_text.insert(tk.END, "2. Ecuaciones por elemento:\n")
            for i, elem in enumerate(elementos):
                ecuacion = balanceador.obtener_ecuacion_texto(elem, matriz[i])
                self.output_text.insert(tk.END, f"  {elem}: {ecuacion}\n")
            self.output_text.insert(tk.END, "\n")
            
            # 5. Resolver el sistema y obtener los coeficientes
            coeficientes = balanceador.resolver()
            
            self.output_text.insert(tk.END, "3. Resolución del sistema:\n")
            if not coeficientes:
                self.output_text.insert(tk.END, "  Error: No se encontró solución entera simple o la ecuación es trivial/inválida.\n")
                return

            self.output_text.insert(tk.END, f"  Coeficientes fraccionarios/decimales: {coeficientes}\n")
            
            # 6. Minimizar y mostrar resultado final
            coeficientes_enteros = balanceador.minimizar_coeficientes(coeficientes)
            self.output_text.insert(tk.END, f"  Coeficientes enteros mínimos: {coeficientes_enteros}\n\n")

            ecuacion_balanceada = balanceador.formatear_ecuacion_balanceada(coeficientes_enteros)
            
            # 7. Formatear a subíndices para la presentación final
            ecuacion_sub = self.aplicar_subindices(ecuacion_balanceada)
            
            self.output_text.insert(tk.END, "4. Ecuación Balanceada:\n")
            self.output_text.insert(tk.END, f"  {ecuacion_sub}", ('balanceada',))
            
            # Estilo para el resultado final
            self.output_text.tag_config('balanceada', font=('Consolas', 12, 'bold'), foreground="#0D47A1")

        except ValueError as e:
            messagebox.showerror("Error de Parseo", str(e))
        except Exception as e:
            messagebox.showerror("Error Desconocido", f"Ocurrió un error inesperado durante el balanceo: {e}")

    def aplicar_subindices(self, texto):
        """
        Convierte los números de las moléculas a subíndices unicode, 
        pero mantiene los coeficientes (números al inicio) grandes.
        
        Nota: Esta función espera recibir el texto en formato NORMAL (sin subíndices).
        """
        partes = texto.split()
        resultado = []
        for parte in partes:
            
            if parte in ('+', '→'):
                resultado.append(parte)
                continue
            
            # 1. Separar coeficiente (si existe) y molécula
            match = re.match(r'^(\d*)(.*)$', parte)
            
            if match:
                coef = match.group(1) # Coeficiente, se mantiene normal
                mol = match.group(2)  # Molécula
                
                # 2. Aplicar subíndices solo a la parte de la molécula
                mol_subscripted = mol.translate(NORMAL_TO_SUB)
                
                # 3. Recomponer (Coeficiente normal + Molécula con subíndice)
                resultado.append(coef + mol_subscripted)
            else:
                 # Si no hay match (solo es un símbolo de elemento, por ejemplo), no hacemos nada
                 resultado.append(parte)
                 
        return " ".join(resultado)
        
# ----------------------------------------------------
# FUNCIÓN DE INICIO REQUERIDA POR ui/main.py
# ----------------------------------------------------
def iniciar_interfaz():
    """Función wrapper para iniciar la clase Interfaz."""
    app = Interfaz()
    app.mainloop()

if __name__ == '__main__':
    iniciar_interfaz()