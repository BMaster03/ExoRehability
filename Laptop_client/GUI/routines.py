from time import sleep
import threading
from gpiozero import DigitalOutputDevice, Device  # type: ignore
from gpiozero.pins.lgpio import LGPIOFactory      # type: ignore

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

    def __init__(self, actualizar_estado=None):
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

    # ------------------------ utilidades de log ------------------------
    def _msg(self, texto: str):
        print(texto)
        if self.actualizar_estado:
            try:
                self.actualizar_estado(texto)
            except Exception:
                pass

    # ------------------------ API pública ------------------------------
    def activar_actuador(self, actuador_num: int):
        self.actuadores[actuador_num]["estado"] = "activo"
        self._msg(f"Actuador {actuador_num}: Activado (lógico).")

    def desactivar_actuador(self, actuador_num: int):
        self.actuadores[actuador_num]["estado"] = "reposo"
        self._both_off(actuador_num)
        self._msg(f"Actuador {actuador_num}: Desactivado (A=OFF, B=OFF).")

    def mover_actuador(self, actuador_num: int, tiempo_avance: float, tiempo_pause: float,
                       tiempo_retroceso: float, sentido_inicio: str = "open"):
        """
        Secuencia completa para 1 actuador: avance -> pausa -> retroceso.
        """
        self._msg(f"Moviendo Actuador {actuador_num}...")
        self.activar_actuador(actuador_num)

        # Avance
        self._drive(actuador_num, sentido=sentido_inicio, dur_s=float(tiempo_avance))
        self._msg(f"Actuador {actuador_num}: Avanzando por {tiempo_avance} s.")

        # Pausa con todo en OFF
        self._both_off(actuador_num)
        self._msg(f"Actuador {actuador_num}: En pausa por {tiempo_pause} s.")
        sleep(max(0.0, float(tiempo_pause)))

        # Retroceso
        sentido_vuelta = "close" if sentido_inicio == "open" else "open"
        self._drive(actuador_num, sentido=sentido_vuelta, dur_s=float(tiempo_retroceso))
        self._msg(f"Actuador {actuador_num}: Retrocediendo por {tiempo_retroceso} s.")

        # Finaliza
        self.desactivar_actuador(actuador_num)
        self._msg(f"Actuador {actuador_num}: Detenido.\n")

    def posicion_reposo(self):
        self._msg("Llevando todos los actuadores a la posición de reposo (HOME)...")
        for actuador_num in self.actuadores:
            self._both_off(actuador_num)
            self.actuadores[actuador_num]["estado"] = "reposo"
        self._msg("Todos los actuadores en reposo.\n")

    # ------------------------ Rutinas EN PARALELO ----------------------
    def _run_parallel(self, tareas):
        """
        Ejecuta en paralelo una lista de callables (sin argumentos) y espera a que terminen.
        """
        hilos = [threading.Thread(target=t, daemon=True) for t in tareas]
        for th in hilos:
            th.start()
        for th in hilos:
            th.join()

    def rutina_1(self):
        """
        Rutina 1 (PARALELA):
        Todos los actuadores 1..5 avanzan al mismo tiempo 2s, pausa 1s, retroceso 2s.
        """
        self._msg("Iniciando Rutina 1 (paralela)...")
        try:
            self.posicion_reposo()
            tareas = [
                (lambda n=n: self.mover_actuador(n, 2, 1, 2, "open"))
                for n in (1, 2, 3, 4, 5)
            ]
            self._run_parallel(tareas)
            self._msg("Rutina 1 completada.\n")
        finally:
            self.posicion_reposo()

    def rutina_2(self):
        """
        Rutina 2 (PARALELA):
        Todos los actuadores 1..5 avanzan al mismo tiempo 2s, pausa 1s, retroceso 2s.
        (Mantengo los mismos tiempos para coherencia; si quieres otros, cámbialos aquí.)
        """
        self._msg("Iniciando Rutina 2 (paralela)...")
        try:
            self.posicion_reposo()
            tareas = [
                (lambda n=n: self.mover_actuador(n, 2, 1, 2, "open"))
                for n in (1, 2, 3, 4, 5)
            ]
            self._run_parallel(tareas)
            self._msg("Rutina 2 completada.\n")
        finally:
            self.posicion_reposo()

    def rutina_3(self):
        """
        Rutina 3 (PARALELA):
        Ejemplo con tiempos distintos por actuador, pero todos arrancan juntos.
        - 3: 2s, pausa 1s, ret 1s
        - 1: 1s, pausa 1s, ret 2s
        - 5: 3s, pausa 1s, ret 1s
        - 2: 1s, pausa 1s, ret 1s
        - 4: 2s, pausa 1s, ret 2s
        """
        self._msg("Iniciando Rutina 3 (paralela)...")
        try:
            self.posicion_reposo()
            tareas = [
                (lambda: self.mover_actuador(3, 2, 1, 1, "open")),
                (lambda: self.mover_actuador(1, 1, 1, 2, "open")),
                (lambda: self.mover_actuador(5, 3, 1, 1, "open")),
                (lambda: self.mover_actuador(2, 1, 1, 1, "open")),
                (lambda: self.mover_actuador(4, 2, 1, 2, "open")),
            ]
            self._run_parallel(tareas)
            self._msg("Rutina 3 completada.\n")
        finally:
            self.posicion_reposo()

    # ------------------------ Bajo nivel (seguridad) -------------------
    def _both_off(self, actuador_num: int):
        A = self.relays[actuador_num]["A"]
        B = self.relays[actuador_num]["B"]
        A.off(); B.off()

    def _drive(self, actuador_num: int, sentido: str, dur_s: float):
        assert sentido in ("open", "close"), "sentido debe ser 'open' o 'close'"
        A = self.relays[actuador_num]["A"]
        B = self.relays[actuador_num]["B"]

        # Interlock + deadtime
        A.off(); B.off()
        sleep(self.deadtime_s)

        # Activa solo el sentido requerido
        if sentido == "open":
            A.on(); B.off()
        else:
            B.on(); A.off()

        # Mantiene activación el tiempo solicitado
        sleep(max(0.0, float(dur_s)))

        # Apaga y espera deadtime
        A.off(); B.off()
        sleep(self.deadtime_s)

    def limpiar(self):
        self._msg("Limpiando: apagando todos los relés y liberando GPIO.")
        self.posicion_reposo()
        for n in self.relays:
            self.relays[n]["A"].close()
            self.relays[n]["B"].close()
