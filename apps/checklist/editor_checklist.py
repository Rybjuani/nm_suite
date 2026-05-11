"""editor_checklist.py — Editor de plantillas clínicas para el Checklist de Rutina."""
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
import plantillas as _plantillas
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion
from shared.components import NMToplevel, BotonPrimario, BotonSecundario, InputTexto

_SEC_LABEL = {"manana": "Mañana", "tarde": "Tarde", "noche": "Noche"}
_SEC_KEY   = {"Mañana": "manana", "Tarde": "tarde", "Noche": "noche"}
CATEGORIAS = ["Logro", "Placer", "Autocuidado", "Social"]


class VentanaEditorChecklist(NMToplevel):
    def __init__(self, master, modo: str = "dark"):
        super().__init__(master, modo=modo)
        self.modo = modo
        self.title("Editor de Plantillas — Modo Terapeuta")
        _w, _h = 820, 540
        _x = (self.winfo_screenwidth() - _w) // 2
        _y = (self.winfo_screenheight() - _h) // 2
        self.geometry(f"{_w}x{_h}+{_x}+{_y}")
        self.resizable(False, False)
        self.grab_set()
        self._edit_id = None
        self._edit_es_custom = 0
        self._construir()

    def _construir(self):
        colores = COLORS[self.modo]
        p = LAYOUT["padding_card"]

        strip = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=36, corner_radius=0)
        strip.pack(fill="x")
        strip.pack_propagate(False)
        ctk.CTkLabel(
            strip, text="⚠ Modo Terapeuta — cambios guardados de forma inmediata",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["warning"]
        ).pack(side="left", padx=12, pady=8)

        area = ctk.CTkFrame(self, fg_color="transparent")
        area.pack(fill="both", expand=True, padx=p, pady=p)

        # ── Panel izquierdo: lista ────────────────────────────────────────────
        frame_lista = ctk.CTkFrame(area, fg_color=colores["bg_surface"],
                                   corner_radius=LAYOUT["radius_card"], width=230)
        frame_lista.pack(side="left", fill="y", padx=(0, p))
        frame_lista.pack_propagate(False)

        ctk.CTkLabel(
            frame_lista, text="Plantillas clínicas",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=p, pady=(p, 4), anchor="w")

        self.scroll_lista = ctk.CTkScrollableFrame(
            frame_lista, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.scroll_lista.pack(fill="both", expand=True, padx=6, pady=(0, p))

        # ── Panel derecho: formulario ─────────────────────────────────────────
        frame_form = ctk.CTkFrame(area, fg_color=colores["bg_surface"],
                                  corner_radius=LAYOUT["radius_card"])
        frame_form.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            frame_form, text="Editar plantilla",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=colores["accent"]
        ).pack(padx=p, pady=(p, 8), anchor="w")

        def _fila(lbl):
            f = ctk.CTkFrame(frame_form, fg_color="transparent")
            f.pack(fill="x", padx=p, pady=(0, 6))
            ctk.CTkLabel(
                f, text=lbl, width=96, anchor="w",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_secondary"]
            ).pack(side="left")
            return f

        f_desc = _fila("Descripción:")
        self.e_desc = InputTexto(f_desc, modo=self.modo, height=32,
                                 placeholder_text="Tarea terapéutica")
        self.e_desc.pack(side="left", fill="x", expand=True)

        f_sec = _fila("Sección:")
        self.combo_sec = ctk.CTkComboBox(
            f_sec, values=["Mañana", "Tarde", "Noche"], width=130,
            fg_color=colores["bg_input"], border_color=colores["border"],
            button_color=colores["accent"], button_hover_color=colores["accent_hover"],
            dropdown_fg_color=colores["bg_surface"], dropdown_hover_color=colores["bg_hover"],
            text_color=colores["text_primary"], dropdown_text_color=colores["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            corner_radius=LAYOUT["radius_input"]
        )
        self.combo_sec.set("Mañana")
        self.combo_sec.pack(side="left")

        f_cat = _fila("Categoría:")
        self.combo_cat = ctk.CTkComboBox(
            f_cat, values=CATEGORIAS, width=130,
            fg_color=colores["bg_input"], border_color=colores["border"],
            button_color=colores["accent"], button_hover_color=colores["accent_hover"],
            dropdown_fg_color=colores["bg_surface"], dropdown_hover_color=colores["bg_hover"],
            text_color=colores["text_primary"], dropdown_text_color=colores["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            corner_radius=LAYOUT["radius_input"]
        )
        self.combo_cat.set(CATEGORIAS[0])
        self.combo_cat.pack(side="left")

        self.lbl_msg = ctk.CTkLabel(
            frame_form, text="",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["error"]
        )
        self.lbl_msg.pack(padx=p, anchor="w")

        # ── Botones de acción ─────────────────────────────────────────────────
        f_btns = ctk.CTkFrame(frame_form, fg_color="transparent")
        f_btns.pack(fill="x", padx=p, pady=(8, p))

        BotonPrimario(
            f_btns, text="Guardar plantilla", modo=self.modo, width=140, height=32,
            command=self._guardar
        ).pack(side="left", padx=(0, 8))
        BotonSecundario(
            f_btns, text="Nuevo", modo=self.modo, width=72, height=32,
            command=self._limpiar_form
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            f_btns, text="Agregar al checklist", height=32, width=148,
            fg_color=colores["success"], hover_color="#4A8A70",
            text_color=colores["text_on_accent"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            command=self._agregar_al_checklist
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            f_btns, text="Eliminar", height=32, width=80,
            fg_color=colores["error"],
            hover_color="#BF5555" if self.modo == "light" else "#C83040",
            text_color=colores["text_on_accent"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            command=self._eliminar
        ).pack(side="left")
        self.lbl_ok = ctk.CTkLabel(
            f_btns, text="",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["success"]
        )
        self.lbl_ok.pack(side="right")

        self._cargar_lista()

    # ── Lista ─────────────────────────────────────────────────────────────────

    def _cargar_lista(self):
        for w in self.scroll_lista.winfo_children():
            w.destroy()
        colores = COLORS[self.modo]
        seccion_actual = None
        for pr in _plantillas.obtener_plantillas():
            if pr["seccion"] != seccion_actual:
                seccion_actual = pr["seccion"]
                ctk.CTkLabel(
                    self.scroll_lista,
                    text=f"— {_SEC_LABEL.get(seccion_actual, seccion_actual)} —",
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
                    text_color=colores["accent"]
                ).pack(anchor="w", padx=4, pady=(6, 2))
            badge = "✚" if pr["es_custom"] else "·"
            ctk.CTkButton(
                self.scroll_lista,
                text=f"{badge}  {pr['descripcion']}",
                anchor="w", height=28,
                fg_color="transparent", hover_color=colores["bg_hover"],
                text_color=colores["text_primary"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                command=lambda p=pr: self._seleccionar(p)
            ).pack(fill="x", pady=1)

    def _seleccionar(self, plantilla: dict):
        self._edit_id = plantilla["id"]
        self._edit_es_custom = plantilla["es_custom"]
        self.e_desc.delete(0, "end")
        self.e_desc.insert(0, plantilla["descripcion"])
        self.combo_sec.set(_SEC_LABEL.get(plantilla["seccion"], "Mañana"))
        cat = plantilla.get("categoria", "Logro")
        self.combo_cat.set(cat if cat in CATEGORIAS else "Logro")
        self.lbl_msg.configure(text="")
        self.lbl_ok.configure(text="")

    def _limpiar_form(self):
        self._edit_id = None
        self._edit_es_custom = 1
        self.e_desc.delete(0, "end")
        self.combo_sec.set("Mañana")
        self.combo_cat.set("Logro")
        self.lbl_msg.configure(text="")
        self.lbl_ok.configure(text="")

    # ── Guardado ──────────────────────────────────────────────────────────────

    def _guardar(self):
        desc = self.e_desc.get().strip()
        if not desc:
            self.lbl_msg.configure(text="La descripción es obligatoria.")
            return
        _plantillas.guardar_plantilla({
            "id": self._edit_id,
            "descripcion": desc,
            "seccion": _SEC_KEY.get(self.combo_sec.get(), "manana"),
            "categoria": self.combo_cat.get(),
        })
        self.lbl_msg.configure(text="")
        self.lbl_ok.configure(text="Guardado.")
        self._edit_id = None
        self._cargar_lista()

    def _agregar_al_checklist(self):
        if not self._edit_id:
            self.lbl_msg.configure(text="Seleccioná una plantilla primero.")
            return
        todas = _plantillas.obtener_plantillas()
        p = next((x for x in todas if x["id"] == self._edit_id), None)
        if not p:
            return
        conn = obtener_conexion()
        max_ord = conn.execute(
            "SELECT COALESCE(MAX(orden), 0) as m FROM checklist_tareas WHERE seccion=?",
            (p["seccion"],)
        ).fetchone()["m"]
        conn.execute(
            "INSERT INTO checklist_tareas "
            "(seccion, descripcion, orden, categoria) VALUES (?,?,?,?)",
            (p["seccion"], p["descripcion"], max_ord + 1, p["categoria"])
        )
        conn.commit()
        conn.close()
        self.lbl_ok.configure(text=f"Agregada a {_SEC_LABEL.get(p['seccion'], p['seccion'])}.")

    def _eliminar(self):
        if not self._edit_id:
            self.lbl_msg.configure(text="Seleccioná una plantilla de la lista.")
            return
        _plantillas.eliminar_plantilla(self._edit_id)
        self._limpiar_form()
        self._cargar_lista()
        self.lbl_ok.configure(text="Eliminada.")

