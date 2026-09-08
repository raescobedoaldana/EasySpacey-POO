"""Vista de consola y visualización de las tres mejores distribuciones."""

import matplotlib.pyplot as blt  # yum
from matplotlib.patches import Patch, Rectangle

from distribucion import Distribucion
from habitacion import Habitacion
from mueble import Mueble
from punto3d import Punto3D


class Vista:
    def mostrar_mensaje(self, message):
        print(message)

    def mostrar_error(self, message):
        print(f"Error: {message}")

    def solicitar_texto(self, prompt):
        while True:
            text = input(prompt).strip()
            if text:
                return text
            self.mostrar_error("Este dato no puede quedar vacío.")

    def solicitar_numero_positivo(self, prompt):
        while True:
            try:
                number = float(input(prompt))
                if number > 0:
                    return number
                self.mostrar_error("El número debe ser mayor que cero.")
            except ValueError:
                self.mostrar_error("Debe ingresar un número válido.")

    def solicitar_utilidad(self):
        while True:
            try:
                utility = int(input("Utilidad del mueble (1-10): "))
                if 1 <= utility <= 10:
                    return utility
                self.mostrar_error("La utilidad debe estar entre 1 y 10.")
            except ValueError:
                self.mostrar_error("Debe ingresar un número entero.")

    def solicitar_uso(self):
        uses = {
            "1": "Dormir",
            "2": "Cocinar",
            "3": "Comer",
            "4": "Descansar",
            "5": "Trabajar/Estudiar",
            "6": "Almacenamiento",
            "7": "Otro",
        }
        print("Uso o propósito del mueble:")
        for option, use in uses.items():
            print(f"{option}. {use}")

        while True:
            choice = input("Seleccione una opción: ").strip()
            if choice not in uses:
                self.mostrar_error("Seleccione una opción del 1 al 7.")
                continue
            if choice == "7":
                return self.solicitar_texto("Escriba el uso: ").title()
            return uses[choice]

    def solicitar_habitacion(self):
        print("\nCREAR HABITACIÓN")
        name = self.solicitar_texto("Nombre: ")
        width = self.solicitar_numero_positivo("Ancho (m): ")
        length = self.solicitar_numero_positivo("Largo (m): ")
        height = self.solicitar_numero_positivo("Alto (m): ")
        return Habitacion(name, width, length, height)

    def solicitar_cantidad(self):
        while True:
            try:
                quantity = int(input("Cantidad de este mueble: "))
                if quantity > 0:
                    return quantity
                self.mostrar_error("La cantidad debe ser mayor que cero.")
            except ValueError:
                self.mostrar_error("Debe ingresar un número entero.")

    def solicitar_muebles(self):
        print("\nAGREGAR MUEBLE")
        name = self.solicitar_texto("Nombre: ")
        width = self.solicitar_numero_positivo("Ancho (m): ")
        length = self.solicitar_numero_positivo("Largo (m): ")
        height = self.solicitar_numero_positivo("Alto (m): ")
        utility = self.solicitar_utilidad()
        use = self.solicitar_uso()
        quantity = self.solicitar_cantidad()

        furniture_list = []
        for item_number in range(1, quantity + 1):
            furniture_name = name if quantity == 1 else f"{name} {item_number}"
            furniture_list.append(
                Mueble(
                    furniture_name,
                    width,
                    length,
                    height,
                    utility,
                    Punto3D(0, 0, 0),
                    use,
                )
            )
        return furniture_list

    def preguntar_si_no(self, prompt):
        while True:
            answer = input(f"{prompt} (s/n): ").strip().lower()
            if answer in ("s", "n"):
                return answer == "s"
            self.mostrar_error("Responda con 's' o 'n'.")

    def mostrar_distribucion(self, distribution):
        if distribution is None:
            self.mostrar_error(
                "No se encontró una distribución válida. "
                "Revise si los muebles caben en la habitación."
            )
            return

        room = distribution.get_habitacion()
        print("\nMEJOR DISTRIBUCIÓN ENCONTRADA")
        print(f"Habitación: {room.nombre}")
        print(f"Dimensiones: {room.ancho} x {room.largo} x {room.alto} m")

        if not distribution.get_muebles():
            print("Estado: habitación vacía")
            print("Muebles: 0")
            print("Puntaje: 0.00")
        else:
            print(distribution)

    def mostrar_plano(self, distribution, alternative_number=1):
        room = distribution.get_habitacion()
        figure, axes = blt.subplots(
            num=f"EasySpacey - Alternativa {alternative_number}",
            figsize=(9, 6),
        )
        room_patch = Rectangle(
            (0, 0), room.ancho, room.largo,
            fill=False, edgecolor="black", linewidth=4,
        )
        axes.add_patch(room_patch)

        colors = [
            "cornflowerblue", "lightcoral", "mediumseagreen", "khaki",
            "plum", "lightsalmon", "turquoise", "silver",
        ]
        legend_items = []
        for index, furniture in enumerate(distribution.get_muebles()):
            color = colors[index % len(colors)]
            position = furniture.posicion
            furniture_patch = Rectangle(
                (position.x, position.y), furniture.ancho, furniture.largo,
                facecolor=color, edgecolor="black", linewidth=2, alpha=0.85,
            )
            axes.add_patch(furniture_patch)
            axes.text(
                position.x + furniture.ancho / 2,
                position.y + furniture.largo / 2,
                furniture.nombre,
                ha="center", va="center", fontsize=9,
            )
            legend_items.append(
                Patch(
                    facecolor=color,
                    edgecolor="black",
                    label=(
                        f"{furniture.nombre}: {furniture.ancho} x "
                        f"{furniture.largo} m | {furniture.uso} | "
                        f"utilidad {furniture.utilidad}"
                    ),
                )
            )

        margin_x = max(room.ancho * 0.03, 0.1)
        margin_y = max(room.largo * 0.03, 0.1)
        axes.set_xlim(-margin_x, room.ancho + margin_x)
        axes.set_ylim(room.largo + margin_y, -margin_y)
        axes.set_aspect("equal", adjustable="box")
        axes.set_xlabel("Ancho - eje X (m)")
        axes.set_ylabel("Largo - eje Y (m)")
        axes.set_title(
            f"Alternativa {alternative_number} - {room.nombre}\n"
            f"Puntaje: {distribution.get_puntaje():.2f}"
        )
        axes.grid(True, linestyle=":", alpha=0.35)

        if legend_items:
            axes.legend(
                handles=legend_items,
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
            )
            figure.subplots_adjust(right=0.72)
        else:
            axes.text(
                room.ancho / 2,
                room.largo / 2,
                "Habitación vacía",
                ha="center", va="center", fontsize=15, color="gray",
            )
        return figure

    def mostrar_planos(self, distributions, limit=3):
        if not distributions:
            self.mostrar_error("No se encontraron distribuciones válidas.")
            return

        blt.close("all")
        for alternative_number, distribution in enumerate(
            distributions[:limit], start=1
        ):
            self.mostrar_plano(distribution, alternative_number)
        blt.show()

    def mostrar_distribuciones(self, distributions, limit=3):
        if not distributions:
            self.mostrar_distribucion(None)
            return

        print(f"\nSe encontraron {len(distributions)} alternativas válidas.")
        for number, distribution in enumerate(distributions[:limit], start=1):
            print(f"\nALTERNATIVA {number}")
            print(distribution)

    def ejecutar(self):
        print("=== EASYSPACEY ===")
        room = self.solicitar_habitacion()

        while self.preguntar_si_no("¿Desea agregar un tipo de mueble?"):
            new_furniture = self.solicitar_muebles()
            for furniture in new_furniture:
                room.agregar_mueble(furniture)
            self.mostrar_mensaje(
                f"{len(new_furniture)} mueble(s) agregado(s) correctamente."
            )

        if not room.get_muebles():
            empty_distribution = Distribucion(room)
            empty_distribution.validar()
            empty_distribution.calcular_puntaje()
            self.mostrar_distribucion(empty_distribution)
            self.mostrar_planos([empty_distribution], limit=1)
            return

        self.mostrar_mensaje("\nGenerando distribuciones...")
        distributions = Distribucion.generar_distribuciones(room, amount=200)
        if not distributions:
            self.mostrar_distribucion(None)
            return

        best_distributions = distributions[:3]
        self.mostrar_distribuciones(best_distributions, limit=3)
        self.mostrar_planos(best_distributions, limit=3)


if __name__ == "__main__":
    Vista().ejecutar()
