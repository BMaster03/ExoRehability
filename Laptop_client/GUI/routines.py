# routines.py
from __future__ import annotations
from time import sleep
import threading

# --- Intentamos usar GPIO real; si falla, simulamos (útil en laptop) ---
try:
    from gpiozero import DigitalOutputDevice, Device  # type: ignore
    from gpiozero.pins.lgpio import LGPIOFactory      # type: ignore
    Device.pin_factory = LGPIOFactory()
    _GPIO_OK = True
except Exception:
    _GPIO_OK = False

    class DigitalOutputDevice:  # simulador mínimo
        def __init__(self, pin, active_high=True, initial_value=False):
            self.pin = pin
            self.state = bool(initial_value)
        def on(self):  self.state = True
        def off(self): self.state = False
        def close(self): self.off()


class ControlActuadores:
    """
    Mapea 5 actuadores (1..5) a 5 dedos. Cada actuador tiene 2 relés (A/B).
    'open'  -> A ON (B OFF)
    'close' -> B ON (A OFF)

    Seguridad:
    - Interlock: nunca A y B activos a la vez
    - Deadtime: pequeña pausa antes de invertir sentido
    - HOME: todo OFF; además exponemos home_now() que hace 3s de 'close' en paralelo.
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
        self.relays = {}
        for n, pins in self.RELAY_PINS_BCM.items():
            self.relays[n] = {
                "A": DigitalOutputDevice(pins["A"], active_high=True, initial_value=False),
                "B": DigitalOutputDevice(pins["B"], active_high=True, initial_value=False),
            }
        self._msg("Inicializando controlador de actuadores "
                  + ("(GPIO real LGPIO)." if _GPIO_OK else "(SIM sin GPIO)."))
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
    def posicion_reposo(self):
        """Todo OFF."""
        for n in self.relays:
            self._both_off(n)
        self._msg("Todos los actuadores en reposo (OFF).")

    def home_now(self, close_seconds: float = 3.0):
        """
        'HOME' mecánico: pone TODOS en 'close' durante close_seconds en paralelo
        y luego OFF. Útil para regresar al origen.
        """
        self._msg(f"HOME: todos en 'close' {close_seconds:.2f}s en paralelo...")
        tareas = [lambda n=n: self._drive(n, "close", float(close_seconds)) for n in self.relays]
        self._run_parallel(tareas)
        self.posicion_reposo()
        self._msg("HOME completado.")

    def stop_and_home(self, stop_event: threading.Event | None = None, close_seconds: float = 3.0):
        """
        Señal de paro + HOME. Si recibimos stop_event lo marcamos, y ejecutamos HOME.
        """
        if stop_event:
            stop_event.set()
        self._msg("PARO solicitado: llevando a HOME.")
        self.home_now(close_seconds=close_seconds)

    def mover_actuador(self, actuador_num: int, tiempo_avance: float,
                       tiempo_pause: float, tiempo_retroceso: float,
                       sentido_inicio: str = "open",
                       stop_event: threading.Event | None = None):
        """
        Secuencia completa para 1 actuador: avance -> pausa -> retroceso.
        Responde a stop_event si se marca entre fases.
        """
        if stop_event and stop_event.is_set():
            return

        self._msg(f"Actuador {actuador_num}: Avance {tiempo_avance}s, pausa {tiempo_pause}s, retroceso {tiempo_retroceso}s.")
        # Avance
        self._drive(actuador_num, sentido=sentido_inicio, dur_s=float(tiempo_avance))
        if stop_event and stop_event.is_set():
            return

        # Pausa OFF
        self._both_off(actuador_num)
        self._sleep_with_stop(tiempo_pause, stop_event)
        if stop_event and stop_event.is_set():
            return

        # Retroceso
        sentido_vuelta = "close" if sentido_inicio == "open" else "open"
        self._drive(actuador_num, sentido=sentido_vuelta, dur_s=float(tiempo_retroceso))
        self._both_off(actuador_num)

    # ------------------------ Rutinas base --------------------------------
    def rutina_1_once(self, stop_event: threading.Event | None = None):
        """Todos (1..5) en paralelo: 2s avance, 4s pausa, 2s retroceso."""
        self._msg("Rutina 1 (paralela) - una pasada.")
        tareas = [
            (lambda n=n: self.mover_actuador(n, 2, 4, 2, "open", stop_event))
            for n in (1, 2, 3, 4, 5)
        ]
        self._run_parallel(tareas)

    def rutina_2_once(self, stop_event: threading.Event | None = None):
        """Todos (1..5) en paralelo: 0.5s avance, 4s pausa, 0.5s retroceso."""
        self._msg("Rutina 2 (paralela) - una pasada.")
        tareas = [
            (lambda n=n: self.mover_actuador(n, 0.5, 4, 0.5, "open", stop_event))
            for n in (1, 2, 3, 4, 5)
        ]
        self._run_parallel(tareas)

    def rutina_3_once(self, stop_event: threading.Event | None = None):
        """
        Patrón pedido:
        1) Cuatro dedos (2,3,4,5) en paralelo: avance/pausa/retroceso.
        2) Pulgar (1) solo.
        3) Cuatro dedos (2,3,4,5) otra vez.
        4) Pulgar (1) otra vez.
        5) Cuatro dedos (2,3,4,5) de nuevo.
        Tiempos ejemplo (ajústalos si quieres): avance=2s, pausa=1s, retroceso=2s.
        """
        self._msg("Rutina 3 (patrón 4 dedos ↔ pulgar) - una pasada.")
        grupos = [
            (2, 3, 4, 5),
            (1,),
            (2, 3, 4, 5),
            (1,),
            (2, 3, 4, 5),
        ]
        for grupo in grupos:
            if stop_event and stop_event.is_set():
                return
            tareas = [
                (lambda n=n: self.mover_actuador(n, 2, 1, 2, "open", stop_event))
                for n in grupo
            ]
            self._run_parallel(tareas)

    # ------------------------ API de ciclos --------------------------------
    def run_routine(self, name: str, cycles: int = 1, stop_event: threading.Event | None = None):
        """
        Ejecuta la rutina 'name' el número de 'cycles', respetando stop_event.
        name: "Rutina 1" | "Rutina 2" | "Rutina 3"
        """
        self._msg(f"Ejecutando {name} por {cycles} ciclo(s).")
        try:
            for i in range(cycles):
                if stop_event and stop_event.is_set():
                    break
                self._msg(f"→ Ciclo {i+1}/{cycles}")
                if name == "Rutina 1":
                    self.rutina_1_once(stop_event)
                elif name == "Rutina 2":
                    self.rutina_2_once(stop_event)
                elif name == "Rutina 3":
                    self.rutina_3_once(stop_event)
                else:
                    self._msg(f"Rutina desconocida: {name}")
                    break
            self._msg(f"{name} finalizada.")
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

    def _run_parallel(self, tareas: list[callable]):
        """Ejecuta en paralelo una lista de callables (sin args) y espera a que terminen."""
        hilos = [threading.Thread(target=t, daemon=True) for t in tareas]
        for th in hilos: th.start()
        for th in hilos: th.join()

    def _sleep_with_stop(self, dur: float, stop_event: threading.Event | None):
        """Espera 'dur' segundos comprobando stop_event para poder abortar pausa."""
        if dur <= 0:
            return
        end = max(0.0, float(dur))
        step = 0.05
        t = 0.0
        while t < end:
            if stop_event and stop_event.is_set():
                return
            sl = min(step, end - t)
            sleep(sl)
            t += sl
