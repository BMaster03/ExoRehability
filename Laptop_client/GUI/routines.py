from time import sleep

class ControlActuadores:
    def __init__(self):
        # Simulación de actuadores (sin GPIO)
        print("Inicializando controlador de actuadores (simulación).")

    def rutina_1(self):
        """Simula mover los actuadores 1 y 2 hacia adelante."""
        print("Rutina 1: Actuadores 1 y 2 avanzando...")
        sleep(2)  # Simula el tiempo de movimiento
        print("Rutina 1: Actuadores 1 y 2 detenidos.")

    def rutina_2(self):
        """Simula mover los 5 actuadores hacia adelante y luego retroceder."""
        print("Rutina 2: Todos los actuadores avanzando...")
        sleep(3)  # Simula el tiempo de movimiento
        print("Rutina 2: Todos los actuadores retrocediendo...")
        sleep(3)
        print("Rutina 2: Actuadores detenidos.")

    def rutina_3(self):
        """Simula mover los actuadores 3, 4 y 5 hacia adelante."""
        print("Rutina 3: Actuadores 3, 4 y 5 avanzando...")
        sleep(2)  # Simula el tiempo de movimiento
        print("Rutina 3: Actuadores 3, 4 y 5 detenidos.")

    def limpiar(self):
        """Simula la limpieza de los actuadores."""
        print("Limpiando y deteniendo todos los actuadores (simulación).")