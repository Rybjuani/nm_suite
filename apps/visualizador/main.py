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
from tkinter import filedialog
import calendar

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas, guardar_config, leer_config
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido, mostrar_mensaje,
    aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import color_por_puntaje

MESES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
         7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

# Paleta de degradado por puntaje 0-10 (hex sin alpha)
COLORES_PUNTAJE = {
    0: "#E74C3C", 1: "#E96134", 2: "#EC762C", 3: "#EF8C24",
    4: "#F0A500", 5: "#EAB800", 6: "#C0C030", 7: "#7CBD50",
    8: "#3AAE70", 9: "#2BBF7A", 10: "#22D47E",
}


def _color_puntaje_hex(v: float) -> str:
    return COLORES_PUNTAJE.get(int(round(max(0, min(10, v)))), "#1EC8D4")


class VisualizadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()
        self.modo = leer_config("theme", "dark")
        self.periodo = 7
        self._hover_id = None

        self.title("NeuroMood · Visualizador de Evolución")
        w, h = 980, 700
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(860, 600)
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

    # ── UI principal ──────────────────────────────────────────────────────────

    def _construir_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        self.configure(fg_color=colores["bg_primary"])

        HeaderFrame(
            self,
            titulo="Visualizador de Evolución",
            subtitulo="Evolución del estado emocional registrado",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        ).pack(fill="x")

        barra_inferior = ctk.CTkFrame(self, fg_color=colores["bg_secondary"],
                                      height=40, corner_radius=0)
        barra_inferior.pack(fill="x", side="bottom")
        barra_inferior.pack_propagate(False)
        BotonSecundario(
            barra_inferior, text="Acerca de", modo=self.modo, width=100, height=30,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=12, pady=5)

        controles = ctk.CTkFrame(self, fg_color="transparent", height=50)
        controles.pack(fill="x", padx=LAYOUT["padding_container"], pady=(14, 0))
        controles.pack_propagate(False)

        for texto, dias in [("7 días", 7), ("30 días", 30), ("Todo", None)]:
            activo = dias == self.periodo
            ctk.CTkButton(
                controles, text=texto, height=34,
                fg_color=("#4A7EA5" if self.modo == "light" else colores["accent"]) if activo else ("#B5D0E8" if self.modo == "light" else colores["bg_hover"]),
                hover_color=("#3A6E95" if self.modo == "light" else colores["accent_hover"]) if activo else ("#9ABDD8" if self.modo == "light" else colores["accent_hover"]),
                text_color=(colores["text_on_accent"] if activo else "#1E4D78") if self.modo == "light" else colores["text_on_accent"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                command=lambda d=dias: self._cambiar_periodo(d)
            ).pack(side="left", padx=4)

        BotonSecundario(
            controles, text="Exportar PDF", modo=self.modo, width=120, height=34,
            command=self._exportar_pdf
        ).pack(side="right")

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True,
                       padx=LAYOUT["padding_container"], pady=LAYOUT["padding_container"])

        self._construir_contenido(contenido)

    def _construir_contenido(self, parent):
        colores = COLORS[self.modo]
        grupos = self._obtener_grupos()
        puntos = self._calcular_puntos(grupos)
        fecha_ini = grupos[0][1] if grupos else self._obtener_fecha_inicio()
        datos = self._obtener_datos_completos(fecha_ini)
        stats = self._calcular_stats(datos)

        # ── Fila de estadísticas ──────────────────────────────────────────────
        fila_stats = ctk.CTkFrame(parent, fg_color="transparent")
        fila_stats.pack(fill="x", pady=(0, 12))

        items_stats = [
            ("Registros",  str(stats["total"])),
            ("Promedio",   f"{stats['promedio']:.1f}" if stats["total"] else "—"),
            ("Máximo",     str(stats["maximo"])        if stats["total"] else "—"),
            ("Mínimo",     str(stats["minimo"])        if stats["total"] else "—"),
            ("Tendencia",  stats["tendencia"]),
        ]

        for titulo, valor in items_stats:
            card_stat = CardFrame(fila_stats, modo=self.modo)
            card_stat.pack(side="left", expand=True, fill="both", padx=(0, 8))
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
            lbl_val = ctk.CTkLabel(
                card_stat, text=valor,
                font=(TYPOGRAPHY["font_family"], 22, "bold"),
                text_color=color_val
            )
            lbl_val.pack(pady=(10, 2))
            ctk.CTkLabel(
                card_stat, text=titulo,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=(0, 10))
            self._animar_contador(lbl_val, valor, color_val)

        # ── Gráfico interactivo ───────────────────────────────────────────────
        card_grafico = CardFrame(parent, modo=self.modo)
        card_grafico.pack(fill="both", expand=True)

        subtitulos = {7: "Últimos 7 días", 30: "Últimos 30 días", None: "Historial completo"}
        header_g = ctk.CTkFrame(card_grafico, fg_color="transparent")
        header_g.pack(fill="x", padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 0))
        ctk.CTkLabel(
            header_g, text="Estado emocional",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(side="left")
        ctk.CTkLabel(
            header_g, text=f"· {subtitulos.get(self.periodo, '')}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(side="left", padx=(6, 0))

        # Leyenda de colores
        leyenda = ctk.CTkFrame(header_g, fg_color="transparent")
        leyenda.pack(side="right")
        for color_hex, label in [("#E74C3C", "Bajo"), ("#F0A500", "Medio"), ("#7CBD50", "Bien"), ("#22D47E", "Óptimo")]:
            ctk.CTkFrame(leyenda, fg_color=color_hex, width=10, height=10,
                         corner_radius=5).pack(side="left", padx=(6, 2))
            ctk.CTkLabel(leyenda, text=label,
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                         text_color=colores["text_tertiary"]).pack(side="left", padx=(0, 4))

        # Canvas del gráfico
        self._canvas_grafico = tk.Canvas(
            card_grafico,
            bg=colores["bg_surface"],
            highlightthickness=0
        )
        self._canvas_grafico.pack(fill="both", expand=True,
                                   padx=LAYOUT["padding_card"],
                                   pady=(8, LAYOUT["padding_card"]))

        self._puntos_grafico = puntos
        self._canvas_grafico.bind("<Configure>",
                                   lambda e: self._redibujar_grafico())
        self._canvas_grafico.bind("<Motion>", self._on_hover_canvas)
        self._canvas_grafico.bind("<Leave>", self._on_leave_canvas)
        self._canvas_grafico.after(60, self._redibujar_grafico)

    def _calcular_puntos(self, grupos):
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
            puntos.append({
                "etiq": etiq,
                "val": row["avg"],
                "cnt": row["cnt"],
                "ini": ini,
                "fin": fin,
            })
        conn.close()
        return puntos

    def _redibujar_grafico(self):
        c = self._canvas_grafico
        c.delete("all")
        colores = COLORS[self.modo]
        puntos = self._puntos_grafico

        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or h < 10:
            return

        mg_l, mg_r, mg_t, mg_b = 58, 24, 22, 44
        ancho = w - mg_l - mg_r
        # Reservar padding vertical extra para que y=0 y y=10 no queden en el borde
        pad_v = 14
        alto  = h - mg_t - mg_b - 2 * pad_v
        y_base = mg_t + pad_v   # y canvas donde va el valor 10

        bg    = colores["bg_surface"]
        borde = colores["border"]
        dim   = colores["text_tertiary"]
        prim  = colores["text_primary"]

        spacing_y = alto / 10
        paso_y = 1 if spacing_y >= 12 else 2
        for val_y in range(0, 11, paso_y):
            fy = y_base + alto - int(alto * val_y / 10)
            dash = (2, 4)
            c.create_line(mg_l, fy, w - mg_r, fy,
                          fill=borde, dash=dash, width=1)
            c.create_text(mg_l - 6, fy, text=str(val_y),
                          fill=dim, font=("Segoe UI", 9), anchor="e")

        n = len(puntos)
        # Coordenadas x de cada punto
        if n == 1:
            xs = [mg_l + ancho // 2]
        else:
            xs = [mg_l + int(ancho * i / (n - 1)) for i in range(n)]

        def y_de(v):
            return y_base + alto - int(alto * v / 10)

        vals_con_datos = [(i, p["val"]) for i, p in enumerate(puntos) if p["val"] is not None]

        if not vals_con_datos:
            c.create_text(w // 2, h // 2,
                          text="Sin registros en el período seleccionado",
                          fill=dim, font=("Segoe UI", 12))
            return

        # ── Barras de color por emoción ────────────────────────────────────────
        self._items_hover = []
        bar_w = 12

        for i, p in enumerate(puntos):
            if p["val"] is None:
                continue
            cx_pt = xs[i]
            color_pt = _color_puntaje_hex(p["val"])
            bx0 = cx_pt - bar_w // 2
            bx1 = cx_pt + bar_w // 2
            by_top = y_de(p["val"])
            by_bot = y_base + alto
            c.create_rectangle(bx0, by_top, bx1, by_bot, fill=color_pt, outline="")
            self._items_hover.append(
                (bx0 - 2, by_top - 10, bx1 + 2, by_bot,
                 p["etiq"], p["val"], p["cnt"])
            )

        # ── Etiquetas eje X ───────────────────────────────────────────────────
        paso = max(1, n // 10)
        for i, p in enumerate(puntos):
            if i % paso == 0 or i == n - 1:
                c.create_text(xs[i], y_base + alto + 14,
                              text=p["etiq"],
                              fill=dim, font=("Segoe UI", 9), anchor="n")


    def _on_hover_canvas(self, event):
        c = self._canvas_grafico
        if not hasattr(self, '_items_hover'):
            return
        colores = COLORS[self.modo]
        mx, my = event.x, event.y

        # Limpiar tooltip anterior
        if self._hover_id:
            c.delete(self._hover_id)
            self._hover_id = None
        c.delete("tooltip_text")

        for x0, y0, x1, y1, etiq, val, cnt in self._items_hover:
            if x0 <= mx <= x1 and y0 <= my <= y1:
                color_pt = _color_puntaje_hex(val)
                # Texto del tooltip
                linea1 = etiq
                linea2 = f"{val:.1f} / 10"
                linea3 = f"{cnt} registro{'s' if cnt != 1 else ''}"

                # Posición del tooltip
                tw, th = 130, 62
                tx = mx + 14
                ty = my - th - 4
                if tx + tw > c.winfo_width() - 8:
                    tx = mx - tw - 14
                if tx < 2:
                    tx = 2
                if ty < 4:
                    ty = my + 14

                r = 8
                # Caja con borde coloreado (simulado con dos rectángulos)
                bg_t = colores["bg_surface"]
                self._hover_id = c.create_rectangle(
                    tx, ty, tx + tw, ty + th,
                    fill=bg_t, outline=color_pt, width=2
                )
                c.create_text(tx + tw // 2, ty + 12,
                              text=linea1, fill=colores["text_tertiary"],
                              font=("Segoe UI", 9), anchor="center",
                              tags="tooltip_text")
                c.create_text(tx + tw // 2, ty + 30,
                              text=linea2, fill=color_pt,
                              font=("Segoe UI", 14, "bold"), anchor="center",
                              tags="tooltip_text")
                c.create_text(tx + tw // 2, ty + 50,
                              text=linea3, fill=colores["text_tertiary"],
                              font=("Segoe UI", 9), anchor="center",
                              tags="tooltip_text")
                return

    def _on_leave_canvas(self, event):
        if self._hover_id:
            self._canvas_grafico.delete(self._hover_id)
            self._canvas_grafico.delete("tooltip_text")
            self._hover_id = None

    # ── Datos y cálculos ──────────────────────────────────────────────────────

    def _obtener_fecha_inicio(self):
        if self.periodo is None:
            return None
        return (datetime.now().date() - timedelta(days=self.periodo)).isoformat()

    def _obtener_datos_completos(self, fecha_inicio_override=None):
        conn = obtener_conexion()
        fecha_inicio = fecha_inicio_override if fecha_inicio_override is not None else self._obtener_fecha_inicio()
        if fecha_inicio:
            rows = conn.execute(
                "SELECT fecha, hora, puntaje, nota FROM termometro "
                "WHERE fecha >= ? ORDER BY fecha, hora",
                (fecha_inicio,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT fecha, hora, puntaje, nota FROM termometro "
                "ORDER BY fecha, hora"
            ).fetchall()
        conn.close()
        return rows

    def _calcular_stats(self, datos):
        if not datos:
            return {"total": 0, "promedio": 0, "maximo": 0,
                    "minimo": 0, "tendencia": "—"}
        puntajes = [r["puntaje"] for r in datos]
        total = len(puntajes)
        promedio = sum(puntajes) / total
        maximo = max(puntajes)
        minimo = min(puntajes)

        if total >= 4:
            mitad = total // 2
            p1 = sum(puntajes[:mitad]) / mitad
            p2 = sum(puntajes[mitad:]) / (total - mitad)
            diff = p2 - p1
            if diff > 0.5:
                tendencia = "▲ Mejorando"
            elif diff < -0.5:
                tendencia = "▼ Bajando"
            else:
                tendencia = "● Estable"
        else:
            tendencia = "— Pocos datos"

        return {"total": total, "promedio": promedio,
                "maximo": maximo, "minimo": minimo, "tendencia": tendencia}

    def _obtener_grupos(self):
        hoy = datetime.now().date()
        grupos = []

        if self.periodo == 7:
            for i in range(6, -1, -1):
                d = hoy - timedelta(days=i)
                grupos.append((d.strftime("%d/%m"), d.isoformat(), d.isoformat()))

        elif self.periodo == 30:
            for i in range(29, -1, -1):
                d = hoy - timedelta(days=i)
                grupos.append((d.strftime("%d/%m"), d.isoformat(), d.isoformat()))

        elif self.periodo == 90:
            # Últimos 3 meses calendario reales
            for m in range(2, -1, -1):
                mes_num = hoy.month - m
                año_num = hoy.year
                while mes_num < 1:
                    mes_num += 12
                    año_num -= 1
                ultimo  = calendar.monthrange(año_num, mes_num)[1]
                inicio  = datetime(año_num, mes_num, 1).date()
                fin     = datetime(año_num, mes_num, ultimo).date()
                grupos.append((MESES[mes_num], inicio.isoformat(), fin.isoformat()))

        else:
            # Todo el historial: un punto por mes con registros
            conn = obtener_conexion()
            row = conn.execute("SELECT MIN(fecha) as primera FROM termometro").fetchone()
            conn.close()
            if not row or not row["primera"]:
                return []
            primera = datetime.fromisoformat(row["primera"]).date()
            año, mes = primera.year, primera.month
            while (año, mes) <= (hoy.year, hoy.month):
                ultimo = calendar.monthrange(año, mes)[1]
                inicio = datetime(año, mes, 1).date()
                fin    = datetime(año, mes, ultimo).date()
                etiq   = f"{MESES[mes]} {str(año)[2:]}"
                grupos.append((etiq, inicio.isoformat(), fin.isoformat()))
                mes += 1
                if mes > 12:
                    mes = 1
                    año += 1

        return grupos

    # ── Exportar PDF ──────────────────────────────────────────────────────────

    def _exportar_pdf(self):
        periodo_txt = {7: "última semana", 30: "último mes",
                       90: "últimos 3 meses", None: "historial completo"}
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"evolucion_emocional_{datetime.now().strftime('%Y-%m-%d')}.pdf"
        )
        if not ruta:
            return

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as rl_colors
            from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                             Spacer, Table, TableStyle)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm

            C_BORDE = rl_colors.HexColor(COLORS["light"]["border"])
            C_FONDO = rl_colors.HexColor(COLORS["light"]["bg_primary"])
            C_TEXTO = rl_colors.HexColor(COLORS["light"]["text_primary"])
            C_DIM   = rl_colors.HexColor(COLORS["light"]["text_tertiary"])

            ESTILO_TABLA = TableStyle([
                ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME',   (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE',   (0, 0), (-1, -1), 9),
                ('TEXTCOLOR',  (0, 0), (-1, -1), C_TEXTO),
                ('BACKGROUND', (0, 0), (0, -1), C_FONDO),
                ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
                ('GRID',       (0, 0), (-1, -1), 0.5, C_BORDE),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ])

            def tabla(filas):
                t = Table(filas, colWidths=[4 * cm, 12.5 * cm])
                t.setStyle(ESTILO_TABLA)
                return t

            styles = getSampleStyleSheet()
            est_titulo = ParagraphStyle(
                'NMT', parent=styles['Title'],
                textColor=C_TEXTO, fontSize=20, spaceAfter=4)
            est_sub = ParagraphStyle(
                'NMS', parent=styles['Normal'],
                textColor=C_DIM, fontSize=10)
            est_seccion = ParagraphStyle(
                'NMSC', parent=styles['Normal'],
                textColor=C_TEXTO, fontSize=12,
                spaceBefore=16, spaceAfter=6,
                fontName='Helvetica-Bold')

            datos = self._obtener_datos_completos()
            stats = self._calcular_stats(datos)

            elementos = []
            elementos.append(Paragraph("NeuroMood — Informe de Evolución Emocional", est_titulo))
            elementos.append(Paragraph(
                f"Período: {periodo_txt.get(self.periodo, f'últimos {self.periodo} días')}  ·  "
                f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                est_sub
            ))
            elementos.append(Spacer(1, 0.5 * cm))

            elementos.append(Paragraph("Resumen del período", est_seccion))
            if stats["total"]:
                elementos.append(tabla([
                    ["Total de registros", str(stats["total"])],
                    ["Promedio",           f"{stats['promedio']:.1f} / 10"],
                    ["Valor máximo",       f"{stats['maximo']} / 10"],
                    ["Valor mínimo",       f"{stats['minimo']} / 10"],
                    ["Tendencia",          stats["tendencia"].replace("▲", "").replace("▼", "").replace("●", "").strip()],
                ]))
            else:
                elementos.append(Paragraph("Sin registros en el período seleccionado.", styles["Normal"]))

            elementos.append(Spacer(1, 0.5 * cm))
            elementos.append(Paragraph("Detalle de registros", est_seccion))
            if datos:
                for r in datos:
                    nota = (r["nota"][:150] + "...") if r["nota"] and len(r["nota"]) > 150 else (r["nota"] or "—")
                    elementos.append(tabla([
                        ["Fecha / Hora", f"{r['fecha']}  {r['hora'][:5]}"],
                        ["Puntaje",      f"{r['puntaje']} / 10"],
                        ["Nota",         nota],
                    ]))
                    elementos.append(Spacer(1, 0.2 * cm))
            else:
                elementos.append(Paragraph("Sin registros.", styles["Normal"]))

            doc = SimpleDocTemplate(ruta, pagesize=A4,
                                    topMargin=2 * cm, bottomMargin=2 * cm,
                                    leftMargin=2.5 * cm, rightMargin=2.5 * cm)
            doc.build(elementos)
            mostrar_mensaje(self, "Exportar", f"Informe guardado:\n{ruta}", tipo="success", modo=self.modo)

        except ImportError:
            mostrar_mensaje(self, "Error", "Se necesita reportlab.\nInstalalo con: pip install reportlab", tipo="error", modo=self.modo)
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo generar el PDF.\n{e}", tipo="error", modo=self.modo)

    # ── Animación contadores ──────────────────────────────────────────────────

    def _animar_contador(self, lbl, target_str, color_final, steps=18):
        try:
            val = float(target_str)
        except ValueError:
            return
        delta = val / steps

        def tick(i=0, cur=0.0):
            try:
                if not lbl.winfo_exists():
                    return
                if i >= steps:
                    lbl.configure(text=target_str, text_color=color_final)
                    return
                lbl.configure(
                    text=f"{cur:.1f}" if '.' in target_str else str(int(round(cur)))
                )
                lbl.after(22, lambda: tick(i + 1, cur + delta))
            except Exception:
                pass

        tick()

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _cambiar_periodo(self, dias):
        self.periodo = dias
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
    app = VisualizadorApp()
    app.mainloop()
