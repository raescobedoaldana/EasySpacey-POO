
import unittest

from habitacion import Habitacion
from mueble import Mueble
from punto3d import Punto3D
from distribucion import Distribucion
from restriccion import Restriccion


class TestCirculacion(unittest.TestCase):

    # Crea una habitacion de prueba con dimensiones conocidas.
    def setUp(self):
        self.habitacion = Habitacion("Prueba", 5, 4, 3)

    # Agrega un mueble directamente en una posicion determinada.
    # Esto permite probar la circulacion sin generar alternativas.
    def agregar_mueble(self, nombre, x, y, ancho, largo,
                       z=0, alto=1):

        mueble = Mueble(
            nombre,
            ancho,
            largo,
            alto,
            8,
            Punto3D(x, y, z),
            "Prueba"
        )

        self.habitacion.agregar_mueble(mueble)
        return mueble


    # Crea una puerta usando el tipo registrado en Restriccion.
    # Evita utilizar un nombre que la clase no reconoce.
   
    # Crea una puerta utilizando el sistema original de restricciones.
    # La habitacion debe enviarse primero porque asi funciona el metodo.
    def agregar_puerta(self, pared="Superior", ancho=1.2):

        puerta = Restriccion.crear_desde_pared(
            self.habitacion,
            "Puerta",
            pared,
            "Centro",
            ancho,
            2.1,
            0.8
        )

        # Registra la puerta para que el sistema de circulacion la detecte.
        self.habitacion.agregar_restriccion(puerta)

        return puerta


    # Sin puertas registradas no se debe bloquear la distribucion.
    def test_sin_puertas(self):
        distribucion = Distribucion(self.habitacion)

        self.assertTrue(
            distribucion.verificar_circulacion()
        )

    # Una habitacion vacia debe permitir circular desde una puerta.
    def test_habitacion_vacia(self):
        self.agregar_puerta()

        distribucion = Distribucion(self.habitacion)

        self.assertTrue(
            distribucion.verificar_circulacion()
        )

    # Un mueble alejado de la entrada no debe impedir la circulacion.
    def test_mueble_no_bloquea(self):
        self.agregar_puerta()

        self.agregar_mueble(
            "Cama", 0, 2, 2, 1
        )

        distribucion = Distribucion(self.habitacion)

        self.assertTrue(
            distribucion.verificar_circulacion()
        )

    # Un mueble que ocupa toda la zona de entrada bloquea el paso.
    def test_entrada_bloqueada(self):
        self.agregar_puerta()

        self.agregar_mueble(
            "Armario", 0, 0, 5, 1
        )

        distribucion = Distribucion(self.habitacion)

        self.assertFalse(
            distribucion.verificar_circulacion()
        )

    # Una puerta menor que el ancho minimo no permite el paso.
    def test_puerta_demasiado_estrecha(self):
        self.agregar_puerta(ancho=0.6)

        distribucion = Distribucion(self.habitacion)

        self.assertFalse(
            distribucion.verificar_circulacion()
        )

    # Un objeto suficientemente elevado no bloquea el suelo.
    def test_objeto_elevado(self):
        self.agregar_puerta()

        self.agregar_mueble(
            "Objeto elevado",
            0, 0, 5, 1,
            z=2.1,
            alto=0.3
        )

        distribucion = Distribucion(self.habitacion)

        self.assertTrue(
            distribucion.verificar_circulacion()
        )


    # Una habitacion demasiado estrecha no permite circular.
    def test_habitacion_estrecha(self):

        habitacion = Habitacion(
            "Pasillo estrecho", 0.6, 4, 3
        )

        # Crea la puerta utilizando el orden correcto de argumentos.
        puerta = Restriccion.crear_desde_pared(
            habitacion,
            "Puerta",
            "Superior",
            "Centro",
            0.6,
            2.1,
            0.8
        )

        habitacion.agregar_restriccion(puerta)

        distribucion = Distribucion(habitacion)

        self.assertFalse(
            distribucion.verificar_circulacion()
        )


    # Comprueba que una zona aislada no sea considerada accesible.
    # Un armario divide la habitacion en dos partes.
    def test_zona_aislada(self):
        self.agregar_puerta()

        # Forma una barrera que atraviesa la habitacion.
        self.agregar_mueble(
            "Barrera", 0, 1.5, 5, 0.5
        )

        # Este mueble queda al otro lado de la barrera.
        self.agregar_mueble(
            "Escritorio", 2, 3, 1, 0.5
        )

        distribucion = Distribucion(self.habitacion)

        self.assertFalse(
            distribucion.verificar_circulacion()
        )

    # Comprueba que una distribucion transitable tenga mejor puntuacion.
    # Ambas alternativas usan los mismos muebles y utilidad.
    def test_penalizacion_circulacion(self):
        habitacion_libre = Habitacion("Libre", 5, 4, 3)
        habitacion_bloqueada = Habitacion("Bloqueada", 5, 4, 3)

        for habitacion in (habitacion_libre, habitacion_bloqueada):
            puerta = Restriccion.crear_desde_pared(
                habitacion, "Puerta", "Superior",
                "Centro", 1.2, 2.1, 0.8
            )
            habitacion.agregar_restriccion(puerta)

        # Coloca el mismo armario en posiciones diferentes.
        libre = Mueble(
            "Armario", 5, 1, 1, 8,
            Punto3D(0, 2, 0), "Almacenamiento"
        )

        bloqueado = Mueble(
            "Armario", 5, 1, 1, 8,
            Punto3D(0, 0, 0), "Almacenamiento"
        )

        habitacion_libre.agregar_mueble(libre)
        habitacion_bloqueada.agregar_mueble(bloqueado)

        distribucion_libre = Distribucion(habitacion_libre)
        distribucion_bloqueada = Distribucion(habitacion_bloqueada)

        self.assertTrue(distribucion_libre.verificar_circulacion())
        self.assertFalse(distribucion_bloqueada.verificar_circulacion())

        # La distribucion transitable debe obtener un puntaje mayor.
        self.assertGreater(
            distribucion_libre.calcular_puntaje(),
            distribucion_bloqueada.calcular_puntaje()
        )


    # Comprueba que la circulacion sea independiente de las colisiones.
    # Una puerta estrecha puede impedir el paso sin invalidar los muebles.
    def test_circulacion_no_invalida_geometria(self):
        self.agregar_puerta(ancho=0.6)

        distribucion = Distribucion(self.habitacion)

        self.assertFalse(
            distribucion.verificar_circulacion()
        )

        # No existen muebles fuera de limites ni traslapes.
        self.assertTrue(
            distribucion.validar()
        )



if __name__ == "__main__":
    unittest.main()
