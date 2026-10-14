
import json
from math import isfinite

#Persistencia de datos, guardando y recuperando datos con archivos JSON
#Funciona cambiando los objetos a diccionarios y listas
#Guardado
#Habitacion -> Mueble -> Punto3D -> Diccionario -> JSON
#Carga
#JSON -> Diccionario -> Punto3D -> Mueble -> Habitacion

from habitacion import Habitacion
from mueble import Mueble
from punto3d import Punto3D
from restriccion import Restriccion


# Validar números y dimensiones

def validar_numero_positivo(numero):
    #Verifica que sea un número positivo y finito
    if isinstance(numero, bool) or not isinstance(numero, (int, float)):
        raise ValueError("El valor debe ser numerico.")

    if not isfinite(numero) or numero <= 0:
        raise ValueError("La dimension debe ser mayor que cero.")

    return True


# Convertir a Diccionarios (cada uno)

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


def restriction_to_dictionary(restriction):
    return {
        "tipo": restriction.tipo,
        "pared": restriction.pared,
        "seccion": restriction.seccion,
        "ancho": restriction.ancho,
        "alto": restriction.alto,
        "profundidad": restriction.profundidad,
        "posicion": punto_a_diccionario(restriction.posicion)
    }


def habitacion_a_diccionario(habitacion):
    muebles = []

    #para cada mueble...
    for mueble in habitacion.get_muebles():
        muebles.append(mueble_a_diccionario(mueble))

    restrictions = [
        restriction_to_dictionary(restriction)
        for restriction in habitacion.get_restricciones()
    ]

    return {
        "nombre": habitacion.get_nombre(),
        "ancho": habitacion.get_ancho(),
        "largo": habitacion.get_largo(),
        "alto": habitacion.get_alto(),
        "muebles": muebles,
        "restricciones": restrictions
    }


# Guardar un Proyecto

def guardar_proyecto(habitacion, nombre_archivo):
    #Guarda los datos en un archivo JSON, con habitación y nombre de archivo.
    #W permite crear o sobreescribir el archivo
    try:
        datos = habitacion_a_diccionario(habitacion)

        #Validar los datos antes de guardarlos
        diccionario_a_habitacion(datos)

        #Abrir el archivo y escribir los datos
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            json.dump(
                datos,
                archivo,
                indent=4,
                ensure_ascii=False,
                allow_nan=False
            )

        print(f"Proyecto guardado correctamente en: {nombre_archivo}")
        return True

    #Controlar errores de escritura o datos incorrectos
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"Error al guardar el proyecto: {error}")
        return False


# De diccionarios a objetos

def diccionario_a_punto(datos):
    #Verificar que las coordenadas sean válidas
    if not isinstance(datos, dict):
        raise ValueError("La posicion debe ser un diccionario.")

    for eje in ("x", "y", "z"):
        valor = datos[eje]

        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValueError("Las coordenadas deben ser numericas.")

        if not isfinite(valor):
            raise ValueError("Las coordenadas deben ser finitas.")

    return Punto3D(
        datos["x"],
        datos["y"],
        datos["z"]
    )


def diccionario_a_mueble(datos):
    #Reconstruir muebles
    if not isinstance(datos, dict):
        raise ValueError("Los datos del mueble deben ser un diccionario.")

    #Verificar las dimensiones del mueble
    validar_numero_positivo(datos["ancho"])
    validar_numero_positivo(datos["largo"])
    validar_numero_positivo(datos["alto"])

    #Verificar la utilidad entre 1 y 10
    utilidad = datos["utilidad"]

    if type(utilidad) is not int or not 1 <= utilidad <= 10:
        raise ValueError("La utilidad debe ser un entero entre 1 y 10.")

    #Verificar nombre y uso del mueble
    if not isinstance(datos["nombre"], str) or not datos["nombre"].strip():
        raise ValueError("El nombre del mueble no es valido.")

    if not isinstance(datos["uso"], str) or not datos["uso"].strip():
        raise ValueError("El uso del mueble no es valido.")

    posicion = diccionario_a_punto(datos["posicion"])

    return Mueble(
        datos["nombre"],
        datos["ancho"],
        datos["largo"],
        datos["alto"],
        datos["utilidad"],
        posicion,
        datos["uso"]
    )


