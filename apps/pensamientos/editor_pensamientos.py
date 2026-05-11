import sys
import os
import json

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import guardar_config, leer_config
from shared.components import BotonPrimario, BotonSecundario, NMToplevel, mostrar_mensaje

_NOMBRES_PASOS = {
    "1": "Paso 1 — ¿Qué estaba pasando?",
    "2": "Paso 2 — ¿Qué sentiste?",
    "3": "Paso 3 — ¿Qué pensaste?",
    "4": "Paso 4 — Análisis del pensamiento",
    "5": "Paso 5 — Respuesta alternativa",
    "6": "Paso 6 — Cierre TCC",
}

_MAX_SUBTITULO = 280
_MAX_INFOBOX = 280
_MAX_DIST_NOMBRE = 40
_MAX_DIST_DESC = 280
_MAX_DISTORSIONES = 12
_MIN_DISTORSIONES = 2


def _cargar_conf() -> dict:
    raw = leer_config("pensamientos_config", "")
    if raw:
        try:
            conf = json.loads(raw)
            if "pasos" in conf and "distorsiones" in conf:
                return conf
        except Exception:
            pass
    return None


def _conf_defecto() -> dict:
    from apps.pensamientos.main import _CONF_PASOS_DEFECTO, _DISTORSIONES_DEFECTO
    return {
        "pasos": {str(k): (v if isinstance(v, dict) else {"subtitulo": v})
                  for k, v in _CONF_PASOS_DEFECTO.items()},
        "distorsiones": [d.copy() for d in _DISTORSIONES_DEFECTO],
    }


