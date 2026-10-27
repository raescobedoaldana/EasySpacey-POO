import unittest
from punto3d import Punto3D
from outlet import Outlet

class TestOutlet(unittest.TestCase):
    # Comprueba la creacion y la capacidad de conexiones.
    def test_creacion(self):
        outlet = Outlet("T1", "Superior", Punto3D(1, 0, 0.3), 2)
        self.assertEqual(outlet.get_capacidad(), 2)

    # Rechaza capacidades que no representan conexiones validas.
    def test_capacidad_invalida(self):
        with self.assertRaises(ValueError):
            Outlet("T1", "Superior", Punto3D(1, 0, 0), 0)


if __name__ == "__main__":
    unittest.main()
