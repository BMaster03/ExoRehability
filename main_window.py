# main_window.py
from __future__ import annotations
import threading
import time
import socket
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import flet as ft
from flet import canvas as cv
import webbrowser

# ================= CONFIG (Raspberry Pi 5) =================
HOST = "169.254.69.170"   # IP fija de la Pi
START_PORT = 5000
ASSETS_DIR = "assets"
OPEN_BROWSER_ON_SERVER = True
# ===========================================================

def _find_free_port(host: str, start_port: int, tries: int = 50) -> int:
    for p in range(start_port, start_port + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.15)
            if s.connect_ex((host, p)) != 0:
                return p
    raise RuntimeError("No hay puertos libres en el rango solicitado.")

# ---------------------- Datos usuarios/pacientes -----------------------------
@dataclass
class User:
    user_id: str
    nombre: str
    correo: str = ""
    telefono: str = ""
    notas: str = ""

@dataclass
class Patient:
    patient_id: str
    nombre: str
    edad: int = 0
    diagnostico: str = ""
    notas: str = ""

def sample_users() -> List[User]:
    return [
        User("U-001", "Bryan",   "bryan@example.com",   "+52 55 0000 0001", "Doctor"),
        User("U-003", "Yansito", "yansito@example.com", "+52 55 0000 0003", "Terapeuta junior"),
        User("U-004", "Max",     "max@example.com",     "+52 55 0000 0004", "Terapeuta senior"),
    ]

def sample_patients_by_user() -> Dict[str, List[Patient]]:
    return {
        "U-001": [
            Patient("P-101", "Yaneth",   28, "Lesión muñeca y ligamento", "Protocolo A."),
            Patient("P-102", "Angélica", 32, "Túnel carpiano", "Protocolo B."),
            Patient("P-103", "Nain",     25, "Rehab post-quirúrgica", "Protocolo C."),
        ],
        "U-003": [
            Patient("P-201", "Bachi", 40, "Dolor crónico mano", "Sesiones 2/10."),
            Patient("P-202", "Sara",  35, "Lesión de ligamentos", "Sesiones 5/12."),
        ],
        "U-004": [],
    }

# ---------------------- BottomSheets usuarios/pacientes ----------------------
def open_users_sheet(page: ft.Page, on_user_selected: Callable[[User], None]):
    data = sample_users()

    detail_title = ft.Text("Selecciona un usuario", size=18, weight=ft.FontWeight.BOLD)
    detail_col = ft.Column([detail_title, ft.Divider(), ft.Text("—", selectable=True)], spacing=8, expand=True)
    detail_container = ft.Container(
        content=detail_col, padding=12,
        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
        border_radius=8, expand=True
    )

    def show_detail(u: User):
        detail_col.controls = [
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
            ),
        ]
        detail_title.value = f"{u.nombre}"; page.update()

    list_panel = ft.ListView(spacing=2, expand=True, auto_scroll=False)
    items_state = []

    def recolor(container: ft.Container, selected: bool, hover: bool):
        if selected:
            container.bgcolor = ft.Colors.with_opacity(0.45, ft.Colors.PURPLE_200)
        else:
            container.bgcolor = ft.Colors.with_opacity(0.18, ft.Colors.WHITE) if hover else ft.Colors.with_opacity(0.08, ft.Colors.WHITE)

    def on_click_factory(item):
        def _clk(e):
            for st in items_state:
                st["selected"] = False
                recolor(st["ctrl"], False, False)
            item["selected"] = True
            recolor(item["ctrl"], True, False)
            on_user_selected(item["user"])
            show_detail(item["user"])
        return _clk

    def on_hover_factory(item):
        def _hv(e: ft.HoverEvent):
            if not item["selected"]:
                recolor(item["ctrl"], False, (e.data == "true")); page.update()
        return _hv

    header = ft.Container(
        content=ft.Row([ft.Text("Usuarios", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)]),
        padding=ft.Padding(10, 8, 10, 8),
        bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
    )
    list_panel.controls.append(header)

    search = ft.TextField(hint_text="Buscar…", prefix_icon=ft.Icons.SEARCH, width=260,
                          on_change=lambda e: apply_filter())
    list_panel.controls.append(ft.Container(content=search, padding=ft.Padding(8, 8, 8, 4)))

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

    list_panel.controls.extend([build_item(u) for u in data])

    def apply_filter():
        term = (search.value or "").strip().lower()
        list_panel.controls = list_panel.controls[:2]
        for st in items_state:
            u = st["user"]
            if (not term) or (term in u.nombre.lower()) or (term in u.user_id.lower()):
                list_panel.controls.append(st["ctrl"])
        page.update()

    sheet_content = ft.Container(
        content=ft.Row([ft.Container(list_panel, width=300, padding=8), detail_container], spacing=12),
        padding=12, width=860, bgcolor=ft.Colors.BLUE_GREY_900
    )
    bs = ft.BottomSheet(content=sheet_content, open=True, show_drag_handle=True, is_scroll_controlled=True)
    page.overlay.append(bs); bs.open = True; page.update()

