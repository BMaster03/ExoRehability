# main_window.py
from __future__ import annotations
import threading
import socket
import traceback
from dataclasses import dataclass
from typing import List
import flet as ft
import webbrowser

# ======== Config ========
LAN_IP = "169.254.69.170"   # IP fija de tu Raspberry Pi
HOST = LAN_IP               # el servidor escuchará solo en esta IP
START_PORT = 5000           # puerto preferido
ASSETS_DIR = "assets"       # assets/arm.png, assets/fonts/Poppins-Regular.ttf
OPEN_BROWSER_ON_SERVER = False
# ========================

def _find_free_port(host: str, start_port: int, tries: int = 50) -> int:
    for p in range(start_port, start_port + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.15)
            if s.connect_ex((host, p)) != 0:
                return p
    raise RuntimeError("No hay puertos libres en el rango solicitado.")

# -----------------------------------------------------------------------------
# Usuarios (datos + hoja deslizable)
# -----------------------------------------------------------------------------
@dataclass
class User:
    user_id: str
    nombre: str
    correo: str = ""
    telefono: str = ""
    notas: str = ""

def sample_users() -> List[User]:
    return [
        User("U-001", "Bryan",   "bryan@example.com",   "+52 55 0000 0001", "Paciente demo."),
        User("U-002", "Joje",    "joje@example.com",    "+52 55 0000 0002", "Estudio EMG."),
        User("U-003", "Yansito", "yansito@example.com", "+52 55 0000 0003", "Sesiones 3/12."),
        User("U-004", "Mar",     "mar@example.com",     "+52 55 0000 0004", "Notas adicionales."),
    ]

