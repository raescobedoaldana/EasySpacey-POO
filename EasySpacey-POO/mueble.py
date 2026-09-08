from punto3d import Punto3D


class Mueble:

    def __init__(
        self,
        nombre,
        ancho,
        largo,
        alto,
        utilidad,
        posicion,
        uso = "Algo",
    ):
        self.nombre = nombre
        self.ancho = ancho
        self.largo = largo
        self.alto = alto
        self.utilidad = utilidad
        self.posicion = posicion
        self.uso = uso

    def calcular_volumen(self):
        return self.ancho * self.largo * self.alto

    def set_nombre(self, nombre):
        self.nombre = nombre

    def set_ancho(self, ancho):
        self.ancho = ancho

    def set_largo(self, largo):
        self.largo = largo

    def set_alto(self, alto):
        self.alto = alto

    def set_utilidad(self, utilidad):
        self.utilidad = utilidad

    def set_posicion(self, posicion):
        self.posicion = posicion

    def set_uso(self, uso):
        self.uso = uso

    def get_uso(self):
        return self.uso

    def __str__(self):
        return (
            f"{self.nombre} | {self.ancho} x {self.largo} x {self.alto} | "
            f"Utilidad: {self.utilidad} | Uso: {self.uso} | "
            f"Posición: {self.posicion}"
        )


if __name__ == "__main__":
    cama = Mueble(
        "Cama", 2.0, 1.5, 0.6, 10, Punto3D(0, 0, 0), "Dormir"
    )
    print(cama)
    print("Volumen:", cama.calcular_volumen())