def dictionary_to_restriction(data):
    if not isinstance(data, dict):
        raise ValueError("La restricción debe ser un diccionario.")
    for field in ("ancho", "alto", "profundidad"):
        validar_numero_positivo(data[field])
    if data["tipo"] not in Restriccion.VALID_TYPES:
        raise ValueError("Tipo de restricción inválido.")
    if data["pared"] not in Restriccion.VALID_WALLS:
        raise ValueError("Pared de restricción inválida.")
    if data["seccion"] not in Restriccion.VALID_SECTIONS:
        raise ValueError("Sección de restricción inválida.")
    return Restriccion(
        data["tipo"],
        data["pared"],
        data["seccion"],
        data["ancho"],
        data["alto"],
        data["profundidad"],
        diccionario_a_punto(data["posicion"])
    )


def diccionario_a_habitacion(datos):
    #Crea una habitación vacía
    if not isinstance(datos, dict):
        raise ValueError("Los datos de la habitacion deben ser un diccionario.")

    #Verificar las dimensiones de la habitacion
    validar_numero_positivo(datos["ancho"])
    validar_numero_positivo(datos["largo"])
    validar_numero_positivo(datos["alto"])

    #Verificar el nombre de la habitacion
    if not isinstance(datos["nombre"], str) or not datos["nombre"].strip():
        raise ValueError("El nombre de la habitacion no es valido.")

    #Verificar que muebles sea una lista
    if not isinstance(datos["muebles"], list):
        raise ValueError("Los muebles deben estar en una lista.")

    habitacion = Habitacion(
        datos["nombre"],
        datos["ancho"],
        datos["largo"],
        datos["alto"]
    )

    #y agrega cada mueble
    for datos_mueble in datos["muebles"]:
        mueble = diccionario_a_mueble(datos_mueble)
        habitacion.agregar_mueble(mueble)

                                                                            
    restrictions = datos.get("restricciones", [])
    if not isinstance(restrictions, list):
        raise ValueError("Las restricciones deben estar en una lista.")
    for restriction_data in restrictions:
        habitacion.agregar_restriccion(
            dictionary_to_restriction(restriction_data)
        )

    return habitacion


# Cargar Proyecto

def cargar_proyecto(nombre_archivo):
    #Cargar un archivo JSON
    try:
        #Abrir el archivo JSON para lectura
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        #Reconstruir los objetos EasySpacey
        habitacion = diccionario_a_habitacion(datos)

        print(f"Proyecto cargado correctamente desde: {nombre_archivo}")

        return habitacion

    #A menos que no lo encuentre
    except FileNotFoundError:
        print("Error: No se encontro el archivo.")
        return None

    #O que no cumpla con el formato
    except json.JSONDecodeError:
        print("Error: El archivo JSON no tiene un formato valido.")
        return None

    #O que falten datos obligatorios
    except (KeyError, TypeError, ValueError) as error:
        print(f"Error: Los datos del proyecto no son validos: {error}")
        return None

    #O que exista un problema al leer el archivo
    except (OSError, UnicodeError) as error:
        print(f"Error al leer el archivo: {error}")
        return None


# PRUEBA

if __name__ == "__main__":

    # Crear habitacion
    habitacion = Habitacion(
        "Mi cuarto",
        5,
        4,
        3
    )

    # Crear cama
    cama = Mueble(
        "Cama",
        2.0,
        1.5,
        0.6,
        10,
        Punto3D(1, 1, 0),
        "Dormir"
    )

    # Crear escritorio
    escritorio = Mueble(
        "Escritorio",
        1.2,
        0.6,
        0.75,
        8,
        Punto3D(3, 2, 0),
        "Trabajar/Estudiar"
    )

    # Agregar muebles a la habitacion
    habitacion.agregar_mueble(cama)
    habitacion.agregar_mueble(escritorio)

    # Mostrar datos originales
    print("\n===== DATOS ORIGINALES =====")
    print(habitacion)

    for mueble in habitacion.get_muebles():
        print(mueble)

    # Guardar
    guardar_proyecto(
        habitacion,
        "mi_cuarto.json"
    )

    # Cargar
    habitacion_cargada = cargar_proyecto(
        "mi_cuarto.json"
    )

    # Mostrar lo recuperado
    if habitacion_cargada is not None:

        print("\n===== DATOS RECUPERADOS =====")
        print(habitacion_cargada)

        for mueble in habitacion_cargada.get_muebles():
            print(mueble)
