# Vista de consola y visualización de las tres mejores distribuciones.
import math
import matplotlib.pyplot as blt
from matplotlib.patches import Patch, Rectangle
from distribucion import Distribucion
from habitacion import Habitacion
from mueble import Mueble
from punto3d import Punto3D
from restriccion import Restriccion
from persistencia import guardar_proyecto, cargar_proyecto
class Vista:
    # Gestiona entradas, proyectos y visualización de distribuciones.
    # Muestra mensajes informativos en consola.
    def mostrar_mensaje(self, message):
        print(message)
    # Muestra errores de entrada o procesamiento.
    def mostrar_error(self, message):
        print(f"Error: {message}")
    # VALIDACIONES Y ENTRADAS
    # Solicita texto y rechaza entradas vacías.
    def solicitar_texto(self, prompt):
        while True:
            text = input(prompt).strip()
            if text:
                return text
            self.mostrar_error("Este dato no puede quedar vacío.")
    # Solicita números positivos y controla errores de formato.
    def solicitar_numero_positivo(self, prompt):
        while True:
            try:
                number = float(input(prompt))
                if math.isfinite(number) and number > 0:
                    return number
                
                self.mostrar_error("El número debe ser mayor que cero.")
                #except es el exception
            except ValueError:
                self.mostrar_error("Debe ingresar un número válido.")
    # Valida la utilidad del mueble entre 1 y 10.
    def solicitar_utilidad(self):
        while True:
            try:
                utility = int(input("Utilidad del mueble (1-10): "))
                if 1 <= utility <= 10:
                    return utility
                self.mostrar_error("La utilidad debe estar entre 1 y 10.")
            except ValueError:
                self.mostrar_error("Debe ingresar un número entero.")
    # Permite elegir el propósito principal del mueble.
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
            choice = input("Seleccione una opción: ").strip() #Eliminación de espacios
            if choice not in uses:
                self.mostrar_error("Seleccione una opción del 1 al 7.")
                continue
            if choice == "7":
                return self.solicitar_texto("Escriba el uso: ").title()
            return uses[choice]
    # Solicita dimensiones y crea la habitación.
    def solicitar_habitacion(self):
        print("\nCREAR HABITACIÓN")
        name = self.solicitar_texto("Nombre: ")
        width = self.solicitar_numero_positivo("Ancho (m): ")
        length = self.solicitar_numero_positivo("Largo (m): ")
        height = self.solicitar_numero_positivo("Alto (m): ")
        room = Habitacion(
            name,
            width,
            length,
            height
        )
        while self.preguntar_si_no("¿Desea agregar una puerta o ventana?"):
            room.agregar_restriccion(self.solicitar_restriccion(room))
            self.mostrar_mensaje("Restricción agregada correctamente.")
        return room

    def solicitar_opcion(self, title, options):
        print(title)
        for number, label in options.items():
            print(f"{number}. {label}")
        while True:
            choice = input("Seleccione una opción: ").strip()
            if choice in options:
                return options[choice]
            self.mostrar_error("Seleccione una opción disponible.")

    def solicitar_restriccion(self, room):
        print("\nAGREGAR PUERTA O VENTANA")
        restriction_type = self.solicitar_opcion(
            "Tipo:", {"1": "Puerta", "2": "Ventana"}
        )
        wall = self.solicitar_opcion(
            "Pared:",
            {"1": "Superior", "2": "Inferior", "3": "Izquierda", "4": "Derecha"}
        )
        horizontal = wall in ("Superior", "Inferior")
        labels = (
            {"1": "Izquierda", "2": "Centro", "3": "Derecha"}
            if horizontal
            else {"1": "Arriba", "2": "Centro", "3": "Abajo"}
        )
        displayed_section = self.solicitar_opcion("Posición aproximada:", labels)
        section = {
            "Izquierda": "Inicio", "Arriba": "Inicio", "Centro": "Centro",
            "Derecha": "Final", "Abajo": "Final"
        }[displayed_section]

        while True:
            width = self.solicitar_numero_positivo("Ancho sobre la pared (m): ")
            height = self.solicitar_numero_positivo("Alto (m): ")
            if restriction_type == "Puerta":
                depth = width
                self.mostrar_mensaje(
                    f"Área libre para abrir: {width:.2f} x {width:.2f} m."
                )
            else:
                depth = self.solicitar_numero_positivo(
                    "Profundidad libre frente a la ventana (m, sugerido 0.50): "
                )
            try:
                return Restriccion.crear_desde_pared(
                    room, restriction_type, wall, section,
                    width, height, depth
                )
            except ValueError as error:
                self.mostrar_error(str(error))
    # Solicita una cantidad entera mayor que cero.
    def solicitar_cantidad(self):
        while True:
            try:
                quantity = int(
                    input("Cantidad de este mueble: ")
                )
                if quantity > 0:
                    return quantity
                self.mostrar_error("La cantidad debe ser mayor que cero.")
            except ValueError:
                self.mostrar_error("Debe ingresar un número entero.")
    # Crea uno o varios muebles con los datos ingresados.
    def solicitar_muebles(self):
        print("\nAGREGAR MUEBLE")
        name = self.solicitar_texto("Nombre: ")
        width = self.solicitar_numero_positivo(
            "Ancho (m): "
        )
        length = self.solicitar_numero_positivo(
            "Largo (m): "
        )
        height = self.solicitar_numero_positivo(
            "Alto (m): "
        )
        utility = self.solicitar_utilidad()
        use = self.solicitar_uso()
        quantity = self.solicitar_cantidad()
        furniture_list = []
        for item_number in range(
            1,
            quantity + 1
        ):
            furniture_name = (
                name
                if quantity == 1
                else f"{name} {item_number}"
            )
            furniture_list.append(
                Mueble(
                    furniture_name,
                    width,
                    length,
                    height,
                    utility,
                    Punto3D(0, 0, 0),
                    use
                )
            )
        return furniture_list
    # Convierte una respuesta s/n en un valor booleano.
    def preguntar_si_no(self, prompt):
        while True:
            answer = input(
                f"{prompt} (s/n): "
            ).strip().lower()
            if answer in ("s", "n"):
                return answer == "s"
            self.mostrar_error(
                "Responda con 's' o 'n'."
            )
    # =====================================================
    # PERSISTENCIA
    # =====================================================
    # Muestra las opciones de crear, cargar o salir.
    def menu_inicial(self):
        while True:
            print("\n=== EASYSPACEY ===")
            print("1. Crear nuevo proyecto")
            print("2. Cargar proyecto")
            print("3. Salir")
            opcion = input(
                "Seleccione una opción: "
            ).strip()
            if opcion in ("1", "2", "3"):
                return opcion
            self.mostrar_error(
                "Seleccione una opción del 1 al 3."
            )
    # Solicita un archivo JSON y carga la habitación.
    def solicitar_cargar_proyecto(self):
        nombre_archivo = self.solicitar_texto(
            "Nombre del archivo JSON: "
        )
        if not nombre_archivo.endswith(".json"):
            nombre_archivo += ".json"
        return cargar_proyecto(
            nombre_archivo
        )
    # Pregunta si se desea guardar la habitación en JSON.
    def solicitar_guardar_proyecto(
        self,
        habitacion
    ):
        if not self.preguntar_si_no(
            "¿Desea guardar el proyecto?"
        ):
            return
        nombre_archivo = self.solicitar_texto(
            "Nombre del archivo: "
        )
        if not nombre_archivo.endswith(".json"):
            nombre_archivo += ".json"
        guardar_proyecto(
            habitacion,
            nombre_archivo
        )
    # =====================================================
    # MOSTRAR RESULTADOS
    # =====================================================
    # Muestra el resultado textual de una distribución.
    def mostrar_distribucion(
        self,
        distribution
    ):
        if distribution is None:
            self.mostrar_error(
                "No se encontró una distribución válida. "
                "Revise si los muebles caben en la habitación."
            )
            return
        room = distribution.get_habitacion()
        print(
            "\nMEJOR DISTRIBUCIÓN ENCONTRADA"
        )
        print(
            f"Habitación: {room.nombre}"
        )
        print(
            f"Dimensiones: "
            f"{room.ancho} x "
            f"{room.largo} x "
            f"{room.alto} m"
        )
        print(f"Puertas/ventanas: {len(room.get_restricciones())}")
        if not distribution.get_muebles():
            print(
                "Estado: habitación vacía"
            )
            print("Muebles: 0")
            print("Puntaje: 0.00")
        else:
            print(distribution)
    # =====================================================
    # VISUALIZACIÓN
    # =====================================================
    # Dibuja la habitación y los muebles en vista superior.
    def mostrar_plano(
        self,
        distribution,
        alternative_number=1
    ):
        room = distribution.get_habitacion()
        figure, axes = blt.subplots(
            num=(
                f"EasySpacey - "
                f"Alternativa "
                f"{alternative_number}"
            ),
            figsize=(9, 6),
        )
        room_patch = Rectangle(
            (0, 0),
            room.ancho,
            room.largo,
            fill=False,
            edgecolor="black",
            linewidth=4,
        )
        axes.add_patch(room_patch)
        colors = [
            "cornflowerblue",
            "lightcoral",
            "mediumseagreen",
            "khaki",
            "plum",
            "lightsalmon",
            "turquoise",
            "silver",
        ]
        legend_items = []
        for restriction in room.get_restricciones():
            restricted_width, restricted_length = restriction.get_floor_dimensions()
            color = "tomato" if restriction.tipo == "Puerta" else "deepskyblue"
            restriction_patch = Rectangle(
                (restriction.posicion.x, restriction.posicion.y),
                restricted_width,
                restricted_length,
                facecolor=color,
                edgecolor="black",
                linewidth=2,
                alpha=0.35,
                hatch="//"
            )
            axes.add_patch(restriction_patch)
            axes.text(
                restriction.posicion.x + restricted_width / 2,
                restriction.posicion.y + restricted_length / 2,
                restriction.tipo,
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold"
            )
            legend_items.append(Patch(
                facecolor=color,
                edgecolor="black",
                alpha=0.35,
                hatch="//",
                label=f"{restriction.tipo}: {restriction.pared}, {restriction.ancho} m"
            ))
        for index, furniture in enumerate(
            distribution.get_muebles()
        ):
            color = colors[
                index % len(colors)
            ]
            position = furniture.posicion
            furniture_patch = Rectangle(
                (
                    position.x,
                    position.y
                ),
                furniture.ancho,
                furniture.largo,
                facecolor=color,
                edgecolor="black",
                linewidth=2,
                alpha=0.85,
            )
            axes.add_patch(
                furniture_patch
            )
            axes.text(
                position.x
                + furniture.ancho / 2,
                position.y
                + furniture.largo / 2,
                furniture.nombre,
                ha="center",
                va="center",
                fontsize=9,
            )
            legend_items.append(
                Patch(
                    facecolor=color,
                    edgecolor="black",
                    label=(
                        f"{furniture.nombre}: "
                        f"{furniture.ancho} x "
                        f"{furniture.largo} m | "
                        f"{furniture.uso} | "
                        f"utilidad "
                        f"{furniture.utilidad}"
                    ),
                )
            )
        margin_x = max(
            room.ancho * 0.03,
            0.1
        )
        margin_y = max(
            room.largo * 0.03,
            0.1
        )
        axes.set_xlim(
            -margin_x,
            room.ancho + margin_x
        )
        axes.set_ylim(
            room.largo + margin_y,
            -margin_y
        )
        axes.set_aspect(
            "equal",
            adjustable="box"
        )
        axes.set_xlabel(
            "Ancho - eje X (m)"
        )
        axes.set_ylabel(
            "Largo - eje Y (m)"
        )
        axes.set_title(
            f"Alternativa "
            f"{alternative_number} - "
            f"{room.nombre}\n"
            f"Puntaje: "
            f"{distribution.get_puntaje():.2f}"
        )
        axes.grid(
            True,
            linestyle=":",
            alpha=0.35
        )
        if legend_items:
            axes.legend(
                handles=legend_items,
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
            )
            figure.subplots_adjust(
                right=0.72
            )
        else:
            axes.text(
                room.ancho / 2,
                room.largo / 2,
                "Habitación vacía",
                ha="center",
                va="center",
                fontsize=15,
                color="gray",
            )
        return figure
    # Presenta gráficamente las mejores alternativas.
    def mostrar_planos(
        self,
        distributions,
        limit=3
    ):
        if not distributions:
            self.mostrar_error(
                "No se encontraron "
                "distribuciones válidas."
            )
            return
        blt.close("all")
        for (
            alternative_number,
            distribution
        ) in enumerate(
            distributions[:limit],
            start=1
        ):
            self.mostrar_plano(
                distribution,
                alternative_number
            )
        blt.show()
    # Muestra los puntajes y muebles de cada alternativa.
    def mostrar_distribuciones(
        self,
        distributions,
        limit=3
    ):
        if not distributions:
            self.mostrar_distribucion(
                None
            )
            return
        print(
            f"\nSe encontraron "
            f"{len(distributions)} "
            f"alternativas válidas."
        )
        for number, distribution in enumerate(
            distributions[:limit],
            start=1
        ):
            print(
                f"\nALTERNATIVA {number}"
            )
            print(distribution)
    # =====================================================
    # EJECUCIÓN PRINCIPAL
    # =====================================================
    # Coordina el flujo principal de EasySpacey.
    
    # Mantiene el menú disponible después de terminar cada operación.
    def ejecutar(self):
        while True:
            continuar = self.ejecutar_proyecto()

            if continuar is False:
                break
    
    def ejecutar_proyecto(self):
        opcion = self.menu_inicial()
        # -----------------------------
        # SALIR
        # -----------------------------
        if opcion == "3":
            self.mostrar_mensaje(
                "Hasta luego."
            )
            return False
        # -----------------------------
        # NUEVO PROYECTO
        # -----------------------------
        if opcion == "1":
            room = self.solicitar_habitacion()
            while self.preguntar_si_no(
                "¿Desea agregar "
                "un tipo de mueble?"
            ):
                new_furniture = (
                    self.solicitar_muebles()
                )
                for furniture in (
                    new_furniture
                ):
                    room.agregar_mueble(
                        furniture
                    )
                self.mostrar_mensaje(
                    f"{len(new_furniture)} "
                    f"mueble(s) agregado(s) "
                    f"correctamente."
                )
            
        # -----------------------------
        # CARGAR PROYECTO
        # -----------------------------
        elif opcion == "2":
            room = (
                self.solicitar_cargar_proyecto()
            )
            if room is None:
                self.mostrar_error(
                    "No fue posible "
                    "cargar el proyecto."
                )
                return
            self.mostrar_mensaje(
                f"Proyecto "
                f"'{room.get_nombre()}' "
                f"cargado correctamente."
            )

                    # Comprueba el espacio antes de intentar distribuir los muebles.
        if not Distribucion.verificar_espacio(room):
            self.mostrar_error(
                "Los muebles no caben en la habitación según "
                "las dimensiones o la superficie disponible."
            )
            return

        # Permite guardar el proyecto después de comprobar el espacio.
        if opcion == "1":
            self.solicitar_guardar_proyecto(room)

            
        # -----------------------------
        # HABITACIÓN VACÍA
        # -----------------------------
        if not room.get_muebles():
            empty_distribution = (
                Distribucion(room)
            )
            empty_distribution.validar()
            empty_distribution.calcular_puntaje()
            self.mostrar_distribucion(
                empty_distribution
            )
            self.mostrar_planos(
                [empty_distribution],
                limit=1
            )
            return
        # -----------------------------
        # GENERAR DISTRIBUCIONES
        # -----------------------------
        self.mostrar_mensaje(
            "\nGenerando distribuciones..."
        )
        distributions = (
            Distribucion.generar_distribuciones(
                room,
                amount=200
            )
        )
        if not distributions:
            self.mostrar_distribucion(
                None
            )
            return
        best_distributions = (
            distributions[:3]
        )
        self.mostrar_distribuciones(
            best_distributions,
            limit=3
        )
        self.mostrar_planos(
            best_distributions,
            limit=3
        )
if __name__ == "__main__":
                                                                       
    from interfaz_grafica import MatplotlibInterface
    MatplotlibInterface().run()
