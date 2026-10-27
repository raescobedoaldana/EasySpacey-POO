
import unittest

from habitacion import Habitacion
from mueble import Mueble
from outlet import Outlet
from punto3d import Punto3D


class TestIntegracionOutlet(unittest.TestCase):

    # Crea una habitación vacía para cada prueba.
    def setUp(self):
        self.habitacion = Habitacion("Prueba", 5, 4, 3)

    # Comprueba que los muebles antiguos sigan funcionando.
    def test_compatibilidad_mueble(self):
        cama = Mueble(
            "Cama", 2, 1.5, 0.6, 10,
            Punto3D(0, 0, 0), "Dormir"
        )
        self.assertEqual(cama.get_conexiones_necesarias(), 0)
        self.assertFalse(cama.requiere_electricidad())

    # Comprueba las conexiones necesarias de un mueble.
    def test_mueble_electrico(self):
        escritorio = Mueble(
            "Escritorio", 1.2, 0.6, 0.75, 8,
            Punto3D(0, 0, 0), "Trabajar",
            conexiones_necesarias=2
        )
        self.assertEqual(escritorio.get_conexiones_necesarias(), 2)
        self.assertTrue(escritorio.requiere_electricidad())

    # Comprueba que la habitación almacene outlets.
    def test_agregar_outlet(self):
        outlet = Outlet(
            "Outlet 1", "Superior", Punto3D(2, 0, 0.3), 2
        )
        self.habitacion.agregar_outlet(outlet)
        self.assertEqual(len(self.habitacion.get_outlets()), 1)
        self.assertEqual(
            self.habitacion.contar_conexiones_disponibles(), 2
        )

    # Comprueba cuántas conexiones faltan.
    def test_conexiones_faltantes(self):
        escritorio = Mueble(
            "Escritorio", 1.2, 0.6, 0.75, 8,
            Punto3D(0, 0, 0), "Trabajar",
            conexiones_necesarias=3
        )
        self.habitacion.agregar_mueble(escritorio)

        outlet = Outlet(
            "Outlet 1", "Superior", Punto3D(2, 0, 0.3), 1
        )
        self.habitacion.agregar_outlet(outlet)

        self.assertEqual(
            self.habitacion.contar_conexiones_necesarias(), 3
        )
        self.assertEqual(
            self.habitacion.contar_conexiones_disponibles(), 1
        )
        self.assertEqual(self.habitacion.conexiones_faltantes(), 2)

    # Rechaza cantidades eléctricas negativas.
    def test_conexiones_invalidas(self):
        with self.assertRaises(ValueError):
            Mueble(
                "Escritorio", 1.2, 0.6, 0.75, 8,
                Punto3D(0, 0, 0), "Trabajar",
                conexiones_necesarias=-1
            )


if __name__ == "__main__":
    unittest.main()
