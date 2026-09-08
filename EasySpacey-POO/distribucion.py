from copy import deepcopy
from math import hypot
from random import Random

from punto3d import Punto3D


class Distribucion:
    PURPOSE_PROXIMITY_WEIGHT = 8.0
    MINIMUM_USEFUL_GAP = 0.60
    WASTED_GAP_PENALTY = 12.0

    def __init__(self, room, furniture=None):
        self.habitacion = room
        source_furniture = room.get_muebles() if furniture is None else furniture
        self.muebles = deepcopy(source_furniture)
        self.puntaje = 0.0
        self.valida = False

    def get_habitacion(self):
        return self.habitacion

    def get_muebles(self):
        return self.muebles

    def get_puntaje(self):
        return self.puntaje

    def es_valida(self):
        return self.valida

    def agregar_mueble(self, furniture):
        self.muebles.append(deepcopy(furniture))

    def eliminar_mueble(self, furniture):
        self.muebles.remove(furniture)

    def mueble_esta_dentro(self, furniture):
        position = furniture.posicion
        return (
            position.x >= 0
            and position.y >= 0
            and position.z >= 0
            and position.x + furniture.ancho <= self.habitacion.ancho
            and position.y + furniture.largo <= self.habitacion.largo
            and position.z + furniture.alto <= self.habitacion.alto
        )

    @staticmethod
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

    def tiene_colisiones(self):
        for index_a in range(len(self.muebles)):
            for index_b in range(index_a + 1, len(self.muebles)):
                if self.muebles_se_traslapan(
                    self.muebles[index_a], self.muebles[index_b]
                ):
                    return True
        return False

    def validar(self):
        all_inside = all(
            self.mueble_esta_dentro(item) for item in self.muebles
        )
        self.valida = all_inside and not self.tiene_colisiones()
        return self.valida

    def colocar_muebles(self, attempts_per_item=250, random_generator=None):
        random_generator = random_generator or Random()
        placed_furniture = []
        self.muebles.sort(key=lambda item: item.calcular_volumen(), reverse=True)

        for furniture in self.muebles:
            max_x = self.habitacion.ancho - furniture.ancho
            max_y = self.habitacion.largo - furniture.largo

            if max_x < 0 or max_y < 0 or furniture.alto > self.habitacion.alto:
                self.valida = False
                return False

            was_placed = False
            for attempt in range(attempts_per_item):
                mode = attempt % 5
                x = (
                    0.0
                    if mode == 0
                    else max_x
                    if mode == 1
                    else random_generator.uniform(0, max_x)
                )
                y = (
                    0.0
                    if mode == 2
                    else max_y
                    if mode == 3
                    else random_generator.uniform(0, max_y)
                )
                furniture.set_posicion(Punto3D(round(x, 2), round(y, 2), 0.0))

                has_collision = any(
                    self.muebles_se_traslapan(furniture, other)
                    for other in placed_furniture
                )
                if not has_collision:
                    placed_furniture.append(furniture)
                    was_placed = True
                    break

            if not was_placed:
                self.valida = False
                return False

        return self.validar()

    @classmethod
    def _dead_gap_penalty(cls, gap):
        if gap <= 0 or gap >= cls.MINIMUM_USEFUL_GAP:
            return 0.0
        ratio = gap / cls.MINIMUM_USEFUL_GAP
        return cls.WASTED_GAP_PENALTY * 4 * ratio * (1 - ratio)

    @staticmethod
    def _intervals_overlap(start_a, end_a, start_b, end_b):
        return min(end_a, end_b) > max(start_a, start_b)

    def calcular_puntaje(self):
        if not self.validar():
            self.puntaje = 0.0
            return self.puntaje

        score = 0.0
        for furniture in self.muebles:
            position = furniture.posicion
            wall_distances = (
                position.x,
                position.y,
                self.habitacion.ancho - (position.x + furniture.ancho),
                self.habitacion.largo - (position.y + furniture.largo),
            )
            nearest_wall_distance = min(wall_distances)
            wall_bonus = furniture.utilidad / (1.0 + nearest_wall_distance)
            score += furniture.utilidad + wall_bonus

            score -= sum(
                self._dead_gap_penalty(gap) for gap in wall_distances
            )

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

        self.puntaje = round(score, 2)
        return self.puntaje

    @classmethod
    def generar_distribuciones(
        cls,
        room,
        amount=100,
        attempts_per_item=250,
        seed=None,
    ):
        if amount <= 0:
            return []

        random_generator = Random(seed)
        results = []
        for _ in range(amount):
            alternative = cls(room)
            if alternative.colocar_muebles(attempts_per_item, random_generator):
                alternative.calcular_puntaje()
                results.append(alternative)

        results.sort(key=lambda distribution: distribution.get_puntaje(), reverse=True)
        return results

    @staticmethod
    def obtener_mejor(distributions):
        return distributions[0] if distributions else None

    def __str__(self):
        status = "válida" if self.valida else "inválida"
        lines = [f"Distribución {status} | Puntaje: {self.puntaje:.2f}"]
        for furniture in self.muebles:
            lines.append(
                f"- {furniture.nombre} | Uso: {furniture.uso} | "
                f"Posición: {furniture.posicion}"
            )
        return "\n".join(lines)
