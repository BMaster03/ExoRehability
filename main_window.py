# main_window.py
import threading
import socket
import traceback
import flet as ft
import webbrowser

# ======== Config ========
LAN_IP = "169.254.69.170"   # IP fija de tu Raspberry Pi para enlace directo
HOST = LAN_IP               # el servidor escuchará solo en esta IP
START_PORT = 5000           # puerto preferido
ASSETS_DIR = "assets"       # assets/arm.png, assets/fonts/Poppins-Regular.ttf

# ¿Abrir navegador automáticamente en la MÁQUINA SERVIDOR?
# Como la Pi es el servidor y verás la UI desde tu laptop, déjalo en False.
OPEN_BROWSER_ON_SERVER = False
# ========================

def _find_free_port(host: str, start_port: int, tries: int = 50) -> int:
    # Busca un puerto libre intentando conectar: si no hay servicio, el puerto está libre
    for p in range(start_port, start_port + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.15)
            if s.connect_ex((host, p)) != 0:
                return p
    raise RuntimeError("No hay puertos libres en el rango solicitado.")

def window_main(page: ft.Page):
    # ============ UI Básica ============
    page.title = "Exo-arm-1"
    page.bgcolor = ft.Colors.BLUE_GREY_900
    page.window.resizable = False  # web lo ignora pero no molesta

    # Fuentes / Tema (dentro de assets/)
    page.fonts = {"Poppins": "fonts/Poppins-Regular.ttf"}
    page.theme = ft.Theme(font_family="Poppins")

    # Contenedor de estado + zona de errores visibles
    status = ft.Text(value="Estado: En espera", size=14, color=ft.Colors.GREY_300)
    error_box = ft.Text(value="", size=12, color=ft.Colors.RED_300, selectable=True)
    estado_container = ft.Container(
        content=ft.Column([status, error_box], tight=True, spacing=4),
        padding=10,
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREY_100),
        width=350,
    )

    def set_estado_visual(texto: str, color):
        status.value = texto
        estado_container.bgcolor = color
        page.update()

    def actualizar_estado(texto: str):
        status.value = texto
        page.update()

    # ============ Imports perezosos y manejo de errores ============
    try:
        from Laptop_client.GUI.routines import ControlActuadores
        from Laptop_client.GUI.signal_graph import mostrar_ecg_tiempo_real
    except Exception:
        tb = traceback.format_exc()
        error_box.value = "Error al importar módulos:\n" + tb
        set_estado_visual("Error al iniciar (imports).", ft.Colors.RED_300)
        page.add(
            ft.Container(
                content=ft.Text(
                    "Revisa el error mostrado y corrige dependencias/rutas.",
                    color=ft.Colors.RED_100
                ),
                padding=10
            )
        )
        page.update()
        return

    controlador = ControlActuadores(actualizar_estado=actualizar_estado)

    # Drawer
    def mostrar_datos_anteriores(e):
        pass

    def abrir_datos_actuales(e):
        threading.Thread(target=mostrar_ecg_tiempo_real, daemon=True).start()

    page.drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                ft.Text("⚙️ Opciones", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                padding=10,
            ),
            ft.TextButton("📁 Datos anteriores", on_click=mostrar_datos_anteriores,
                          style=ft.ButtonStyle(color=ft.Colors.WHITE)),
            ft.TextButton("📈 Datos actuales", on_click=abrir_datos_actuales,
                          style=ft.ButtonStyle(color=ft.Colors.WHITE)),
        ],
        bgcolor=ft.Colors.BLUE_GREY_800
    )

    # Rutinas
    def ejecutar_rutina(e):
        if not rutina.value:
            return
        rutina_seleccionada = rutina.value
        rutina.disabled = True
        btn_ejecutar.disabled = True
        set_estado_visual(f"Ejecutando {rutina_seleccionada}...", ft.Colors.GREEN_300)

        def run():
            try:
                getattr(controlador, f"rutina_{rutina_seleccionada[-1]}")()
            except Exception:
                error_box.value = "Error ejecutando rutina:\n" + traceback.format_exc()
                set_estado_visual("Error en rutina", ft.Colors.RED_300)
            else:
                set_estado_visual("Estado: En espera", ft.Colors.with_opacity(0.08, ft.Colors.GREY_100))
            finally:
                rutina.disabled = False
                btn_ejecutar.disabled = False
                page.update()

        threading.Thread(target=run, daemon=True).start()

    def on_dropdown_change(e):
        btn_ejecutar.disabled = not bool(rutina.value)
        page.update()

    rutina = ft.Dropdown(
        options=[ft.dropdown.Option(f"Rutina {i}") for i in range(1, 4)],
        width=220,
        hint_text="Selecciona una rutina",
        on_change=on_dropdown_change,
        text_style=ft.TextStyle(color=ft.Colors.WHITE),
        hint_style=ft.TextStyle(color=ft.Colors.GREY_400)
    )

    btn_ejecutar = ft.FilledButton(
        text="🚀 Ejecutar Rutina",
        on_click=ejecutar_rutina,
        bgcolor=ft.Colors.INDIGO,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
        disabled=True
    )

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
            width=180,
        )

    def abrir_menu(e):
        page.drawer.open = True
        page.update()

    usuarios_section = ft.Column(
        [
            ft.Text("Usuarios", size=14, color=ft.Colors.GREY_300),
            ft.OutlinedButton("Usuarios", icon=ft.Icons.PERSON, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
            ft.OutlinedButton("Pacientes", icon=ft.Icons.PEOPLE, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
        ],
        spacing=10,
    )

    sensores_section = ft.Column(
        [
            ft.Text("Control de sensores", size=14, color=ft.Colors.GREY_300),
            crear_boton("Start Sensor", ft.Icons.PLAY_ARROW, ft.Colors.GREEN_400),
            crear_boton("Stop Sensor", ft.Icons.STOP, ft.Colors.RED_400),
            crear_boton("Reset Sensor", ft.Icons.REFRESH, ft.Colors.AMBER_400),
        ],
        spacing=10,
    )

    menu_column = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(icon=ft.Icons.MENU, on_click=abrir_menu, icon_color=ft.Colors.WHITE),
                            ft.Text("Panel Principal", size=16, weight="bold", color=ft.Colors.WHITE),
                        ]
                    ),
                    ft.Divider(color=ft.Colors.WHITE),
                    usuarios_section,
                    ft.Divider(color=ft.Colors.WHITE),
                    sensores_section,
                    ft.Divider(color=ft.Colors.WHITE),
                    btn_ejecutar,
                ],
                spacing=10,
            ),
            padding=15,
        ),
        elevation=2,
        color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    side_column = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Container(content=ft.Image(src="arm.png", width=160), alignment=ft.alignment.center),
                    rutina,
                    estado_container,
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=15,
        ),
        elevation=2,
        color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    layout = ft.Row(
        [menu_column, side_column],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        expand=True
    )
    page.add(layout)

if __name__ == "__main__":
    # Busca un puerto disponible en la IP específica de la Pi
    port = _find_free_port(HOST, START_PORT)

    print("\n[Flet] Iniciando servidor web…")
    print(f" - Host/IP: {HOST}")
    print(f" - Puerto : {port}")
    print(f" - Abre en tu laptop:  http://{HOST}:{port}")

    # Nota: view=None evita que la Raspberry abra su propio navegador.
    view_mode = ft.WEB_BROWSER if OPEN_BROWSER_ON_SERVER else None

    # Si quisieras abrir un navegador local en la Pi (no recomendado aquí):
    if OPEN_BROWSER_ON_SERVER:
        try:
            webbrowser.open(f"http://{HOST}:{port}")
        except Exception:
            pass

    ft.app(
        target=window_main,
        assets_dir=ASSETS_DIR,
        view=view_mode,
        host=HOST,
        port=port,
    )
