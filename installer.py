"""
installer.py — NeuroMood Installer
Compilar con: pyinstaller installer.spec
"""
import sys
import os
import shutil
import subprocess
import threading
import time
import hashlib
import sqlite3
from pathlib import Path

import customtkinter as ctk
from PIL import Image

# Importar utilidades comunes (colores, recurso, acceso directo, captionbar)
try:
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, crear_acceso_directo, aplicar_captionbar_installer,
    )
except ImportError:
    # Fallback frozen: shared/ está junto al exe
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        FONT_FAMILY, recurso, crear_acceso_directo, aplicar_captionbar_installer,
    )

DEFAULT_INSTALL = os.path.join(os.path.expanduser("~"), "NeuroMood")
APP_EXE = "NeuroMood.exe"
APP_NOMBRE = "NeuroMood"


def ruta_app_bundled(exe: str) -> str:
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dist"
    )
    return os.path.join(base, exe)


class InstaladorNeuroMood(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Instalador — NeuroMood")
        self.geometry("740x540")
        self.resizable(False, False)
        self.configure(fg_color=BG_PRIMARY)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 740) // 2
        y = (self.winfo_screenheight() - 540) // 2
        self.geometry(f"740x540+{x}+{y}")

        # iconbitmap() activa _iconbitmap_method_called en CTk, bloqueando su override de 200ms
        self._aplicar_icono()
        self.after(100, lambda: aplicar_captionbar_installer(self))

        self.pagina_actual = 0
        self.install_path = ctk.StringVar(value=DEFAULT_INSTALL)
        self._install_dir_done: Path | None = None
        self._icon_dest_done: str | None = None

        # Identidad del paciente
        self.nombre_paciente = ctk.StringVar()
        self.password_paciente = ctk.StringVar()
        self.confirm_paciente = ctk.StringVar()
        self._es_login = False
        self.install_code_var = ctk.StringVar()
        self._codigo_instalacion = ""

        self._construir_layout()
        self._ir_a(0)

    def _aplicar_icono(self):
        try:
            self.iconbitmap(recurso("installer_icon.ico"))
        except Exception:
            pass

    # ── Layout ─────────────────────────────────────────────────

    def _construir_layout(self):
        self.sidebar = ctk.CTkFrame(self, width=200, fg_color=BG_SECONDARY, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._sidebar_logo()
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(0, 14))
        self._sidebar_pasos()
        ctk.CTkLabel(self.sidebar, text="neuromood.com.ar",
                     font=("Segoe UI", 10), text_color=TEXT_TERT).pack(side="bottom", pady=14)

        self.content = ctk.CTkFrame(self, fg_color=BG_PRIMARY, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        self.page_area = ctk.CTkFrame(self.content, fg_color=BG_PRIMARY)
        self.page_area.pack(fill="both", expand=True, padx=28, pady=(24, 0))

        nav = ctk.CTkFrame(self.content, fg_color=BG_SECONDARY, height=58, corner_radius=0)
        nav.pack(fill="x", side="bottom")
        nav.pack_propagate(False)

        self.btn_ant = ctk.CTkButton(
            nav, text="← Anterior", width=120, height=36,
            fg_color="transparent", border_width=2, border_color=ACCENT,
            text_color=ACCENT, hover_color=BG_SURFACE, font=("Segoe UI", 13),
            command=self._anterior,
        )
        self.btn_ant.pack(side="left", padx=16, pady=11)

        self.btn_sig = ctk.CTkButton(
            nav, text="Siguiente →", width=140, height=36,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY, font=("Segoe UI", 13, "bold"),
            command=self._siguiente,
        )
        self.btn_sig.pack(side="right", padx=16, pady=11)

        self.paginas = [ctk.CTkFrame(self.page_area, fg_color=BG_PRIMARY) for _ in range(4)]
        self._build_p0()
        self._build_p1_registro()
        self._build_p2_instalacion()
        self._build_p3_finalizar()

    def _sidebar_logo(self):
        try:
            img = Image.open(recurso("LOGO.png")).convert("RGBA")
            img.thumbnail((168, 72), Image.LANCZOS)
            self._logo_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            ctk.CTkLabel(self.sidebar, image=self._logo_ctk, text="").pack(pady=(20, 12))
        except Exception:
            ctk.CTkLabel(self.sidebar, text="NeuroMood",
                         font=("Segoe UI", 16, "bold"), text_color=TEXT_PRIMARY).pack(pady=(20, 12))

    def _sidebar_pasos(self):
        self._step_widgets = []
        pasos = ["Bienvenida", "Registro", "Instalación", "Finalizar"]
        for i, nombre in enumerate(pasos):
            row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=3)
            circle = ctk.CTkLabel(row, text=str(i + 1), width=26, height=26,
                                  fg_color=BORDER, corner_radius=13,
                                  font=("Segoe UI", 11, "bold"), text_color=TEXT_TERT)
            circle.pack(side="left")
            lbl = ctk.CTkLabel(row, text=nombre, font=("Segoe UI", 12),
                               text_color=TEXT_TERT, anchor="w")
            lbl.pack(side="left", padx=8)
            self._step_widgets.append((circle, lbl))

    # ── Páginas ────────────────────────────────────────────────

    def _build_p0(self):
        f = self.paginas[0]
        ctk.CTkLabel(f, text="Bienvenido a", font=("Segoe UI", 14), text_color=TEXT_TERT).pack(anchor="w")
        ctk.CTkLabel(f, text="NeuroMood Suite", font=("Segoe UI", 26, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor="w", pady=(2, 10))
        ctk.CTkFrame(f, height=2, fg_color=ACCENT).pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            f,
            text=(
                "Este instalador configurará en tu computadora las\n"
                "aplicaciones de la Suite NeuroMood, diseñadas para\n"
                "acompañar tu bienestar emocional y mental.\n\n"
                "En los siguientes pasos podrás crear tu perfil\n"
                "y elegir cuáles aplicaciones instalar."
            ),
            font=("Segoe UI", 13), text_color=TEXT_SEC, justify="left", anchor="w",
        ).pack(anchor="w", pady=(0, 24))

        card = ctk.CTkFrame(f, fg_color=BG_SURFACE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x")
        ctk.CTkLabel(
            card,
            text="  ℹ   Compatible con Windows 10 y Windows 11.",
            font=("Segoe UI", 12), text_color=TEXT_TERT, anchor="w",
        ).pack(padx=14, pady=8, anchor="w")

    def _build_p1_registro(self):
        f = self.paginas[1]

        self._lbl_reg_titulo = ctk.CTkLabel(
            f, text="Crear cuenta nueva",
            font=("Segoe UI", 20, "bold"), text_color=TEXT_PRIMARY)
        self._lbl_reg_titulo.pack(anchor="w")
        self._lbl_reg_sub = ctk.CTkLabel(
            f, text="Configurá tu perfil para empezar",
            font=("Segoe UI", 12), text_color=TEXT_TERT)
        self._lbl_reg_sub.pack(anchor="w", pady=(2, 10))

        ctk.CTkSegmentedButton(
            f, values=["Primera vez", "Ya tengo cuenta"],
            command=self._cambiar_modo_acceso,
            selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
            unselected_color=BG_SURFACE, unselected_hover_color=BG_PRIMARY,
            fg_color=BG_SURFACE, text_color=TEXT_PRIMARY,
            font=("Segoe UI", 12),
        ).pack(fill="x", pady=(0, 10))

        card = ctk.CTkFrame(f, fg_color=BG_SURFACE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", pady=(0, 10))

        _ent_kw = dict(font=("Segoe UI", 13), fg_color=BG_PRIMARY,
                       border_color=BORDER, text_color=TEXT_PRIMARY, height=38)

        ctk.CTkLabel(card, text="Nombre completo", font=("Segoe UI", 12),
                     text_color=TEXT_SEC, anchor="w").pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkEntry(card, textvariable=self.nombre_paciente, **_ent_kw).pack(
            fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(card, text="Contraseña", font=("Segoe UI", 12),
                     text_color=TEXT_SEC, anchor="w").pack(anchor="w", padx=16, pady=(8, 2))
        ctk.CTkEntry(card, textvariable=self.password_paciente, show="●", **_ent_kw).pack(
            fill="x", padx=16, pady=(0, 4))

        self._frame_confirm = ctk.CTkFrame(card, fg_color="transparent")
        self._frame_confirm.pack(fill="x")
        ctk.CTkLabel(self._frame_confirm, text="Confirmar contraseña", font=("Segoe UI", 12),
                     text_color=TEXT_SEC, anchor="w").pack(anchor="w", padx=16, pady=(8, 2))
        ctk.CTkEntry(self._frame_confirm, textvariable=self.confirm_paciente, show="●",
                     **_ent_kw).pack(fill="x", padx=16, pady=(0, 12))

        self._frame_codigo = ctk.CTkFrame(card, fg_color="transparent")
        # No hacer pack aquí (oculto en modo primera vez)
        ctk.CTkLabel(self._frame_codigo, text="Código de instalación", font=("Segoe UI", 12),
                     text_color=TEXT_SEC, anchor="w").pack(anchor="w", padx=16, pady=(8, 2))
        ctk.CTkEntry(self._frame_codigo, textvariable=self.install_code_var, font=("Segoe UI", 13),
                     fg_color=BG_PRIMARY, border_color=BORDER, text_color=TEXT_PRIMARY,
                     height=38).pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            self._frame_codigo,
            text="El código lo encontrás en tu primera instalación o lo provee tu terapeuta.",
            font=("Segoe UI", 10), text_color=TEXT_TERT, anchor="w",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        info = ctk.CTkFrame(f, fg_color="#091E10", corner_radius=8,
                            border_width=1, border_color=SUCCESS)
        info.pack(fill="x", pady=(0, 8))
        self._lbl_info_reg = ctk.CTkLabel(
            info,
            text="ℹ   Tu contraseña es tu clave de acceso única.\n"
                 "    El profesional puede recuperarla desde el Hub si la olvidás.",
            font=("Segoe UI", 11), text_color=SUCCESS, justify="left", anchor="w",
        )
        self._lbl_info_reg.pack(padx=12, pady=7, anchor="w")

        self._error_registro = ctk.CTkLabel(f, text="", font=("Segoe UI", 12),
                                            text_color=ERROR_C, anchor="w")
        self._error_registro.pack(anchor="w")

    def _cambiar_modo_acceso(self, valor: str):
        self._es_login = (valor == "Ya tengo cuenta")
        if self._es_login:
            self._lbl_reg_titulo.configure(text="Iniciar sesión")
            self._lbl_reg_sub.configure(text="Recuperá tu progreso con tus credenciales")
            self._frame_confirm.pack_forget()
            self._frame_codigo.pack(fill="x")
            self._lbl_info_reg.configure(
                text="ℹ   Usá el mismo nombre y contraseña exactos de tu cuenta.\n"
                     "    Tus datos en la nube se sincronizarán al abrir las apps."
            )
        else:
            self._lbl_reg_titulo.configure(text="Crear cuenta nueva")
            self._lbl_reg_sub.configure(text="Configurá tu perfil para empezar")
            self._frame_confirm.pack(fill="x")
            self._frame_codigo.pack_forget()
            self._lbl_info_reg.configure(
                text="ℹ   Tu contraseña es tu clave de acceso única.\n"
                     "    El profesional puede recuperarla desde el Hub si la olvidás."
            )
        self._error_registro.configure(text="")

    def _build_p2_instalacion(self):
        f = self.paginas[2]
        ctk.CTkLabel(f, text="Instalando...",
                     font=("Segoe UI", 20, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")

        ctk.CTkLabel(f, text="Carpeta de instalación:", font=("Segoe UI", 12),
                     text_color=TEXT_SEC).pack(anchor="w", pady=(12, 3))
        path_row = ctk.CTkFrame(f, fg_color="transparent")
        path_row.pack(fill="x", pady=(0, 12))
        ctk.CTkEntry(path_row, textvariable=self.install_path, font=("Segoe UI", 12),
                     fg_color=BG_SURFACE, border_color=BORDER,
                     text_color=TEXT_PRIMARY, height=36).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(path_row, text="Examinar", width=90, height=36,
                      fg_color=BG_SURFACE, border_width=1, border_color=BORDER,
                      text_color=TEXT_SEC, hover_color=BG_PRIMARY, font=("Segoe UI", 12),
                      command=self._browse).pack(side="right")

        self._progress_bar = ctk.CTkProgressBar(f, height=8, fg_color=BORDER,
                                                progress_color=ACCENT, corner_radius=4)
        self._progress_bar.pack(fill="x", pady=(0, 6))
        self._progress_bar.set(0)
        self._progress_lbl = ctk.CTkLabel(f, text="Presioná 'Instalar' para continuar.",
                                          font=("Segoe UI", 12), text_color=TEXT_TERT, anchor="w")
        self._progress_lbl.pack(anchor="w", pady=(0, 8))
        self._log_frame = ctk.CTkScrollableFrame(f, fg_color=BG_SURFACE, corner_radius=8, height=210,
                                                 scrollbar_button_color=BORDER,
                                                 scrollbar_button_hover_color=ACCENT)
        self._log_frame.pack(fill="both", expand=True)

    def _build_p3_finalizar(self):
        f = self.paginas[3]
        ctk.CTkLabel(f, text="¡Instalación completada!",
                     font=("Segoe UI", 20, "bold"), text_color=SUCCESS).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(
            f,
            text="NeuroMood se instaló correctamente.\n"
                 "Abrí la app e ingresá con tu nombre de usuario para comenzar.",
            font=("Segoe UI", 13), text_color=TEXT_SEC, anchor="w",
        ).pack(anchor="w", pady=(0, 12))

        # Botón principal: abrir la app ahora
        ctk.CTkButton(
            f, text="Abrir NeuroMood ahora →", width=230, height=40,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY, font=("Segoe UI", 13, "bold"),
            corner_radius=8,
            command=self._abrir_app,
        ).pack(anchor="w", pady=(0, 16))

        ctk.CTkFrame(f, height=1, fg_color=BORDER).pack(fill="x", pady=(0, 12))

        self.var_escritorio = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            f, text="Crear acceso directo en el Escritorio",
            variable=self.var_escritorio,
            font=("Segoe UI", 13), text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, checkmark_color="#FFFFFF",
            border_color=BORDER,
        ).pack(anchor="w", pady=(0, 10))

        self.var_menu_inicio = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            f, text="Crear acceso directo en el Menú de Inicio",
            variable=self.var_menu_inicio,
            font=("Segoe UI", 13), text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, checkmark_color="#FFFFFF",
            border_color=BORDER,
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkButton(
            f, text="Abrir carpeta de instalación",
            width=230, height=32,
            fg_color="transparent", border_width=1, border_color=BORDER,
            text_color=TEXT_TERT, hover_color=BG_SURFACE, font=("Segoe UI", 11),
            command=self._abrir_carpeta,
        ).pack(anchor="w")

    # ── Navegación ─────────────────────────────────────────────

    def _ir_a(self, n: int):
        for p in self.paginas:
            p.pack_forget()
        self.paginas[n].pack(fill="both", expand=True)
        self.pagina_actual = n

        for i, (circle, lbl) in enumerate(self._step_widgets):
            if i == n:
                circle.configure(fg_color=ACCENT, text_color="#FFFFFF")
                lbl.configure(text_color=TEXT_PRIMARY, font=("Segoe UI", 12, "bold"))
            elif i < n:
                circle.configure(fg_color=SUCCESS, text_color="#FFFFFF")
                lbl.configure(text_color=TEXT_SEC, font=("Segoe UI", 12))
            else:
                circle.configure(fg_color=BORDER, text_color=TEXT_TERT)
                lbl.configure(text_color=TEXT_TERT, font=("Segoe UI", 12))

        self.btn_ant.configure(state="normal" if n == 1 else "disabled")
        if n == 3:
            self.btn_sig.configure(text="Finalizar", state="normal")
        elif n == 2:
            self.btn_sig.configure(text="Instalar", state="normal")
        else:
            self.btn_sig.configure(text="Siguiente →", state="normal")

    def _anterior(self):
        if self.pagina_actual == 1:
            self._ir_a(0)

    def _siguiente(self):
        if self.pagina_actual == 0:
            self._ir_a(1)

        elif self.pagina_actual == 1:
            nombre = self.nombre_paciente.get().strip()
            pwd = self.password_paciente.get()
            if not nombre:
                self._error_registro.configure(text="  El nombre no puede estar vacío.")
                return
            if len(pwd) < 6:
                self._error_registro.configure(text="  La contraseña debe tener al menos 6 caracteres.")
                return
            if not self._es_login:
                if pwd != self.confirm_paciente.get():
                    self._error_registro.configure(text="  Las contraseñas no coinciden.")
                    return
                import secrets
                self._codigo_instalacion = secrets.token_hex(3).upper()
            else:
                codigo = self.install_code_var.get().strip().upper()
                if not codigo:
                    self._error_registro.configure(text="  Ingresá tu código de instalación.")
                    return
                self._codigo_instalacion = codigo
            self._error_registro.configure(text="")
            self._ir_a(2)

        elif self.pagina_actual == 2:
            if self._es_ruta_protegida(self.install_path.get()):
                from tkinter import messagebox
                if messagebox.askyesno(
                    "Carpeta con restricciones",
                    "Esa carpeta requiere permisos de administrador y el desinstalador\n"
                    "no podrá eliminarla correctamente.\n\n"
                    f"¿Instalar en la carpeta recomendada?\n{DEFAULT_INSTALL}"
                ):
                    self.install_path.set(DEFAULT_INSTALL)
                else:
                    return
            self.btn_sig.configure(text="Instalando...", state="disabled")
            threading.Thread(target=self._instalar, daemon=True).start()

        elif self.pagina_actual == 3:
            self._finalizar()

    def _browse(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(initialdir=self.install_path.get())
        if folder:
            self.install_path.set(folder.replace("/", "\\"))

    def _es_ruta_protegida(self, ruta: str) -> bool:
        ruta_norm = os.path.normpath(ruta).lower()
        protegidas = [
            os.path.normpath(os.environ.get("PROGRAMFILES", r"C:\Program Files")).lower(),
            os.path.normpath(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")).lower(),
            os.path.normpath(os.environ.get("WINDIR", r"C:\Windows")).lower(),
            os.path.normpath(r"C:\ProgramData").lower(),
        ]
        return any(ruta_norm.startswith(p) for p in protegidas)

    # ── Instalación ────────────────────────────────────────────

    def _log(self, texto: str, color: str = TEXT_SEC):
        lbl = ctk.CTkLabel(self._log_frame, text=texto, font=("Segoe UI", 11),
                           text_color=color, anchor="w")
        lbl.pack(anchor="w", padx=10, pady=1)
        try:
            self._log_frame.update()
            self._log_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _set_progress(self, v: float, t: str):
        self._progress_bar.set(v)
        self._progress_lbl.configure(text=t)

    def _registrar_identidad_paciente(self):
        """Guarda patient_id, patient_name y patient_pwd en la DB de NeuroMood."""
        nombre = self.nombre_paciente.get().strip()
        pwd = self.password_paciente.get()
        if not nombre or not pwd:
            return
        # Usar la misma función canónica de identidad.py — garantiza IDs coherentes
        from shared.identidad import generar_patient_id
        pid = generar_patient_id(nombre, pwd, self._codigo_instalacion)
        db_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NeuroMood")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "nm_data.db")
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)"
            )
            for clave, valor in [
                ("patient_name", nombre),
                ("patient_id",   pid),
                ("patient_pwd",  pwd),
                ("install_code", self._codigo_instalacion),
            ]:
                conn.execute(
                    "INSERT OR REPLACE INTO config (clave, valor) VALUES (?, ?)",
                    (clave, valor),
                )
            conn.commit()
            conn.close()
        except Exception as e:
            self._log(f"  Advertencia: no se pudo guardar identidad ({e})", WARNING_C)

    def _instalar(self):
        try:
            install_dir = Path(self.install_path.get())
            total = 4
            paso = 0

            self._set_progress(0, "Creando carpeta de instalación...")
            install_dir.mkdir(parents=True, exist_ok=True)
            paso += 1
            self._set_progress(paso / total, "Carpeta lista.")
            self._log(f"  Carpeta: {install_dir}")

            # Copiar NeuroMood.exe
            self._set_progress(paso / total, "Copiando NeuroMood...")
            src = ruta_app_bundled(APP_EXE)
            if not os.path.exists(src):
                self._log(f"  No encontrado: {APP_EXE}", ERROR_C)
            else:
                shutil.copy2(src, install_dir / APP_EXE)
                self._log(f"  {APP_NOMBRE}", SUCCESS)
            paso += 1
            self._set_progress(paso / total, "NeuroMood copiado.")
            time.sleep(0.05)

            # Icono (oculto, para accesos directos)
            icon_dest = None
            try:
                import ctypes as _ct
                icon_path = install_dir / "NM_icon.ico"
                shutil.copy2(recurso("NM_icon.ico"), icon_path)
                icon_dest = str(icon_path)
                _ct.windll.kernel32.SetFileAttributesW(str(icon_path), 0x2)
            except Exception:
                pass

            # Desinstalador
            self._set_progress(paso / total, "Copiando desinstalador...")
            uninst_dest = install_dir / "Desinstalar NeuroMood.exe"
            try:
                uninst_src = ruta_app_bundled("Desinstalar NeuroMood.exe")
                shutil.copy2(uninst_src, uninst_dest)
                self._log("  Desinstalador copiado", SUCCESS)
            except Exception as e:
                self._log(f"  Desinstalador no disponible: {e}", WARNING_C)
            paso += 1

            # install_path.txt (oculto)
            try:
                import ctypes as _ct
                path_txt = install_dir / "install_path.txt"
                with open(path_txt, "w", encoding="utf-8") as fp:
                    fp.write(str(install_dir))
                _ct.windll.kernel32.SetFileAttributesW(str(path_txt), 0x2)
            except Exception:
                pass

            # Registro en Windows (Panel de control)
            self._registrar_windows(install_dir, uninst_dest)

            paso += 1
            self._set_progress(1.0, "Completado.")
            self._log("")
            self._log("  ¡NeuroMood instalado correctamente!", SUCCESS)

            # Guardar identidad del paciente en la DB
            self._registrar_identidad_paciente()

            self._install_dir_done = install_dir
            self._icon_dest_done = icon_dest

            self.after(900, lambda: self._ir_a(3))

        except PermissionError:
            self._log("", ERROR_C)
            self._log("  Sin permisos en la carpeta seleccionada.", ERROR_C)
            self._log("  Elegí otra ubicación.", TEXT_TERT)
            self._set_progress(0, "Error de permisos.")
            self.after(0, lambda: (
                self._ir_a(2),
                self.btn_sig.configure(text="Instalar", state="normal"),
            ))
        except Exception as e:
            self._log(f"  Error inesperado: {e}", ERROR_C)
            self._set_progress(0, "Error durante la instalación.")
            self.after(0, lambda: self.btn_sig.configure(text="Instalar", state="normal"))

    def _registrar_windows(self, install_dir: Path, uninst_path: Path):
        try:
            import winreg
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMood"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, "NeuroMood")
                # Comillas alrededor de la ruta: Windows las necesita si hay espacios en el nombre de usuario
                winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ, f'"{uninst_path}"')
                # DisplayIcon apunta al exe del desinstalador (icono embebido, no .ico externo)
                winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, f'"{uninst_path}",0')
                winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, "NeuroMood")
                winreg.SetValueEx(k, "URLInfoAbout", 0, winreg.REG_SZ, "https://neuromood.com.ar")
                winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
                winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
        except Exception:
            pass

    # ── Finalizar ──────────────────────────────────────────────

    def _finalizar(self):
        if self._install_dir_done:
            exe_path = str(self._install_dir_done / APP_EXE)
            icono = self._icon_dest_done or exe_path
            if self.var_escritorio.get():
                try:
                    escritorio = Path(os.path.expanduser("~")) / "Desktop"
                    crear_acceso_directo(exe_path, str(escritorio / f"{APP_NOMBRE}.lnk"), icono)
                except Exception:
                    pass
            if self.var_menu_inicio.get():
                try:
                    start_nm = (
                        Path(os.environ.get("APPDATA", ""))
                        / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "NeuroMood"
                    )
                    start_nm.mkdir(parents=True, exist_ok=True)
                    crear_acceso_directo(exe_path, str(start_nm / f"{APP_NOMBRE}.lnk"), icono)
                except Exception:
                    pass
        self.destroy()

    def _abrir_app(self):
        if self._install_dir_done:
            exe = self._install_dir_done / APP_EXE
            if exe.exists():
                try:
                    subprocess.Popen([str(exe)])
                except Exception:
                    pass

    def _abrir_carpeta(self):
        if self._install_dir_done and self._install_dir_done.exists():
            subprocess.Popen(["explorer", str(self._install_dir_done)])


if __name__ == "__main__":
    app = InstaladorNeuroMood()
    app.mainloop()
