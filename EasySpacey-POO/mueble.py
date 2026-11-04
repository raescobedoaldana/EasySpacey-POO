from punto3d import Punto3D


class Mueble:
    VALID_PLACEMENT_TYPES = ("Suelo", "Sobre objeto", "Pared")
    VALID_WALLS = ("Automática", "Superior", "Inferior", "Izquierda", "Derecha")
        #Un mueble dentro de EasySpacey
        #Esto hará un prisma rectángular con sus dimensiones

    def __init__(
        self,
        nombre,
        ancho, #X
        largo, #Y
        alto, #Z #Entre 1 y 10
        utilidad,
        posicion, #Coordenadas. Este es un punto
        uso = "Algo", #Funcionamiento
        conexiones_necesarias=0,
        permite_rotacion=True,
        rotacion=0,
        placement_type="Suelo",
        supports_objects=False,
        preferred_wall="Automática",
        wall_height=0.0,
    ):
        self.nombre = nombre
        #características principales, ahora iniciadas
        self.ancho = ancho
        self.largo = largo
        self.alto = alto
        self.utilidad = utilidad
        self.posicion = posicion
        self.uso = uso
        # Necesidades electricas propuestas conjuntamente por Raul y Dominic.
        self.set_conexiones_necesarias(conexiones_necesarias)
        # Permite o bloquea la rotacion automatica de este mueble.
        if type(permite_rotacion) is not bool:
            raise ValueError("Permite rotacion debe ser True o False.")
        self.permite_rotacion = permite_rotacion
        self.rotacion = 0
        self.set_rotacion(rotacion)
        self.set_placement_type(placement_type)
        self.set_supports_objects(supports_objects)
        self.set_preferred_wall(preferred_wall)
        self.set_wall_height(wall_height)

    def calcular_volumen(self):
        return self.ancho * self.largo * self.alto

    def set_nombre(self, nombre):
        #definir nombre
        self.nombre = nombre

    def set_ancho(self, ancho):
        #definir ancho
        self.ancho = ancho

    def set_largo(self, largo):
        #define largo
        self.largo = largo

    def set_alto(self, alto):
        #define alto
        self.alto = alto

    def set_utilidad(self, utilidad):
        #define utilidad
        self.utilidad = utilidad

    def set_posicion(self, posicion):
        #define posicion. Modifica la posición tridimensional.
        self.posicion = posicion

    def set_uso(self, uso):
        #define uso
        self.uso = uso

    def get_uso(self):
        #trae el uso
        return self.uso

    # Guarda una cantidad entera y no negativa de conexiones.
    def set_conexiones_necesarias(self, cantidad):
        if type(cantidad) is not int or cantidad < 0:
            raise ValueError("Las conexiones necesarias deben ser un entero no negativo.")
        self.conexiones_necesarias = cantidad

    # Devuelve las conexiones que necesita este mueble.
    def get_conexiones_necesarias(self):
        return self.conexiones_necesarias

    # Indica si el mueble necesita electricidad.
    def requiere_electricidad(self):
        return self.conexiones_necesarias > 0

    # Indica si el algoritmo puede girar este mueble.
    def puede_rotar(self):
        return self.permite_rotacion

    # Cambia el permiso de rotacion sin modificar su orientacion actual.
    def set_permite_rotacion(self, permitido):
        if type(permitido) is not bool:
            raise ValueError("Permite rotacion debe ser True o False.")
        self.permite_rotacion = permitido

    # Devuelve la orientacion actual del mueble.
    def get_rotacion(self):
        return self.rotacion

    # Fija la orientacion sin acumular giros al repetir la llamada.
    def set_rotacion(self, grados):
        if type(grados) is not int or grados not in (0, 90):
            raise ValueError("La rotacion debe ser 0 o 90 grados.")
        if grados != self.rotacion:
            self.ancho, self.largo = self.largo, self.ancho
            self.rotacion = grados

    # Alterna entre las orientaciones horizontal y vertical.
    def rotar(self):
        self.set_rotacion(90 if self.rotacion == 0 else 0)

    def set_placement_type(self, placement_type):
        if placement_type == "Sobre superficie":
            placement_type = "Sobre objeto"
        if placement_type not in self.VALID_PLACEMENT_TYPES:
            raise ValueError("El tipo de colocacion no es valido.")
        self.placement_type = placement_type

    def get_placement_type(self):
        return self.placement_type

    def set_supports_objects(self, supports_objects):
        if type(supports_objects) is not bool:
            raise ValueError("Puede sostener objetos debe ser True o False.")
        self.supports_objects = supports_objects

    def can_support_objects(self):
        return self.supports_objects

    def set_preferred_wall(self, preferred_wall):
        if preferred_wall not in self.VALID_WALLS:
            raise ValueError("La pared preferida no es valida.")
        self.preferred_wall = preferred_wall

    def get_preferred_wall(self):
        return self.preferred_wall

    def set_wall_height(self, wall_height):
        if isinstance(wall_height, bool) or not isinstance(wall_height, (int, float)):
            raise ValueError("La altura de pared debe ser numerica.")
        if wall_height < 0:
            raise ValueError("La altura de pared no puede ser negativa.")
        self.wall_height = float(wall_height)

    def get_wall_height(self):
        return self.wall_height

    def __str__(self):
        #representación textual del mueble
        return (
            f"{self.nombre} | {self.ancho} x {self.largo} x {self.alto} | "
            f"Utilidad: {self.utilidad} | Uso: {self.uso} | "
            f"Colocacion: {self.placement_type} | "
            f"Posición: {self.posicion}"
        )

#PRUEBA (no hace más allá que ser nuestra prueba y prototipo)
if __name__ == "__main__":
    cama = Mueble(
        "Cama", 2.0, 1.5, 0.6, 10, Punto3D(0, 0, 0), "Dormir"
    )
    print(cama)
    print("Volumen:", cama.calcular_volumen())