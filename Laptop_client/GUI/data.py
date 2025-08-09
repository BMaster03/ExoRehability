import numpy as np

class ECGSimulator:
    def __init__(self, fs=100):
        self.fs = fs
        self.t = 0

    def generar(self, duracion=0.05):
        n = int(self.fs * duracion)
        tiempos = np.linspace(self.t, self.t + duracion, n, endpoint=False)
        base = 0.05 * np.sin(2 * np.pi * 1 * tiempos)
        qrs = np.exp(-((tiempos - np.round(tiempos)) ** 2) / 0.0015)
        ruido = 0.02 * np.random.randn(n)
        ecg = base + qrs + ruido
        self.t += duracion
        return ecg.tolist(), tiempos.tolist()

