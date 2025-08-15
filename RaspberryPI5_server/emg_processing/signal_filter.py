from __future__ import annotations
import math
import random
from dataclasses import dataclass
from typing import List

@dataclass
class EMGSimulator:
    """
    Simulador ligero de EMG para N canales, sin numpy.
    Genera ruido banda limitada con envolvente lenta y ráfagas aleatorias.
    Devuelve milivoltios (mV).
    """
    fs: int = 300            # Hz de simulación (suficiente para la GUI)
    channels: int = 2
    seed: int | None = None

    def __post_init__(self):
        self.rng = random.Random(self.seed)
        self._t = 0.0
        self._phase = [self.rng.random() * 2.0 * math.pi for _ in range(self.channels)]
        # estado por canal
        self._burst = [0.0 for _ in range(self.channels)]     # nivel de ráfaga
        self._lp_y  = [0.0 for _ in range(self.channels)]     # salida low-pass
        self._lp_a  = 0.90                                    # coef LP
        self._slow_f = [0.4 + 0.35*self.rng.random() for _ in range(self.channels)]  # 0.4–0.75 Hz

    def reset(self):
        self._t = 0.0
        self._burst = [0.0 for _ in range(self.channels)]
        self._lp_y  = [0.0 for _ in range(self.channels)]

    def _envelope(self, t: float, ch: int) -> float:
        # senoide lenta + ráfagas aleatorias con decaimiento
        self._burst[ch] *= 0.94
        if self.rng.random() < 0.02:           # ~2% prob. por muestra
            self._burst[ch] += 1.0
        slow = 0.5 + 0.5 * math.sin(2*math.pi*self._slow_f[ch]*t + self._phase[ch])
        env = 0.25 + 0.9 * (slow + self._burst[ch])
        # limita envolvente (mV relativos)
        return max(0.05, min(env, 3.0))

    def next_chunk(self, n: int = 10) -> List[List[float]]:
        """
        Devuelve lista por canal con 'n' muestras (mV).
        shape: [channels][n]
        """
        out = [[0.0]*n for _ in range(self.channels)]
        dt = 1.0 / self.fs
        for i in range(n):
            t = self._t
            self._t += dt
            for ch in range(self.channels):
                # ruido ~N(0,1) con Box-Muller
                u1, u2 = max(1e-12, self.rng.random()), self.rng.random()
                gauss = math.sqrt(-2.0*math.log(u1)) * math.cos(2*math.pi*u2)
                # banda limitada (LP IIR sencillo)
                self._lp_y[ch] = self._lp_a*self._lp_y[ch] + (1.0-self._lp_a)*gauss
                env = self._envelope(t, ch)
                y = self._lp_y[ch] * env * 2.0          # ~2 mV pico típico
                out[ch][i] = y
        return out
