import unittest
from distribucion import Distribucion
from habitacion import Habitacion
from mueble import Mueble
from punto3d import Punto3D

class TestCuadricula(unittest.TestCase):
    # Comprueba la regla de huecos propuesta por Dominic.
    def test_penalizacion(self):
        self.assertEqual(Distribucion._dead_gap_penalty(0), 0)
        self.assertGreater(Distribucion._dead_gap_penalty(0.01), 0)
        self.assertGreater(Distribucion._dead_gap_penalty(0.14), 0)
        self.assertEqual(Distribucion._dead_gap_penalty(0.15), 0)

    # Verifica que las posiciones generadas coincidan con centimetros enteros.
    def test_coordenadas_centimetricas(self):
        room = Habitacion("Prueba", 5, 4, 3)
        room.agregar_mueble(Mueble("Cama", 2, 1.5, 0.6, 10, Punto3D(0, 0, 0), "Dormir"))
        results = Distribucion.generar_distribuciones(room, amount=30, seed=42)
        self.assertTrue(results)
        for distribution in results:
            self.assertTrue(distribution.validar())
            for furniture in distribution.get_muebles():
                self.assertAlmostEqual(furniture.posicion.x * 100, round(furniture.posicion.x * 100))
                self.assertAlmostEqual(furniture.posicion.y * 100, round(furniture.posicion.y * 100))

if __name__ == "__main__":
    unittest.main()
