import itertools
import unittest

from distribucion import Distribucion
from habitacion import Habitacion
from mueble import Mueble
from persistencia import diccionario_a_mueble, mueble_a_diccionario
from punto3d import Punto3D


class TestPlacementSettings(unittest.TestCase):
    def make_item(self, placement_type, supports_objects):
        wall = "Superior" if placement_type == "Pared" else "Automática"
        wall_height = 1.0 if placement_type == "Pared" else 0.0
        return Mueble(
            f"{placement_type}-{supports_objects}",
            0.8, 0.3, 0.4, 5, Punto3D(0, 0, 0), "Decoración",
            placement_type=placement_type,
            supports_objects=supports_objects,
            preferred_wall=wall,
            wall_height=wall_height
        )

    def test_all_six_setting_permutations_round_trip(self):
        combinations = itertools.product(Mueble.VALID_PLACEMENT_TYPES, (False, True))
        for placement_type, supports_objects in combinations:
            with self.subTest(placement_type=placement_type, supports=supports_objects):
                original = self.make_item(placement_type, supports_objects)
                restored = diccionario_a_mueble(mueble_a_diccionario(original))
                self.assertEqual(restored.get_placement_type(), placement_type)
                self.assertEqual(restored.can_support_objects(), supports_objects)
                self.assertEqual(restored.get_preferred_wall(), original.get_preferred_wall())
                self.assertEqual(restored.get_wall_height(), original.get_wall_height())

    def test_all_six_setting_permutations_validate(self):
        for supports_objects in (False, True):
            with self.subTest(placement_type="Suelo", supports=supports_objects):
                room = Habitacion("Suelo", 5, 4, 3)
                item = self.make_item("Suelo", supports_objects)
                room.agregar_mueble(item)
                self.assertTrue(Distribucion(room, [item]).validar())

            with self.subTest(placement_type="Pared", supports=supports_objects):
                room = Habitacion("Pared", 5, 4, 3)
                item = self.make_item("Pared", supports_objects)
                item.set_posicion(Punto3D(1, 0, 1))
                room.agregar_mueble(item)
                self.assertTrue(Distribucion(room, [item]).validar())

            with self.subTest(placement_type="Sobre objeto", supports=supports_objects):
                room = Habitacion("Superficie", 5, 4, 3)
                support = Mueble(
                    "Mesa", 2, 1, 0.8, 7, Punto3D(1, 1, 0), "Decoración",
                    supports_objects=True
                )
                item = self.make_item("Sobre objeto", supports_objects)
                item.set_posicion(Punto3D(1.2, 1.2, 0.8))
                room.agregar_mueble(support)
                room.agregar_mueble(item)
                self.assertTrue(Distribucion(room, [support, item]).validar())

    def test_generation_places_floor_wall_and_surface_items(self):
        room = Habitacion("Mixta", 6, 5, 3)
        room.agregar_mueble(Mueble(
            "Mesa", 2, 1, 0.8, 8, Punto3D(0, 0, 0), "Decoración",
            supports_objects=True
        ))
        room.agregar_mueble(Mueble(
            "Repisa", 1.2, 0.25, 0.2, 7, Punto3D(0, 0, 0), "Decoración",
            placement_type="Pared", supports_objects=True,
            preferred_wall="Superior", wall_height=1.5
        ))
        room.agregar_mueble(Mueble(
            "Lámpara", 0.3, 0.3, 0.5, 6, Punto3D(0, 0, 0), "Decoración",
            placement_type="Sobre objeto"
        ))

        results = Distribucion.generar_distribuciones(room, amount=40, seed=23)
        self.assertTrue(results)
        for distribution in results:
            self.assertTrue(distribution.validar())
            items = {item.nombre: item for item in distribution.get_muebles()}
            self.assertEqual(items["Mesa"].posicion.z, 0)
            self.assertEqual(items["Repisa"].posicion.y, 0)
            self.assertAlmostEqual(items["Repisa"].posicion.z, 1.5)
            self.assertIsNotNone(distribution._supporting_furniture(items["Lámpara"]))

    def test_support_chain_must_reach_floor_or_wall(self):
        room = Habitacion("Cadena", 5, 4, 3)
        floating_support = Mueble(
            "Repisa flotante", 1, 0.5, 0.2, 5, Punto3D(1, 1, 1), "Decoración",
            placement_type="Sobre objeto", supports_objects=True
        )
        decoration = Mueble(
            "Adorno", 0.2, 0.2, 0.2, 4, Punto3D(1.1, 1.1, 1.2), "Decoración",
            placement_type="Sobre objeto"
        )
        room.agregar_mueble(floating_support)
        room.agregar_mueble(decoration)
        self.assertFalse(Distribucion(room, [floating_support, decoration]).validar())

    def test_wall_item_must_touch_its_selected_wall(self):
        room = Habitacion("Pared", 5, 4, 3)
        item = self.make_item("Pared", False)
        item.set_posicion(Punto3D(1, 1, 1))
        room.agregar_mueble(item)
        self.assertFalse(Distribucion(room, [item]).validar())


if __name__ == "__main__":
    unittest.main()