class VentanaEditorPensamientos(NMToplevel):
    def __init__(self, master, modo: str = "dark"):
        super().__init__(master, modo=modo)
        self.modo = modo
        self.title("Editor — Registro de Pensamientos")
        _w, _h = 840, 600
        _sw, _sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{_w}x{_h}+{(_sw - _w) // 2}+{(_sh - _h) // 2}")
        self.minsize(700, 480)
        self.resizable(True, True)

        c = COLORS[modo]
        self.configure(fg_color=c["bg_primary"])
        self.grab_set()

        self._conf = _cargar_conf() or _conf_defecto()
        self._sel = "1"

        self._construir()
        self._seleccionar("1")
        self.after(10, self.focus_force)

    def _construir(self):
        c = COLORS[self.modo]
        p = LAYOUT["padding_card"]

        # Header
        hdr = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=44, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="Editor de Registro de Pensamientos",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"]
        ).pack(side="left", padx=p, pady=8)

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=p, pady=p)

        # Columna izquierda
        col_izq = ctk.CTkFrame(body, fg_color=c["bg_surface"],
                               corner_radius=LAYOUT["radius_card"],
                               border_width=LAYOUT["border_card_width"],
                               border_color=c["border"],
                               width=200)
        col_izq.pack(side="left", fill="y", padx=(0, 12))
        col_izq.pack_propagate(False)

        ctk.CTkLabel(
            col_izq, text="Elementos",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=c["text_secondary"]
        ).pack(anchor="w", padx=12, pady=(12, 6))

        self._btns_izq: dict[str, ctk.CTkButton] = {}
        for clave, nombre in list(_NOMBRES_PASOS.items()) + [("distorsiones", "Distorsiones cognitivas")]:
            btn = ctk.CTkButton(
                col_izq, text=nombre, anchor="w", height=34,
                fg_color="transparent",
                hover_color=c["bg_hover"],
                text_color=c["text_primary"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                command=lambda k=clave: self._seleccionar(k)
            )
            btn.pack(fill="x", padx=6, pady=2)
            self._btns_izq[clave] = btn

        # Columna derecha
        self._col_der = ctk.CTkFrame(body, fg_color=c["bg_surface"],
                                      corner_radius=LAYOUT["radius_card"],
                                      border_width=LAYOUT["border_card_width"],
                                      border_color=c["border"])
        self._col_der.pack(side="left", fill="both", expand=True)

        # Footer
        footer = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=48, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        BotonSecundario(
            footer, text="Restaurar defecto", modo=self.modo, height=32,
            command=self._restaurar_defecto
        ).pack(side="left", padx=12, pady=8)

        BotonPrimario(
            footer, text="Guardar cambios", modo=self.modo, height=32,
            command=self._guardar
        ).pack(side="right", padx=12, pady=8)

    def _seleccionar(self, clave: str):
        c = COLORS[self.modo]
        self._sel = clave
        for k, btn in self._btns_izq.items():
            btn.configure(
                fg_color=c["accent"] if k == clave else "transparent",
                text_color=c["text_on_accent"] if k == clave else c["text_primary"]
            )
        for w in self._col_der.winfo_children():
            w.destroy()
        if clave == "distorsiones":
            self._editor_distorsiones()
        else:
            self._editor_paso(clave)

    def _editor_paso(self, clave: str):
        c = COLORS[self.modo]
        p = LAYOUT["padding_card"]
        frame = ctk.CTkFrame(self._col_der, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=p, pady=p)

        ctk.CTkLabel(
            frame, text=_NOMBRES_PASOS.get(clave, f"Paso {clave}"),
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"]
        ).pack(anchor="w", pady=(0, 12))

        paso_conf = self._conf["pasos"].get(clave, {})

        ctk.CTkLabel(
            frame, text=f"Descripción del paso (máx {_MAX_SUBTITULO} caracteres):",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=c["text_secondary"]
        ).pack(anchor="w", pady=(0, 4))

        self._txt_subtitulo = ctk.CTkTextbox(
            frame, height=90, wrap="word",
            fg_color=c["bg_input"], border_color=c["border"],
            text_color=c["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            border_width=LAYOUT["border_width"],
            corner_radius=LAYOUT["radius_input"]
        )
        self._txt_subtitulo.pack(fill="x", pady=(0, 12))
        sub = paso_conf.get("subtitulo", "")
        if sub:
            self._txt_subtitulo.insert("1.0", sub)

        if clave == "5":
            ctk.CTkLabel(
                frame, text=f"Texto informativo en el paso (máx {_MAX_INFOBOX} caracteres):",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                text_color=c["text_secondary"]
            ).pack(anchor="w", pady=(0, 4))
            self._txt_infobox = ctk.CTkTextbox(
                frame, height=90, wrap="word",
                fg_color=c["bg_input"], border_color=c["border"],
                text_color=c["text_primary"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                border_width=LAYOUT["border_width"],
                corner_radius=LAYOUT["radius_input"]
            )
            self._txt_infobox.pack(fill="x")
            ib = paso_conf.get("infobox", "")
            if ib:
                self._txt_infobox.insert("1.0", ib)
        else:
            self._txt_infobox = None

    def _editor_distorsiones(self):
        c = COLORS[self.modo]
        p = LAYOUT["padding_card"]
        frame = ctk.CTkFrame(self._col_der, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=p, pady=p)

        ctk.CTkLabel(
            frame, text="Distorsiones cognitivas",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"]
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            frame,
            text=f"Mínimo {_MIN_DISTORSIONES}, máximo {_MAX_DISTORSIONES}. Nombre máx {_MAX_DIST_NOMBRE} chars.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"]
        ).pack(anchor="w", pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(
            frame, fg_color="transparent", height=320,
            scrollbar_button_color=c["bg_hover"],
            scrollbar_button_hover_color=c["accent"]
        )
        scroll.pack(fill="both", expand=True, pady=(0, 8))

        self._dist_widgets: list[dict] = []

        def _render_dist():
            for w in scroll.winfo_children():
                w.destroy()
            self._dist_widgets.clear()
            for i, d in enumerate(self._conf["distorsiones"]):
                fila = ctk.CTkFrame(scroll, fg_color=c["bg_list_item"],
                                    corner_radius=LAYOUT["radius_button"])
                fila.pack(fill="x", pady=2)
                ent_n = ctk.CTkEntry(
                    fila, fg_color=c["bg_input"], border_color=c["border"],
                    text_color=c["text_primary"],
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                    height=28, width=140
                )
                ent_n.insert(0, d["nombre"])
                ent_n.pack(side="left", padx=(8, 4), pady=6)

                ent_d = ctk.CTkEntry(
                    fila, fg_color=c["bg_input"], border_color=c["border"],
                    text_color=c["text_primary"],
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                    height=28
                )
                ent_d.insert(0, d["descripcion"][:60])
                ent_d.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=6)

                def _quitar(idx=i):
                    if len(self._conf["distorsiones"]) <= _MIN_DISTORSIONES:
                        mostrar_mensaje(self, "Límite mínimo",
                                        f"No se puede bajar de {_MIN_DISTORSIONES} distorsiones.",
                                        tipo="warning", modo=self.modo)
                        return
                    self._conf["distorsiones"].pop(idx)
                    _render_dist()

                ctk.CTkButton(
                    fila, text="✕", width=26, height=26,
                    fg_color="transparent",
                    hover_color=c["error"],
                    text_color=c["text_tertiary"],
                    corner_radius=LAYOUT["radius_button"],
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    command=_quitar
                ).pack(side="right", padx=6)

                self._dist_widgets.append({
                    "nombre": ent_n,
                    "descripcion": ent_d,
                    "keywords": d.get("keywords", [])
                })

        _render_dist()

        # Agregar nueva
        add_row = ctk.CTkFrame(frame, fg_color="transparent")
        add_row.pack(fill="x")
        ent_new = ctk.CTkEntry(
            add_row, placeholder_text="Nombre de la nueva distorsión...",
            fg_color=c["bg_input"], border_color=c["border"],
            text_color=c["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            height=32
        )
        ent_new.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def _agregar():
            nombre = ent_new.get().strip()[:_MAX_DIST_NOMBRE]
            if not nombre:
                return
            if len(self._conf["distorsiones"]) >= _MAX_DISTORSIONES:
                mostrar_mensaje(self, "Límite máximo",
                                f"No se puede superar {_MAX_DISTORSIONES} distorsiones.",
                                tipo="warning", modo=self.modo)
                return
            self._conf["distorsiones"].append({
                "nombre": nombre,
                "descripcion": "",
                "keywords": []
            })
            ent_new.delete(0, "end")
            _render_dist()

        BotonSecundario(
            add_row, text="+ Agregar", modo=self.modo, height=32,
            command=_agregar
        ).pack(side="left")

        self._render_dist_fn = _render_dist

    def _recopilar_cambios_dist(self):
        if not hasattr(self, '_dist_widgets'):
            return
        for i, wdg in enumerate(self._dist_widgets):
            if i < len(self._conf["distorsiones"]):
                self._conf["distorsiones"][i]["nombre"] = wdg["nombre"].get().strip()[:_MAX_DIST_NOMBRE]
                desc_raw = wdg["descripcion"].get().strip()
                self._conf["distorsiones"][i]["descripcion"] = desc_raw[:_MAX_DIST_DESC]

    def _guardar(self):
        # Recopilar cambios del paso seleccionado
        if self._sel != "distorsiones":
            sub = self._txt_subtitulo.get("1.0", "end").strip()[:_MAX_SUBTITULO]
            self._conf["pasos"][self._sel]["subtitulo"] = sub
            if self._sel == "5" and self._txt_infobox:
                ib = self._txt_infobox.get("1.0", "end").strip()[:_MAX_INFOBOX]
                self._conf["pasos"]["5"]["infobox"] = ib
        else:
            self._recopilar_cambios_dist()

        try:
            guardar_config("pensamientos_config", json.dumps(self._conf, ensure_ascii=False))
            mostrar_mensaje(self, "Guardado",
                            "Los cambios se aplicarán la próxima vez que se abra el Registro de Pensamientos.",
                            tipo="success", modo=self.modo)
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo guardar: {e}", tipo="error", modo=self.modo)

    def _restaurar_defecto(self):
        self._conf = _conf_defecto()
        guardar_config("pensamientos_config", "")
        mostrar_mensaje(self, "Restaurado",
                        "Se restauró la configuración por defecto.",
                        tipo="info", modo=self.modo)
        self._seleccionar(self._sel)
