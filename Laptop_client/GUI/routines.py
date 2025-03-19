from gpiozero import OutputDevice # type: ignore
from time import sleep

class ControlActuadores:
    def __init__(self): # Configuración de los pines GPIO para los actuadores
        self.actuadores = {
            1: OutputDevice(22),  # Actuador 1 en GPIO 22, Dedo pulgar, rojo
            2: OutputDevice(23),  # Actuador 2 en GPIO 23, Dedo índice, naranja
            3: OutputDevice(24),  # Actuador 3 en GPIO 24, Dedo medio, amarillo
            4: OutputDevice(25),  # Actuador 4 en GPIO 25, Dedo anular, verde
            5: OutputDevice(27),  # Actuador 5 en GPIO 27, Dedo meñique, azul    
        }
        print("Inicializando controlador de actuadores con GPIO.")
        
        self.posicion_reposo() # Asegurar que los actuadores estén en posición de reposo al iniciar el programa

    def mover_actuador(self, actuador_num, tiempo_avance, tiempo_retroceso):
        """
            Mueve un actuador hacia adelante y luego lo retrae.
        """
        print(f"Actuador {actuador_num}: Avanzando...")
        self.actuadores[actuador_num].on()  # Activar el actuador (avanzar)
        sleep(tiempo_avance)  # Tiempo de avance
        print(f"Actuador {actuador_num}: Retrocediendo...")
        self.actuadores[actuador_num].off()  # Desactivar el actuador (retroceder)
        sleep(tiempo_retroceso)  # Tiempo de retroceso
        print(f"Actuador {actuador_num}: Detenido.")

    def posicion_reposo(self):
        """
            Retrae todos los actuadores a su posición de reposo.
        """
        print("Llevando todos los actuadores a la posición de reposo...")
        for actuador_num in self.actuadores:
            print(f"Retrayendo Actuador {actuador_num}...")
            self.actuadores[actuador_num].off()  # Asegurar que el actuador esté desactivado
            sleep(1)  # Tiempo para asegurar que el actuador retroceda completamente
        print("Todos los actuadores están en posición de reposo.\n")

    def rutina_1(self): # (self, actuador_num, tiempo_avance, tiempo_retroceso)
        """
            Rutina 1: Secuencia de actuadores 1, 2, 3, 4, 5 con tiempos diferentes.
        """
        print("Iniciando Rutina 1...")
        self.mover_actuador(1, 2, 1)  # Actuador 1: Avanza 2s, retrocede 1s
        self.mover_actuador(2, 1, 2)  # Actuador 2: Avanza 1s, retrocede 2s
        self.mover_actuador(3, 3, 1)  # Actuador 3: Avanza 3s, retrocede 1s
        self.mover_actuador(4, 1, 1)  # Actuador 4: Avanza 1s, retrocede 1s
        self.mover_actuador(5, 2, 2)  # Actuador 5: Avanza 2s, retrocede 2s
        print("Rutina 1 completada.\n")

    def rutina_2(self):
        """
            Rutina 2: Secuencia de actuadores 5, 4, 3, 2, 1 con tiempos diferentes.
        """
        print("Iniciando Rutina 2...")
        self.mover_actuador(5, 1, 1)  
        self.mover_actuador(4, 2, 2)  
        self.mover_actuador(3, 1, 3)  
        self.mover_actuador(2, 3, 1)  
        self.mover_actuador(1, 2, 2)  
        print("Rutina 2 completada.\n")

    def rutina_3(self):
        """
            Rutina 3: Secuencia de actuadores 3, 1, 5, 2, 4 con tiempos diferentes.
        """
        print("Iniciando Rutina 3...")
        self.mover_actuador(3, 2, 1)  
        self.mover_actuador(1, 1, 2)  
        self.mover_actuador(5, 3, 1)  
        self.mover_actuador(2, 1, 1)  
        self.mover_actuador(4, 2, 2)  
        print("Rutina 3 completada.\n")

    def limpiar(self):
        """
            Detiene y limpia todos los actuadores.
        """
        print("Limpiando y deteniendo todos los actuadores...")
        for actuador in self.actuadores.values():
            actuador.off()  
        print("Todos los actuadores detenidos.\n")