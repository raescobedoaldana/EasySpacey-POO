
import unittest
from copy import deepcopy

from distribucion import Distribucion
from habitacion import Habitacion
from mueble import Mueble
from outlet import Outlet
from punto3d import Punto3D


class TestElectricidad(unittest.TestCase):

    # Crea una habitacion con un outlet y un escritorio electrico.
    def setUp(self):
        self.habitacion = Habitacion("Prueba", 5, 4, 3)

        self.outlet = Outlet(
            "Outlet 1", "Superior",
            Punto3D(2, 0, 0.3), 2
        )
        self.habitacion.agregar_outlet(self.outlet)

        self.escritorio = Mueble(
            "Escritorio", 1.2, 0.6, 0.75, 8,
            Punto3D(1.5, 0, 0), "Trabajar",
            conexiones_necesarias=1
        )
        self.habitacion.agregar_mueble(self.escritorio)

    # Comprueba que la cercania electrica aumente la bonificacion.
    def test_proximidad_electrica(self):
        cercana = Distribucion(self.habitacion)
        lejana = Distribucion(self.habitacion)

        lejana.get_muebles()[0].set_posicion(
            Punto3D(3.5, 3, 0)
        )

        self.assertGreater(
            cercana.calcular_bonificacion_electrica(),
            lejana.calcular_bonificacion_electrica()
        )

    # Comprueba que una habitacion sin outlets no reciba bonificacion.
    def test_sin_outlets(self):
        habitacion = Habitacion("Sin electricidad", 5, 4, 3)

        mueble = deepcopy(self.escritorio)
        habitacion.agregar_mueble(mueble)

        distribucion = Distribucion(habitacion)

        self.assertEqual(
            distribucion.calcular_bonificacion_electrica(), 0
        )

    # Comprueba que los muebles normales no necesiten electricidad.
    def test_mueble_sin_electricidad(self):
        habitacion = Habitacion("Prueba", 5, 4, 3)
        habitacion.agregar_outlet(self.outlet)

        cama = Mueble(
            "Cama", 2, 1.5, 0.6, 10,
            Punto3D(0, 0, 0), "Dormir"
        )
        habitacion.agregar_mueble(cama)

        distribucion = Distribucion(habitacion)

        self.assertEqual(
            distribucion.calcular_bonificacion_electrica(), 0
        )

    # Comprueba que la cantidad de conexiones faltantes sea correcta.
    def test_conexiones_insuficientes(self):
        self.escritorio.set_conexiones_necesarias(3)

        self.assertEqual(
            self.habitacion.conexiones_faltantes(), 1
        )

    # Comprueba que las alternativas respeten la geometria.
    def test_distribuciones_validas(self):
        alternativas = Distribucion.generar_distribuciones(
            self.habitacion,
            amount=100,
            seed=42
        )

        self.assertGreater(len(alternativas), 0)

        for alternativa in alternativas:
            self.assertTrue(alternativa.validar())


if __name__ == "__main__":
    unittest.main()
