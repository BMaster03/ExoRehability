from time import sleep
from gpiozero import DigitalOutputDevice, Device # type: ignore
from gpiozero.pins.lgpio import LGPIOFactory # type: ignore

Device.pin_factory = LGPIOFactory()

class ControlActuadores:
    """
    Mapea 5 actuadores (1..5) a 5 dedos. Cada actuador tiene 2 relés (A/B).
    'open'  -> A ON (B OFF)
    'close' -> B ON (A OFF)

    Seguridad:
    - Interlock: nunca A y B activos a la vez
    - Deadtime: pequeña pausa antes de invertir sentido
    - HOME: todo OFF al inicio y al finalizar cada rutina
    """

    RELAY_PINS_BCM = {
        1: {"A": 17, "B": 27},  # pulgar
        2: {"A": 22, "B": 23},  # índice
        3: {"A": 24, "B": 25},  # medio
        4: {"A": 5,  "B": 6},   # anular
        5: {"A": 12, "B": 13},  # meñique
    }

    deadtime_s = 0.05

    def __init__(self, actualizar_estado=None):  # <-- acepta el callback
        self.actualizar_estado = actualizar_estado

        self.actuadores = {
            1: {"estado": "reposo"},
            2: {"estado": "reposo"},
            3: {"estado": "reposo"},
            4: {"estado": "reposo"},
            5: {"estado": "reposo"},
        }

        self.relays = {}
        for n, pins in self.RELAY_PINS_BCM.items():
            self.relays[n] = {
                "A": DigitalOutputDevice(pins["A"], active_high=True, initial_value=False),
                "B": DigitalOutputDevice(pins["B"], active_high=True, initial_value=False),
            }

        self._msg("Inicializando controlador de actuadores (GPIO listo con LGPIO).")
        self.posicion_reposo()

    # helper para log + UI
    def _msg(self, texto: str):
        print(texto)
        if self.actualizar_estado:
            try:
                self.actualizar_estado(texto)
            except Exception:
                pass

    def activar_actuador(self, actuador_num: int):
        self.actuadores[actuador_num]["estado"] = "activo"
        self._msg(f"Actuador {actuador_num}: Activado (lógico).")

    def desactivar_actuador(self, actuador_num: int):
        self.actuadores[actuador_num]["estado"] = "reposo"
        self._both_off(actuador_num)
        self._msg(f"Actuador {actuador_num}: Desactivado (A=OFF, B=OFF).")

    def mover_actuador(self, actuador_num: int, tiempo_avance: float, tiempo_pause: float,
                       tiempo_retroceso: float, sentido_inicio: str = "open"):
        self._msg(f"Moviendo Actuador {actuador_num}...")
        self.activar_actuador(actuador_num)

        self._drive(actuador_num, sentido=sentido_inicio, dur_s=float(tiempo_avance))
        self._msg(f"Actuador {actuador_num}: Avanzando por {tiempo_avance} s.")

        self._both_off(actuador_num)
        self._msg(f"Actuador {actuador_num}: En pausa por {tiempo_pause} s.")
        sleep(max(0.0, float(tiempo_pause)))

        sentido_vuelta = "close" if sentido_inicio == "open" else "open"
        self._drive(actuador_num, sentido=sentido_vuelta, dur_s=float(tiempo_retroceso))
        self._msg(f"Actuador {actuador_num}: Retrocediendo por {tiempo_retroceso} s.")

        self.desactivar_actuador(actuador_num)
        self._msg(f"Actuador {actuador_num}: Detenido.\n")

    def posicion_reposo(self):
        self._msg("Llevando todos los actuadores a la posición de reposo (HOME)...")
        for actuador_num in self.actuadores:
            self._both_off(actuador_num)
            self.actuadores[actuador_num]["estado"] = "reposo"
        self._msg("Todos los actuadores en reposo.\n")

    def rutina_1(self):
        self._msg("Iniciando Rutina 1...")
        try:
            self.posicion_reposo()
            self.mover_actuador(1, 2, 1, 2)
            self.mover_actuador(2, 2, 1, 2)
            self.mover_actuador(3, 2, 1, 2)
            self.mover_actuador(4, 2, 1, 2)
            self.mover_actuador(5, 2, 1, 2)
            self._msg("Rutina 1 completada.\n")
        finally:
            self.posicion_reposo()

    def rutina_2(self):
        self._msg("Iniciando Rutina 2...")
        try:
            self.posicion_reposo()
            self.mover_actuador(5, 2, 1, 2)
            self.mover_actuador(4, 2, 1, 2)
            self.mover_actuador(3, 2, 1, 2)
            self.mover_actuador(2, 2, 1, 2)
            self.mover_actuador(1, 2, 1, 2)
            self._msg("Rutina 2 completada.\n")
        finally:
            self.posicion_reposo()

    def rutina_3(self):
        self._msg("Iniciando Rutina 3...")
        try:
            self.posicion_reposo()
            self.mover_actuador(3, 2, 1, 1)
            self.mover_actuador(1, 1, 1, 2)
            self.mover_actuador(5, 3, 1, 1)
            self.mover_actuador(2, 1, 1, 1)
            self.mover_actuador(4, 2, 1, 2)
            self._msg("Rutina 3 completada.\n")
        finally:
            self.posicion_reposo()

    def _both_off(self, actuador_num: int):
        A = self.relays[actuador_num]["A"]
        B = self.relays[actuador_num]["B"]
        A.off(); B.off()

    def _drive(self, actuador_num: int, sentido: str, dur_s: float):
        assert sentido in ("open", "close"), "sentido debe ser 'open' o 'close'"
        A = self.relays[actuador_num]["A"]
        B = self.relays[actuador_num]["B"]

        A.off(); B.off()
        sleep(self.deadtime_s)

        if sentido == "open":
            A.on(); B.off()
        else:
            B.on(); A.off()

        sleep(max(0.0, float(dur_s)))

        A.off(); B.off()
        sleep(self.deadtime_s)

    def limpiar(self):
        self._msg("Limpiando: apagando todos los relés y liberando GPIO.")
        self.posicion_reposo()
        for n in self.relays:
            self.relays[n]["A"].close()
            self.relays[n]["B"].close()
