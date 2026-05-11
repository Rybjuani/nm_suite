import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

_app_dir = os.path.join(_base, "apps", "checklist")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas, guardar_config, leer_config
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    InputTexto, mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido, NMToplevel,
    aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy
import random
import plantillas as _plantillas

try:
    import pygame
    pygame.mixer.init()
    SONIDO_DISPONIBLE = True
except Exception:
    SONIDO_DISPONIBLE = False


SECCIONES = [("manana", "Mañana"), ("tarde", "Tarde"), ("noche", "Noche")]

CATEGORIAS_TAREA = ["Logro", "Placer", "Autocuidado", "Social"]
_CAT_COLOR = {
    "Logro":       "#3A6EA5",
    "Placer":      "#3A8E5A",
    "Autocuidado": "#7A4EA5",
    "Social":      "#C07030",
}


class ChecklistApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()
        _plantillas.sembrar_plantillas_si_vacio()
        try:
            from shared.sync import sync_al_abrir as _sync_al_abrir
            _sync_al_abrir()
        except Exception:
            pass
        self.modo = leer_config("theme", "dark")
        self.seccion_activa = "manana"
        self._semana_offset = 0

        self.title("NeuroMood · Checklist de Rutina")
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

        self._centrar_ventana()
        self._construir_ui()
        self._fecha_actual = fecha_hoy()
        self._guardar_snapshot_hoy()
        self._verificar_cambio_dia()
        self.after(1000, self._poll_tema)

    def _centrar_ventana(self):
        self._prev_state = "zoomed"
        self.after(50, lambda: self.state("zoomed"))
        self.bind("<Configure>", self._on_configure_centrar)

    def _on_configure_centrar(self, event):
        if event.widget is not self:
            return
        estado = self.state()
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
            titulo="Checklist de Rutina",
            subtitulo="Estructura tu día para mejorar tu bienestar",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        )
        self.header.pack(fill="x")

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=LAYOUT["padding_container"],
                       pady=LAYOUT["padding_container"])

        col_izq = ctk.CTkFrame(contenido, fg_color="transparent")
        col_izq.pack(side="left", fill="both", expand=True, padx=(0, 12))

        col_der = ctk.CTkFrame(contenido, fg_color="transparent", width=280)
        col_der.pack(side="right", fill="both", padx=(12, 0))

        self._construir_tabs(col_izq)
        self._construir_tareas(col_izq)
        self._construir_panel_derecho(col_der)

        barra_inferior = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=40, corner_radius=0)
        barra_inferior.pack(fill="x", side="bottom")
        barra_inferior.pack_propagate(False)


        BotonSecundario(
            barra_inferior, text="Acerca de", modo=self.modo, width=100, height=30,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=12, pady=5)

    def _construir_tabs(self, parent):
        colores = COLORS[self.modo]

        tabs_frame = ctk.CTkFrame(parent, fg_color="transparent", height=44)
        tabs_frame.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))
        tabs_frame.pack_propagate(False)

        for clave, nombre in SECCIONES:
            es_activa = clave == self.seccion_activa
            ctk.CTkButton(
                tabs_frame, text=nombre, height=36,
                fg_color=("#4A7EA5" if self.modo == "light" else colores["accent"]) if es_activa else ("#B5D0E8" if self.modo == "light" else colores["bg_hover"]),
                hover_color=("#3A6E95" if self.modo == "light" else colores["accent_hover"]) if es_activa else ("#9ABDD8" if self.modo == "light" else colores["accent_hover"]),
                text_color=(colores["text_on_accent"] if es_activa else "#1E4D78") if self.modo == "light" else colores["text_on_accent"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                command=lambda c=clave: self._cambiar_seccion(c)
            ).pack(side="left", padx=4, fill="y")

    def _construir_tareas(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        self.frame_tareas = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_tareas.pack(fill="both", expand=True, padx=LAYOUT["padding_card"],
                               pady=(0, LAYOUT["padding_card"]))

        self._cargar_tareas()

        if leer_config("perm_checklist_manual", "0") == "1":
            add_row = ctk.CTkFrame(card, fg_color="transparent")
            add_row.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))
            self._entry_nueva_tarea = InputTexto(add_row, modo=self.modo, placeholder_text="Nueva tarea...")
            self._entry_nueva_tarea.pack(side="left", fill="x", expand=True, padx=(0, 8))
            BotonSecundario(add_row, text="+ Agregar", modo=self.modo, width=90, height=34,
                            command=self._agregar_tarea_manual).pack(side="left")

    def _cargar_tareas(self):
        for widget in self.frame_tareas.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        hoy = fecha_hoy()

        conn = obtener_conexion()
        try:
            tareas_raw = conn.execute(
                "SELECT id, descripcion, orden, "
                "COALESCE(categoria, 'Logro') as categoria, "
                "animo_rango "
                "FROM checklist_tareas WHERE seccion = ? ORDER BY orden",
                (self.seccion_activa,)
            ).fetchall()
        except Exception:
            tareas_raw = conn.execute(
                "SELECT id, descripcion, orden, "
                "COALESCE(categoria, 'Logro') as categoria "
                "FROM checklist_tareas WHERE seccion = ? ORDER BY orden",
                (self.seccion_activa,)
            ).fetchall()
        row_animo = conn.execute(
            "SELECT puntaje FROM termometro ORDER BY fecha DESC, hora DESC LIMIT 1"
        ).fetchone()
        puntaje_animo = row_animo["puntaje"] if row_animo else None

        completadas_hoy = set()
        rows = conn.execute(
            "SELECT tarea_id FROM checklist_completadas WHERE fecha = ?", (hoy,)
        ).fetchall()
        for r in rows:
            completadas_hoy.add(r["tarea_id"])
        conn.close()

        _RANGOS = {"Bajo": (1, 4), "Medio": (4, 7), "Alto": (7, 10)}

        def _visible(t):
            try:
                rango = t["animo_rango"]
            except (IndexError, KeyError):
                rango = None
            if not rango:
                return True
            if puntaje_animo is None:
                return True
            amin, amax = _RANGOS.get(rango, (1, 10))
            return amin <= puntaje_animo <= amax

        tareas = [t for t in tareas_raw if _visible(t)]

        if not tareas:
            todas_seccion = len(tareas_raw)
            msg = ("Sin tareas en esta sección" if todas_seccion == 0
                   else "Sin tareas para tu nivel de ánimo actual")
            ctk.CTkLabel(
                self.frame_tareas, text=msg,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        for tarea in tareas:
            esta_completada = tarea["id"] in completadas_hoy
            cat = tarea["categoria"]
            fila = ctk.CTkFrame(
                self.frame_tareas,
                fg_color=colores["bg_list_item"],
                corner_radius=LAYOUT["radius_button"]
            )
            fila.pack(fill="x", pady=3)

            var_check = ctk.BooleanVar(value=esta_completada)
            tarea_id = tarea["id"]
            _cb_fg = colores["success"] if self.modo == "light" else colores["accent"]
            _cb_hv = "#4A8A70" if self.modo == "light" else colores["accent_hover"]

            cb = ctk.CTkCheckBox(
                fila, text=tarea["descripcion"],
                variable=var_check,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["success"] if esta_completada else colores["text_primary"],
                fg_color=_cb_fg,
                hover_color=_cb_hv,
                border_color=colores["border"],
                checkmark_color=colores["text_on_accent"],
                command=lambda tid=tarea_id, v=var_check: self._toggle_tarea(tid, v)
            )
            cb.pack(side="left", padx=12, pady=10)

            ctk.CTkLabel(
                fila, text=cat, width=80, height=20,
                fg_color=_CAT_COLOR.get(cat, _CAT_COLOR["Logro"]),
                corner_radius=4,
                text_color="#FFFFFF",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"])
            ).pack(side="left", padx=(0, 4))

            if not esta_completada:
                ctk.CTkButton(
                    fila, text="✕", width=32, height=28,
                    fg_color="transparent",
                    hover_color=colores["error"],
                    text_color=colores["text_tertiary"],
                    corner_radius=LAYOUT["radius_button"],
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                    command=lambda tid=tarea_id: self._eliminar_tarea(tid)
                ).pack(side="right", padx=8)

    def _construir_panel_derecho(self, parent):
        colores = COLORS[self.modo]
        self._tab_der = getattr(self, '_tab_der', 'hoy')

        tab_bar = ctk.CTkFrame(parent, fg_color="transparent", height=36)
        tab_bar.pack(fill="x", pady=(0, 6))
        tab_bar.pack_propagate(False)

        frame_hoy      = ctk.CTkFrame(parent, fg_color="transparent")
        frame_stats    = ctk.CTkFrame(parent, fg_color="transparent")
        frame_propuestas = ctk.CTkFrame(parent, fg_color="transparent")

        def _ocultar_todos():
            frame_hoy.pack_forget()
            frame_stats.pack_forget()
            frame_propuestas.pack_forget()

        def _ir_hoy():
            self._tab_der = 'hoy'
            _ocultar_todos()
            frame_hoy.pack(fill="both", expand=True)
            btn_hoy.configure(fg_color=colores["accent"], text_color=colores["text_on_accent"])
            btn_stats.configure(fg_color=colores["bg_hover"], text_color=colores["text_primary"])
            btn_prop.configure(fg_color=colores["bg_hover"], text_color=colores["text_primary"])

        def _ir_stats():
            self._tab_der = 'stats'
            _ocultar_todos()
            frame_stats.pack(fill="both", expand=True)
            btn_hoy.configure(fg_color=colores["bg_hover"], text_color=colores["text_primary"])
            btn_stats.configure(fg_color=colores["accent"], text_color=colores["text_on_accent"])
            btn_prop.configure(fg_color=colores["bg_hover"], text_color=colores["text_primary"])

        def _ir_propuestas():
            self._tab_der = 'propuestas'
            _ocultar_todos()
            frame_propuestas.pack(fill="both", expand=True)
            btn_hoy.configure(fg_color=colores["bg_hover"], text_color=colores["text_primary"])
            btn_stats.configure(fg_color=colores["bg_hover"], text_color=colores["text_primary"])
            btn_prop.configure(fg_color=colores["accent"], text_color=colores["text_on_accent"])

        _btn_kw = dict(
            height=32, hover_color=colores["accent_hover"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold")
        )
        btn_hoy = ctk.CTkButton(
            tab_bar, text="Hoy",
            fg_color=colores["accent"] if self._tab_der == 'hoy' else colores["bg_hover"],
            text_color=colores["text_on_accent"] if self._tab_der == 'hoy' else colores["text_primary"],
            command=_ir_hoy, **_btn_kw
        )
        btn_hoy.pack(side="left", padx=(0, 4), fill="y")

        btn_stats = ctk.CTkButton(
            tab_bar, text="Estadísticas",
            fg_color=colores["accent"] if self._tab_der == 'stats' else colores["bg_hover"],
            text_color=colores["text_on_accent"] if self._tab_der == 'stats' else colores["text_primary"],
            command=_ir_stats, **_btn_kw
        )
        btn_stats.pack(side="left", padx=(0, 4), fill="y")

        btn_prop = ctk.CTkButton(
            tab_bar, text="Propuestas",
            fg_color=colores["accent"] if self._tab_der == 'propuestas' else colores["bg_hover"],
            text_color=colores["text_on_accent"] if self._tab_der == 'propuestas' else colores["text_primary"],
            command=_ir_propuestas, **_btn_kw
        )
        btn_prop.pack(side="left", fill="y")

        self._construir_tab_hoy(frame_hoy)
        self._construir_tab_stats(frame_stats)
        self._construir_tab_propuestas(frame_propuestas)

        if self._tab_der == 'stats':
            frame_stats.pack(fill="both", expand=True)
        elif self._tab_der == 'propuestas':
            frame_propuestas.pack(fill="both", expand=True)
        else:
            frame_hoy.pack(fill="both", expand=True)

    def _construir_tab_hoy(self, parent):
        self._construir_progreso(parent)
        self._construir_cat_breakdown(parent)
        self._construir_notas_dia(parent)

    def _construir_tab_stats(self, parent):
        self._construir_historial_semanal(parent)
        self._construir_stats_30dias(parent)

    def _construir_tab_propuestas(self, parent):
        colores = COLORS[self.modo]

        conn = obtener_conexion()
        row_animo = conn.execute(
            "SELECT puntaje FROM termometro ORDER BY fecha DESC, hora DESC LIMIT 1"
        ).fetchone()
        puntaje = row_animo["puntaje"] if row_animo else None

        if puntaje is not None:
            actividades = conn.execute(
                "SELECT * FROM activacion_actividades "
                "WHERE activa=1 AND animo_min<=? AND animo_max>=? "
                "ORDER BY dificultad ASC, nombre ASC",
                (puntaje, puntaje)
            ).fetchall()
        else:
            actividades = conn.execute(
                "SELECT * FROM activacion_actividades WHERE activa=1 "
                "ORDER BY dificultad ASC, nombre ASC"
            ).fetchall()
        conn.close()

        card_top = CardFrame(parent, modo=self.modo)
        card_top.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        lbl_ctx = (f"Ánimo: {puntaje}/10  ·  {len(actividades)} propuestas"
                   if puntaje is not None
                   else f"Sin medición  ·  {len(actividades)} actividades")
        ctk.CTkLabel(
            card_top, text=lbl_ctx,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["text_secondary"]
        ).pack(padx=LAYOUT["padding_card"], pady=8, anchor="w")

        card_list = CardFrame(parent, modo=self.modo)
        card_list.pack(fill="both", expand=True)

        if not actividades:
            ctk.CTkLabel(
                card_list,
                text="Sin actividades para\ntu nivel de ánimo actual",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"],
                justify="center"
            ).pack(pady=20, padx=LAYOUT["padding_card"])
            return

        scroll = ctk.CTkScrollableFrame(
            card_list, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        scroll.pack(fill="both", expand=True, padx=6, pady=6)

        def _marcar_hecha(nombre_act, btn_ref):
            _p = puntaje if puntaje is not None else 5
            ahora = datetime.now()
            conn2 = obtener_conexion()
            try:
                conn2.execute(
                    "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) "
                    "VALUES (?, ?, ?, ?, ?, 'hecha')",
                    (ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), _p, _p, nombre_act)
                )
                conn2.commit()
            except Exception:
                pass
            conn2.close()
            try:
                from shared.sync import sync_inmediato_background as _sib
                _sib()
            except Exception:
                pass
            btn_ref.configure(text="✓", state="disabled",
                              fg_color=colores["success"],
                              hover_color=colores["success"])

        for act in actividades:
            nombre = act["nombre"]
            cat    = act.get("categoria", "Autocuidado")
            dur    = act.get("duracion_min", 10)
            desc   = act.get("descripcion", "") or ""

            fila = ctk.CTkFrame(
                scroll, fg_color=colores["bg_list_item"],
                corner_radius=LAYOUT["radius_button"]
            )
            fila.pack(fill="x", pady=3)

            top_row = ctk.CTkFrame(fila, fg_color="transparent")
            top_row.pack(fill="x", padx=8, pady=(6, 2))

            ctk.CTkLabel(
                top_row, text=nombre,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                text_color=colores["text_primary"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                top_row, text=cat, width=72, height=18,
                fg_color=_CAT_COLOR.get(cat, "#3A6EA5"),
                corner_radius=4, text_color="#FFFFFF",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"])
            ).pack(side="right")

            if desc:
                ctk.CTkLabel(
                    fila,
                    text=desc[:72] + ("…" if len(desc) > 72 else ""),
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    text_color=colores["text_secondary"],
                    anchor="w", wraplength=210
                ).pack(fill="x", padx=8, pady=(0, 2))

            bot_row = ctk.CTkFrame(fila, fg_color="transparent")
            bot_row.pack(fill="x", padx=8, pady=(0, 6))

            ctk.CTkLabel(
                bot_row, text=f"{dur} min",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(side="left")

            btn = ctk.CTkButton(
                bot_row, text="Hecha", width=58, height=24,
                fg_color=colores["accent"],
                hover_color=colores["accent_hover"],
                text_color=colores["text_on_accent"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold")
            )
            btn.configure(command=lambda n=nombre, b=btn: _marcar_hecha(n, b))
            btn.pack(side="right")

    def _construir_progreso(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="Progreso de hoy",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8), anchor="w")

        self.canvas_progreso = tk.Canvas(
            card, bg=colores["bg_surface"], highlightthickness=0,
            width=160, height=160
        )
        self.canvas_progreso.pack(pady=(0, 8))

        racha = self._calcular_racha()
        self.lbl_racha = ctk.CTkLabel(
            card, text=f"Seguimiento: {racha} día{'s' if racha != 1 else ''}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["accent"]
        )
        self.lbl_racha.pack(pady=(0, LAYOUT["padding_card"]))

        self._dibujar_progreso()

    def _dibujar_progreso(self):
        canvas = self.canvas_progreso
        canvas.delete("all")
        colores = COLORS[self.modo]

        hoy = fecha_hoy()
        conn = obtener_conexion()
        total_tareas = conn.execute("SELECT COUNT(*) as c FROM checklist_tareas").fetchone()["c"]
        completadas = conn.execute(
            "SELECT COUNT(*) as c FROM checklist_completadas WHERE fecha = ?", (hoy,)
        ).fetchone()["c"]
        conn.close()

        porcentaje = min(completadas / max(total_tareas, 1), 1.0)

        cx, cy = 80, 80
        radio = 65
        grosor = 12

        canvas.create_oval(
            cx - radio, cy - radio, cx + radio, cy + radio,
            outline=colores["progress_track"], width=grosor
        )

        if porcentaje > 0:
            angulo = porcentaje * 360
            _arc_color = colores["success"] if self.modo == "light" else colores["accent"]
            if porcentaje >= 1.0:
                canvas.create_oval(
                    cx - radio, cy - radio, cx + radio, cy + radio,
                    outline=_arc_color, width=grosor
                )
            else:
                canvas.create_arc(
                    cx - radio, cy - radio, cx + radio, cy + radio,
                    start=90, extent=-angulo,
                    outline=_arc_color, width=grosor, style="arc"
                )

        texto_pct = f"{int(porcentaje * 100)}%"
        canvas.create_text(
            cx, cy, text=texto_pct,
            fill=colores["text_primary"],
            font=(TYPOGRAPHY["font_family"], 20, "bold")
        )
        canvas.create_text(
            cx, cy + 20, text=f"{completadas}/{total_tareas}",
            fill=colores["text_tertiary"],
            font=(TYPOGRAPHY["font_family"], 10)
        )

    def _construir_cat_breakdown(self, parent):
        colores = COLORS[self.modo]
        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="Por categoría",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4), anchor="w")

        self.canvas_cat = tk.Canvas(
            card, bg=colores["bg_surface"], highlightthickness=0, height=88
        )
        self.canvas_cat.pack(fill="x", padx=LAYOUT["padding_card"],
                             pady=(0, LAYOUT["padding_card"]))
        self.canvas_cat.bind("<Configure>", lambda e: self._dibujar_cat_breakdown())
        self._dibujar_cat_breakdown()

    def _dibujar_cat_breakdown(self):
        if not hasattr(self, 'canvas_cat'):
            return
        try:
            if not self.canvas_cat.winfo_exists():
                return
        except Exception:
            return
        canvas = self.canvas_cat
        canvas.delete("all")
        colores = COLORS[self.modo]

        hoy = fecha_hoy()
        conn = obtener_conexion()
        tot_rows = conn.execute(
            "SELECT COALESCE(categoria, 'Logro') as cat, COUNT(*) as n "
            "FROM checklist_tareas GROUP BY cat"
        ).fetchall()
        totales = {r["cat"]: r["n"] for r in tot_rows}
        comp_rows = conn.execute(
            "SELECT COALESCE(ct.categoria, 'Logro') as cat, COUNT(*) as n "
            "FROM checklist_completadas cc "
            "JOIN checklist_tareas ct ON cc.tarea_id = ct.id "
            "WHERE cc.fecha=? GROUP BY ct.categoria",
            (hoy,)
        ).fetchall()
        completadas_cat = {r["cat"]: r["n"] for r in comp_rows}
        conn.close()

        cats = ["Logro", "Placer", "Autocuidado", "Social"]
        row_h = 18
        y_pad = 5
        w = canvas.winfo_width() or 240

        for i, cat in enumerate(cats):
            total = totales.get(cat, 0)
            comp  = completadas_cat.get(cat, 0)
            pct   = min(comp / max(total, 1), 1.0) if total > 0 else 0
            y = y_pad + i * (row_h + y_pad)

            canvas.create_text(
                4, y + row_h // 2, text=cat, anchor="w",
                fill=colores["text_secondary"], font=("Segoe UI", 9)
            )
            bar_x = 84
            bar_w = w - bar_x - 36
            canvas.create_rectangle(
                bar_x, y + 4, bar_x + bar_w, y + row_h - 4,
                fill=colores["progress_track"], outline=""
            )
            if pct > 0 and total > 0:
                canvas.create_rectangle(
                    bar_x, y + 4, bar_x + max(bar_w * pct, 4), y + row_h - 4,
                    fill=_CAT_COLOR.get(cat, "#3A6EA5"), outline=""
                )
            label = f"{comp}/{total}" if total > 0 else "—"
            canvas.create_text(
                w - 2, y + row_h // 2, text=label, anchor="e",
                fill=colores["text_secondary"], font=("Segoe UI", 8)
            )

    def _construir_historial_semanal(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x")

        header_sem = ctk.CTkFrame(card, fg_color="transparent")
        header_sem.pack(fill="x", padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4))

        ctk.CTkButton(
            header_sem, text="←", width=28, height=26,
            fg_color="transparent", hover_color=colores["bg_hover"],
            text_color=colores["text_primary"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], 14, "bold"),
            command=self._semana_anterior
        ).pack(side="left")

        offset = self._semana_offset
        titulo = ("Última semana" if offset == 0
                  else "Semana anterior" if offset == -1
                  else f"Hace {abs(offset)} semanas")
        self.lbl_semana_titulo = ctk.CTkLabel(
            header_sem, text=titulo,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["text_primary"]
        )
        self.lbl_semana_titulo.pack(side="left", padx=4)

        self.btn_semana_sig = ctk.CTkButton(
            header_sem, text="→", width=28, height=26,
            fg_color="transparent",
            hover_color=colores["bg_hover"] if offset < 0 else colores["bg_surface"],
            text_color=colores["text_secondary"] if offset < 0 else colores["progress_track"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], 14, "bold"),
            command=self._semana_siguiente
        )
        self.btn_semana_sig.pack(side="left")

        self.canvas_semana = tk.Canvas(
            card, bg=colores["bg_surface"], highlightthickness=0,
            height=115
        )
        self.canvas_semana.pack(fill="x", padx=LAYOUT["padding_card"],
                                pady=(0, 4))
        self.canvas_semana.bind("<Configure>", lambda e: self._dibujar_semana())
        self.canvas_semana.bind("<Button-1>", self._on_click_semana)
        self.canvas_semana.bind("<Motion>", self._on_motion_semana)

        ctk.CTkLabel(
            card, text="Tocá una barra para ver el detalle del día",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["text_tertiary"]
        ).pack(pady=(0, LAYOUT["padding_card"]))

        self._dibujar_semana()

    def _dibujar_semana(self):
        canvas = self.canvas_semana
        canvas.delete("all")
        colores = COLORS[self.modo]

        hoy = datetime.now().date()
        base_date = hoy + timedelta(weeks=getattr(self, '_semana_offset', 0))

        conn = obtener_conexion()
        total_actual = max(conn.execute("SELECT COUNT(*) as c FROM checklist_tareas").fetchone()["c"], 1)

        datos = []
        dias_nombres = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]

        for i in range(6, -1, -1):
            dia = base_date - timedelta(days=i)
            fecha_str = dia.isoformat()
            completadas = conn.execute(
                "SELECT COUNT(*) as c FROM checklist_completadas WHERE fecha = ?", (fecha_str,)
            ).fetchone()["c"]
            snap = conn.execute(
                "SELECT total_tareas FROM checklist_snapshot WHERE fecha = ?", (fecha_str,)
            ).fetchone()
            total = max(snap["total_tareas"], 1) if snap else total_actual
            pct = min(completadas / total, 1.0)
            datos.append((dias_nombres[dia.weekday()], pct, completadas, dia == hoy, dia))
        conn.close()

        self._barras_semana = []
        w = canvas.winfo_width() or 240
        ancho_barra = 24
        gap = (w - len(datos) * ancho_barra) / (len(datos) + 1)

        for i, (nombre, pct, completadas, es_hoy, dia) in enumerate(datos):
            x = gap + i * (ancho_barra + gap)
            alto_max = 60
            y_base = 72

            if completadas > 0:
                alto = max(alto_max * pct, 3)
                y_top = y_base - alto
                _accent = colores["success"] if self.modo == "light" else colores["accent"]
                color = _accent if pct >= 0.8 else colores["warning"] if pct >= 0.4 else colores["progress_track"]
                if es_hoy:
                    color = _accent
                canvas.create_rectangle(
                    x, y_top, x + ancho_barra, y_base,
                    fill=color, outline=""
                )
            self._barras_semana.append((dia.isoformat(), x, 0, x + ancho_barra, y_base + 30))

            color_lbl = colores["accent"] if es_hoy else colores["text_tertiary"]
            canvas.create_text(
                x + ancho_barra / 2, y_base + 10, text=nombre,
                fill=color_lbl, font=("Segoe UI", 9, "bold" if es_hoy else "normal")
            )
            canvas.create_text(
                x + ancho_barra / 2, y_base + 23,
                text=f"{dia.day}/{dia.month}",
                fill=color_lbl, font=("Segoe UI", 8)
            )

    def _toggle_tarea(self, tarea_id, var):
        marcado = var.get()
        hoy = fecha_hoy()
        conn = obtener_conexion()
        if marcado:
            try:
                conn.execute(
                    "INSERT INTO checklist_completadas (tarea_id, fecha) VALUES (?, ?)",
                    (tarea_id, hoy)
                )
                conn.commit()
                self._reproducir_logro()
                try:
                    from shared.sync import sync_inmediato_background as _sib
                    _sib()
                except Exception:
                    pass
            except Exception:
                pass
        else:
            conn.execute(
                "DELETE FROM checklist_completadas WHERE tarea_id=? AND fecha=?",
                (tarea_id, hoy)
            )
            conn.commit()
        conn.close()
        self._cargar_tareas()
        self._dibujar_progreso()
        self._dibujar_cat_breakdown()
        self._dibujar_semana()
        if marcado:
            self._verificar_celebracion()

    def _agregar_tarea_manual(self):
        desc = getattr(self, '_entry_nueva_tarea', None)
        if not desc:
            return
        texto = desc.get().strip()
        if not texto:
            return
        conn = obtener_conexion()
        max_orden = conn.execute(
            "SELECT COALESCE(MAX(orden), 0) FROM checklist_tareas WHERE seccion = ?",
            (self.seccion_activa,)
        ).fetchone()[0]
        try:
            conn.execute(
                "INSERT INTO checklist_tareas (seccion, descripcion, orden, categoria, origen) "
                "VALUES (?, ?, ?, 'Logro', 'paciente')",
                (self.seccion_activa, texto, max_orden + 1)
            )
            conn.commit()
        except Exception:
            pass
        conn.close()
        desc.delete(0, "end")
        self._cargar_tareas()

    def _eliminar_tarea(self, tarea_id):
        conn = obtener_conexion()
        conn.execute("DELETE FROM checklist_tareas WHERE id = ?", (tarea_id,))
        conn.commit()
        conn.close()
        self._guardar_snapshot_hoy()
        self._cargar_tareas()
        self._dibujar_progreso()

    def _reproducir_logro(self):
        if not SONIDO_DISPONIBLE:
            return
        try:
            import numpy as np
            sr = 44100
            dur = 0.4
            t = np.linspace(0, dur, int(sr * dur), False)
            wave = (
                np.sin(2 * 3.14159 * 880 * t) * np.exp(-t * 5.0) * 0.7 +
                np.sin(2 * 3.14159 * 1760 * t) * np.exp(-t * 8.0) * 0.3
            )
            fi = int(sr * 0.01)
            wave[:fi] *= np.linspace(0, 1, fi)
            wave = (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)
            stereo = np.column_stack((wave, wave))
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
        except Exception:
            pass

    def _calcular_racha(self) -> int:
        hoy = datetime.now().date()
        conn = obtener_conexion()
        total_tareas = max(conn.execute("SELECT COUNT(*) as c FROM checklist_tareas").fetchone()["c"], 1)
        hace_365 = (hoy - timedelta(days=364)).isoformat()
        rows = conn.execute(
            "SELECT fecha, COUNT(*) as c FROM checklist_completadas WHERE fecha >= ? GROUP BY fecha",
            (hace_365,)
        ).fetchall()
        conn.close()

        conteos = {r["fecha"]: r["c"] for r in rows}
        racha = 0
        for i in range(365):
            dia = hoy - timedelta(days=i)
            completadas = conteos.get(dia.isoformat(), 0)
            if completadas / total_tareas >= 0.7:
                racha += 1
            else:
                if i > 0:
                    break
        return racha

    def _construir_stats_30dias(self, parent):
        colores = COLORS[self.modo]
        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(LAYOUT["gap_cards"], 0))

        ctk.CTkLabel(
            card, text="Últimos 30 días",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 6), anchor="w")

        stats = self._calcular_stats_30dias()
        racha = self._calcular_racha()
        datos = [
            ("Promedio diario",    f"{stats['pct_promedio']}%"),
            ("Días completados",   f"{stats['dias_completos']} / 30"),
            ("Categoría top",      stats['cat_top'] or "—"),
            ("Seguimiento actual", f"{racha} día{'s' if racha != 1 else ''}"),
        ]
        for lbl, val in datos:
            fila = ctk.CTkFrame(card, fg_color="transparent")
            fila.pack(fill="x", padx=LAYOUT["padding_card"], pady=2)
            ctk.CTkLabel(
                fila, text=lbl,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_secondary"]
            ).pack(side="left")
            ctk.CTkLabel(
                fila, text=val,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
                text_color=colores["text_primary"]
            ).pack(side="right")

        ctk.CTkFrame(card, fg_color="transparent", height=LAYOUT["padding_card"]).pack()

    def _calcular_stats_30dias(self) -> dict:
        from datetime import date as _date, timedelta as _td
        hoy  = _date.today()
        hace_30 = (hoy - _td(days=29)).isoformat()

        conn = obtener_conexion()
        total_act = max(conn.execute(
            "SELECT COUNT(*) as c FROM checklist_tareas"
        ).fetchone()["c"], 1)

        filas = conn.execute(
            "SELECT fecha, COUNT(*) as c FROM checklist_completadas "
            "WHERE fecha >= ? GROUP BY fecha", (hace_30,)
        ).fetchall()

        pcts = []
        dias_completos = 0
        for r in filas:
            snap = conn.execute(
                "SELECT total_tareas FROM checklist_snapshot WHERE fecha=?", (r["fecha"],)
            ).fetchone()
            total = snap["total_tareas"] if snap else total_act
            pct = min(r["c"] / max(total, 1), 1.0)
            pcts.append(pct)
            if pct >= 0.7:
                dias_completos += 1

        row_cat = conn.execute(
            "SELECT COALESCE(ct.categoria, 'Logro') as cat, COUNT(*) as n "
            "FROM checklist_completadas cc "
            "JOIN checklist_tareas ct ON cc.tarea_id = ct.id "
            "WHERE cc.fecha >= ? GROUP BY cat ORDER BY n DESC LIMIT 1",
            (hace_30,)
        ).fetchone()
        conn.close()

        return {
            "pct_promedio":   round(sum(pcts) / len(pcts) * 100) if pcts else 0,
            "dias_completos": dias_completos,
            "cat_top":        row_cat["cat"] if row_cat else None,
        }

    def _verificar_cambio_dia(self):
        hoy = fecha_hoy()
        if hoy != self._fecha_actual:
            self._fecha_actual = hoy
            self._guardar_snapshot_hoy()
            self._cargar_tareas()
            self._dibujar_progreso()
            self._dibujar_cat_breakdown()
            self._dibujar_semana()
        self.after(60000, self._verificar_cambio_dia)

    def _guardar_snapshot_hoy(self):
        hoy = fecha_hoy()
        conn = obtener_conexion()
        total = conn.execute("SELECT COUNT(*) as c FROM checklist_tareas").fetchone()["c"]
        conn.execute(
            "INSERT OR REPLACE INTO checklist_snapshot (fecha, total_tareas) VALUES (?, ?)",
            (hoy, total)
        )
        conn.commit()
        conn.close()

    def _semana_anterior(self):
        self._semana_offset -= 1
        self._actualizar_nav_semana()
        self._dibujar_semana()

    def _semana_siguiente(self):
        if self._semana_offset < 0:
            self._semana_offset += 1
            self._actualizar_nav_semana()
            self._dibujar_semana()

    def _actualizar_nav_semana(self):
        if not hasattr(self, 'lbl_semana_titulo'):
            return
        colores = COLORS[self.modo]
        offset = self._semana_offset
        if offset == 0:
            texto = "Última semana"
        elif offset == -1:
            texto = "Semana anterior"
        else:
            texto = f"Hace {abs(offset)} semanas"
        self.lbl_semana_titulo.configure(text=texto)
        if hasattr(self, 'btn_semana_sig'):
            if offset < 0:
                self.btn_semana_sig.configure(
                    text_color=colores["text_secondary"],
                    hover_color=colores["bg_hover"]
                )
            else:
                self.btn_semana_sig.configure(
                    text_color=colores["progress_track"],
                    hover_color=colores["bg_surface"]
                )

    def _on_click_semana(self, event):
        if not hasattr(self, '_barras_semana'):
            return
        mx, my = event.x, event.y
        for fecha_str, x0, y0, x1, y1 in self._barras_semana:
            if x0 <= mx <= x1 and y0 <= my <= y1:
                self._mostrar_detalle_dia(fecha_str)
                return

    def _on_motion_semana(self, event):
        if not hasattr(self, '_barras_semana'):
            return
        for _, x0, y0, x1, y1 in self._barras_semana:
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                self.canvas_semana.configure(cursor="hand2")
                return
        self.canvas_semana.configure(cursor="")

    def _mostrar_detalle_dia(self, fecha_str):
        colores = COLORS[self.modo]
        conn = obtener_conexion()
        completadas = conn.execute(
            """SELECT COALESCE(ct.descripcion, '(tarea eliminada)') as descripcion,
                      COALESCE(ct.seccion, 'manana') as seccion
               FROM checklist_completadas cc
               LEFT JOIN checklist_tareas ct ON cc.tarea_id = ct.id
               WHERE cc.fecha = ?
               ORDER BY cc.id""",
            (fecha_str,)
        ).fetchall()
        snap = conn.execute(
            "SELECT total_tareas FROM checklist_snapshot WHERE fecha = ?", (fecha_str,)
        ).fetchone()
        total_ese_dia = (snap["total_tareas"] if snap
                         else conn.execute("SELECT COUNT(*) as c FROM checklist_tareas").fetchone()["c"])
        conn.close()

        try:
            dt = datetime.fromisoformat(fecha_str)
            dias_completos = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            titulo_fecha = f"{dias_completos[dt.weekday()]} {dt.day}/{dt.month}/{dt.year}"
        except Exception:
            titulo_fecha = fecha_str

        win = NMToplevel(self, modo=self.modo)
        win.title(f"Tareas · {titulo_fecha}")
        _w, _h = 360, 420
        _sw = win.winfo_screenwidth()
        _sh = win.winfo_screenheight()
        win.geometry(f"{_w}x{_h}+{(_sw - _w) // 2}+{(_sh - _h) // 2}")
        win.configure(fg_color=colores["bg_primary"])
        win.resizable(False, False)
        win.grab_set()
        win.after(10, win.focus_force)

        frame = ctk.CTkFrame(win, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=LAYOUT["padding_card"], pady=LAYOUT["padding_card"])

        ctk.CTkLabel(
            frame, text=titulo_fecha,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(anchor="w", pady=(0, 4))

        n_comp = len(completadas)
        pct = int(n_comp / max(total_ese_dia, 1) * 100)
        ctk.CTkLabel(
            frame, text=f"{n_comp} de {total_ese_dia} tareas  ·  {pct}%",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(anchor="w", pady=(0, 12))

        if not completadas:
            ctk.CTkLabel(
                frame, text="Sin tareas completadas ese día",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
        else:
            secciones_nombres = {"manana": "Mañana", "tarde": "Tarde", "noche": "Noche"}
            seccion_actual = None
            scroll = ctk.CTkScrollableFrame(
                frame, fg_color="transparent",
                scrollbar_button_color=colores["bg_hover"],
                scrollbar_button_hover_color=colores["accent"]
            )
            scroll.pack(fill="both", expand=True)
            for reg in completadas:
                if reg["seccion"] != seccion_actual:
                    seccion_actual = reg["seccion"]
                    ctk.CTkLabel(
                        scroll,
                        text=secciones_nombres.get(seccion_actual, seccion_actual),
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                        text_color=colores["accent"]
                    ).pack(anchor="w", pady=(8, 2))
                ctk.CTkLabel(
                    scroll, text=f"✓  {reg['descripcion']}",
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                    text_color=colores["success"],
                    anchor="w"
                ).pack(anchor="w", padx=8, pady=2)

        _kw_cerrar = {"fg_color": colores["success"], "hover_color": "#4A8A70"} if self.modo == "light" else {}
        BotonPrimario(
            frame, text="Cerrar", modo=self.modo, width=100,
            command=win.destroy, **_kw_cerrar
        ).pack(pady=(12, 0))

    def _verificar_celebracion(self):
        if getattr(self, '_celebracion_mostrada_hoy', '') == fecha_hoy():
            return
        hoy = fecha_hoy()
        conn = obtener_conexion()
        total = conn.execute("SELECT COUNT(*) as c FROM checklist_tareas").fetchone()["c"]
        completadas = conn.execute(
            "SELECT COUNT(*) as c FROM checklist_completadas WHERE fecha=?", (hoy,)
        ).fetchone()["c"]
        conn.close()
        if total > 0 and completadas >= total:
            self._celebracion_mostrada_hoy = hoy
            self._mostrar_celebracion()

    def _mostrar_celebracion(self):
        colores = COLORS[self.modo]
        win = NMToplevel(self, modo=self.modo)
        win.title("¡Día completado!")
        _w, _h = 320, 220
        win.geometry(f"{_w}x{_h}+{(win.winfo_screenwidth() - _w) // 2}+{(win.winfo_screenheight() - _h) // 2}")
        win.resizable(False, False)
        win.grab_set()
        win.after(10, win.focus_force)

        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            f, text="¡Completaste el día!",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["success"]
        ).pack(pady=(0, 8))

        _mensajes = [
            "Cada pequeño paso construye el camino.",
            "Tu constancia es tu mayor fortaleza.",
            "Hoy fue un buen día. Lo lograste.",
            "La estructura es una forma de cuidarte.",
            "Momento a momento, día a día.",
        ]
        ctk.CTkLabel(
            f, text=random.choice(_mensajes),
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"],
            wraplength=260
        ).pack(pady=(0, 16))

        _kw_cel = {"fg_color": colores["success"], "hover_color": "#4A8A70"} if self.modo == "light" else {}
        BotonPrimario(
            f, text="¡Gracias!", modo=self.modo, width=120,
            command=win.destroy, **_kw_cel
        ).pack()
        win.after(6000, lambda: win.destroy() if win.winfo_exists() else None)

    def _construir_notas_dia(self, parent):
        colores = COLORS[self.modo]
        from shared.components import CardFrame
        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="Nota del día",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4), anchor="w")

        self.txt_nota = ctk.CTkTextbox(
            card, height=56, wrap="word",
            fg_color=colores["bg_input"],
            border_color=colores["border"],
            border_width=1,
            text_color=colores["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            corner_radius=LAYOUT["radius_input"]
        )
        self.txt_nota.pack(fill="x", padx=LAYOUT["padding_card"],
                           pady=(0, LAYOUT["padding_card"]))

        hoy = fecha_hoy()
        conn = obtener_conexion()
        row = conn.execute(
            "SELECT nota FROM checklist_notas_dia WHERE fecha=?", (hoy,)
        ).fetchone()
        conn.close()
        if row and row["nota"]:
            self.txt_nota.insert("end", row["nota"])

        self.txt_nota.bind("<FocusOut>", lambda e: self._guardar_nota())

    def _guardar_nota(self):
        if not hasattr(self, 'txt_nota'):
            return
        try:
            nota = self.txt_nota.get("1.0", "end").strip()
            hoy = fecha_hoy()
            conn = obtener_conexion()
            conn.execute(
                "INSERT OR REPLACE INTO checklist_notas_dia (fecha, nota) VALUES (?,?)",
                (hoy, nota)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _cambiar_seccion(self, seccion):
        if self.seccion_activa == seccion:
            return
        self.seccion_activa = seccion
        estado = self.state()
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        if estado == "zoomed":
            self.state("zoomed")

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
        estado = self.state()
        self.modo = nuevo_modo
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")

    def _toggle_modo(self):
        estado = self.state()
        self.modo = "light" if self.modo == "dark" else "dark"
        guardar_config("theme", self.modo)
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = ChecklistApp()
    app.mainloop()
