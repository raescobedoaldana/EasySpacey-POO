import os
import tempfile
import unittest

import matplotlib
matplotlib.use("Agg")

from distribucion import Distribucion
from habitacion import Habitacion
from interfaz_grafica import MatplotlibInterface
from mueble import Mueble
from persistencia import cargar_proyecto, guardar_proyecto
from punto3d import Punto3D
from restriccion import Restriccion


class TestRestrictions(unittest.TestCase):
    def setUp(self):
        self.room = Habitacion("Prueba", 5, 4, 3)
        self.door = Restriccion.crear_desde_pared(
            self.room, "Puerta", "Superior", "Centro", 1, 2.1, 0.9
        )
        self.room.agregar_restriccion(self.door)

    def test_approximate_position_to_coordinates(self):
        self.assertEqual(self.door.posicion.x, 2)
        self.assertEqual(self.door.posicion.y, 0)
        self.assertEqual(self.door.profundidad, self.door.ancho)

    def test_furniture_cannot_block_door(self):
        blocked = Mueble(
            "Caja", 1, 1, 1, 5, Punto3D(2, 0, 0), "Almacenamiento"
        )
        self.assertTrue(
            Distribucion.furniture_overlaps_restriction(blocked, self.door)
        )

    def test_generation_respects_restrictions(self):
        self.room.agregar_mueble(
            Mueble("Cama", 2, 1.5, 0.6, 10, Punto3D(0, 0, 0), "Dormir")
        )
        alternatives = Distribucion.generar_distribuciones(
            self.room, amount=100, seed=42
        )
        self.assertGreater(len(alternatives), 0)
        self.assertTrue(all(item.validar() for item in alternatives))
        self.assertTrue(all(not item.overlaps_restrictions() for item in alternatives))

    def test_persistence_with_restrictions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "room.json")
            self.assertTrue(guardar_proyecto(self.room, path))
            restored = cargar_proyecto(path)
            self.assertEqual(len(restored.get_restricciones()), 1)
            self.assertEqual(restored.get_restricciones()[0].tipo, "Puerta")

    def test_clickable_interface_basic_flow(self):
        app = MatplotlibInterface()
        app.room_name.set_val("Prueba")
        app.room_width.set_val("5")
        app.room_length.set_val("4")
        app.room_height.set_val("3")
        app._create_room()

        app.restriction_type.set_active(0)
        app.restriction_wall.set_active(0)
        app.restriction_section.set_active(1)
        app.restriction_width.set_val("1")
        app.restriction_height.set_val("2")
        app._add_restriction()

        app.furniture_name.set_val("Cama")
        app.furniture_width.set_val("2")
        app.furniture_length.set_val("1.5")
        app.furniture_height.set_val("0.6")
        app.furniture_utility.set_val("10")
        app.furniture_quantity.set_val("1")
        app.furniture_use.set_active(0)
        app._add_furniture()
        app._generate()
        self.assertIsNotNone(app.room)
        self.assertEqual(len(app.room.get_restricciones()), 1)
        self.assertEqual(len(app.room.get_muebles()), 1)
        self.assertGreater(len(app.distributions), 0)

    def test_interface_starts_without_default_parameters(self):
        app = MatplotlibInterface()
        textboxes = (
            app.room_name, app.room_width, app.room_length, app.room_height,
            app.furniture_name, app.furniture_width, app.furniture_length,
            app.furniture_height, app.furniture_utility, app.furniture_quantity,
            app.restriction_width, app.restriction_height, app.restriction_depth,
            app.file_name
        )
        self.assertTrue(all(field.text == "" for field in textboxes))
        self.assertIsNone(app.furniture_use.value_selected)
        self.assertIsNone(app.restriction_type.value_selected)
        self.assertIsNone(app.restriction_wall.value_selected)
        self.assertIsNone(app.restriction_section.value_selected)

        app._create_room()
        self.assertIsNone(app.room)

    def test_interface_can_delete_list_items(self):
        app = MatplotlibInterface()
        app.room = Habitacion("Prueba", 5, 4, 3)
        furniture = Mueble(
            "Mesa", 1.2, 0.8, 0.75, 8, Punto3D(0, 0, 0), "Comer"
        )
        window = Restriccion.crear_desde_pared(
            app.room, "Ventana", "Superior", "Centro", 1.2, 1, 0.4
        )
        app.room.agregar_mueble(furniture)
        app.room.agregar_restriccion(window)
        app._refresh_lists()

        self.assertEqual(len(app.list_buttons), 2)
        app._delete_furniture(0)
        app._delete_restriction(0)

        self.assertEqual(app.room.get_muebles(), [])
        self.assertEqual(app.room.get_restricciones(), [])


if __name__ == "__main__":
    unittest.main()
