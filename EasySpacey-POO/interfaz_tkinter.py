import copy
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
    def _entry(self, parent, key, label, row, column=0):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, sticky="ew", padx=4, pady=3)
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
        ttk.Label(furniture_box, text="Opcional: deje vacío si no necesita electricidad (0).",
                  style="Card.TLabel", wraplength=335, justify="left").grid(
                      row=5, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 3))
        self.furniture_use = self._combo(
            furniture_box, "Uso o propósito",
            ("Dormir", "Comer", "Cocinar", "Descansar", "Trabajar", "Almacenamiento"), 3, 1
        )
        ttk.Button(furniture_box, text="Agregar mueble(s)", style="Primary.TButton",
                   command=self._add_furniture).grid(row=6, column=0, columnspan=2, sticky="ew", padx=4, pady=5)

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
            restriction_box, "restriction_depth", "Profundidad libre (m)", 1, 2
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
        # Una guia indica donde comienza la medida y donde quedara la abertura.
        self.restriction_guide_canvas = tk.Canvas(
            restriction_box, height=78, background="#FFFFFF", highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.restriction_guide_canvas.grid(row=5, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
        self.restriction_guide_canvas.bind("<Configure>", self._draw_restriction_guide)
        self.restriction_wall.bind("<<ComboboxSelected>>", self._update_restriction_slider)
        self.entries["restriction_width"].bind("<KeyRelease>", self._update_restriction_slider)
        ttk.Button(restriction_box, text="Agregar puerta o ventana", style="Primary.TButton",
                   command=self._add_restriction).grid(row=6, column=0, columnspan=3, sticky="ew", padx=4, pady=5)

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
        self._entry(outlet_box, "outlet_distance", "Distancia desde esquina (m)", 1, 0)
        self._entry(outlet_box, "outlet_height", "Altura desde suelo (m)", 1, 1)
        self._entry(outlet_box, "outlet_capacity", "Conexiones", 1, 2)
        self.outlet_guide = tk.StringVar(value="Seleccione una pared para ver desde donde se mide.")
        ttk.Label(outlet_box, textvariable=self.outlet_guide, style="Card.TLabel",
                  wraplength=340, justify="left").grid(row=2, column=0, columnspan=3,
                                                       sticky="ew", padx=4, pady=(5, 2))
        # La guia muestra el inicio y el extremo de la pared elegida.
        self.outlet_guide_canvas = tk.Canvas(outlet_box, height=98, background="#FFFFFF",
                                             highlightthickness=1, highlightbackground="#CBD5E1")
        self.outlet_guide_canvas.grid(row=3, column=0, columnspan=3, sticky="ew", padx=4, pady=3)
        self.outlet_guide_canvas.bind("<Configure>", self._draw_outlet_guide)
        self.entries["outlet_distance"].bind("<KeyRelease>", self._draw_outlet_guide)
        ttk.Button(outlet_box, text="Agregar outlet", style="Primary.TButton",
                   command=self._add_outlet).grid(row=4, column=0, columnspan=3, sticky="ew", padx=4, pady=4)

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
        self.preview_panel.rowconfigure(1, weight=1)
        self.preview_title = tk.StringVar(value="Vista previa de la habitación")
        ttk.Label(self.preview_panel, textvariable=self.preview_title,
                  style="CardTitle.TLabel", anchor="center").grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.preview = tk.Canvas(
            self.preview_panel, background="#FFFFFF", highlightthickness=1,
            highlightbackground="#CBD5E1"
        )
        self.preview.grid(row=1, column=0, sticky="nsew")
        # Programa el redibujado cuando cambia el tamaño.
        self.preview.bind("<Configure>", self._schedule_preview)

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

    # Convierte texto a un número positivo o lanza ValueError.
    @staticmethod
    def _positive(text, field_name):
        try:
            value = float(text)
        except ValueError as error:
            raise ValueError(f"{field_name} debe ser numérico.") from error
        if value <= 0:
            raise ValueError(f"{field_name} debe ser mayor que cero.")
        return value

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
            self._draw_preview()
            self._update_restriction_slider()
            self._set_status(f"Habitación '{name}' creada.")
        except ValueError as error:
            self._set_status(str(error), True)

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
                    Mueble(item_name, *dimensions, utility, Punto3D(0, 0, 0), use, conexiones_necesarias=connections)
                )
            self._invalidate_distributions()
            self._clear_entries(
                "furniture_name", "furniture_width", "furniture_length",
                "furniture_height", "furniture_utility", "furniture_quantity", "furniture_connections"
            )
            self.furniture_use.set("")
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
            limit = self._restriction_limit()
            offset = min(max(round(self.restriction_offset.get() * 100) / 100, 0.0), limit)
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
            self._draw_outlet_guide()
            return
        maximum = f" Longitud de la pared: {limit:g} m." if limit is not None else ""
        self.outlet_guide.set(f"Mida {direction}.{maximum} Puede usar centimetros (ej. 2.35 m).")
        self._draw_outlet_guide()

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
        try:
            distance = self._centimeters(self._entry_value("outlet_distance"), "Distancia", True)
        except (ValueError, KeyError):
            distance = None
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
            distance = self._centimeters(self._entry_value("outlet_distance"), "Distancia", True)
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
            lambda item: f"{item.nombre}\n{item.uso} · {item.ancho:g} × {item.largo:g} m",
            self._delete_furniture, "No hay muebles agregados."
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
    def _populate_list(self, target, items, description, delete_callback, empty_message):
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
            ttk.Label(row, text=description(item), style="ListText.TLabel",
                      justify="left").grid(row=0, column=0, sticky="w")
            ttk.Button(row, text="×", width=3, style="Delete.TButton",
                       command=lambda i=index: delete_callback(i)).grid(row=0, column=1, padx=(6, 0))
            ttk.Separator(target.content).grid(row=index * 2 + 1, column=0, sticky="ew")

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
            self.preview_title.set("Vista previa de la habitación")
            return

        margin = 42
        room = self.room
        # Calcula una escala que conserva las proporciones.
        scale = min((width - 2 * margin) / room.ancho, (height - 2 * margin) / room.largo)
        room_width = room.ancho * scale
        room_height = room.largo * scale
        origin_x = (width - room_width) / 2
        origin_y = (height - room_height) / 2

        # Convierte medidas reales a coordenadas del Canvas.
        def rectangle(x, y, item_width, item_height, **options):
            return canvas.create_rectangle(
                origin_x + x * scale, origin_y + y * scale,
                origin_x + (x + item_width) * scale,
                origin_y + (y + item_height) * scale, **options
            )

        rectangle(0, 0, room.ancho, room.largo, fill="#FFFFFF", outline="#0F172A", width=4)
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

        furniture = []
        score = None
        if self.distributions:
            distribution = self.distributions[self.current_index]
            furniture = distribution.get_muebles()
            score = distribution.get_puntaje()
        # Dibuja cada mueble de la alternativa activa.
        for index, item in enumerate(furniture):
            rectangle(item.posicion.x, item.posicion.y, item.ancho, item.largo,
                      fill=self.COLORS[index % len(self.COLORS)], outline="#0F172A", width=2)
            canvas.create_text(
                origin_x + (item.posicion.x + item.ancho / 2) * scale,
                origin_y + (item.posicion.y + item.largo / 2) * scale,
                text=item.nombre, fill="#FFFFFF", font=("Segoe UI", 8, "bold"),
                width=max(item.ancho * scale - 6, 25)
            )

        if self.distributions:
            self.preview_title.set(
                f"{room.nombre} — Alternativa {self.current_index + 1}/{len(self.distributions)} — Puntaje {score:.2f}"
            )
        else:
            self.preview_title.set(
                f"{room.nombre} — {len(room.get_muebles())} muebles pendientes de distribuir"
            )

    # Inicia el ciclo de eventos de Tkinter.
    def run(self):
        # Mantiene activa la ventana y procesa eventos.
        self.root.mainloop()


if __name__ == "__main__":
    TkinterInterface().run()
