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