import json

from habitacion import Habitacion
from mueble import Mueble
from punto3d import Punto3D


def punto_a_diccionario(punto):
    return {
        "x": punto.get_x(),
        "y": punto.get_y(),
        "z": punto.get_z()
    }


def mueble_a_diccionario(mueble):
    return {
        "nombre": mueble.nombre,
        "ancho": mueble.ancho,
        "largo": mueble.largo,
        "alto": mueble.alto,
        "utilidad": mueble.utilidad,
        "uso": mueble.uso,
        "posicion": punto_a_diccionario(mueble.posicion)
    }


def habitacion_a_diccionario(habitacion):
    muebles = []

    for mueble in habitacion.get_muebles():
        muebles.append(mueble_a_diccionario(mueble))

    return {
        "nombre": habitacion.get_nombre(),
        "ancho": habitacion.get_ancho(),
        "largo": habitacion.get_largo(),
        "alto": habitacion.get_alto(),
        "muebles": muebles
    }

def guardar_proyecto(habitacion, nombre_archivo):
    datos = habitacion_a_diccionario(habitacion)

    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)

    print(f"Proyecto guardado correctamente en: {nombre_archivo}")


# Prueba temporal
if __name__ == "__main__":

    habitacion = Habitacion(
        "Mi cuarto",
        5,
        4,
        3
    )

    cama = Mueble(
        "Cama",
        2.0,
        1.5,
        0.6,
        10,
        Punto3D(1, 1, 0),
        "Dormir"
    )

    escritorio = Mueble(
        "Escritorio",
        1.2,
        0.6,
        0.75,
        8,
        Punto3D(3, 2, 0),
        "Trabajar/Estudiar"
    )

    habitacion.agregar_mueble(cama)
    habitacion.agregar_mueble(escritorio)

    datos = habitacion_a_diccionario(habitacion)

    print(datos)
    guardar_proyecto(habitacion, "mi_cuarto.json")