import sys
import os
import tkinter as tk
import json

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas, guardar_config, leer_config
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    InputTexto, AreaTexto, mostrar_acerca_de, obtener_icono_solido,
    mostrar_mensaje, NMToplevel, aplicar_captionbar_flush,
    _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy, hora_actual, fecha_legible, color_por_puntaje_exacto


# ── Catálogo clínico TCC ────────────────────────────────────────────────────

EMOCIONES_LISTA = [
    "Ansiedad", "Tristeza", "Enojo", "Miedo",
    "Culpa", "Vergüenza", "Alegría", "Otra",
]

DISTORSIONES = {
    "Catastrofismo":
        "Imaginás que ocurrirá lo peor, aunque la evidencia no lo justifique.\n"
        "Ej: 'Si me equivoco en esto, todo estará arruinado para siempre'.",
    "Sobregeneralización":
        "Sacás una conclusión general negativa a partir de un solo evento.\n"
        "Palabras clave: 'siempre', 'nunca', 'todo el tiempo'.",
    "Lectura de mente":
        "Asumís que sabés lo que otros piensan o sienten, sin evidencia real.\n"
        "Ej: 'Sé que les parecí aburrido/a'.",
    "Adivinación del futuro":
        "Predecís que las cosas saldrán mal como si fuera un hecho inevitable.\n"
        "Ej: 'Esta entrevista va a salir mal, lo sé'.",
    "Pensamiento todo o nada":
        "Ves las situaciones en extremos: éxito total o fracaso total, sin matices.\n"
        "Ej: 'Si no lo hago perfecto, soy un fracaso completo'.",
    "Personalización":
        "Te atribuís la responsabilidad de eventos negativos que no dependen solo de vos.\n"
        "Ej: 'Si están de mal humor, es por algo que hice yo'.",
    "Filtro negativo":
        "Te concentrás únicamente en lo negativo, ignorando lo que salió bien.\n"
        "Ej: 'Todo salió mal' (aunque varias cosas salieron bien).",
    "Descalificar lo positivo":
        "Cuando algo bueno ocurre, lo descartás como suerte o irrelevante.\n"
        "Ej: 'Me felicitaron, pero fue suerte — no cuenta'.",
    "Deberías":
        "Aplicás reglas rígidas sobre cómo vos u otros deberían comportarse.\n"
        "Genera culpa si vos las incumplís, o enojo si las incumplen otros.",
    "Razonamiento emocional":
        "Creés que algo es verdad porque así lo sentís, sin base objetiva.\n"
        "Ej: 'Me siento un fracasado, entonces lo soy'.",
}

_KWORDS = {
    "Catastrofismo":          ["terrible", "catástrofe", "horrible", "lo peor", "desastre", "todo se va a arruinar", "todo va a salir mal"],
    "Sobregeneralización":    ["siempre", "nunca", "jamás", "todo el tiempo", "cada vez que", "todos me"],
    "Lectura de mente":       ["sé que piensan", "deben pensar", "piensan que", "creen que", "van a pensar que"],
    "Adivinación del futuro": ["va a salir mal", "sé que va a", "seguramente va a", "estoy seguro de que va"],
    "Pensamiento todo o nada":["completamente", "totalmente", "si no es perfecto", "fracaso total", "todo o nada"],
    "Personalización":        ["por mi culpa", "es mi culpa", "yo lo causé", "por mi causa"],
    "Filtro negativo":        ["solo hay cosas malas", "nada bueno", "solo sale mal", "lo único que pasa"],
    "Descalificar lo positivo":["fue suerte", "no cuenta", "cualquiera podría", "eso no vale"],
    "Deberías":               ["debería", "tengo que", "habría que", "debo", "debería haber"],
    "Razonamiento emocional": ["lo siento y es así", "si lo siento es verdad", "lo sé porque lo siento"],
}

TOTAL_PASOS   = 6
NOMBRES_PASOS = ["Situación", "Emoción", "Pensamiento", "Análisis", "Respuesta", "Cierre"]


_CONF_PASOS_DEFECTO = {
    "1": "Describí el contexto: dónde estabas, qué hacías, con quién. Sé específico/a.",
    "2": "Identificar la emoción presente permite comprender la respuesta cognitiva asociada. Las emociones son información, no el problema en sí.",
    "3": "El pensamiento automático aparece de forma rápida e involuntaria. Registralo sin juzgarlo.",
    "4": "Identificá distorsiones cognitivas y buscá evidencia real — el corazón del trabajo cognitivo.",
    "5": {
        "subtitulo": "Basándote en la evidencia recopilada, formulá una perspectiva más realista y equilibrada de la situación.",
        "infobox": "Reformulá el pensamiento original considerando toda la evidencia analizada. Una perspectiva alternativa debe ser realista, equilibrada y fundamentada en hechos concretos.",
    },
    "6": "Resumen clínico del registro — basado en el modelo de Beck.",
}

_DISTORSIONES_DEFECTO = [
    {"nombre": k, "descripcion": v, "keywords": _KWORDS.get(k, [])}
    for k, v in DISTORSIONES.items()
]


def _cargar_conf_pensamientos() -> dict:
    raw = leer_config("pensamientos_config", "")
    if raw:
        try:
            conf = json.loads(raw)
            if "pasos" in conf and "distorsiones" in conf:
                return conf
        except Exception:
            pass
    return {
        "pasos": {str(k): (v if isinstance(v, dict) else {"subtitulo": v})
                  for k, v in _CONF_PASOS_DEFECTO.items()},
        "distorsiones": [d.copy() for d in _DISTORSIONES_DEFECTO],
    }


