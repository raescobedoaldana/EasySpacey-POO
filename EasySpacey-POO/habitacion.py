from mueble import Mueble
class Habitacion:

    def __init__(self, nombre, ancho, largo, alto):
        self.nombre = nombre
        self.ancho = ancho
        self.largo = largo
        self.alto = alto
        self.muebles = []

    def agregar_mueble(self, mueble):
        self.muebles.append(mueble)

    def eliminar_mueble(self, mueble):
        self.muebles.remove(mueble)

    def calcular_volumen(self):
        return self.ancho * self.largo * self.alto

    def get_nombre(self):
        return self.nombre

    def get_ancho(self):
        return self.ancho

    def get_largo(self):
        return self.largo

    def get_alto(self):
        return self.alto

    def get_muebles(self):
        return self.muebles

    def set_nombre(self, nombre):
        self.nombre = nombre

    def set_ancho(self, ancho):
        self.ancho = ancho

    def set_largo(self, largo):
        self.largo = largo

    def set_alto(self, alto):
        self.alto = alto

    def __str__(self):
            return f"{self.nombre} | {self.ancho} x {self.largo} x {self.alto} | Muebles: {len(self.muebles)}"
