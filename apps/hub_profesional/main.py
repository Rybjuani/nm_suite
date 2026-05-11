"""
main.py — Hub Profesional NeuroMood
Gestión remota de pacientes vía base de datos + herramientas locales.
"""
import sys
import os
import threading

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

for _sub in ("activacion", "checklist", "temporizador", "pensamientos"):
    _p = os.path.join(_base, "apps", _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import motor as _motor_hub
    _CATEGORIAS_ACT = _motor_hub.CATEGORIAS
except Exception:
    _CATEGORIAS_ACT = ["Autocuidado", "Cognitiva", "Física", "Placer", "Rutina", "Social", "Maestría"]

import customtkinter as ctk
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.components import CardFrame, BotonPrimario, BotonSecundario, NMToplevel, mostrar_mensaje

try:
    from supabase import create_client as _sb_create
    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False

_SUPABASE_URL = "https://ehmqxgknkjjhdrdghdhp.supabase.co"
_SUPABASE_KEY = "sb_publishable_ztJdbXpwi-mIIODxZ_t56A_BpLjdlUC"

_ANIMO_SEGMENTOS = ["Bajo (1–4)", "Medio (4–7)", "Alto (7–10)"]
_ANIMO_MAP       = {"Bajo (1–4)": (1, 4), "Medio (4–7)": (4, 7), "Alto (7–10)": (7, 10)}
_ANIMO_LABEL     = {(1, 4): "Bajo", (4, 7): "Medio", (7, 10): "Alto"}


def _get_sb():
    if not _SUPABASE_OK:
        return None, "módulo no instalado"
    try:
        return _sb_create(_SUPABASE_URL, _SUPABASE_KEY), None
    except Exception as e:
        return None, str(e)[:60]


class HubProfesional(ctk.CTk):
    def __init__(self, modo: str = "dark"):
        super().__init__()
        self.modo = modo
        c = COLORS[modo]
        ctk.set_appearance_mode(modo)
        ctk.set_default_color_theme("blue")

        self.title("NeuroMood · Hub Profesional")
        self.geometry("1060x640")
        self.minsize(860, 540)
        self.configure(fg_color=c["bg_primary"])

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1060x640+{(sw - 1060)//2}+{(sh - 640)//2}")

        self._paciente_id: str | None = None
        self._paciente_nombre: str = ""
        self._paciente_pwd: str = ""
        self._pacientes: list = []
        self._pacientes_pwd: dict = {}
        self._sb = None

        self._construir()
        self.after(200, self._inicializar)

    def _inicializar(self):
        self._conectar_bd()
        self._cargar_pacientes()

    # ── Conexión base de datos ────────────────────────────────────────────────

    def _conectar_bd(self):
        self._sb, motivo = _get_sb()
        if self._sb:
            self._lbl_sync.configure(
                text="Base de datos: conectada",
                text_color=COLORS[self.modo]["success"]
            )
        else:
            self._lbl_sync.configure(
                text=f"Base de datos: {motivo}",
                text_color=COLORS[self.modo]["error"]
            )

    # ── Lista de pacientes ────────────────────────────────────────────────────

    def _cargar_pacientes(self):
        if not self._sb:
            self._actualizar_lista_pacientes([])
            return

        def _fetch():
            try:
                res = self._sb.table("patients").select("patient_id,patient_name,pwd").execute()
                pats = res.data or []
            except Exception:
                pats = []
            self.after(0, lambda: self._actualizar_lista_pacientes(pats))

        threading.Thread(target=_fetch, daemon=True).start()

    def _actualizar_lista_pacientes(self, pats: list):
        self._pacientes = pats
        self._pacientes_pwd = {p["patient_id"]: p.get("pwd", "") for p in pats}
        for w in self._scroll_pats.winfo_children():
            w.destroy()
        c = COLORS[self.modo]
        if not pats:
            ctk.CTkLabel(
                self._scroll_pats,
                text="Sin pacientes\nregistrados",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=c["text_tertiary"], justify="center"
            ).pack(pady=20)
            return
        for p in pats:
            nombre = p.get("patient_name") or p.get("patient_id", "—")
            ctk.CTkButton(
                self._scroll_pats, text=nombre,
                anchor="w", height=34,
                fg_color="transparent", hover_color=c["bg_hover"],
                text_color=c["text_primary"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                command=lambda pid=p["patient_id"], pn=nombre: self._seleccionar_paciente(pid, pn)
            ).pack(fill="x", pady=1, padx=4)

    def _seleccionar_paciente(self, pid: str, nombre: str):
        self._paciente_id = pid
        self._paciente_nombre = nombre
        self._paciente_pwd = self._pacientes_pwd.get(pid, "")
        self._lbl_paciente.configure(text=f"Paciente: {nombre}")
        self._cargar_tab_actual()

    # ── Layout principal ──────────────────────────────────────────────────────

    def _construir(self):
        c = COLORS[self.modo]

        # Header
        header = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=48, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Hub Profesional",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"]
        ).pack(side="left", padx=LAYOUT["padding_card"])
        self._lbl_sync = ctk.CTkLabel(
            header, text="Base de datos: iniciando...",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"]
        )
        self._lbl_sync.pack(side="left", padx=8)
        ctk.CTkButton(
            header, text="↻ Reconectar", width=110, height=28,
            fg_color="transparent", hover_color=c["bg_hover"],
            text_color=c["text_tertiary"], border_width=1, border_color=c["border"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            command=lambda: (self._conectar_bd(), self._cargar_pacientes())
        ).pack(side="right", padx=LAYOUT["padding_card"])

        # Cuerpo
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar de pacientes
        side = ctk.CTkFrame(body, fg_color=c["bg_secondary"], width=200, corner_radius=0)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        ctk.CTkLabel(
            side, text="Pacientes",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=c["text_primary"]
        ).pack(padx=12, pady=(14, 4), anchor="w")

        self._scroll_pats = ctk.CTkScrollableFrame(
            side, fg_color="transparent",
            scrollbar_button_color=c["bg_hover"],
            scrollbar_button_hover_color=c["accent"]
        )
        self._scroll_pats.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        BotonSecundario(
            side, text="↻ Actualizar lista", modo=self.modo, width=168, height=36,
            command=self._cargar_pacientes
        ).pack(padx=16, pady=(0, 14))

        # Panel derecho
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        self._lbl_paciente = ctk.CTkLabel(
            right, text="Seleccioná un paciente",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=c["accent"]
        )
        self._lbl_paciente.pack(anchor="w", padx=LAYOUT["padding_container"], pady=(10, 2))

        # Barra de tabs
        tab_bar = ctk.CTkFrame(right, fg_color=c["bg_secondary"], height=38, corner_radius=0)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        self._tab_content = ctk.CTkFrame(right, fg_color="transparent")
        self._tab_content.pack(
            fill="both", expand=True,
            padx=LAYOUT["padding_container"], pady=LAYOUT["padding_container"]
        )

        _act   = c["accent"]
        _off   = c["bg_hover"]
        _off_t = c["text_secondary"]
        _kw = dict(
            height=28, corner_radius=LAYOUT["radius_button"], border_width=0,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold")
        )

        tabs = [
            ("registros", "Registros del paciente"),
            ("gestion",   "Gestión"),
            ("permisos",  "Permisos"),
        ]
        self._tab_btns: dict[str, ctk.CTkButton] = {}
        self._tab_actual = "registros"

        def _ir(nombre: str):
            self._tab_actual = nombre
            for n, b in self._tab_btns.items():
                b.configure(
                    fg_color=_act if n == nombre else _off,
                    text_color=c["text_on_accent"] if n == nombre else _off_t
                )
            self._cargar_tab_actual()

        primer = True
        for nombre, label in tabs:
            btn = ctk.CTkButton(
                tab_bar, text=label, width=200,
                fg_color=_act if primer else _off,
                text_color=c["text_on_accent"] if primer else _off_t,
                hover_color=_act, command=lambda n=nombre: _ir(n), **_kw
            )
            btn.pack(side="left", padx=(LAYOUT["padding_container"] if primer else 4, 0), pady=5)
            self._tab_btns[nombre] = btn
            primer = False

    def _cargar_tab_actual(self):
        for w in self._tab_content.winfo_children():
            w.destroy()
        getattr(self, f"_tab_{self._tab_actual}")()

    # ── Tab: Registros del paciente ───────────────────────────────────────────

    def _tab_registros(self):
        c = COLORS[self.modo]
        p = LAYOUT["padding_card"]
        if not self._paciente_id:
            ctk.CTkLabel(
                self._tab_content, text="Seleccioná un paciente para ver sus registros.",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=c["text_tertiary"]
            ).pack(expand=True)
            return

        top = ctk.CTkFrame(self._tab_content, fg_color="transparent")
        top.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            top, text=f"Historial — {self._paciente_nombre}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=c["text_primary"]
        ).pack(side="left")
        self._btn_pdf = ctk.CTkButton(
            top, text="⬇ Exportar PDF", width=140, height=30,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
            command=self._exportar_pdf_paciente,
        )
        self._btn_pdf.pack(side="right")

        scroll = ctk.CTkScrollableFrame(
            self._tab_content, fg_color="transparent",
            scrollbar_button_color=c["bg_hover"],
            scrollbar_button_hover_color=c["accent"]
        )
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="Cargando registros...",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=c["text_tertiary"]
        ).pack(pady=20)

        def _fetch():
            datos = {}
            if not self._sb:
                self.after(0, lambda: self._mostrar_datos(scroll, datos))
                return
            tablas = {
                "animo":     ("mood_records",          "fecha,hora,puntaje,nota",                         14),
                "resp":      ("breathing_sessions",    "fecha,hora,tecnica,duracion_minutos",              10),
                "pens":      ("thought_records",       "fecha,hora,emocion,intensidad,pensamiento",        10),
                "checklist": ("checklist_completions", "fecha,descripcion,categoria,origen",               20),
                "timer":     ("timer_sessions",        "fecha,hora,nombre,categoria,duracion_real,notas",  14),
                "reclog":    ("reminder_logs",         "fecha,hora,mensaje,cerrado",                       14),
            }
            for clave, (tabla, campos, lim) in tablas.items():
                try:
                    res = (self._sb.table(tabla).select(campos)
                           .eq("patient_id", self._paciente_id)
                           .order("fecha", desc=True).limit(lim).execute())
                    datos[clave] = res.data or []
                except Exception:
                    datos[clave] = []
            self._datos_cache = datos
            self.after(0, lambda: self._mostrar_datos(scroll, datos))

        threading.Thread(target=_fetch, daemon=True).start()

    def _mostrar_datos(self, scroll, datos: dict):
        for w in scroll.winfo_children():
            w.destroy()
        c = COLORS[self.modo]
        p = LAYOUT["padding_card"]

        def _card(titulo, filas, col_fn):
            card = CardFrame(scroll, modo=self.modo)
            card.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(
                card, text=titulo,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                text_color=c["accent"]
            ).pack(anchor="w", padx=p, pady=(p, 4))
            if not filas:
                ctk.CTkLabel(
                    card, text="Sin registros.",
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    text_color=c["text_tertiary"]
                ).pack(anchor="w", padx=p, pady=(0, p))
            else:
                for r in filas:
                    f = ctk.CTkFrame(card, fg_color=c["bg_list_item"],
                                     corner_radius=LAYOUT["radius_button"])
                    f.pack(fill="x", padx=p, pady=1)
                    ctk.CTkLabel(
                        f, text=col_fn(r),
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                        text_color=c["text_secondary"], anchor="w"
                    ).pack(padx=8, pady=3, anchor="w")
                ctk.CTkLabel(card, text="").pack(pady=(0, 2))

        animo = datos.get("animo", [])
        if animo:
            puntajes = [r["puntaje"] for r in animo if r.get("puntaje") is not None]
            prom = round(sum(puntajes) / len(puntajes), 1) if puntajes else "—"
            card = CardFrame(scroll, modo=self.modo)
            card.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(
                card, text="Registros de ánimo",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                text_color=c["accent"]
            ).pack(anchor="w", padx=p, pady=(p, 2))
            ctk.CTkLabel(
                card,
                text=f"Promedio: {prom}/10  |  Total: {len(animo)} registros",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=c["text_primary"]
            ).pack(anchor="w", padx=p, pady=(0, 4))
            for r in animo:
                f = ctk.CTkFrame(card, fg_color=c["bg_list_item"],
                                 corner_radius=LAYOUT["radius_button"])
                f.pack(fill="x", padx=p, pady=1)
                nota = (r.get("nota") or "")[:50]
                ctk.CTkLabel(
                    f,
                    text=f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                         f"Ánimo: {r.get('puntaje','—')}  {nota}",
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    text_color=c["text_secondary"], anchor="w"
                ).pack(padx=8, pady=3, anchor="w")
            ctk.CTkLabel(card, text="").pack(pady=(0, 2))
        else:
            _card("Registros de ánimo", [], lambda r: "")

        _card("Sesiones de respiración", datos.get("resp", []),
              lambda r: f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                        f"{r.get('tecnica','?')}  ({r.get('duracion_minutos','?')} min)")

        _card("Registros de pensamientos", datos.get("pens", []),
              lambda r: f"{r.get('fecha','')[:10]}  —  {r.get('emocion','?')} "
                        f"(int. {r.get('intensidad','?')})  {(r.get('pensamiento') or '')[:55]}")

        all_check = datos.get("checklist", [])
        _card("Actividades de activación completadas",
              [r for r in all_check if r.get("origen") == "activacion"],
              lambda r: f"{r.get('fecha','')[:10]}  [{r.get('categoria','?')}]  "
                        f"{(r.get('descripcion') or '')[:60]}")

        _card("Checklist completadas",
              [r for r in all_check if r.get("origen") != "activacion"],
              lambda r: f"{r.get('fecha','')[:10]}  "
                        f"{'[Prof] ' if r.get('origen') == 'profesional' else ''}"
                        f"[{r.get('categoria','?')}]  "
                        f"{(r.get('descripcion') or '')[:55]}")

        _card("Sesiones de temporizador", datos.get("timer", []),
              lambda r: f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                        f"{(r.get('nombre') or 'Sin nombre')[:30]}  "
                        f"[{r.get('categoria','?')}]  "
                        f"{(r.get('duracion_real') or 0)//60} min"
                        + (f"  ·  {(r.get('notas') or '')[:30]}" if r.get('notas') else ""))

        _card("Recordatorios disparados", datos.get("reclog", []),
              lambda r: f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                        f"{(r.get('mensaje') or '')[:55]}  "
                        + ("[cerrado]" if r.get('cerrado') else "[pendiente]"))

    def _exportar_pdf_paciente(self):
        if not self._paciente_id:
            return
        datos = getattr(self, "_datos_cache", None)
        if datos is None:
            mostrar_mensaje(self, "Sin datos",
                            "Abrí la pestaña 'Registros del paciente' primero.",
                            tipo="info", modo=self.modo)
            return
        self._btn_pdf.configure(state="disabled", text="Generando...")
        threading.Thread(target=self._generar_pdf, args=(datos,), daemon=True).start()

    def _generar_pdf(self, datos: dict):
        import os
        from datetime import datetime
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as rl_colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                            Table, TableStyle, HRFlowable)
        except ImportError:
            self.after(0, lambda: (
                mostrar_mensaje(self, "Error", "reportlab no está instalado.",
                                tipo="error", modo=self.modo),
                self._btn_pdf.configure(state="normal", text="⬇ Exportar PDF"),
            ))
            return

        nombre_seg = "".join(c for c in self._paciente_nombre if c.isalnum() or c in " _-")
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"NeuroMood_{nombre_seg}_{fecha_str}.pdf"
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads):
            downloads = os.path.expanduser("~")
        filepath = os.path.join(downloads, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        ac = "#1EC8D4"
        titulo_st = ParagraphStyle("titulo", parent=styles["Title"],
                                   fontSize=18, textColor=rl_colors.HexColor(ac))
        h2_st = ParagraphStyle("h2", parent=styles["Heading2"],
                               fontSize=12, textColor=rl_colors.HexColor(ac), spaceAfter=4)
        normal_st = styles["Normal"]
        caption_st = ParagraphStyle("cap", parent=styles["Normal"], fontSize=8,
                                    textColor=rl_colors.HexColor("#555555"))

        story = []
        story.append(Paragraph(f"NeuroMood — Registro de {self._paciente_nombre}", titulo_st))
        story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", caption_st))
        story.append(HRFlowable(width="100%", thickness=1, color=rl_colors.HexColor(ac), spaceAfter=12))

        def _seccion(titulo, filas, encabezados, row_fn, prom_txt=None):
            story.append(Paragraph(titulo, h2_st))
            if prom_txt:
                story.append(Paragraph(prom_txt, normal_st))
                story.append(Spacer(1, 4))
            if not filas:
                story.append(Paragraph("Sin registros.", caption_st))
                story.append(Spacer(1, 10))
                return
            tabla_data = [encabezados] + [row_fn(r) for r in filas]
            col_w = (A4[0] - 4*cm) / len(encabezados)
            t = Table(tabla_data, colWidths=[col_w] * len(encabezados), repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), rl_colors.HexColor(ac)),
                ("TEXTCOLOR",     (0, 0), (-1, 0), rl_colors.white),
                ("FONTSIZE",      (0, 0), (-1, 0), 9),
                ("FONTSIZE",      (0, 1), (-1, -1), 8),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1),
                 [rl_colors.HexColor("#F4F8FC"), rl_colors.white]),
                ("GRID",          (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#CCDDEE")),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING",   (0, 0), (-1, -1), 4),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
                ("TOPPADDING",    (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(t)
            story.append(Spacer(1, 12))

        animo = datos.get("animo", [])
        puntajes = [r["puntaje"] for r in animo if r.get("puntaje") is not None]
        prom_txt = (f"Promedio: {round(sum(puntajes)/len(puntajes),1)}/10  |  "
                    f"Total: {len(animo)} registros") if puntajes else None
        _seccion("Registros de ánimo", animo,
                 ["Fecha", "Hora", "Puntaje", "Nota"],
                 lambda r: [r.get("fecha","")[:10], r.get("hora","")[:5],
                            str(r.get("puntaje","")), (r.get("nota") or "")[:60]],
                 prom_txt)
        _seccion("Sesiones de respiración", datos.get("resp", []),
                 ["Fecha", "Hora", "Técnica", "Duración (min)"],
                 lambda r: [r.get("fecha","")[:10], r.get("hora","")[:5],
                            r.get("tecnica","?"), str(r.get("duracion_minutos","?"))])
        _seccion("Registros de pensamientos", datos.get("pens", []),
                 ["Fecha", "Emoción", "Intensidad", "Pensamiento"],
                 lambda r: [r.get("fecha","")[:10], r.get("emocion","?"),
                            str(r.get("intensidad","?")), (r.get("pensamiento") or "")[:80]])
        _all_check = datos.get("checklist", [])
        _seccion("Actividades de activación completadas",
                 [r for r in _all_check if r.get("origen") == "activacion"],
                 ["Fecha", "Categoría", "Actividad"],
                 lambda r: [r.get("fecha","")[:10], r.get("categoria","?"),
                            (r.get("descripcion") or "")[:80]])
        _seccion("Checklist completadas",
                 [r for r in _all_check if r.get("origen") != "activacion"],
                 ["Fecha", "Origen", "Categoría", "Descripción"],
                 lambda r: [r.get("fecha","")[:10],
                            "Profesional" if r.get("origen") == "profesional" else "Paciente",
                            r.get("categoria","?"), (r.get("descripcion") or "")[:70]])
        _seccion("Sesiones de temporizador", datos.get("timer", []),
                 ["Fecha", "Hora", "Actividad", "Duración (min)"],
                 lambda r: [r.get("fecha","")[:10], r.get("hora","")[:5],
                            (r.get("nombre") or "Sin nombre")[:40],
                            str((r.get("duracion_real") or 0)//60)])
        _seccion("Recordatorios disparados", datos.get("reclog", []),
                 ["Fecha", "Hora", "Mensaje", "Estado"],
                 lambda r: [r.get("fecha","")[:10], r.get("hora","")[:5],
                            (r.get("mensaje") or "")[:80],
                            "Cerrado" if r.get("cerrado") else "Pendiente"])
        try:
            doc.build(story)
            os.startfile(filepath)
            self.after(0, lambda: self._btn_pdf.configure(
                state="normal", text="⬇ Exportar PDF"))
        except Exception as e:
            self.after(0, lambda: (
                mostrar_mensaje(self, "Error al generar PDF", str(e), tipo="error", modo=self.modo),
                self._btn_pdf.configure(state="normal", text="⬇ Exportar PDF"),
            ))

    # ── Tab: Gestión (herramientas + asignaciones) ────────────────────────────

    def _tab_gestion(self):
        c = COLORS[self.modo]
        p = LAYOUT["padding_card"]

        scroll = ctk.CTkScrollableFrame(
            self._tab_content, fg_color="transparent",
            scrollbar_button_color=c["bg_hover"],
            scrollbar_button_hover_color=c["accent"]
        )
        scroll.pack(fill="both", expand=True)

        # ── Herramientas locales ──────────────────────────────────────────────
        herr_card = CardFrame(scroll, modo=self.modo)
        herr_card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            herr_card, text="Herramientas locales",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=c["text_primary"]
        ).pack(anchor="w", padx=p, pady=(p, 8))

        btn_grid = ctk.CTkFrame(herr_card, fg_color="transparent")
        btn_grid.pack(fill="x", padx=p, pady=(0, p))
        herramientas = [
            ("Checklist · banco de actividades",     self._abrir_terapeuta),
            ("Checklist · plantillas",               self._abrir_editor_checklist),
            ("Temporizador · presets",               self._abrir_editor_presets),
            ("Reg. de Pensamientos · pasos",         self._abrir_editor_pensamientos),
        ]
        for i, (label, cmd) in enumerate(herramientas):
            BotonSecundario(
                btn_grid, text=label, modo=self.modo,
                width=220, height=40, command=cmd
            ).pack(side="left", padx=(0, 8 if i < 3 else 0))

        # ── Banco de actividades ──────────────────────────────────────────────
        banco_card = CardFrame(scroll, modo=self.modo)
        banco_card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            banco_card, text="Banco de actividades conductuales",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=c["text_primary"]
        ).pack(anchor="w", padx=p, pady=(p, 2))
        ctk.CTkLabel(
            banco_card,
            text="Las actividades se sincronizan automáticamente al abrir cada app de paciente.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"]
        ).pack(anchor="w", padx=p, pady=(0, 8))

        banco_cols = ctk.CTkFrame(banco_card, fg_color="transparent")
        banco_cols.pack(fill="both", expand=True, padx=p, pady=(0, p))
        banco_cols.columnconfigure(0, weight=1)
        banco_cols.columnconfigure(1, weight=1)
        banco_cols.rowconfigure(0, weight=1)

        self._construir_col_banco_general(banco_cols)
        self._construir_col_actividades_paciente(banco_cols)

        # ── Asignaciones al paciente ──────────────────────────────────────────
        if not self._paciente_id:
            ctk.CTkLabel(
                scroll, text="Seleccioná un paciente para asignar tareas y recordatorios.",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=c["text_tertiary"]
            ).pack(pady=10)
            return

        asig_card = CardFrame(scroll, modo=self.modo)
        asig_card.pack(fill="both", expand=True)
        ctk.CTkLabel(
            asig_card, text="Asignaciones al paciente",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=c["text_primary"]
        ).pack(anchor="w", padx=p, pady=(p, 8))

        cols = ctk.CTkFrame(asig_card, fg_color="transparent")
        cols.pack(fill="both", expand=True, padx=p, pady=(0, p))
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)
        cols.rowconfigure(0, weight=1)

        self._construir_col_tareas(cols)
        self._construir_col_recordatorios(cols)

    def _construir_col_banco_general(self, parent):
        c = COLORS[self.modo]

        col = ctk.CTkFrame(parent, fg_color=c["bg_secondary"],
                           corner_radius=LAYOUT["radius_button"])
        col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(
            col, text="General — para todos los pacientes",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
            text_color=c["accent"]
        ).pack(anchor="w", padx=12, pady=(12, 6))

        form = ctk.CTkFrame(col, fg_color="transparent")
        form.pack(fill="x", padx=10, pady=(0, 4))

        ent_n = ctk.CTkEntry(
            form, placeholder_text="Nombre de la actividad...",
            fg_color=c["bg_input"], border_color=c["border"],
            text_color=c["text_primary"], height=32,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])
        )
        ent_n.pack(fill="x", pady=(0, 4))

        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 4))

        cmb_cat = ctk.CTkComboBox(
            row2, values=_CATEGORIAS_ACT, width=140,
            fg_color=c["bg_input"], border_color=c["border"],
            button_color=c["bg_hover"], button_hover_color=c["accent"],
            dropdown_fg_color=c["bg_surface"], dropdown_hover_color=c["bg_hover"],
            dropdown_text_color=c["text_primary"], text_color=c["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]), height=30
        )
        cmb_cat.set(_CATEGORIAS_ACT[0])
        cmb_cat.pack(side="left", padx=(0, 6))

        row3 = ctk.CTkFrame(form, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(row3, text="Ánimo:",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                     text_color=c["text_tertiary"]).pack(side="left", padx=(0, 6))
        seg_animo_bg = ctk.CTkSegmentedButton(
            row3, values=_ANIMO_SEGMENTOS,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            fg_color=c["bg_input"],
            selected_color=c["accent"], selected_hover_color=c["accent_hover"],
            unselected_color=c["bg_hover"], unselected_hover_color=c["bg_surface"],
            text_color=c["text_primary"], height=28
        )
        seg_animo_bg.set(_ANIMO_SEGMENTOS[0])
        seg_animo_bg.pack(side="left")

        lbl_ok = ctk.CTkLabel(
            form, text="",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=c["success"]
        )
        lbl_ok.pack(anchor="w", pady=(0, 2))

        scroll_a = ctk.CTkFrame(col, fg_color="transparent")
        scroll_a.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        def _cargar():
            for w in scroll_a.winfo_children():
                w.destroy()
            if not self._sb:
                return
            def _f():
                try:
                    res = (self._sb.table("activity_bank")
                           .select("id,nombre,categoria,animo_min,animo_max")
                           .eq("activa", True).order("nombre").execute())
                    items = res.data or []
                except Exception:
                    items = []
                self.after(0, lambda: _render(items))
            def _render(items):
                for w in scroll_a.winfo_children():
                    w.destroy()
                if not items:
                    ctk.CTkLabel(
                        scroll_a, text="Sin actividades en el banco.",
                        text_color=c["text_tertiary"],
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"])
                    ).pack(pady=8)
                    return
                for t in items:
                    fila = ctk.CTkFrame(scroll_a, fg_color=c["bg_list_item"],
                                        corner_radius=LAYOUT["radius_button"])
                    fila.pack(fill="x", pady=2)
                    lbl_animo = _ANIMO_LABEL.get((t.get("animo_min"), t.get("animo_max")), "Todos")
                    ctk.CTkLabel(
                        fila,
                        text=f"[{(t.get('categoria') or '')[:3]}] {(t.get('nombre') or '')[:24]}  · {lbl_animo}",
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                        text_color=c["text_primary"], anchor="w"
                    ).pack(side="left", padx=8, pady=4, fill="x", expand=True)
                    def _quitar(tid=t["id"]):
                        try:
                            self._sb.table("activity_bank").update({"activa": False}).eq("id", tid).execute()
                            _cargar()
                        except Exception:
                            pass
                    ctk.CTkButton(
                        fila, text="✕", width=24, height=24,
                        fg_color=c["error"], hover_color="#C83040",
                        text_color="#FFFFFF", corner_radius=6,
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                        command=_quitar
                    ).pack(side="right", padx=6, pady=4)
            threading.Thread(target=_f, daemon=True).start()

        def _agregar():
            nombre = ent_n.get().strip()
            if not nombre or not self._sb:
                lbl_ok.configure(text="Nombre requerido.", text_color=c["error"])
                return
            try:
                amin, amax = _ANIMO_MAP.get(seg_animo_bg.get(), (1, 4))
                self._sb.table("activity_bank").upsert({
                    "nombre": nombre,
                    "descripcion": "",
                    "categoria": cmb_cat.get(),
                    "animo_min": amin,
                    "animo_max": amax,
                    "activa": True,
                }, on_conflict="nombre").execute()
                ent_n.delete(0, "end")
                lbl_ok.configure(text="✓ Agregada al banco", text_color=c["success"])
                _cargar()
            except Exception as e:
                lbl_ok.configure(text=f"Error: {str(e)[:30]}", text_color=c["error"])

        BotonPrimario(
            form, text="+ Agregar al banco", modo=self.modo,
            height=36, command=_agregar
        ).pack(fill="x")

        _cargar()

    def _construir_col_actividades_paciente(self, parent):
        c = COLORS[self.modo]

        col = ctk.CTkFrame(parent, fg_color=c["bg_secondary"],
                           corner_radius=LAYOUT["radius_button"])
        col.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(
            col, text="Personalizadas — paciente seleccionado",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
            text_color=c["accent"]
        ).pack(anchor="w", padx=12, pady=(12, 6))

        if not self._paciente_id:
            ctk.CTkLabel(
                col, text="Seleccioná un paciente\npara gestionar sus actividades.",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=c["text_tertiary"], justify="center"
            ).pack(expand=True, pady=20)
            return

        form = ctk.CTkFrame(col, fg_color="transparent")
        form.pack(fill="x", padx=10, pady=(0, 4))

        ent_n = ctk.CTkEntry(
            form, placeholder_text="Nombre de la actividad...",
            fg_color=c["bg_input"], border_color=c["border"],
            text_color=c["text_primary"], height=32,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])
        )
        ent_n.pack(fill="x", pady=(0, 4))

        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 4))

        cmb_cat = ctk.CTkComboBox(
            row2, values=_CATEGORIAS_ACT, width=140,
            fg_color=c["bg_input"], border_color=c["border"],
            button_color=c["bg_hover"], button_hover_color=c["accent"],
            dropdown_fg_color=c["bg_surface"], dropdown_hover_color=c["bg_hover"],
            dropdown_text_color=c["text_primary"], text_color=c["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]), height=30
        )
        cmb_cat.set(_CATEGORIAS_ACT[0])
        cmb_cat.pack(side="left", padx=(0, 6))

        row3 = ctk.CTkFrame(form, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(row3, text="Ánimo:",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                     text_color=c["text_tertiary"]).pack(side="left", padx=(0, 6))
        seg_animo_pt = ctk.CTkSegmentedButton(
            row3, values=_ANIMO_SEGMENTOS,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            fg_color=c["bg_input"],
            selected_color=c["accent"], selected_hover_color=c["accent_hover"],
            unselected_color=c["bg_hover"], unselected_hover_color=c["bg_surface"],
            text_color=c["text_primary"], height=28
        )
        seg_animo_pt.set(_ANIMO_SEGMENTOS[0])
        seg_animo_pt.pack(side="left")

        lbl_ok = ctk.CTkLabel(
            form, text="",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=c["success"]
        )
        lbl_ok.pack(anchor="w", pady=(0, 2))

        scroll_a = ctk.CTkFrame(col, fg_color="transparent")
        scroll_a.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        pid = self._paciente_id

        def _cargar():
            for w in scroll_a.winfo_children():
                w.destroy()
            if not self._sb:
                return
            def _f():
                try:
                    res = (self._sb.table("patient_activities")
                           .select("id,nombre,categoria,animo_min,animo_max")
                           .eq("patient_id", pid).eq("activa", True)
                           .order("nombre").execute())
                    items = res.data or []
                except Exception:
                    items = []
                self.after(0, lambda: _render(items))
            def _render(items):
                for w in scroll_a.winfo_children():
                    w.destroy()
                if not items:
                    ctk.CTkLabel(
                        scroll_a, text="Sin actividades personalizadas.",
                        text_color=c["text_tertiary"],
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"])
                    ).pack(pady=8)
                    return
                for t in items:
                    fila = ctk.CTkFrame(scroll_a, fg_color=c["bg_list_item"],
                                        corner_radius=LAYOUT["radius_button"])
                    fila.pack(fill="x", pady=2)
                    lbl_animo = _ANIMO_LABEL.get((t.get("animo_min"), t.get("animo_max")), "Todos")
                    ctk.CTkLabel(
                        fila,
                        text=f"[{(t.get('categoria') or '')[:3]}] {(t.get('nombre') or '')[:24]}  · {lbl_animo}",
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                        text_color=c["text_primary"], anchor="w"
                    ).pack(side="left", padx=8, pady=4, fill="x", expand=True)
                    def _quitar(tid=t["id"]):
                        try:
                            self._sb.table("patient_activities").update({"activa": False}).eq("id", tid).execute()
                            _cargar()
                        except Exception:
                            pass
                    ctk.CTkButton(
                        fila, text="✕", width=24, height=24,
                        fg_color=c["error"], hover_color="#C83040",
                        text_color="#FFFFFF", corner_radius=6,
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                        command=_quitar
                    ).pack(side="right", padx=6, pady=4)
            threading.Thread(target=_f, daemon=True).start()

        def _agregar():
            nombre = ent_n.get().strip()
            if not nombre or not self._sb:
                lbl_ok.configure(text="Nombre requerido.", text_color=c["error"])
                return
            try:
                amin, amax = _ANIMO_MAP.get(seg_animo_pt.get(), (1, 4))
                self._sb.table("patient_activities").upsert({
                    "patient_id": pid,
                    "nombre": nombre,
                    "descripcion": "",
                    "categoria": cmb_cat.get(),
                    "animo_min": amin,
                    "animo_max": amax,
                    "activa": True,
                }, on_conflict="patient_id,nombre").execute()
                ent_n.delete(0, "end")
                lbl_ok.configure(text="✓ Agregada al paciente", text_color=c["success"])
                _cargar()
            except Exception as e:
                lbl_ok.configure(text=f"Error: {str(e)[:30]}", text_color=c["error"])

        BotonPrimario(
            form, text="+ Agregar al paciente", modo=self.modo,
            height=36, command=_agregar
        ).pack(fill="x")

        _cargar()

    def _construir_col_tareas(self, parent):
        c = COLORS[self.modo]
        p = LAYOUT["padding_card"]

        col = ctk.CTkFrame(parent, fg_color=c["bg_secondary"],
                           corner_radius=LAYOUT["radius_button"])
        col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(
            col, text="Tareas asignadas",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
            text_color=c["accent"]
        ).pack(anchor="w", padx=12, pady=(12, 6))

        # Formulario mínimo
        form = ctk.CTkFrame(col, fg_color="transparent")
        form.pack(fill="x", padx=10, pady=(0, 6))

        ent_desc = ctk.CTkEntry(
            form, placeholder_text="Descripción de la tarea...",
            fg_color=c["bg_input"], border_color=c["border"],
            text_color=c["text_primary"], height=32,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])
        )
        ent_desc.pack(fill="x", pady=(0, 4))

        row_sec = ctk.CTkFrame(form, fg_color="transparent")
        row_sec.pack(fill="x", pady=(0, 6))

        cmb_sec = ctk.CTkComboBox(
            row_sec, values=["Mañana", "Tarde", "Noche"], width=130,
            fg_color=c["bg_input"], border_color=c["border"],
            button_color=c["bg_hover"], button_hover_color=c["accent"],
            dropdown_fg_color=c["bg_surface"], dropdown_hover_color=c["bg_hover"],
            dropdown_text_color=c["text_primary"],
            text_color=c["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]), height=30
        )
        cmb_sec.set("Tarde")
        cmb_sec.pack(side="left", padx=(0, 8))

        lbl_ok_t = ctk.CTkLabel(
            row_sec, text="",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=c["success"]
        )
        lbl_ok_t.pack(side="left")

        row_animo_t = ctk.CTkFrame(form, fg_color="transparent")
        row_animo_t.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            row_animo_t, text="Ánimo:", width=48, anchor="w",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"]
        ).pack(side="left")
        cmb_animo_t = ctk.CTkComboBox(
            row_animo_t, values=["Todos", "Bajo", "Medio", "Alto"], width=110,
            fg_color=c["bg_input"], border_color=c["border"],
            button_color=c["bg_hover"], button_hover_color=c["accent"],
            dropdown_fg_color=c["bg_surface"], dropdown_hover_color=c["bg_hover"],
            dropdown_text_color=c["text_primary"],
            text_color=c["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]), height=30
        )
        cmb_animo_t.set("Todos")
        cmb_animo_t.pack(side="left")

        scroll_t = ctk.CTkFrame(col, fg_color="transparent")
        scroll_t.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        def _sec_db(val: str) -> str:
            return {"Mañana": "manana", "Tarde": "tarde", "Noche": "noche"}.get(val, "tarde")

        def _cargar_tareas():
            for w in scroll_t.winfo_children():
                w.destroy()
            if not self._sb:
                return
            def _f():
                try:
                    res = (self._sb.table("assigned_tasks")
                           .select("id,descripcion,seccion,animo_rango")
                           .eq("patient_id", self._paciente_id)
                           .eq("activa", True).execute())
                    items = res.data or []
                except Exception:
                    items = []
                self.after(0, lambda: _render(items))
            def _render(items):
                for w in scroll_t.winfo_children():
                    w.destroy()
                if not items:
                    ctk.CTkLabel(
                        scroll_t, text="Sin tareas asignadas.",
                        text_color=c["text_tertiary"],
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"])
                    ).pack(pady=8)
                    return
                for t in items:
                    fila = ctk.CTkFrame(scroll_t, fg_color=c["bg_list_item"],
                                        corner_radius=LAYOUT["radius_button"])
                    fila.pack(fill="x", pady=2)
                    sec = t.get("seccion","")[:3].upper()
                    animo = t.get("animo_rango") or ""
                    desc_txt = t.get("descripcion","")[:30]
                    label_txt = f"{sec}  {desc_txt}" + (f"  [{animo}]" if animo else "")
                    ctk.CTkLabel(
                        fila,
                        text=label_txt,
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                        text_color=c["text_primary"], anchor="w"
                    ).pack(side="left", padx=8, pady=4, fill="x", expand=True)
                    def _quitar(tid=t["id"]):
                        try:
                            self._sb.table("assigned_tasks").update({"activa": False}).eq("id", tid).execute()
                            _cargar_tareas()
                        except Exception:
                            pass
                    ctk.CTkButton(
                        fila, text="✕", width=24, height=24,
                        fg_color=c["error"], hover_color="#C83040",
                        text_color="#FFFFFF", corner_radius=6,
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                        command=_quitar
                    ).pack(side="right", padx=6, pady=4)
            threading.Thread(target=_f, daemon=True).start()

        def _asignar_tarea():
            desc = ent_desc.get().strip()
            sec = _sec_db(cmb_sec.get())
            if not desc or not self._sb:
                lbl_ok_t.configure(text="Requerido.", text_color=c["error"])
                return
            animo_val = cmb_animo_t.get()
            animo_rango = None if animo_val == "Todos" else animo_val
            try:
                self._sb.table("assigned_tasks").upsert({
                    "patient_id": self._paciente_id,
                    "descripcion": desc,
                    "seccion": sec,
                    "categoria": "Logro",
                    "animo_rango": animo_rango,
                    "activa": True,
                }, on_conflict="patient_id,descripcion").execute()
                ent_desc.delete(0, "end")
                lbl_ok_t.configure(text="✓ Asignada", text_color=c["success"])
                _cargar_tareas()
            except Exception as e:
                lbl_ok_t.configure(text=f"Error: {str(e)[:30]}", text_color=c["error"])

        BotonPrimario(
            form, text="+ Asignar tarea", modo=self.modo, height=36, command=_asignar_tarea
        ).pack(fill="x")

        _cargar_tareas()

    def _construir_col_recordatorios(self, parent):
        c = COLORS[self.modo]
        p = LAYOUT["padding_card"]

        col = ctk.CTkFrame(parent, fg_color=c["bg_secondary"],
                           corner_radius=LAYOUT["radius_button"])
        col.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(
            col, text="Recordatorios asignados",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
            text_color=c["accent"]
        ).pack(anchor="w", padx=12, pady=(12, 6))

        form = ctk.CTkFrame(col, fg_color="transparent")
        form.pack(fill="x", padx=10, pady=(0, 6))

        row_hr = ctk.CTkFrame(form, fg_color="transparent")
        row_hr.pack(fill="x", pady=(0, 4))
        ent_hora = ctk.CTkEntry(
            row_hr, placeholder_text="09:00", width=80,
            fg_color=c["bg_input"], border_color=c["border"],
            text_color=c["text_primary"], height=32,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])
        )
        ent_hora.pack(side="left", padx=(0, 8))
        ent_msg = ctk.CTkEntry(
            row_hr, placeholder_text="Mensaje del recordatorio...",
            fg_color=c["bg_input"], border_color=c["border"],
            text_color=c["text_primary"], height=32,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])
        )
        ent_msg.pack(side="left", fill="x", expand=True)

        lbl_ok_r = ctk.CTkLabel(
            form, text="",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=c["success"]
        )
        lbl_ok_r.pack(anchor="w", pady=(0, 4))

        scroll_r = ctk.CTkFrame(col, fg_color="transparent")
        scroll_r.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        def _cargar_recordatorios():
            for w in scroll_r.winfo_children():
                w.destroy()
            if not self._sb:
                return
            def _f():
                try:
                    res = (self._sb.table("assigned_reminders")
                           .select("id,hora,mensaje")
                           .eq("patient_id", self._paciente_id)
                           .eq("activa", True).execute())
                    items = res.data or []
                except Exception:
                    items = []
                self.after(0, lambda: _render(items))
            def _render(items):
                for w in scroll_r.winfo_children():
                    w.destroy()
                if not items:
                    ctk.CTkLabel(
                        scroll_r, text="Sin recordatorios asignados.",
                        text_color=c["text_tertiary"],
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"])
                    ).pack(pady=8)
                    return
                for t in items:
                    fila = ctk.CTkFrame(scroll_r, fg_color=c["bg_list_item"],
                                        corner_radius=LAYOUT["radius_button"])
                    fila.pack(fill="x", pady=2)
                    ctk.CTkLabel(
                        fila,
                        text=f"{t.get('hora','')}  —  {t.get('mensaje','')[:34]}",
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                        text_color=c["text_primary"], anchor="w"
                    ).pack(side="left", padx=8, pady=4, fill="x", expand=True)
                    def _quitar(tid=t["id"]):
                        try:
                            self._sb.table("assigned_reminders").update({"activa": False}).eq("id", tid).execute()
                            _cargar_recordatorios()
                        except Exception:
                            pass
                    ctk.CTkButton(
                        fila, text="✕", width=24, height=24,
                        fg_color=c["error"], hover_color="#C83040",
                        text_color="#FFFFFF", corner_radius=6,
                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                        command=_quitar
                    ).pack(side="right", padx=6, pady=4)
            threading.Thread(target=_f, daemon=True).start()

        def _asignar_rec():
            hora = ent_hora.get().strip()
            msg = ent_msg.get().strip()
            if not hora or not msg or not self._sb:
                lbl_ok_r.configure(text="Hora y mensaje requeridos.", text_color=c["error"])
                return
            try:
                self._sb.table("assigned_reminders").upsert({
                    "patient_id": self._paciente_id,
                    "hora": hora, "mensaje": msg,
                    "dias": "1,2,3,4,5,6,7", "activa": True,
                }, on_conflict="patient_id,hora,mensaje").execute()
                ent_hora.delete(0, "end")
                ent_msg.delete(0, "end")
                lbl_ok_r.configure(text="✓ Asignado", text_color=c["success"])
                _cargar_recordatorios()
            except Exception as e:
                lbl_ok_r.configure(text=f"Error: {str(e)[:30]}", text_color=c["error"])

        BotonPrimario(
            form, text="+ Asignar recordatorio", modo=self.modo, height=36, command=_asignar_rec
        ).pack(fill="x")

        _cargar_recordatorios()

    # ── Tab: Permisos del paciente ────────────────────────────────────────────

    def _tab_permisos(self):
        c = COLORS[self.modo]
        p = LAYOUT["padding_card"]

        card = CardFrame(self._tab_content, modo=self.modo)
        card.pack(fill="both", expand=True)
        ctk.CTkLabel(
            card, text="Permisos del paciente",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"]
        ).pack(anchor="w", padx=p, pady=(p, 4))
        ctk.CTkLabel(
            card,
            text="Define qué puede hacer el paciente en cada app. Los cambios se sincronizan en la próxima apertura.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"]
        ).pack(anchor="w", padx=p, pady=(0, 16))

        if not self._paciente_id:
            ctk.CTkLabel(
                card, text="Seleccioná un paciente primero.",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=c["text_tertiary"]
            ).pack(anchor="w", padx=p)
            return

        perms_actuales: dict = {}
        if self._sb:
            try:
                res = (self._sb.table("patients")
                       .select("perm_checklist_activacion,perm_checklist_manual,"
                               "perm_temporizador_manual,perm_recordatorios_manual")
                       .eq("patient_id", self._paciente_id)
                       .maybe_single().execute())
                if res.data:
                    perms_actuales = res.data
            except Exception:
                pass

        permisos = [
            ("perm_checklist_activacion",
             "Checklist — proponer tareas por activación conductual", True),
            ("perm_checklist_manual",
             "Checklist — agregar tareas manualmente", False),
            ("perm_temporizador_manual",
             "Temporizador — agregar actividades manualmente", False),
            ("perm_recordatorios_manual",
             "Recordatorios — modificar recordatorios manualmente", False),
        ]

        self._perm_vars: dict[str, ctk.BooleanVar] = {}
        for key, label, default in permisos:
            val = perms_actuales.get(key, default)
            var = ctk.BooleanVar(value=bool(val))
            self._perm_vars[key] = var

            row = ctk.CTkFrame(card, fg_color=c["bg_list_item"],
                               corner_radius=LAYOUT["radius_button"])
            row.pack(fill="x", padx=p, pady=3)
            ctk.CTkLabel(
                row, text=label,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=c["text_primary"], anchor="w"
            ).pack(side="left", padx=12, pady=10)
            ctk.CTkSwitch(
                row, text="", variable=var, width=44,
                button_color=c["accent"], button_hover_color=c["accent"],
                progress_color=c["accent"], fg_color=c["bg_hover"]
            ).pack(side="right", padx=12, pady=8)

        ctk.CTkFrame(card, height=1, fg_color=c["border"], corner_radius=0).pack(
            fill="x", padx=p, pady=(12, 8))

        def _guardar():
            if not self._sb:
                mostrar_mensaje(self, "Sin conexión",
                                "Base de datos no disponible.", tipo="warning", modo=self.modo)
                return
            datos = {k: v.get() for k, v in self._perm_vars.items()}
            try:
                self._sb.table("patients").update(datos).eq("patient_id", self._paciente_id).execute()
                mostrar_mensaje(self, "Guardado",
                                "Permisos actualizados.", tipo="success", modo=self.modo)
            except Exception as e:
                mostrar_mensaje(self, "Error", str(e)[:120], tipo="error", modo=self.modo)

        BotonPrimario(
            card, text="Guardar permisos", modo=self.modo,
            width=180, height=40, command=_guardar
        ).pack(anchor="e", padx=p, pady=(0, p))

    # ── Herramientas locales ──────────────────────────────────────────────────

    def _abrir_terapeuta(self):
        try:
            import terapeuta as _ter
            _ter.VentanaTerapeuta(self, modo=self.modo)
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo abrir: {e}", tipo="error", modo=self.modo)

    def _abrir_editor_checklist(self):
        try:
            import editor_checklist as _ec
            _ec.VentanaEditorChecklist(self, modo=self.modo)
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo abrir: {e}", tipo="error", modo=self.modo)

    def _abrir_editor_presets(self):
        try:
            import editor_presets as _ep
            _ep.VentanaEditorPresets(self, modo=self.modo)
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo abrir: {e}", tipo="error", modo=self.modo)

    def _abrir_editor_pensamientos(self):
        try:
            import editor_pensamientos as _ep
            _ep.VentanaEditorPensamientos(self, modo=self.modo)
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo abrir: {e}", tipo="error", modo=self.modo)


if __name__ == "__main__":
    app = HubProfesional(modo="dark")
    app.mainloop()
