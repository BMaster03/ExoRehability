import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
from  Laptop_client.GUI.data import ECGSimulator
import numpy as np

def mostrar_ecg_tiempo_real():
    sim = ECGSimulator(fs=100)

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.subplots_adjust(bottom=0.2)  # Espacio para botones
    fig.patch.set_facecolor('#f0f0f5')
    ax.set_facecolor('#ffffff')

    x_data, y_data = [], []
    line, = ax.plot([], [], lw=2, color='#007ACC')
    fill = None

    ventana = 5  # ancho ventana visible (segundos)
    x_min = 0
    x_max = ventana

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-0.5, 1.5)

    ax.grid(True, linestyle='--', alpha=0.4)
    ax.set_title('Simulación ECG en Tiempo Real', fontsize=16, color='#333333')
    ax.set_xlabel('Tiempo (s)', fontsize=12)
    ax.set_ylabel('Amplitud (mV)', fontsize=12)

    paused = [False]

    ax_pause = plt.axes([0.8, 0.05, 0.1, 0.075])
    btn_pause = Button(ax_pause, 'Pausar', color='#007ACC', hovercolor='#005f99')

    def toggle_pause(event):
        paused[0] = not paused[0]
        btn_pause.label.set_text('Reanudar' if paused[0] else 'Pausar')

    btn_pause.on_clicked(toggle_pause)

    def init():
        nonlocal fill
        line.set_data([], [])
        if fill:
            fill.remove()
        fill = None
        return line,

    def update(frame):
        nonlocal fill, x_max, x_min

        if paused[0]:
            return (line, fill) if fill else (line,)

        ecg_segment, tiempos_segment = sim.generar(duracion=0.05)
        tiempos_abs = tiempos_segment

        x_data.extend(tiempos_abs)
        y_data.extend(ecg_segment)

        # Mantener los datos con un máximo de 60 segundos para evitar uso excesivo de memoria
        while x_data and (x_data[-1] - x_data[0] > 60):
            x_data.pop(0)
            y_data.pop(0)

        line.set_data(x_data, y_data)

        # No movemos automáticamente el scroll si el usuario desplazó el eje X manualmente
        # Solo ajustamos límites si el scroll está en el extremo derecho (ver más abajo)

        # Actualizar límites solo si estamos viendo el final del gráfico para que la animación avance
        if x_max >= x_data[-1] - 0.1:
            x_max = x_data[-1]
            x_min = max(0, x_max - ventana)
            ax.set_xlim(x_min, x_max)
            ticks = np.arange(np.floor(x_min), np.ceil(x_max) + 1, 1)
            ax.set_xticks(ticks)
            ax.set_xticklabels([f"{tick:.0f}" for tick in ticks])

        if fill:
            fill.remove()
        fill = ax.fill_between(x_data, y_data, color='#007ACC', alpha=0.2)

        return line, fill

    def on_scroll(event):
        nonlocal x_min, x_max, ventana

        step = ventana * 0.1  # desplazamiento por scroll

        if event.button == 'up':  # rueda hacia arriba: desplazamos a la derecha (mostrar datos más recientes)
            x_min = min(x_min + step, x_data[-1] - ventana)
            x_max = x_min + ventana
        elif event.button == 'down':  # rueda hacia abajo: desplazamos a la izquierda (datos más antiguos)
            x_min = max(0, x_min - step)
            x_max = x_min + ventana

        ax.set_xlim(x_min, x_max)
        ticks = np.arange(np.floor(x_min), np.ceil(x_max) + 1, 1)
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{tick:.0f}" for tick in ticks])
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect('scroll_event', on_scroll)

    ani = animation.FuncAnimation(fig, update, init_func=init, interval=50, blit=True)

    plt.rcParams['toolbar'] = 'toolbar2'

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    mostrar_ecg_tiempo_real()