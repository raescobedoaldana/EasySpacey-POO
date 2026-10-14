import copy
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from distribucion import Distribucion
from habitacion import Habitacion
from mueble import Mueble
from persistencia import guardar_proyecto
from punto3d import Punto3D
from restriccion import Restriccion


class ScrollableList(ttk.Frame):
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
        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._fit_width)
        self.canvas.bind("<Enter>", lambda _event: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda _event: self.canvas.unbind_all("<MouseWheel>"))

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _fit_width(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)

    def _wheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def clear(self):
        for child in self.content.winfo_children():
            child.destroy()


class TkinterInterface:
    COLORS = (
        "#4C78A8", "#F58518", "#54A24B", "#E45756",
        "#B279A2", "#FF9DA6", "#9D755D", "#72B7B2"
    )

    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.room = None
        self.distributions = []
        self.current_index = 0
        self.generation_token = 0
        self.resize_job = None
        self.entries = {}
        self._configure_window()
        self._configure_styles()
        self._build_interface()
        self._refresh_lists()
        self._draw_preview()

    def _configure_window(self):
        self.root.title("EasySpacey")
        self.root.geometry("1500x850")
        self.root.minsize(1120, 700)
        self.root.configure(background="#F1F5F9")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

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

    def _build_interface(self):
        header = ttk.Frame(self.root, padding=(22, 14, 22, 8))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="EasySpacey", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Diseño automático de habitaciones", style="Subtitle.TLabel").grid(
            row=1, column=0, sticky="w"
        )

        body = ttk.Panedwindow(self.root, orient="horizontal")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 8))
        self.form_panel = ttk.Frame(body, style="Card.TFrame", padding=12, width=390)
        self.preview_panel = ttk.Frame(body, style="Card.TFrame", padding=10)
        self.list_panel = ttk.Frame(body, style="Card.TFrame", padding=12, width=340)
        body.add(self.form_panel, weight=0)
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

    def _entry(self, parent, key, label, row, column=0):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, sticky="ew", padx=4, pady=3)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label, style="Card.TLabel").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(frame)
        entry.grid(row=1, column=0, sticky="ew", pady=(1, 0))
        self.entries[key] = entry
        return entry

    def _combo(self, parent, label, values, row, column=0):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, sticky="ew", padx=4, pady=3)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label, style="Card.TLabel").grid(row=0, column=0, sticky="w")
        combo = ttk.Combobox(frame, values=values, state="readonly")
        combo.set("")
        combo.grid(row=1, column=0, sticky="ew", pady=(1, 0))
        return combo

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
        self.furniture_use = self._combo(
            furniture_box, "Uso o propósito",
            ("Dormir", "Comer", "Cocinar", "Descansar", "Trabajar", "Almacenamiento"), 3, 1
        )
        ttk.Button(furniture_box, text="Agregar mueble(s)", style="Primary.TButton",
                   command=self._add_furniture).grid(row=4, column=0, columnspan=2, sticky="ew", padx=4, pady=5)

        restriction_box = ttk.LabelFrame(panel, text="3. Puertas y ventanas", padding=8)
        restriction_box.grid(row=2, column=0, sticky="ew", pady=8)
        for column in (0, 1, 2):
            restriction_box.columnconfigure(column, weight=1)
        self.restriction_type = self._combo(restriction_box, "Tipo", ("Puerta", "Ventana"), 0, 0)
        self.restriction_type.bind("<<ComboboxSelected>>", self._restriction_type_changed)
        self.restriction_wall = self._combo(
            restriction_box, "Pared", ("Superior", "Inferior", "Izquierda", "Derecha"), 0, 1
        )
        self.restriction_section = self._combo(
            restriction_box, "Posición", ("Inicio", "Centro", "Final"), 0, 2
        )
        self._entry(restriction_box, "restriction_width", "Ancho (m)", 1, 0)
        self._entry(restriction_box, "restriction_height", "Alto (m)", 1, 1)
        self.restriction_depth = self._entry(
            restriction_box, "restriction_depth", "Profundidad libre (m)", 1, 2
        )
        ttk.Button(restriction_box, text="Agregar puerta o ventana", style="Primary.TButton",
                   command=self._add_restriction).grid(row=2, column=0, columnspan=3, sticky="ew", padx=4, pady=5)

        actions = ttk.Frame(panel, style="Card.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        for column in (0, 1, 2):
            actions.columnconfigure(column, weight=1)
        self.generate_button = ttk.Button(
            actions, text="Generar alternativas", style="Primary.TButton", command=self._generate
        )
        self.generate_button.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        ttk.Button(actions, text="Anterior", command=self._previous).grid(row=1, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(actions, text="Siguiente", command=self._next).grid(row=1, column=1, sticky="ew", padx=3)
        ttk.Button(actions, text="Guardar JSON", command=self._save).grid(row=1, column=2, sticky="ew", padx=(3, 0))

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
        self.preview.bind("<Configure>", self._schedule_preview)

    def _build_lists(self):
        self.list_panel.columnconfigure(0, weight=1)
        self.list_panel.rowconfigure(1, weight=1)
        self.list_panel.rowconfigure(3, weight=1)
        ttk.Label(self.list_panel, text="Muebles agregados", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self.furniture_list = ScrollableList(self.list_panel)
        self.furniture_list.grid(row=1, column=0, sticky="nsew", pady=(0, 14))
        ttk.Label(self.list_panel, text="Puertas y ventanas", style="CardTitle.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )
        self.restriction_list = ScrollableList(self.list_panel)
        self.restriction_list.grid(row=3, column=0, sticky="nsew")

    @staticmethod
    def _positive(text, field_name):
        try:
            value = float(text)
        except ValueError as error:
            raise ValueError(f"{field_name} debe ser numérico.") from error
        if value <= 0:
            raise ValueError(f"{field_name} debe ser mayor que cero.")
        return value

    @staticmethod
    def _integer(text, field_name):
        try:
            return int(text)
        except ValueError as error:
            raise ValueError(f"{field_name} debe ser un número entero.") from error

    @staticmethod
    def _required(text, field_name):
        value = text.strip()
        if not value:
            raise ValueError(f"Seleccione o escriba {field_name}.")
        return value

    def _entry_value(self, key):
        return self.entries[key].get().strip()

    def _clear_entries(self, *keys):
        for key in keys:
            self.entries[key].delete(0, tk.END)

    def _invalidate_distributions(self):
        self.distributions = []
        self.current_index = 0
        self.generation_token += 1

    def _set_status(self, message, error=False):
        self.status_var.set(message)
        self.status_label.configure(foreground="#B91C1C" if error else "#166534")

    def _create_room(self):
        try:
            name = self._required(self._entry_value("room_name"), "el nombre")
            new_room = Habitacion(
                name,
                self._positive(self._entry_value("room_width"), "Ancho"),
                self._positive(self._entry_value("room_length"), "Largo"),
                self._positive(self._entry_value("room_height"), "Alto")
            )
            if self.room and (self.room.get_muebles() or self.room.get_restricciones()):
                if not messagebox.askyesno(
                    "Reemplazar habitación",
                    "Crear otra habitación eliminará los elementos actuales. ¿Desea continuar?"
                ):
                    return
            self.room = new_room
            self._invalidate_distributions()
            self._refresh_lists()
            self._draw_preview()
            self._set_status(f"Habitación '{name}' creada.")
        except ValueError as error:
            self._set_status(str(error), True)

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
            dimensions = (
                self._positive(self._entry_value("furniture_width"), "Ancho"),
                self._positive(self._entry_value("furniture_length"), "Largo"),
                self._positive(self._entry_value("furniture_height"), "Alto")
            )
            for number in range(1, quantity + 1):
                item_name = name if quantity == 1 else f"{name} {number}"
                self.room.agregar_mueble(
                    Mueble(item_name, *dimensions, utility, Punto3D(0, 0, 0), use)
                )
            self._invalidate_distributions()
            self._clear_entries(
                "furniture_name", "furniture_width", "furniture_length",
                "furniture_height", "furniture_utility", "furniture_quantity"
            )
            self.furniture_use.set("")
            self._refresh_lists()
            self._draw_preview()
            self._set_status(f"Se agregaron {quantity} mueble(s).")
        except ValueError as error:
            self._set_status(str(error), True)

    def _restriction_type_changed(self, _event=None):
        if self.restriction_type.get() == "Puerta":
            self.restriction_depth.delete(0, tk.END)
            self.restriction_depth.configure(state="disabled")
        else:
            self.restriction_depth.configure(state="normal")

    def _add_restriction(self):
        if self.room is None:
            self._set_status("Primero cree una habitación.", True)
            return
        try:
            restriction_type = self._required(self.restriction_type.get(), "el tipo")
            wall = self._required(self.restriction_wall.get(), "la pared")
            section = self._required(self.restriction_section.get(), "la posición")
            width = self._positive(self._entry_value("restriction_width"), "Ancho")
            depth = width if restriction_type == "Puerta" else self._positive(
                self._entry_value("restriction_depth"), "Profundidad"
            )
            restriction = Restriccion.crear_desde_pared(
                self.room, restriction_type, wall, section, width,
                self._positive(self._entry_value("restriction_height"), "Alto"), depth
            )
            self.room.agregar_restriccion(restriction)
            self._invalidate_distributions()
            self._clear_entries("restriction_width", "restriction_height")
            self.restriction_depth.configure(state="normal")
            self._clear_entries("restriction_depth")
            self.restriction_type.set("")
            self.restriction_wall.set("")
            self.restriction_section.set("")
            self._refresh_lists()
            self._draw_preview()
            detail = "apertura igual al ancho" if restriction_type == "Puerta" else f"profundidad {depth:g} m"
            self._set_status(f"{restriction_type} agregada en pared {wall}; {detail}.")
        except ValueError as error:
            self._set_status(str(error), True)

    def _refresh_lists(self):
        self.furniture_list.clear()
        self.restriction_list.clear()
        furniture = self.room.get_muebles() if self.room else []
        restrictions = self.room.get_restricciones() if self.room else []
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

    def _populate_list(self, target, items, description, delete_callback, empty_message):
        target.content.columnconfigure(0, weight=1)
        if not items:
            ttk.Label(target.content, text=empty_message, style="ListText.TLabel",
                      anchor="center").grid(row=0, column=0, sticky="ew", padx=8, pady=18)
            return
        for index, item in enumerate(items):
            row = ttk.Frame(target.content, style="List.TFrame", padding=(8, 5))
            row.grid(row=index * 2, column=0, sticky="ew")
            row.columnconfigure(0, weight=1)
            ttk.Label(row, text=description(item), style="ListText.TLabel",
                      justify="left").grid(row=0, column=0, sticky="w")
            ttk.Button(row, text="×", width=3, style="Delete.TButton",
                       command=lambda i=index: delete_callback(i)).grid(row=0, column=1, padx=(6, 0))
            ttk.Separator(target.content).grid(row=index * 2 + 1, column=0, sticky="ew")

    def _delete_furniture(self, index):
        item = self.room.get_muebles()[index]
        self.room.eliminar_mueble(item)
        self._invalidate_distributions()
        self._refresh_lists()
        self._draw_preview()
        self._set_status(f"Mueble '{item.nombre}' eliminado.")

    def _delete_restriction(self, index):
        item = self.room.get_restricciones()[index]
        self.room.eliminar_restriccion(item)
        self._invalidate_distributions()
        self._refresh_lists()
        self._draw_preview()
        self._set_status(f"{item.tipo} de la pared {item.pared} eliminada.")

    def _generate(self):
        if self.room is None:
            self._set_status("Primero cree una habitación.", True)
            return
        if not Distribucion.verificar_espacio(self.room):
            self._set_status("Los muebles exceden el espacio disponible.", True)
            return
        token = self.generation_token
        room_copy = copy.deepcopy(self.room)
        self.generation_queue = queue.Queue(maxsize=1)
        self.generate_button.state(["disabled"])
        self._set_status("Generando alternativas…")
        threading.Thread(target=self._generate_worker, args=(room_copy, token), daemon=True).start()
        self.root.after(50, self._poll_generation)

    def _generate_worker(self, room, token):
        try:
            if not room.get_muebles():
                distribution = Distribucion(room)
                distribution.validar()
                distribution.calcular_puntaje()
                results = [distribution]
            else:
                results = Distribucion.generar_distribuciones(
                    room, amount=300, limite_resultados=3
                )
            self.generation_queue.put((results, token, None))
        except Exception as error:
            self.generation_queue.put(([], token, str(error)))

    def _poll_generation(self):
        try:
            results, token, error = self.generation_queue.get_nowait()
        except queue.Empty:
            self.root.after(50, self._poll_generation)
            return
        self._finish_generation(results, token, error)

    def _finish_generation(self, results, token, error):
        self.generate_button.state(["!disabled"])
        if token != self.generation_token:
            return
        if error:
            self._set_status(f"No se pudieron generar alternativas: {error}", True)
            return
        if not results:
            self._set_status("No se encontró una distribución válida.", True)
            return
        self.distributions = results
        self.current_index = 0
        self._draw_preview()
        self._set_status(f"{len(results)} alternativa(s) generada(s).")

    def _previous(self):
        if self.distributions:
            self.current_index = (self.current_index - 1) % len(self.distributions)
            self._draw_preview()

    def _next(self):
        if self.distributions:
            self.current_index = (self.current_index + 1) % len(self.distributions)
            self._draw_preview()

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

    def _schedule_preview(self, _event=None):
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(50, self._draw_preview)

    def _draw_preview(self):
        self.resize_job = None
        canvas = self.preview
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
        scale = min((width - 2 * margin) / room.ancho, (height - 2 * margin) / room.largo)
        room_width = room.ancho * scale
        room_height = room.largo * scale
        origin_x = (width - room_width) / 2
        origin_y = (height - room_height) / 2

        def rectangle(x, y, item_width, item_height, **options):
            return canvas.create_rectangle(
                origin_x + x * scale, origin_y + y * scale,
                origin_x + (x + item_width) * scale,
                origin_y + (y + item_height) * scale, **options
            )

        rectangle(0, 0, room.ancho, room.largo, fill="#FFFFFF", outline="#0F172A", width=4)
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

        furniture = []
        score = None
        if self.distributions:
            distribution = self.distributions[self.current_index]
            furniture = distribution.get_muebles()
            score = distribution.get_puntaje()
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

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    TkinterInterface().run()
