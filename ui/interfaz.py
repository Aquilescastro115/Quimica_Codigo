# interfaz.py (archivo fusionado)
import tkinter as tk
from tkinter import scrolledtext, messagebox
import pandas as pd
import customtkinter as ctk
import re  # Necesario para buscar números al inicio de la cadena
import math
import numpy as _np

# Importaciones absolutas (mantenidas)
from modules.tabla_periodica import TablaPeriodica
from modules.parser import parsear_ecuacion
from modules.balanceo import BalanceadorEcuacion
# Asumo que estas constantes y funciones existen en modules/utils.py
from modules.utils import NORMAL_TO_SUB, cargar_elementos, SUB_TO_NORMAL
# Nuevo changelog/novedades (existía en la versión más nueva)
try:
    from ui.novedades import VentanaNovedades
except Exception:
    VentanaNovedades = None  # si no existe, lo ignoramos (compatibilidad)

class Interfaz(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Balanceador de Ecuaciones Químicas (por Mínimos Cuadrados)")
        self.geometry("1100x800")
        try:
            self.state('zoomed')
        except Exception:
            pass

        # Mostrar ventana de novedades si existe (no bloqueante)
        if VentanaNovedades is not None:
            # pequeño delay para que la ventana principal renderice
            self.after(600, lambda: VentanaNovedades(self))

        # Cargar datos para el tooltip (ambas versiones usan esto)
        self.df_elementos = cargar_elementos()

        # Inicializar layout y widgets
        self.crear_layout()

    def crear_layout(self):
        """Configura el layout principal usando grid."""
        # Configuración principal del grid
        self.grid_rowconfigure(0, weight=0, minsize=210)
        self.grid_rowconfigure(1, weight=0, minsize=160)
        # en la versión nueva minsize era 230 y en la vieja 300 -> elegimos un valor intermedio
        self.grid_rowconfigure(2, weight=1, minsize=260)
        self.grid_columnconfigure(0, weight=1)

        # --- Frame Principal de la Tabla (Fila 0) ---
        self.frame_top = tk.Frame(self, bg='#CFD8DC')
        self.frame_top.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 0))

        self.frame_middle = tk.Frame(self)  # Frame invisible contenedor
        self.frame_middle.grid(row=1, column=0, sticky="nsew", padx=5, pady=0)
        self.frame_middle.grid_columnconfigure(0, weight=3)
        self.frame_middle.grid_columnconfigure(1, weight=2)
        self.frame_middle.grid_rowconfigure(0, weight=1)

        # Dentro de frame_top la columna 0 es el panel de info y la 1 la tabla (expandible)
        self.frame_top.grid_columnconfigure(0, weight=0, minsize=160)  # panel información ancho fijo
        self.frame_top.grid_columnconfigure(1, weight=1)  # tabla ocupa el resto
        self.frame_top.grid_rowconfigure(0, weight=1)

        # --- TARJETA DE INFORMACIÓN (estilo nueva) usando CTkFrame si está disponible ---
        # La versión nueva tiene un CTkFrame estilizado; lo mantenemos si customtkinter está presente.
        try:
            self.frame_info = ctk.CTkFrame(
                self.frame_top,
                fg_color="#ECEFF1",
                corner_radius=15,
                border_width=2,
                border_color="#CFD8DC",
                width=220
            )
            self.frame_info.pack_propagate(False)
            self.frame_info.grid(row=0, column=0, sticky="nsew", padx=(5, 10), pady=5)

            self.lbl_simbolo_grande = ctk.CTkLabel(
                self.frame_info,
                text="?",
                font=("Roboto", 40, "bold"),
                text_color="#455A64"
            )
            self.lbl_simbolo_grande.pack(pady=(20, 5))

            self.lbl_nombre_elemento = ctk.CTkLabel(
                self.frame_info,
                text="Selecciona un elemento",
                font=("Roboto", 16, "bold"),
                text_color="#37474F"
            )
            self.lbl_nombre_elemento.pack(pady=(0, 10))

            self.lbl_detalles = ctk.CTkLabel(
                self.frame_info,
                text="Masa: --\nN° Atómico: --\nFamilia: --",
                font=("Roboto", 12),
                text_color="#546E7A",
                justify="center"
            )
            self.lbl_detalles.pack(pady=5)
        except Exception:
            # Fallback simple si customtkinter no funciona: etiqueta tk.Label
            self.frame_info = tk.Label(self.frame_top, text="Clic en un elemento\npara ver detalles.",
                                       bg='#EFEFEF', bd=1, relief=tk.SOLID, justify=tk.LEFT,
                                       font=('Helvetica', 10), anchor='nw', width=28, height=8,
                                       padx=8, pady=8)
            self.frame_info.grid(row=0, column=0, sticky="nsw", padx=10, pady=10)
            self.lbl_simbolo_grande = None
            self.lbl_nombre_elemento = None
            self.lbl_detalles = None

        # --- Tabla Periódica --- (Columna 1)
        self.tabla_periodica = TablaPeriodica(self.frame_top,
                                              click_callback=self.evento_click_elemento,
                                              hover_callback=self.actualizar_panel_info)
        self.tabla_periodica.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

        # --- Frame de Entrada de Ecuación (Fila 1) CustomTKinter / fallback ---
        try:
            self.frame_input = ctk.CTkFrame(
                master=self.frame_middle,
                fg_color='#B0BEC5',
                corner_radius=20,
            )
        except Exception:
            self.frame_input = tk.Frame(self.frame_middle, bg='#B0BEC5')

        self.frame_input.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        self.frame_input.grid_columnconfigure(0, weight=1)

        # Título
        try:
            lbl_EcuacionQ = ctk.CTkLabel(master=self.frame_input, corner_radius=20,
                                         text="Ecuación Química",
                                         text_color="#000000",
                                         font=("Helvetica", 18, 'bold'))
        except Exception:
            lbl_EcuacionQ = tk.Label(self.frame_input, text="Ecuación Química",
                                     font=("Helvetica", 18, 'bold'), bg='#B0BEC5')
        lbl_EcuacionQ.grid(row=0, column=0, columnspan=10, pady=2)

        # Campo de entrada de la ecuación
        self.ecuacion_var = tk.StringVar(value="")
        self.entry_ecuacion = tk.Entry(self.frame_input, textvariable=self.ecuacion_var,
                                       font=('Helvetica', 12), width=35, bd=2, relief=tk.SUNKEN)
        self.entry_ecuacion.grid(row=1, column=0, columnspan=10, padx=5, pady=5, sticky="ew")

        # Frame para el constructor de la ecuación
        self.frame_constructor = tk.Frame(self.frame_input, bg='#B0BEC5')
        self.frame_constructor.grid(row=2, column=0, columnspan=10, pady=5, sticky="ew")
        self.frame_constructor.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        lbl_mol = tk.Label(self.frame_constructor, text="Molécula:", font=('Helvetica', 11), bg='#B0BEC5')
        lbl_mol.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.molecula_var = tk.StringVar(value="")
        # añadir trace; la función manejará la re-adición del trace con seguridad
        self.molecula_var.trace_add('write', self.convertir_a_subindices)
        self.entry_molecula = tk.Entry(self.frame_constructor, textvariable=self.molecula_var,
                                       font=('Helvetica', 11), width=12, bd=1)
        self.entry_molecula.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- BOTONES ---
        try:
            btn_agregar = ctk.CTkButton(master=self.frame_constructor, text="Agregar (+)",
                                        fg_color="#1E88E5", hover_color="#1565C0",
                                        corner_radius=15, height=30, width=100,
                                        font=("Helvetica", 13, "bold"),
                                        command=self.agregar_molecula)
            btn_flecha = ctk.CTkButton(master=self.frame_constructor, text="Flecha (→)",
                                       fg_color="#FFC107", hover_color="#C09000",
                                       corner_radius=15, height=30, width=100,
                                       font=("Helvetica", 13, "bold"),
                                       command=self.agregar_flecha)
            btn_limpiar = ctk.CTkButton(master=self.frame_constructor, text="Limpiar",
                                        fg_color="#E34234", hover_color="#BE3A2E",
                                        corner_radius=15, height=32, width=110,
                                        font=("Helvetica", 13, "bold"),
                                        command=self.limpiar_ecuacion)
            btn_balancear = ctk.CTkButton(master=self.frame_constructor, text="Balancear",
                                          fg_color="#00A86B", hover_color="#027E50",
                                          corner_radius=15, height=32, width=110,
                                          font=("Helvetica", 13, "bold"),
                                          command=self.balancear_ecuacion)
            btn_lewis = ctk.CTkButton(master=self.frame_constructor, text="Ver Lewis",
                                      fg_color="#9C27B0", hover_color="#751E85",
                                      corner_radius=15, height=32, width=110,
                                      font=("Helvetica", 13, "bold"),
                                      command=self.mostrar_lewis_actual)
        except Exception:
            # fallback a tk.Button si CTk no está disponible
            btn_agregar = tk.Button(self.frame_constructor, text="Agregar (+)", command=self.agregar_molecula)
            btn_flecha = tk.Button(self.frame_constructor, text="Flecha (→)", command=self.agregar_flecha)
            btn_limpiar = tk.Button(self.frame_constructor, text="Limpiar", command=self.limpiar_ecuacion)
            btn_balancear = tk.Button(self.frame_constructor, text="Balancear", command=self.balancear_ecuacion)
            btn_lewis = tk.Button(self.frame_constructor, text="Ver Lewis", command=self.mostrar_lewis_actual)

        btn_agregar.grid(row=0, column=2, padx=5, pady=5)
        btn_flecha.grid(row=0, column=3, padx=5, pady=5)
        btn_limpiar.grid(row=1, column=1, padx=5, pady=(2, 5))
        btn_balancear.grid(row=1, column=2, padx=5, pady=(2, 5))
        btn_lewis.grid(row=1, column=3, padx=5, pady=(2, 5))

        # --- Frame de Resultado (Fila 2) ---
        try:
            self.frame_bottom = ctk.CTkFrame(master=self.frame_middle, fg_color='#B0BEC5', corner_radius=20)
            self.frame_bottom.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        except Exception:
            self.frame_bottom = tk.Frame(self.frame_middle, bg='#ECEFF1', padx=10, pady=10)
            self.frame_bottom.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)

        self.frame_bottom.grid_columnconfigure(0, weight=1)
        self.frame_bottom.grid_rowconfigure(1, weight=1)

        try:
            lbl_resultados = ctk.CTkLabel(master=self.frame_bottom, text="Procedimiento y Resultado",
                                          text_color="#000000", font=("Helvetica", 18, 'bold'))
            lbl_resultados.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        except Exception:
            tk.Label(self.frame_bottom, text="Procedimiento y Resultado", font=('Helvetica', 14, 'bold'),
                     bg='#ECEFF1').grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.output_text = scrolledtext.ScrolledText(self.frame_bottom, wrap=tk.WORD, height=6,
                                                     font=('Consolas', 11), bd=0, relief=tk.FLAT, bg="#ECEFF1",
                                                     padx=10, pady=10)
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        # --- Frame para Lewis (Fila final) ---
        self.frame_lewis = tk.Frame(self, bg='#DDE3E8', padx=5, pady=5)
        self.frame_lewis.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))

        self.frame_lewis.grid_columnconfigure(0, weight=1)
        self.frame_lewis.grid_columnconfigure(1, weight=2)
        self.frame_lewis.grid_rowconfigure(0, weight=0, minsize=30)
        self.frame_lewis.grid_rowconfigure(1, weight=1)

        self.label_lewis_title = tk.Label(self.frame_lewis, text="Estructura de Lewis (2D) y Modelo (3D)",
                                          font=('Helvetica', 14, 'bold'), bg='#DDE3E8')
        self.label_lewis_title.grid(row=0, column=0, columnspan=2, pady=(2, 5), sticky="n")

        self.canvas_2d = tk.Canvas(self.frame_lewis, bg="white", highlightthickness=1, highlightbackground="#AAAAAA")
        self.canvas_2d.grid(row=1, column=0, sticky="nsew", padx=5, pady=0)

        self.frame_3d = tk.Frame(self.frame_lewis, bg="black")
        self.frame_3d.grid(row=1, column=1, sticky="nsew", padx=2, pady=0)

        # variables internas
        self._vtk_actors = []

    # -----------------------------
    # Generador heurístico de geometría
    # -----------------------------
    def formula_a_atoms_bonds(self, formula_norm):
        """
        Entrada: formula_norm tipo 'H2O' (sin subíndices unicode).
        Salida:
          atoms_2d: [{'elem': 'O', 'x':..., 'y':...}, ...]
          atoms_3d: [{'elem':'O', 'pos':(x,y,z)}, ...]
          bonds: [(i,j,order), ...]
        Heurístico para moléculas sencillas.
        """
        tokens = re.findall(r'([A-Z][a-z]?)(\d*)', formula_norm)
        atoms = []
        for sym, num in tokens:
            n = int(num) if num else 1
            for _ in range(n):
                atoms.append(sym.capitalize())
        if 'C' in atoms:
            central_idx = atoms.index('C')
        else:
            non_h = [i for i, a in enumerate(atoms) if a != 'H']
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
                idx = i if i < central_idx else i - 1
                theta = 2 * math.pi * (idx / max(1, n_subs))
                x = cx + radius * math.cos(theta)
                y = cy + radius * math.sin(theta)
                atoms_2d.append({'elem': elem, 'x': x, 'y': y})

        atoms_3d = []
        for i, elem in enumerate(atoms):
            if i == central_idx:
                atoms_3d.append({'elem': elem, 'pos': (0.0, 0.0, 0.0)})
            else:
                angle = 2 * math.pi * (i / max(1, len(atoms)))
                r = 1.2
                z = 0.0 if len(atoms) <= 3 else (0.2 * (((i % 2) * 2) - 1))
                atoms_3d.append({'elem': elem, 'pos': (r * math.cos(angle), r * math.sin(angle), z)})
        return atoms_2d, atoms_3d, bonds

    # -----------------------------
    # Dibujado 2D en canvas (versión mejorada del viejo)
    # -----------------------------
    def dibujar_2d_en_canvas(self, atoms_2d, bonds):
        """
        Dibuja la estructura en canvas escalada y con apariencia mejorada.
        Esta versión viene de la implementación más completa (viejointerfaz).
        """
        self.canvas_2d.delete("all")
        self.canvas_2d.update_idletasks()
        canvas_w = max(220, self.canvas_2d.winfo_width())
        canvas_h = max(140, self.canvas_2d.winfo_height())
        padding = 18

        if not atoms_2d:
            return

        xs = [a['x'] for a in atoms_2d]
        ys = [a['y'] for a in atoms_2d]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        content_w = maxx - minx if maxx > minx else 1.0
        content_h = maxy - miny if maxy > miny else 1.0

        scale_x = (canvas_w - 2 * padding) / content_w
        scale_y = (canvas_h - 2 * padding) / content_h
        scale = min(scale_x, scale_y, 1.4)

        cx_orig = (minx + maxx) / 2.0
        cy_orig = (miny + maxy) / 2.0
        cx_canvas = canvas_w / 2.0
        cy_canvas = canvas_h / 2.0

        atoms_t = []
        for a in atoms_2d:
            tx = cx_canvas + (a['x'] - cx_orig) * scale
            ty = cy_canvas + (a['y'] - cy_orig) * scale
            atoms_t.append({'elem': a['elem'], 'x': tx, 'y': ty})

        atom_color = {
            "H": "#FFFFFF", "C": "#333333", "O": "#FF3B30", "N": "#007AFF",
            "S": "#FFD60A", "Cl": "#00C853", "F": "#00C853", "P": "#FF9500"
        }

        def draw_bond(p1, p2, order):
            x1, y1 = p1; x2, y2 = p2
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            if length == 0:
                return
            ux, uy = dx / length, dy / length
            px, py = -uy, ux
            offset = max(3, 6 * (scale / 1.2))
            if order == 1:
                self.canvas_2d.create_line(x1, y1, x2, y2, width=max(1, int(2 * scale)), capstyle=tk.ROUND)
            else:
                if order == 2:
                    steps = [-offset / 2, offset / 2]
                elif order == 3:
                    steps = [-offset, 0, offset]
                else:
                    steps = [0]
                for s in steps:
                    sx1 = x1 + px * s; sy1 = y1 + py * s
                    sx2 = x2 + px * s; sy2 = y2 + py * s
                    self.canvas_2d.create_line(sx1, sy1, sx2, sy2, width=max(1, int(1.6 * scale)), capstyle=tk.ROUND)

        # Dibujar enlaces
        for i, j, order in bonds:
            if i < 0 or j < 0 or i >= len(atoms_t) or j >= len(atoms_t):
                continue
            a = atoms_t[i]; b = atoms_t[j]
            draw_bond((a['x'], a['y']), (b['x'], b['y']), order)

        # Dibujar átomos
        for idx, a in enumerate(atoms_t):
            x = a['x']; y = a['y']
            elem = a['elem']
            base_r = max(8, 14 * scale)
            try:
                self.canvas_2d.create_oval(x - base_r - 2, y - base_r - 2, x + base_r + 2, y + base_r + 2, fill="#E6E6E6", outline="")
            except Exception:
                pass

            fill = atom_color.get(elem, "#B0BEC5")
            if elem == "H":
                fill = atom_color.get("H", "#FFFFFF")
            self.canvas_2d.create_oval(x - base_r, y - base_r, x + base_r, y + base_r, fill=fill, outline="#222222", width=max(1, int(1.5 * scale)))

            font_size = max(9, int(12 * scale))
            self.canvas_2d.create_text(x, y - 1, text=elem, font=("Helvetica", font_size, "bold"))

            try:
                if hasattr(self, "df_elementos") and self.df_elementos is not None:
                    df = self.df_elementos
                    row = df[df["Simbolo"] == elem]
                    if not row.empty:
                        z = int(row["NumeroAtomico"].values[0])
                        self.canvas_2d.create_text(x, y + base_r - 6, text=str(z), font=("Helvetica", max(6, int(8 * scale))), fill="#333333")
            except Exception:
                pass

        self.canvas_2d.create_rectangle(2, 2, canvas_w - 2, canvas_h - 2, outline="#CCCCCC")

    # -----------------------------
    # VTK 3D (inicialización y render)
    # -----------------------------
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

    def clear_vtk_scene(self):
        for actor in getattr(self, "_vtk_actors", []):
            self.vtk_renderer.RemoveActor(actor)
        self._vtk_actors = []
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.GetRenderWindow().Render()

    def render_molecule_3d(self, atoms3d, bonds):
        try:
            from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper
            from vtkmodules.vtkFiltersSources import vtkSphereSource, vtkCylinderSource
            from vtkmodules.vtkCommonTransforms import vtkTransform
        except Exception as e:
            # si falla aquí, init_vtk_3d ya debería haber manejado el error
            print(f"[DEBUG] Error importando módulos VTK durante render: {e}")
            return

        self.clear_vtk_scene()

        radius_map = {"H": 0.2, "C": 0.35, "O": 0.33, "N": 0.33, "S": 0.4}
        color_map = {"H": (1, 1, 1), "C": (0.2, 0.2, 0.2), "O": (1, 0, 0), "N": (0, 0, 1), "S": (1, 1, 0)}

        for a in atoms3d:
            elem = a.get("elem", "X"); pos = a.get("pos", (0, 0, 0))
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
            actor.GetProperty().SetColor(color_map.get(elem, (0.5, 0.5, 0.5)))
            self.vtk_renderer.AddActor(actor)
            self._vtk_actors.append(actor)

        for i, j, order in bonds:
            p1 = _np.array(atoms3d[i]['pos']); p2 = _np.array(atoms3d[j]['pos'])
            v = p2 - p1
            length = _np.linalg.norm(v)
            if length == 0:
                continue
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
            actor.GetProperty().SetColor(0.7, 0.7, 0.7)

            self.vtk_renderer.AddActor(actor)
            self._vtk_actors.append(actor)

        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.GetRenderWindow().Render()

    # -----------------------------
    # Validaciones + propiedades moleculares (version vieja)
    # -----------------------------
    def _validar_molecula_sin_coeficiente(self, molecula_normal: str) -> bool:
        """
        Devuelve True si la molécula NO tiene coeficiente al inicio.
        Ej: "CH4" -> True, "2CH4" -> False
        """
        if not molecula_normal:
            return False
        if re.match(r'^\d+', molecula_normal):
            return False
        return True

    def calcular_propiedades_molecula(self, formula_norm, atoms_2d, atoms_3d, bonds):
        """
        Genera un texto breve con características principales de la molécula.
        Implementación conservada de la versión anterior (viejointerfaz).
        """
        from collections import Counter
        import numpy as _np

        VALENCE = {
            "H": 1, "He": 2,
            "Li": 1, "Be": 2, "B": 3, "C": 4, "N": 5, "O": 6, "F": 7, "Ne": 8,
            "P": 5, "S": 6, "Cl": 7, "Br": 7, "I": 7
        }

        bond_orders = [int(order) if order is not None else 1 for (_, _, order) in bonds]
        total_bonds = len(bonds)
        singles = sum(1 for o in bond_orders if o == 1)
        doubles = sum(1 for o in bond_orders if o == 2)
        triples = sum(1 for o in bond_orders if o >= 3)
        total_pairs_in_bonds = sum(bond_orders)

        lines = []
        lines.append(f"Fórmula: {formula_norm}")
        lines.append("")

        lines.append("Tipo y número de enlaces:")
        if total_bonds == 0:
            lines.append("  - No se detectaron enlaces.")
        else:
            types = []
            if singles:
                types.append(f"{singles} simple(s)")
            if doubles:
                types.append(f"{doubles} doble(s)")
            if triples:
                types.append(f"{triples} triple(s)")
            types_str = ", ".join(types)
            example = ""
            if "C" in [a["elem"] for a in atoms_2d] and "O" in [a["elem"] for a in atoms_2d] and doubles:
                example = " Ej.: en CO₂ hay dos enlaces dobles."
            lines.append(f"  - {types_str}.{example}")
            lines.append(f"  - Enlaces totales: {total_bonds}")
            lines.append(f"  - Pares de electrones compartidos en enlaces: {total_pairs_in_bonds} (cada par = 2 e-)")
        lines.append("")

        lines.append("Configuración y valencia (resumen por átomo):")
        elems = [a["elem"] for a in atoms_2d]
        counts = Counter(elems)

        degs = [0] * len(atoms_2d)
        for i, j, order in bonds:
            o = int(order) if order is not None else 1
            degs[i] += o
            degs[j] += o

        for idx, a in enumerate(atoms_2d):
            sym = a.get("elem", "?")
            val = VALENCE.get(sym, None)
            if val is None:
                try:
                    if hasattr(self, "df_elementos") and self.df_elementos is not None:
                        row = self.df_elementos[self.df_elementos["Simbolo"] == sym]
                        if not row.empty and "NumeroAtomico" in row.columns:
                            z = int(row["NumeroAtomico"].values[0])
                            val = z % 8
                            if val == 0:
                                val = 8
                        else:
                            val = 0
                    else:
                        val = 0
                except Exception:
                    val = 0

            bonds_count = degs[idx]
            electrons_around_from_bonds = bonds_count * 2
            lone_elec = val - bonds_count
            if lone_elec < 0:
                lone_elec = 0
            lone_pairs = lone_elec // 2 if lone_elec >= 2 else (1 if lone_elec == 1 else 0)
            electrons_around = electrons_around_from_bonds + (lone_pairs * 2)

            target = 2 if sym == "H" else 8
            meets = "Sí" if electrons_around == target else "No (estimado)"
            lines.append(f"  - {sym}: valencia ≈ {val}e-, enlaces ≈ {bonds_count}, pares solitarios ≈ {lone_pairs}. Cumple regla ({target}): {meets}")

        lines.append("")
        lines.append("Notas (para estudiantes):")
        lines.append("  - Cada línea = 1 par de electrones (2 e-). Doble = 2 pares, triple = 3 pares.")
        lines.append("  - La regla del octeto significa tener ~8 electrones alrededor (H solo 2).")
        lines.append("  - Esta es una explicación simplificada para aprender la idea; estructuras reales pueden tener excepciones.")

        return "\n".join(lines)

    # -----------------------------
    # Mostrar Lewis (botón) - combinación robusta de ambas versiones
    # -----------------------------
    def mostrar_lewis_actual(self):
        """
        Obtiene la molécula del campo, dibuja 2D y 3D y escribe propiedades en el panel de salida.
        Implementación robusta (captura errores parciales y asegura que la UI no se rompa).
        """
        mol_unicode = self.molecula_var.get().strip()
        mol_norm = mol_unicode.translate(SUB_TO_NORMAL)

        if not mol_norm:
            messagebox.showinfo("Info", "Escribe una molécula en el campo 'Molécula' (ej: CH4) y pulsa Ver Lewis.")
            return

        # Validación: evitar coeficientes en el campo 'Molécula' (ej: "2CH4")
        if not self._validar_molecula_sin_coeficiente(mol_norm):
            messagebox.showwarning(
                "Formato inválido",
                "Por favor ingresa una molécula estable en el campo 'Molécula' (ej: CH4). "
                "No escribas coeficientes al inicio (por ejemplo: 2CH4)."
            )
            return

        try:
            atoms_2d, atoms_3d, bonds = self.formula_a_atoms_bonds(mol_norm)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la geometría para '{mol_norm}': {e}")
            return

        # Dibujar 2D
        try:
            self.dibujar_2d_en_canvas(atoms_2d, bonds)
        except Exception as e:
            print(f"[DEBUG] Error al dibujar 2D: {e}")

        # Inicializar y renderizar VTK (si está disponible)
        try:
            if not hasattr(self, 'vtk_widget'):
                self.init_vtk_3d()
            if hasattr(self, 'vtk_widget'):
                try:
                    self.render_molecule_3d(atoms_3d, bonds)
                except Exception as e:
                    print(f"[DEBUG] Error al renderizar 3D: {e}")
        except Exception as e:
            print(f"[DEBUG] Excepción al manejar VTK: {e}")

        # Asegurar output editable y escribir propiedades
        try:
            self.output_text.configure(state='normal')
        except Exception:
            pass

        try:
            props = self.calcular_propiedades_molecula(mol_norm, atoms_2d, atoms_3d, bonds)
            self.output_text.insert(tk.END, "=== Propiedades de la molécula ===\n")
            self.output_text.insert(tk.END, props + "\n")
            self.output_text.insert(tk.END, "=== Fin propiedades ===\n\n")
            self.output_text.see(tk.END)
        except Exception as e:
            try:
                self.output_text.insert(tk.END, f"Mostrar Lewis: {mol_norm} | átomos: {len(atoms_2d)} | enlaces: {len(bonds)}\n")
                self.output_text.insert(tk.END, f"(Error al calcular propiedades: {e})\n")
                self.output_text.see(tk.END)
            except Exception:
                print(f"[DEBUG] Error al insertar texto en output_text: {e}")

    # -----------------------------
    # Conversión a subíndices (trace)
    # -----------------------------
    def convertir_a_subindices(self, *args):
        """
        Trace que convierte números en subíndices en self.molecula_var,
        protegiendo coeficientes al inicio.
        """
        current_value_unicode = self.molecula_var.get()
        current_value_normal = current_value_unicode.translate(SUB_TO_NORMAL)

        match = re.match(r'^(\d*)(.*)$', current_value_normal)
        new_value_unicode = current_value_unicode

        if match:
            coef = match.group(1)
            mol = match.group(2)
            mol_subscripted = mol.translate(NORMAL_TO_SUB)
            new_value_unicode = coef + mol_subscripted
        else:
            new_value_unicode = current_value_normal.translate(NORMAL_TO_SUB)

        # Evitar bucle de trace: quitar y volver a agregar
        try:
            trace_info = self.molecula_var.trace_info()
            trace_id = trace_info[0][1] if trace_info else None
        except Exception:
            trace_id = None

        if trace_id:
            try:
                self.molecula_var.trace_remove('write', trace_id)
            except Exception:
                pass

        if new_value_unicode != current_value_unicode:
            self.molecula_var.set(new_value_unicode)
            try:
                self.entry_molecula.icursor(tk.END)
            except Exception:
                pass

        if trace_id:
            try:
                self.molecula_var.trace_add('write', self.convertir_a_subindices)
            except Exception:
                pass

    # -----------------------------
    # Panel información (actualizar)
    # -----------------------------
    def actualizar_panel_info(self, info_elemento):
        """
        Actualiza el panel de información. Si usamos CTK muestra diseño más bonito,
        si no, actualiza el label simple.
        """
        simbolo = info_elemento.get('Simbolo')
        nombre = str(info_elemento.get('Nombre', 'Elemento')).title()
        numero = info_elemento.get('NumeroAtomico')
        masa = info_elemento.get('MasaAtomica')
        tipo = info_elemento.get('TipoElemento')

        # Si usamos CTk labels, actualizar esos
        try:
            from modules.utils import COLORES_GRUPOS
            color_familia = COLORES_GRUPOS.get(tipo, "#455A64")
        except Exception:
            color_familia = "#455A64"

        if hasattr(self, "lbl_simbolo_grande") and self.lbl_simbolo_grande is not None:
            try:
                self.lbl_simbolo_grande.configure(text=simbolo)
                self.lbl_simbolo_grande.configure(text_color=color_familia)
            except Exception:
                try:
                    self.lbl_simbolo_grande.configure(text=simbolo)
                except Exception:
                    pass

        if hasattr(self, "lbl_nombre_elemento") and self.lbl_nombre_elemento is not None:
            try:
                self.lbl_nombre_elemento.configure(text=nombre)
            except Exception:
                pass

        if hasattr(self, "lbl_detalles") and self.lbl_detalles is not None:
            texto_detalles = f"N° Atómico: {numero}\nMasa: {masa}\n{tipo}"
            try:
                self.lbl_detalles.configure(text=texto_detalles)
            except Exception:
                pass

        # Si tenemos un fallback label self.frame_info como tk.Label, actualizar su texto
        try:
            if isinstance(self.frame_info, tk.Label):
                info = (f"{nombre} ({simbolo})\nZ: {numero} | Masa: {masa}\nTipo: {tipo}")
                self.frame_info.config(text=info)
        except Exception:
            pass

    # -----------------------------
    # Eventos y operaciones de la ecuación
    # -----------------------------
    def evento_click_elemento(self, elemento_info):
        # Actualiza panel y agrega símbolo al entry de molécula (con subíndices)
        self.actualizar_panel_info(elemento_info)
        simbolo = elemento_info['Simbolo']
        current_molecula = self.molecula_var.get()
        current_molecula_normal = current_molecula.translate(SUB_TO_NORMAL)
        new_normal = current_molecula_normal + simbolo
        self.molecula_var.set(new_normal.translate(NORMAL_TO_SUB))
        try:
            self.entry_molecula.focus_set()
        except Exception:
            pass

    def agregar_molecula(self):
        molecula_unicode = self.molecula_var.get().strip()
        molecula_normal = molecula_unicode.translate(SUB_TO_NORMAL)
        ecuacion_actual_unicode = self.ecuacion_var.get().strip()
        ecuacion_actual_normal = ecuacion_actual_unicode.translate(SUB_TO_NORMAL)

        if molecula_normal:
            if not ecuacion_actual_normal or ecuacion_actual_normal.endswith('→'):
                nueva_ecuacion_normal = ecuacion_actual_normal + " " + molecula_normal
            elif ecuacion_actual_normal.endswith('+ '):
                nueva_ecuacion_normal = ecuacion_actual_normal[:-2] + " + " + molecula_normal
            else:
                nueva_ecuacion_normal = ecuacion_actual_normal + " + " + molecula_normal

            ecuacion_a_mostrar = self.aplicar_subindices(nueva_ecuacion_normal.strip())
            self.ecuacion_var.set(ecuacion_a_mostrar)
            self.molecula_var.set("")

    def agregar_flecha(self):
        ecuacion_actual_unicode = self.ecuacion_var.get().strip()
        if not ecuacion_actual_unicode.endswith('→'):
            ecuacion_actual_normal = ecuacion_actual_unicode.translate(SUB_TO_NORMAL)
            if ecuacion_actual_normal.endswith('+'):
                ecuacion_actual_normal = ecuacion_actual_normal[:-1]
            elif ecuacion_actual_normal.endswith('+ '):
                ecuacion_actual_normal = ecuacion_actual_normal[:-2]
            parte_limpia_unicode = self.aplicar_subindices(ecuacion_actual_normal.strip())
            self.ecuacion_var.set(parte_limpia_unicode + " → ")
            self.molecula_var.set("")

    def limpiar_ecuacion(self):
        self.ecuacion_var.set("")
        self.molecula_var.set("")
        try:
            self.output_text.delete(1.0, tk.END)
        except Exception:
            pass

    # -----------------------------
    # Balanceo de ecuación
    # -----------------------------
    def balancear_ecuacion(self):
        ecuacion_unicode_str = self.ecuacion_var.get().strip()
        ecuacion_str = ecuacion_unicode_str.translate(SUB_TO_NORMAL)
        try:
            self.output_text.delete(1.0, tk.END)
        except Exception:
            pass

        if not ecuacion_str or '→' not in ecuacion_str:
            messagebox.showerror("Error de Formato", "Por favor, introduce una ecuación química válida con reactivos, flecha (→) y productos.")
            return

        try:
            reactivos_str, productos_str = [s.strip() for s in ecuacion_str.split('→')]
            reactivos = [parsear_ecuacion(s.strip()) for s in reactivos_str.split('+')]
            productos = [parsear_ecuacion(s.strip()) for s in productos_str.split('+')]

            balanceador = BalanceadorEcuacion(reactivos, productos)

            self.output_text.insert(tk.END, "1. Asignamos variables:\n")
            ecuacion_con_variables = balanceador.obtener_ecuacion_con_variables()
            self.output_text.insert(tk.END, self.aplicar_subindices(ecuacion_con_variables) + "\n\n")

            matriz, elementos = balanceador.construir_matriz()

            self.output_text.insert(tk.END, "2. Ecuaciones por elemento:\n")
            for i, elem in enumerate(elementos):
                ecuacion = balanceador.obtener_ecuacion_texto(elem, matriz[i])
                self.output_text.insert(tk.END, f"  {elem}: {ecuacion}\n")
            self.output_text.insert(tk.END, "\n")

            coeficientes = balanceador.resolver()

            self.output_text.insert(tk.END, "3. Resolución del sistema:\n")
            if not coeficientes:
                self.output_text.insert(tk.END, "  Error: No se encontró solución entera simple o la ecuación es trivial/inválida.\n")
                return

            self.output_text.insert(tk.END, f"  Coeficientes fraccionarios/decimales: {coeficientes}\n")

            coeficientes_enteros = balanceador.minimizar_coeficientes(coeficientes)
            self.output_text.insert(tk.END, f"  Coeficientes enteros mínimos: {coeficientes_enteros}\n\n")

            ecuacion_balanceada = balanceador.formatear_ecuacion_balanceada(coeficientes_enteros)
            ecuacion_sub = self.aplicar_subindices(ecuacion_balanceada)

            self.output_text.insert(tk.END, "4. Ecuación Balanceada:\n")
            self.output_text.insert(tk.END, f"  {ecuacion_sub}", ('balanceada',))
            self.output_text.tag_config('balanceada', font=('Consolas', 12, 'bold'), foreground="#0D47A1")

        except ValueError as e:
            messagebox.showerror("Error de Parseo", str(e))
        except Exception as e:
            messagebox.showerror("Error Desconocido", f"Ocurrió un error inesperado durante el balanceo: {e}")

    # -----------------------------
    # Formateo a subíndices (util)
    # -----------------------------
    def aplicar_subindices(self, texto):
        """
        Convierte los números de las moléculas a subíndices unicode,
        manteniendo los coeficientes al inicio.
        """
        partes = texto.split()
        resultado = []
        for parte in partes:
            if parte in ('+', '→'):
                resultado.append(parte)
                continue
            match = re.match(r'^(\d*)(.*)$', parte)
            if match:
                coef = match.group(1)
                mol = match.group(2)
                mol_subscripted = mol.translate(NORMAL_TO_SUB)
                resultado.append(coef + mol_subscripted)
            else:
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
