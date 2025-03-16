import math
import random

class SimulacionEMG:
    def __init__(self):
        # Inicialización de la simulación
        pass

    def generar_senal_emg(self, tiempo):
        """Genera una señal EMG simulada."""
        # Simulación de una señal EMG con una función senoidal y ruido aleatorio
        señal = math.sin(tiempo) + random.uniform(-0.2, 0.2)
        return señal