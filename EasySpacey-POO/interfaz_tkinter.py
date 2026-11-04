import copy
import math
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from time import perf_counter

from distribucion import Distribucion
from habitacion import Habitacion
from mueble import Mueble
from persistencia import guardar_proyecto
from punto3d import Punto3D
from restriccion import Restriccion
from outlet import Outlet


# Lista desplazable para mostrar muebles y restricciones.
class ScrollableList(ttk.Frame):
    # Inicializa el estado y construye los elementos de la interfaz.
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, background="#FFFFFF")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, style="List.TFrame")
        self.window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        # Ajusta el desplazamiento cuando cambia el contenido.
        self.content.bind("<Configure>", self._update_scroll_region)
        # Mantiene el contenido ajustado al ancho visible.
        self.canvas.bind("<Configure>", self._fit_width)
        self.canvas.bind("<Enter>", lambda _event: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda _event: self.canvas.unbind_all("<MouseWheel>"))

    # Actualiza el área desplazable según su contenido.
    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # Ajusta el ancho del contenido al tamaño del Canvas.
    def _fit_width(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)

    # Desplaza la lista con la rueda del ratón.
    def _wheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    # Elimina los widgets actuales de la lista.
    def clear(self):
        for child in self.content.winfo_children():
            child.destroy()


