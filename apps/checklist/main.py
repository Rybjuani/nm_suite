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
from datetime import datetime, timedelta
from tkinter import messagebox

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    InputTexto, mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido, NMToplevel,
    aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy

try:
    import pygame
    pygame.mixer.init()
    SONIDO_DISPONIBLE = True
except Exception:
    SONIDO_DISPONIBLE = False


SECCIONES = [("manana", "Mañana"), ("tarde", "Tarde"), ("noche", "Noche")]


class ChecklistApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()
        self.modo = "dark"
        self.seccion_activa = "manana"
        self._entrada_temp = ""
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
            subtitulo="Estructura tu día para mayor bienestar",
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
        self._construir_progreso(col_der)
        self._construir_historial_semanal(col_der)

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
                fg_color=colores["accent"] if es_activa else colores["bg_hover"],
                hover_color=colores["accent_hover"],
                text_color=colores["text_on_accent"] if es_activa else colores["text_primary"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"],
                      "bold" if es_activa else "normal"),
                command=lambda c=clave: self._cambiar_seccion(c)
            ).pack(side="left", padx=4, fill="y")

    def _construir_tareas(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        agregar_frame = ctk.CTkFrame(card, fg_color="transparent")
        agregar_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=LAYOUT["padding_card"])

        self.entry_nueva = InputTexto(
            agregar_frame, modo=self.modo,
            placeholder_text="Nueva tarea..."
        )
        self.entry_nueva.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_nueva.bind("<Return>", lambda e: self._agregar_tarea())
        if self._entrada_temp:
            self.entry_nueva.insert(0, self._entrada_temp)

        BotonPrimario(
            agregar_frame, text="+", modo=self.modo, width=44,
            command=self._agregar_tarea
        ).pack(side="right")

        self.frame_tareas = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_tareas.pack(fill="both", expand=True, padx=LAYOUT["padding_card"],
                               pady=(0, LAYOUT["padding_card"]))

        self._cargar_tareas()

    def _cargar_tareas(self):
        for widget in self.frame_tareas.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        hoy = fecha_hoy()

        conn = obtener_conexion()
        tareas = conn.execute(
            "SELECT id, descripcion, orden FROM checklist_tareas WHERE seccion = ? ORDER BY orden",
            (self.seccion_activa,)
        ).fetchall()

        completadas_hoy = set()
        rows = conn.execute(
            "SELECT tarea_id FROM checklist_completadas WHERE fecha = ?", (hoy,)
        ).fetchall()
        for r in rows:
            completadas_hoy.add(r["tarea_id"])
        conn.close()

        if not tareas:
            ctk.CTkLabel(
                self.frame_tareas, text="Sin tareas en esta sección",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        for tarea in tareas:
            esta_completada = tarea["id"] in completadas_hoy
            fila = ctk.CTkFrame(
                self.frame_tareas,
                fg_color=colores["bg_hover"],
                corner_radius=LAYOUT["radius_button"]
            )
            fila.pack(fill="x", pady=3)

            var_check = ctk.BooleanVar(value=esta_completada)
            tarea_id = tarea["id"]

            cb = ctk.CTkCheckBox(
                fila, text=tarea["descripcion"],
                variable=var_check,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["success"] if esta_completada else colores["text_primary"],
                fg_color=colores["success"],
                hover_color=colores["success"] if esta_completada else colores["accent_hover"],
                border_color=colores["text_tertiary"],
                checkmark_color=colores["text_on_accent"],
                command=lambda tid=tarea_id, v=var_check: self._toggle_tarea(tid, v)
            )
            cb.pack(side="left", padx=12, pady=10)

            if not esta_completada:
                ctk.CTkButton(
                    fila, text="Cancelar", height=28,
                    fg_color="transparent",
                    hover_color=colores["error"],
                    text_color=colores["text_tertiary"],
                    corner_radius=LAYOUT["radius_button"],
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    command=lambda tid=tarea_id: self._eliminar_tarea(tid)
                ).pack(side="right", padx=8)

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
            width=200, height=200
        )
        self.canvas_progreso.pack(pady=(0, 8))

        racha = self._calcular_racha()
        self.lbl_racha = ctk.CTkLabel(
            card, text=f"Racha: {racha} día{'s' if racha != 1 else ''}",
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

        cx, cy = 100, 100
        radio = 80
        grosor = 14

        canvas.create_oval(
            cx - radio, cy - radio, cx + radio, cy + radio,
            outline=colores["progress_track"], width=grosor
        )

        if porcentaje > 0:
            angulo = porcentaje * 360
            canvas.create_arc(
                cx - radio, cy - radio, cx + radio, cy + radio,
                start=90, extent=angulo,
                outline=colores["accent"], width=grosor, style="arc"
            )

        texto_pct = f"{int(porcentaje * 100)}%"
        canvas.create_text(
            cx, cy, text=texto_pct,
            fill=colores["text_primary"],
            font=(TYPOGRAPHY["font_family"], 24, "bold")
        )
        canvas.create_text(
            cx, cy + 25, text=f"{completadas}/{total_tareas}",
            fill=colores["text_tertiary"],
            font=(TYPOGRAPHY["font_family"], 11)
        )

    def _construir_historial_semanal(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        header_sem = ctk.CTkFrame(card, fg_color="transparent")
        header_sem.pack(fill="x", padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4))

        ctk.CTkButton(
            header_sem, text="←", width=28, height=26,
            fg_color="transparent", hover_color=colores["bg_hover"],
            text_color=colores["text_primary"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], 14),
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
            font=(TYPOGRAPHY["font_family"], 14),
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
                color = colores["accent"] if pct >= 0.8 else colores["warning"] if pct >= 0.4 else colores["progress_track"]
                if es_hoy:
                    color = colores["accent"]
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

    def _agregar_tarea(self):
        texto = self.entry_nueva.get().strip()
        if not texto:
            return

        conn = obtener_conexion()
        max_orden = conn.execute(
            "SELECT COALESCE(MAX(orden), 0) as m FROM checklist_tareas WHERE seccion = ?",
            (self.seccion_activa,)
        ).fetchone()["m"]

        conn.execute(
            "INSERT INTO checklist_tareas (seccion, descripcion, orden) VALUES (?, ?, ?)",
            (self.seccion_activa, texto, max_orden + 1)
        )
        conn.commit()
        conn.close()

        self.entry_nueva.delete(0, "end")
        self._guardar_snapshot_hoy()
        self._cargar_tareas()
        self._dibujar_progreso()

    def _toggle_tarea(self, tarea_id, var):
        if not var.get():
            var.set(True)
            return
        hoy = fecha_hoy()
        conn = obtener_conexion()
        try:
            conn.execute(
                "INSERT INTO checklist_completadas (tarea_id, fecha) VALUES (?, ?)",
                (tarea_id, hoy)
            )
            self._reproducir_logro()
        except Exception:
            pass
        conn.commit()
        conn.close()
        self._cargar_tareas()
        self._dibujar_progreso()
        self._dibujar_semana()

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
            sample_rate = 44100
            duracion = 0.15
            t = np.linspace(0, duracion, int(sample_rate * duracion), False)
            wave = np.sin(2 * 3.14159 * 1200 * t) * 0.2
            wave = (wave * 32767).astype(np.int16)
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

    def _verificar_cambio_dia(self):
        hoy = fecha_hoy()
        if hoy != self._fecha_actual:
            self._fecha_actual = hoy
            self._guardar_snapshot_hoy()
            self._cargar_tareas()
            self._dibujar_progreso()
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

        BotonPrimario(
            frame, text="Cerrar", modo=self.modo, width=100,
            command=win.destroy
        ).pack(pady=(12, 0))

    def _cambiar_seccion(self, seccion):
        if self.seccion_activa == seccion:
            return
        self._entrada_temp = self.entry_nueva.get().strip() if hasattr(self, 'entry_nueva') else ""
        self.seccion_activa = seccion
        estado = self.state()
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        if estado == "zoomed":
            self.state("zoomed")

    def _toggle_modo(self):
        estado = self.state()
        self._entrada_temp = self.entry_nueva.get().strip() if hasattr(self, 'entry_nueva') else ""
        self.modo = "light" if self.modo == "dark" else "dark"
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
