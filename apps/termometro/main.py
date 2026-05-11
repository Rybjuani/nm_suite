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
import calendar

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas, guardar_config, leer_config
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    AreaTexto, mostrar_acerca_de, mostrar_mensaje, obtener_ruta_recurso, obtener_icono_solido,
    aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy, hora_actual, fecha_legible, color_por_puntaje, color_por_puntaje_exacto

_activacion_dir = os.path.join(_base, "apps", "activacion")
if _activacion_dir not in sys.path:
    sys.path.insert(0, _activacion_dir)
try:
    import motor as _motor
    _MOTOR_OK = True
except Exception:
    _MOTOR_OK = False

try:
    from shared.sync import sync_al_abrir as _sync_al_abrir, sync_inmediato_background as _sync_inmediato
    _SYNC_OK = True
except Exception:
    _SYNC_OK = False


COLORES_PUNTAJE = {
    1: "#E96134", 2: "#EC762C", 3: "#EF8C24",
    4: "#F0A500", 5: "#EAB800", 6: "#C0C030", 7: "#7CBD50",
    8: "#3AAE70", 9: "#2BBF7A", 10: "#22D47E",
}


def _color_puntaje_hex(v: float) -> str:
    return COLORES_PUNTAJE.get(int(round(max(1, min(10, v)))), "#1EC8D4")


class TermometroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()

        if _SYNC_OK:
            _sync_al_abrir()

        self.modo = leer_config("theme", "dark")
        self.puntaje_actual = 5  # centro aproximado de la escala 1-10
        self._nota_temp = ""
        self._vista = "termometro"
        self.periodo_viz = 7

        self.title("NeuroMood · Termómetro Emocional")
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
            titulo="Termómetro Emocional",
            subtitulo="Registrá tu estado de ánimo diario",
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

        if self._vista == "termometro":
            self._construir_vista_termometro(contenido)
        else:
            self._construir_vista_visualizador(contenido)

    # ── Vista: Termómetro ─────────────────────────────────────────────────────

    def _construir_vista_termometro(self, parent):
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.pack(fill="both", expand=True)

        self._construir_termometro(col)
        self._construir_registro(col)

        colores = COLORS[self.modo]
        _kw_evol = {"fg_color": colores["info"], "hover_color": "#3A6E95", "border_width": 0} if self.modo == "light" else {}
        BotonSecundario(
            col, text="Ver evolución →", modo=self.modo, height=36,
            command=self._ir_visualizador, **_kw_evol
        ).pack(anchor="e", pady=(8, 0))

    def _construir_termometro(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="¿Cómo te sentís hoy?",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 2))

        ctk.CTkLabel(
            card,
            text="Podés registrar tu estado de ánimo las veces que quieras a lo largo del día.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"],
            justify="center"
        ).pack(padx=LAYOUT["padding_card"], pady=(0, 8))

        self.EMOJIS = ["😢", "😞", "😔", "😕", "😐", "🙂", "😊", "😄", "😁", "🤩"]

        emoji_frame = ctk.CTkFrame(card, fg_color="transparent")
        emoji_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=12)

        self.emoji_labels = []
        for i, emoji in enumerate(self.EMOJIS):
            lbl = ctk.CTkLabel(
                emoji_frame, text=emoji,
                font=(TYPOGRAPHY["font_family"], 20),
                width=36, height=36
            )
            lbl.pack(side="left", expand=True)
            self.emoji_labels.append(lbl)

        self._actualizar_emojis()

        self.lbl_puntaje = ctk.CTkLabel(
            card, text="5 — Neutral",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h2"], "bold"),
            text_color=color_por_puntaje(5, self.modo)
        )
        self.lbl_puntaje.pack(pady=(4, 8))

        slider_frame = ctk.CTkFrame(card, fg_color="transparent")
        slider_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))

        _sc = colores["success"] if self.modo == "light" else colores["accent"]
        self.slider = ctk.CTkSlider(
            slider_frame, from_=0, to=10, number_of_steps=10,
            progress_color=_sc,
            button_color=_sc,
            button_hover_color=colores["accent_hover"],
            fg_color=colores["progress_track"],
            command=self._on_slider_change
        )
        self.slider.set(self.puntaje_actual)
        self.slider.pack(fill="x")

    def _construir_registro(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="Nota (opcional)",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4), anchor="w")

        self.txt_nota = AreaTexto(card, modo=self.modo, height=60)
        self.txt_nota.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 12))
        if self._nota_temp:
            self.txt_nota.insert("1.0", self._nota_temp)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))

        _kw_reg = {"fg_color": colores["success"], "hover_color": "#4A8A70"} if self.modo == "light" else {}
        BotonPrimario(
            btn_frame, text="Registrar estado", modo=self.modo,
            command=self._registrar, **_kw_reg
        ).pack(side="left")

    # ── Vista: Visualizador ───────────────────────────────────────────────────

    def _ir_visualizador(self):
        self._vista = "visualizador"
        estado = self.state()
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        if estado == "zoomed":
            self.state("zoomed")

    def _volver_termometro(self):
        self._vista = "termometro"
        estado = self.state()
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.slider.set(self.puntaje_actual)
        self._on_slider_change(self.puntaje_actual)
        self.update_idletasks()
        _unfreeze_window(hwnd)
        if estado == "zoomed":
            self.state("zoomed")

    def _construir_vista_visualizador(self, parent):
        colores = COLORS[self.modo]

        # Fila de controles: ← Volver | período buttons
        ctrl_row = ctk.CTkFrame(parent, fg_color="transparent", height=44)
        ctrl_row.pack(fill="x", pady=(0, 8))
        ctrl_row.pack_propagate(False)

        _kw_volver = {"fg_color": colores["bg_hover"], "hover_color": colores["border"]} if self.modo == "light" else {}
        BotonSecundario(
            ctrl_row, text="← Volver", modo=self.modo, width=90, height=34,
            command=self._volver_termometro, **_kw_volver
        ).pack(side="left", padx=(0, 16))

        for texto, dias in [("7 días", 7), ("30 días", 30), ("Todo", None)]:
            activo = dias == self.periodo_viz
            ctk.CTkButton(
                ctrl_row, text=texto, height=34,
                fg_color=("#4A7EA5" if self.modo == "light" else colores["accent"]) if activo else ("#B5D0E8" if self.modo == "light" else colores["bg_hover"]),
                hover_color=("#3A6E95" if self.modo == "light" else colores["accent_hover"]) if activo else ("#9ABDD8" if self.modo == "light" else colores["accent_hover"]),
                text_color=(colores["text_on_accent"] if activo else "#1E4D78") if self.modo == "light" else colores["text_on_accent"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                command=lambda d=dias: self._viz_cambiar_periodo(d)
            ).pack(side="left", padx=4)

        # Datos
        grupos = self._viz_obtener_grupos()
        puntos = self._viz_calcular_puntos(grupos)
        stats = self._viz_calcular_stats()

        # Fila de estadísticas
        fila_stats = ctk.CTkFrame(parent, fg_color="transparent")
        fila_stats.pack(fill="x", pady=(0, 10))

        items_stats = [
            ("Registros",  str(stats["total"])),
            ("Promedio",   f"{stats['promedio']:.1f}" if stats["total"] else "—"),
            ("Máximo",     str(stats["maximo"])        if stats["total"] else "—"),
            ("Mínimo",     str(stats["minimo"])        if stats["total"] else "—"),
            ("Tendencia",  stats["tendencia"]),
        ]
        for titulo, valor in items_stats:
            card_stat = CardFrame(fila_stats, modo=self.modo)
            card_stat.pack(side="left", expand=True, fill="both", padx=(0, 6))
            color_val = colores["accent"]
            if titulo == "Tendencia":
                if "Mejorando" in valor:
                    color_val = colores["success"]
                elif "Bajando" in valor:
                    color_val = colores["error"]
            elif titulo in ("Promedio", "Máximo", "Mínimo") and stats["total"]:
                try:
                    color_val = _color_puntaje_hex(float(valor))
                except ValueError:
                    pass
            ctk.CTkLabel(
                card_stat, text=valor,
                font=(TYPOGRAPHY["font_family"], 22, "bold"),
                text_color=color_val
            ).pack(pady=(10, 2))
            ctk.CTkLabel(
                card_stat, text=titulo,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=(0, 10))

        # Gráfico
        card_g = CardFrame(parent, modo=self.modo)
        card_g.pack(fill="both", expand=True)

        subtitulos = {7: "Últimos 7 días", 30: "Últimos 30 días", None: "Historial completo"}
        hdr_g = ctk.CTkFrame(card_g, fg_color="transparent")
        hdr_g.pack(fill="x", padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 0))
        ctk.CTkLabel(
            hdr_g, text="Estado emocional",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(side="left")
        ctk.CTkLabel(
            hdr_g, text=f"· {subtitulos.get(self.periodo_viz, '')}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(side="left", padx=(6, 0))

        leyenda = ctk.CTkFrame(hdr_g, fg_color="transparent")
        leyenda.pack(side="right")
        for chex, lbl in [("#E74C3C", "Bajo"), ("#F0A500", "Medio"), ("#7CBD50", "Bien"), ("#22D47E", "Óptimo")]:
            ctk.CTkFrame(leyenda, fg_color=chex, width=10, height=10, corner_radius=5).pack(side="left", padx=(6, 2))
            ctk.CTkLabel(leyenda, text=lbl,
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                         text_color=colores["text_tertiary"]).pack(side="left", padx=(0, 4))

        self._viz_canvas = tk.Canvas(
            card_g, bg=colores["bg_surface"], highlightthickness=0
        )
        self._viz_canvas.pack(fill="both", expand=True,
                               padx=LAYOUT["padding_card"], pady=(8, LAYOUT["padding_card"]))
        self._viz_puntos = puntos
        self._viz_canvas.bind("<Configure>", lambda e: self._viz_redibujar())
        self._viz_canvas.after(60, self._viz_redibujar)

    def _viz_cambiar_periodo(self, dias):
        self.periodo_viz = dias
        estado = self.state()
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        if estado == "zoomed":
            self.state("zoomed")

    def _viz_obtener_grupos(self):
        hoy = datetime.now().date()
        grupos = []
        if self.periodo_viz == 7:
            for i in range(6, -1, -1):
                d = hoy - timedelta(days=i)
                etiq = d.strftime("%d/%m")
                grupos.append((etiq, d.isoformat(), d.isoformat()))
        elif self.periodo_viz == 30:
            for i in range(29, -1, -1):
                d = hoy - timedelta(days=i)
                etiq = d.strftime("%d/%m")
                grupos.append((etiq, d.isoformat(), d.isoformat()))
        else:
            conn = obtener_conexion()
            row = conn.execute("SELECT MIN(fecha) as mi FROM termometro").fetchone()
            conn.close()
            if not row or not row["mi"]:
                return []
            fecha_ini = datetime.strptime(row["mi"], "%Y-%m-%d").date()
            cur = fecha_ini.replace(day=1)
            while cur <= hoy:
                ultimo_dia = calendar.monthrange(cur.year, cur.month)[1]
                fin_mes = cur.replace(day=ultimo_dia)
                etiq = f"{cur.strftime('%b')} {cur.year}"
                grupos.append((etiq, cur.isoformat(), min(fin_mes, hoy).isoformat()))
                if cur.month == 12:
                    cur = cur.replace(year=cur.year + 1, month=1)
                else:
                    cur = cur.replace(month=cur.month + 1)
        return grupos

    def _viz_calcular_puntos(self, grupos):
        if not grupos:
            return []
        conn = obtener_conexion()
        puntos = []
        for etiq, ini, fin in grupos:
            row = conn.execute(
                "SELECT AVG(puntaje) as avg, COUNT(*) as cnt "
                "FROM termometro WHERE fecha >= ? AND fecha <= ?",
                (ini, fin)
            ).fetchone()
            puntos.append({"etiq": etiq, "val": row["avg"], "cnt": row["cnt"]})
        conn.close()
        return puntos

    def _viz_calcular_stats(self):
        conn = obtener_conexion()
        hoy = datetime.now().date()
        if self.periodo_viz:
            desde = (hoy - timedelta(days=self.periodo_viz - 1)).isoformat()
            rows = conn.execute(
                "SELECT puntaje FROM termometro WHERE fecha >= ?", (desde,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT puntaje FROM termometro").fetchall()
        conn.close()
        vals = [r["puntaje"] for r in rows]
        if not vals:
            return {"total": 0, "promedio": 0, "maximo": 0, "minimo": 0, "tendencia": "Sin datos"}
        tendencia = "Sin datos"
        if len(vals) >= 4:
            mid = len(vals) // 2
            prom_ant = sum(vals[:mid]) / mid
            prom_rec = sum(vals[mid:]) / (len(vals) - mid)
            diff = prom_rec - prom_ant
            if diff > 0.5:
                tendencia = "↑ Mejorando"
            elif diff < -0.5:
                tendencia = "↓ Bajando"
            else:
                tendencia = "→ Estable"
        return {
            "total": len(vals),
            "promedio": sum(vals) / len(vals),
            "maximo": max(vals),
            "minimo": min(vals),
            "tendencia": tendencia,
        }

    def _viz_redibujar(self):
        if not hasattr(self, '_viz_canvas'):
            return
        c = self._viz_canvas
        c.delete("all")
        colores = COLORS[self.modo]
        puntos = self._viz_puntos

        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or h < 10:
            return

        mg_l, mg_r, mg_t, mg_b = 50, 20, 18, 40
        ancho = w - mg_l - mg_r
        pad_v = 12
        alto = h - mg_t - mg_b - 2 * pad_v
        y_base = mg_t + pad_v

        borde = colores["border"]
        dim = colores["text_tertiary"]

        spacing_y = alto / 10
        paso_y = 1 if spacing_y >= 12 else 2
        for val_y in range(0, 11, paso_y):
            fy = y_base + alto - int(alto * val_y / 10)
            c.create_line(mg_l, fy, w - mg_r, fy, fill=borde, dash=(2, 4), width=1)
            c.create_text(mg_l - 6, fy, text=str(val_y),
                          fill=dim, font=("Segoe UI", 9), anchor="e")

        n = len(puntos)
        if n == 0:
            c.create_text(w // 2, h // 2, text="Sin registros en este período",
                          fill=dim, font=("Segoe UI", 12))
            return

        if n == 1:
            xs = [mg_l + ancho // 2]
        else:
            xs = [mg_l + int(ancho * i / (n - 1)) for i in range(n)]

        def y_de(v):
            return y_base + alto - int(alto * v / 10)

        vals_con_datos = [(i, p["val"]) for i, p in enumerate(puntos) if p["val"] is not None]

        if not vals_con_datos:
            c.create_text(w // 2, h // 2, text="Sin registros en este período",
                          fill=dim, font=("Segoe UI", 12))
            return

        bar_w = max(4, min(20, ancho // max(n, 1) - 2))
        for i, p in enumerate(puntos):
            if p["val"] is None:
                continue
            cx_pt = xs[i]
            color_pt = _color_puntaje_hex(p["val"])
            c.create_rectangle(
                cx_pt - bar_w // 2, y_de(p["val"]),
                cx_pt + bar_w // 2, y_base + alto,
                fill=color_pt, outline=""
            )

        for j in range(1, len(vals_con_datos)):
            i1, v1 = vals_con_datos[j - 1]
            i2, v2 = vals_con_datos[j]
            c.create_line(xs[i1], y_de(v1), xs[i2], y_de(v2),
                          fill=colores["accent"], width=2)

        for i, p in enumerate(puntos):
            if p["val"] is None:
                continue
            cx_pt = xs[i]
            if n <= 30:
                c.create_text(cx_pt, y_base + alto + 8, text=p["etiq"],
                              fill=dim, font=("Segoe UI", 7), anchor="n")

    # ── Lógica de registro ────────────────────────────────────────────────────

    def _actualizar_emojis(self):
        colores = COLORS[self.modo]
        for i, lbl in enumerate(self.emoji_labels):
            if i + 1 == self.puntaje_actual:
                lbl.configure(
                    font=(TYPOGRAPHY["font_family"], 36),
                    text_color=color_por_puntaje_exacto(i)
                )
            else:
                lbl.configure(
                    font=(TYPOGRAPHY["font_family"], 20),
                    text_color=colores["text_tertiary"]
                )

    def _on_slider_change(self, valor):
        self.puntaje_actual = max(1, int(round(valor)))
        etiqueta = self._etiqueta_puntaje(self.puntaje_actual)
        color = color_por_puntaje(self.puntaje_actual, self.modo)
        self.lbl_puntaje.configure(
            text=f"{self.puntaje_actual} — {etiqueta}",
            text_color=color
        )
        self._actualizar_emojis()

    def _etiqueta_puntaje(self, p: int) -> str:
        _ETIQUETAS = [
            "Muy perturbado",    # 1
            "Perturbado",        # 2
            "Disfórico",         # 3
            "Desanimado",        # 4
            "Neutral",           # 5
            "Tranquilo",         # 6
            "Estable",           # 7
            "Satisfecho",        # 8
            "Optimista",         # 9
            "Pleno",             # 10
        ]
        return _ETIQUETAS[max(1, min(p, 10)) - 1]

    def _registrar(self):
        nota = self.txt_nota.get("1.0", "end").strip()[:200]
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO termometro (fecha, hora, puntaje, nota) VALUES (?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), self.puntaje_actual, nota)
            )
            conn.commit()
            conn.close()
            self.txt_nota.delete("1.0", "end")
            if _MOTOR_OK:
                try:
                    _motor.sembrar_actividades_si_vacio()
                    _motor.agregar_a_checklist(self.puntaje_actual)
                except Exception:
                    pass
            if _SYNC_OK:
                _sync_inmediato()
            self._verificar_alerta()
            self._mostrar_confirmacion()
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo guardar el registro.\n{e}", tipo="error", modo=self.modo)

    def _mostrar_confirmacion(self):
        from shared.components import NMToplevel
        colores = COLORS[self.modo]
        win = NMToplevel(self, modo=self.modo)
        win.title("Registro guardado")
        _w, _h = 320, 190
        win.geometry(f"{_w}x{_h}+{(win.winfo_screenwidth()-_w)//2}+{(win.winfo_screenheight()-_h)//2}")
        win.resizable(False, False)
        win.configure(fg_color=colores["bg_surface"])
        win.grab_set()
        ctk.CTkFrame(win, fg_color=colores["success"], height=3, corner_radius=0).pack(fill="x")
        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=28, pady=(12, 20))
        ctk.CTkLabel(f, text="✓",
                     font=(TYPOGRAPHY["font_family"], 26),
                     text_color=colores["success"]).pack(pady=(0, 4))
        ctk.CTkLabel(f, text="Registro guardado",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                     text_color=colores["success"] if self.modo == "light" else colores["text_primary"]
                     ).pack(pady=(0, 14))
        _kw = {"fg_color": colores["success"], "hover_color": "#4A8A70"} if self.modo == "light" else {}
        BotonPrimario(f, text="Continuar", modo=self.modo, width=120,
                      command=win.destroy, **_kw).pack()
        win.after(10, win.focus_force)

    def _verificar_alerta(self):
        conn = obtener_conexion()
        hoy = datetime.now().date()
        ultimos_3 = []
        for i in range(3):
            dia = (hoy - timedelta(days=i)).isoformat()
            row = conn.execute(
                "SELECT puntaje FROM termometro WHERE fecha = ? ORDER BY hora DESC LIMIT 1",
                (dia,)
            ).fetchone()
            if row:
                ultimos_3.append(row["puntaje"])
        conn.close()

        if len(ultimos_3) == 3 and all(p <= 3 for p in ultimos_3):
            self._mostrar_alerta_apoyo()

    def _mostrar_alerta_apoyo(self):
        if hasattr(self, '_alerta_apoyo') and self._alerta_apoyo.winfo_exists():
            return
        colores = COLORS[self.modo]
        alerta = ctk.CTkFrame(
            self, fg_color=colores["bg_surface"],
            corner_radius=LAYOUT["radius_card"],
            border_color=colores["warning"],
            border_width=2
        )
        self._alerta_apoyo = alerta
        alerta.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            alerta, text="💛",
            font=(TYPOGRAPHY["font_family"], 28)
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            alerta, text="Notamos que tus últimos días fueron difíciles",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["warning"] if self.modo == "light" else colores["text_primary"]
        ).pack(padx=24)

        ctk.CTkLabel(
            alerta,
            text="Recordá que no estás solo/a. Si necesitás hablar,\ncontactá a tu equipo terapéutico.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"],
            justify="center"
        ).pack(padx=24, pady=8)

        _kw_warn = {"fg_color": colores["warning"], "hover_color": "#B06830"} if self.modo == "light" else {}
        BotonPrimario(
            alerta, text="Entendido", modo=self.modo, width=120,
            command=alerta.destroy, **_kw_warn
        ).pack(pady=(8, 20))

    # ── Tema ──────────────────────────────────────────────────────────────────

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
        self._nota_temp = (
            self.txt_nota.get("1.0", "end").strip()
            if hasattr(self, 'txt_nota') and self.txt_nota.winfo_exists()
            else ""
        )
        self.modo = nuevo_modo
        ctk.set_appearance_mode(nuevo_modo)
        hwnd = _freeze_window(self)
        self._construir_ui()
        if self._vista == "termometro":
            self.slider.set(self.puntaje_actual)
            self._on_slider_change(self.puntaje_actual)
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")

    def _toggle_modo(self):
        estado = self.state()
        self._nota_temp = (
            self.txt_nota.get("1.0", "end").strip()
            if hasattr(self, 'txt_nota') and self.txt_nota.winfo_exists()
            else ""
        )
        self.modo = "light" if self.modo == "dark" else "dark"
        guardar_config("theme", self.modo)
        ctk.set_appearance_mode(self.modo)
        hwnd = _freeze_window(self)
        self._construir_ui()
        if self._vista == "termometro":
            self.slider.set(self.puntaje_actual)
            self._on_slider_change(self.puntaje_actual)
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = TermometroApp()
    app.mainloop()
