import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta, date
import math
import threading

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas, guardar_config, leer_config
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    InputTexto, BadgeLabel, mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido,
    NMToplevel, aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy, hora_actual

if not getattr(sys, 'frozen', False):
    _app_dir = os.path.join(_base, "apps", "temporizador")
    if _app_dir not in sys.path:
        sys.path.insert(0, _app_dir)
import sonido as _sonido
import presets as _presets

try:
    import pystray
    from PIL import Image as PILImage
    TRAY_DISPONIBLE = True
except ImportError:
    TRAY_DISPONIBLE = False

try:
    import pygame
    pygame.mixer.init()
    SONIDO_DISPONIBLE = True
except Exception:
    SONIDO_DISPONIBLE = False


CATEGORIAS = ["Relajación", "Cognitiva", "Física", "Social", "Autocuidado"]


class TemporizadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()
        _presets.sembrar_presets_si_vacio()
        try:
            from shared.sync import sync_al_abrir as _sync_al_abrir
            _sync_al_abrir()
        except Exception:
            pass
        self.modo = leer_config("theme", "dark")
        self._nombre_temp = ""
        self._actividad_texto = ""
        self._nombre_actividad = ""
        self._notas_temp = ""
        self.tray_icon = None

        self.duracion_total = 300
        self.tiempo_restante = 300
        self.corriendo = False
        self.en_pausa = False
        self.timer_id = None
        self.tiempo_inicio = None
        self._tiempo_objetivo = None
        self.categoria_actual = CATEGORIAS[0]

        self.title("NeuroMood · Temporizador de Actividades")
        w, h = 960, 720
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(900, 680)
        self.configure(fg_color=COLORS[self.modo]["bg_primary"])

        try:
            self.iconbitmap(obtener_icono_solido())
        except Exception:
            pass

        self._estado_ventana = "zoomed"
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        self._centrar_ventana()
        self._construir_ui()
        self.after(1000, self._poll_tema)

    def _centrar_ventana(self):
        self._prev_state = "zoomed"
        self.after(50, lambda: self.state("zoomed"))
        self.bind("<Configure>", self._on_configure_centrar)

    def _on_configure_centrar(self, event):
        if event.widget is not self:
            return
        estado = self.state()
        if estado in ("zoomed", "normal"):
            self._estado_ventana = estado
        if self._prev_state == "zoomed" and estado == "normal":
            self.after(20, self._recentrar)
        self._prev_state = estado

    def _recentrar(self):
        if self.state() != "normal":
            return
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _construir_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        self.configure(fg_color=colores["bg_primary"])

        self.header = HeaderFrame(
            self,
            titulo="Temporizador de Actividades",
            subtitulo="Delimitá tus actividades terapéuticas en el tiempo",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        )
        self.header.pack(fill="x")

        barra_inferior = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=40, corner_radius=0)
        barra_inferior.pack(fill="x", side="bottom")
        barra_inferior.pack_propagate(False)

        BotonSecundario(
            barra_inferior, text="Acerca de", modo=self.modo, width=100, height=30,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=12, pady=5)

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=LAYOUT["padding_container"],
                       pady=LAYOUT["padding_container"])

        col_izq = ctk.CTkFrame(contenido, fg_color="transparent")
        col_izq.pack(side="left", fill="both", expand=True, padx=(0, 12))

        col_der = ctk.CTkFrame(contenido, fg_color="transparent", width=300)
        col_der.pack(side="right", fill="both", padx=(12, 0))

        self._construir_temporizador(col_izq)
        self._construir_controles(col_izq)
        self._construir_panel_derecho(col_der)

    def _construir_temporizador(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        self.canvas_timer = tk.Canvas(
            card, bg=colores["bg_surface"], highlightthickness=0,
            width=180, height=180
        )
        self.canvas_timer.pack(pady=LAYOUT["padding_card"])

        self.lbl_tiempo = ctk.CTkLabel(
            card, text=self._formatear_tiempo(self.tiempo_restante),
            font=(TYPOGRAPHY["font_family"], 36, "bold"),
            text_color=colores["text_primary"]
        )
        self.lbl_tiempo.pack(pady=(0, 8))

        self.lbl_actividad = ctk.CTkLabel(
            card, text="Sin actividad configurada",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_tertiary"]
        )
        self.lbl_actividad.pack(pady=(0, LAYOUT["padding_card"]))
        if self._actividad_texto and self._actividad_texto != "Sin actividad configurada":
            if self._actividad_texto == "Actividad sin nombre":
                color = colores["text_tertiary"]
            else:
                color = colores["accent"] if self.corriendo else colores["success"]
            self.lbl_actividad.configure(text=self._actividad_texto, text_color=color)

        self._dibujar_arco()

    def _construir_controles(self, parent):
        colores = COLORS[self.modo]
        p = LAYOUT["padding_card"]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x")

        # ── Fila: Actividad ───────────────────────────
        row_act = ctk.CTkFrame(card, fg_color="transparent")
        row_act.pack(fill="x", padx=p, pady=(0, 8))
        ctk.CTkLabel(
            row_act, text="Actividad:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"],
            width=72, anchor="w"
        ).pack(side="left", padx=(0, 8))
        self.entry_nombre = InputTexto(row_act, modo=self.modo, placeholder_text="Nombre de la actividad", height=34)
        self.entry_nombre.pack(side="left", fill="x", expand=True)
        if self._nombre_temp:
            self.entry_nombre.insert(0, self._nombre_temp)

        # ── Fila: Notas ───────────────────────────────
        row_notas = ctk.CTkFrame(card, fg_color="transparent")
        row_notas.pack(fill="x", padx=p, pady=(0, 8))
        ctk.CTkLabel(
            row_notas, text="Notas:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"],
            width=72, anchor="w"
        ).pack(side="left", padx=(0, 8))
        self.entry_notas = InputTexto(
            row_notas, modo=self.modo,
            placeholder_text="Nota breve de sesión (opcional)", height=34
        )
        self.entry_notas.pack(side="left", fill="x", expand=True)
        if self._notas_temp:
            self.entry_notas.insert(0, self._notas_temp)

        # ── Fila: Categoría ───────────────────────────
        row_cat = ctk.CTkFrame(card, fg_color="transparent")
        row_cat.pack(fill="x", padx=p, pady=(0, 8))
        ctk.CTkLabel(
            row_cat, text="Categoría:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"],
            width=72, anchor="w"
        ).pack(side="left", padx=(0, 8))
        self.combo_categoria = ctk.CTkComboBox(
            row_cat, values=CATEGORIAS,
            fg_color=colores["bg_input"],
            border_color=colores["border"],
            button_color=colores["accent"],
            button_hover_color=colores["accent_hover"],
            dropdown_fg_color=colores["bg_surface"],
            dropdown_hover_color=colores["bg_hover"],
            text_color=colores["text_primary"],
            dropdown_text_color=colores["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            corner_radius=LAYOUT["radius_input"],
            command=self._on_categoria
        )
        self.combo_categoria.set(self.categoria_actual)
        self.combo_categoria.pack(side="left")

        # ── Fila: Duración ────────────────────────────
        row_dur = ctk.CTkFrame(card, fg_color="transparent")
        row_dur.pack(fill="x", padx=p, pady=(0, 8))
        ctk.CTkLabel(
            row_dur, text="Duración:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"],
            width=72, anchor="w"
        ).pack(side="left", padx=(0, 8))

        presets = [("5'", 300), ("10'", 600), ("15'", 900), ("20'", 1200), ("30'", 1800)]
        self.preset_btns = {}
        for texto, seg in presets:
            selec = (self.duracion_total == seg)
            b = ctk.CTkButton(
                row_dur, text=texto, width=44, height=34,
                fg_color=("#4A7EA5" if self.modo == "light" else colores["accent"]) if selec else ("#B5D0E8" if self.modo == "light" else colores["bg_hover"]),
                hover_color=("#3A6E95" if self.modo == "light" else colores["accent_hover"]) if selec else ("#9ABDD8" if self.modo == "light" else colores["accent_hover"]),
                text_color=(colores["text_on_accent"] if selec else "#1E4D78") if self.modo == "light" else colores["text_on_accent"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                command=lambda s=seg: self._set_duracion(s)
            )
            b.pack(side="left", padx=2)
            self.preset_btns[seg] = b

        self.entry_custom = InputTexto(row_dur, modo=self.modo, width=50, height=34, placeholder_text="min")
        self.entry_custom.pack(side="left", padx=(8, 4))
        ctk.CTkButton(
            row_dur, text="OK", width=36, height=34,
            fg_color=colores["accent"],
            hover_color=colores["accent_hover"],
            text_color=colores["text_on_accent"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            command=self._set_custom
        ).pack(side="left")

        # ── Separador ─────────────────────────────────
        ctk.CTkFrame(card, fg_color=colores["border"], height=1, corner_radius=0).pack(
            fill="x", padx=p, pady=(8, 0)
        )

        # ── Botones de control ────────────────────────
        frame_btns = ctk.CTkFrame(card, fg_color="transparent")
        frame_btns.pack(fill="x", padx=p, pady=(p // 2, p))

        if self.modo == "light":
            self.btn_iniciar = ctk.CTkButton(
                frame_btns, text="Iniciar", width=100, height=44,
                fg_color=colores["success"], hover_color="#4A8A70",
                text_color=colores["text_on_accent"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                command=self._iniciar
            )
        else:
            self.btn_iniciar = BotonPrimario(
                frame_btns, text="Iniciar", modo=self.modo, command=self._iniciar,
                width=100, height=44
            )
        self.btn_iniciar.pack(side="left", padx=(0, 8))

        if self.modo == "light":
            self.btn_pausar = ctk.CTkButton(
                frame_btns, text="Pausar", width=100, height=44,
                fg_color=colores["warning"], hover_color="#B06830",
                text_color=colores["text_on_accent"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                command=self._pausar
            )
        else:
            self.btn_pausar = BotonSecundario(
                frame_btns, text="Pausar", modo=self.modo, command=self._pausar,
                width=100, height=44
            )
        self.btn_pausar.pack(side="left", padx=(0, 8))

        _kw_sec = {"fg_color": colores["error"], "hover_color": "#BF5555", "border_width": 0} if self.modo == "light" else {}
        BotonSecundario(
            frame_btns, text="Reiniciar", modo=self.modo, command=self._reiniciar,
            width=100, height=44, **_kw_sec
        ).pack(side="left")

        BotonSecundario(
            frame_btns, text="+5 min", modo=self.modo, command=self._agregar_cinco_min,
            width=80, height=44
        ).pack(side="left", padx=(8, 0))

    def _construir_panel_derecho(self, parent):
        colores = COLORS[self.modo]
        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        tab_row = ctk.CTkFrame(card, fg_color="transparent")
        tab_row.pack(fill="x", padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4))

        _act      = colores["accent"]
        _inact_fg = colores["bg_hover"]
        _inact_tx = colores["text_secondary"]
        _tab_kw   = dict(height=28, corner_radius=LAYOUT["radius_button"], border_width=0,
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"))

        def _reset_tabs():
            self.btn_tab_hoy.configure(fg_color=_inact_fg, text_color=_inact_tx, hover_color=_act)
            self.btn_tab_pres.configure(fg_color=_inact_fg, text_color=_inact_tx, hover_color=_act)

        def _ir_hoy():
            _reset_tabs()
            self.btn_tab_hoy.configure(fg_color=_act, text_color=colores["text_on_accent"],
                                        hover_color=colores["accent_hover"])
            self._mostrar_tab_hoy()

        def _ir_presets():
            _reset_tabs()
            self.btn_tab_pres.configure(fg_color=_act, text_color=colores["text_on_accent"],
                                         hover_color=colores["accent_hover"])
            self._mostrar_tab_presets()

        self.btn_tab_hoy = ctk.CTkButton(
            tab_row, text="Hoy", width=72, command=_ir_hoy,
            fg_color=_act, text_color=colores["text_on_accent"],
            hover_color=colores["accent_hover"], **_tab_kw
        )
        self.btn_tab_hoy.pack(side="left", padx=(0, 4))

        self.btn_tab_pres = ctk.CTkButton(
            tab_row, text="Presets", width=76, command=_ir_presets,
            fg_color=_inact_fg, text_color=_inact_tx, hover_color=_act, **_tab_kw
        )
        self.btn_tab_pres.pack(side="left")

        self.frame_panel_der = ctk.CTkFrame(card, fg_color="transparent")
        self.frame_panel_der.pack(fill="both", expand=True,
                                   padx=LAYOUT["padding_card"],
                                   pady=(4, LAYOUT["padding_card"]))
        self._fn_ir_hoy = _ir_hoy
        self._fn_ir_presets = _ir_presets
        self._mostrar_tab_hoy()

    def _cargar_historial(self):
        if not hasattr(self, 'frame_historial'):
            return
        try:
            if not self.frame_historial.winfo_exists():
                return
        except Exception:
            return
        for widget in self.frame_historial.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        conn = obtener_conexion()
        registros = conn.execute(
            "SELECT nombre, categoria, hora, duracion_real, notas "
            "FROM actividades_temporizador WHERE fecha = ? ORDER BY hora DESC",
            (fecha_hoy(),)
        ).fetchall()
        conn.close()

        if not registros:
            ctk.CTkLabel(
                self.frame_historial, text="Sin actividades completadas hoy",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        for reg in registros:
            fila = ctk.CTkFrame(self.frame_historial, fg_color=colores["bg_list_item"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=2)

            info = ctk.CTkFrame(fila, fg_color="transparent")
            info.pack(side="left", padx=12, pady=8, fill="x", expand=True)

            ctk.CTkLabel(
                info, text=f"✓ {reg['nombre']}",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_primary"]
            ).pack(anchor="w")

            sub = reg["categoria"] or ""
            if reg["notas"]:
                sub = f"{sub} · {reg['notas']}" if sub else reg["notas"]
            if sub:
                ctk.CTkLabel(
                    info, text=sub,
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    text_color=colores["text_tertiary"]
                ).pack(anchor="w")

            mins = reg["duracion_real"] // 60
            segs = reg["duracion_real"] % 60
            dur_txt = f"{mins}'{segs:02d}\""
            ctk.CTkLabel(
                fila, text=dur_txt,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["success"] if self.modo == "light" else colores["accent"]
            ).pack(side="right", padx=12)

            ctk.CTkLabel(
                fila, text=reg["hora"][:5],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(side="right", padx=4)

    def _mostrar_tab_hoy(self):
        for w in self.frame_panel_der.winfo_children():
            w.destroy()
        colores = COLORS[self.modo]
        self.frame_historial = ctk.CTkScrollableFrame(
            self.frame_panel_der, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_historial.pack(fill="both", expand=True)
        self._cargar_historial()

    def _calcular_stats(self) -> dict:
        hoy = fecha_hoy()
        desde_sem = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        desde_mes = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        conn = obtener_conexion()
        hoy_rows = conn.execute(
            "SELECT duracion_real FROM actividades_temporizador WHERE fecha=?", (hoy,)
        ).fetchall()
        sem_rows = conn.execute(
            "SELECT duracion_real FROM actividades_temporizador WHERE fecha >= ?", (desde_sem,)
        ).fetchall()
        cat_rows = conn.execute(
            "SELECT categoria, COUNT(*) as cnt, SUM(duracion_real) as total_seg "
            "FROM actividades_temporizador WHERE fecha >= ? GROUP BY categoria ORDER BY cnt DESC",
            (desde_mes,)
        ).fetchall()
        fechas_set = {r["fecha"] for r in conn.execute(
            "SELECT DISTINCT fecha FROM actividades_temporizador"
        ).fetchall()}
        conn.close()
        racha = 0
        d = date.today()
        while d.strftime("%Y-%m-%d") in fechas_set:
            racha += 1
            d -= timedelta(days=1)
        return {
            "hoy_ses":  len(hoy_rows),
            "hoy_mins": sum(r["duracion_real"] for r in hoy_rows) // 60,
            "sem_ses":  len(sem_rows),
            "sem_mins": sum(r["duracion_real"] for r in sem_rows) // 60,
            "por_cat":  [dict(r) for r in cat_rows],
            "racha":    racha,
        }

    def _mostrar_tab_presets(self):
        for w in self.frame_panel_der.winfo_children():
            w.destroy()
        colores = COLORS[self.modo]
        scroll = ctk.CTkScrollableFrame(
            self.frame_panel_der, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        scroll.pack(fill="both", expand=True)

        visibles = _presets.obtener_presets()

        if not visibles:
            ctk.CTkLabel(
                scroll, text="Sin presets disponibles",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        for pr in visibles:
            fila = ctk.CTkFrame(scroll, fg_color=colores["bg_list_item"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=2)

            info = ctk.CTkFrame(fila, fg_color="transparent")
            info.pack(side="left", padx=10, pady=6, fill="x", expand=True)

            ctk.CTkLabel(
                info, text=pr["nombre"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_primary"], anchor="w"
            ).pack(anchor="w")

            sub_parts = []
            if pr.get("categoria"):
                sub_parts.append(pr["categoria"])
            if pr.get("duracion_seg"):
                mins = pr["duracion_seg"] // 60
                sub_parts.append(f"{mins} min" if mins else "libre")
            if sub_parts:
                ctk.CTkLabel(
                    info, text=" · ".join(sub_parts),
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    text_color=colores["text_tertiary"], anchor="w"
                ).pack(anchor="w")

            ctk.CTkButton(
                fila, text="Usar", width=52, height=28,
                fg_color=colores["accent"], hover_color=colores["accent_hover"],
                text_color=colores["text_on_accent"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
                command=lambda p=pr: self._aplicar_preset(p)
            ).pack(side="right", padx=8, pady=6)

    def _aplicar_preset(self, preset: dict):
        if self.corriendo:
            return
        if hasattr(self, "entry_nombre"):
            self.entry_nombre.delete(0, "end")
            self.entry_nombre.insert(0, preset["nombre"])
        cat = preset.get("categoria", "")
        if hasattr(self, "combo_categoria") and cat in CATEGORIAS:
            self.combo_categoria.set(cat)
            self.categoria_actual = cat
        dur = preset.get("duracion_seg", 0)
        if dur and dur > 0:
            self._set_duracion(dur)

    def _dibujar_arco(self):
        canvas = self.canvas_timer
        canvas.delete("all")
        colores = COLORS[self.modo]

        w = 180
        h = 180
        cx, cy = w // 2, h // 2
        radio = 70
        grosor = 10

        canvas.create_oval(
            cx - radio, cy - radio, cx + radio, cy + radio,
            outline=colores["progress_track"], width=grosor
        )

        if self.duracion_total > 0:
            progreso = self.tiempo_restante / self.duracion_total if self.corriendo or self.tiempo_restante > 0 else 1.0
        else:
            progreso = 0

        if progreso > 0:
            angulo_inicio = 90
            angulo_ext = progreso * 360
            if self.corriendo and self.tiempo_restante <= 10:
                _arc_color = colores["error"]
            elif self.corriendo and self.tiempo_restante <= 60:
                _arc_color = colores["warning"]
            else:
                _arc_color = colores["success"] if self.modo == "light" else colores["accent"]
            canvas.create_arc(
                cx - radio, cy - radio, cx + radio, cy + radio,
                start=angulo_inicio, extent=angulo_ext,
                outline=_arc_color, width=grosor, style="arc"
            )

    def _formatear_tiempo(self, segundos: int) -> str:
        m = segundos // 60
        s = segundos % 60
        return f"{m:02d}:{s:02d}"

    def _set_duracion(self, segundos: int):
        if not self.corriendo:
            self.duracion_total = segundos
            self.tiempo_restante = segundos
            self.lbl_tiempo.configure(text=self._formatear_tiempo(segundos))
            self._dibujar_arco()
            if hasattr(self, 'preset_btns'):
                colores = COLORS[self.modo]
                for seg, btn in self.preset_btns.items():
                    if seg == segundos:
                        btn.configure(fg_color="#4A7EA5" if self.modo == "light" else colores["accent"], hover_color="#3A6E95" if self.modo == "light" else colores["accent_hover"], text_color=colores["text_on_accent"])
                    else:
                        btn.configure(fg_color="#B5D0E8" if self.modo == "light" else colores["bg_hover"], hover_color="#9ABDD8" if self.modo == "light" else colores["accent_hover"], text_color="#1E4D78" if self.modo == "light" else colores["text_on_accent"])

    def _set_custom(self):
        try:
            minutos = int(self.entry_custom.get().strip())
            if 1 <= minutos <= 180:
                self._set_duracion(minutos * 60)
        except ValueError:
            pass

    def _on_categoria(self, valor):
        self.categoria_actual = valor

    def _iniciar(self):
        if self.corriendo:
            return
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            nombre = "Actividad sin nombre"

        self._nombre_actividad = nombre

        colores = COLORS[self.modo]
        self.lbl_actividad.configure(text=nombre, text_color=colores["accent"])

        if self.tiempo_restante <= 0:
            self.tiempo_restante = self.duracion_total

        self.en_pausa = False
        self.btn_pausar.configure(text="Pausar")
        self.tiempo_inicio = datetime.now()
        self._tiempo_objetivo = self.tiempo_inicio + timedelta(seconds=self.tiempo_restante)
        self.corriendo = True
        if hasattr(self, 'entry_nombre'):
            self.entry_nombre.configure(state="disabled")
        if hasattr(self, 'combo_categoria'):
            self.combo_categoria.configure(state="disabled")
        if hasattr(self, 'entry_custom'):
            self.entry_custom.configure(state="disabled")
        if hasattr(self, 'combo_preset'):
            self.combo_preset.configure(state="disabled")
        if hasattr(self, 'entry_notas'):
            self.entry_notas.configure(state="disabled")
        if self.modo == "light" and hasattr(self, 'btn_iniciar'):
            self.btn_iniciar.configure(fg_color="#3D7A60", text_color="#E8F5EE")
        self._tick()

    def _pausar(self):
        if self.corriendo:
            self.corriendo = False
            if self.timer_id:
                self.after_cancel(self.timer_id)
                self.timer_id = None
            self.en_pausa = True
            colores = COLORS[self.modo]
            if self.modo == "light":
                self.btn_pausar.configure(text="Reanudar", fg_color=colores["warning"], hover_color="#B06830", text_color=colores["text_on_accent"])
                self.btn_iniciar.configure(state="disabled", fg_color="#3D7A60", text_color="#E8F5EE")
            else:
                self.btn_pausar.configure(text="Reanudar")
                self.btn_iniciar.configure(state="disabled")
            if hasattr(self, 'entry_nombre'):
                self.entry_nombre.configure(state="normal")
            if hasattr(self, 'combo_categoria'):
                self.combo_categoria.configure(state="normal")
            if hasattr(self, 'entry_custom'):
                self.entry_custom.configure(state="normal")
            if hasattr(self, 'combo_preset'):
                self.combo_preset.configure(state="normal")
            if hasattr(self, 'entry_notas'):
                self.entry_notas.configure(state="normal")
        elif self.en_pausa:
            self.en_pausa = False
            self.corriendo = True
            colores = COLORS[self.modo]
            if self.modo == "light":
                self.btn_pausar.configure(text="Pausar", fg_color=colores["warning"], hover_color="#B06830", text_color=colores["text_on_accent"])
                self.btn_iniciar.configure(state="normal", fg_color="#3D7A60", text_color="#E8F5EE")
            else:
                self.btn_pausar.configure(text="Pausar")
                self.btn_iniciar.configure(state="normal")
            if hasattr(self, 'entry_nombre'):
                self.entry_nombre.configure(state="disabled")
            if hasattr(self, 'combo_categoria'):
                self.combo_categoria.configure(state="disabled")
            if hasattr(self, 'entry_custom'):
                self.entry_custom.configure(state="disabled")
            if hasattr(self, 'combo_preset'):
                self.combo_preset.configure(state="disabled")
            if hasattr(self, 'entry_notas'):
                self.entry_notas.configure(state="disabled")
            self._tiempo_objetivo = datetime.now() + timedelta(seconds=self.tiempo_restante)
            self._tick()

    def _reiniciar(self):
        self.corriendo = False
        self._tiempo_objetivo = None
        self.en_pausa = False
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.tiempo_restante = self.duracion_total
        self.lbl_tiempo.configure(text=self._formatear_tiempo(self.duracion_total))
        colores = COLORS[self.modo]
        if self.modo == "light":
            self.btn_pausar.configure(text="Pausar", fg_color=colores["warning"], hover_color="#B06830", text_color=colores["text_on_accent"])
            self.btn_iniciar.configure(state="normal", fg_color=colores["success"], text_color=colores["text_on_accent"])
        else:
            self.btn_pausar.configure(text="Pausar")
            self.btn_iniciar.configure(state="normal")
        self.lbl_actividad.configure(text="Sin actividad configurada", text_color=colores["text_tertiary"])
        if hasattr(self, 'entry_nombre'):
            self.entry_nombre.configure(state="normal")
        if hasattr(self, 'combo_categoria'):
            self.combo_categoria.configure(state="normal")
        if hasattr(self, 'entry_custom'):
            self.entry_custom.configure(state="normal")
        if hasattr(self, 'combo_preset'):
            self.combo_preset.configure(state="normal")
        if hasattr(self, 'entry_notas'):
            self.entry_notas.configure(state="normal")
        self._dibujar_arco()

    def _tick(self):
        if not self.corriendo:
            return

        if self._tiempo_objetivo is not None:
            self.tiempo_restante = max(0, round((self._tiempo_objetivo - datetime.now()).total_seconds()))
        else:
            self.tiempo_restante = max(0, self.tiempo_restante - 1)

        self.lbl_tiempo.configure(text=self._formatear_tiempo(self.tiempo_restante))
        self._dibujar_arco()

        if self.tiempo_restante <= 0:
            self.corriendo = False
            self._finalizar()
            return

        self.timer_id = self.after(1000, self._tick)

    def _finalizar(self):
        nombre = self._nombre_actividad or self.entry_nombre.get().strip()
        duracion_real = self.duracion_total - self.tiempo_restante
        notas = self.entry_notas.get().strip() if hasattr(self, 'entry_notas') else ""
        for attr in ('entry_nombre', 'combo_categoria', 'entry_custom', 'combo_preset', 'entry_notas'):
            w = getattr(self, attr, None)
            if w:
                w.configure(state="normal")

        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO actividades_temporizador "
                "(fecha, hora, nombre, categoria, duracion_config, duracion_real, notas) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), nombre, self.categoria_actual,
                 self.duracion_total, duracion_real, notas)
            )
            conn.commit()
            conn.close()
            try:
                from shared.sync import sync_inmediato_background as _sib
                _sib()
            except Exception:
                pass
        except Exception:
            pass

        self._reproducir_alarma()

        if self.tray_icon is not None:
            self._restaurar_desde_bandeja()
        if hasattr(self, '_fn_ir_hoy'):
            self._fn_ir_hoy()
        else:
            self._cargar_historial()
        self._mostrar_finalizado(nombre, duracion_real, self.categoria_actual)

    def _reproducir_alarma(self):
        tipo = leer_config("timer_alarma", "campana")
        _sonido.reproducir(tipo)

    def _agregar_cinco_min(self):
        if not self.corriendo and not self.en_pausa:
            return
        self.duracion_total += 300
        self.tiempo_restante += 300
        if self._tiempo_objetivo is not None:
            self._tiempo_objetivo += timedelta(seconds=300)

    def _mostrar_finalizado(self, nombre: str = "", duracion_real: int = 0, categoria: str = ""):
        self._restaurar_ventana()
        colores = COLORS[self.modo]
        if hasattr(self, 'lbl_actividad'):
            _es_placeholder = not nombre or nombre == "Actividad sin nombre"
            self.lbl_actividad.configure(
                text=nombre or "Actividad",
                text_color=colores["text_tertiary"] if _es_placeholder else colores["success"]
            )

        popup = NMToplevel(self, modo=self.modo)
        popup.title("Actividad completada")
        _w, _h = 400, 240
        _sw = popup.winfo_screenwidth()
        _sh = popup.winfo_screenheight()
        popup.geometry(f"{_w}x{_h}+{(_sw - _w) // 2}+{(_sh - _h) // 2}")
        popup.resizable(False, False)
        popup.configure(fg_color=colores["bg_surface"])
        popup.attributes("-topmost", True)
        popup.grab_set()
        popup.after(10, lambda: popup.focus_force())

        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=LAYOUT["padding_container"],
                   pady=LAYOUT["padding_container"])

        ctk.CTkLabel(
            frame, text="✓  Sesión completada",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["success"] if self.modo == "light" else colores["accent"]
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            frame,
            text=nombre if nombre and nombre != "Actividad sin nombre" else "Sesión sin nombre",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_primary"], wraplength=340
        ).pack(pady=(0, 10))

        # Duration + category pill
        info_row = ctk.CTkFrame(frame, fg_color=colores["bg_hover"],
                                corner_radius=LAYOUT["radius_button"])
        info_row.pack(fill="x", pady=(0, 16))
        mins = duracion_real // 60
        segs = duracion_real % 60
        dur_txt = f"⏱  {mins} min {segs} seg" if segs else f"⏱  {mins} min"
        ctk.CTkLabel(
            info_row, text=dur_txt,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["text_primary"]
        ).pack(side="left", padx=14, pady=8)
        if categoria:
            ctk.CTkLabel(
                info_row, text=categoria,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(side="right", padx=14, pady=8)

        _kw_verde = {"fg_color": colores["success"], "hover_color": "#4A8A70"} if self.modo == "light" else {}
        BotonPrimario(
            frame, text="Entendido", modo=self.modo, width=130,
            command=popup.destroy, **_kw_verde
        ).pack()

    def _al_cerrar(self):
        if self.corriendo:
            self._enviar_a_bandeja()
        else:
            self.destroy()

    def _enviar_a_bandeja(self):
        if not TRAY_DISPONIBLE:
            self.destroy()
            return
        self.withdraw()

        def _crear_imagen():
            try:
                ruta = obtener_ruta_recurso("NM_icon.ico")
                img = PILImage.open(ruta).convert("RGBA").resize((64, 64), PILImage.LANCZOS)
                return img
            except Exception:
                img = PILImage.new("RGBA", (64, 64), (30, 200, 212, 255))
                return img

        menu = pystray.Menu(
            pystray.MenuItem("Abrir Temporizador", lambda icon, item: self.after(0, self._restaurar_desde_bandeja), default=True),
            pystray.MenuItem("Salir", lambda icon, item: self.after(0, self._salir_desde_bandeja)),
        )
        self.tray_icon = pystray.Icon(
            "NM_Temporizador",
            _crear_imagen(),
            "Temporizador en ejecución",
            menu=menu
        )
        hilo = threading.Thread(target=self.tray_icon.run, daemon=True)
        hilo.start()

    def _restaurar_desde_bandeja(self):
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self._restaurar_ventana()

    def _salir_desde_bandeja(self):
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self.destroy()

    def _restaurar_ventana(self):
        self.deiconify()
        estado = getattr(self, "_estado_ventana", "zoomed")
        if estado == "zoomed":
            self.state("zoomed")
        self.lift()
        self.focus_force()

    def _poll_tema(self):
        try:
            modo_config = leer_config("theme", self.modo)
            if modo_config != self.modo:
                self._aplicar_tema_externo(modo_config)
        except Exception:
            pass
        try:
            self.after(1000, self._poll_tema)
        except Exception:
            pass

    def _aplicar_tema_externo(self, nuevo_modo):
        if nuevo_modo == self.modo:
            return
        self._toggle_modo_con(nuevo_modo)

    def _toggle_modo_con(self, nuevo_modo):
        estado = self.state()
        self._nombre_temp = self.entry_nombre.get().strip() if hasattr(self, 'entry_nombre') else ""
        self._notas_temp = self.entry_notas.get().strip() if hasattr(self, 'entry_notas') else ""
        self._actividad_texto = self.lbl_actividad.cget("text") if hasattr(self, 'lbl_actividad') else ""
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        was_corriendo = self.corriendo
        self.corriendo = False
        self.modo = nuevo_modo
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")
        if was_corriendo:
            self.corriendo = True
            self._tick()
            if hasattr(self, 'entry_nombre'):
                self.entry_nombre.configure(state="disabled")
            if hasattr(self, 'combo_categoria'):
                self.combo_categoria.configure(state="disabled")
            if hasattr(self, 'entry_custom'):
                self.entry_custom.configure(state="disabled")
            if self.modo == "light" and hasattr(self, 'btn_iniciar'):
                self.btn_iniciar.configure(fg_color="#3D7A60", text_color="#E8F5EE")
        elif self.en_pausa:
            if self.modo == "light":
                colores_p = COLORS[self.modo]
                self.btn_pausar.configure(text="Reanudar", fg_color=colores_p["warning"], hover_color="#B06830", text_color=colores_p["text_on_accent"])
                self.btn_iniciar.configure(state="disabled", fg_color="#3D7A60", text_color="#E8F5EE")
            else:
                self.btn_pausar.configure(text="Reanudar")
                self.btn_iniciar.configure(state="disabled")

    def _toggle_modo(self):
        nuevo = "light" if self.modo == "dark" else "dark"
        guardar_config("theme", nuevo)
        self._toggle_modo_con(nuevo)



if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = TemporizadorApp()
    app.mainloop()
