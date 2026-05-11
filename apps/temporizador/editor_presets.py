"""editor_presets.py — Editor de presets clínicos para el Temporizador."""
import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

_app_dir = os.path.join(_base, "apps", "temporizador")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

import customtkinter as ctk
import presets as _presets
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.components import NMToplevel, BotonPrimario, BotonSecundario, InputTexto

CATEGORIAS_TIMER = ["Relajación", "Cognitiva", "Física", "Social", "Autocuidado"]


class VentanaEditorPresets(NMToplevel):
    def __init__(self, master, modo: str = "dark"):
        super().__init__(master, modo=modo)
        self.modo = modo
        self.title("Editor de Presets — Modo Terapeuta")
        _w, _h = 820, 460
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

        # ── Panel izquierdo: lista de presets ─────────────────────────────────
        frame_lista = ctk.CTkFrame(area, fg_color=colores["bg_surface"],
                                   corner_radius=LAYOUT["radius_card"], width=220)
        frame_lista.pack(side="left", fill="y", padx=(0, p))
        frame_lista.pack_propagate(False)

        ctk.CTkLabel(
            frame_lista, text="Presets activos",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=p, pady=(p, 4), anchor="w")

        self.scroll_lista = ctk.CTkScrollableFrame(
            frame_lista, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.scroll_lista.pack(fill="both", expand=True, padx=6, pady=(0, p))

        # ── Panel derecho: formulario ──────────────────────────────────────────
        frame_form = ctk.CTkFrame(area, fg_color=colores["bg_surface"],
                                  corner_radius=LAYOUT["radius_card"])
        frame_form.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            frame_form, text="Editar preset",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=colores["accent"]
        ).pack(padx=p, pady=(p, 8), anchor="w")

        def _campo(lbl, placeholder, **kw):
            f = ctk.CTkFrame(frame_form, fg_color="transparent")
            f.pack(fill="x", padx=p, pady=(0, 6))
            ctk.CTkLabel(
                f, text=lbl, width=96, anchor="w",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_secondary"]
            ).pack(side="left")
            w = InputTexto(f, modo=self.modo, height=32, placeholder_text=placeholder, **kw)
            w.pack(side="left", fill="x", expand=True)
            return w

        self.e_nom  = _campo("Nombre:",      "Nombre del preset")
        self.e_desc = _campo("Descripción:", "Descripción clínica breve")

        f_cat = ctk.CTkFrame(frame_form, fg_color="transparent")
        f_cat.pack(fill="x", padx=p, pady=(0, 6))
        ctk.CTkLabel(
            f_cat, text="Categoría:", width=96, anchor="w",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"]
        ).pack(side="left")
        self.combo_cat = ctk.CTkComboBox(
            f_cat, values=CATEGORIAS_TIMER,
            fg_color=colores["bg_input"], border_color=colores["border"],
            button_color=colores["accent"], button_hover_color=colores["accent_hover"],
            dropdown_fg_color=colores["bg_surface"], dropdown_hover_color=colores["bg_hover"],
            text_color=colores["text_primary"], dropdown_text_color=colores["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            corner_radius=LAYOUT["radius_input"]
        )
        self.combo_cat.set(CATEGORIAS_TIMER[0])
        self.combo_cat.pack(side="left")

        f_dur = ctk.CTkFrame(frame_form, fg_color="transparent")
        f_dur.pack(fill="x", padx=p, pady=(0, 6))
        ctk.CTkLabel(
            f_dur, text="Duración:", width=96, anchor="w",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"]
        ).pack(side="left")
        self.e_dur = InputTexto(f_dur, modo=self.modo, width=76, height=32, placeholder_text="seg")
        self.e_dur.pack(side="left")
        ctk.CTkLabel(
            f_dur, text="segundos  (0 = duración libre)",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["text_tertiary"]
        ).pack(side="left", padx=(8, 0))

        self.lbl_msg = ctk.CTkLabel(
            frame_form, text="",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["error"]
        )
        self.lbl_msg.pack(padx=p, anchor="w")

        # ── Botones de acción ──────────────────────────────────────────────────
        f_btns = ctk.CTkFrame(frame_form, fg_color="transparent")
        f_btns.pack(fill="x", padx=p, pady=(8, p))

        BotonPrimario(
            f_btns, text="Guardar preset", modo=self.modo, width=140, height=32,
            command=self._guardar
        ).pack(side="left", padx=(0, 8))
        BotonSecundario(
            f_btns, text="Nuevo", modo=self.modo, width=72, height=32,
            command=self._limpiar_form
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

    # ── Lista ──────────────────────────────────────────────────────────────────

    def _cargar_lista(self):
        for w in self.scroll_lista.winfo_children():
            w.destroy()
        colores = COLORS[self.modo]
        for pr in _presets.obtener_presets():
            badge = "✚" if pr["es_custom"] else "·"
            ctk.CTkButton(
                self.scroll_lista,
                text=f"{badge}  {pr['nombre']}",
                anchor="w", height=28,
                fg_color="transparent", hover_color=colores["bg_hover"],
                text_color=colores["text_primary"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                command=lambda p=pr: self._seleccionar(p)
            ).pack(fill="x", pady=1)

    def _seleccionar(self, preset: dict):
        self._edit_id = preset["id"]
        self._edit_es_custom = preset["es_custom"]
        self.e_nom.delete(0, "end");  self.e_nom.insert(0, preset["nombre"])
        self.e_desc.delete(0, "end"); self.e_desc.insert(0, preset.get("descripcion", ""))
        self.e_dur.delete(0, "end");  self.e_dur.insert(0, str(preset["duracion_seg"]))
        cat = preset.get("categoria", "")
        self.combo_cat.set(cat if cat in CATEGORIAS_TIMER else CATEGORIAS_TIMER[0])
        self.lbl_msg.configure(text="")
        self.lbl_ok.configure(text="")

    def _limpiar_form(self):
        self._edit_id = None
        self._edit_es_custom = 1
        for e in (self.e_nom, self.e_desc, self.e_dur):
            e.delete(0, "end")
        self.combo_cat.set(CATEGORIAS_TIMER[0])
        self.lbl_msg.configure(text="")
        self.lbl_ok.configure(text="")

    # ── Guardado ───────────────────────────────────────────────────────────────

    def _guardar(self):
        nombre = self.e_nom.get().strip()
        if not nombre:
            self.lbl_msg.configure(text="El nombre es obligatorio.")
            return
        try:
            dur = int(self.e_dur.get().strip())
            if dur < 0:
                raise ValueError
        except (ValueError, AttributeError):
            self.lbl_msg.configure(text="Duración inválida (número entero ≥ 0).")
            return
        _presets.guardar_preset({
            "id": self._edit_id,
            "nombre": nombre,
            "descripcion": self.e_desc.get().strip(),
            "categoria": self.combo_cat.get(),
            "duracion_seg": dur,
        })
        self.lbl_msg.configure(text="")
        self.lbl_ok.configure(text="Guardado.")
        self._edit_id = None
        self._cargar_lista()

    def _eliminar(self):
        if not self._edit_id:
            self.lbl_msg.configure(text="Seleccioná un preset de la lista.")
            return
        _presets.eliminar_preset(self._edit_id)
        self._limpiar_form()
        self._cargar_lista()
        self.lbl_ok.configure(text="Eliminado.")
