import json
import os
import tempfile
import unittest
from habitacion import Habitacion
from mueble import Mueble
from punto3d import Punto3D
from distribucion import Distribucion
from persistencia import guardar_proyecto, cargar_proyecto

class TestLogica(unittest.TestCase):
    def setUp(self):
        self.room = Habitacion('Prueba', 5, 4, 3)
        self.room.agregar_mueble(Mueble('Cama', 2, 1.5, 0.6, 10, Punto3D(0, 0, 0), 'Dormir'))
        self.room.agregar_mueble(Mueble('Mesa', 1, 0.6, 0.7, 6, Punto3D(0, 0, 0), 'Trabajar'))

    def test_alternativas_distintas_y_validas(self):
        ds = Distribucion.generar_distribuciones(self.room, amount=200, seed=42)
        self.assertEqual(len(ds), 3)
        for i, d in enumerate(ds):
            self.assertTrue(d.es_valida())
            for other in ds[:i]:
                self.assertTrue(d.es_diferente_de(other, 0.5))

    def test_puntajes_ordenados(self):
        ds = Distribucion.generar_distribuciones(self.room, amount=200, seed=42)
        self.assertEqual([d.puntaje for d in ds], sorted([d.puntaje for d in ds], reverse=True))

    def test_json_guardar_cargar(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'proyecto.json')
            self.assertTrue(guardar_proyecto(self.room, path))
            restored = cargar_proyecto(path)
            self.assertEqual(len(restored.get_muebles()), 2)

    def test_json_incompleto(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'incompleto.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'nombre': 'Incompleto', 'ancho': 5}, f)
            self.assertIsNone(cargar_proyecto(path))

    def test_json_dimensiones_invalidas(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'invalido.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'nombre':'Cuarto','ancho':-5,'largo':4,'alto':3,'muebles':[]}, f)
            self.assertIsNone(cargar_proyecto(path))

    def test_json_inexistente(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertIsNone(cargar_proyecto(os.path.join(folder, 'nada.json')))

if __name__ == '__main__':
    unittest.main()
