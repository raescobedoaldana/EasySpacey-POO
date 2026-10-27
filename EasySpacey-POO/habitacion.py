from mueble import Mueble
class Habitacion:
    #habitaciones dentro de EasySpacey (Prisma rectángular)
    #Sirve de almacen de muebles

    def __init__(self, nombre, ancho, largo, alto):
        #inicia una habitación y sus muebles
        self.nombre = nombre
        self.ancho = ancho
        self.largo = largo
        self.alto = alto
        self.muebles = []
        self.restricciones = []
        # Sistema electrico propuesto conjuntamente por Raul y Dominic.
        self.outlets = []

    def agregar_mueble(self, mueble):
        #append es agregar
        #esto es agrega un mueble
        self.muebles.append(mueble)

    def eliminar_mueble(self, mueble):
        #remove, quita un mueble
        self.muebles.remove(mueble)

    def calcular_volumen(self):
        #el volumen de un prisma, blh
        return self.ancho * self.largo * self.alto

    def get_nombre(self):
        #trae el nombre
        #self es para que sea atributo
        return self.nombre

    def get_ancho(self):
        #trae el ancho
        return self.ancho

    def get_largo(self):
        #trae el largo
        return self.largo

    def get_alto(self):
        #trae el alto
        return self.alto

    def get_muebles(self):
        #trae la lista de muebles
        return self.muebles

    def agregar_restriccion(self, restriccion):
        self.restricciones.append(restriccion)

    def eliminar_restriccion(self, restriccion):
        self.restricciones.remove(restriccion)

    def get_restricciones(self):
        return self.restricciones

    # Agrega un outlet a la habitacion.
    def agregar_outlet(self, outlet):
        from outlet import Outlet
        if not isinstance(outlet, Outlet):
            raise TypeError("El elemento debe ser un Outlet.")
        self.outlets.append(outlet)

    # Elimina un outlet registrado.
    def eliminar_outlet(self, outlet):
        self.outlets.remove(outlet)

    # Devuelve los outlets de la habitacion.
    def get_outlets(self):
        return self.outlets

    # Suma las conexiones disponibles de todos los outlets.
    def contar_conexiones_disponibles(self):
        return sum(outlet.capacidad for outlet in self.outlets)

    # Suma las conexiones solicitadas por los muebles.
    def contar_conexiones_necesarias(self):
        return sum(mueble.conexiones_necesarias for mueble in self.muebles)

    # Calcula cuantas conexiones faltan, si las hay.
    def conexiones_faltantes(self):
        return max(0, self.contar_conexiones_necesarias() - self.contar_conexiones_disponibles())

    def set_nombre(self, nombre):
        #altera el nombre
        self.nombre = nombre

    def set_ancho(self, ancho):
        #altera el ancho
        self.ancho = ancho

    def set_largo(self, largo):
        #altera el largo
        self.largo = largo

    def set_alto(self, alto):
        #altera el alto
        self.alto = alto

    def __str__(self):
            #representación textual de la habitación
            return (
                f"{self.nombre} | {self.ancho} x {self.largo} x {self.alto} | "
                f"Muebles: {len(self.muebles)} | "
                f"Restricciones: {len(self.restricciones)}"
            )
