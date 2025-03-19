import flet as ft
from Laptop_client.GUI.routines import ControlActuadores

# Inicializa el controlador de actuadores (simulación)
controlador = ControlActuadores()

def main(page: ft.Page):
    page.title = "Control de Actuadores Lineales (Simulación)"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Estado actual de la rutina
    status = ft.Text(value="Estado: En espera", size=20)

    # Función para ejecutar la rutina seleccionada
    def ejecutar_rutina(e):     
        rutina_seleccionada = dropdown_rutinas.value
        if rutina_seleccionada == "Rutina 1":
            controlador.rutina_1()
            status.value = "Ejecutando Rutina 1"
        elif rutina_seleccionada == "Rutina 2":
            controlador.rutina_2()
            status.value = "Ejecutando Rutina 2"
        elif rutina_seleccionada == "Rutina 3":
            controlador.rutina_3()
            status.value = "Ejecutando Rutina 3"
        page.update()

    # Menú desplegable para seleccionar rutinas
    dropdown_rutinas = ft.Dropdown(
        options=[
            ft.dropdown.Option("Rutina 1"),
            ft.dropdown.Option("Rutina 2"),
            ft.dropdown.Option("Rutina 3"),
        ],
        width=200,
        hint_text="Selecciona una rutina",
    )

    # Botón para ejecutar la rutina seleccionada
    btn_ejecutar = ft.ElevatedButton(text="Ejecutar Rutina", on_click=ejecutar_rutina)

    # Añadir widgets a la página
    page.add(
        status,
        ft.Row([dropdown_rutinas, btn_ejecutar], alignment=ft.MainAxisAlignment.CENTER)
    )

# Ejecutar la aplicación Flet
ft.app(target=main)