def _sugerir_distorsiones(texto: str, distorsiones_conf: list) -> list:
    t = texto.lower()
    sugeridas = []
    for d in distorsiones_conf:
        kws = d.get("keywords", [])
        if any(k in t for k in kws):
            sugeridas.append(d["nombre"])
    return sugeridas


def _generar_cierre_tcc(datos: dict) -> list:
    """Devuelve lista de (título, texto) para el paso 6."""
    emocion      = datos.get("emocion", "desconocida")
    intensidad   = int(datos.get("intensidad", 5))
    distorsiones = datos.get("distorsiones_list", [])

    nivel = "alta" if intensidad >= 7 else "moderada" if intensidad >= 4 else "baja"

    secs = []

    secs.append((
        "Emoción predominante",
        f"{emocion} — intensidad {nivel} ({intensidad}/10).\n"
        + ("Un nivel alto de malestar merece atención sostenida con tu terapeuta." if intensidad >= 7
           else "Un nivel moderado: hay espacio real para trabajar con el pensamiento." if intensidad >= 4
           else "El malestar era manejable, lo cual facilita la reestructuración.")
    ))

    if distorsiones:
        secs.append((
            "Patrones cognitivos identificados",
            f"{', '.join(distorsiones)}.\n"
            "Nombrar la distorsión es el primer paso para cuestionarla con evidencia real."
        ))
    else:
        secs.append((
            "Patrones cognitivos",
            "No identificaste distorsiones específicas en este registro. "
            "Podés revisarlo con tu terapeuta para un análisis más profundo."
        ))

    if intensidad >= 8:
        sig = "Dado el nivel de malestar, compartí este registro con tu terapeuta en la próxima sesión."
    elif distorsiones:
        sig = (
            f"Observá en los próximos días si el patrón '{distorsiones[0]}' "
            "aparece en otras situaciones. La repetición revela el esquema subyacente."
        )
    else:
        sig = "Seguí registrando con consistencia. La práctica regular es la base del cambio cognitivo."
    secs.append(("Siguiente paso sugerido", sig))

    return secs


# ── Tooltip simple (sin dependencia externa) ────────────────────────────────

class _Tooltip:
    def __init__(self, widget, text: str, modo: str = "dark"):
        self._win  = None
        self._text = text
        self._modo = modo
        widget.bind("<Enter>",   self._show, add="+")
        widget.bind("<Leave>",   self._hide, add="+")
        widget.bind("<Destroy>", lambda e: self._hide(), add="+")

    def _show(self, event=None):
        if self._win or not event:
            return
        try:
            colores = COLORS[self._modo]
            w = event.widget
            x = w.winfo_rootx() + 26
            y = w.winfo_rooty() + 30
            self._win = tk.Toplevel(w)
            self._win.wm_overrideredirect(True)
            self._win.wm_geometry(f"+{x}+{y}")
            self._win.configure(bg=colores["accent"])
            outer = tk.Frame(self._win, bg=colores["accent"], padx=1, pady=1)
            outer.pack()
            tk.Label(
                outer, text=self._text,
                font=("Segoe UI", 10),
                fg=colores["text_secondary"],
                bg=colores["bg_surface"],
                wraplength=300, justify="left",
                padx=10, pady=7,
            ).pack()
            self._win.lift()
        except Exception:
            pass

    def _hide(self, event=None):
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None


# ── App ─────────────────────────────────────────────────────────────────────

class PensamientosApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        inicializar_tablas()
        try:
            from shared.sync import sync_al_abrir as _sync_al_abrir
            _sync_al_abrir()
        except Exception:
            pass
        self.modo = leer_config("theme", "dark")
        self.paso_actual   = 1
        self._filtro_buscar = ""
        self._panel_activo = "historial"
        self._conf = _cargar_conf_pensamientos()

        self.title("NeuroMood · Registro de Pensamientos")
        w, h = 1040, 720
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(920, 680)
        self.configure(fg_color=COLORS[self.modo]["bg_primary"])

        try:
            self.iconbitmap(obtener_icono_solido())
        except Exception:
            pass

        self._prev_state = "zoomed"
        self.after(50, lambda: self.state("zoomed"))
        self.bind("<Configure>", self._on_configure)

        self._construir_ui()
        self.after(1000, self._poll_tema)

    def _on_configure(self, event):
        if event.widget is not self:
            return
        estado = self.state()
        if self._prev_state == "zoomed" and estado == "normal":
            self.after(20, self._recentrar)
        self._prev_state = estado

    def _recentrar(self):
        if self.state() != "normal":
            return
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Build ───────────────────────────────────────────────────────────────

    def _construir_ui(self):
        for child in self.winfo_children():
            child.destroy()
        colores = COLORS[self.modo]
        self.configure(fg_color=colores["bg_primary"])

        HeaderFrame(
            self,
            titulo="Registro de Pensamientos",
            subtitulo="Reestructuración cognitiva · Modelo A-B-C-D (Beck)",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        ).pack(fill="x")

        barra = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=40, corner_radius=0)
        barra.pack(fill="x", side="bottom")
        barra.pack_propagate(False)
        BotonSecundario(
            barra, text="Acerca de", modo=self.modo, width=100, height=30,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=12, pady=5)

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True,
                       padx=LAYOUT["padding_container"], pady=LAYOUT["padding_container"])

        col_izq = ctk.CTkFrame(contenido, fg_color="transparent")
        col_izq.pack(side="left", fill="both", expand=True, padx=(0, 12))

        col_der = ctk.CTkFrame(contenido, fg_color="transparent", width=340)
        col_der.pack(side="right", fill="both", padx=(12, 0))

        self._construir_formulario(col_izq)
        self._construir_panel_der(col_der)

    # ── Form scaffold ───────────────────────────────────────────────────────

    def _construir_formulario(self, parent):
        colores = COLORS[self.modo]

        prog = ctk.CTkFrame(parent, fg_color="transparent", height=28)
        prog.pack(fill="x", pady=(0, 4))
        prog.pack_propagate(False)
        _c_on = colores["success"] if self.modo == "light" else colores["accent"]
        for i in range(TOTAL_PASOS):
            color = _c_on if (i + 1) <= self.paso_actual else colores["progress_track"]
            ctk.CTkFrame(prog, fg_color=color, corner_radius=4, height=6).pack(
                side="left", padx=2, pady=11, fill="x", expand=True
            )

        ctk.CTkLabel(
            parent,
            text=f"Paso {self.paso_actual} de {TOTAL_PASOS} — {NOMBRES_PASOS[self.paso_actual - 1]}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(anchor="w", pady=(0, 4))

        self.card_form = CardFrame(parent, modo=self.modo)
        self.card_form.pack(fill="both", expand=True)

        {1: self._paso_situacion,
         2: self._paso_emocion,
         3: self._paso_pensamiento,
         4: self._paso_analisis,
         5: self._paso_respuesta,
         6: self._paso_cierre}[self.paso_actual]()

    def _titulo_paso(self, titulo: str, subtitulo: str):
        colores = COLORS[self.modo]
        ctk.CTkLabel(
            self.card_form, text=titulo,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 2), anchor="w")
        ctk.CTkLabel(
            self.card_form, text=subtitulo,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"],
            wraplength=600, justify="left"
        ).pack(padx=LAYOUT["padding_card"], anchor="w", pady=(0, 6))

    def _scroll_area(self) -> ctk.CTkScrollableFrame:
        colores = COLORS[self.modo]
        s = ctk.CTkScrollableFrame(
            self.card_form, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        s.pack(fill="both", expand=True, padx=LAYOUT["padding_card"], pady=(0, 6))
        return s

    def _nav(self, anterior=False, siguiente=False, guardar=False, texto_sig="Siguiente →"):
        colores = COLORS[self.modo]
        nav = ctk.CTkFrame(self.card_form, fg_color="transparent")
        nav.pack(side="bottom", fill="x",
                 padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))
        _kw = {"fg_color": colores["success"], "hover_color": "#4A8A70"} if self.modo == "light" else {}
        if anterior:
            BotonSecundario(nav, text="← Anterior", modo=self.modo,
                            command=self._paso_anterior).pack(side="left")
        if siguiente:
            BotonPrimario(nav, text=texto_sig, modo=self.modo,
                          command=self._siguiente_paso, **_kw).pack(side="right")
        if guardar:
            BotonPrimario(nav, text="Guardar registro", modo=self.modo,
                          command=self._guardar, **_kw).pack(side="right")

    def _info_box(self, parent, texto: str):
        colores = COLORS[self.modo]
        box = ctk.CTkFrame(parent, fg_color=colores["accent_subtle"], corner_radius=8)
        box.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            box, text=texto,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["accent"] if self.modo == "dark" else colores["info"],
            wraplength=520, justify="left"
        ).pack(padx=12, pady=8)

    def _separador(self, parent):
        ctk.CTkFrame(parent, fg_color=COLORS[self.modo]["border"],
                     height=1, corner_radius=0).pack(fill="x", pady=10)

    # ── Steps ───────────────────────────────────────────────────────────────

    def _paso_situacion(self):
        self._titulo_paso(
            "¿Qué estaba pasando?",
            self._conf["pasos"]["1"]["subtitulo"]
        )
        self._nav(siguiente=True)
        scroll = self._scroll_area()
        colores = COLORS[self.modo]

        self.txt_situacion = AreaTexto(scroll, modo=self.modo, height=170)
        self.txt_situacion.pack(fill="x", pady=(0, 10))
        if hasattr(self, '_datos') and self._datos.get("situacion"):
            self.txt_situacion.insert("1.0", self._datos["situacion"])

        ctk.CTkLabel(
            scroll,
            text="Esta herramienta es de apoyo psicoeducativo y no reemplaza la atención profesional.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["text_tertiary"], wraplength=560
        ).pack(pady=(4, 0))

    def _paso_emocion(self):
        self._titulo_paso(
            "¿Qué sentiste?",
            self._conf["pasos"]["2"]["subtitulo"]
        )
        self._nav(anterior=True, siguiente=True)
        scroll = self._scroll_area()
        colores = COLORS[self.modo]

        ctk.CTkLabel(
            scroll, text="Emoción principal",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["text_secondary"]
        ).pack(anchor="w", pady=(0, 4))

        combo_row = ctk.CTkFrame(scroll, fg_color="transparent")
        combo_row.pack(fill="x", pady=(0, 6))

        _btn_c = colores["success"] if self.modo == "light" else colores["accent"]
        _btn_hv = "#4A8A70" if self.modo == "light" else colores["accent_hover"]
        self.combo_emocion = ctk.CTkComboBox(
            combo_row, values=EMOCIONES_LISTA, width=190,
            fg_color=colores["bg_input"],
            border_color=colores["border"],
            button_color=_btn_c,
            button_hover_color=_btn_hv,
            dropdown_fg_color=colores["bg_surface"],
            dropdown_text_color=colores["text_primary"],
            dropdown_hover_color=colores["bg_hover"],
            text_color=colores["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
        )
        guardada = self._datos.get("emocion", "") if hasattr(self, '_datos') else ""
        if guardada in EMOCIONES_LISTA:
            self.combo_emocion.set(guardada)
        else:
            self.combo_emocion.set("Ansiedad")
        self.combo_emocion.pack(side="left", padx=(0, 10))

        self.entry_emocion_libre = InputTexto(
            combo_row, modo=self.modo, width=160,
            placeholder_text="Otra emoción..."
        )
        self.entry_emocion_libre.pack(side="left")
        if guardada and guardada not in EMOCIONES_LISTA:
            self.combo_emocion.set("Otra")
            self.entry_emocion_libre.insert(0, guardada)

        ctk.CTkLabel(
            scroll, text="Intensidad  (1 = casi nada  ·  10 = máxima)",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["text_secondary"]
        ).pack(anchor="w", pady=(12, 4))

        s_row = ctk.CTkFrame(scroll, fg_color="transparent")
        s_row.pack(fill="x", pady=(0, 2))
        for txt, side in [("1", "left"), ("10", "right")]:
            ctk.CTkLabel(s_row, text=txt, text_color=colores["text_tertiary"],
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])).pack(side=side)

        self.intensidad_val = int(self._datos.get("intensidad", 5)) if hasattr(self, '_datos') else 5
        _ic = color_por_puntaje_exacto(self.intensidad_val)
        self.slider_intensidad = ctk.CTkSlider(
            s_row, from_=1, to=10, number_of_steps=10,
            progress_color=_ic, button_color=_ic, button_hover_color=_ic,
            fg_color=colores["progress_track"], command=self._on_intensidad
        )
        self.slider_intensidad.set(self.intensidad_val)
        self.slider_intensidad.pack(side="left", fill="x", expand=True, padx=8)

        self.lbl_intensidad = ctk.CTkLabel(
            scroll, text=str(self.intensidad_val),
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h2"], "bold"),
            text_color=_ic
        )
        self.lbl_intensidad.pack(pady=(0, 6))

    def _paso_pensamiento(self):
        self._titulo_paso(
            "¿Qué pensaste en ese momento?",
            self._conf["pasos"]["3"]["subtitulo"]
        )
        self._nav(anterior=True, siguiente=True)
        scroll = self._scroll_area()
        colores = COLORS[self.modo]

        self._info_box(
            scroll,
            "Los pensamientos automáticos son interpretaciones instantáneas de los eventos. "
            "No siempre reflejan la realidad — pueden estar distorsionados sin que lo notemos. "
            "Anotá exactamente qué apareció en tu mente."
        )

        self.txt_pensamiento = AreaTexto(scroll, modo=self.modo, height=130)
        self.txt_pensamiento.pack(fill="x", pady=(0, 14))
        if hasattr(self, '_datos') and self._datos.get("pensamiento"):
            self.txt_pensamiento.insert("1.0", self._datos["pensamiento"])

        ctk.CTkLabel(
            scroll, text="¿Cuánto creés en ese pensamiento? (%)",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["text_secondary"]
        ).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            scroll, text="Antes de revisar la evidencia — ¿qué tan verdadero te parece ahora mismo?",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["text_tertiary"]
        ).pack(anchor="w", pady=(0, 6))

        s_row = ctk.CTkFrame(scroll, fg_color="transparent")
        s_row.pack(fill="x", pady=(0, 2))
        for txt, side in [("0%", "left"), ("100%", "right")]:
            ctk.CTkLabel(s_row, text=txt, text_color=colores["text_tertiary"],
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])).pack(side=side)

        self.creencia_antes_val = int(self._datos.get("creencia_antes", 80)) if hasattr(self, '_datos') else 80
        _cc = color_por_puntaje_exacto(round(self.creencia_antes_val / 10))
        self.slider_creencia_antes = ctk.CTkSlider(
            s_row, from_=0, to=100, number_of_steps=100,
            progress_color=_cc, button_color=_cc, button_hover_color=_cc,
            fg_color=colores["progress_track"], command=self._on_creencia_antes
        )
        self.slider_creencia_antes.set(self.creencia_antes_val)
        self.slider_creencia_antes.pack(side="left", fill="x", expand=True, padx=8)

        self.lbl_creencia_antes = ctk.CTkLabel(
            scroll, text=f"{self.creencia_antes_val}%",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h2"], "bold"),
            text_color=_cc
        )
        self.lbl_creencia_antes.pack(pady=(0, 4))

    def _paso_analisis(self):
        self._titulo_paso(
            "Análisis del pensamiento",
            self._conf["pasos"]["4"]["subtitulo"]
        )
        self._nav(anterior=True, siguiente=True)
        scroll = self._scroll_area()
        colores = COLORS[self.modo]

        ctk.CTkLabel(
            scroll, text="Distorsiones cognitivas",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["text_secondary"]
        ).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            scroll, text="Pasá el cursor sobre cada nombre para ver la explicación. Marcá las que reconocés.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["text_tertiary"]
        ).pack(anchor="w", pady=(0, 6))

        distorsiones_conf = self._conf["distorsiones"]
        dist_dict = {d["nombre"]: d["descripcion"] for d in distorsiones_conf}

        sugeridas = _sugerir_distorsiones(
            self._datos.get("pensamiento", "") if hasattr(self, '_datos') else "",
            distorsiones_conf
        )
        guardadas = self._datos.get("distorsiones_list", []) if hasattr(self, '_datos') else []

        dist_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        dist_frame.pack(fill="x", pady=(0, 6))

        _cb_fg = colores["success"] if self.modo == "light" else colores["accent"]
        _cb_hv = "#4A8A70" if self.modo == "light" else colores["accent_hover"]
        self.distorsion_vars = {}

        for i, (nombre, descripcion) in enumerate((d["nombre"], d["descripcion"]) for d in distorsiones_conf):
            var = ctk.BooleanVar(value=(nombre in guardadas) or (nombre in sugeridas))
            if nombre in guardadas:
                var.set(True)
            self.distorsion_vars[nombre] = var

            fila = ctk.CTkFrame(dist_frame, fg_color="transparent")
            fila.grid(row=i // 2, column=i % 2, sticky="w", padx=4, pady=2)

            cb = ctk.CTkCheckBox(
                fila, text=nombre, variable=var,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_secondary"],
                fg_color=_cb_fg, hover_color=_cb_hv,
                border_color=colores["border"],
                checkmark_color=colores["text_on_accent"]
            )
            cb.pack(side="left")
            _Tooltip(cb, dist_dict[nombre], modo=self.modo)

            if nombre in sugeridas and nombre not in guardadas:
                ctk.CTkLabel(
                    fila, text=" sugerida",
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    text_color=colores["warning"]
                ).pack(side="left", padx=(2, 0))

        self._separador(scroll)

        for campo_id, etiqueta, hint in [
            ("txt_evidencia_favor",
             "Evidencia a favor del pensamiento",
             "¿Qué hechos concretos (no interpretaciones) respaldan este pensamiento?"),
            ("txt_evidencia_contra",
             "Evidencia en contra del pensamiento",
             "¿Qué hechos, experiencias o perspectivas lo contradicen?"),
        ]:
            ctk.CTkLabel(
                scroll, text=etiqueta,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                text_color=colores["text_secondary"]
            ).pack(anchor="w", pady=(0, 2))
            ctk.CTkLabel(
                scroll, text=hint,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(anchor="w", pady=(0, 4))
            txt = AreaTexto(scroll, modo=self.modo, height=68)
            txt.pack(fill="x", pady=(0, 10))
            setattr(self, campo_id, txt)
            saved = self._datos.get(campo_id.replace("txt_", ""), "") if hasattr(self, '_datos') else ""
            if saved:
                txt.insert("1.0", saved)

    def _paso_respuesta(self):
        self._titulo_paso(
            "Respuesta alternativa",
            self._conf["pasos"]["5"]["subtitulo"]
        )
        self._nav(anterior=True, siguiente=True, texto_sig="Ver cierre →")
        scroll = self._scroll_area()
        colores = COLORS[self.modo]

        self._info_box(
            scroll,
            self._conf["pasos"]["5"].get("infobox", "No se trata de 'pensar en positivo' — se trata de encontrar una perspectiva más equilibrada, basada en la evidencia real que recopilaste.")
        )

        self.txt_respuesta = AreaTexto(scroll, modo=self.modo, height=120)
        self.txt_respuesta.pack(fill="x", pady=(0, 14))
        if hasattr(self, '_datos') and self._datos.get("respuesta"):
            self.txt_respuesta.insert("1.0", self._datos["respuesta"])

    def _paso_cierre(self):
        self._titulo_paso(
            "Análisis TCC completado",
            self._conf["pasos"]["6"]["subtitulo"]
        )
        self._nav(anterior=True, guardar=True)
        scroll = self._scroll_area()
        colores = COLORS[self.modo]

        _acc = colores["success"] if self.modo == "light" else colores["accent"]
        _bg_sec = "#EFEFED" if self.modo == "light" else colores["bg_hover"]

        secciones = _generar_cierre_tcc(self._datos if hasattr(self, '_datos') else {})
        for titulo, texto in secciones:
            sec = ctk.CTkFrame(scroll, fg_color=_bg_sec, corner_radius=8)
            sec.pack(fill="x", pady=4)
            ctk.CTkLabel(
                sec, text=titulo,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                text_color=_acc
            ).pack(anchor="w", padx=12, pady=(8, 2))
            ctk.CTkLabel(
                sec, text=texto,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_primary"],
                wraplength=490, justify="left", anchor="w"
            ).pack(anchor="w", fill="x", padx=12, pady=(0, 8))

    # ── Slider callbacks ─────────────────────────────────────────────────────

    def _on_intensidad(self, val):
        self.intensidad_val = max(0, int(round(float(val))))
        _c = color_por_puntaje_exacto(self.intensidad_val)
        self.lbl_intensidad.configure(text=str(self.intensidad_val), text_color=_c)
        self.slider_intensidad.configure(progress_color=_c, button_color=_c, button_hover_color=_c)

    def _on_creencia_antes(self, val):
        self.creencia_antes_val = max(0, min(100, int(round(float(val)))))
        _c = color_por_puntaje_exacto(round(self.creencia_antes_val / 10))
        self.lbl_creencia_antes.configure(text=f"{self.creencia_antes_val}%", text_color=_c)
        self.slider_creencia_antes.configure(progress_color=_c, button_color=_c, button_hover_color=_c)

    # ── Navigation & persistence ─────────────────────────────────────────────

    def _siguiente_paso(self):
        self._guardar_datos_paso()
        if self.paso_actual < TOTAL_PASOS:
            self.paso_actual += 1
            self._rebuild()

    def _paso_anterior(self):
        self._guardar_datos_paso()
        if self.paso_actual > 1:
            self.paso_actual -= 1
            self._rebuild()

    def _rebuild(self):
        estado = self.state()
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        if estado == "zoomed":
            self.state("zoomed")

    def _guardar_datos_paso(self):
        if not hasattr(self, '_datos'):
            self._datos = {}
        p = self.paso_actual
        if p == 1 and hasattr(self, 'txt_situacion'):
            self._datos["situacion"] = self.txt_situacion.get("1.0", "end").strip()
        elif p == 2:
            if hasattr(self, 'combo_emocion'):
                sel = self.combo_emocion.get()
                if sel == "Otra" and hasattr(self, 'entry_emocion_libre'):
                    self._datos["emocion"] = self.entry_emocion_libre.get().strip() or "Otra"
                else:
                    self._datos["emocion"] = sel
            self._datos["intensidad"] = getattr(self, 'intensidad_val', 5)
        elif p == 3:
            if hasattr(self, 'txt_pensamiento'):
                self._datos["pensamiento"] = self.txt_pensamiento.get("1.0", "end").strip()
            self._datos["creencia_antes"] = getattr(self, 'creencia_antes_val', 80)
        elif p == 4:
            if hasattr(self, 'distorsion_vars'):
                self._datos["distorsiones_list"] = [
                    d for d, v in self.distorsion_vars.items() if v.get()
                ]
            if hasattr(self, 'txt_evidencia_favor'):
                self._datos["evidencia_favor"] = self.txt_evidencia_favor.get("1.0", "end").strip()
            if hasattr(self, 'txt_evidencia_contra'):
                self._datos["evidencia_contra"] = self.txt_evidencia_contra.get("1.0", "end").strip()
        elif p == 5:
            if hasattr(self, 'txt_respuesta'):
                self._datos["respuesta"] = self.txt_respuesta.get("1.0", "end").strip()

    def _guardar(self):
        self._guardar_datos_paso()
        d = self._datos if hasattr(self, '_datos') else {}

        if not d.get("situacion") or not d.get("emocion") or not d.get("pensamiento"):
            mostrar_mensaje(
                self, "Faltan datos",
                "Completá al menos la situación (paso 1), la emoción (paso 2) "
                "y el pensamiento automático (paso 3).",
                tipo="warning", modo=self.modo
            )
            return

        try:
            conn = obtener_conexion()
            conn.execute("""
                INSERT INTO pensamientos
                    (fecha, hora, situacion, emocion, intensidad, pensamiento,
                     respuesta_alternativa, distorsiones, evidencia_favor, evidencia_contra,
                     creencia_antes, creencia_despues, emocion_resultante, reflexion_ia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fecha_hoy(), hora_actual(),
                d.get("situacion", ""),
                d.get("emocion", ""),
                int(d.get("intensidad", 5)),
                d.get("pensamiento", ""),
                d.get("respuesta", ""),
                ",".join(d.get("distorsiones_list", [])),
                d.get("evidencia_favor", ""),
                d.get("evidencia_contra", ""),
                int(d.get("creencia_antes", 80)),
                d.get("creencia_despues", 0),
                d.get("emocion_resultante", ""),
                d.get("reflexion_ia", ""),
            ))
            conn.commit()
            conn.close()
            try:
                from shared.sync import sync_inmediato_background as _sib
                _sib()
            except Exception:
                pass
            self._datos = {}
            self.paso_actual = 1
            self._rebuild()
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo guardar.\n{e}", tipo="error", modo=self.modo)

    # ── Right panel ──────────────────────────────────────────────────────────

    def _construir_panel_der(self, parent):
        colores = COLORS[self.modo]
        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True,
                   padx=LAYOUT["padding_card"], pady=LAYOUT["padding_card"])

        self._panel_historial(inner)

    def _panel_historial(self, parent):
        colores = COLORS[self.modo]

        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            hdr, text="Últimos registros",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["text_primary"]
        ).pack(side="left")
        self.entry_buscar = InputTexto(hdr, modo=self.modo, width=130,
                                       placeholder_text="Buscar...")
        self.entry_buscar.pack(side="right")
        if self._filtro_buscar:
            self.entry_buscar.insert(0, self._filtro_buscar)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._buscar())

        self.frame_historial = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_historial.pack(fill="both", expand=True)
        self._cargar_historial(self._filtro_buscar)

    def _cargar_historial(self, filtro: str = ""):
        for w in self.frame_historial.winfo_children():
            w.destroy()
        colores = COLORS[self.modo]

        _cols = """id, fecha, hora, situacion, emocion, intensidad, pensamiento,
                   respuesta_alternativa, distorsiones,
                   COALESCE(creencia_antes, 50) as creencia_antes,
                   COALESCE(creencia_despues, 50) as creencia_despues,
                   COALESCE(evidencia_favor, '') as evidencia_favor,
                   COALESCE(evidencia_contra, '') as evidencia_contra,
                   COALESCE(emocion_resultante, '') as emocion_resultante,
                   COALESCE(reflexion_ia, '') as reflexion_ia"""

        conn = obtener_conexion()
        if filtro:
            registros = conn.execute(
                f"SELECT {_cols} FROM pensamientos "
                "WHERE situacion LIKE ? OR emocion LIKE ? OR pensamiento LIKE ? OR fecha LIKE ? "
                "ORDER BY fecha DESC, hora DESC LIMIT 25",
                tuple(f"%{filtro}%" for _ in range(4))
            ).fetchall()
        else:
            registros = conn.execute(
                f"SELECT {_cols} FROM pensamientos ORDER BY fecha DESC, hora DESC LIMIT 25"
            ).fetchall()
        conn.close()

        if not registros:
            ctk.CTkLabel(
                self.frame_historial, text="Sin registros todavía.",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        for reg in registros:
            r = dict(reg)
            fila = ctk.CTkFrame(self.frame_historial, fg_color=colores["bg_list_item"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=3)

            ctk.CTkLabel(
                fila, text=f"{fecha_legible(r['fecha'])} · {r['hora'][:5]}",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(padx=12, pady=(8, 0), anchor="w")

            ctk.CTkLabel(
                fila, text=f"{r['emocion']}  {r['intensidad']}/10",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                text_color=color_por_puntaje_exacto(r['intensidad'])
            ).pack(padx=12, anchor="w")

            dist = (r.get("distorsiones") or "").strip()
            if dist:
                ctk.CTkLabel(
                    fila, text=dist[:55] + ("..." if len(dist) > 55 else ""),
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    text_color=colores["warning"], anchor="w"
                ).pack(padx=12, anchor="w")

            ctk.CTkLabel(
                fila,
                text=r["situacion"][:95] + ("..." if len(r["situacion"]) > 95 else ""),
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_secondary"],
                anchor="w", wraplength=255, justify="left"
            ).pack(fill="x", padx=12, pady=(2, 4), anchor="w")

            btn_row = ctk.CTkFrame(fila, fg_color="transparent")
            btn_row.pack(fill="x", padx=12, pady=(0, 8))

            _vfg = colores["warning"] if self.modo == "light" else "transparent"
            _vhv = "#B06830" if self.modo == "light" else colores["bg_hover"]
            _vtx = colores["text_on_accent"] if self.modo == "light" else colores["accent"]
            _vbr = colores["warning"] if self.modo == "light" else colores["accent"]
            ctk.CTkButton(
                btn_row, text="Ver completo", width=90, height=24,
                fg_color=_vfg, hover_color=_vhv, text_color=_vtx,
                border_width=1 if self.modo == "light" else 2,
                border_color=_vbr, corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
                command=lambda rc=r: self._mostrar_detalle(rc)
            ).pack(side="left")

            if r.get("reflexion_ia"):
                ctk.CTkLabel(
                    btn_row, text="· IA",
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
                    text_color=colores["info"] if self.modo == "light" else colores["accent"]
                ).pack(side="left", padx=(8, 0))

    def _mostrar_detalle(self, reg: dict):
        colores = COLORS[self.modo]
        win = NMToplevel(self, modo=self.modo)
        win.title("Detalle del registro")
        _w, _h = 560, 660
        win.geometry(f"{_w}x{_h}+{(win.winfo_screenwidth()-_w)//2}+{(win.winfo_screenheight()-_h)//2}")
        win.configure(fg_color=colores["bg_primary"])
        win.grab_set()
        win.after(10, win.focus_force)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            scroll, text=f"{reg.get('fecha', '')}  ·  {str(reg.get('hora', ''))[:5]}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(anchor="w", pady=(0, 10))

        _acc = colores["warning"] if self.modo == "light" else colores["accent"]
        dist_txt = ", ".join(
            d.strip() for d in (reg.get("distorsiones") or "").split(",") if d.strip()
        ) or "—"
        ca = reg.get("creencia_antes", "—")

        campos = [
            ("Emoción",                f"{reg.get('emocion', '')}  ·  {reg.get('intensidad', 0)}/10"),
            ("Situación",              reg.get("situacion", "")),
            ("Pensamiento automático", reg.get("pensamiento", "")),
            ("Creencia inicial",       f"{ca}%" if ca != "—" else "—"),
            ("Distorsiones",           dist_txt),
            ("Evidencia a favor",      reg.get("evidencia_favor", "") or "—"),
            ("Evidencia en contra",    reg.get("evidencia_contra", "") or "—"),
            ("Respuesta alternativa",  reg.get("respuesta_alternativa", "") or "—"),
        ]
        if reg.get("reflexion_ia"):
            campos.append(("Reflexión IA", reg.get("reflexion_ia", "")))

        for titulo, texto in campos:
            ctk.CTkLabel(
                scroll, text=titulo,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                text_color=_acc
            ).pack(anchor="w", pady=(8, 2))
            ctk.CTkLabel(
                scroll, text=str(texto) or "—",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_primary"],
                wraplength=505, justify="left", anchor="w"
            ).pack(anchor="w", fill="x")

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(pady=(0, 16))
        _kw_c = {"fg_color": colores["success"], "hover_color": "#4A8A70"} if self.modo == "light" else {}
        BotonPrimario(btn_row, text="Cerrar", modo=self.modo, width=100,
                      command=win.destroy, **_kw_c).pack()

    def _exportar_pdf(self, reg: dict):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import ParagraphStyle
            import tempfile

            ruta = os.path.join(
                tempfile.gettempdir(),
                f"NM_Pensamiento_{reg.get('fecha', 'sin_fecha')}.pdf"
            )
            doc = SimpleDocTemplate(ruta, pagesize=A4,
                                    leftMargin=55, rightMargin=55,
                                    topMargin=60, bottomMargin=55)
            NAVY  = HexColor('#0B1928')
            TEAL  = HexColor('#1EC8D4')
            GRAY  = HexColor('#8BA4BE')
            AMBER = HexColor('#F0A500')
            BODY  = HexColor('#E8EEF4')

            st_title = ParagraphStyle("t", fontName="Helvetica-Bold",  fontSize=18, textColor=TEAL,  spaceAfter=4)
            st_date  = ParagraphStyle("d", fontName="Helvetica",        fontSize=10, textColor=GRAY,  spaceAfter=16)
            st_head  = ParagraphStyle("h", fontName="Helvetica-Bold",  fontSize=11, textColor=AMBER, spaceBefore=12, spaceAfter=4)
            st_body  = ParagraphStyle("b", fontName="Helvetica",        fontSize=11, textColor=BODY,  leading=16)
            st_disc  = ParagraphStyle("disc", fontName="Helvetica-Oblique", fontSize=9, textColor=GRAY)

            dist_txt = ", ".join(
                d.strip() for d in (reg.get("distorsiones") or "").split(",") if d.strip()
            ) or "—"

            story = [
                Paragraph("Registro de Pensamientos · NeuroMood", st_title),
                Paragraph(f"{reg.get('fecha', '')}  ·  {str(reg.get('hora', ''))[:5]}", st_date),
            ]
            for titulo, texto in [
                ("Emoción",                f"{reg.get('emocion', '')}  ({reg.get('intensidad', 0)}/10)"),
                ("Situación",              reg.get("situacion", "")),
                ("Pensamiento automático", reg.get("pensamiento", "")),
                ("Creencia inicial",       f"{reg.get('creencia_antes', '—')}%"),
                ("Distorsiones",           dist_txt),
                ("Evidencia a favor",      reg.get("evidencia_favor", "") or "—"),
                ("Evidencia en contra",    reg.get("evidencia_contra", "") or "—"),
                ("Respuesta alternativa",  reg.get("respuesta_alternativa", "") or "—"),
                ("Creencia tras análisis", f"{reg.get('creencia_despues', '—')}%"),
                ("Emoción resultante",     reg.get("emocion_resultante", "") or "—"),
            ]:
                story += [
                    Paragraph(titulo, st_head),
                    Paragraph(str(texto).replace("\n", "<br/>"), st_body),
                    Spacer(1, 4),
                ]
            if reg.get("reflexion_ia"):
                story += [
                    Paragraph("Reflexión IA (Groq · Llama 3)", st_head),
                    Paragraph(str(reg["reflexion_ia"]).replace("\n", "<br/>"), st_body),
                    Spacer(1, 4),
                ]
            story += [
                Spacer(1, 20),
                Paragraph(
                    "Generado por NeuroMood Suite. No reemplaza la consulta profesional. "
                    "neuromood.com.ar · Dra. Lucía Fazzito",
                    st_disc
                ),
            ]
            doc.build(story)
            os.startfile(ruta)
        except ImportError:
            mostrar_mensaje(
                self, "PDF no disponible",
                "La librería reportlab no está instalada.\nEjecutá: pip install reportlab",
                tipo="warning", modo=self.modo
            )
        except Exception as e:
            mostrar_mensaje(self, "Error al exportar", str(e), tipo="error", modo=self.modo)

    def _buscar(self):
        self._filtro_buscar = self.entry_buscar.get().strip()
        self._cargar_historial(self._filtro_buscar)

    # ── Theme sync ───────────────────────────────────────────────────────────

    def _poll_tema(self):
        try:
            cfg = leer_config("theme", self.modo)
            if cfg != self.modo:
                self._aplicar_tema_externo(cfg)
        except Exception:
            pass
        try:
            self.after(1000, self._poll_tema)
        except Exception:
            pass

    def _aplicar_tema_externo(self, nuevo_modo):
        if nuevo_modo == self.modo:
            return
        self._guardar_datos_paso()
        self._filtro_buscar = self.entry_buscar.get().strip() if hasattr(self, 'entry_buscar') else ""
        self.modo = nuevo_modo
        ctk.set_appearance_mode(nuevo_modo)
        estado = self.state()
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")

    def _toggle_modo(self):
        self._guardar_datos_paso()
        self._filtro_buscar = self.entry_buscar.get().strip() if hasattr(self, 'entry_buscar') else ""
        self.modo = "light" if self.modo == "dark" else "dark"
        guardar_config("theme", self.modo)
        ctk.set_appearance_mode(self.modo)
        estado = self.state()
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
    app = PensamientosApp()
    app.mainloop()
