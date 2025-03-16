import flet as ft
import time
from GUI.signal_graph import SimulacionEMG

def main(page: ft.Page):
    page.title = "Simulación de Señal EMG"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Inicializa la simulación
    simulacion = SimulacionEMG()

    # Configuración de la gráfica
    grafica = ft.LineChart()
    datos_grafica = ft.LineChartData()
    linea = ft.LineChartDataPoint(x=0, y=0)
    datos_grafica.data_points.append(linea)
    grafica.data_series.append(datos_grafica)

    # Configuración de los ejes de la gráfica
    grafica.bottom_axis = ft.ChartAxis(
        title=ft.Text("Tiempo (s)"),
        title_size=14,
    )
    grafica.left_axis = ft.ChartAxis(
        title=ft.Text("Amplitud"),
        title_size=14,
    )

    # Estado actual de la simulación
    estado = ft.Text(value="Presiona 'Iniciar Simulación' para comenzar", size=20)

    # Función para actualizar la gráfica
    def actualizar_grafica(e):
        tiempo_inicio = time.time()
        duracion = 20  # Duración de la simulación en segundos

        # Limpiar la gráfica antes de comenzar
        datos_grafica.data_points.clear()

        while time.time() - tiempo_inicio < duracion:
            tiempo = time.time() - tiempo_inicio
            señal = simulacion.generar_senal_emg(tiempo)

            # Agregar el nuevo punto a la gráfica
            datos_grafica.data_points.append(ft.LineChartDataPoint(x=tiempo, y=señal))

            # Actualizar la gráfica
            grafica.update()

            # Esperar un breve momento antes de la siguiente actualización
            time.sleep(0.1)

        estado.value = "Simulación finalizada"
        page.update()

    # Botón para iniciar la simulación
    btn_iniciar = ft.ElevatedButton(text="Iniciar Simulación", on_click=actualizar_grafica)

    # Añadir widgets a la página
    page.add(
        estado,
        grafica,
        btn_iniciar
    )

# Ejecutar la aplicación Flet
ft.app(target=main)