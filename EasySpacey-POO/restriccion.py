
from punto3d import Punto3D


class Restriccion:
    VALID_TYPES = ("Puerta", "Ventana")
    VALID_WALLS = ("Superior", "Inferior", "Izquierda", "Derecha")
    VALID_SECTIONS = ("Inicio", "Centro", "Final", "Personalizada")

    def __init__(self, tipo, pared, seccion, ancho, alto, profundidad, posicion):
        self.tipo = tipo
        self.pared = pared
        self.seccion = seccion
        self.ancho = ancho
        self.alto = alto
        self.profundidad = profundidad
        self.posicion = posicion

    @classmethod
    def crear_desde_pared(
        cls, room, restriction_type, wall, section,
        width, height, clearance_depth
    ):
        if restriction_type not in cls.VALID_TYPES:
            raise ValueError("Tipo de restricción inválido.")
        if wall not in cls.VALID_WALLS:
            raise ValueError("Pared inválida.")
        if section not in cls.VALID_SECTIONS:
            raise ValueError("Sección inválida.")

        if restriction_type == "Puerta":
            clearance_depth = width

        if min(width, height, clearance_depth) <= 0:
            raise ValueError("Las dimensiones deben ser mayores que cero.")
        if height > room.alto:
            raise ValueError("La altura supera la altura de la habitación.")

        horizontal_wall = wall in ("Superior", "Inferior")
        wall_length = room.ancho if horizontal_wall else room.largo
        room_depth = room.largo if horizontal_wall else room.ancho

        if width > wall_length:
            raise ValueError("El ancho supera la longitud de la pared.")
        if clearance_depth > room_depth:
            raise ValueError("La profundidad supera el tamaño de la habitación.")

        offset = cls._section_offset(wall_length, width, section)

        if wall == "Superior":
            x, y = offset, 0.0
        elif wall == "Inferior":
            x, y = offset, room.largo - clearance_depth
        elif wall == "Izquierda":
            x, y = 0.0, offset
        else:
            x, y = room.ancho - clearance_depth, offset

        return cls(
            restriction_type, wall, section, width, height, clearance_depth,
            Punto3D(round(x, 2), round(y, 2), 0.0)
        )

    @staticmethod
    def _section_offset(wall_length, width, section):
        # Posicion personalizada: la interfaz ajusta la coordenada despues.
        if section == "Personalizada":
            return 0.0
        if section == "Inicio":
            return 0.0
        if section == "Centro":
            return (wall_length - width) / 2
        return wall_length - width

    def get_floor_dimensions(self):
        if self.pared in ("Superior", "Inferior"):
            return self.ancho, self.profundidad
        return self.profundidad, self.ancho

    def __str__(self):
        return (
            f"{self.tipo} | Pared: {self.pared} | Sección: {self.seccion} | "
            f"Ancho: {self.ancho} m | Alto: {self.alto} m | "
            f"Profundidad libre: {self.profundidad} m"
        )
