import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.widgets import Button, RadioButtons, TextBox

from distribucion import Distribucion
from habitacion import Habitacion
from mueble import Mueble
from persistencia import guardar_proyecto
from punto3d import Punto3D
from restriccion import Restriccion


class MatplotlibInterface:
    COLORS = [
        "#4C78A8", "#F58518", "#54A24B", "#E45756",
        "#B279A2", "#FF9DA6", "#9D755D", "#72B7B2"
    ]

    def __init__(self):
        self.room = None
        self.distributions = []
        self.current_index = 0
        self.furniture_page = 0
        self.restriction_page = 0
        self.list_button_axes = []
        self.list_buttons = []
        self.figure = plt.figure(figsize=(16, 9), facecolor="#F4F6F8")
        self.figure.canvas.manager.set_window_title("EasySpacey")
        self.preview_axes = self.figure.add_axes([0.41, 0.12, 0.35, 0.78])
        self.furniture_list_axes = self.figure.add_axes([0.79, 0.53, 0.19, 0.34])
        self.restriction_list_axes = self.figure.add_axes([0.79, 0.13, 0.19, 0.32])
        self.status_text = self.figure.text(
            0.41, 0.045, "Cree una habitación para comenzar.",
            fontsize=10, color="#334155"
        )
        self._build_controls()
        self._refresh_lists()
        self._draw_preview()

    def _textbox(self, position, label, initial=""):
        axes = self.figure.add_axes(position)
        textbox = TextBox(axes, label, initial=initial, color="white", hovercolor="#E8F0FE")
        textbox.label.set_fontsize(9)
        textbox.text_disp.set_fontsize(9)
        return textbox

    def _button(self, position, label, callback, color="#2563EB"):
        axes = self.figure.add_axes(position)
        button = Button(axes, label, color=color, hovercolor="#60A5FA")
        button.label.set_color("white")
        button.label.set_fontsize(9)
        button.on_clicked(callback)
        return button

    def _radios(self, position, labels):
        axes = self.figure.add_axes(position, facecolor="white")
        radios = RadioButtons(axes, labels, active=0, activecolor="#2563EB")
        for label in radios.labels:
            label.set_fontsize(8.5)
                                                                          
                                                                              
        if hasattr(radios, "_buttons"):
            radios._buttons.set_sizes([42] * len(radios.labels))
            radios._buttons.set_linewidths([1.1] * len(radios.labels))
        elif hasattr(radios, "circles"):
            for circle in radios.circles:
                circle.set_radius(0.04)
                circle.set_linewidth(1.1)
        self._clear_radios(radios)
        return radios

    @staticmethod
    def _clear_radios(radios):
        radios.value_selected = None
        radios.index_selected = None
        if hasattr(radios, "_buttons"):
            radios._buttons.set_facecolor(["none"] * len(radios.labels))
        elif hasattr(radios, "circles"):
            for circle in radios.circles:
                circle.set_facecolor("none")

    def _build_controls(self):
        self.figure.text(0.035, 0.945, "EasySpacey", fontsize=22, weight="bold", color="#0F172A")
        self.figure.text(0.035, 0.91, "Diseño automático de habitaciones", fontsize=10, color="#64748B")
        self.figure.text(0.035, 0.865, "1. Habitación", fontsize=12, weight="bold")
        self.room_name = self._textbox([0.12, 0.82, 0.25, 0.04], "Nombre ")
        self.room_width = self._textbox([0.12, 0.77, 0.07, 0.04], "Ancho ")
        self.room_length = self._textbox([0.30, 0.77, 0.07, 0.04], "Largo ")
        self.room_height = self._textbox([0.12, 0.72, 0.07, 0.04], "Alto ")
        self.create_room_button = self._button([0.23, 0.715, 0.14, 0.05], "Crear habitación", self._create_room)

        self.figure.text(0.035, 0.665, "2. Muebles", fontsize=12, weight="bold")
        self.furniture_name = self._textbox([0.12, 0.62, 0.25, 0.04], "Nombre ")
        self.furniture_width = self._textbox([0.12, 0.57, 0.07, 0.04], "Ancho ")
        self.furniture_length = self._textbox([0.30, 0.57, 0.07, 0.04], "Largo ")
        self.furniture_height = self._textbox([0.12, 0.52, 0.07, 0.04], "Alto ")
        self.furniture_utility = self._textbox([0.30, 0.52, 0.07, 0.04], "Utilidad ")
        self.furniture_quantity = self._textbox([0.12, 0.47, 0.07, 0.04], "Cantidad ")
        self.furniture_use = self._radios(
            [0.23, 0.43, 0.14, 0.08],
            ("Dormir", "Comer", "Descansar", "Trabajar", "Almacenamiento")
        )
        self.add_furniture_button = self._button([0.12, 0.385, 0.25, 0.04], "Agregar mueble(s)", self._add_furniture, "#059669")

        self.figure.text(0.035, 0.365, "3. Puertas y ventanas", fontsize=12, weight="bold")
        self.figure.text(0.035, 0.348, "Tipo", fontsize=8.5, weight="bold", color="#475569")
        self.figure.text(0.135, 0.348, "Pared", fontsize=8.5, weight="bold", color="#475569")
        self.figure.text(0.25, 0.348, "Posición", fontsize=8.5, weight="bold", color="#475569")
        self.restriction_type = self._radios([0.035, 0.26, 0.09, 0.09], ("Puerta", "Ventana"))
        self.restriction_wall = self._radios(
            [0.135, 0.235, 0.105, 0.12], ("Superior", "Inferior", "Izquierda", "Derecha")
        )
        self.restriction_section = self._radios(
            [0.25, 0.26, 0.12, 0.09], ("Inicio", "Centro", "Final")
        )
        self.restriction_width = self._textbox([0.12, 0.19, 0.07, 0.035], "Ancho ")
        self.restriction_height = self._textbox([0.30, 0.19, 0.07, 0.035], "Alto ")
        self.restriction_depth = self._textbox([0.12, 0.145, 0.07, 0.035], "Prof. ventana ")
        self.add_restriction_button = self._button(
            [0.23, 0.14, 0.14, 0.045], "Agregar restricción", self._add_restriction, "#D97706"
        )

        self.generate_button = self._button([0.035, 0.075, 0.16, 0.055], "Generar alternativas", self._generate)
        self.previous_button = self._button([0.205, 0.075, 0.075, 0.055], "Anterior", self._previous, "#475569")
        self.next_button = self._button([0.29, 0.075, 0.075, 0.055], "Siguiente", self._next, "#475569")
        self.file_name = self._textbox([0.12, 0.02, 0.16, 0.035], "Archivo ")
        self.save_button = self._button([0.29, 0.015, 0.075, 0.045], "Guardar", self._save, "#7C3AED")

        self.figure.text(0.79, 0.89, "Muebles agregados", fontsize=12, weight="bold", color="#0F172A")
        self.figure.text(0.79, 0.47, "Puertas y ventanas agregadas", fontsize=12, weight="bold", color="#0F172A")
        self.furniture_previous_page = self._button([0.79, 0.485, 0.035, 0.032], "‹", self._previous_furniture_page, "#64748B")
        self.furniture_next_page = self._button([0.935, 0.485, 0.035, 0.032], "›", self._next_furniture_page, "#64748B")
        self.restriction_previous_page = self._button([0.79, 0.085, 0.035, 0.032], "‹", self._previous_restriction_page, "#64748B")
        self.restriction_next_page = self._button([0.935, 0.085, 0.035, 0.032], "›", self._next_restriction_page, "#64748B")

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
    def _selection(radios, field_name):
        if radios.value_selected is None:
            raise ValueError(f"Seleccione {field_name}.")
        return radios.value_selected

    def _set_status(self, message, error=False, redraw=True):
        self.status_text.set_text(message)
        self.status_text.set_color("#B91C1C" if error else "#166534")
        if redraw:
            self.figure.canvas.draw_idle()

    @staticmethod
    def _clear_textboxes(*textboxes):
        for textbox in textboxes:
            textbox.set_val("")

    def _clear_generated_results(self):
        self.distributions = []
        self.current_index = 0

    def _refresh_lists(self):
        for axes in self.list_button_axes:
            axes.remove()
        self.list_button_axes = []
        self.list_buttons = []

        furniture = self.room.get_muebles() if self.room else []
        restrictions = self.room.get_restricciones() if self.room else []
        self._draw_item_list(
            self.furniture_list_axes, furniture, self.furniture_page,
            self._delete_furniture, "No hay muebles agregados.", 0.79, 0.53, 0.34
        )
        self._draw_item_list(
            self.restriction_list_axes, restrictions, self.restriction_page,
            self._delete_restriction, "No hay puertas ni ventanas.", 0.79, 0.13, 0.32,
            restriction_list=True
        )

    def _draw_item_list(self, axes, items, page, delete_callback, empty_message,
                        left, bottom, height, restriction_list=False):
        page_size = 6
        page_count = max(1, (len(items) + page_size - 1) // page_size)
        page = min(page, page_count - 1)
        if restriction_list:
            self.restriction_page = page
        else:
            self.furniture_page = page

        axes.clear()
        axes.set_facecolor("white")
        axes.set_xticks([])
        axes.set_yticks([])
        for spine in axes.spines.values():
            spine.set_color("#CBD5E1")

        if not items:
            axes.text(0.5, 0.5, empty_message, ha="center", va="center",
                      fontsize=9, color="#94A3B8", transform=axes.transAxes)
        else:
            start = page * page_size
            for row, item in enumerate(items[start:start + page_size]):
                index = start + row
                y = 0.90 - row * 0.145
                if restriction_list:
                    description = f"{item.tipo} · {item.pared} · {item.ancho:g} m"
                else:
                    description = f"{item.nombre} · {item.uso} · {item.ancho:g}×{item.largo:g} m"
                if len(description) > 37:
                    description = description[:34] + "..."
                axes.text(0.04, y, description, va="center", fontsize=8.5,
                          color="#1E293B", transform=axes.transAxes)
                axes.plot([0.03, 0.97], [y - 0.07, y - 0.07], color="#E2E8F0",
                          linewidth=0.8, transform=axes.transAxes)
                button_axes = self.figure.add_axes([
                    left + 0.163,
                    bottom + height * (y - 0.045),
                    0.021,
                    height * 0.09
                ])
                button = Button(button_axes, "×", color="#DC2626", hovercolor="#F87171")
                button.label.set_color("white")
                button.label.set_fontsize(10)
                button.on_clicked(lambda _event, i=index: delete_callback(i))
                self.list_button_axes.append(button_axes)
                self.list_buttons.append(button)

        axes.text(0.5, 0.02, f"Página {page + 1}/{page_count} · {len(items)} elemento(s)",
                  ha="center", va="bottom", fontsize=8, color="#64748B",
                  transform=axes.transAxes)

    def _delete_furniture(self, index):
        if self.room is None or index >= len(self.room.get_muebles()):
            return
        item = self.room.get_muebles()[index]
        self.room.eliminar_mueble(item)
        self._clear_generated_results()
        self._refresh_lists()
        self._set_status(f"Mueble '{item.nombre}' eliminado.", redraw=False)
        self._draw_preview()

    def _delete_restriction(self, index):
        if self.room is None or index >= len(self.room.get_restricciones()):
            return
        item = self.room.get_restricciones()[index]
        self.room.eliminar_restriccion(item)
        self._clear_generated_results()
        self._refresh_lists()
        self._set_status(f"{item.tipo} de la pared {item.pared} eliminada.", redraw=False)
        self._draw_preview()

    def _previous_furniture_page(self, _event=None):
        if self.furniture_page > 0:
            self.furniture_page -= 1
            self._refresh_lists()
            self.figure.canvas.draw_idle()

    def _next_furniture_page(self, _event=None):
        count = len(self.room.get_muebles()) if self.room else 0
        if (self.furniture_page + 1) * 6 < count:
            self.furniture_page += 1
            self._refresh_lists()
            self.figure.canvas.draw_idle()

    def _previous_restriction_page(self, _event=None):
        if self.restriction_page > 0:
            self.restriction_page -= 1
            self._refresh_lists()
            self.figure.canvas.draw_idle()

    def _next_restriction_page(self, _event=None):
        count = len(self.room.get_restricciones()) if self.room else 0
        if (self.restriction_page + 1) * 6 < count:
            self.restriction_page += 1
            self._refresh_lists()
            self.figure.canvas.draw_idle()

    def _create_room(self, _event=None):
        try:
            name = self.room_name.text.strip()
            if not name:
                raise ValueError("El nombre no puede quedar vacío.")
            self.room = Habitacion(
                name,
                self._positive(self.room_width.text, "Ancho"),
                self._positive(self.room_length.text, "Largo"),
                self._positive(self.room_height.text, "Alto")
            )
            self._clear_generated_results()
            self.furniture_page = 0
            self.restriction_page = 0
            self._refresh_lists()
            self._set_status(f"Habitación '{name}' creada.", redraw=False)
            self._draw_preview()
        except ValueError as error:
            self._set_status(str(error), True)

    def _add_furniture(self, _event=None):
        if self.room is None:
            self._set_status("Primero cree una habitación.", True)
            return
        try:
            name = self.furniture_name.text.strip()
            if not name:
                raise ValueError("El mueble necesita un nombre.")
            utility = self._integer(self.furniture_utility.text, "Utilidad")
            quantity = self._integer(self.furniture_quantity.text, "Cantidad")
            if not 1 <= utility <= 10:
                raise ValueError("La utilidad debe estar entre 1 y 10.")
            if quantity <= 0:
                raise ValueError("La cantidad debe ser mayor que cero.")
            dimensions = (
                self._positive(self.furniture_width.text, "Ancho"),
                self._positive(self.furniture_length.text, "Largo"),
                self._positive(self.furniture_height.text, "Alto")
            )
            use = self._selection(self.furniture_use, "el uso del mueble")
            for number in range(1, quantity + 1):
                item_name = name if quantity == 1 else f"{name} {number}"
                self.room.agregar_mueble(Mueble(
                    item_name, *dimensions, utility, Punto3D(0, 0, 0),
                    use
                ))
            self._clear_generated_results()
            self._clear_textboxes(
                self.furniture_name, self.furniture_width, self.furniture_length,
                self.furniture_height, self.furniture_utility, self.furniture_quantity
            )
            self._clear_radios(self.furniture_use)
            self.furniture_page = max(0, (len(self.room.get_muebles()) - 1) // 6)
            self._refresh_lists()
            self._set_status(f"Se agregaron {quantity} mueble(s).", redraw=False)
            self._draw_preview()
        except (ValueError, TypeError) as error:
            self._set_status(str(error), True)

    def _add_restriction(self, _event=None):
        if self.room is None:
            self._set_status("Primero cree una habitación.", True)
            return
        try:
            width = self._positive(self.restriction_width.text, "Ancho")
            restriction_type = self._selection(self.restriction_type, "el tipo de restricción")
            wall = self._selection(self.restriction_wall, "la pared")
            section = self._selection(self.restriction_section, "la posición aproximada")
            clearance_depth = (
                width
                if restriction_type == "Puerta"
                else self._positive(self.restriction_depth.text, "Profundidad")
            )
            restriction = Restriccion.crear_desde_pared(
                self.room,
                restriction_type,
                wall,
                section,
                width,
                self._positive(self.restriction_height.text, "Alto"),
                clearance_depth
            )
            self.room.agregar_restriccion(restriction)
            self._clear_generated_results()
            detail = (
                f"área de apertura {width:.2f} x {width:.2f} m"
                if restriction_type == "Puerta"
                else f"profundidad libre {clearance_depth:.2f} m"
            )
            self._clear_textboxes(
                self.restriction_width, self.restriction_height, self.restriction_depth
            )
            self._clear_radios(self.restriction_type)
            self._clear_radios(self.restriction_wall)
            self._clear_radios(self.restriction_section)
            self.restriction_page = max(0, (len(self.room.get_restricciones()) - 1) // 6)
            self._refresh_lists()
            self._set_status(
                f"{restriction.tipo} agregada en pared {restriction.pared}; {detail}.",
                redraw=False
            )
            self._draw_preview()
        except ValueError as error:
            self._set_status(str(error), True)

    def _generate(self, _event=None):
        if self.room is None:
            self._set_status("Primero cree una habitación.", True)
            return
        if not Distribucion.verificar_espacio(self.room):
            self._set_status("Los muebles exceden el espacio disponible.", True)
            return
        if not self.room.get_muebles():
            empty = Distribucion(self.room)
            empty.validar()
            empty.calcular_puntaje()
            self.distributions = [empty]
        else:
            self.distributions = Distribucion.generar_distribuciones(
                self.room, amount=300, limite_resultados=3
            )
        self.current_index = 0
        if not self.distributions:
            self._set_status("No se encontró una distribución válida.", True)
            return
        self._set_status(f"{len(self.distributions)} alternativa(s) generada(s).", redraw=False)
        self._draw_preview()

    def _previous(self, _event=None):
        if self.distributions:
            self.current_index = (self.current_index - 1) % len(self.distributions)
            self._draw_preview()

    def _next(self, _event=None):
        if self.distributions:
            self.current_index = (self.current_index + 1) % len(self.distributions)
            self._draw_preview()

    def _save(self, _event=None):
        if self.room is None:
            self._set_status("No hay una habitación para guardar.", True)
            return
        filename = self.file_name.text.strip()
        if not filename:
            self._set_status("Escriba un nombre de archivo para guardar.", True)
            return
        if not filename.lower().endswith(".json"):
            filename += ".json"
        if guardar_proyecto(self.room, filename):
            self._set_status(f"Proyecto guardado en {filename}.")
        else:
            self._set_status("No se pudo guardar el proyecto.", True)

    def _draw_preview(self):
        axes = self.preview_axes
        axes.clear()
        axes.set_facecolor("white")
        if self.room is None:
            axes.text(0.5, 0.5, "Vista previa de la habitación", ha="center", va="center", transform=axes.transAxes, color="#94A3B8", fontsize=16)
            axes.set_axis_off()
            self.figure.canvas.draw_idle()
            return

        room = self.room
        axes.set_axis_on()
        axes.add_patch(Rectangle((0, 0), room.ancho, room.largo, fill=False, edgecolor="#0F172A", linewidth=4))
        legend = []
        for restriction in room.get_restricciones():
            width, length = restriction.get_floor_dimensions()
            color = "#EF4444" if restriction.tipo == "Puerta" else "#0EA5E9"
            axes.add_patch(Rectangle(
                (restriction.posicion.x, restriction.posicion.y), width, length,
                facecolor=color, edgecolor="#0F172A", alpha=0.35, hatch="//"
            ))
            legend.append(Patch(facecolor=color, alpha=0.35, hatch="//", label=restriction.tipo))

        furniture = []
        score = None
        if self.distributions:
            current = self.distributions[self.current_index]
            furniture = current.get_muebles()
            score = current.get_puntaje()
        for index, item in enumerate(furniture):
            color = self.COLORS[index % len(self.COLORS)]
            axes.add_patch(Rectangle(
                (item.posicion.x, item.posicion.y), item.ancho, item.largo,
                facecolor=color, edgecolor="#0F172A", linewidth=1.5, alpha=0.88
            ))
            axes.text(
                item.posicion.x + item.ancho / 2,
                item.posicion.y + item.largo / 2,
                item.nombre, ha="center", va="center", fontsize=8
            )

        margin = max(min(room.ancho, room.largo) * 0.04, 0.1)
        axes.set_xlim(-margin, room.ancho + margin)
        axes.set_ylim(room.largo + margin, -margin)
        axes.set_aspect("equal", adjustable="box")
        axes.grid(True, linestyle=":", alpha=0.25)
        title = room.nombre
        if self.distributions:
            title += f" — Alternativa {self.current_index + 1}/{len(self.distributions)} — Puntaje {score:.2f}"
        else:
            title += f" — {len(room.get_muebles())} muebles pendientes de distribuir"
        axes.set_title(title, fontsize=14, weight="bold", color="#0F172A")
        axes.set_xlabel("Ancho X (m)")
        axes.set_ylabel("Largo Y (m)")
        if legend:
            axes.legend(handles=legend, loc="upper right")
        self.figure.canvas.draw_idle()

    def run(self):
        plt.show()


if __name__ == "__main__":
    MatplotlibInterface().run()
