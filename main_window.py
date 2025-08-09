import flet as ft
import threading
from Laptop_client.GUI.routines import ControlActuadores
from Laptop_client.GUI.signal_graph import mostrar_ecg_tiempo_real

def window_main(page: ft.Page):
    # Configuración básica de la ventana
    page.title            = "Exo-arm-1"                   # Título ventana
    page.bgcolor          = ft.Colors.BLUE_GREY_900       # Color fondo
    page.window.width     = 600                            # Ancho ventana
    page.window.height    = 580                            # Alto ventana
    page.window.resizable = False                          # No redimensionable

    # Configuración fuente personalizada
    page.fonts = {"Poppins": "/fonts/Poppins-Regular.ttf"}  # Fuente Poppins cargada
    page.theme = ft.Theme(font_family="Poppins")             # Aplicar fuente a toda la app

    # Texto para mostrar el estado actual (espera, ejecución, etc.)
    status = ft.Text(value="Estado: En espera", size=14, color=ft.Colors.GREY_300)
    estado_container = ft.Container(
        content       = status,
        padding       = 10,
        border_radius = 12,
        bgcolor       = ft.Colors.with_opacity(0.08, ft.Colors.GREY_100),  # Fondo tenue
        width         = 250
    )

    # Función para actualizar el texto del estado y refrescar interfaz
    def actualizar_estado(texto):
        status.value = texto
        page.update()

    # Instancia del controlador que maneja las rutinas, con función para actualizar estado
    controlador = ControlActuadores(actualizar_estado=actualizar_estado)

    # Cambiar visualmente el estado con texto y color de fondo
    def set_estado_visual(texto, color):
        status.value = texto
        estado_container.bgcolor = color
        page.update()

    # Funciones para menú lateral (a implementar según necesidad)
    def mostrar_datos_anteriores(e):
        pass

    def abrir_datos_actuales(e):
        # Abre ventana con ECG en hilo aparte para no congelar UI
        threading.Thread(target=mostrar_ecg_tiempo_real, daemon=True).start()

    # Menú lateral (drawer) con opciones configuradas
    page.drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(ft.Text("⚙️ Opciones", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), padding=10),
            ft.TextButton("📁 Datos anteriores", on_click=mostrar_datos_anteriores, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
            ft.TextButton("📈 Datos actuales", on_click=abrir_datos_actuales, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
        ],
        bgcolor=ft.Colors.BLUE_GREY_800
    )

    # Ejecutar rutina seleccionada desde dropdown
    def ejecutar_rutina(e):
        rutina_seleccionada = rutina.value
        rutina.disabled = True           # Desactiva dropdown para evitar cambios
        btn_ejecutar.disabled = True    # Desactiva botón para evitar clicks repetidos
        set_estado_visual(f"Ejecutando {rutina_seleccionada}...", ft.Colors.GREEN_300)

        # Ejecuta rutina en hilo separado para no bloquear UI
        def run():
            getattr(controlador, f"rutina_{rutina_seleccionada[-1]}")()
            set_estado_visual("Estado: En espera", ft.Colors.with_opacity(0.08, ft.Colors.GREY_100))
            rutina.disabled = False
            btn_ejecutar.disabled = False
            page.update()

        threading.Thread(target=run).start()

    # Habilita/deshabilita botón según si hay rutina seleccionada
    def on_dropdown_change(e):
        btn_ejecutar.disabled = not rutina.value or rutina.disabled
        page.update()

    # Dropdown para seleccionar entre Rutina 1, 2 o 3
    rutina = ft.Dropdown(
        options=[ft.dropdown.Option(f"Rutina {i}") for i in range(1, 4)],
        width=220,
        hint_text="Selecciona una rutina",
        on_change=on_dropdown_change,
        text_style=ft.TextStyle(color=ft.Colors.WHITE),
        hint_style=ft.TextStyle(color=ft.Colors.GREY_400)
    )

    # Botón para ejecutar la rutina seleccionada
    btn_ejecutar = ft.FilledButton(
        text="🚀 Ejecutar Rutina",
        on_click=ejecutar_rutina,
        bgcolor=ft.Colors.INDIGO,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
        disabled=True  # Inicia deshabilitado hasta seleccionar rutina
    )

    # Función para crear botones con estilo uniforme para control sensores
    def crear_boton(texto, icono, color):
        return ft.FilledButton(
            text=texto,
            icon=icono,
            bgcolor=color,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=18),
                padding=ft.Padding(12, 10, 12, 10),
            ),
            height=45,
            width=180
        )

    # Abre el menú lateral (drawer)
    def abrir_menu(e):
        page.drawer.open = True
        page.update()

    # Sección usuarios con botones para "Usuarios" y "Pacientes"
    usuarios_section = ft.Column([
        ft.Text("Usuarios", size=14, color=ft.Colors.GREY_300),
        ft.OutlinedButton("Usuarios", icon=ft.Icons.PERSON, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
        ft.OutlinedButton("Pacientes", icon=ft.Icons.PEOPLE, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
    ], spacing=10)

    # Sección control de sensores con botones Start, Stop y Reset
    sensores_section = ft.Column([
        ft.Text("Control de sensores", size=14, color=ft.Colors.GREY_300),
        crear_boton("Start Sensor", ft.Icons.PLAY_ARROW, ft.Colors.GREEN_400),
        crear_boton("Stop Sensor", ft.Icons.STOP, ft.Colors.RED_400),
        crear_boton("Reset Sensor", ft.Icons.REFRESH, ft.Colors.AMBER_400),
    ], spacing=10)

    # Panel izquierdo con menú y botones
    menu_column = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(icon=ft.Icons.MENU, on_click=abrir_menu, icon_color=ft.Colors.WHITE),
                    ft.Text("Panel Principal", size=16, weight="bold", color=ft.Colors.WHITE),
                ]),
                ft.Divider(color=ft.Colors.WHITE),
                usuarios_section,
                ft.Divider(color=ft.Colors.WHITE),
                sensores_section,
                ft.Divider(color=ft.Colors.WHITE),
                btn_ejecutar,
            ], spacing=10),
            padding=15
        ),
        elevation=2,
        color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12)
    )

    # Panel derecho con la imagen cargada desde assets, dropdown y estado
    side_column = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Image(src="arm.png", width=160),  # Imagen desde carpeta assets
                    alignment=ft.alignment.center
                ),
                rutina,
                estado_container
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15
        ),
        elevation=2,
        color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12)
    )

    # Layout principal con los dos paneles lado a lado
    layout = ft.Row(
        [menu_column, side_column],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        expand=True
    )

    # Añadir layout a la página
    page.add(layout)

# Aquí indicamos que la carpeta "assets" contiene los archivos estáticos (imágenes, fuentes, etc.)
ft.app(target=window_main, assets_dir="assets")