def open_users_sheet(page: ft.Page, users: List[User] | None = None):
    """Hoja deslizable con lista de usuarios (izq) y detalle (der)."""
    data = users or sample_users()

    # ----------------- Panel de detalle (derecha) -----------------
    detail_title = ft.Text("Selecciona un usuario", size=18, weight=ft.FontWeight.BOLD)
    detail_col = ft.Column(
        [
            detail_title,
            ft.Divider(),
            ft.Text("—", selectable=True),
        ],
        spacing=8,
        expand=True,
    )
    detail_container = ft.Container(
        content=detail_col,
        padding=12,
        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
        border_radius=8,
        expand=True,
    )

    def show_detail(u: User):
        detail_col.controls.clear()
        detail_col.controls.extend(
            [
                ft.Text(f"Usuario: {u.nombre}", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([ft.Text("ID:", weight=ft.FontWeight.BOLD), ft.Text(u.user_id)]),
                ft.Row([ft.Text("Correo:", weight=ft.FontWeight.BOLD), ft.Text(u.correo or "—")]),
                ft.Row([ft.Text("Teléfono:", weight=ft.FontWeight.BOLD), ft.Text(u.telefono or "—")]),
                ft.Text("Notas:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(u.notas or "—", selectable=True),
                    padding=ft.Padding(8, 6, 8, 6),
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                    border_radius=8,
                    expand=False,
                ),
            ]
        )
        detail_title.value = f"{u.nombre}"
        page.update()

    # ----------------- Lista estilo "menu" (izquierda) -----------------
    list_panel = ft.ListView(spacing=2, expand=True, auto_scroll=False)
    items_state = []  # para manejar selección visual

    def recolor(item_container: ft.Container, selected: bool, hover: bool):
        if selected:
            item_container.bgcolor = ft.Colors.with_opacity(0.45, ft.Colors.PURPLE_200)
        else:
            item_container.bgcolor = (
                ft.Colors.with_opacity(0.18, ft.Colors.WHITE)
                if hover else ft.Colors.with_opacity(0.08, ft.Colors.WHITE)
            )

    def on_click_factory(item):
        def _clk(e):
            for st in items_state:
                st["selected"] = False
                recolor(st["ctrl"], selected=False, hover=False)
            item["selected"] = True
            recolor(item["ctrl"], selected=True, hover=False)
            show_detail(item["user"])
            page.update()
        return _clk

    def on_hover_factory(item):
        def _hv(e: ft.HoverEvent):
            if not item["selected"]:
                recolor(item["ctrl"], selected=False, hover=(e.data == "true"))
                page.update()
        return _hv

    # encabezado de la lista
    header = ft.Container(
        content=ft.Row(
            [ft.Text("Usuarios", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(10, 8, 10, 8),
        bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
    )
    list_panel.controls.append(header)

    # campo búsqueda
    search = ft.TextField(
        hint_text="Buscar…",
        prefix_icon=ft.Icons.SEARCH,
        width=260,
        on_change=lambda e: apply_filter(),
    )
    list_panel.controls.append(ft.Container(content=search, padding=ft.Padding(8, 8, 8, 4)))

    # ítems
    def build_item(u: User):
        name = ft.Text(u.nombre, color=ft.Colors.WHITE, size=13)
        cont = ft.Container(
            content=ft.Row([name], alignment=ft.MainAxisAlignment.START),
            padding=ft.Padding(12, 8, 12, 8),
            border_radius=4,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            ink=True,
        )
        state = {"ctrl": cont, "user": u, "selected": False}
        cont.on_click = on_click_factory(state)
        cont.on_hover = on_hover_factory(state)
        items_state.append(state)
        return cont

    items_controls = [build_item(u) for u in data]
    list_panel.controls.extend(items_controls)

    def apply_filter():
        term = (search.value or "").strip().lower()
        # preserva header y búsqueda, limpia el resto
        list_panel.controls = list_panel.controls[:2]
        for st in items_state:
            u = st["user"]
            if (not term) or (term in u.nombre.lower()) or (term in u.user_id.lower()):
                list_panel.controls.append(st["ctrl"])
        page.update()

    # ----------------- BottomSheet -----------------
    sheet_content = ft.Container(
        content=ft.Row(
            [
                ft.Container(list_panel, width=300, padding=8),
                detail_container,
            ],
            spacing=12,
        ),
        padding=12,
        width=860,
        bgcolor=ft.Colors.BLUE_GREY_900,
    )

    bs = ft.BottomSheet(
        content=sheet_content,
        open=True,
        show_drag_handle=True,
        is_scroll_controlled=True,
        on_dismiss=lambda e: None,
    )
    # agregar a overlay y abrir
    page.overlay.append(bs)
    bs.open = True
    page.update()

# -----------------------------------------------------------------------------
# UI principal
# -----------------------------------------------------------------------------
def window_main(page: ft.Page):
    # ===== Page / Tema =====
    page.title = "Exo-arm-1"
    page.bgcolor = ft.Colors.BLUE_GREY_900
    page.window.resizable = False
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 6  # bordes casi pegados
    page.fonts = {"Poppins": "fonts/Poppins-Regular.ttf"}
    page.theme = ft.Theme(font_family="Poppins")

    # ===== Estado + Bitácora =====
    estado_text = ft.Text(value="Todos los actuadores en reposo.", size=14, color=ft.Colors.GREY_200)
    error_box = ft.Text(value="", size=12, color=ft.Colors.RED_300, selectable=True)
    log_list = ft.ListView(expand=1, spacing=4, auto_scroll=True)

    def push_log(txt: str, color=ft.Colors.GREY_300):
        log_list.controls.append(ft.Text(txt, size=12, color=color))
        page.update()

    estado_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    estado_text,
                    ft.Divider(color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                    ft.Text("Bitácora", size=12, color=ft.Colors.GREY_400),
                    log_list,
                    error_box,
                ],
                spacing=8,
                expand=True,
            ),
            padding=8,
            width=360,
            height=260,
        ),
        elevation=2,
        color=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    def set_estado_visual(texto: str, color):
        estado_text.value = texto
        estado_card.bgcolor = color
        page.update()

    def actualizar_estado(texto: str):
        estado_text.value = texto
        push_log(texto)

    # ===== Backend actuadores =====
    try:
        from Laptop_client.GUI.routines import ControlActuadores
    except Exception:
        tb = traceback.format_exc()
        error_box.value = "Error al importar módulos:\n" + tb
        set_estado_visual("Error al iniciar (imports).", ft.Colors.RED_300)
        page.add(ft.Container(content=ft.Text("Revisa el error mostrado y corrige dependencias/rutas.",
                                              color=ft.Colors.RED_100), padding=10))
        page.update()
        return
    controlador = ControlActuadores(actualizar_estado=actualizar_estado)

    # ===== AppBar + Drawer =====
    def abrir_menu(e=None):
        page.drawer.open = True
        page.update()

    page.appbar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.MENU, on_click=abrir_menu, icon_color=ft.Colors.WHITE),
        title=ft.Text("", size=1),
        center_title=False,
        bgcolor=ft.Colors.TRANSPARENT,
        elevation=0,
        toolbar_height=40,
    )

    def mostrar_datos_anteriores(e):
        push_log("Abrir 'Datos anteriores' (pendiente).")

    def abrir_datos_actuales(e):
        push_log("Abriendo 'Datos actuales'…")

    page.drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(ft.Text("⚙️ Opciones", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), padding=10),
            ft.TextButton("📁 Datos anteriores", on_click=mostrar_datos_anteriores, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
            ft.TextButton("📈 Datos actuales", on_click=abrir_datos_actuales, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
        ],
        bgcolor=ft.Colors.BLUE_GREY_800
    )

    # ===== Rutinas (izquierda) =====
    rutina = ft.Dropdown(
        options=[ft.dropdown.Option(f"Rutina {i}") for i in range(1, 4)],
        width=220,
        hint_text="Selecciona una rutina",
        on_change=lambda e: (setattr(btn_ejecutar, "disabled", not bool(rutina.value)), page.update()),
        text_style=ft.TextStyle(color=ft.Colors.WHITE),
        hint_style=ft.TextStyle(color=ft.Colors.GREY_400),
    )

    def ejecutar_rutina(e):
        if not rutina.value:
            return
        rutina_sel = rutina.value
        rutina.disabled = True
        btn_ejecutar.disabled = True
        set_estado_visual(f"Ejecutando {rutina_sel}...", ft.Colors.with_opacity(0.08, ft.Colors.GREEN_200))
        push_log(f"→ {rutina_sel} iniciada", ft.Colors.GREEN_200)

        def run():
            try:
                getattr(controlador, f"rutina_{rutina_sel[-1]}")()
            except Exception:
                tb = traceback.format_exc()
                error_box.value = "Error ejecutando rutina:\n" + tb
                push_log("✖ Error en rutina", ft.Colors.RED_200)
                set_estado_visual("Error en rutina", ft.Colors.RED_300)
            else:
                set_estado_visual("Todos los actuadores en reposo.", ft.Colors.with_opacity(0.08, ft.Colors.GREY_100))
                push_log(f"✓ {rutina_sel} completada", ft.Colors.GREEN_200)
            finally:
                rutina.disabled = False
                btn_ejecutar.disabled = False
                page.update()

        threading.Thread(target=run, daemon=True).start()

    btn_ejecutar = ft.FilledButton(
        text="🚀 Ejecutar Rutina",
        on_click=ejecutar_rutina,
        bgcolor=ft.Colors.INDIGO,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
        disabled=True
    )

    rutinas_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [ft.Text("Rutinas", size=14, color=ft.Colors.GREY_300), rutina, btn_ejecutar],
                spacing=10,
            ),
            padding=8,
            width=360,
        ),
        elevation=2,
        color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    # ===== Control manual por dedo (izquierda) =====
    def control_row(nombre: str, num: int):
        dur_field = ft.TextField(
            value="1.0",
            width=66,
            text_align=ft.TextAlign.RIGHT,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9\.]", replacement_string=""),
            label="s",
            label_style=ft.TextStyle(color=ft.Colors.GREY_500),
        )

        def do_pulse(sentido: str):
            try:
                t = float(dur_field.value or "0")
                if t <= 0:
                    push_log("Duración debe ser > 0", ft.Colors.AMBER_200)
                    return
            except ValueError:
                push_log("Duración inválida", ft.Colors.AMBER_200)
                return

            push_log(f"[{nombre}] {sentido.upper()} {t:.2f}s", ft.Colors.BLUE_200)

            def run():
                try:
                    if sentido == "open":
                        controlador.mover_actuador(num, t, 0, 0, sentido_inicio="open")
                    else:
                        controlador.mover_actuador(num, t, 0, 0, sentido_inicio="close")
                except Exception:
                    error_box.value = "Error en control manual:\n" + traceback.format_exc()
                    push_log("✖ Error en control manual", ft.Colors.RED_200)
                    page.update()

            threading.Thread(target=run, daemon=True).start()

        return ft.Row(
            [
                ft.Text(nombre, width=80, color=ft.Colors.GREY_200),
                ft.FilledButton("Open", icon=ft.Icons.ARROW_UPWARD, on_click=lambda e: do_pulse("open"),
                                bgcolor=ft.Colors.GREEN_400, color=ft.Colors.WHITE),
                ft.FilledButton("Close", icon=ft.Icons.ARROW_DOWNWARD, on_click=lambda e: do_pulse("close"),
                                bgcolor=ft.Colors.RED_400, color=ft.Colors.WHITE),
                dur_field,
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    manual_panel = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Control manual de dedos", size=14, color=ft.Colors.GREY_300),
                            ft.FilledButton(
                                "🏠 HOME",
                                on_click=lambda e: (
                                    threading.Thread(target=controlador.posicion_reposo, daemon=True).start(),
                                    push_log("HOME: todos OFF", ft.Colors.BLUE_200)
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color=ft.Colors.WHITE),
                    control_row("Pulgar", 1),
                    control_row("Índice", 2),
                    control_row("Medio", 3),
                    control_row("Anular", 4),
                    control_row("Meñique", 5),
                ],
                spacing=10,
            ),
            padding=8,
            width=360,
        ),
        elevation=2,
        color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    # ===== Usuarios (izquierda) =====
    usuarios_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Usuarios", size=14, color=ft.Colors.GREY_300),
                    ft.OutlinedButton(
                        "Usuarios",
                        icon=ft.Icons.PERSON,
                        style=ft.ButtonStyle(color=ft.Colors.WHITE),
                        on_click=lambda e: open_users_sheet(page),
                    ),
                    ft.OutlinedButton("Pacientes", icon=ft.Icons.PEOPLE, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                ],
                spacing=10,
            ),
            padding=8,
            width=360,
        ),
        elevation=2,
        color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    # ===== Sensores (derecha-superior) =====
    def crear_boton(texto, icono, color, on_click=None):
        return ft.FilledButton(
            text=texto,
            icon=icono,
            bgcolor=color,
            color=ft.Colors.WHITE,
            on_click=on_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=18),
                padding=ft.Padding(12, 10, 12, 10),
            ),
            height=44,
            width=180,
        )

    def start_sensor(e):
        push_log("Sensor: START", ft.Colors.GREEN_200)

    def stop_sensor(e):
        push_log("Sensor: STOP (placeholder)", ft.Colors.AMBER_200)

    def reset_sensor(e):
        push_log("Sensor: RESET (placeholder)", ft.Colors.AMBER_200)

    sensores_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Control de sensores", size=14, color=ft.Colors.GREY_300),
                    ft.Divider(color=ft.Colors.WHITE),
                    crear_boton("Start Sensor", ft.Icons.PLAY_ARROW, ft.Colors.GREEN_400, start_sensor),
                    crear_boton("Stop Sensor", ft.Icons.STOP, ft.Colors.RED_400, stop_sensor),
                    crear_boton("Reset Sensor", ft.Icons.REFRESH, ft.Colors.AMBER_400, reset_sensor),
                ],
                spacing=10,
            ),
            padding=8,
            width=360,
        ),
        elevation=2,
        color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    # ===== Layout pegado a bordes =====
    left_stack = ft.Column([usuarios_card, rutinas_card, manual_panel], spacing=10)
    left_container = ft.Container(content=left_stack, padding=0, alignment=ft.alignment.top_left, width=372)

    right_stack = ft.Column([sensores_card, estado_card], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.END)
    right_container = ft.Container(content=right_stack, padding=0, alignment=ft.alignment.top_right, width=372)

    layout = ft.Row(
        [left_container, right_container],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
        spacing=0,
        expand=True,
    )
    page.add(layout)

    # Limpieza segura al desconectar
    def _cleanup(*_):
        try:
            controlador.posicion_reposo()
        except Exception:
            pass
        push_log("Conexión cerrada: HOME aplicado.", ft.Colors.AMBER_200)

    page.on_disconnect = _cleanup

# -----------------------------------------------------------------------------
# Lanzador
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = _find_free_port(HOST, START_PORT)

    print("\n[Flet] Iniciando servidor web…")
    print(f" - Host/IP: {HOST}")
    print(f" - Puerto : {port}")
    print(f" - Abre en tu laptop:  http://{HOST}:{port}")

    view_mode = ft.WEB_BROWSER if OPEN_BROWSER_ON_SERVER else None
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
