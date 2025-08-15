# main_window.py
from __future__ import annotations
import threading
import time
import socket
from dataclasses import dataclass
from typing import List, Dict, Optional
import flet as ft
from flet import canvas as cv
import webbrowser
import sys
import os

# ================= CONFIG (Raspberry Pi 5) =================
# Cambia HOST a la IP de tu Raspberry si quieres abrir desde otras máquinas.
# Para exponer en todas las interfaces puedes usar "0.0.0.0".
HOST = "169.254.69.170"
START_PORT = 5000
ASSETS_DIR = "assets"
OPEN_BROWSER_ON_SERVER = False
# ==========================================================

def _find_free_port(host: str, start_port: int, tries: int = 50) -> int:
    for p in range(start_port, start_port + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.15)
            if s.connect_ex((host, p)) != 0:
                return p
    raise RuntimeError("No hay puertos libres en el rango solicitado.")

# Asegura que el paquete local emg_processing sea importable
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

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
def open_users_sheet(page: ft.Page, on_user_selected):
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

def open_patients_sheet(page: ft.Page, selected_user: Optional[User], on_patient_selected):
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

# Motor de datos en tiempo real (usa el simulador)
class EMGEngine:
    def __init__(self, page: ft.Page, scope1: Scope, scope2: Scope,
                 seconds_window=5.0, fs=300):
        # Import flexible para que funcione tanto en Pi como en laptop
        try:
            from RaspberryPI5_server.emg_processing.signal_filter import EMGSimulator  # paquete local
        except Exception:
            # Fallback a una ruta alternativa si usas otra estructura
            from RaspberryPI5_server.emg_processing.signal_filter import EMGSimulator  # type: ignore
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
        self.sim = EMGSimulator(fs=self.fs, channels=2)

    def start(self):
        if self._running:
            print("Sensor ya estaba en marcha."); return
        self._stop.clear()
        threading.Thread(target=self._loop, daemon=True).start()
        self._running = True
        print("Sensor: START")

    def stop(self):
        if not self._running:
            print("Sensor: STOP (ya detenido)"); return
        self._stop.set()
        self._running = False
        print("Sensor: STOP")

    def reset(self):
        if hasattr(self.sim, "reset"):
            self.sim.reset()
        self.t.clear(); self.y1.clear(); self.y2.clear()
        self._render()
        print("Sensor: RESET")

    def _loop(self):
        block = max(3, int(self.fs * 0.03))  # ~30 ms
        t0 = self.t[-1] if self.t else 0.0
        while not self._stop.is_set():
            chunk = self.sim.next_chunk(block)   # [2][block]
            ch1, ch2 = chunk[0], chunk[1]
            dt = 1.0 / self.fs
            x = [t0 + (i+1)*dt for i in range(block)]
            t0 = x[-1]
            self.t.extend(x); self.y1.extend(ch1); self.y2.extend(ch2)
            if len(self.t) > self.max_pts:
                extra = len(self.t) - self.max_pts
                self.t = self.t[extra:]; self.y1 = self.y1[extra:]; self.y2 = self.y2[extra:]
            self._render()
            time.sleep(0.03)

    def _render(self):
        self.scope1.update_wave(self.t, self.y1, color=ft.Colors.AMBER_200)
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

    estado_title = ft.Text("SIM: controlador iniciado (sin GPIO).", size=14, color=ft.Colors.GREY_200)

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

    # ===== Controlador real (rutinas/gpio) o simulado =====
    def actualizar_estado(msg: str):
        push_log(msg, ft.Colors.GREY_300)

    try:
        # Importa tus rutinas reales desde routines.py (en el mismo dir que main_window.py)
        from Laptop_client.GUI.routines import ControlActuadores  # <-- usando gpiozero LGPIOFactory
        controlador = ControlActuadores(actualizar_estado=actualizar_estado)
        estado_title.value = "GPIO listo (LGPIO)."
    except Exception as ex:
        # Fallback simulado con mismas firmas de métodos
        push_log(f"[AVISO] Usando controlador SIMULADO: {ex}", ft.Colors.AMBER_200)
        class ControlActuadores:
            def __init__(self, actualizar_estado=None):
                self.actualizar_estado = actualizar_estado
                self._log("SIM: controlador iniciado (sin GPIO).")
            def _log(self, msg):
                if self.actualizar_estado: self.actualizar_estado(msg)
            def posicion_reposo(self):
                self._log("SIM: HOME (todos OFF).")
            def mover_actuador(self, num, t_av, t_pause, t_ret, sentido_inicio="open"):
                self._log(f"SIM: mover_actuador num={num} av={t_av}s pause={t_pause}s ret={t_ret}s sentido={sentido_inicio}")
            def rutina_1(self):
                self._log("SIM: rutina_1 inicia"); time.sleep(0.5); self._log("SIM: rutina_1 fin")
            def rutina_2(self):
                self._log("SIM: rutina_2 inicia"); time.sleep(0.5); self._log("SIM: rutina_2 fin")
            def rutina_3(self):
                self._log("SIM: rutina_3 inicia"); time.sleep(0.5); self._log("SIM: rutina_3 fin")
            def limpiar(self):
                self._log("SIM: limpiar()")
        controlador = ControlActuadores(actualizar_estado=actualizar_estado)

    # ===== Estado de selección (Usuarios/Pacientes) =====
    selected_user: Optional[User] = None

    # Botones Usuarios / Pacientes
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

    # ===== RUTINAS (DropDown + Ejecutar) =====
    rutina = ft.Dropdown(
        options=[ft.dropdown.Option(f"Rutina {i}") for i in range(1, 4)],
        width=220, hint_text="Selecciona una rutina",
        on_change=lambda e: (setattr(btn_ejecutar, "disabled", not bool(rutina.value)), page.update()),
        text_style=ft.TextStyle(color=ft.Colors.WHITE), hint_style=ft.TextStyle(color=ft.Colors.GREY_400),
    )

    def ejecutar_rutina(e):
        if not rutina.value:
            return
        rutina_sel = rutina.value
        btn_ejecutar.disabled = True; page.update()
        push_log(f"→ {rutina_sel} iniciada", ft.Colors.GREEN_200)

        def run():
            try:
                # Llama a rutina_1 / rutina_2 / rutina_3 del controlador real
                getattr(controlador, f"rutina_{rutina_sel[-1]}")()
                push_log(f"✓ {rutina_sel} completada", ft.Colors.GREEN_200)
            except Exception as ex:
                push_log(f"✖ Error en {rutina_sel}: {ex}", ft.Colors.RED_200)
            finally:
                btn_ejecutar.disabled = False; page.update()
        threading.Thread(target=run, daemon=True).start()

    btn_ejecutar = ft.FilledButton(
        text="🚀 Ejecutar Rutina", on_click=ejecutar_rutina,
        bgcolor=ft.Colors.INDIGO, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
        disabled=True
    )

    rutinas_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [ft.Text("Rutinas", size=14, color=ft.Colors.GREY_300), rutina, btn_ejecutar],
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
            padding=8, width=360),
        elevation=2, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    # Gráficas con canvas (dos canales)
    scope1 = Scope("EMG - Canal 1", width=950, height=280, y_range_mV=6.0)
    scope2 = Scope("EMG - Canal 2", width=950, height=280, y_range_mV=6.0)
    charts_col = ft.Column([scope1.container, scope2.container], spacing=12, expand=True)

    # Motor RT
    engine = EMGEngine(page, scope1, scope2, seconds_window=5.0, fs=300)

    # Botones sensor
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

    # Layout (rutinas entre usuarios y manual)
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

    # Limpieza segura al desconectar / cerrar
    def _cleanup(*_):
        try:
            controlador.posicion_reposo()
        except Exception:
            pass
        try:
            if hasattr(controlador, "limpiar"):
                controlador.limpiar()
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
    if HOST in ("169.254.69.170", "0.0.0.0"):
        print(f" - Abre en tu navegador:  http://169.254.69.170:{port}")
    else:
        print(f" - Abre en tu laptop:  http://{HOST}:{port}")

    view_mode = ft.WEB_BROWSER if OPEN_BROWSER_ON_SERVER else None
    if OPEN_BROWSER_ON_SERVER:
        try: webbrowser.open(f"http://169.254.69.170:{port}")
        except Exception: pass

    ft.app(target=window_main, assets_dir=ASSETS_DIR, view=view_mode, host=HOST, port=port)
