
import unittest
from time import perf_counter

from distribucion import Distribucion
from habitacion import Habitacion
from mueble import Mueble
from punto3d import Punto3D


class TestDiversidad(unittest.TestCase):

    # Crea una habitación con tres muebles para las pruebas.
    def setUp(self):
        self.habitacion = Habitacion("Prueba", 6, 5, 3)

        muebles = [
            Mueble("Cama", 2, 1.5, 0.6, 10,
                   Punto3D(0, 0, 0), "Dormir"),
            Mueble("Escritorio", 1.2, 0.6, 0.75, 8,
                   Punto3D(0, 0, 0), "Trabajar"),
            Mueble("Armario", 1, 0.8, 2, 7,
                   Punto3D(0, 0, 0), "Almacenamiento")
        ]

        for mueble in muebles:
            self.habitacion.agregar_mueble(mueble)

    # Comprueba que las alternativas sean válidas y diferentes.
    def test_distribuciones_diferentes(self):
        alternativas = Distribucion.generar_distribuciones(
            self.habitacion,
            amount=100,
            seed=42,
            distancia_minima=0.5,
            limite_resultados=3
        )

        self.assertEqual(len(alternativas), 3)

        for alternativa in alternativas:
            self.assertTrue(alternativa.validar())

        for i in range(len(alternativas)):
            for j in range(i + 1, len(alternativas)):
                self.assertTrue(
                    alternativas[i].es_diferente_de(
                        alternativas[j], 0.5
                    )
                )

    # Comprueba que las puntuaciones estén ordenadas.
    def test_puntajes_ordenados(self):
        alternativas = Distribucion.generar_distribuciones(
            self.habitacion,
            amount=100,
            seed=42
        )

        puntajes = [a.get_puntaje() for a in alternativas]

        self.assertEqual(puntajes, sorted(puntajes, reverse=True))

    # Comprueba que la generación termine en un tiempo razonable.
    def test_rendimiento(self):
        inicio = perf_counter()

        alternativas = Distribucion.generar_distribuciones(
            self.habitacion,
            amount=100,
            seed=42
        )

        tiempo = perf_counter() - inicio

        print(f"\nTiempo de generación: {tiempo:.4f} segundos")

        self.assertGreater(len(alternativas), 0)

        # Umbral orientativo para detectar regresiones graves.
        self.assertLess(tiempo, 10)


if __name__ == "__main__":
    unittest.main()
