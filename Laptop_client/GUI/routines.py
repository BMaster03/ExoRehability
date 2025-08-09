from time import sleep, time

class ControlActuadores:
    def __init__(self, actualizar_estado=None):
        """
        actualizar_estado: función para mostrar mensajes en la interfaz (opcional).
        """
        self.actualizar_estado = actualizar_estado
        print("Inicializando controlador de actuadores (simulación).")

    def rutina_1(self):
        self._mensaje("Rutina 1: Actuadores 1 y 2 avanzando...")
        sleep(5)
        self._mensaje("Rutina 1: Completada.")

    def rutina_2(self):
        self._mensaje("Rutina 2: Todos los actuadores avanzando...")
        sleep(2.5)
        self._mensaje("Rutina 2: Retrocediendo...")
        sleep(2.5)
        self._mensaje("Rutina 2: Completada.")

    def rutina_3(self):
        self._mensaje("Rutina 3: Actuadores 3, 4 y 5 avanzando...")
        sleep(5)
        self._mensaje("Rutina 3: Completada.")

    def limpiar(self):
        self._mensaje("Limpiando y deteniendo todos los actuadores (simulación).")

    def _mensaje(self, texto):
        print(texto)
        if self.actualizar_estado:
            self.actualizar_estado(texto)
