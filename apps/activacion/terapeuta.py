"""terapeuta.py — Ventana de Modo Terapeuta para Activación Conductual."""
import sys
import os
import hashlib
import tkinter as tk

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
from shared.db import obtener_conexion, guardar_config, leer_config
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.components import (
    CardFrame, BotonPrimario, BotonSecundario, NMToplevel, mostrar_mensaje
)
import motor
import perfil as _perfil


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


class VentanaTerapeuta(NMToplevel):
    def __init__(self, master, modo: str = "dark"):
        super().__init__(master, modo=modo)
        self.modo = modo
        self._edit_id: int | None = None

        self.title("NeuroMood · Modo Terapeuta")
        w, h = 940, 660
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.minsize(820, 540)
        self.configure(fg_color=COLORS[modo]["bg_primary"])
        self.grab_set()
        self._construir()

    # ── Estructura principal ────────────────────────────────────────────────

    def _construir(self):
        c = COLORS[self.modo]

        header = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Modo Terapeuta",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                     text_color=c["text_primary"]).pack(side="left", padx=LAYOUT["padding_card"])
        ctk.CTkLabel(header, text="⚠ Sesión clínica protegida",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                     text_color=c["warning"]).pack(side="left", padx=(0, 8))
        BotonSecundario(header, text="Cerrar", modo=self.modo, width=80, height=30,
                        command=self.destroy).pack(side="right", padx=LAYOUT["padding_card"], pady=10)

        tab_bar = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=42, corner_radius=0)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        self._tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._tab_frame.pack(fill="both", expand=True,
                             padx=LAYOUT["padding_container"], pady=LAYOUT["padding_container"])

        _act, _off_fg, _off_tx = c["accent"], c["bg_hover"], c["text_secondary"]
        _kw = dict(height=30, corner_radius=LAYOUT["radius_button"], border_width=0,
                   font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"))
        tabs = [("biblioteca", "Biblioteca"), ("perfil", "Perfil paciente"),
                ("pin", "PIN / Seguridad"), ("auditoria", "Auditoría")]
        self._tab_btns: dict[str, ctk.CTkButton] = {}

        def _ir(nombre: str):
            for n, b in self._tab_btns.items():
                if n == nombre:
                    b.configure(fg_color=_act, text_color=c["text_on_accent"])
                else:
                    b.configure(fg_color=_off_fg, text_color=_off_tx)
            for w in self._tab_frame.winfo_children():
                w.destroy()
            getattr(self, f"_tab_{nombre}")()

        primer = True
        for nombre, label in tabs:
            btn = ctk.CTkButton(
                tab_bar, text=label, width=150,
                fg_color=_act if primer else _off_fg,
                text_color=c["text_on_accent"] if primer else _off_tx,
                hover_color=_act,
                command=lambda n=nombre: _ir(n), **_kw
            )
            btn.pack(side="left", padx=(LAYOUT["padding_container"] if primer else 4, 0), pady=6)
            self._tab_btns[nombre] = btn
            primer = False

        self._tab_biblioteca()

    # ── Tab: Biblioteca de actividades ────────────────────────────────────

    def _tab_biblioteca(self):
        c = COLORS[self.modo]
        frame = self._tab_frame
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)
        frame.rowconfigure(0, weight=1)

        card_lista = CardFrame(frame, modo=self.modo)
        card_lista.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        top = ctk.CTkFrame(card_lista, fg_color="transparent")
        top.pack(fill="x", padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8))
        ctk.CTkLabel(top, text="Biblioteca de actividades",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                     text_color=c["text_primary"]).pack(side="left")
        BotonPrimario(top, text="+ Nueva", modo=self.modo, width=90, height=30,
                      command=self._limpiar_form).pack(side="right")

        self.scroll_lista = ctk.CTkScrollableFrame(
            card_lista, fg_color="transparent",
            scrollbar_button_color=c["bg_hover"], scrollbar_button_hover_color=c["accent"]
        )
        self.scroll_lista.pack(fill="both", expand=True,
                               padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))
        self._cargar_lista()

        card_form = CardFrame(frame, modo=self.modo, width=370)
        card_form.grid(row=0, column=1, sticky="nsew")
        card_form.grid_propagate(False)
        self.card_form = card_form
        self._construir_form()

    def _cargar_lista(self):
        for w in self.scroll_lista.winfo_children():
            w.destroy()
        c = COLORS[self.modo]
        conn = obtener_conexion()
        acts = conn.execute(
            "SELECT * FROM activacion_actividades ORDER BY animo_min, dificultad, nombre"
        ).fetchall()
        conn.close()

        if not acts:
            ctk.CTkLabel(self.scroll_lista, text="Sin actividades. Agregá una nueva.",
                         text_color=c["text_tertiary"],
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"])).pack(pady=20)
            return

        _cmap = motor.CATEGORIA_COLOR_DARK if self.modo == "dark" else motor.CATEGORIA_COLOR_LIGHT
        for act in acts:
            fila = ctk.CTkFrame(self.scroll_lista, fg_color=c["bg_list_item"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=2)

            sw_var = ctk.BooleanVar(value=bool(act["activa"]))
            ctk.CTkSwitch(fila, text="", variable=sw_var, width=44,
                          progress_color=c["success"], button_color=c["success"],
                          fg_color=c["bg_hover"],
                          command=lambda aid=act["id"], v=sw_var: self._toggle_activa(aid, v.get())
                          ).pack(side="left", padx=(8, 4), pady=6)

            ctk.CTkLabel(fila, text=act["nombre"],
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                         text_color=c["text_primary"] if act["activa"] else c["text_tertiary"]
                         ).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(fila, text=act["categoria"],
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                         text_color=_cmap.get(act["categoria"], c["accent"])
                         ).pack(side="left")

            ctk.CTkButton(fila, text="✕", width=26, height=26,
                          fg_color=c["error"],
                          hover_color="#BF5555" if self.modo == "light" else "#C83040",
                          text_color="#FFFFFF", corner_radius=6,
                          font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                          command=lambda aid=act["id"]: self._eliminar(aid)
                          ).pack(side="right", padx=(4, 8), pady=6)
            ctk.CTkButton(fila, text="✏", width=26, height=26,
                          fg_color=c["warning"],
                          hover_color="#B06830" if self.modo == "light" else "#D08800",
                          text_color="#FFFFFF", corner_radius=6,
                          font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                          command=lambda a=dict(act): self._editar(a)
                          ).pack(side="right", padx=4, pady=6)

    def _construir_form(self):
        c = COLORS[self.modo]
        for w in self.card_form.winfo_children():
            w.destroy()

        sf = ctk.CTkScrollableFrame(self.card_form, fg_color="transparent",
                                     scrollbar_button_color=c["bg_hover"],
                                     scrollbar_button_hover_color=c["accent"])
        sf.pack(fill="both", expand=True,
                padx=LAYOUT["padding_card"], pady=LAYOUT["padding_card"])

        self.lbl_form_t = ctk.CTkLabel(
            sf, text="Nueva actividad",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["accent"])
        self.lbl_form_t.pack(anchor="w", pady=(0, 10))

        def _lbl(texto):
            ctk.CTkLabel(sf, text=texto,
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                         text_color=c["text_tertiary"]).pack(anchor="w", pady=(5, 1))

        def _entry(valor=""):
            e = ctk.CTkEntry(sf, fg_color=c["bg_input"], text_color=c["text_primary"],
                             border_color=c["border"], border_width=1,
                             font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]), height=32)
            if valor:
                e.insert(0, valor)
            e.pack(fill="x")
            return e

        _lbl("Nombre")
        self.ent_nombre = _entry()
        _lbl("Descripción")
        self.ent_desc = ctk.CTkTextbox(sf, fg_color=c["bg_input"], text_color=c["text_primary"],
                                        border_color=c["border"], border_width=1,
                                        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                                        height=56)
        self.ent_desc.pack(fill="x")
        _lbl("Categoría")
        self.cmb_cat = ctk.CTkComboBox(
            sf, values=motor.CATEGORIAS, fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1,
            button_color=c["bg_hover"], button_hover_color=c["accent"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]), height=32)
        self.cmb_cat.set(motor.CATEGORIAS[0])
        self.cmb_cat.pack(fill="x")
        _lbl("Beneficio esperado")
        self.ent_ben = _entry()
        _lbl("Dificultad")
        self._dif = tk.IntVar(value=1)
        dif_row = ctk.CTkFrame(sf, fg_color="transparent")
        dif_row.pack(anchor="w")
        for txt, val in [("Baja", 1), ("Media", 2), ("Alta", 3)]:
            ctk.CTkRadioButton(dif_row, text=txt, variable=self._dif, value=val,
                               font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])
                               ).pack(side="left", padx=(0, 12))
        _lbl("Duración (min)")
        self.ent_dur = _entry("10")
        _lbl("Rango de ánimo recomendado")

        def _slider_row(label_widget, init_val, callback):
            row = ctk.CTkFrame(sf, fg_color="transparent")
            row.pack(fill="x", pady=(0, 2))
            lbl_v = ctk.CTkLabel(row, text=f"{label_widget}: {init_val}",
                                  font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                                  text_color=c["success"], width=55)
            lbl_v.pack(side="left")
            sld = ctk.CTkSlider(row, from_=0, to=10, number_of_steps=10,
                                progress_color=c["success"], button_color=c["success"],
                                fg_color=c["progress_track"],
                                command=lambda v, l=lbl_v, lk=label_widget: (
                                    l.configure(text=f"{lk}: {int(round(v))}"),
                                    callback(int(round(v)))
                                ))
            sld.set(init_val)
            sld.pack(side="left", fill="x", expand=True, padx=6)
            return sld

        self._amin_val, self._amax_val = 0, 10
        self.sld_amin = _slider_row("Mín", 0, lambda v: setattr(self, '_amin_val', v))
        self.sld_amax = _slider_row("Máx", 10, lambda v: setattr(self, '_amax_val', v))

        btn_row = ctk.CTkFrame(sf, fg_color="transparent")
        btn_row.pack(fill="x", pady=(12, 0))
        BotonPrimario(btn_row, text="Guardar", modo=self.modo,
                      command=self._guardar, height=34).pack(side="left", fill="x", expand=True, padx=(0, 4))
        BotonSecundario(btn_row, text="Cancelar", modo=self.modo,
                        command=self._limpiar_form, height=34).pack(side="left", fill="x", expand=True)

    def _limpiar_form(self):
        self._edit_id = None
        self.lbl_form_t.configure(text="Nueva actividad")
        self.ent_nombre.delete(0, "end")
        self.ent_desc.delete("1.0", "end")
        self.cmb_cat.set(motor.CATEGORIAS[0])
        self.ent_ben.delete(0, "end")
        self._dif.set(1)
        self.ent_dur.delete(0, "end")
        self.ent_dur.insert(0, "10")
        self.sld_amin.set(0)
        self.sld_amax.set(10)
        self._amin_val, self._amax_val = 0, 10

    def _editar(self, act: dict):
        self._edit_id = act["id"]
        self.lbl_form_t.configure(text=f"Editando: {act['nombre'][:28]}")
        self.ent_nombre.delete(0, "end");   self.ent_nombre.insert(0, act["nombre"])
        self.ent_desc.delete("1.0", "end"); self.ent_desc.insert("1.0", act["descripcion"])
        self.cmb_cat.set(act["categoria"])
        self.ent_ben.delete(0, "end");      self.ent_ben.insert(0, act.get("beneficio", ""))
        self._dif.set(act["dificultad"])
        self.ent_dur.delete(0, "end");      self.ent_dur.insert(0, str(act["duracion_min"]))
        self.sld_amin.set(act["animo_min"]); self._amin_val = act["animo_min"]
        self.sld_amax.set(act["animo_max"]); self._amax_val = act["animo_max"]

    def _guardar(self):
        nombre = self.ent_nombre.get().strip()
        if not nombre:
            return
        desc = self.ent_desc.get("1.0", "end").strip()
        cat  = self.cmb_cat.get()
        dif  = self._dif.get()
        ben  = self.ent_ben.get().strip()
        try:
            dur = max(1, int(self.ent_dur.get()))
        except ValueError:
            dur = 10
        emin = min(self._amin_val, self._amax_val)
        emax = max(self._amin_val, self._amax_val)

        conn = obtener_conexion()
        if self._edit_id is None:
            conn.execute(
                "INSERT INTO activacion_actividades "
                "(nombre, descripcion, categoria, dificultad, duracion_min, beneficio, animo_min, animo_max, activa, es_custom) "
                "VALUES (?,?,?,?,?,?,?,?,1,1)",
                (nombre, desc, cat, dif, dur, ben, emin, emax)
            )
        else:
            conn.execute(
                "UPDATE activacion_actividades SET nombre=?,descripcion=?,categoria=?,"
                "dificultad=?,duracion_min=?,beneficio=?,animo_min=?,animo_max=? WHERE id=?",
                (nombre, desc, cat, dif, dur, ben, emin, emax, self._edit_id)
            )
        conn.commit()
        conn.close()
        self._limpiar_form()
        self._cargar_lista()

    def _toggle_activa(self, act_id: int, activa: bool):
        conn = obtener_conexion()
        conn.execute("UPDATE activacion_actividades SET activa=? WHERE id=?",
                     (1 if activa else 0, act_id))
        conn.commit()
        conn.close()

    def _eliminar(self, act_id: int):
        conn = obtener_conexion()
        act = conn.execute("SELECT nombre, es_custom FROM activacion_actividades WHERE id=?",
                           (act_id,)).fetchone()
        conn.close()
        if not act:
            return
        conn = obtener_conexion()
        conn.execute("DELETE FROM activacion_actividades WHERE id=?", (act_id,))
        conn.commit()
        conn.close()
        if self._edit_id == act_id:
            self._limpiar_form()
        self._cargar_lista()

    # ── Tab: Perfil del paciente ─────────────────────────────────────────

    def _tab_perfil(self):
        c = COLORS[self.modo]
        perfil = _perfil.cargar_perfil()
        card = CardFrame(self._tab_frame, modo=self.modo)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(card, text="Perfil del paciente",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                     text_color=c["text_primary"]
                     ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 2), anchor="w")
        ctk.CTkLabel(
            card,
            text="Esta información personaliza las sugerencias. No se comparte ni se envía a ningún servidor.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=c["text_tertiary"], wraplength=680, justify="left"
        ).pack(padx=LAYOUT["padding_card"], pady=(0, 10), anchor="w")

        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                         scrollbar_button_color=c["bg_hover"],
                                         scrollbar_button_hover_color=c["accent"])
        scroll.pack(fill="both", expand=True, padx=LAYOUT["padding_card"],
                    pady=(0, LAYOUT["padding_card"]))
        scroll.columnconfigure(0, weight=1)
        scroll.columnconfigure(1, weight=1)

        def _lbl_f(parent, texto):
            ctk.CTkLabel(parent, text=texto,
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                         text_color=c["text_tertiary"]).pack(anchor="w", pady=(8, 2))

        def _entry_f(parent, valor=""):
            e = ctk.CTkEntry(parent, fg_color=c["bg_input"], text_color=c["text_primary"],
                             border_color=c["border"], border_width=1,
                             font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]), height=32)
            if valor:
                e.insert(0, valor)
            e.pack(fill="x")
            return e

        # Columna izquierda
        izq = ctk.CTkFrame(scroll, fg_color="transparent")
        izq.grid(row=0, column=0, padx=(0, 12), sticky="new")

        _lbl_f(izq, "Metas terapéuticas")
        self.ent_metas = _entry_f(izq, perfil.get("metas", ""))

        _lbl_f(izq, "Restricciones (físicas o psicológicas)")
        self.ent_restricciones = _entry_f(izq, perfil.get("restricciones", ""))

        _lbl_f(izq, "Horario preferido")
        self.cmb_horario = ctk.CTkComboBox(
            izq, values=["Flexible", "Mañana", "Tarde", "Noche"],
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1,
            button_color=c["bg_hover"], button_hover_color=c["accent"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]), height=32)
        self.cmb_horario.set(perfil.get("horario", "flexible").capitalize())
        self.cmb_horario.pack(fill="x")

        _lbl_f(izq, "Notas del terapeuta (privadas)")
        self.txt_notas = ctk.CTkTextbox(
            izq, fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]), height=100)
        notas = perfil.get("notas_terapeuta", "")
        if notas:
            self.txt_notas.insert("1.0", notas)
        self.txt_notas.pack(fill="x")

        # Columna derecha — categorías preferidas
        der = ctk.CTkFrame(scroll, fg_color="transparent")
        der.grid(row=0, column=1, sticky="new")

        _lbl_f(der, "Categorías de actividad preferidas")
        cats_pref = {c2.strip() for c2 in perfil.get("cat_preferidas", "").split(",") if c2.strip()}
        self._cat_vars: dict[str, tk.BooleanVar] = {}
        _cmap = motor.CATEGORIA_COLOR_DARK if self.modo == "dark" else motor.CATEGORIA_COLOR_LIGHT
        for cat in motor.CATEGORIAS:
            var = tk.BooleanVar(value=cat in cats_pref)
            self._cat_vars[cat] = var
            ctk.CTkCheckBox(
                der, text=cat, variable=var,
                text_color=_cmap.get(cat, c["text_primary"]),
                fg_color=_cmap.get(cat, c["accent"]),
                hover_color=_cmap.get(cat, c["accent_hover"]),
                checkmark_color="#FFFFFF",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"])
            ).pack(anchor="w", pady=3)

        BotonPrimario(
            scroll, text="Guardar perfil", modo=self.modo,
            command=self._guardar_perfil, height=34
        ).grid(row=1, column=0, columnspan=2, pady=(14, 0), sticky="ew")

    def _guardar_perfil(self):
        cats = ",".join(cat for cat, var in self._cat_vars.items() if var.get())
        _perfil.guardar_perfil({
            "metas":           self.ent_metas.get().strip(),
            "restricciones":   self.ent_restricciones.get().strip(),
            "horario":         self.cmb_horario.get().lower(),
            "cat_preferidas":  cats,
            "notas_terapeuta": self.txt_notas.get("1.0", "end").strip(),
        })
        mostrar_mensaje(self, "Perfil guardado",
                        "El perfil del paciente fue guardado correctamente.",
                        tipo="success", modo=self.modo)

    # ── Tab: PIN / Seguridad ────────────────────────────────────────────

    def _tab_pin(self):
        c = COLORS[self.modo]
        card = CardFrame(self._tab_frame, modo=self.modo)
        card.pack(fill="both", expand=True)
        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.pack(padx=LAYOUT["padding_card"] * 2, pady=LAYOUT["padding_card"] * 2, anchor="nw")

        ctk.CTkLabel(frame, text="Seguridad · PIN del Modo Terapeuta",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                     text_color=c["text_primary"]).pack(anchor="w", pady=(0, 8))

        pin_actual = leer_config("pin_terapeuta", "")
        est_txt = "PIN activo — el acceso requiere contraseña." if pin_actual \
                  else "Sin PIN — el Modo Terapeuta es libre."
        ctk.CTkLabel(frame, text=est_txt,
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                     text_color=c["success"] if pin_actual else c["warning"]
                     ).pack(anchor="w", pady=(0, 16))

        def _campo(label):
            ctk.CTkLabel(frame, text=label,
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                         text_color=c["text_tertiary"]).pack(anchor="w", pady=(4, 2))
            e = ctk.CTkEntry(frame, show="•", width=220,
                             fg_color=c["bg_input"], text_color=c["text_primary"],
                             border_color=c["border"], border_width=1,
                             font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]), height=34)
            e.pack(anchor="w")
            return e

        ent_n = _campo("Nuevo PIN (mínimo 4 caracteres)")
        ent_c = _campo("Confirmar PIN")

        def _guardar_pin():
            n, conf = ent_n.get(), ent_c.get()
            if len(n) < 4:
                mostrar_mensaje(self, "PIN inválido", "El PIN debe tener al menos 4 caracteres.",
                                tipo="warning", modo=self.modo); return
            if n != conf:
                mostrar_mensaje(self, "No coincide", "Los campos de PIN no coinciden.",
                                tipo="error", modo=self.modo); return
            guardar_config("pin_terapeuta", hash_pin(n))
            mostrar_mensaje(self, "PIN guardado", "El PIN fue configurado correctamente.",
                            tipo="success", modo=self.modo)
            self._tab_pin()

        def _quitar_pin():
            guardar_config("pin_terapeuta", "")
            mostrar_mensaje(self, "PIN eliminado", "El Modo Terapeuta ya no requiere PIN.",
                            tipo="info", modo=self.modo)
            self._tab_pin()

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(anchor="w", pady=(16, 0))
        BotonPrimario(btn_row, text="Guardar PIN", modo=self.modo,
                      command=_guardar_pin, height=34).pack(side="left", padx=(0, 8))
        if pin_actual:
            BotonSecundario(btn_row, text="Quitar PIN", modo=self.modo,
                            command=_quitar_pin, height=34).pack(side="left")

    # ── Tab: Auditoría ─────────────────────────────────────────────────

    def _tab_auditoria(self):
        c = COLORS[self.modo]
        card = CardFrame(self._tab_frame, modo=self.modo)
        card.pack(fill="both", expand=True)
        ctk.CTkLabel(card, text="Auditoría · Últimas sesiones del paciente",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                     text_color=c["text_primary"]
                     ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8), anchor="w")

        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                         scrollbar_button_color=c["bg_hover"],
                                         scrollbar_button_hover_color=c["accent"])
        scroll.pack(fill="both", expand=True, padx=LAYOUT["padding_card"],
                    pady=(0, LAYOUT["padding_card"]))

        conn = obtener_conexion()
        rows = conn.execute(
            "SELECT fecha, hora, energia, animo, actividad, resultado "
            "FROM activacion ORDER BY fecha DESC, hora DESC LIMIT 40"
        ).fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(scroll, text="Sin registros.",
                         text_color=c["text_tertiary"],
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"])).pack(pady=20)
            return

        _col = {"hecha": c["success"], "intentada": c["warning"], "no_pude": c["error"]}
        _txt = {"hecha": "✓ Hecha", "intentada": "~ Intentada", "no_pude": "✗ No pude"}

        for r in rows:
            fila = ctk.CTkFrame(scroll, fg_color=c["bg_list_item"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=2)
            col = _col.get(r["resultado"], c["text_tertiary"])
            txt = _txt.get(r["resultado"], r["resultado"])

            meta = ctk.CTkFrame(fila, fg_color="transparent")
            meta.pack(fill="x", padx=8, pady=(4, 2))
            ctk.CTkLabel(meta, text=txt,
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
                         text_color=col).pack(side="left")
            ctk.CTkLabel(meta,
                         text=f"{r['fecha']} {r['hora'][:5]}  ·  Ánimo: {r['animo']}",
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                         text_color=c["text_tertiary"]).pack(side="right")
            ctk.CTkLabel(fila, text=r["actividad"],
                         font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                         text_color=c["text_secondary"],
                         wraplength=620, justify="left", anchor="w"
                         ).pack(padx=8, pady=(0, 5), anchor="w")
