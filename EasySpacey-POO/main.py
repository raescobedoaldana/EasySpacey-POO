from mueble import Mueble
from punto3d import Punto3D
from habitacion import Habitacion

nombre = input("Nombre de la habitacion: ")
while True:
    try:
        ancho = float(input("Ingrese el Ancho (metros): "))
        if ancho > 0:
            break
        print("Error: El ancho debe ser mayor que 0.")
    except ValueError:
        print("Error: Debe ingresar un numero.")

while True:
    try:
        largo = float(input("Ingrese el Largo (metros): "))
        if largo > 0:
            break
        print("Error: El largo debe ser mayor que 0.")
    except ValueError:
        print("Error: Debe ingresar un numero.")

while True:
    try:
        alto = float(input("Ingrese el Alto (metros): "))
        if alto > 0:
            break
        print("Error: El alto debe ser mayor que 0.")
    except ValueError:
        print("Error: Debe ingresar un numero.")

habitacion = Habitacion(nombre, ancho, largo, alto)

print("\nHabitacion creada correctamente")
print(habitacion)

while True:
    print("\nDesea agregar un mueble?")
    print("1. Si")
    print("2. No")

    opcion = input("Seleccione una opcion: ")

    if opcion == "2":
        break

    if opcion != "1":
        print("Opcion invalida.")
        continue

    nombre_mueble = input("Nombre del mueble: ")

    while True:
        try:
            ancho_mueble = float(input("Ancho del mueble (metros): "))

            if ancho_mueble > 0:
                break

            print("Error: El ancho debe ser mayor que 0.")

        except ValueError:
            print("Error: Debe ingresar un numero.")

    while True:
        try:
            largo_mueble = float(input("Largo del mueble (metros): "))

            if largo_mueble > 0:
                break

            print("Error: El largo debe ser mayor que 0.")

        except ValueError:
            print("Error: Debe ingresar un numero.")

    while True:
        try:
            alto_mueble = float(input("Alto del mueble (metros): "))

            if alto_mueble > 0:
                break

            print("Error: El alto debe ser mayor que 0.")

        except ValueError:
            print("Error: Debe ingresar un numero.")

    while True:
        try:
            utilidad = int(input("Utilidad del mueble (1-10): "))

            if 1 <= utilidad <= 10:
                break

            print("Error: La utilidad debe estar entre 1 y 10.")

        except ValueError:
            print("Error: Debe ingresar un numero entero.")

    posicion = Punto3D(0, 0, 0)

    mueble = Mueble(
        nombre_mueble,
        ancho_mueble,
        largo_mueble,
        alto_mueble,
        utilidad,
        posicion
    )

    habitacion.agregar_mueble(mueble)

    print("Mueble agregado correctamente.")
    print(mueble)

print("\nRESUMEN DE LA HABITACIÓN")
print(habitacion)

print("\nMuebles registrados:")

for mueble in habitacion.get_muebles():
    print("-", mueble)