def open_patients_sheet(page: ft.Page, selected_user: Optional[User], on_patient_selected: Callable[[Patient], None]):
    if not selected_user:
        page.snack_bar = ft.SnackBar(ft.Text("Selecciona un usuario primero."), bgcolor=ft.Colors.RED_700)
        page.snack_bar.open = True; page.update(); return

    mapping = sample_patients_by_user()
    patients = mapping.get(selected_user.user_id, [])

    detail_title = ft.Text("Selecciona un paciente", size=18, weight=ft.FontWeight.BOLD)
    detail_col = ft.Column([detail_title, ft.Divider(), ft.Text("—", selectable=True)], spacing=8, expand=True)
    detail_container = ft.Container(
        content=detail_col, padding=12,
        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
        border_radius=8, expand=True
    )

    def show_detail(p: Patient):
        detail_col.controls = [
            ft.Text(f"Paciente: {p.nombre}", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([ft.Text("ID:", weight=ft.FontWeight.BOLD), ft.Text(p.patient_id)]),
            ft.Row([ft.Text("Edad:", weight=ft.FontWeight.BOLD), ft.Text(str(p.edad))]),
            ft.Row([ft.Text("Diagnóstico:", weight=ft.FontWeight.BOLD), ft.Text(p.diagnostico or "—")]),
            ft.Text("Notas:", weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(p.notas or "—", selectable=True),
                padding=ft.Padding(8, 6, 8, 6),
                bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                border_radius=8,
            ),
        ]
        detail_title.value = f"{p.nombre}"; page.update()

    list_panel = ft.ListView(spacing=2, expand=True, auto_scroll=False)
    items_state = []

    def recolor(container: ft.Container, selected: bool, hover: bool):
        if selected:
            container.bgcolor = ft.Colors.with_opacity(0.45, ft.Colors.CYAN_200)
        else:
            container.bgcolor = ft.Colors.with_opacity(0.18, ft.Colors.WHITE) if hover else ft.Colors.with_opacity(0.08, ft.Colors.WHITE)

    def on_click_factory(item):
        def _clk(e):
            for st in items_state:
                st["selected"] = False
                recolor(st["ctrl"], False, False)
            item["selected"] = True
            recolor(item["ctrl"], True, False)
            on_patient_selected(item["patient"])
            show_detail(item["patient"])
        return _clk

    def on_hover_factory(item):
        def _hv(e: ft.HoverEvent):
            if not item["selected"]:
                recolor(item["ctrl"], False, (e.data == "true")); page.update()
        return _hv

    header = ft.Container(
        content=ft.Row([ft.Text(f"Pacientes de {selected_user.nombre}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)]),
        padding=ft.Padding(10, 8, 10, 8), bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
    )
    list_panel.controls.append(header)

    search = ft.TextField(hint_text="Buscar paciente…", prefix_icon=ft.Icons.SEARCH, width=260,
                          on_change=lambda e: apply_filter())
    list_panel.controls.append(ft.Container(content=search, padding=ft.Padding(8, 8, 8, 4)))

    def build_item(p: Patient):
        name = ft.Text(p.nombre, color=ft.Colors.WHITE, size=13)
        cont = ft.Container(
            content=ft.Row([name], alignment=ft.MainAxisAlignment.START),
            padding=ft.Padding(12, 8, 12, 8), border_radius=4,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE), ink=True,
        )
        state = {"ctrl": cont, "patient": p, "selected": False}
        cont.on_click = on_click_factory(state); cont.on_hover = on_hover_factory(state)
        items_state.append(state); return cont

    list_panel.controls.extend([build_item(p) for p in patients])

    def apply_filter():
        term = (search.value or "").strip().lower()
        list_panel.controls = list_panel.controls[:2]
        for st in items_state:
            p = st["patient"]
            if (not term) or (term in p.nombre.lower()) or (term in p.patient_id.lower()):
                list_panel.controls.append(st["ctrl"])
        page.update()

    sheet_content = ft.Container(
        content=ft.Row([ft.Container(list_panel, width=300, padding=8), detail_container], spacing=12),
        padding=12, width=860, bgcolor=ft.Colors.BLUE_GREY_900
    )
    bs = ft.BottomSheet(content=sheet_content, open=True, show_drag_handle=True, is_scroll_controlled=True)
    page.overlay.append(bs); bs.open = True; page.update()

# ---------------------- Osciloscopio con flet.canvas ------------------------
class Scope:
    def __init__(self, title: str, width=950, height=280, y_range_mV=6.0):
        self.w, self.h = width, height
        self.y_range = y_range_mV
        self.title_lbl = ft.Text(title, weight=ft.FontWeight.BOLD)
        self.canvas = cv.Canvas(width=self.w, height=self.h)
        self.container = ft.Column(
            [self.title_lbl,
             ft.Container(self.canvas, border_radius=12,
                          bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE), padding=6)],
            spacing=6, expand=True)
        self._draw_frame()

    def _draw_frame(self):
        shapes: list = [
            cv.Rect(0, 0, self.w, self.h, paint=ft.Paint(color=ft.Colors.BLUE_GREY_800,
                                                         style=ft.PaintingStyle.FILL))
        ]
        grid_color = ft.Colors.with_opacity(0.25, ft.Colors.GREY_400)
        for i in range(0, 11):
            x = int(i * (self.w-2) / 10) + 1
            shapes.append(cv.Line(x, 1, x, self.h-1, paint=ft.Paint(color=grid_color, stroke_width=1)))
        for j in range(0, 9):
            y = int(j * (self.h-2) / 8) + 1
            shapes.append(cv.Line(1, y, self.w-1, y, paint=ft.Paint(color=grid_color, stroke_width=1)))
        baseline_y = self._map_y(0.0)
        shapes.append(cv.Line(1, baseline_y, self.w-1, baseline_y,
                              paint=ft.Paint(color=ft.Colors.AMBER, stroke_width=1)))
        self.canvas.shapes = shapes

    def _map_y(self, mV: float) -> float:
        half = self.y_range / 2.0
        mV_clamped = max(-half, min(half, mV))
        norm = (mV_clamped + half) / (self.y_range)   # 0..1
        return (1 - norm) * (self.h-2) + 1

    def update_wave(self, t: list[float], y: list[float], color=ft.Colors.AMBER_200):
        self._draw_frame()
        if len(t) < 2 or len(y) < 2:
            return
        path = cv.Path()
        n = len(y)
        def x_at(i: int) -> float:
            return 1 + i * (self.w-2) / (n-1)
        path.move_to(x_at(0), self._map_y(y[0]))
        for i in range(1, n):
            path.line_to(x_at(i), self._map_y(y[i]))
        self.canvas.shapes.append(cv.Stroke(path=path,
                                   paint=ft.Paint(color=color, stroke_width=1.6)))
        baseline = self._map_y(0.0)
        fill_path = cv.Path()
        fill_path.move_to(x_at(0), baseline)
        for i in range(0, n):
            fill_path.line_to(x_at(i), self._map_y(y[i]))
        fill_path.line_to(x_at(n-1), baseline)
        fill_path.close()
        self.canvas.shapes.append(cv.Fill(path=fill_path,
                                   paint=ft.Paint(color=ft.Colors.with_opacity(0.18, ft.Colors.AMBER))))

# Motor de datos en tiempo real (simulación sencilla si no importas tu EMG)
class EMGEngine:
    def __init__(self, page: ft.Page, scope1: Scope, scope2: Scope | None,
                 seconds_window=5.0, fs=300):
        self.page = page
        self.scope1, self.scope2 = scope1, scope2
        self.fs = fs
        self.window = seconds_window
        self.max_pts = int(self.fs * self.window)
        self.t: list[float] = []
        self.y1: list[float] = []
        self.y2: list[float] = []
        self._stop = threading.Event()
        self._running = False
        self._t0 = 0.0

    def start(self):
        if self._running:
            return
        self._stop.clear()
        threading.Thread(target=self._loop, daemon=True).start()
        self._running = True

    def stop(self):
        if not self._running:
            return
        self._stop.set()
        self._running = False

    def reset(self):
        self.t.clear(); self.y1.clear(); self.y2.clear()
        self._render()

    def _loop(self):
        block = max(3, int(self.fs * 0.03))  # ~30 ms
        t0 = self.t[-1] if self.t else 0.0
        import math, random
        while not self._stop.is_set():
            # Fallback de EMG simple
            dt = 1.0 / self.fs
            ch1, ch2 = [], []
            for i in range(block):
                tt = self._t0 + (i+1)*dt
                val = 0.8 * math.sin(2*math.pi*5*tt) + 0.25*random.random()
                ch1.append(val); ch2.append(val * 0.6)
            self._t0 += block * dt

            x = [t0 + (i+1)*dt for i in range(block)]
            t0 = x[-1]
            self.t.extend(x); self.y1.extend(ch1)
            if self.scope2 is not None:
                self.y2.extend(ch2)
            if len(self.t) > self.max_pts:
                extra = len(self.t) - self.max_pts
                self.t = self.t[extra:]; self.y1 = self.y1[extra:]
                if self.scope2 is not None:
                    self.y2 = self.y2[extra:]
            self._render()
            time.sleep(0.03)

    def _render(self):
        self.scope1.update_wave(self.t, self.y1, color=ft.Colors.AMBER_200)
        if self.scope2 is not None:
            self.scope2.update_wave(self.t, self.y2, color=ft.Colors.CYAN_200)
        self.page.update()

# ---------------------- UI principal ----------------------------------------
def window_main(page: ft.Page):
    page.title = "Exo-arm-1"
    page.bgcolor = ft.Colors.BLUE_GREY_900
    page.window.resizable = False
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 6
    page.fonts = {"Poppins": "fonts/Poppins-Regular.ttf"}
    page.theme = ft.Theme(font_family="Poppins")

    # Bitácora / estado
    log_list = ft.ListView(expand=1, spacing=4, auto_scroll=True)
    def push_log(txt: str, color=ft.Colors.GREY_300):
        log_list.controls.append(ft.Text(txt, size=12, color=color)); page.update()

    estado_title = ft.Text("Inicializando…", size=14, color=ft.Colors.GREY_200)

    estado_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [estado_title,
                 ft.Divider(color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                 ft.Text("Bitácora", size=12, color=ft.Colors.GREY_400),
                 log_list],
                spacing=8, expand=True),
            padding=8, width=360, height=260),
        elevation=2, color=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    page.appbar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.MENU, on_click=lambda e: None, icon_color=ft.Colors.WHITE),
        title=ft.Text("", size=1), center_title=False,
        bgcolor=ft.Colors.TRANSPARENT, elevation=0, toolbar_height=40,
    )

    # ===== Controlador GPIO a través de routines.py =====
    def actualizar_estado(msg: str):
        push_log(msg, ft.Colors.GREY_300)

    try:
        from Laptop_client.GUI.routines import ControlActuadores
        controlador = ControlActuadores(actualizar_estado=actualizar_estado)
        estado_title.value = "GPIO listo (LGPIO) o SIM según entorno."
    except Exception as ex:
        # Respaldo mínimo si hubiera error importando routines.py
        class ControlActuadores:
            def __init__(self, actualizar_estado=None):
                self.actualizar_estado = actualizar_estado
                if actualizar_estado: actualizar_estado(f"SIM: controlador (sin GPIO). Motivo: {ex}")
            def home_now(self, s=3.0): 
                if self.actualizar_estado: self.actualizar_estado(f"SIM: home_now({s})")
            def stop_and_home(self, stop_event=None, close_seconds=3.0):
                if stop_event: stop_event.set()
                if self.actualizar_estado: self.actualizar_estado("SIM: stop_and_home()")
            def mover_actuador(self, *a, **k):
                if self.actualizar_estado: self.actualizar_estado(f"SIM: mover_actuador{a}{k}")
            def run_routine(self, name, cycles=1, stop_event=None):
                if self.actualizar_estado: self.actualizar_estado(f"SIM: run_routine({name}, cycles={cycles})")
        controlador = ControlActuadores(actualizar_estado=actualizar_estado)
        estado_title.value = "SIM sin GPIO"

    # ===== Estado de selección (Usuarios/Pacientes) =====
    selected_user: Optional[User] = None

    usuarios_btn = ft.OutlinedButton("Usuarios", icon=ft.Icons.PERSON,
                                     style=ft.ButtonStyle(color=ft.Colors.WHITE),
                                     on_click=lambda e: open_users_sheet(page, on_user_selected))
    pacientes_btn = ft.OutlinedButton("Pacientes", icon=ft.Icons.PEOPLE,
                                      style=ft.ButtonStyle(color=ft.Colors.WHITE),
                                      on_click=lambda e: open_patients_sheet(page, selected_user, on_patient_selected))

    def on_user_selected(u: User):
        nonlocal selected_user
        selected_user = u
        usuarios_btn.text = u.nombre
        pacientes_btn.text = "Pacientes"
        page.snack_bar = ft.SnackBar(ft.Text(f"Usuario seleccionado: {u.nombre}"), bgcolor=ft.Colors.GREEN_700)
        page.snack_bar.open = True; page.update()

    def on_patient_selected(p: Patient):
        pacientes_btn.text = f"Paciente/{p.nombre}"
        page.snack_bar = ft.SnackBar(ft.Text(f"Paciente seleccionado: {p.nombre}"), bgcolor=ft.Colors.CYAN_700)
        page.snack_bar.open = True; page.update()

    usuarios_card = ft.Card(
        content=ft.Container(
            content=ft.Column([ft.Text("Usuarios / Pacientes", size=14, color=ft.Colors.GREY_300),
                               usuarios_btn, pacientes_btn], spacing=10),
            padding=8, width=360),
        elevation=2, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    # ===== RUTINAS (con ciclos + PARO) =====
    stop_event = threading.Event()

    rutina_dd = ft.Dropdown(
        options=[
            ft.dropdown.Option("Rutina 1"),
            ft.dropdown.Option("Rutina 2"),
            ft.dropdown.Option("Rutina 3"),
        ],
        value="Rutina 1",
        width=220, hint_text="Elige rutina",
        text_style=ft.TextStyle(color=ft.Colors.WHITE),
        hint_style=ft.TextStyle(color=ft.Colors.GREY_400),
    )

    ciclos_tf = ft.TextField(
        value="1", width=80, label="Ciclos", text_align=ft.TextAlign.RIGHT,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""),
        label_style=ft.TextStyle(color=ft.Colors.GREY_500)
    )
    delay_tf = ft.TextField(   # estético; no lo usa run_routine()
        value="0", width=100, label="Delay (s)", text_align=ft.TextAlign.RIGHT,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9\.]", replacement_string=""),
        label_style=ft.TextStyle(color=ft.Colors.GREY_500)
    )

    def _run_thread(fn):
        threading.Thread(target=fn, daemon=True).start()

    def ejecutar_una_vez(e):
        name = rutina_dd.value or "Rutina 1"
        stop_event.clear()
        def run():
            try:
                push_log(f"→ Ejecutando {name} (1 vez)", ft.Colors.GREEN_200)
                controlador.run_routine(name, cycles=1, stop_event=stop_event)
                push_log(f"✓ {name} completada", ft.Colors.GREEN_200)
            except Exception as ex:
                push_log(f"✖ Error en {name}: {ex}", ft.Colors.RED_200)
        _run_thread(run)

    def ejecutar_en_ciclos(e):
        name = rutina_dd.value or "Rutina 1"
        stop_event.clear()
        try:
            n = int(ciclos_tf.value or "1")
            if n < 1: n = 1
        except:
            n = 1
        def run():
            try:
                push_log(f"→ Ejecutando {name} en {n} ciclo(s)", ft.Colors.GREEN_200)
                controlador.run_routine(name, cycles=n, stop_event=stop_event)
                push_log(f"✓ {name} ciclos completados", ft.Colors.GREEN_200)
            except Exception as ex:
                push_log(f"✖ Error en ciclos de {name}: {ex}", ft.Colors.RED_200)
        _run_thread(run)

    def parar_rutina_home(e):
        def run():
            try:
                push_log("⛔ Paro de rutina solicitado…", ft.Colors.AMBER_200)
                controlador.stop_and_home(stop_event, close_seconds=3.0)
                push_log("✓ Rutina detenida y HOME aplicado.", ft.Colors.GREEN_200)
            except Exception as ex:
                push_log(f"✖ Error en paro de rutina: {ex}", ft.Colors.RED_200)
        _run_thread(run)

    btn_una_vez = ft.FilledButton(
        text="▶ Ejecutar (1 vez)", on_click=ejecutar_una_vez,
        bgcolor=ft.Colors.INDIGO, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
    )
    btn_ciclos = ft.FilledButton(
        text="🔁 Ejecutar en ciclos", on_click=ejecutar_en_ciclos,
        bgcolor=ft.Colors.DEEP_PURPLE, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
    )
    btn_paro = ft.FilledButton(
        text="⛔ Paro de rutina (HOME)", on_click=parar_rutina_home,
        bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
    )

    rutinas_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Rutinas", size=14, color=ft.Colors.GREY_300),
                    rutina_dd,
                    ft.Row([ciclos_tf, delay_tf], spacing=8),
                    ft.Row([btn_una_vez, btn_ciclos], spacing=8),
                    ft.Row([btn_paro], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=10),
            padding=8, width=360),
        elevation=2, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    # ===== Panel de control manual de dedos =====
    def control_row(nombre: str, num: int):
        dur_field = ft.TextField(
            value="1.0", width=66, text_align=ft.TextAlign.RIGHT,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9\.]", replacement_string=""),
            label="s", label_style=ft.TextStyle(color=ft.Colors.GREY_500)
        )
        def do_pulse(sentido: str):
            try:
                t = float(dur_field.value or "0")
                if t <= 0:
                    push_log("Duración debe ser > 0", ft.Colors.AMBER_200); return
            except ValueError:
                push_log("Duración inválida", ft.Colors.AMBER_200); return
            push_log(f"[{nombre}] {sentido.upper()} {t:.2f}s", ft.Colors.BLUE_200)
            def run():
                try:
                    controlador.mover_actuador(num, t, 0, 0,
                                               sentido_inicio=("open" if sentido == "open" else "close"))
                except Exception as ex:
                    push_log(f"✖ Error en control manual: {ex}", ft.Colors.RED_200); page.update()
            threading.Thread(target=run, daemon=True).start()
        return ft.Row(
            [
                ft.Text(nombre, width=80, color=ft.Colors.GREY_200),
                ft.FilledButton("Open", icon=ft.Icons.ARROW_UPWARD,
                                on_click=lambda e: do_pulse("open"),
                                bgcolor=ft.Colors.GREEN_400, color=ft.Colors.WHITE),
                ft.FilledButton("Close", icon=ft.Icons.ARROW_DOWNWARD,
                                on_click=lambda e: do_pulse("close"),
                                bgcolor=ft.Colors.RED_400, color=ft.Colors.WHITE),
                dur_field,
            ],
            spacing=8, alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
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
                                    threading.Thread(target=lambda: controlador.home_now(3.0), daemon=True).start(),
                                    push_log("HOME forzado: retroceso 3s a todos", ft.Colors.BLUE_200)
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(color=ft.Colors.WHITE),
                    control_row("Pulgar", 1),
                    control_row("Índice", 2),
                    control_row("Medio", 3),
                    control_row("Anular", 4),
                    control_row("Meñique", 5),
                ],
                spacing=10,
            ),
            padding=8, width=360),
        elevation=2, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    # ===== Gráficas EMG (dos canales simulados) =====
    scope1 = Scope("EMG - Canal 1", width=950, height=280, y_range_mV=6.0)
    scope2 = Scope("EMG - Canal 2", width=950, height=280, y_range_mV=6.0)
    charts_col = ft.Column([scope1.container, scope2.container], spacing=12, expand=True)

    # Motor RT
    engine = EMGEngine(page, scope1, scope2, seconds_window=5.0, fs=300)

    # ===== Botones sensor (sim) =====
    def crear_boton(texto, icono, color, on_click=None):
        return ft.FilledButton(
            text=texto, icon=icono, bgcolor=color, color=ft.Colors.WHITE, on_click=on_click,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=18),
                                 padding=ft.Padding(12, 10, 12, 10)),
            height=44, width=180)

    def start_sensor(e): engine.start(); push_log("Sensor: START", ft.Colors.GREEN_200)
    def stop_sensor(e):  engine.stop();  push_log("Sensor: STOP",  ft.Colors.AMBER_200)
    def reset_sensor(e): engine.reset(); push_log("Sensor: RESET", ft.Colors.AMBER_200)

    sensores_card = ft.Card(
        content=ft.Container(
            content=ft.Column([ft.Text("Control de sensores", size=14, color=ft.Colors.GREY_300),
                               ft.Divider(color=ft.Colors.WHITE),
                               crear_boton("Start Sensor", ft.Icons.PLAY_ARROW, ft.Colors.GREEN_400, start_sensor),
                               crear_boton("Stop Sensor",  ft.Icons.STOP,        ft.Colors.RED_400,   stop_sensor),
                               crear_boton("Reset Sensor", ft.Icons.REFRESH,     ft.Colors.AMBER_400, reset_sensor)],
                              spacing=10),
            padding=8, width=360),
        elevation=2, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    # ===== Layout =====
    left_container  = ft.Container(
        content=ft.Column([usuarios_card, rutinas_card, manual_panel], spacing=10),
        padding=0, alignment=ft.alignment.top_left,  width=372
    )
    right_container = ft.Container(
        content=ft.Column([sensores_card, estado_card], spacing=10,
                          horizontal_alignment=ft.CrossAxisAlignment.END),
        padding=0, alignment=ft.alignment.top_right, width=372
    )

    layout = ft.Row([left_container,
                     ft.Container(charts_col, expand=True, padding=ft.Padding(12, 0, 12, 0)),
                     right_container],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=0, expand=True)
    page.add(layout)

    # Limpieza segura al desconectar
    def _cleanup(*_):
        try:
            engine.stop()
        except Exception:
            pass
        try:
            controlador.stop_and_home(stop_event, close_seconds=3.0)
        except Exception:
            pass
        push_log("Conexión cerrada: HOME aplicado.", ft.Colors.AMBER_200)
    page.on_disconnect = _cleanup

# ---------------------- Lanzador --------------------------------------------
if __name__ == "__main__":
    port = _find_free_port(HOST, START_PORT)
    print("\n[Flet] Iniciando servidor web…")
    print(f" - Host/IP: {HOST}")
    print(f" - Puerto : {port}")
    print(f" - Abre en tu navegador:  http://{HOST}:{port}")

    view_mode = ft.WEB_BROWSER if OPEN_BROWSER_ON_SERVER else None
    if OPEN_BROWSER_ON_SERVER:
        try: webbrowser.open(f"http://{HOST}:{port}")
        except Exception: pass

    ft.app(target=window_main, assets_dir=ASSETS_DIR, view=view_mode, host=HOST, port=port)
