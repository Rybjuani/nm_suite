import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
from datetime import datetime
import threading
import time
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas, guardar_config, leer_config
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    InputTexto, mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido,
    mostrar_mensaje, NMToplevel, aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import hora_actual, fecha_hoy

try:
    import pystray
    from PIL import Image as PILImage
    TRAY_DISPONIBLE = True
except ImportError:
    TRAY_DISPONIBLE = False

try:
    import numpy as np
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    SONIDO_DISPONIBLE = True
except Exception:
    SONIDO_DISPONIBLE = False

try:
    import winreg
    _WINREG_OK = True
except ImportError:
    _WINREG_OK = False

_REG_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
_REG_VAL = "NeuroMood_Recordatorios"

DISCLAIMER = "Herramienta de apoyo al bienestar. No sustituye atención profesional ni diagnóstico."


# ── Sonido ───────────────────────────────────────────────────────────────────

def _generar_tono(frecuencia, duracion, volumen=0.25):
    if not SONIDO_DISPONIBLE:
        return None
    try:
        sr = 44100
        t = np.linspace(0, duracion, int(sr * duracion), False)
        onda = np.sin(2 * np.pi * frecuencia * t) * volumen
        fade = int(sr * min(0.02, duracion / 4))
        onda[:fade] *= np.linspace(0, 1, fade)
        onda[-fade:] *= np.linspace(1, 0, fade)
        pcm = (onda * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack((pcm, pcm)))
    except Exception:
        return None


def _reproducir_check():
    s = _generar_tono(1046.5, 0.12)
    if s:
        s.play()


def _reproducir_alarma():
    if not SONIDO_DISPONIBLE:
        return
    try:
        sr = 44100
        dur = 0.18
        t = np.linspace(0, dur, int(sr * dur), False)
        onda = np.sin(2 * np.pi * 784 * t) * 0.18 + np.sin(2 * np.pi * 988 * t) * 0.12
        fade = int(sr * 0.02)
        onda[:fade] *= np.linspace(0, 1, fade)
        onda[-fade:] *= np.linspace(1, 0, fade)
        pcm = (onda * 32767).astype(np.int16)
        pygame.sndarray.make_sound(np.column_stack((pcm, pcm))).play()
    except Exception:
        pass


# ── App ──────────────────────────────────────────────────────────────────────

class RecordatoriosApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        inicializar_tablas()
        try:
            from shared.sync import sync_al_abrir as _sync_al_abrir
            _sync_al_abrir()
        except Exception:
            pass
        self.modo = leer_config("theme", "dark")
        self.hilo_activo  = True
        self.tray_icon    = None
        self._estado_ventana = "zoomed"

        self.title("NeuroMood · Recordatorios de Bienestar")
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

        _tray_mode = "--tray" in sys.argv
        if _tray_mode:
            self.withdraw()
        else:
            self._centrar_ventana()

        self._construir_ui()
        self._reset_diario()
        self._iniciar_monitor()

        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        if _tray_mode:
            self.after(0, self._enviar_a_bandeja)
        self.after(1000, self._poll_tema)

    # ── Window helpers ────────────────────────────────────────────────────────

    def _centrar_ventana(self):
        self._prev_state = "zoomed"
        self.after(50, lambda: self.state("zoomed"))
        self.bind("<Configure>", self._on_configure_centrar)

    def _on_configure_centrar(self, event):
        if event.widget is not self:
            return
        estado = self.state()
        if estado in ("zoomed", "normal"):
            self._estado_ventana = estado
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

    def _rebuild(self):
        estado = self.state()
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        if estado == "zoomed":
            self.state("zoomed")

    # ── UI root ───────────────────────────────────────────────────────────────

    def _construir_ui(self):
        for w in self.winfo_children():
            w.destroy()
        colores = COLORS[self.modo]
        self.configure(fg_color=colores["bg_primary"])

        HeaderFrame(
            self,
            titulo="Recordatorios de Bienestar",
            subtitulo="Recordatorios personalizados para tu bienestar",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        ).pack(fill="x")

        barra = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=42, corner_radius=0)
        barra.pack(fill="x", side="bottom")
        barra.pack_propagate(False)

        self._barra_paciente(barra)

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True,
                       padx=LAYOUT["padding_container"], pady=LAYOUT["padding_container"])

        self._contenido_paciente(contenido)

    # ── Bottom bars ───────────────────────────────────────────────────────────

    def _barra_paciente(self, barra):
        colores = COLORS[self.modo]

        # Left: status indicator
        izq = ctk.CTkFrame(barra, fg_color="transparent")
        izq.pack(side="left", fill="y")
        conn = obtener_conexion()
        n_activos = conn.execute("SELECT COUNT(*) FROM recordatorios WHERE activo = 1").fetchone()[0]
        conn.close()
        _dot = colores["success"] if n_activos > 0 else colores["text_tertiary"]
        ctk.CTkFrame(izq, fg_color=_dot, width=10, height=10, corner_radius=5).pack(
            side="left", padx=(14, 5), pady=16
        )
        ctk.CTkLabel(
            izq,
            text=f"{n_activos} activo{'s' if n_activos != 1 else ''}" if n_activos > 0 else "Sin activos",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=_dot
        ).pack(side="left", padx=(0, 8), pady=5)

        # Right: Iniciar Windows + Acerca de + Cerrar + Equipo
        self._inicio_win_var = ctk.BooleanVar(value=self._inicio_windows_activo())
        sw_frame = ctk.CTkFrame(barra, fg_color="transparent")
        sw_frame.pack(side="right", fill="y", padx=(0, 4))
        ctk.CTkSwitch(
            sw_frame, text="",
            variable=self._inicio_win_var,
            width=46, height=24,
            button_color="#4A8A70" if self.modo == "light" else "#1BAD6A",
            button_hover_color="#3A7060" if self.modo == "light" else "#169758",
            progress_color=colores["success"],
            fg_color="#ACACB8" if self.modo == "light" else "#3A5070",
            command=self._toggle_inicio_windows
        ).pack(side="left", padx=(0, 5), pady=9)
        ctk.CTkLabel(
            sw_frame, text="Iniciar con Windows",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"]
        ).pack(side="left")

        ctk.CTkFrame(barra, fg_color=colores["border"], width=1).pack(
            side="right", fill="y", pady=8, padx=4
        )
        BotonSecundario(
            barra, text="Acerca de", modo=self.modo, width=100, height=28,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=(0, 4), pady=7)
        BotonSecundario(
            barra, text="Cerrar", modo=self.modo, width=70, height=28,
            command=self._mostrar_dialogo_cierre
        ).pack(side="right", padx=(0, 4), pady=7)
        ctk.CTkFrame(barra, fg_color=colores["border"], width=1).pack(
            side="right", fill="y", pady=8, padx=4
        )

    # ── Content layouts ───────────────────────────────────────────────────────

    def _contenido_paciente(self, parent):
        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)
        self._lista_paciente(card)

    # ── Patient: read-only list ───────────────────────────────────────────────

    def _lista_paciente(self, card):
        colores = COLORS[self.modo]
        _acc = colores["warning"] if self.modo == "light" else colores["accent"]

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 6))
        ctk.CTkLabel(
            hdr, text="Mis recordatorios",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(side="left")

        self.frame_lista = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_lista.pack(fill="both", expand=True,
                              padx=LAYOUT["padding_card"], pady=(0, 6))

        self._cargar_lista_paciente()

        if leer_config("perm_recordatorios_manual", "0") == "1":
            self._construir_agregar_recordatorio(card)

        # Disclaimer
        ctk.CTkLabel(
            card, text=DISCLAIMER,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["text_tertiary"],
            wraplength=700, justify="center"
        ).pack(pady=(4, LAYOUT["padding_card"]))

    def _cargar_lista_paciente(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()
        colores = COLORS[self.modo]
        hoy = fecha_hoy()
        conn = obtener_conexion()
        registros = conn.execute(
            "SELECT id, hora, mensaje, dias, activo, fecha_disparo FROM recordatorios ORDER BY hora"
        ).fetchall()
        conn.close()

        if not registros:
            ctk.CTkLabel(
                self.frame_lista, text="No hay recordatorios configurados todavía.",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=30)
            return

        dias_nombres = {1: "Lu", 2: "Ma", 3: "Mi", 4: "Ju", 5: "Vi", 6: "Sá", 7: "Do"}
        for rec in registros:
            es_expirado = rec["fecha_disparo"] == hoy if rec["fecha_disparo"] else False
            es_activo = bool(rec["activo"])

            if es_activo:
                estado_txt = "Activo"
                estado_color = colores["success"]
            elif es_expirado:
                estado_txt = "Hoy ya disparó"
                estado_color = colores["warning"]
            else:
                estado_txt = "Inactivo"
                estado_color = colores["text_tertiary"]

            fila = ctk.CTkFrame(self.frame_lista, fg_color=colores["bg_list_item"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=3)

            ctk.CTkLabel(
                fila, text=rec["hora"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                text_color=(colores["warning"] if self.modo == "light" else colores["accent"]) if es_activo else colores["text_tertiary"]
            ).pack(side="left", padx=(16, 14), pady=14)

            mid = ctk.CTkFrame(fila, fg_color="transparent")
            mid.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(
                mid, text=rec["mensaje"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_primary"] if es_activo else colores["text_tertiary"],
                anchor="w", justify="left"
            ).pack(anchor="w", pady=(10, 0))

            dias_lista = [
                dias_nombres.get(int(d), "")
                for d in rec["dias"].split(",")
                if d.strip().isdigit()
            ]
            ctk.CTkLabel(
                mid, text="  ".join(dias_lista),
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(anchor="w", pady=(2, 10))

            right_col = ctk.CTkFrame(fila, fg_color="transparent")
            right_col.pack(side="right", padx=12, pady=8)

            ctk.CTkLabel(
                right_col, text=estado_txt,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
                text_color=estado_color
            ).pack()

            if leer_config("perm_recordatorios_manual", "0") == "1":
                _sw_color = colores["success"] if self.modo == "light" else colores["accent"]
                sw_var = ctk.BooleanVar(value=es_activo)
                ctk.CTkSwitch(
                    right_col, text="", variable=sw_var, width=44,
                    button_color=_sw_color, button_hover_color=_sw_color,
                    progress_color=_sw_color, fg_color=colores["bg_hover"],
                    command=lambda rid=rec["id"], a=es_activo: self._toggle_activo(rid, a)
                ).pack(pady=(4, 0))

    def _construir_agregar_recordatorio(self, card):
        colores = COLORS[self.modo]
        ctk.CTkFrame(card, height=1, fg_color=colores["border"], corner_radius=0).pack(
            fill="x", padx=LAYOUT["padding_card"], pady=(4, 8))

        add_frame = ctk.CTkFrame(card, fg_color="transparent")
        add_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 8))

        ctk.CTkLabel(
            add_frame, text="Agregar recordatorio",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            text_color=colores["text_secondary"]
        ).pack(anchor="w", pady=(0, 6))

        row1 = ctk.CTkFrame(add_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 4))

        self._entry_hora_nueva = InputTexto(row1, modo=self.modo, placeholder_text="HH:MM", width=80)
        self._entry_hora_nueva.pack(side="left", padx=(0, 8))
        self._entry_msg_nuevo = InputTexto(row1, modo=self.modo, placeholder_text="Mensaje del recordatorio...")
        self._entry_msg_nuevo.pack(side="left", fill="x", expand=True, padx=(0, 8))
        BotonSecundario(row1, text="+ Agregar", modo=self.modo, width=90, height=34,
                        command=self._agregar_recordatorio_manual).pack(side="left")

    def _agregar_recordatorio_manual(self):
        hora = getattr(self, '_entry_hora_nueva', None)
        msg = getattr(self, '_entry_msg_nuevo', None)
        if not hora or not msg:
            return
        hora_txt = hora.get().strip()
        msg_txt = msg.get().strip()
        if not hora_txt or not msg_txt:
            return
        import re
        if not re.match(r"^\d{2}:\d{2}$", hora_txt):
            mostrar_mensaje(self, "Hora inválida", "Formato: HH:MM (ej. 09:30)", tipo="warning", modo=self.modo)
            return
        conn = obtener_conexion()
        try:
            conn.execute(
                "INSERT INTO recordatorios (hora, mensaje, dias, activo) VALUES (?, ?, '1,2,3,4,5,6,7', 1)",
                (hora_txt, msg_txt)
            )
            conn.commit()
        except Exception:
            pass
        conn.close()
        hora.delete(0, "end")
        msg.delete(0, "end")
        self._cargar_lista_paciente()

    def _toggle_activo(self, rec_id, activo_actual):
        nuevo_activo = 0 if activo_actual else 1
        if nuevo_activo == 1:
            conn = obtener_conexion()
            rec_check = conn.execute(
                "SELECT hora, dias FROM recordatorios WHERE id = ?", (rec_id,)
            ).fetchone()
            conn.close()
            if rec_check:
                try:
                    hora_obj = datetime.strptime(rec_check["hora"], "%H:%M")
                    ahora = datetime.now()
                    mins_sel = hora_obj.hour * 60 + hora_obj.minute
                    mins_ahora = ahora.hour * 60 + ahora.minute
                    if mins_sel <= mins_ahora:
                        dias_int = sorted([int(d.strip()) for d in rec_check["dias"].split(",") if d.strip()])
                        hoy_int = ahora.isoweekday()
                        sig_dia = next(
                            ((hoy_int - 1 + off) % 7 + 1 for off in range(1, 8)
                             if (hoy_int - 1 + off) % 7 + 1 in dias_int), None
                        )
                        _nombres = {1:"lunes", 2:"martes", 3:"miércoles", 4:"jueves",
                                    5:"viernes", 6:"sábado", 7:"domingo"}
                        nombre = f"el {_nombres[sig_dia]}" if sig_dia else "el próximo día configurado"
                        mostrar_mensaje(
                            self, "Horario pasado",
                            f"Las {rec_check['hora']} ya pasó hoy.\n"
                            f"Podés activarlo antes de las {rec_check['hora']} {nombre}.",
                            tipo="info", modo=self.modo
                        )
                        self._cargar_lista_paciente()
                        return
                except Exception:
                    pass

        conn = obtener_conexion()
        if nuevo_activo == 1:
            conn.execute("UPDATE recordatorios SET activo = 1, fecha_disparo = NULL WHERE id = ?", (rec_id,))
        else:
            conn.execute("UPDATE recordatorios SET activo = 0 WHERE id = ?", (rec_id,))
        conn.commit()
        rec_hora = rec_mensaje = None
        if nuevo_activo == 1:
            rec = conn.execute("SELECT hora, mensaje FROM recordatorios WHERE id = ?", (rec_id,)).fetchone()
            if rec:
                rec_hora, rec_mensaje = rec["hora"], rec["mensaje"]
        conn.close()

        if nuevo_activo == 1 and rec_hora:
            minuto_actual = datetime.now().strftime("%H:%M")
            if rec_hora == minuto_actual:
                self.after(0, lambda m=rec_mensaje, rid=rec_id: (self._mostrar_popup(m, rid), _reproducir_alarma()))
        if not activo_actual:
            _reproducir_check()
        self._cargar_lista_paciente()

    def _eliminar_recordatorio(self, rec_id):
        conn = obtener_conexion()
        conn.execute("DELETE FROM recordatorios WHERE id = ?", (rec_id,))
        conn.commit()
        conn.close()
        self._cargar_lista_paciente()

    # ── Activity logging ──────────────────────────────────────────────────────

    def _log_mostrar(self, rec_id, mensaje) -> int | None:
        try:
            conn = obtener_conexion()
            cur = conn.execute(
                "INSERT INTO recordatorios_log (fecha, hora, mensaje, rec_id, cerrado) VALUES (?,?,?,?,0)",
                (fecha_hoy(), hora_actual()[:5], mensaje, rec_id)
            )
            log_id = cur.lastrowid
            conn.commit()
            conn.close()
            try:
                from shared.sync import sync_inmediato_background as _sib
                _sib()
            except Exception:
                pass
            return log_id
        except Exception:
            return None

    def _log_cerrar(self, log_id):
        if not log_id:
            return
        try:
            conn = obtener_conexion()
            conn.execute("UPDATE recordatorios_log SET cerrado = 1 WHERE id = ?", (log_id,))
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ── Popup ─────────────────────────────────────────────────────────────────

    def _mostrar_popup(self, mensaje, rec_id=None):
        log_id = self._log_mostrar(rec_id, mensaje)

        if self.tray_icon is not None:
            self._restaurar_desde_bandeja()
        elif self.state() == "iconic":
            self._restaurar_ventana()

        if rec_id is not None:
            self._desactivar_recordatorio(rec_id)

        colores = COLORS[self.modo]
        popup = NMToplevel(self, modo=self.modo)
        popup.title("Recordatorio de Bienestar")
        _w, _h = 420, 240
        popup.geometry(
            f"{_w}x{_h}+{(popup.winfo_screenwidth()-_w)//2}+{(popup.winfo_screenheight()-_h)//2}"
        )
        popup.resizable(False, False)
        popup.configure(fg_color=colores["bg_surface"])
        popup.attributes("-topmost", True)
        popup.grab_set()
        popup.after(10, popup.focus_force)

        # Accent bar
        ctk.CTkFrame(popup, fg_color=colores["success"], height=4, corner_radius=0).pack(fill="x")

        fr = ctk.CTkFrame(popup, fg_color="transparent")
        fr.pack(expand=True, fill="both",
                padx=LAYOUT["padding_container"], pady=LAYOUT["padding_container"])

        ctk.CTkLabel(
            fr, text="Recordatorio de Bienestar",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["success"] if self.modo == "light" else colores["accent"]
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            fr, text=mensaje,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_primary"],
            wraplength=360, justify="center"
        ).pack(pady=(0, 16))

        def _cerrar():
            self._log_cerrar(log_id)
            popup.destroy()

        _kw_verde = {"fg_color": colores["success"], "hover_color": "#4A8A70"} if self.modo == "light" else {}
        BotonPrimario(fr, text="Entendido", modo=self.modo,
                      width=140, command=_cerrar, **_kw_verde).pack()

        ctk.CTkLabel(
            popup, text=DISCLAIMER,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            text_color=colores["text_tertiary"]
        ).pack(pady=(4, 8))

    # ── Monitor ───────────────────────────────────────────────────────────────

    def _iniciar_monitor(self):
        self.ultimo_minuto_notificado = ""

        def monitor():
            ultima_fecha = datetime.now().date()
            ultimo_minuto_consultado = ""
            while self.hilo_activo:
                time.sleep(1)
                ahora = datetime.now()
                fecha_actual = ahora.date()
                if fecha_actual > ultima_fecha:
                    ultima_fecha = fecha_actual
                    self.ultimo_minuto_notificado = ""
                    ultimo_minuto_consultado = ""
                    try:
                        self.after(0, self._reset_diario)
                    except Exception:
                        pass

                minuto_actual = ahora.strftime("%H:%M")
                if minuto_actual == self.ultimo_minuto_notificado:
                    continue
                if minuto_actual == ultimo_minuto_consultado:
                    continue

                ultimo_minuto_consultado = minuto_actual
                dia_semana = ahora.isoweekday()

                try:
                    conn = obtener_conexion()
                    try:
                        recordatorios = conn.execute(
                            "SELECT id, mensaje, dias FROM recordatorios WHERE hora = ? AND activo = 1",
                            (minuto_actual,)
                        ).fetchall()
                    finally:
                        conn.close()
                except Exception:
                    continue

                for rec in recordatorios:
                    if str(dia_semana) not in rec["dias"].split(","):
                        continue
                    self.ultimo_minuto_notificado = minuto_actual
                    try:
                        self.after(0, lambda m=rec["mensaje"], rid=rec["id"]: (
                            self._mostrar_popup(m, rid), _reproducir_alarma()
                        ))
                    except Exception:
                        pass

        threading.Thread(target=monitor, daemon=True).start()

    def _reset_diario(self):
        ahora = datetime.now()
        hoy = ahora.date().isoformat()
        dia_semana = str(ahora.isoweekday())
        hora_ahora = ahora.strftime("%H:%M")
        try:
            conn = obtener_conexion()
            inactivos = conn.execute(
                "SELECT id, dias, fecha_disparo FROM recordatorios WHERE activo = 0"
            ).fetchall()
            for rec in inactivos:
                if rec["fecha_disparo"] == hoy:
                    continue
                if dia_semana in rec["dias"].split(","):
                    conn.execute(
                        "UPDATE recordatorios SET activo = 1, fecha_disparo = NULL WHERE id = ?",
                        (rec["id"],)
                    )
            activos = conn.execute(
                "SELECT id, hora, dias FROM recordatorios WHERE activo = 1"
            ).fetchall()
            for rec in activos:
                if rec["hora"] < hora_ahora and dia_semana in rec["dias"].split(","):
                    conn.execute(
                        "UPDATE recordatorios SET activo = 0, fecha_disparo = ? WHERE id = ?",
                        (hoy, rec["id"])
                    )
            conn.commit()
            conn.close()
        except Exception:
            pass
        try:
            self._cargar_lista_paciente()
        except Exception:
            pass

    def _desactivar_recordatorio(self, rec_id):
        hoy = datetime.now().date().isoformat()
        try:
            conn = obtener_conexion()
            conn.execute(
                "UPDATE recordatorios SET activo = 0, fecha_disparo = ? WHERE id = ?",
                (hoy, rec_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        try:
            self._cargar_lista_paciente()
        except Exception:
            pass

    # ── Windows autostart ─────────────────────────────────────────────────────

    def _inicio_windows_activo(self) -> bool:
        if not _WINREG_OK:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY) as key:
                winreg.QueryValueEx(key, _REG_VAL)
                return True
        except Exception:
            return False

    def _toggle_inicio_windows(self):
        if not _WINREG_OK:
            return
        ya_activo = self._inicio_windows_activo()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                if not ya_activo:
                    cmd = (f'"{sys.executable}" --tray' if getattr(sys, 'frozen', False)
                           else f'"{sys.executable}" "{os.path.abspath(__file__)}" --tray')
                    winreg.SetValueEx(key, _REG_VAL, 0, winreg.REG_SZ, cmd)
                else:
                    winreg.DeleteValue(key, _REG_VAL)
        except Exception:
            pass
        self._inicio_win_var.set(self._inicio_windows_activo())

    # ── Close / tray ──────────────────────────────────────────────────────────

    def _al_cerrar(self):
        conn = obtener_conexion()
        activos = conn.execute("SELECT COUNT(*) FROM recordatorios WHERE activo = 1").fetchone()[0]
        conn.close()
        if activos == 0 or not TRAY_DISPONIBLE:
            self.hilo_activo = False
            self.destroy()
        else:
            self._enviar_a_bandeja()

    def _mostrar_dialogo_cierre(self):
        conn = obtener_conexion()
        n_activos = conn.execute("SELECT COUNT(*) FROM recordatorios WHERE activo = 1").fetchone()[0]
        conn.close()
        if n_activos == 0:
            self._salir_definitivo()
            return

        colores = COLORS[self.modo]
        dlg = NMToplevel(self, modo=self.modo)
        dlg.title("Cerrar")
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        h = 230 if TRAY_DISPONIBLE else 192
        w = 400
        dlg.geometry(f"{w}x{h}+{(dlg.winfo_screenwidth()-w)//2}+{(dlg.winfo_screenheight()-h)//2}")
        dlg.configure(fg_color=colores["bg_surface"])
        dlg.grab_set()
        dlg.after(10, dlg.focus_force)

        pad = LAYOUT["padding_container"]
        fr = ctk.CTkFrame(dlg, fg_color="transparent")
        fr.pack(expand=True, fill="both", padx=pad, pady=pad)

        texto_n = "1 recordatorio activo" if n_activos == 1 else f"{n_activos} recordatorios activos"
        ctk.CTkLabel(fr, text=f"🔔 {texto_n}",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                     text_color=colores["warning"]).pack(pady=(0, 8))
        ctk.CTkLabel(fr, text="Las alarmas no sonarán si cerrás la app con este botón.",
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                     text_color=colores["text_secondary"]).pack(pady=(0, 16))

        if TRAY_DISPONIBLE:
            _kw_band = {"fg_color": colores["success"], "hover_color": "#4A8A70"} if self.modo == "light" else {}
            BotonPrimario(fr, text="Minimizar a la bandeja", modo=self.modo,
                          command=lambda: (dlg.destroy(), self._enviar_a_bandeja()),
                          **_kw_band).pack(fill="x", pady=(0, 8))

        _kw_rojo = {"fg_color": colores["error"], "hover_color": "#BF5555", "border_width": 0} if self.modo == "light" else {}
        BotonSecundario(fr, text="Cerrar de todas formas", modo=self.modo,
                        command=lambda: (dlg.destroy(), self._salir_definitivo()),
                        **_kw_rojo).pack(fill="x", pady=(0, 8))
        BotonSecundario(fr, text="Cancelar", modo=self.modo, command=dlg.destroy).pack(fill="x")

    def _salir_definitivo(self):
        self.hilo_activo = False
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self.destroy()

    def _enviar_a_bandeja(self):
        if not TRAY_DISPONIBLE:
            self.hilo_activo = False
            self.destroy()
            return
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self.withdraw()

        def _img():
            try:
                img = PILImage.open(obtener_ruta_recurso("NM_icon.ico")).convert("RGBA").resize((64, 64), PILImage.LANCZOS)
                return img
            except Exception:
                return PILImage.new("RGBA", (64, 64), (30, 200, 212, 255))

        menu = pystray.Menu(
            pystray.MenuItem("Abrir Recordatorios",
                             lambda icon, item: self.after(0, self._restaurar_desde_bandeja),
                             default=True),
            pystray.MenuItem("Salir",
                             lambda icon, item: self.after(0, self._salir_desde_bandeja)),
        )
        self.tray_icon = pystray.Icon("NM_Recordatorios", _img(),
                                       "Recordatorios de Bienestar", menu=menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _restaurar_desde_bandeja(self):
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self._restaurar_ventana()

    def _salir_desde_bandeja(self):
        self.hilo_activo = False
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self.destroy()

    def _restaurar_ventana(self):
        self.deiconify()
        if getattr(self, "_estado_ventana", "zoomed") == "zoomed":
            self.state("zoomed")
        self.lift()
        self.focus_force()

    # ── Theme sync ────────────────────────────────────────────────────────────

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
    app = RecordatoriosApp()
    app.mainloop()