# Controla la ventana y conecta las entradas con la lógica.
class TkinterInterface:
    COLORS = (
        "#4C78A8", "#F58518", "#54A24B", "#E45756",
        "#B279A2", "#FF9DA6", "#9D755D", "#72B7B2"
    )

    # Inicializa el estado y construye los elementos de la interfaz.
    def __init__(self, root=None):
        # Utiliza una ventana recibida o crea una nueva.
        self.root = root or tk.Tk()
        # Guarda la habitación actual o None si todavía no existe.
        self.room = None
        # Almacena las alternativas generadas.
        self.distributions = []
        # Indica cuál alternativa se muestra.
        self.current_index = 0
        # Permite descartar resultados de generaciones anteriores.
        self.generation_token = 0
        # Identifica el redibujado pendiente al cambiar el tamaño.
        self.resize_job = None
        self.preview_zoom = 1.0
        self.preview_pan_x = 0.0
        self.preview_pan_y = 0.0
        self.preview_drag_start = None
        self.preview_pan_start = None
        self.preview_snap_job = None
        self.preview_geometry = None
        self.preview_mode = "2D"
        self.preview_rotation = 0
        # Relaciona claves de texto con campos Entry.
        self.entries = {}
        self._configure_window()
        self._configure_styles()
        self._build_interface()
        self._refresh_lists()
        self._draw_preview()

    # Configura el título, tamaño y distribución de la ventana.
    def _configure_window(self):
        self.root.title("EasySpacey")
        self.root.geometry("1500x850")
        self.root.minsize(1120, 700)
        self.root.configure(background="#F1F5F9")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

    # Define colores, fuentes y estilos de los widgets.
    def _configure_styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#F1F5F9")
        style.configure("Card.TFrame", background="#FFFFFF")
        style.configure("List.TFrame", background="#FFFFFF")
        style.configure("Title.TLabel", background="#F1F5F9", foreground="#0F172A",
                        font=("Segoe UI", 22, "bold"))
        style.configure("Subtitle.TLabel", background="#F1F5F9", foreground="#64748B",
                        font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#FFFFFF", foreground="#0F172A",
                        font=("Segoe UI", 11, "bold"))
        style.configure("PreviewRoom.TLabel", background="#FFFFFF", foreground="#0F172A",
                        font=("Segoe UI", 17, "bold"))
        style.configure("PreviewIteration.TLabel", background="#FFFFFF", foreground="#2563EB",
                        font=("Segoe UI", 11, "bold"))
        style.configure("Card.TLabel", background="#FFFFFF", foreground="#334155",
                        font=("Segoe UI", 9))
        style.configure("ListText.TLabel", background="#FFFFFF", foreground="#334155",
                        font=("Segoe UI", 9))
        style.configure("Primary.TButton", font=("Segoe UI", 9, "bold"))
        style.configure("Delete.TButton", foreground="#FFFFFF", background="#DC2626",
                        font=("Segoe UI", 10, "bold"), padding=(5, 1))
        style.map("Delete.TButton", background=[("active", "#EF4444")])
        style.configure("Status.TLabel", background="#F1F5F9", foreground="#334155",
                        font=("Segoe UI", 9))

    # Construye los paneles principales de la aplicación.
    def _build_interface(self):
        header = ttk.Frame(self.root, padding=(22, 14, 22, 8))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="EasySpacey", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Diseño automático de habitaciones", style="Subtitle.TLabel").grid(
            row=1, column=0, sticky="w"
        )

        body = ttk.Panedwindow(self.root, orient="horizontal")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 8))
        # Permite acceder a todos los formularios mediante desplazamiento.
        self.form_container = ttk.Frame(body, style="Card.TFrame", width=390)
        self.form_canvas = tk.Canvas(
            self.form_container, background="#FFFFFF", highlightthickness=0,
            width=365
        )
        self.form_scrollbar = ttk.Scrollbar(
            self.form_container, orient="vertical", command=self.form_canvas.yview
        )
        self.form_canvas.configure(yscrollcommand=self.form_scrollbar.set)
        self.form_canvas.pack(side="left", fill="both", expand=True)
        self.form_scrollbar.pack(side="right", fill="y")
        self.form_panel = ttk.Frame(self.form_canvas, style="Card.TFrame", padding=12)
        self.form_window = self.form_canvas.create_window(
            (0, 0), window=self.form_panel, anchor="nw"
        )
        # Ajusta la zona desplazable y el ancho de los formularios.
        self.form_panel.bind("<Configure>", self._update_form_scroll)
        self.form_canvas.bind("<Configure>", self._fit_form_width)
        self.form_canvas.bind("<Enter>", self._enable_form_wheel)
        self.form_canvas.bind("<Leave>", self._disable_form_wheel)
        self.preview_panel = ttk.Frame(body, style="Card.TFrame", padding=10)
        self.list_panel = ttk.Frame(body, style="Card.TFrame", padding=12, width=340)
        body.add(self.form_container, weight=0)
        body.add(self.preview_panel, weight=1)
        body.add(self.list_panel, weight=0)
        self._build_forms()
        self._build_preview()
        self._build_lists()

        self.status_var = tk.StringVar(value="Cree una habitación para comenzar.")
        self.status_label = ttk.Label(
            self.root, textvariable=self.status_var, style="Status.TLabel", anchor="w"
        )
        self.status_label.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))

    # Actualiza el espacio desplazable cuando cambian los formularios.
    def _update_form_scroll(self, _event=None):
        self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all"))

    # Mantiene los formularios ajustados al ancho visible.
    def _fit_form_width(self, event):
        self.form_canvas.itemconfigure(self.form_window, width=event.width)

    # Activa la rueda al entrar al panel de formularios.
    def _enable_form_wheel(self, _event=None):
        self.form_canvas.bind_all("<MouseWheel>", self._scroll_forms)

    # Desactiva la rueda al salir del panel de formularios.
    def _disable_form_wheel(self, _event=None):
        self.form_canvas.unbind_all("<MouseWheel>")

    # Desplaza el panel izquierdo sin afectar el plano.
    def _scroll_forms(self, event):
        self.form_canvas.yview_scroll(int(-event.delta / 120), "units")

    # Crea un campo de entrada y lo registra por su clave.
    def _entry(self, parent, key, label, row, column=0, columnspan=1):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, columnspan=columnspan,
                   sticky="ew", padx=4, pady=3)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label, style="Card.TLabel").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(frame)
        entry.grid(row=1, column=0, sticky="ew", pady=(1, 0))
        self.entries[key] = entry
        return entry

    # Crea una lista desplegable de opciones permitidas.
    def _combo(self, parent, label, values, row, column=0):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, sticky="ew", padx=4, pady=3)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label, style="Card.TLabel").grid(row=0, column=0, sticky="w")
        combo = ttk.Combobox(frame, values=values, state="readonly")
        combo.set("")
        combo.grid(row=1, column=0, sticky="ew", pady=(1, 0))
        return combo

    # Construye los formularios y conecta sus botones.
    def _build_forms(self):
        panel = self.form_panel
        panel.columnconfigure(0, weight=1)

        room_box = ttk.LabelFrame(panel, text="1. Habitación", padding=8)
        room_box.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for column in (0, 1):
            room_box.columnconfigure(column, weight=1)
        self._entry(room_box, "room_name", "Nombre", 0, 0)
        self._entry(room_box, "room_width", "Ancho (m)", 1, 0)
        self._entry(room_box, "room_length", "Largo (m)", 1, 1)
        self._entry(room_box, "room_height", "Alto (m)", 2, 0)
        ttk.Button(room_box, text="Crear habitación", style="Primary.TButton",
                   command=self._create_room).grid(row=2, column=1, sticky="ew", padx=4, pady=(18, 3))

        furniture_box = ttk.LabelFrame(panel, text="2. Muebles", padding=8)
        furniture_box.grid(row=1, column=0, sticky="ew", pady=8)
        for column in (0, 1):
            furniture_box.columnconfigure(column, weight=1)
        self._entry(furniture_box, "furniture_name", "Nombre", 0, 0)
        self._entry(furniture_box, "furniture_width", "Ancho (m)", 1, 0)
        self._entry(furniture_box, "furniture_length", "Largo (m)", 1, 1)
        self._entry(furniture_box, "furniture_height", "Alto (m)", 2, 0)
        self._entry(furniture_box, "furniture_utility", "Utilidad (1–10)", 2, 1)
        self._entry(furniture_box, "furniture_quantity", "Cantidad", 3, 0)
        # Registra conexiones para equipos ubicados sobre el mueble.
        # Usa una etiqueta corta para evitar que el texto se corte.
        self._entry(furniture_box, "furniture_connections", "Conexiones eléctricas", 4, 0)
        # Permite decidir si el algoritmo puede girar este tipo de mueble.
        self.furniture_rotation = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            furniture_box, text="Permitir rotación automática (0° / 90°)",
            variable=self.furniture_rotation
        ).grid(row=4, column=1, sticky="w", padx=4, pady=3)
        self.furniture_use = self._combo(
            furniture_box, "Uso o propósito",
            ("Dormir", "Comer", "Cocinar", "Descansar", "Trabajar",
             "Almacenamiento", "Decoración", "Iluminación"), 3, 1
        )
        self.furniture_placement = self._combo(
            furniture_box, "Colocación", ("Suelo", "Sobre objeto", "Pared"), 5, 0
        )
        self.furniture_placement.bind(
            "<<ComboboxSelected>>", self._furniture_placement_changed
        )
        self.furniture_supports = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            furniture_box, text="Puede sostener objetos",
            variable=self.furniture_supports
        ).grid(row=5, column=1, sticky="w", padx=4, pady=(18, 3))
        self.furniture_wall = self._combo(
            furniture_box, "Pared", ("Automática", "Superior", "Inferior", "Izquierda", "Derecha"), 6, 0
        )
        self.furniture_wall.configure(state="disabled")
        self.furniture_wall_height = self._entry(
            furniture_box, "furniture_wall_height", "Altura inferior (m)", 6, 1
        )
        self.furniture_wall_height.configure(state="disabled")
        ttk.Label(furniture_box, text="Conexiones eléctricas: deje vacío si no necesita (0).",
                  style="Card.TLabel", wraplength=335, justify="left").grid(
                      row=7, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 3))
        ttk.Button(furniture_box, text="Agregar mueble(s)", style="Primary.TButton",
                   command=self._add_furniture).grid(row=8, column=0, columnspan=2, sticky="ew", padx=4, pady=5)

        restriction_box = ttk.LabelFrame(panel, text="3. Puertas y ventanas", padding=8)
        restriction_box.grid(row=2, column=0, sticky="ew", pady=8)
        for column in (0, 1, 2):
            restriction_box.columnconfigure(column, weight=1)
        self.restriction_type = self._combo(restriction_box, "Tipo", ("Puerta", "Ventana"), 0, 0)
        self.restriction_type.bind("<<ComboboxSelected>>", self._restriction_type_changed)
        self.restriction_wall = self._combo(
            restriction_box, "Pared", ("Superior", "Inferior", "Izquierda", "Derecha"), 0, 1
        )
        # Posicion libre en centimetros, propuesta para mejorar la interfaz con Dominic.
        self.restriction_offset = tk.DoubleVar(value=0.0)
        self.restriction_position_label = tk.StringVar(value="Distancia desde la esquina inicial: 0.00 m")
        self._entry(restriction_box, "restriction_width", "Ancho (m)", 1, 0)
        self._entry(restriction_box, "restriction_height", "Alto (m)", 1, 1)
        self.restriction_depth = self._entry(
            restriction_box, "restriction_depth", "Profundidad (m)", 1, 2
        )
        ttk.Label(restriction_box, text="Posición sobre la pared (deslizar)",
                  style="Card.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", padx=4)
        self.restriction_slider = ttk.Scale(
            restriction_box, from_=0, to=1, variable=self.restriction_offset,
            command=self._restriction_slider_changed
        )
        self.restriction_slider.grid(row=3, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
        ttk.Label(restriction_box, textvariable=self.restriction_position_label,
                  style="Card.TLabel", wraplength=340).grid(
                      row=4, column=0, columnspan=3, sticky="w", padx=4)
        self.restriction_precise = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            restriction_box, text="Usar posición exacta", variable=self.restriction_precise,
            command=self._toggle_restriction_precise
        ).grid(row=5, column=0, columnspan=3, sticky="w", padx=4, pady=3)
        self.restriction_exact_entry = self._entry(
            restriction_box, "restriction_exact_position", "Posición exacta (m)", 6, 0, 3
        )
        self.restriction_exact_entry.configure(state="disabled")
        self.entries["restriction_exact_position"].bind(
            "<KeyRelease>", self._restriction_exact_changed
        )
        # Una guia indica donde comienza la medida y donde quedara la abertura.
        self.restriction_guide_canvas = tk.Canvas(
            restriction_box, height=78, background="#FFFFFF", highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.restriction_guide_canvas.grid(row=7, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
        self.restriction_guide_canvas.bind("<Configure>", self._draw_restriction_guide)
        self.restriction_wall.bind("<<ComboboxSelected>>", self._update_restriction_slider)
        self.entries["restriction_width"].bind("<KeyRelease>", self._update_restriction_slider)
        ttk.Button(restriction_box, text="Agregar puerta o ventana", style="Primary.TButton",
                   command=self._add_restriction).grid(row=8, column=0, columnspan=3, sticky="ew", padx=4, pady=5)

        # Outlets propuestos conjuntamente por Raul y Dominic.
        outlet_box = ttk.LabelFrame(panel, text="4. Tomacorrientes", padding=8)
        outlet_box.grid(row=3, column=0, sticky="ew", pady=6)
        for column in (0, 1, 2):
            outlet_box.columnconfigure(column, weight=1)
        self._entry(outlet_box, "outlet_name", "Nombre", 0, 0)
        self.outlet_wall = self._combo(
            outlet_box, "Pared", ("Superior", "Inferior", "Izquierda", "Derecha"), 0, 1
        )
        # Explica desde que esquina se mide la distancia en cada pared.
        self.outlet_wall.bind("<<ComboboxSelected>>", self._update_outlet_guide)
        self._entry(outlet_box, "outlet_height", "Altura (m)", 1, 1)
        self._entry(outlet_box, "outlet_capacity", "Conexiones", 1, 2)
        self.outlet_offset = tk.DoubleVar(value=0.0)
        self.outlet_position_label = tk.StringVar(value="Distancia desde la esquina inicial: 0.00 m")
        ttk.Label(outlet_box, text="Posición sobre la pared (deslizar)",
                  style="Card.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", padx=4)
        self.outlet_slider = ttk.Scale(
            outlet_box, from_=0, to=1, variable=self.outlet_offset,
            command=self._outlet_slider_changed
        )
        self.outlet_slider.grid(row=3, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
        ttk.Label(outlet_box, textvariable=self.outlet_position_label,
                  style="Card.TLabel", wraplength=340).grid(
                      row=4, column=0, columnspan=3, sticky="w", padx=4)
        self.outlet_precise = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            outlet_box, text="Usar posición exacta", variable=self.outlet_precise,
            command=self._toggle_outlet_precise
        ).grid(row=5, column=0, columnspan=3, sticky="w", padx=4, pady=3)
        self.outlet_exact_entry = self._entry(
            outlet_box, "outlet_distance", "Posición exacta (m)", 6, 0, 3
        )
        self.outlet_exact_entry.configure(state="disabled")
        self.outlet_guide = tk.StringVar(value="Seleccione una pared para ver desde donde se mide.")
        ttk.Label(outlet_box, textvariable=self.outlet_guide, style="Card.TLabel",
                  wraplength=340, justify="left").grid(row=7, column=0, columnspan=3,
                                                       sticky="ew", padx=4, pady=(5, 2))
        # La guia muestra el inicio y el extremo de la pared elegida.
        self.outlet_guide_canvas = tk.Canvas(outlet_box, height=98, background="#FFFFFF",
                                             highlightthickness=1, highlightbackground="#CBD5E1")
        self.outlet_guide_canvas.grid(row=8, column=0, columnspan=3, sticky="ew", padx=4, pady=3)
        self.outlet_guide_canvas.bind("<Configure>", self._draw_outlet_guide)
        self.entries["outlet_distance"].bind("<KeyRelease>", self._outlet_exact_changed)
        ttk.Button(outlet_box, text="Agregar tomacorriente", style="Primary.TButton",
                   command=self._add_outlet).grid(row=9, column=0, columnspan=3, sticky="ew", padx=4, pady=4)

        actions = ttk.Frame(panel, style="Card.TFrame")
        actions.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        for column in (0, 1, 2):
            actions.columnconfigure(column, weight=1)
        # El botón ejecuta _generate cuando se pulsa.
        self.generate_button = ttk.Button(
            actions, text="Generar alternativas", style="Primary.TButton", command=self._generate
        )
        self.generate_button.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        ttk.Button(actions, text="Anterior", command=self._previous).grid(row=1, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(actions, text="Siguiente", command=self._next).grid(row=1, column=1, sticky="ew", padx=3)
        ttk.Button(actions, text="Guardar JSON", command=self._save).grid(row=1, column=2, sticky="ew", padx=(3, 0))

    # Crea el Canvas donde se dibuja la habitación.
    def _build_preview(self):
        self.preview_panel.columnconfigure(0, weight=1)
        self.preview_panel.rowconfigure(3, weight=1)
        self.preview_title = tk.StringVar(value="SIN HABITACIÓN")
        self.preview_iteration = tk.StringVar(value="Cree una habitación para comenzar")
        ttk.Label(self.preview_panel, textvariable=self.preview_title,
                  style="PreviewRoom.TLabel", anchor="center").grid(
                      row=0, column=0, sticky="ew", pady=(0, 1))
        ttk.Label(self.preview_panel, textvariable=self.preview_iteration,
                  style="PreviewIteration.TLabel", anchor="center").grid(
                      row=1, column=0, sticky="ew", pady=(0, 8))
        view_controls = ttk.Frame(self.preview_panel, style="Card.TFrame")
        view_controls.grid(row=2, column=0, pady=(0, 8))
        self.view_2d_button = ttk.Button(
            view_controls, text="Vista 2D", command=lambda: self._set_preview_mode("2D")
        )
        self.view_2d_button.grid(row=0, column=0, padx=3)
        self.view_3d_button = ttk.Button(
            view_controls, text="Vista 3D", command=lambda: self._set_preview_mode("3D")
        )
        self.view_3d_button.grid(row=0, column=1, padx=3)
        self.rotate_left_button = ttk.Button(
            view_controls, text="Girar izquierda", command=lambda: self._rotate_preview(-1)
        )
        self.rotate_left_button.grid(row=0, column=2, padx=(14, 3))
        self.rotate_right_button = ttk.Button(
            view_controls, text="Girar derecha", command=lambda: self._rotate_preview(1)
        )
        self.rotate_right_button.grid(row=0, column=3, padx=3)
        self.view_2d_button.state(["disabled"])
        self.rotate_left_button.state(["disabled"])
        self.rotate_right_button.state(["disabled"])
        self.preview = tk.Canvas(
            self.preview_panel, background="#FFFFFF", highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.preview.grid(row=3, column=0, sticky="nsew")
        # Programa el redibujado cuando cambia el tamaño.
        self.preview.bind("<Configure>", self._schedule_preview)
        self.preview.bind("<MouseWheel>", self._zoom_preview)
        self.preview.bind("<Button-4>", self._zoom_preview)
        self.preview.bind("<Button-5>", self._zoom_preview)
        self.preview.bind("<ButtonPress-1>", self._start_preview_pan)
        self.preview.bind("<B1-Motion>", self._pan_preview)
        self.preview.bind("<ButtonRelease-1>", self._finish_preview_pan)
        self.preview.bind("<Double-Button-1>", self._reset_preview_view)
        self.preview.configure(cursor="fleur")

    # Crea las listas desplazables de elementos.
    def _build_lists(self):
        self.list_panel.columnconfigure(0, weight=1)
        self.list_panel.rowconfigure(1, weight=1)
        self.list_panel.rowconfigure(3, weight=1)
        self.list_panel.rowconfigure(5, weight=1)
        ttk.Label(self.list_panel, text="Muebles agregados", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self.furniture_list = ScrollableList(self.list_panel)
        self.furniture_list.grid(row=1, column=0, sticky="nsew", pady=(0, 14))
        ttk.Label(self.list_panel, text="Puertas y ventanas", style="CardTitle.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )
        self.restriction_list = ScrollableList(self.list_panel)
        self.restriction_list.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        ttk.Label(self.list_panel, text="Tomacorrientes", style="CardTitle.TLabel").grid(
            row=4, column=0, sticky="w", pady=(0, 6)
        )
        self.outlet_list = ScrollableList(self.list_panel)
        self.outlet_list.grid(row=5, column=0, sticky="nsew")

    # Valida dimensiones positivas con precision maxima de un centimetro.
    @staticmethod
    def _positive(text, field_name):
        return TkinterInterface._centimeters(text, field_name)

    # Valida medidas en centimetros enteros sin redondear entradas invalidas.
    @staticmethod
    def _centimeters(text, field_name, allow_zero=False):
        from decimal import Decimal, InvalidOperation
        try:
            value = Decimal(text)
        except (InvalidOperation, TypeError) as error:
            raise ValueError(f"{field_name} debe ser numerico.") from error
        if not value.is_finite() or value < 0 or (value == 0 and not allow_zero):
            raise ValueError(f"{field_name} debe ser {'no negativo' if allow_zero else 'positivo'}.")
        if value * 100 != (value * 100).to_integral_value():
            raise ValueError(f"{field_name} admite como maximo dos decimales.")
        return float(value)

    # Convierte texto a entero o informa un valor inválido.
    @staticmethod
    def _integer(text, field_name):
        try:
            return int(text)
        except ValueError as error:
            raise ValueError(f"{field_name} debe ser un número entero.") from error

    # Evita aceptar campos de texto vacíos.
    @staticmethod
    def _required(text, field_name):
        value = text.strip()
        if not value:
            raise ValueError(f"Seleccione o escriba {field_name}.")
        return value

    # Obtiene y limpia el texto de un campo de entrada.
    def _entry_value(self, key):
        return self.entries[key].get().strip()

    # Vacía los campos indicados después de usarlos.
    def _clear_entries(self, *keys):
        for key in keys:
            self.entries[key].delete(0, tk.END)

    # Descarta alternativas antiguas tras modificar el proyecto.
    def _invalidate_distributions(self):
        # Almacena las alternativas generadas.
        self.distributions = []
        # Indica cuál alternativa se muestra.
        self.current_index = 0
        # Invalida las tareas anteriores al cambiar el proyecto.
        self.generation_token += 1

    # Actualiza el mensaje inferior y su color.
    def _set_status(self, message, error=False):
        self.status_var.set(message)
        self.status_label.configure(foreground="#B91C1C" if error else "#166534")

    # Valida los datos y crea o reemplaza la habitación.
    def _create_room(self):
        try:
            name = self._required(self._entry_value("room_name"), "el nombre")
            new_room = Habitacion(
                name,
                self._positive(self._entry_value("room_width"), "Ancho"),
                self._positive(self._entry_value("room_length"), "Largo"),
                self._positive(self._entry_value("room_height"), "Alto")
            )
            if self.room and (self.room.get_muebles() or self.room.get_restricciones() or self.room.get_outlets()):
                if not messagebox.askyesno(
                    "Reemplazar habitación",
                    "Crear otra habitación eliminará los elementos actuales. ¿Desea continuar?"
                ):
                    return
            self.room = new_room
            self._invalidate_distributions()
            self._refresh_lists()
            self.preview_zoom = 1.0
            self.preview_pan_x = 0.0
            self.preview_pan_y = 0.0
            self._draw_preview()
            self._update_restriction_slider()
            self._update_outlet_slider()
            self._set_status(f"Habitación '{name}' creada.")
        except ValueError as error:
            self._set_status(str(error), True)

    def _furniture_placement_changed(self, _event=None):
        wall_placement = self.furniture_placement.get() == "Pared"
        self.furniture_wall.configure(state="readonly" if wall_placement else "disabled")
        self.furniture_wall_height.configure(state="normal" if wall_placement else "disabled")
        if not wall_placement:
            self.furniture_wall.set("")
            self.furniture_wall_height.configure(state="normal")
            self._clear_entries("furniture_wall_height")
            self.furniture_wall_height.configure(state="disabled")

    # Valida y agrega la cantidad solicitada de muebles.
    def _add_furniture(self):
        if self.room is None:
            self._set_status("Primero cree una habitación.", True)
            return
        try:
            name = self._required(self._entry_value("furniture_name"), "el nombre del mueble")
            utility = self._integer(self._entry_value("furniture_utility"), "Utilidad")
            quantity = self._integer(self._entry_value("furniture_quantity"), "Cantidad")
            use = self._required(self.furniture_use.get(), "el uso del mueble")
            placement_type = self._required(
                self.furniture_placement.get(), "el tipo de colocación"
            )
            if placement_type == "Pared":
                preferred_wall = self._required(
                    self.furniture_wall.get(), "la pared del mueble"
                )
                wall_height = self._centimeters(
                    self._entry_value("furniture_wall_height"), "Altura inferior", True
                )
            else:
                preferred_wall = "Automática"
                wall_height = 0.0
            if not 1 <= utility <= 10:
                raise ValueError("La utilidad debe estar entre 1 y 10.")
            if quantity <= 0:
                raise ValueError("La cantidad debe ser mayor que cero.")
            # Las conexiones son opcionales y cero significa sin electricidad.
            connections_text = self._entry_value("furniture_connections")
            connections = self._integer(connections_text, "Conexiones") if connections_text else 0
            if connections < 0:
                raise ValueError("Las conexiones no pueden ser negativas.")
            dimensions = (
                self._positive(self._entry_value("furniture_width"), "Ancho"),
                self._positive(self._entry_value("furniture_length"), "Largo"),
                self._positive(self._entry_value("furniture_height"), "Alto")
            )
            # Crea tantos muebles como indique la cantidad.
            for number in range(1, quantity + 1):
                item_name = name if quantity == 1 else f"{name} {number}"
                self.room.agregar_mueble(
                    Mueble(item_name, *dimensions, utility, Punto3D(0, 0, 0), use,
                           conexiones_necesarias=connections,
                           permite_rotacion=self.furniture_rotation.get(),
                           placement_type=placement_type,
                           supports_objects=self.furniture_supports.get(),
                           preferred_wall=preferred_wall,
                           wall_height=wall_height)
                )
            self._invalidate_distributions()
            self._clear_entries(
                "furniture_name", "furniture_width", "furniture_length",
                "furniture_height", "furniture_utility", "furniture_quantity", "furniture_connections"
            )
            self.furniture_use.set("")
            self.furniture_rotation.set(True)
            self.furniture_placement.set("")
            self.furniture_supports.set(False)
            self.furniture_wall.set("")
            self.furniture_wall_height.configure(state="normal")
            self._clear_entries("furniture_wall_height")
            self.furniture_wall.configure(state="disabled")
            self.furniture_wall_height.configure(state="disabled")
            self._refresh_lists()
            self._draw_preview()
            self._set_status(f"Se agregaron {quantity} mueble(s). {self._electrical_warning()}")
        except ValueError as error:
            self._set_status(str(error), True)

    # Habilita la profundidad solo cuando corresponde.
    def _restriction_type_changed(self, _event=None):
        if self.restriction_type.get() == "Puerta":
            self.restriction_depth.delete(0, tk.END)
            self.restriction_depth.configure(state="disabled")
        else:
            self.restriction_depth.configure(state="normal")

    # Calcula la distancia maxima segun pared y ancho de la abertura.
    def _restriction_limit(self):
        if self.room is None:
            return 0.0
        wall = self.restriction_wall.get()
        if wall not in ("Superior", "Inferior", "Izquierda", "Derecha"):
            return 0.0
        length = self.room.ancho if wall in ("Superior", "Inferior") else self.room.largo
        try:
            width = self._positive(self._entry_value("restriction_width"), "Ancho")
        except ValueError:
            return 0.0
        return max(0.0, round(length - width, 2))

    # Actualiza los limites del deslizador al cambiar pared o ancho.
    def _update_restriction_slider(self, _event=None):
        limit = self._restriction_limit()
        self.restriction_slider.configure(to=max(limit, 0.01))
        self.restriction_offset.set(min(self.restriction_offset.get(), limit))
        self._restriction_slider_changed()

    def _toggle_restriction_precise(self):
        precise = self.restriction_precise.get()
        self.restriction_slider.configure(state="disabled" if precise else "normal")
        self.restriction_exact_entry.configure(state="normal" if precise else "disabled")
        if precise:
            self.restriction_exact_entry.delete(0, tk.END)
            self.restriction_exact_entry.insert(0, f"{self.restriction_offset.get():.2f}")
            self.restriction_exact_entry.focus_set()
        self._draw_restriction_guide()

    def _restriction_exact_changed(self, _event=None):
        if not self.restriction_precise.get():
            return
        try:
            value = self._centimeters(
                self._entry_value("restriction_exact_position"), "Posición exacta", True
            )
        except ValueError:
            return
        limit = self._restriction_limit()
        self.restriction_offset.set(min(value, limit))
        self._restriction_slider_changed()

    def _selected_restriction_offset(self):
        limit = self._restriction_limit()
        if self.restriction_precise.get():
            value = self._centimeters(
                self._entry_value("restriction_exact_position"), "Posición exacta", True
            )
            if value > limit:
                raise ValueError(f"La posición exacta debe estar entre 0 y {limit:.2f} m.")
            return value
        return min(max(round(self.restriction_offset.get() * 100) / 100, 0.0), limit)

    # Ajusta la posicion al centimetro mas cercano.
    def _restriction_slider_changed(self, _value=None):
        limit = self._restriction_limit()
        value = min(max(round(self.restriction_offset.get() * 100) / 100, 0.0), limit)
        self.restriction_position_label.set(
            f"Desde la esquina inicial: {value:.2f} m (máximo {limit:.2f} m)"
        )
        self._draw_restriction_guide()

    # Muestra la longitud de pared y la posicion de la abertura.
    def _draw_restriction_guide(self, _event=None):
        if not hasattr(self, "restriction_guide_canvas"):
            return
        canvas = self.restriction_guide_canvas
        canvas.delete("all")
        width_px = max(canvas.winfo_width(), 200)
        wall = self.restriction_wall.get()
        if self.room is None or wall not in ("Superior", "Inferior", "Izquierda", "Derecha"):
            canvas.create_text(width_px / 2, 38, text="Cree una habitación y elija una pared",
                               fill="#64748B")
            return
        length = self.room.ancho if wall in ("Superior", "Inferior") else self.room.largo
        try:
            opening = self._positive(self._entry_value("restriction_width"), "Ancho")
        except ValueError:
            canvas.create_text(width_px / 2, 38, text="Introduzca el ancho de la abertura",
                               fill="#64748B")
            return
        if opening > length:
            canvas.create_text(width_px / 2, 38, text="El ancho supera la longitud de la pared",
                               fill="#B91C1C")
            return
        start, end, y = 28, width_px - 28, 30
        canvas.create_line(start, y, end, y, fill="#0F172A", width=4)
        offset = min(round(self.restriction_offset.get() * 100) / 100, self._restriction_limit())
        x1 = start + (end - start) * offset / length
        x2 = start + (end - start) * (offset + opening) / length
        canvas.create_line(x1, y, x2, y, fill="#F59E0B", width=9)
        canvas.create_text(start, y + 23, text="Inicio: 0 m", anchor="w", fill="#166534")
        canvas.create_text(end, y + 23, text=f"Final: {length:g} m", anchor="e", fill="#64748B")

    # Valida y agrega una puerta o ventana en una posicion libre.
    def _add_restriction(self):
        if self.room is None:
            self._set_status("Primero cree una habitación.", True)
            return
        try:
            restriction_type = self._required(self.restriction_type.get(), "el tipo")
            wall = self._required(self.restriction_wall.get(), "la pared")
            width = self._positive(self._entry_value("restriction_width"), "Ancho")
            depth = width if restriction_type == "Puerta" else self._positive(
                self._entry_value("restriction_depth"), "Profundidad"
            )
            height = self._positive(self._entry_value("restriction_height"), "Alto")
            # La clase Restriccion conserva la validacion de medidas.
            restriction = Restriccion.crear_desde_pared(
                self.room, restriction_type, wall, "Personalizada", width, height, depth
            )
            offset = self._selected_restriction_offset()
            if wall == "Superior":
                x, y = offset, 0.0
            elif wall == "Inferior":
                x, y = offset, self.room.largo - restriction.profundidad
            elif wall == "Izquierda":
                x, y = 0.0, offset
            else:
                x, y = self.room.ancho - restriction.profundidad, offset
            restriction.posicion = Punto3D(round(x, 2), round(y, 2), 0.0)
            self.room.agregar_restriccion(restriction)
            self._invalidate_distributions()
            self._clear_entries("restriction_width", "restriction_height")
            self.restriction_depth.configure(state="normal")
            self._clear_entries("restriction_depth")
            self.restriction_type.set("")
            self.restriction_wall.set("")
            self.restriction_offset.set(0.0)
            self.restriction_precise.set(False)
            self.restriction_slider.configure(state="normal")
            self.restriction_exact_entry.configure(state="normal")
            self._clear_entries("restriction_exact_position")
            self.restriction_exact_entry.configure(state="disabled")
            self._update_restriction_slider()
            self._refresh_lists()
            self._draw_preview()
            detail = "apertura igual al ancho" if restriction_type == "Puerta" else f"profundidad {depth:g} m"
            self._set_status(f"{restriction_type} agregada en pared {wall} a {offset:.2f} m; {detail}.")
        except ValueError as error:
            self._set_status(str(error), True)

    # Explica la direccion de medida de la pared seleccionada.
    def _update_outlet_guide(self, _event=None):
        wall = self.outlet_wall.get()
        if wall in ("Superior", "Inferior"):
            direction = "desde la esquina izquierda hacia la derecha"
            limit = self.room.ancho if self.room else None
        elif wall in ("Izquierda", "Derecha"):
            direction = "desde la esquina superior hacia abajo"
            limit = self.room.largo if self.room else None
        else:
            self.outlet_guide.set("Seleccione una pared para ver desde donde se mide.")
            self._update_outlet_slider()
            return
        maximum = f" Longitud de la pared: {limit:g} m." if limit is not None else ""
        self.outlet_guide.set(f"Mida {direction}.{maximum} Puede usar centimetros (ej. 2.35 m).")
        self._update_outlet_slider()

    def _outlet_limit(self):
        if self.room is None:
            return 0.0
        wall = self.outlet_wall.get()
        if wall in ("Superior", "Inferior"):
            return self.room.ancho
        if wall in ("Izquierda", "Derecha"):
            return self.room.largo
        return 0.0

    def _update_outlet_slider(self, _event=None):
        limit = self._outlet_limit()
        self.outlet_slider.configure(to=max(limit, 0.01))
        self.outlet_offset.set(min(self.outlet_offset.get(), limit))
        self._outlet_slider_changed()

    def _outlet_slider_changed(self, _value=None):
        limit = self._outlet_limit()
        value = min(max(round(self.outlet_offset.get() * 100) / 100, 0.0), limit)
        self.outlet_position_label.set(
            f"Desde la esquina inicial: {value:.2f} m (máximo {limit:.2f} m)"
        )
        self._draw_outlet_guide()

    def _toggle_outlet_precise(self):
        precise = self.outlet_precise.get()
        self.outlet_slider.configure(state="disabled" if precise else "normal")
        self.outlet_exact_entry.configure(state="normal" if precise else "disabled")
        if precise:
            self.outlet_exact_entry.delete(0, tk.END)
            self.outlet_exact_entry.insert(0, f"{self.outlet_offset.get():.2f}")
            self.outlet_exact_entry.focus_set()
        self._draw_outlet_guide()

    def _outlet_exact_changed(self, _event=None):
        if not self.outlet_precise.get():
            return
        try:
            value = self._centimeters(
                self._entry_value("outlet_distance"), "Posición exacta", True
            )
        except ValueError:
            return
        self.outlet_offset.set(min(value, self._outlet_limit()))
        self._outlet_slider_changed()

    def _selected_outlet_distance(self):
        limit = self._outlet_limit()
        if self.outlet_precise.get():
            value = self._centimeters(
                self._entry_value("outlet_distance"), "Posición exacta", True
            )
            if value > limit:
                raise ValueError(f"La posición exacta debe estar entre 0 y {limit:.2f} m.")
            return value
        return min(max(round(self.outlet_offset.get() * 100) / 100, 0.0), limit)

    # Dibuja la pared, el punto inicial y la ubicacion estimada del outlet.
    def _draw_outlet_guide(self, _event=None):
        if not hasattr(self, "outlet_guide_canvas"):
            return
        canvas = self.outlet_guide_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 200)
        wall = self.outlet_wall.get()
        if wall not in ("Superior", "Inferior", "Izquierda", "Derecha"):
            canvas.create_text(width / 2, 45, text="Seleccione una pared", fill="#64748B")
            return
        # La guia es esquematica; la posicion real usa las dimensiones de la habitacion.
        start, end, y = 32, width - 32, 44
        canvas.create_line(start, y, end, y, fill="#0F172A", width=5)
        canvas.create_oval(start - 6, y - 6, start + 6, y + 6,
                           fill="#16A34A", outline="#166534")
        canvas.create_text(start, y + 22, text="0 m (inicio)", anchor="w",
                           fill="#166534", font=("Segoe UI", 8))
        limit = (self.room.ancho if wall in ("Superior", "Inferior")
                 else self.room.largo) if self.room else None
        canvas.create_text(end, y + 22, text=f"{limit:g} m (final)" if limit else "Final",
                           anchor="e", fill="#64748B", font=("Segoe UI", 8))
        distance = min(self.outlet_offset.get(), limit) if limit is not None else None
        if distance is not None and limit and distance <= limit:
            x = start + (end - start) * distance / limit
            canvas.create_oval(x - 9, y - 9, x + 9, y + 9,
                               fill="#FDE68A", outline="#92400E", width=2)
            # Dos ranuras distinguen el outlet de un punto cualquiera.
            canvas.create_line(x - 3, y - 4, x - 3, y + 4, fill="#92400E", width=2)
            canvas.create_line(x + 3, y - 4, x + 3, y + 4, fill="#92400E", width=2)
        canvas.create_text(width / 2, 12, text=f"Pared {wall.lower()} - vista desde arriba",
                           fill="#334155", font=("Segoe UI", 9))

    # Agrega un outlet sobre la pared y a la altura indicada.
    def _add_outlet(self):
        if self.room is None:
            self._set_status("Primero cree una habitación.", True)
            return
        try:
            name = self._required(self._entry_value("outlet_name"), "el nombre del outlet")
            wall = self._required(self.outlet_wall.get(), "la pared del outlet")
            distance = self._selected_outlet_distance()
            height = self._centimeters(self._entry_value("outlet_height"), "Altura", True)
            capacity = self._integer(self._entry_value("outlet_capacity"), "Conexiones")
            # Comprueba que la distancia no exceda la longitud de la pared.
            limit = self.room.ancho if wall in ("Superior", "Inferior") else self.room.largo
            if distance > limit:
                raise ValueError(f"La distancia debe estar entre 0 y {limit:g} m.")
            # Las paredes horizontales usan X y las verticales usan Y.
            if wall == "Superior":
                position = Punto3D(distance, 0, height)
            elif wall == "Inferior":
                position = Punto3D(distance, self.room.largo, height)
            elif wall == "Izquierda":
                position = Punto3D(0, distance, height)
            else:
                position = Punto3D(self.room.ancho, distance, height)
            self.room.agregar_outlet(Outlet(name, wall, position, capacity))
            self._invalidate_distributions()
            self._clear_entries("outlet_name", "outlet_distance", "outlet_height", "outlet_capacity")
            self.outlet_wall.set("")
            self.outlet_offset.set(0.0)
            self.outlet_precise.set(False)
            self.outlet_slider.configure(state="normal")
            self.outlet_exact_entry.configure(state="disabled")
            self._update_outlet_slider()
            self._refresh_lists()
            self._draw_preview()
            self._set_status(f"Outlet '{name}' agregado. {self._electrical_warning()}")
        except (ValueError, TypeError) as error:
            self._set_status(str(error), True)

    # Resume las conexiones insuficientes sin bloquear la generacion.
    def _electrical_warning(self):
        if self.room is None:
            return ""
        missing = self.room.conexiones_faltantes()
        return f"Advertencia: faltan {missing} conexion(es)." if missing else "Conexiones suficientes."

    # Reconstruye las listas con los elementos actuales.
    def _refresh_lists(self):
        # Elimina las filas anteriores antes de actualizar.
        self.furniture_list.clear()
        self.restriction_list.clear()
        self.outlet_list.clear()
        furniture = self.room.get_muebles() if self.room else []
        restrictions = self.room.get_restricciones() if self.room else []
        outlets = self.room.get_outlets() if self.room else []
        self._populate_list(
            self.furniture_list, furniture,
            lambda item: (f"{item.nombre}\n{item.uso} · {item.ancho:g} × {item.largo:g} × {item.alto:g} m"
                          f"\n{item.get_placement_type()} · Sostiene objetos: "
                          f"{'sí' if item.can_support_objects() else 'no'}"),
            self._delete_furniture, "No hay muebles agregados.", self._edit_furniture
        )
        self._populate_list(
            self.restriction_list, restrictions,
            lambda item: f"{item.tipo}\n{item.pared} · {item.seccion} · {item.ancho:g} m",
            self._delete_restriction, "No hay puertas ni ventanas."
        )
        self._populate_list(
            self.outlet_list, outlets,
            lambda item: f"{item.nombre}\n{item.pared} · {item.capacidad} conexion(es)",
            self._delete_outlet, "No hay outlets agregados."
        )

    # Crea las filas y botones para borrar elementos.
    def _populate_list(self, target, items, description, delete_callback, empty_message, edit_callback=None):
        target.content.columnconfigure(0, weight=1)
        if not items:
            ttk.Label(target.content, text=empty_message, style="ListText.TLabel",
                      anchor="center").grid(row=0, column=0, sticky="ew", padx=8, pady=18)
            return
        # Recorre cada elemento junto con su índice.
        for index, item in enumerate(items):
            row = ttk.Frame(target.content, style="List.TFrame", padding=(8, 5))
            row.grid(row=index * 2, column=0, sticky="ew")
            row.columnconfigure(0, weight=1)
            # El nombre del mueble abre su edicion; las otras listas siguen igual.
            if edit_callback is not None:
                ttk.Button(row, text=description(item),
                           command=lambda i=index: edit_callback(i)).grid(
                               row=0, column=0, sticky="ew", padx=(0, 4))
            else:
                ttk.Label(row, text=description(item), style="ListText.TLabel",
                          justify="left").grid(row=0, column=0, sticky="w")
            ttk.Button(row, text="×", width=3, style="Delete.TButton",
                       command=lambda i=index: delete_callback(i)).grid(row=0, column=1, padx=(6, 0))
            ttk.Separator(target.content).grid(row=index * 2 + 1, column=0, sticky="ew")

    # Abre una ventana para modificar un mueble sin borrarlo.
    def _edit_furniture(self, index):
        if self.room is None or not 0 <= index < len(self.room.get_muebles()):
            return
        original = self.room.get_muebles()[index]
        window = tk.Toplevel(self.root)
        window.title(f"Editar mueble - {original.nombre}")
        window.geometry("460x640")
        window.minsize(390, 520)
        window.transient(self.root)
        window.grab_set()

        # El formulario tiene scroll para no ocultar los campos inferiores.
        canvas = tk.Canvas(window, highlightthickness=0)
        scrollbar = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        panel = ttk.Frame(canvas, padding=14)
        panel_id = canvas.create_window((0, 0), window=panel, anchor="nw")
        panel.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(panel_id, width=e.width))
        panel.columnconfigure(1, weight=1)
        fields = {}

        # Rellena cada entrada con el valor actual del objeto.
        def field(label, key, value, row):
            ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w", pady=5)
            entry = ttk.Entry(panel)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=5)
            fields[key] = entry

        field("Nombre", "nombre", original.nombre, 0)
        field("Ancho (m)", "ancho", original.ancho, 1)
        field("Largo (m)", "largo", original.largo, 2)
        field("Alto (m)", "alto", original.alto, 3)
        field("Utilidad (1-10)", "utilidad", original.utilidad, 4)
        field("Conexiones", "conexiones", original.get_conexiones_necesarias(), 5)
        field("Altura en pared (m)", "altura", original.get_wall_height(), 6)

        ttk.Label(panel, text="Uso").grid(row=7, column=0, sticky="w", pady=5)
        use = ttk.Combobox(panel, values=("Dormir", "Comer", "Cocinar", "Descansar",
                                           "Trabajar", "Almacenamiento", "Decoración", "Iluminación"))
        use.set(original.get_uso())
        use.grid(row=7, column=1, sticky="ew", padx=(8, 0), pady=5)

        ttk.Label(panel, text="Colocación").grid(row=8, column=0, sticky="w", pady=5)
        placement = ttk.Combobox(panel, state="readonly", values=Mueble.VALID_PLACEMENT_TYPES)
        placement.set(original.get_placement_type())
        placement.grid(row=8, column=1, sticky="ew", padx=(8, 0), pady=5)

        ttk.Label(panel, text="Pared preferida").grid(row=9, column=0, sticky="w", pady=5)
        wall = ttk.Combobox(panel, state="readonly", values=Mueble.VALID_WALLS)
        wall.set(original.get_preferred_wall())
        wall.grid(row=9, column=1, sticky="ew", padx=(8, 0), pady=5)

        rotate = tk.BooleanVar(value=original.puede_rotar())
        support = tk.BooleanVar(value=original.can_support_objects())
        ttk.Checkbutton(panel, text="Permitir rotación automática", variable=rotate).grid(
            row=10, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Checkbutton(panel, text="Puede sostener objetos", variable=support).grid(
            row=11, column=0, columnspan=2, sticky="w", pady=5)

        # Evita introducir opciones de pared cuando el mueble no va en pared.
        def update_wall(*_args):
            enabled = placement.get() == "Pared"
            wall.configure(state="readonly" if enabled else "disabled")
            fields["altura"].configure(state="normal" if enabled else "disabled")
        placement.bind("<<ComboboxSelected>>", update_wall)
        update_wall()

        # Valida una copia antes de cambiar el mueble original.
        def save_changes():
            try:
                name = self._required(fields["nombre"].get(), "el nombre")
                width = self._centimeters(fields["ancho"].get(), "Ancho")
                length = self._centimeters(fields["largo"].get(), "Largo")
                height = self._centimeters(fields["alto"].get(), "Alto")
                utility = self._integer(fields["utilidad"].get(), "Utilidad")
                connections = self._integer(fields["conexiones"].get(), "Conexiones")
                if not 1 <= utility <= 10:
                    raise ValueError("La utilidad debe estar entre 1 y 10.")
                if connections < 0:
                    raise ValueError("Las conexiones no pueden ser negativas.")
                selected_use = self._required(use.get(), "el uso")
                selected_placement = self._required(placement.get(), "la colocación")
                selected_wall = wall.get() if selected_placement == "Pared" else "Automática"
                wall_height = (self._centimeters(fields["altura"].get(), "Altura inferior", True)
                               if selected_placement == "Pared" else 0.0)
                if selected_placement == "Pared" and wall_height + height > self.room.alto:
                    raise ValueError("El mueble supera la altura de la habitación.")

                # Construye el candidato completo para evitar cambios parciales.
                candidate = Mueble(
                    name, width, length, height, utility,
                    copy.deepcopy(original.posicion), selected_use,
                    conexiones_necesarias=connections,
                    permite_rotacion=rotate.get(),
                    placement_type=selected_placement,
                    supports_objects=support.get(),
                    preferred_wall=selected_wall,
                    wall_height=wall_height
                )
                # Conserva la orientación anterior si el nuevo permiso lo permite.
                candidate.set_rotacion(original.get_rotacion())
                # La lista original se actualiza solo después de validar todo.
                self.room.get_muebles()[index] = candidate
                self._invalidate_distributions()
                self._refresh_lists()
                self._draw_preview()
                self._set_status(f"Mueble '{name}' actualizado. Genere nuevas alternativas. "
                                 f"{self._electrical_warning()}")
                window.destroy()
            except (ValueError, TypeError) as error:
                messagebox.showerror("No se pudo editar el mueble", str(error), parent=window)

        buttons = ttk.Frame(panel)
        buttons.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(12, 4))
        ttk.Button(buttons, text="Guardar cambios", command=save_changes).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Cancelar", command=window.destroy).pack(side="left")

    # Elimina un mueble y actualiza la vista.
    def _delete_furniture(self, index):
        item = self.room.get_muebles()[index]
        self.room.eliminar_mueble(item)
        self._invalidate_distributions()
        self._refresh_lists()
        self._draw_preview()
        self._set_status(f"Mueble '{item.nombre}' eliminado.")

    # Elimina una restricción y actualiza la vista.
    def _delete_restriction(self, index):
        item = self.room.get_restricciones()[index]
        self.room.eliminar_restriccion(item)
        self._invalidate_distributions()
        self._refresh_lists()
        self._draw_preview()
        self._set_status(f"{item.tipo} de la pared {item.pared} eliminada.")

 
    # Elimina un outlet y actualiza las alternativas.
    def _delete_outlet(self, index):
        item = self.room.get_outlets()[index]
        self.room.eliminar_outlet(item)
        self._invalidate_distributions()
        self._refresh_lists()
        self._draw_preview()
        self._set_status(f"Outlet '{item.nombre}' eliminado. {self._electrical_warning()}")

    # Valida el espacio y lanza la generación en otro hilo.
    def _generate(self):
        # Mide el tiempo previo a iniciar el hilo.
        inicio = perf_counter()

        if self.room is None:
            self._set_status("Primero cree una habitación.", True)
            return

        if not Distribucion.verificar_espacio(self.room):
            self._set_status("Los muebles exceden el espacio disponible.", True)
            return

        print(f"[TIEMPO] Validación: {perf_counter() - inicio:.4f} s")

        # Guarda la versión del proyecto que se está procesando.
        token = self.generation_token

        # Mide cuánto tarda copiar la habitación.
        inicio_copia = perf_counter()
        # Copia el proyecto para no modificarlo durante el cálculo.
        room_copy = copy.deepcopy(self.room)
        print(f"[TIEMPO] Copia: {perf_counter() - inicio_copia:.4f} s")

        # Crea una cola para recibir un único resultado del hilo.
        self.generation_queue = queue.Queue(maxsize=1)
        self.generate_button.state(["disabled"])
        self._set_status("Generando alternativas…")

        # Ejecuta el cálculo en un hilo secundario.
        threading.Thread(
            target=self._generate_worker,
            args=(room_copy, token),
            daemon=True
        ).start()

        # Revisa la cola desde el hilo de la interfaz.
        self.root.after(50, self._poll_generation)
        print(f"[TIEMPO] Inicio de generación: {perf_counter() - inicio:.4f} s")



    # Calcula las alternativas sin usar widgets de Tkinter.
    def _generate_worker(self, room, token):
        # Mide la generación matemática en el hilo secundario.
        inicio = perf_counter()

        try:
            if not room.get_muebles():
                distribution = Distribucion(room)
                distribution.validar()
                distribution.calcular_puntaje()
                results = [distribution]
            else:
                # Solicita candidatos y conserva hasta tres alternativas.
                results = Distribucion.generar_distribuciones(
                    room, amount=300, limite_resultados=3
                )

            print(f"[TIEMPO] Algoritmo: {perf_counter() - inicio:.4f} s")
            # Envía resultados y versión a la interfaz.
            self.generation_queue.put((results, token, None))

        except Exception as error:
            print(f"[ERROR] Generación: {error}")
            # Envía el error para mostrarlo sin cerrar la ventana.
            self.generation_queue.put(([], token, str(error)))


    # Consulta la cola sin bloquear la ventana.
    def _poll_generation(self):
        try:
            # Lee la cola sin esperar si aún está vacía.
            results, token, error = self.generation_queue.get_nowait()
        except queue.Empty:
            self.root.after(50, self._poll_generation)
            return
        self._finish_generation(results, token, error)

    # Recibe los resultados y actualiza la interfaz.
    def _finish_generation(self, results, token, error):
        self.generate_button.state(["!disabled"])
        # Ignora resultados que ya no corresponden al proyecto.
        if token != self.generation_token:
            return
        if error:
            self._set_status(f"No se pudieron generar alternativas: {error}", True)
            return
        if not results:
            self._set_status("No se encontró una distribución válida.", True)
            return
        self.distributions = results
        # Indica cuál alternativa se muestra.
        self.current_index = 0
        # Mide el tiempo que tarda el dibujo.
        inicio_dibujo = perf_counter()
        self._draw_preview()
        print(f"[TIEMPO] Dibujo: {perf_counter() - inicio_dibujo:.4f} s")
        self._set_status(f"{len(results)} alternativa(s) generada(s). {self._electrical_warning()}")

    # Muestra la alternativa anterior, si existe.
    def _previous(self):
        if self.distributions:
            self.current_index = (self.current_index - 1) % len(self.distributions)
            self._draw_preview()

    # Muestra la alternativa siguiente, si existe.
    def _next(self):
        if self.distributions:
            self.current_index = (self.current_index + 1) % len(self.distributions)
            self._draw_preview()

    # Solicita una ruta y guarda el proyecto en JSON.
    def _save(self):
        if self.room is None:
            self._set_status("No hay una habitación para guardar.", True)
            return
        filename = filedialog.asksaveasfilename(
            title="Guardar proyecto", defaultextension=".json",
            filetypes=(("Proyecto JSON", "*.json"), ("Todos los archivos", "*.*"))
        )
        if not filename:
            return
        if guardar_proyecto(self.room, filename):
            self._set_status(f"Proyecto guardado en {filename}.")
        else:
            self._set_status("No se pudo guardar el proyecto.", True)

    # Agrupa eventos de cambio de tamaño antes de dibujar.
    def _schedule_preview(self, _event=None):
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(50, self._draw_preview)

    def _set_preview_mode(self, mode):
        if mode not in ("2D", "3D") or mode == self.preview_mode:
            return
        self.preview_mode = mode
        self.view_2d_button.state(["disabled"] if mode == "2D" else ["!disabled"])
        self.view_3d_button.state(["disabled"] if mode == "3D" else ["!disabled"])
        rotation_state = ["!disabled"] if mode == "3D" else ["disabled"]
        self.rotate_left_button.state(rotation_state)
        self.rotate_right_button.state(rotation_state)
        self._reset_preview_view()

    def _rotate_preview(self, direction):
        if self.preview_mode != "3D":
            return
        self.preview_rotation = (self.preview_rotation + direction) % 4
        self._reset_preview_view()

    @staticmethod
    def _bounded_origin(origin, item_size, viewport_size, minimum_visible=80):
        lower = minimum_visible - item_size
        upper = viewport_size - minimum_visible
        if lower > upper:
            return (viewport_size - item_size) / 2
        return min(max(origin, lower), upper)

    def _cancel_preview_snap(self):
        if self.preview_snap_job is not None:
            self.root.after_cancel(self.preview_snap_job)
            self.preview_snap_job = None

    def _schedule_preview_snap(self):
        self._cancel_preview_snap()
        self.preview_snap_job = self.root.after(2500, self._reset_preview_view)

    def _reset_preview_view(self, _event=None):
        self.preview_snap_job = None
        self.preview_zoom = 1.0
        self.preview_pan_x = 0.0
        self.preview_pan_y = 0.0
        self.preview_drag_start = None
        self.preview_pan_start = None
        self._draw_preview()

    def _zoom_preview(self, event):
        if self.room is None:
            return "break"
        self._cancel_preview_snap()
        if self.preview_geometry is None:
            self._draw_preview()
        geometry = self.preview_geometry
        zoom_in = getattr(event, "delta", 0) > 0 or getattr(event, "num", None) == 4
        factor = 1.12 if zoom_in else 1 / 1.12
        new_zoom = min(max(self.preview_zoom * factor, 0.70), 4.0)
        if new_zoom == self.preview_zoom or geometry is None:
            return "break"
        old_scale = geometry["scale"]
        world_x = (event.x - geometry["origin_x"]) / old_scale
        world_y = (event.y - geometry["origin_y"]) / old_scale
        new_scale = geometry["base_scale"] * new_zoom
        centered_x = (
            geometry["width"] / 2
            - (geometry["raw_min_x"] + geometry["raw_width"] / 2) * new_scale
        )
        centered_y = (
            geometry["height"] / 2
            - (geometry["raw_min_y"] + geometry["raw_height"] / 2) * new_scale
        )
        self.preview_zoom = new_zoom
        self.preview_pan_x = event.x - world_x * new_scale - centered_x
        self.preview_pan_y = event.y - world_y * new_scale - centered_y
        self._draw_preview()
        self._schedule_preview_snap()
        return "break"

    def _start_preview_pan(self, event):
        if self.room is None:
            return
        self._cancel_preview_snap()
        self.preview_drag_start = (event.x, event.y)
        self.preview_pan_start = (self.preview_pan_x, self.preview_pan_y)

    def _pan_preview(self, event):
        if self.preview_drag_start is None:
            return
        self.preview_pan_x = self.preview_pan_start[0] + event.x - self.preview_drag_start[0]
        self.preview_pan_y = self.preview_pan_start[1] + event.y - self.preview_drag_start[1]
        self._draw_preview()

    def _finish_preview_pan(self, _event=None):
        if self.preview_drag_start is None:
            return
        self.preview_drag_start = None
        self.preview_pan_start = None
        self._schedule_preview_snap()

    @staticmethod
    def _shade_color(color, factor):
        value = color.lstrip("#")
        channels = [int(value[index:index + 2], 16) for index in (0, 2, 4)]
        adjusted = [min(255, max(0, round(channel * factor))) for channel in channels]
        return "#" + "".join(f"{channel:02X}" for channel in adjusted)

    def _draw_preview_3d(self, canvas, width, height, room, furniture, score):
        rotation = self.preview_rotation % 4

        def rotate_xy(x, y):
            if rotation == 0:
                return x, y
            if rotation == 1:
                return y, room.ancho - x
            if rotation == 2:
                return room.ancho - x, room.largo - y
            return room.largo - y, x

        def raw_project(x, y, z=0.0):
            rotated_x, rotated_y = rotate_xy(x, y)
            return (
                (rotated_x - rotated_y) * 0.8660254,
                (rotated_x + rotated_y) * 0.5 - z * 0.9
            )

        room_corners = [
            raw_project(x, y, z)
            for x in (0.0, room.ancho)
            for y in (0.0, room.largo)
            for z in (0.0, room.alto)
        ]
        raw_min_x = min(point[0] for point in room_corners)
        raw_max_x = max(point[0] for point in room_corners)
        raw_min_y = min(point[1] for point in room_corners)
        raw_max_y = max(point[1] for point in room_corners)
        raw_width = max(raw_max_x - raw_min_x, 0.01)
        raw_height = max(raw_max_y - raw_min_y, 0.01)
        margin = 92
        base_scale = min(
            max(width - 2 * margin, 20) / raw_width,
            max(height - 2 * margin, 20) / raw_height
        )
        scale = base_scale * self.preview_zoom
        centered_origin_x = width / 2 - (raw_min_x + raw_width / 2) * scale
        centered_origin_y = height / 2 - (raw_min_y + raw_height / 2) * scale
        left = centered_origin_x + self.preview_pan_x + raw_min_x * scale
        top = centered_origin_y + self.preview_pan_y + raw_min_y * scale
        left = self._bounded_origin(left, raw_width * scale, width)
        top = self._bounded_origin(top, raw_height * scale, height)
        origin_x = left - raw_min_x * scale
        origin_y = top - raw_min_y * scale
        self.preview_pan_x = origin_x - centered_origin_x
        self.preview_pan_y = origin_y - centered_origin_y
        self.preview_geometry = {
            "width": width, "height": height, "base_scale": base_scale, "scale": scale,
            "origin_x": origin_x, "origin_y": origin_y,
            "raw_min_x": raw_min_x, "raw_min_y": raw_min_y,
            "raw_width": raw_width, "raw_height": raw_height
        }

        def project(x, y, z=0.0):
            raw_x, raw_y = raw_project(x, y, z)
            return origin_x + raw_x * scale, origin_y + raw_y * scale

        def polygon(points, **options):
            flattened = [coordinate for point in points for coordinate in point]
            return canvas.create_polygon(*flattened, **options)

        def dimension(point_a, point_b, text, offset, color="#334155"):
            dx = point_b[0] - point_a[0]
            dy = point_b[1] - point_a[1]
            length = math.hypot(dx, dy)
            if length < 24:
                return
            normal_x, normal_y = -dy / length, dx / length
            a = (point_a[0] + normal_x * offset, point_a[1] + normal_y * offset)
            b = (point_b[0] + normal_x * offset, point_b[1] + normal_y * offset)
            canvas.create_line(*a, *b, fill=color, width=1.4)
            for point in (a, b):
                canvas.create_line(
                    point[0] - normal_x * 4, point[1] - normal_y * 4,
                    point[0] + normal_x * 4, point[1] + normal_y * 4,
                    fill=color, width=1.4
                )
            canvas.create_text(
                (a[0] + b[0]) / 2 + normal_x * 9,
                (a[1] + b[1]) / 2 + normal_y * 9,
                text=text, fill=color, font=("Segoe UI", 8, "bold")
            )

        walls = (
            ((0, 0, 0), (room.ancho, 0, 0), (room.ancho, 0, room.alto), (0, 0, room.alto)),
            ((room.ancho, 0, 0), (room.ancho, room.largo, 0),
             (room.ancho, room.largo, room.alto), (room.ancho, 0, room.alto)),
            ((room.ancho, room.largo, 0), (0, room.largo, 0),
             (0, room.largo, room.alto), (room.ancho, room.largo, room.alto)),
            ((0, room.largo, 0), (0, 0, 0), (0, 0, room.alto), (0, room.largo, room.alto))
        )
        for wall in walls:
            polygon([project(*point) for point in wall], fill="#E2E8F0",
                    outline="#94A3B8", width=1, stipple="gray75")

        floor = [
            project(0, 0), project(room.ancho, 0),
            project(room.ancho, room.largo), project(0, room.largo)
        ]
        polygon(floor, fill="#F8FAFC", outline="#0F172A", width=3)
        dimension(project(0, 0), project(room.ancho, 0), f"{room.ancho:g} m", -18, "#0F172A")
        dimension(project(0, 0), project(0, room.largo), f"{room.largo:g} m", 18, "#0F172A")

        for restriction in room.get_restricciones():
            floor_width, floor_length = restriction.get_floor_dimensions()
            x = restriction.posicion.x
            y = restriction.posicion.y
            clearance = [
                project(x, y, 0.01), project(x + floor_width, y, 0.01),
                project(x + floor_width, y + floor_length, 0.01),
                project(x, y + floor_length, 0.01)
            ]
            color = "#FCA5A5" if restriction.tipo == "Puerta" else "#7DD3FC"
            polygon(clearance, fill=color, outline="#334155", width=1, stipple="gray50")
            top = min(restriction.alto, room.alto)
            if restriction.pared in ("Superior", "Inferior"):
                wall_y = 0 if restriction.pared == "Superior" else room.largo
                wall_points = [
                    project(x, wall_y, 0), project(x + restriction.ancho, wall_y, 0),
                    project(x + restriction.ancho, wall_y, top), project(x, wall_y, top)
                ]
            else:
                wall_x = 0 if restriction.pared == "Izquierda" else room.ancho
                wall_points = [
                    project(wall_x, y, 0), project(wall_x, y + restriction.ancho, 0),
                    project(wall_x, y + restriction.ancho, top), project(wall_x, y, top)
                ]
            polygon(wall_points, fill=color, outline="#334155", width=2)
            center_x = sum(point[0] for point in wall_points) / 4
            center_y = sum(point[1] for point in wall_points) / 4
            canvas.create_text(center_x, center_y, text=restriction.tipo,
                               fill="#0F172A", font=("Segoe UI", 8, "bold"))

        for outlet in room.get_outlets():
            outlet_x, outlet_y = project(
                outlet.posicion.x, outlet.posicion.y, outlet.posicion.z
            )
            canvas.create_oval(outlet_x - 7, outlet_y - 7, outlet_x + 7, outlet_y + 7,
                               fill="#FDE68A", outline="#92400E", width=2)
            canvas.create_line(outlet_x - 2, outlet_y - 3, outlet_x - 2, outlet_y + 3,
                               fill="#92400E", width=1.5)
            canvas.create_line(outlet_x + 2, outlet_y - 3, outlet_x + 2, outlet_y + 3,
                               fill="#92400E", width=1.5)
            canvas.create_text(outlet_x, outlet_y - 13, text=outlet.nombre,
                               fill="#854D0E", font=("Segoe UI", 8, "bold"))

        def furniture_depth(item):
            center_x = item.posicion.x + item.ancho / 2
            center_y = item.posicion.y + item.largo / 2
            return raw_project(center_x, center_y, 0)[1]

        def rendered_support(item):
            if item.get_placement_type() != "Sobre objeto":
                return None
            for candidate in furniture:
                if candidate is item or not candidate.can_support_objects():
                    continue
                touches = abs(
                    item.posicion.z - (candidate.posicion.z + candidate.alto)
                ) <= 1e-9
                fits = (
                    item.posicion.x >= candidate.posicion.x - 1e-9
                    and item.posicion.x + item.ancho
                    <= candidate.posicion.x + candidate.ancho + 1e-9
                    and item.posicion.y >= candidate.posicion.y - 1e-9
                    and item.posicion.y + item.largo
                    <= candidate.posicion.y + candidate.largo + 1e-9
                )
                if touches and fits:
                    return candidate
            return None

        indexed_furniture = list(enumerate(furniture))
        indexed_furniture.sort(key=lambda pair: furniture_depth(pair[1]))
        pairs_by_id = {id(pair[1]): pair for pair in indexed_furniture}
        ordered_furniture = []
        added = set()
        visiting = set()

        def add_with_support(pair):
            item_id = id(pair[1])
            if item_id in added:
                return
            if item_id in visiting:
                ordered_furniture.append(pair)
                added.add(item_id)
                return
            visiting.add(item_id)
            support = rendered_support(pair[1])
            if support is not None and id(support) in pairs_by_id:
                add_with_support(pairs_by_id[id(support)])
            visiting.discard(item_id)
            if item_id not in added:
                ordered_furniture.append(pair)
                added.add(item_id)

        for pair in indexed_furniture:
            add_with_support(pair)
        for color_index, item in ordered_furniture:
            x, y = item.posicion.x, item.posicion.y
            item_width, item_length, item_height = item.ancho, item.largo, item.alto
            base_z = item.posicion.z
            base_color = self.COLORS[color_index % len(self.COLORS)]
            shadow = [
                project(x, y, 0), project(x + item_width, y, 0),
                project(x + item_width, y + item_length, 0), project(x, y + item_length, 0)
            ]
            polygon(shadow, fill="#64748B", outline="", stipple="gray75")
            bottom = [
                project(x, y, base_z), project(x + item_width, y, base_z),
                project(x + item_width, y + item_length, base_z),
                project(x, y + item_length, base_z)
            ]
            top_face = [
                project(x, y, base_z + item_height),
                project(x + item_width, y, base_z + item_height),
                project(x + item_width, y + item_length, base_z + item_height),
                project(x, y + item_length, base_z + item_height)
            ]
            faces = [
                ([bottom[0], bottom[1], top_face[1], top_face[0]], 0.78),
                ([bottom[1], bottom[2], top_face[2], top_face[1]], 0.88),
                ([bottom[2], bottom[3], top_face[3], top_face[2]], 0.72),
                ([bottom[3], bottom[0], top_face[0], top_face[3]], 0.82)
            ]
            faces.sort(key=lambda face: sum(point[1] for point in face[0]) / 4)
            for face, shade in faces:
                polygon(face, fill=self._shade_color(base_color, shade),
                        outline="#0F172A", width=1)
            polygon(top_face, fill=self._shade_color(base_color, 1.18),
                    outline="#0F172A", width=1.5)
            top_center_x = sum(point[0] for point in top_face) / 4
            top_center_y = sum(point[1] for point in top_face) / 4
            rotation_note = " · Giro 90°" if item.get_rotacion() == 90 else ""
            canvas.create_text(
                top_center_x, top_center_y - 5,
                text=f"{item.nombre}{rotation_note}", fill="#FFFFFF",
                font=("Segoe UI", 8, "bold"), width=max(item_width * scale, 45)
            )
            dimension(top_face[0], top_face[1], f"{item_width:g} m", -7, "#FFFFFF")
            dimension(top_face[0], top_face[3], f"{item_length:g} m", 7, "#FFFFFF")
            dimension(bottom[2], top_face[2], f"{item_height:g} m", 7, "#334155")

        self.preview_title.set(
            f"HABITACIÓN: {room.nombre}  ·  {room.ancho:g} × {room.largo:g} × {room.alto:g} m"
        )
        if self.distributions:
            self.preview_iteration.set(
                f"ALTERNATIVA {self.current_index + 1} DE {len(self.distributions)}"
                f"  ·  PUNTAJE {score:.2f}  ·  VISTA 3D"
            )
        elif room.get_muebles():
            self.preview_iteration.set(
                f"SIN GENERAR  ·  {len(room.get_muebles())} MUEBLE(S) PENDIENTE(S)  ·  VISTA 3D"
            )
        else:
            self.preview_iteration.set("VISTA 3D  ·  HABITACIÓN VACÍA")
        canvas.create_text(
            12, height - 12, anchor="sw",
            text="Rueda: zoom  ·  Arrastrar: mover  ·  Botones: girar vista  ·  Doble clic: centrar",
            fill="#64748B", font=("Segoe UI", 8)
        )

    # Dibuja habitación, restricciones y muebles en el Canvas.
    def _draw_preview(self):
        # Identifica el redibujado pendiente al cambiar el tamaño.
        self.resize_job = None
        canvas = self.preview
        # Borra el plano anterior antes de dibujar el nuevo.
        canvas.delete("all")
        width = max(canvas.winfo_width(), 100)
        height = max(canvas.winfo_height(), 100)
        if self.room is None:
            canvas.create_text(width / 2, height / 2, text="Vista previa de la habitación",
                               fill="#94A3B8", font=("Segoe UI", 15))
            self.preview_title.set("SIN HABITACIÓN")
            self.preview_iteration.set("Cree una habitación para comenzar")
            self.preview_geometry = None
            return

        room = self.room
        furniture = []
        score = None
        if self.distributions:
            distribution = self.distributions[self.current_index]
            furniture = distribution.get_muebles()
            score = distribution.get_puntaje()
        if self.preview_mode == "3D":
            self._draw_preview_3d(canvas, width, height, room, furniture, score)
            return

        margin = 78
        base_scale = min(
            max(width - 2 * margin, 20) / room.ancho,
            max(height - 2 * margin, 20) / room.largo
        )
        scale = base_scale * self.preview_zoom
        room_width = room.ancho * scale
        room_height = room.largo * scale
        centered_x = (width - room_width) / 2
        centered_y = (height - room_height) / 2
        origin_x = self._bounded_origin(centered_x + self.preview_pan_x, room_width, width)
        origin_y = self._bounded_origin(centered_y + self.preview_pan_y, room_height, height)
        self.preview_pan_x = origin_x - centered_x
        self.preview_pan_y = origin_y - centered_y
        self.preview_geometry = {
            "width": width, "height": height, "base_scale": base_scale, "scale": scale,
            "origin_x": origin_x, "origin_y": origin_y,
            "raw_min_x": 0.0, "raw_min_y": 0.0,
            "raw_width": room.ancho, "raw_height": room.largo
        }

        # Convierte medidas reales a coordenadas del Canvas.
        def rectangle(x, y, item_width, item_height, **options):
            return canvas.create_rectangle(
                origin_x + x * scale, origin_y + y * scale,
                origin_x + (x + item_width) * scale,
                origin_y + (y + item_height) * scale, **options
            )

        def dimension_line(x1, y1, x2, y2, text, color="#334155", inside=False):
            horizontal = abs(x2 - x1) >= abs(y2 - y1)
            canvas.create_line(x1, y1, x2, y2, fill=color, width=1.5)
            if horizontal:
                canvas.create_line(x1, y1 - 5, x1, y1 + 5, fill=color, width=1.5)
                canvas.create_line(x2, y2 - 5, x2, y2 + 5, fill=color, width=1.5)
                text_y = y1 - 9 if inside else y1 - 11
                canvas.create_text((x1 + x2) / 2, text_y, text=text, fill=color,
                                   font=("Segoe UI", 8, "bold"))
            else:
                canvas.create_line(x1 - 5, y1, x1 + 5, y1, fill=color, width=1.5)
                canvas.create_line(x2 - 5, y2, x2 + 5, y2, fill=color, width=1.5)
                text_x = x1 - 9 if inside else x1 - 13
                canvas.create_text(text_x, (y1 + y2) / 2, text=text, fill=color,
                                   font=("Segoe UI", 8, "bold"), angle=90)

        rectangle(0, 0, room.ancho, room.largo, fill="#FFFFFF", outline="#0F172A", width=4)
        dimension_line(origin_x, origin_y - 24, origin_x + room_width, origin_y - 24,
                       f"{room.ancho:g} m", "#0F172A")
        dimension_line(origin_x - 24, origin_y, origin_x - 24, origin_y + room_height,
                       f"{room.largo:g} m", "#0F172A")
        # Dibuja cada puerta o ventana.
        for restriction in room.get_restricciones():
            item_width, item_height = restriction.get_floor_dimensions()
            color = "#FCA5A5" if restriction.tipo == "Puerta" else "#7DD3FC"
            rectangle(restriction.posicion.x, restriction.posicion.y, item_width, item_height,
                      fill=color, outline="#334155", width=2, stipple="gray50")
            canvas.create_text(
                origin_x + (restriction.posicion.x + item_width / 2) * scale,
                origin_y + (restriction.posicion.y + item_height / 2) * scale,
                text=restriction.tipo, fill="#0F172A", font=("Segoe UI", 8)
            )

        # Dibuja los outlets como puntos sin bloquear superficie.
        for outlet in room.get_outlets():
            ox = origin_x + outlet.posicion.x * scale
            oy = origin_y + outlet.posicion.y * scale
            # Simbolo de enchufe con dos ranuras y etiqueta dentro del plano.
            canvas.create_oval(ox - 11, oy - 11, ox + 11, oy + 11,
                               fill="#FDE68A", outline="#92400E", width=2)
            canvas.create_rectangle(ox - 6, oy - 6, ox + 6, oy + 6,
                                    fill="#FFFFFF", outline="#92400E", width=1)
            canvas.create_line(ox - 2.5, oy - 3, ox - 2.5, oy + 3,
                               fill="#92400E", width=2)
            canvas.create_line(ox + 2.5, oy - 3, ox + 2.5, oy + 3,
                               fill="#92400E", width=2)
            # Coloca el texto hacia el interior para que no quede cortado.
            label_x = ox + (16 if outlet.pared == "Izquierda" else -16 if outlet.pared == "Derecha" else 0)
            label_y = oy + (19 if outlet.pared == "Superior" else -19)
            anchor = "w" if outlet.pared == "Izquierda" else "e" if outlet.pared == "Derecha" else "center"
            canvas.create_text(label_x, label_y, text=f"{outlet.nombre} ({outlet.capacidad})",
                               anchor=anchor, fill="#854D0E", font=("Segoe UI", 9, "bold"))

        # Dibuja cada mueble de la alternativa activa.
        for index, item in enumerate(furniture):
            rectangle(item.posicion.x, item.posicion.y, item.ancho, item.largo,
                      fill=self.COLORS[index % len(self.COLORS)], outline="#0F172A", width=2)
            item_x1 = origin_x + item.posicion.x * scale
            item_y1 = origin_y + item.posicion.y * scale
            item_x2 = origin_x + (item.posicion.x + item.ancho) * scale
            item_y2 = origin_y + (item.posicion.y + item.largo) * scale
            rotation_note = "" if item.get_rotacion() == 0 else "\nGiro: 90°"
            canvas.create_text(
                (item_x1 + item_x2) / 2,
                (item_y1 + item_y2) / 2 - 5,
                text=f"{item.nombre}{rotation_note}", fill="#FFFFFF", font=("Segoe UI", 8, "bold"),
                width=max(item.ancho * scale - 6, 25)
            )
            dimension_line(item_x1 + 5, item_y2 - 8, item_x2 - 5, item_y2 - 8,
                           f"{item.ancho:g} m", "#FFFFFF", True)
            if item_y2 - item_y1 >= 48:
                dimension_line(item_x2 - 8, item_y1 + 5, item_x2 - 8, item_y2 - 5,
                               f"{item.largo:g} m", "#FFFFFF", True)

        if self.distributions:
            self.preview_title.set(
                f"HABITACIÓN: {room.nombre}  ·  {room.ancho:g} × {room.largo:g} × {room.alto:g} m"
            )
            self.preview_iteration.set(
                f"ALTERNATIVA {self.current_index + 1} DE {len(self.distributions)}  ·  PUNTAJE {score:.2f}"
            )
        else:
            self.preview_title.set(
                f"HABITACIÓN: {room.nombre}  ·  {room.ancho:g} × {room.largo:g} × {room.alto:g} m"
            )
            if room.get_muebles():
                self.preview_iteration.set(
                    f"SIN GENERAR  ·  {len(room.get_muebles())} MUEBLE(S) PENDIENTE(S)"
                )
            else:
                self.preview_iteration.set("VISTA BASE  ·  HABITACIÓN VACÍA")
        canvas.create_text(
            12, height - 12, anchor="sw",
            text="Rueda: zoom  ·  Arrastrar: mover  ·  Doble clic: centrar  ·  Giro 90°: mueble rotado",
            fill="#64748B", font=("Segoe UI", 8)
        )

    # Inicia el ciclo de eventos de Tkinter.
    def run(self):
        # Mantiene activa la ventana y procesa eventos.
        self.root.mainloop()


if __name__ == "__main__":
    TkinterInterface().run()