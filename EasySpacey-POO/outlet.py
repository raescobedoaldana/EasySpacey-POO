from math import isfinite
from punto3d import Punto3D


# Modelo de tomacorrientes propuesto conjuntamente por Raul y Dominic.
class Outlet:
    # Representa una conexion electrica sin bloquear espacio del suelo.
    def __init__(self, nombre, pared, posicion, capacidad=1):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre del tomacorriente es obligatorio.")
        if pared not in ("Superior", "Inferior", "Izquierda", "Derecha"):
            raise ValueError("La pared del tomacorriente no es valida.")
        if not isinstance(posicion, Punto3D):
            raise TypeError("La posicion debe ser un Punto3D.")
        if any(not isinstance(v, (int, float)) or not isfinite(v) or v < 0
               for v in (posicion.x, posicion.y, posicion.z)):
            raise ValueError("Las coordenadas deben ser finitas y no negativas.")
        if type(capacidad) is not int or capacidad < 1:
            raise ValueError("La capacidad debe ser un entero positivo.")
        self.nombre = nombre.strip()
        self.pared = pared
        self.posicion = posicion
        self.capacidad = capacidad

    # Devuelve la cantidad de conexiones registradas.
    def get_capacidad(self):
        return self.capacidad

    # Muestra un resumen del tomacorriente.
    def __str__(self):
        return f"{self.nombre} | {self.pared} | {self.capacidad} conexion(es)"
