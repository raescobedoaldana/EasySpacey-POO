from copy import deepcopy
from math import ceil, floor, hypot
from random import Random

from punto3d import Punto3D


# Genera, valida y evalua configuraciones de muebles.
class Distribucion:
    # Peso del beneficio por acercar muebles con el mismo uso.
    PURPOSE_PROXIMITY_WEIGHT = 8.0
    # Separacion minima considerada aprovechable.
    MINIMUM_USEFUL_GAP = 0.15
    # Intensidad de la penalizacion por huecos pequenos.
    WASTED_GAP_PENALTY = 24.0
    # Resolucion centimetrica propuesta junto con Dominic.
    GRID_STEP = 0.01
    # Peso de la cercania electrica acordada por Raul y Dominic.
    ELECTRICAL_PROXIMITY_WEIGHT = 8.0

    # Inicializa una distribucion con copias independientes de muebles.
    def __init__(self, room, furniture=None):
        self.habitacion = room
        source_furniture = room.get_muebles() if furniture is None else furniture
        # Evita que mover una alternativa cambie los muebles originales.
        self.muebles = deepcopy(source_furniture)
        # Conserva el indice original aunque el algoritmo ordene los muebles.
        for index, item in enumerate(self.muebles):
            item._source_index = index
        self.puntaje = 0.0
        self.valida = False

    # Devuelve la habitacion asociada.
    def get_habitacion(self):
        return self.habitacion

    # Devuelve los muebles de esta alternativa.
    def get_muebles(self):
        return self.muebles

    # Devuelve la puntuacion calculada.
    def get_puntaje(self):
        return self.puntaje

    # Indica si la distribucion supera las validaciones.
    def es_valida(self):
        return self.valida

    # Agrega una copia del mueble a la alternativa.
    def agregar_mueble(self, furniture):
        self.muebles.append(deepcopy(furniture))

    # Elimina un mueble de la alternativa.
    def eliminar_mueble(self, furniture):
        self.muebles.remove(furniture)

    def _supporting_furniture(self, furniture):
        if furniture.get_placement_type() != "Sobre objeto":
            return None
        tolerance = 1e-9
        for support in self.muebles:
            if support is furniture or not support.can_support_objects():
                continue
            touches_top = abs(
                furniture.posicion.z
                - (support.posicion.z + support.alto)
            ) <= tolerance
            fits_x = (
                furniture.posicion.x >= support.posicion.x - tolerance
                and furniture.posicion.x + furniture.ancho
                <= support.posicion.x + support.ancho + tolerance
            )
            fits_y = (
                furniture.posicion.y >= support.posicion.y - tolerance
                and furniture.posicion.y + furniture.largo
                <= support.posicion.y + support.largo + tolerance
            )
            if touches_top and fits_x and fits_y:
                return support
        return None

    # Comprueba que el mueble este apoyado y dentro de la habitacion.
    def mueble_esta_dentro(self, furniture):
        position = furniture.posicion
        inside_bounds = (
            position.x >= 0
            and position.y >= 0
            and position.z >= 0
            and position.x + furniture.ancho <= self.habitacion.ancho
            and position.y + furniture.largo <= self.habitacion.largo
            and position.z + furniture.alto <= self.habitacion.alto
        )
        if not inside_bounds:
            return False
        if furniture.get_placement_type() == "Suelo":
            return abs(position.z) <= 1e-9
        if furniture.get_placement_type() == "Pared":
            touches = {
                "Superior": abs(position.y) <= 1e-9,
                "Inferior": abs(position.y + furniture.largo - self.habitacion.largo) <= 1e-9,
                "Izquierda": abs(position.x) <= 1e-9,
                "Derecha": abs(position.x + furniture.ancho - self.habitacion.ancho) <= 1e-9,
            }
            preferred = furniture.get_preferred_wall()
            if preferred == "Automática":
                return any(touches.values())
            return touches.get(preferred, False)
        return self._supporting_furniture(furniture) is not None

    @staticmethod
    # Detecta interseccion tridimensional entre dos muebles.
    def muebles_se_traslapan(furniture_a, furniture_b):
        position_a = furniture_a.posicion
        position_b = furniture_b.posicion

        separated_x = (
            position_a.x + furniture_a.ancho <= position_b.x
            or position_b.x + furniture_b.ancho <= position_a.x
        )
        separated_y = (
            position_a.y + furniture_a.largo <= position_b.y
            or position_b.y + furniture_b.largo <= position_a.y
        )
        separated_z = (
            position_a.z + furniture_a.alto <= position_b.z
            or position_b.z + furniture_b.alto <= position_a.z
        )
        return not (separated_x or separated_y or separated_z)

    # Busca traslapes entre todos los pares de muebles.
    def tiene_colisiones(self):
        for index_a in range(len(self.muebles)):
            for index_b in range(index_a + 1, len(self.muebles)):
                if self.muebles_se_traslapan(
                    self.muebles[index_a], self.muebles[index_b]
                ):
                    return True
        return False

    @staticmethod
    # Detecta interseccion en planta con una zona restringida.
    def furniture_overlaps_restriction(furniture, restriction):
        restricted_width, restricted_length = restriction.get_floor_dimensions()
        furniture_position = furniture.posicion
        restriction_position = restriction.posicion
        separated_x = (
            furniture_position.x + furniture.ancho <= restriction_position.x
            or restriction_position.x + restricted_width <= furniture_position.x
        )
        separated_y = (
            furniture_position.y + furniture.largo <= restriction_position.y
            or restriction_position.y + restricted_length <= furniture_position.y
        )
        return not (separated_x or separated_y)

    # Comprueba si uno o varios muebles invaden restricciones.
    def overlaps_restrictions(self, furniture=None):
        items = self.muebles if furniture is None else [furniture]
        return any(
            self.furniture_overlaps_restriction(item, restriction)
            for item in items
            for restriction in self.habitacion.get_restricciones()
        )

    # Valida limites, traslapes y restricciones.
    def validar(self):
        all_inside = all(
            self.mueble_esta_dentro(item) for item in self.muebles
        )
        self.valida = (
            all_inside
            and not self.tiene_colisiones()
            and not self.overlaps_restrictions()
        )
        return self.valida

        # Comprueba si existen impedimentos evidentes para colocar los muebles.

    @staticmethod
    # Descarta muebles demasiado grandes o exceso de superficie.
    def verificar_espacio(habitacion):
        muebles = habitacion.get_muebles()

        superficie_habitacion = habitacion.ancho * habitacion.largo
        superficie_muebles = 0

        for mueble in muebles:
            # Un mueble girable puede caber solo al intercambiar ancho y largo.
            cabe_actual = (mueble.ancho <= habitacion.ancho
                           and mueble.largo <= habitacion.largo)
            cabe_girado = (mueble.puede_rotar() and not mueble.esta_fijado()
                           and mueble.largo <= habitacion.ancho
                           and mueble.ancho <= habitacion.largo)
            if (not (cabe_actual or cabe_girado)
                    or mueble.alto > habitacion.alto):
                return False

            if mueble.get_placement_type() == "Suelo":
                superficie_muebles += mueble.ancho * mueble.largo
            elif mueble.get_placement_type() == "Pared":
                if mueble.get_wall_height() + mueble.alto > habitacion.alto:
                    return False
                wall = mueble.get_preferred_wall()
                horizontal_fit = (
                    mueble.ancho <= habitacion.ancho
                    and mueble.largo <= habitacion.largo
                )
                vertical_fit = (
                    mueble.largo <= habitacion.ancho
                    and mueble.ancho <= habitacion.largo
                )
                if wall in ("Superior", "Inferior") and not horizontal_fit:
                    return False
                if wall in ("Izquierda", "Derecha") and not vertical_fit:
                    return False
                if wall == "Automática" and not (horizontal_fit or vertical_fit):
                    return False

        supports = [item for item in muebles if item.can_support_objects()]
        for item in muebles:
            if item.get_placement_type() != "Sobre objeto":
                continue
            can_fit = any(
                support is not item
                and (
                    (item.ancho <= support.ancho and item.largo <= support.largo)
                    or (
                        item.puede_rotar()
                        and item.largo <= support.ancho
                        and item.ancho <= support.largo
                    )
                )
                and support.get_wall_height() + support.alto + item.alto <= habitacion.alto
                for support in supports
            )
            if not can_fit:
                return False

        if superficie_muebles > superficie_habitacion:
            return False

        return True

    # Mide la separación entre un mueble y una restricción en planta.
    @staticmethod
    def _distancia_restriccion(furniture, restriction):
        width, length = restriction.get_floor_dimensions()
        x1, y1 = furniture.posicion.x, furniture.posicion.y
        x2, y2 = restriction.posicion.x, restriction.posicion.y
        gap_x = max(x1 - (x2 + width), x2 - (x1 + furniture.ancho), 0.0)
        gap_y = max(y1 - (y2 + length), y2 - (y1 + furniture.largo), 0.0)
        return hypot(gap_x, gap_y)

    def _place_on_wall(self, furniture, placed_furniture, attempts, random_generator):
        preferred = furniture.get_preferred_wall()
        walls = ([preferred] if preferred != "Automática" else
                 ["Superior", "Inferior", "Izquierda", "Derecha"])
        random_generator.shuffle(walls)
        original_rotation = furniture.get_rotacion()
        candidates = []
        z = furniture.get_wall_height()
        if z + furniture.alto > self.habitacion.alto:
            return False

        for wall in walls:
            orientation = 0 if wall in ("Superior", "Inferior") else 90
            furniture.set_rotacion(orientation)
            if wall in ("Superior", "Inferior"):
                maximum_cm = floor(
                    (self.habitacion.ancho - furniture.ancho) * 100 + 1e-9
                )
            else:
                maximum_cm = floor(
                    (self.habitacion.largo - furniture.largo) * 100 + 1e-9
                )
            if maximum_cm < 0:
                continue
            for attempt in range(min(attempts, 30)):
                mode = attempt % 4
                if mode == 0:
                    offset_cm = 0
                elif mode == 1:
                    offset_cm = maximum_cm
                elif mode == 2:
                    offset_cm = maximum_cm // 2
                else:
                    offset_cm = random_generator.randint(0, maximum_cm)
                offset = offset_cm / 100
                if wall == "Superior":
                    x, y = offset, 0.0
                elif wall == "Inferior":
                    x, y = offset, self.habitacion.largo - furniture.largo
                elif wall == "Izquierda":
                    x, y = 0.0, offset
                else:
                    x, y = self.habitacion.ancho - furniture.ancho, offset
                furniture.set_posicion(Punto3D(x, y, z))
                if any(
                    self.muebles_se_traslapan(furniture, other)
                    for other in placed_furniture
                ) or self.overlaps_restrictions(furniture):
                    continue
                candidates.append((x, y, z, orientation, wall))
                break

        if not candidates:
            furniture.set_rotacion(original_rotation)
            return False
        x, y, z, orientation, wall = random_generator.choice(candidates)
        furniture.set_rotacion(orientation)
        furniture.set_preferred_wall(wall)
        furniture.set_posicion(Punto3D(x, y, z))
        return True

    def _place_on_surface(self, furniture, placed_furniture, attempts, random_generator):
        supports = [item for item in placed_furniture if item.can_support_objects()]
        random_generator.shuffle(supports)
        original_rotation = furniture.get_rotacion()
        orientations = [original_rotation]
        if furniture.puede_rotar() and furniture.ancho != furniture.largo:
            orientations.append(90 if original_rotation == 0 else 0)
        candidates = []

        for support in supports:
            for orientation in orientations:
                furniture.set_rotacion(orientation)
                min_x_cm = ceil((support.posicion.x - 1e-9) * 100)
                min_y_cm = ceil((support.posicion.y - 1e-9) * 100)
                max_x_cm = floor(
                    (support.posicion.x + support.ancho - furniture.ancho) * 100 + 1e-9
                )
                max_y_cm = floor(
                    (support.posicion.y + support.largo - furniture.largo) * 100 + 1e-9
                )
                z = round(support.posicion.z + support.alto, 2)
                if max_x_cm < min_x_cm or max_y_cm < min_y_cm:
                    continue
                if z + furniture.alto > self.habitacion.alto:
                    continue

                for attempt in range(min(attempts, 30)):
                    mode = attempt % 6
                    if mode == 0:
                        x_cm, y_cm = min_x_cm, min_y_cm
                    elif mode == 1:
                        x_cm, y_cm = max_x_cm, min_y_cm
                    elif mode == 2:
                        x_cm, y_cm = min_x_cm, max_y_cm
                    elif mode == 3:
                        x_cm, y_cm = max_x_cm, max_y_cm
                    elif mode == 4:
                        x_cm = (min_x_cm + max_x_cm) // 2
                        y_cm = (min_y_cm + max_y_cm) // 2
                    else:
                        x_cm = random_generator.randint(min_x_cm, max_x_cm)
                        y_cm = random_generator.randint(min_y_cm, max_y_cm)
                    furniture.set_posicion(Punto3D(x_cm / 100, y_cm / 100, z))
                    if any(
                        self.muebles_se_traslapan(furniture, other)
                        for other in placed_furniture
                    ):
                        continue
                    same_purpose = int(
                        furniture.uso.casefold() == support.uso.casefold()
                    )
                    candidates.append(
                        (same_purpose, support.utilidad, x_cm / 100, y_cm / 100, z, orientation)
                    )
                    break

        if not candidates:
            furniture.set_rotacion(original_rotation)
            return False
        best_purpose = max(candidate[0] for candidate in candidates)
        preferred = [candidate for candidate in candidates if candidate[0] == best_purpose]
        _, _, x, y, z, orientation = random_generator.choice(preferred)
        furniture.set_rotacion(orientation)
        furniture.set_posicion(Punto3D(x, y, z))
        return True

    # Coloca muebles sin favorecer siempre la pared izquierda.
    def colocar_muebles(self, attempts_per_item=250, random_generator=None):
        random_generator = random_generator if random_generator is not None else Random()
        placed_furniture = []
        restrictions = self.habitacion.get_restricciones()
        placement_order = {"Suelo": 0, "Pared": 1, "Sobre objeto": 2}
        self.muebles.sort(key=lambda item: (
            placement_order[item.get_placement_type()],
            -item.calcular_volumen()
        ))

        # Coloca primero los fijados para que los otros respeten su espacio.
        pinned = [item for item in self.muebles if item.esta_fijado()]
        free = [item for item in self.muebles if not item.esta_fijado()]
        # Los apoyos fijados deben existir antes de validar objetos apilados.
        self.muebles = pinned + free
        for item in pinned:
            if not self.mueble_esta_dentro(item):
                self.valida = False
                return False
            if self.overlaps_restrictions(item) or any(
                self.muebles_se_traslapan(item, other) for other in placed_furniture
            ):
                self.valida = False
                return False
            placed_furniture.append(item)

        for furniture in free:
            if furniture.get_placement_type() == "Pared":
                if not self._place_on_wall(
                    furniture, placed_furniture, attempts_per_item, random_generator
                ):
                    self.valida = False
                    return False
                placed_furniture.append(furniture)
                continue
            if furniture.get_placement_type() == "Sobre objeto":
                if not self._place_on_surface(
                    furniture, placed_furniture, attempts_per_item, random_generator
                ):
                    self.valida = False
                    return False
                placed_furniture.append(furniture)
                continue
            # Prueba 0 y 90 grados solo si el mueble permite rotacion.
            original_rotation = furniture.get_rotacion()
            orientations = [original_rotation]
            if furniture.puede_rotar() and furniture.ancho != furniture.largo:
                orientations.append(90 if original_rotation == 0 else 0)

            # Mezcla las orientaciones para no favorecer siempre la original.
            random_generator.shuffle(orientations)
            valid_positions = []
            modes = list(range(5))

            # Mantiene el limite total de intentos por mueble.
            for attempt in range(attempts_per_item):
                orientation = orientations[attempt % len(orientations)]
                furniture.set_rotacion(orientation)
                max_x = self.habitacion.ancho - furniture.ancho
                max_y = self.habitacion.largo - furniture.largo
                if max_x < 0 or max_y < 0 or furniture.alto > self.habitacion.alto:
                    continue

                if attempt % len(modes) == 0:
                    random_generator.shuffle(modes)
                mode = modes[attempt % len(modes)]
                # Genera posiciones en centimetros enteros sin crear una matriz.
                max_x_cm = max(0, floor(max_x * 100 + 1e-9))
                max_y_cm = max(0, floor(max_y * 100 + 1e-9))
                x_cm = (0 if mode == 0 else max_x_cm if mode == 1
                        else random_generator.randint(0, max_x_cm))
                y_cm = (0 if mode == 2 else max_y_cm if mode == 3
                        else random_generator.randint(0, max_y_cm))
                furniture.set_posicion(Punto3D(x_cm / 100, y_cm / 100, 0.0))

                # Rechaza posiciones que invaden muebles o restricciones.
                has_collision = any(
                    self.muebles_se_traslapan(furniture, other)
                    for other in placed_furniture
                )
                if has_collision or self.overlaps_restrictions(furniture):
                    continue

                if restrictions:
                    clearance = min(
                        self._distancia_restriccion(furniture, restriction)
                        for restriction in restrictions
                    )
                else:
                    clearance = 0.0
                valid_positions.append((clearance, x_cm / 100, y_cm / 100, orientation))
                if len(valid_positions) >= 8:
                    break

            if not valid_positions:
                furniture.set_rotacion(original_rotation)
                self.valida = False
                return False

            # Con restricciones, prefiere separacion; sin ellas, elige al azar.
            if restrictions:
                best_clearance = max(item[0] for item in valid_positions)
                choices = [item for item in valid_positions if item[0] >= best_clearance - 1e-9]
            else:
                choices = valid_positions
            _, x, y, orientation = random_generator.choice(choices)
            furniture.set_rotacion(orientation)
            furniture.set_posicion(Punto3D(x, y, 0.0))
            placed_furniture.append(furniture)

        return self.validar()

    @classmethod
    # Penaliza separaciones pequenas y poco aprovechables.
    def _dead_gap_penalty(cls, gap):
        # Penalizacion fuerte por huecos positivos menores a 15 cm; 0 cm es valido.
        gap_cm = round(gap * 100)
        if gap_cm <= 0 or gap_cm >= round(cls.MINIMUM_USEFUL_GAP * 100):
            return 0.0
        return cls.WASTED_GAP_PENALTY

    @staticmethod
    # Comprueba interseccion de intervalos con longitud positiva.
    def _intervals_overlap(start_a, end_a, start_b, end_b):
        return min(end_a, end_b) > max(start_a, start_b)

    # Calcula la distancia en planta entre un mueble y un outlet.
    @staticmethod
    def _distancia_outlet(furniture, outlet):
        x = outlet.posicion.x
        y = outlet.posicion.y
        left = furniture.posicion.x
        right = left + furniture.ancho
        top = furniture.posicion.y
        bottom = top + furniture.largo
        gap_x = max(left - x, x - right, 0.0)
        gap_y = max(top - y, y - bottom, 0.0)
        return hypot(gap_x, gap_y)

    # Premia conexiones cercanas sin superar la capacidad de los outlets.
    def calcular_bonificacion_electrica(self):
        outlets = self.habitacion.get_outlets()
        if not outlets:
            return 0.0

        # Cada outlet dispone de un numero limitado de conexiones.
        capacidades = [outlet.capacidad for outlet in outlets]
        score = 0.0
        electricos = [m for m in self.muebles if m.requiere_electricidad()]

        # Asigna primero los muebles con mayor utilidad.
        electricos.sort(key=lambda m: m.utilidad, reverse=True)
        for furniture in electricos:
            pendientes = furniture.get_conexiones_necesarias()
            opciones = sorted(
                range(len(outlets)),
                key=lambda i: self._distancia_outlet(furniture, outlets[i])
            )
            for index in opciones:
                if pendientes == 0:
                    break
                asignadas = min(pendientes, capacidades[index])
                if asignadas <= 0:
                    continue
                distancia = self._distancia_outlet(furniture, outlets[index])
                score += (asignadas * self.ELECTRICAL_PROXIMITY_WEIGHT
                          * furniture.utilidad / (1.0 + distancia))
                capacidades[index] -= asignadas
                pendientes -= asignadas

        return score

    # Evalua utilidad, cercania a paredes y separaciones.
    def calcular_puntaje(self):
        if not self.validar():
            self.puntaje = 0.0
            return self.puntaje

        score = 0.0
        for furniture in self.muebles:
            position = furniture.posicion
            if furniture.get_placement_type() == "Sobre objeto":
                support = self._supporting_furniture(furniture)
                score += furniture.utilidad * 3
                if support and furniture.uso.casefold() == support.uso.casefold():
                    score += furniture.utilidad
                continue
            wall_distances = (
                position.x,
                position.y,
                self.habitacion.ancho - (position.x + furniture.ancho),
                self.habitacion.largo - (position.y + furniture.largo),
            )

            # Evalua la distancia a paredes segun la preferencia del mueble.
            # Evita favorecer paredes para muebles que necesitan espacio alrededor.
            nearest_wall_distance = min(wall_distances)
            score += furniture.utilidad

            # Los muebles de pared deben permanecer junto a una pared.
            # No se les aplica una preferencia que contradiga su colocacion.
            if furniture.get_placement_type() == "Pared":
                wall_bonus = furniture.utilidad / (1.0 + nearest_wall_distance)
            else:
                # Los muebles antiguos mantienen la bonificacion original.
                preference = getattr(furniture, "preferencia_pared", "Cerca")

                if preference == "Cerca":
                    wall_bonus = furniture.utilidad / (1.0 + nearest_wall_distance)

                elif preference == "Lejos":
                    # La distancia normalizada evita favorecer habitaciones grandes.
                    maximum_distance = min(
                        (self.habitacion.ancho - furniture.ancho) / 2,
                        (self.habitacion.largo - furniture.largo) / 2,
                    )

                    wall_bonus = (
                        furniture.utilidad * nearest_wall_distance / maximum_distance
                        if maximum_distance > 0 else 0.0
                    )

                else:
                    # Sin preferencia no suma puntos por estar cerca o lejos.
                    wall_bonus = 0.0

            score += wall_bonus


        for index_a in range(len(self.muebles)):
            for index_b in range(index_a + 1, len(self.muebles)):
                furniture_a = self.muebles[index_a]
                furniture_b = self.muebles[index_b]

                gap_x = max(
                    furniture_a.posicion.x
                    - (furniture_b.posicion.x + furniture_b.ancho),
                    furniture_b.posicion.x
                    - (furniture_a.posicion.x + furniture_a.ancho),
                    0.0,
                )
                gap_y = max(
                    furniture_a.posicion.y
                    - (furniture_b.posicion.y + furniture_b.largo),
                    furniture_b.posicion.y
                    - (furniture_a.posicion.y + furniture_a.largo),
                    0.0,
                )

                overlaps_vertically = self._intervals_overlap(
                    furniture_a.posicion.y,
                    furniture_a.posicion.y + furniture_a.largo,
                    furniture_b.posicion.y,
                    furniture_b.posicion.y + furniture_b.largo,
                )
                overlaps_horizontally = self._intervals_overlap(
                    furniture_a.posicion.x,
                    furniture_a.posicion.x + furniture_a.ancho,
                    furniture_b.posicion.x,
                    furniture_b.posicion.x + furniture_b.ancho,
                )
                if overlaps_vertically:
                    score -= self._dead_gap_penalty(gap_x)
                if overlaps_horizontally:
                    score -= self._dead_gap_penalty(gap_y)

                if furniture_a.uso.casefold() != furniture_b.uso.casefold():
                    continue

                # Calcula separacion entre muebles del mismo uso.
                distance = hypot(gap_x, gap_y)
                average_utility = (
                    furniture_a.utilidad + furniture_b.utilidad
                ) / 2
                category_bonus = (
                    average_utility
                    * self.PURPOSE_PROXIMITY_WEIGHT
                    / (1.0 + distance)
                )
                score += category_bonus

        # Incorpora la cercania electrica al puntaje original.
        score += self.calcular_bonificacion_electrica()

        self.puntaje = round(score, 2)
        return self.puntaje

    # Identifica una configuración por mueble y coordenadas.
    # Crea una firma estable con nombres y posiciones redondeadas.
    def obtener_firma(self):
        return tuple(sorted(
            (m.nombre, round(m.posicion.x, 2), round(m.posicion.y, 2),
             round(m.posicion.z, 2), m.get_rotacion()) for m in self.muebles
        ))

    # Calcula el desplazamiento promedio de los muebles entre dos alternativas.
    def distancia_promedio(self, otra):
        posiciones = {m.nombre: m.posicion for m in otra.muebles}
        if len(posiciones) != len(otra.muebles) or set(posiciones) != {m.nombre for m in self.muebles}:
            return 0.0
        if not self.muebles:
            return 0.0
        return sum(
            hypot(m.posicion.x - posiciones[m.nombre].x,
                  m.posicion.y - posiciones[m.nombre].y)
            for m in self.muebles
        ) / len(self.muebles)

    # Exige que el desplazamiento promedio alcance la distancia minima.
    def es_diferente_de(self, otra, distancia_minima=0.5):
        if self.obtener_firma() == otra.obtener_firma():
            return False
        if self.distancia_promedio(otra) >= distancia_minima:
            return True
        # Una rotacion de un rectangulo tambien representa una alternativa distinta.
        orientaciones = {m.nombre: m.get_rotacion() for m in otra.muebles}
        return any(
            m.nombre in orientaciones and m.ancho != m.largo
            and m.get_rotacion() != orientaciones[m.nombre]
            for m in self.muebles
        )

    @classmethod
    # Genera candidatos y selecciona alternativas validas y variadas.
    def generar_distribuciones(
        cls,
        room,
        amount=100,
        attempts_per_item=250,
        seed=None,
        distancia_minima=0.5,
        limite_resultados=3,
    ):
        if amount <= 0 or limite_resultados <= 0 or distancia_minima < 0:
            return []

        random_generator = Random(seed)
        candidates = []
        for _ in range(amount):
            alternative = cls(room)
            if alternative.colocar_muebles(attempts_per_item, random_generator):
                alternative.calcular_puntaje()
                candidates.append(alternative)

        # Conserva el mejor puntaje como primera referencia.
        candidates.sort(key=lambda d: d.get_puntaje(), reverse=True)
        if not candidates:
            return []
        results = [candidates.pop(0)]

        # Busca variedad entre opciones con puntajes cercanos al mejor.
        while candidates and len(results) < limite_resultados:
            valid_candidates = [
                item for item in candidates
                if all(item.es_diferente_de(other, distancia_minima) for other in results)
            ]
            if not valid_candidates:
                break

            # Prioriza un puntaje cercano al mejor sin exigirlo cuando no hay opciones.
            best_score = results[0].get_puntaje()
            tolerance = max(abs(best_score) * 0.10, 1.0)
            competitive = [
                item for item in valid_candidates
                if item.get_puntaje() >= best_score - tolerance
            ]
            pool = competitive if competitive else valid_candidates

            # Maximiza la distancia promedio respecto a la alternativa mas cercana.
            selected = max(
                pool,
                key=lambda item: (
                    min(item.distancia_promedio(other) for other in results),
                    item.get_puntaje(),
                ),
            )
            results.append(selected)
            candidates.remove(selected)

        # Mantiene la compatibilidad con obtener_mejor().
        results.sort(key=lambda d: d.get_puntaje(), reverse=True)
        return results

    @staticmethod
    # Devuelve la primera alternativa, ordenada por puntuacion.
    def obtener_mejor(distributions):
        return distributions[0] if distributions else None

    # Resume el estado, el puntaje y las posiciones.
    def __str__(self):
        status = "válida" if self.valida else "inválida"
        lines = [f"Distribución {status} | Puntaje: {self.puntaje:.2f}"]
        for furniture in self.muebles:
            lines.append(
                f"- {furniture.nombre} | Uso: {furniture.uso} | "
                f"Posición: {furniture.posicion}"
            )
        return "\n".join(lines)

