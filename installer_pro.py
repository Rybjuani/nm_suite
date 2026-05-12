"""
installer_pro.py — Instalador del Hub Profesional NeuroMood
Compilar con: pyinstaller installer_pro.spec
"""
import sys
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

import customtkinter as ctk
from PIL import Image

BG_PRIMARY   = "#0B1928"
BG_SECONDARY = "#0D2137"
BG_SURFACE   = "#112740"
ACCENT       = "#4A9EE8"
ACCENT_HOVER = "#5AAEF8"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SEC     = "#E8EEF4"
TEXT_TERT    = "#8BA4BE"
BORDER       = "#1A3050"
SUCCESS      = "#22D47E"
WARNING_C    = "#F0A500"
ERROR_C      = "#E8505B"

DEFAULT_INSTALL = os.path.join(os.path.expanduser("~"), "NeuroMood Pro")


def recurso(nombre: str) -> str:
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, nombre)


def ruta_bundled(exe: str) -> str:
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dist"
    )
    return os.path.join(base, "pro", exe)


def ruta_bundled_uninstaller() -> str:
    return ruta_bundled("Desinstalar NeuroMood Pro.exe")


def crear_acceso_directo(origen: str, destino_lnk: str, icono: str):
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        lnk = shell.CreateShortcut(destino_lnk)
        lnk.TargetPath = origen
        lnk.IconLocation = f"{icono},0"
        lnk.Save()
    except Exception:
        import tempfile
        ps_script = (
            f'$s = New-Object -ComObject WScript.Shell\n'
            f'$l = $s.CreateShortcut("{destino_lnk}")\n'
            f'$l.TargetPath = "{origen}"\n'
            f'$l.IconLocation = "{icono},0"\n'
            f'$l.Save()\n'
        )
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".ps1", delete=False) as f:
            f.write(b'\xef\xbb\xbf')
            f.write(ps_script.encode("utf-8"))
            ps1_path = f.name
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-File", ps1_path],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        try:
            os.unlink(ps1_path)
        except Exception:
            pass


class InstaladorPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Instalador — NeuroMood Hub Profesional")
        self.geometry("680x480")
        self.resizable(False, False)
        self.configure(fg_color=BG_PRIMARY)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 680) // 2
        y = (self.winfo_screenheight() - 480) // 2
        self.geometry(f"680x480+{x}+{y}")

        self._aplicar_icono()
        self.after(100, self._aplicar_captionbar_dark)

        self.pagina_actual = 0
        self.install_path = ctk.StringVar(value=DEFAULT_INSTALL)
        self._install_dir_done: Path | None = None
        self._icon_dest_done: str | None = None

        self._construir_layout()
        self._ir_a(0)

    def _aplicar_icono(self):
        try:
            self.iconbitmap(recurso("installer_icon.ico"))
        except Exception:
            pass

    def _aplicar_captionbar_dark(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd == 0:
                hwnd = self.winfo_id()
            v = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), 4)
            if sys.getwindowsversion().build >= 22000:
                r, g, b = 0x0D, 0x21, 0x37
                color = ctypes.c_uint(r | (g << 8) | (b << 16))
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0037)
        except Exception:
            pass

    def _construir_layout(self):
        self.sidebar = ctk.CTkFrame(self, width=190, fg_color=BG_SECONDARY, corner_radius=0)
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
        self.page_area.pack(fill="both", expand=True, padx=26, pady=(22, 0))

        nav = ctk.CTkFrame(self.content, fg_color=BG_SECONDARY, height=54, corner_radius=0)
        nav.pack(fill="x", side="bottom")
        nav.pack_propagate(False)

        self.btn_ant = ctk.CTkButton(
            nav, text="← Anterior", width=110, height=34,
            fg_color="transparent", border_width=2, border_color=ACCENT,
            text_color=ACCENT, hover_color=BG_SURFACE, font=("Segoe UI", 13),
            command=self._anterior,
        )
        self.btn_ant.pack(side="left", padx=14, pady=10)

        self.btn_sig = ctk.CTkButton(
            nav, text="Siguiente →", width=130, height=34,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY, font=("Segoe UI", 13, "bold"),
            command=self._siguiente,
        )
        self.btn_sig.pack(side="right", padx=14, pady=10)

        self.paginas = [ctk.CTkFrame(self.page_area, fg_color=BG_PRIMARY) for _ in range(3)]
        self._build_p0()
        self._build_p1()
        self._build_p2()

    def _sidebar_logo(self):
        try:
            img = Image.open(recurso("LOGO.png")).convert("RGBA")
            img.thumbnail((158, 64), Image.LANCZOS)
            self._logo_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            ctk.CTkLabel(self.sidebar, image=self._logo_ctk, text="").pack(pady=(18, 10))
        except Exception:
            ctk.CTkLabel(self.sidebar, text="NeuroMood",
                         font=("Segoe UI", 15, "bold"), text_color=TEXT_PRIMARY).pack(pady=(18, 10))

    def _sidebar_pasos(self):
        self._step_widgets = []
        for i, nombre in enumerate(["Bienvenida", "Instalación", "Finalizar"]):
            row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=3)
            circle = ctk.CTkLabel(row, text=str(i + 1), width=24, height=24,
                                  fg_color=BORDER, corner_radius=12,
                                  font=("Segoe UI", 11, "bold"), text_color=TEXT_TERT)
            circle.pack(side="left")
            lbl = ctk.CTkLabel(row, text=nombre, font=("Segoe UI", 12),
                               text_color=TEXT_TERT, anchor="w")
            lbl.pack(side="left", padx=8)
            self._step_widgets.append((circle, lbl))

    def _build_p0(self):
        f = self.paginas[0]
        ctk.CTkLabel(f, text="Hub Profesional", font=("Segoe UI", 24, "bold"),
                     text_color=ACCENT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(f, text="NeuroMood Suite — Instalación para profesionales",
                     font=("Segoe UI", 13), text_color=TEXT_TERT).pack(anchor="w", pady=(0, 20))
        ctk.CTkFrame(f, height=2, fg_color=ACCENT).pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            f,
            text=(
                "Este instalador configurará el Hub Profesional NeuroMood\n"
                "en tu computadora.\n\n"
                "Desde el Hub podrás ver datos de tus pacientes,\n"
                "asignar tareas y recordatorios en la nube,\n"
                "y acceder a las herramientas clínicas locales."
            ),
            font=("Segoe UI", 13), text_color=TEXT_SEC, justify="left", anchor="w",
        ).pack(anchor="w", pady=(0, 24))
        card = ctk.CTkFrame(f, fg_color=BG_SURFACE, corner_radius=10,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x")
        ctk.CTkLabel(
            card,
            text="  ℹ   Requiere conexión a internet para funciones remotas.",
            font=("Segoe UI", 12), text_color=TEXT_TERT, anchor="w",
        ).pack(padx=14, pady=8, anchor="w")

    def _build_p1(self):
        f = self.paginas[1]
        ctk.CTkLabel(f, text="Instalación",
                     font=("Segoe UI", 20, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(f, text="Elegí dónde instalar el Hub Profesional",
                     font=("Segoe UI", 12), text_color=TEXT_TERT).pack(anchor="w", pady=(2, 20))

        ctk.CTkLabel(f, text="Carpeta de instalación:", font=("Segoe UI", 12),
                     text_color=TEXT_SEC).pack(anchor="w", pady=(0, 4))
        path_row = ctk.CTkFrame(f, fg_color="transparent")
        path_row.pack(fill="x", pady=(0, 20))
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
        self._progress_lbl = ctk.CTkLabel(f, text="Listo para instalar.", font=("Segoe UI", 12),
                                          text_color=TEXT_TERT, anchor="w")
        self._progress_lbl.pack(anchor="w", pady=(0, 8))
        self._log_frame = ctk.CTkScrollableFrame(f, fg_color=BG_SURFACE, corner_radius=8, height=160,
                                                scrollbar_button_color=BORDER,
                                                scrollbar_button_hover_color=ACCENT)
        self._log_frame.pack(fill="both", expand=True)

    def _build_p2(self):
        f = self.paginas[2]
        ctk.CTkLabel(f, text="¡Instalación completada!",
                     font=("Segoe UI", 20, "bold"), text_color=SUCCESS).pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(f, text="El Hub Profesional NeuroMood está listo.",
                     font=("Segoe UI", 13), text_color=TEXT_SEC).pack(anchor="w", pady=(0, 18))
        ctk.CTkFrame(f, height=1, fg_color=BORDER).pack(fill="x", pady=(0, 16))

        self.var_escritorio = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            f, text="Crear acceso directo en el Escritorio",
            variable=self.var_escritorio,
            font=("Segoe UI", 13), text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, checkmark_color="#FFFFFF",
            border_color=BORDER,
        ).pack(anchor="w", pady=(0, 12))

        self.var_menu_inicio = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            f, text="Crear acceso directo en el Menú de Inicio",
            variable=self.var_menu_inicio,
            font=("Segoe UI", 13), text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, checkmark_color="#FFFFFF",
            border_color=BORDER,
        ).pack(anchor="w", pady=(0, 16))

        ctk.CTkButton(
            f, text="Abrir carpeta de instalación", width=220, height=36,
            fg_color="transparent", border_width=2, border_color=ACCENT,
            text_color=ACCENT, hover_color=BG_SURFACE, font=("Segoe UI", 13),
            command=self._abrir_carpeta,
        ).pack(anchor="w")

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
        if n == 2:
            self.btn_sig.configure(text="Finalizar", state="normal")
        elif n == 1 and self._instalando:
            self.btn_sig.configure(text="Instalando...", state="disabled")
        else:
            self.btn_sig.configure(text="Siguiente →", state="normal")

    _instalando = False

    def _anterior(self):
        if self.pagina_actual == 1:
            self._ir_a(0)

    def _siguiente(self):
        if self.pagina_actual == 0:
            self._ir_a(1)
        elif self.pagina_actual == 1 and not self._instalando:
            self._instalar_ahora()
        elif self.pagina_actual == 2:
            self._finalizar()

    def _browse(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(initialdir=self.install_path.get())
        if folder:
            self.install_path.set(folder.replace("/", "\\"))

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

    def _instalar_ahora(self):
        self._instalando = True
        self.btn_sig.configure(text="Instalando...", state="disabled")
        self.btn_ant.configure(state="disabled")
        threading.Thread(target=self._instalar, daemon=True).start()

    def _instalar(self):
        try:
            install_dir = Path(self.install_path.get())
            self._set_progress(0, "Creando carpeta...")
            install_dir.mkdir(parents=True, exist_ok=True)
            self._log(f"  Carpeta: {install_dir}")

            self._set_progress(0.3, "Instalando Hub Profesional...")
            src = ruta_bundled("HubProfesional.exe")
            if os.path.exists(src):
                shutil.copy2(src, install_dir / "NeuroMood Hub Profesional.exe")
                self._log("  Hub Profesional", SUCCESS)
            else:
                self._log(f"  No encontrado: HubProfesional.exe", WARNING_C)

            self._set_progress(0.5, "Instalando desinstalador...")
            src_un = ruta_bundled_uninstaller()
            uninstaller_dest = install_dir / "Desinstalar NeuroMood Pro.exe"
            if os.path.exists(src_un):
                shutil.copy2(src_un, uninstaller_dest)
                self._log("  Desinstalador", SUCCESS)
            else:
                self._log("  Desinstalar NeuroMood Pro.exe no encontrado", WARNING_C)

            self._set_progress(0.7, "Copiando recursos...")
            icon_dest = None
            try:
                import ctypes as _ct
                icon_path = install_dir / "NM_icon.ico"
                shutil.copy2(recurso("NM_icon.ico"), icon_path)
                icon_dest = str(icon_path)
                _ct.windll.kernel32.SetFileAttributesW(str(icon_path), 0x2)
            except Exception:
                pass

            # Copiar .env a %APPDATA%\NeuroMoodPro\ para que HubProfesional.exe lo encuentre
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            env_dir = os.path.join(appdata, "NeuroMoodPro")
            os.makedirs(env_dir, exist_ok=True)
            env_src = recurso(".env")
            if os.path.exists(env_src):
                try:
                    import ctypes as _ct2
                    env_dest = os.path.join(env_dir, ".env")
                    shutil.copy2(env_src, env_dest)
                    _ct2.windll.kernel32.SetFileAttributesW(env_dest, 0x2)
                    self._log("  Configuracion de red copiada", SUCCESS)
                except Exception as e:
                    self._log(f"  Config red: {e}", WARNING_C)
            else:
                self._log("  Sin .env bundleado — configurar credenciales manualmente", WARNING_C)

            self._registrar_windows(install_dir)
            self._set_progress(1.0, "Completado.")
            self._log("  ¡Hub Profesional instalado correctamente!", SUCCESS)
            self._install_dir_done = install_dir
            self._icon_dest_done = icon_dest
            self._instalando = False
            self.after(800, lambda: self._ir_a(2))

        except PermissionError:
            self._log("  Sin permisos en la carpeta seleccionada.", ERROR_C)
            self._set_progress(0, "Error de permisos.")
            self._instalando = False
            self.after(0, lambda: (
                self.btn_ant.configure(state="normal"),
                self.btn_sig.configure(text="Siguiente →", state="normal"),
            ))
        except Exception as e:
            self._log(f"  Error: {e}", ERROR_C)
            self._set_progress(0, "Error durante la instalación.")
            self._instalando = False

    def _registrar_windows(self, install_dir: Path):
        try:
            import winreg
            exe = install_dir / "NeuroMood Hub Profesional.exe"
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodPro"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, "NeuroMood Hub Profesional")
                uninstaller_path = str(install_dir / "Desinstalar NeuroMood Pro.exe")
                winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_path}"')
                winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, f'"{exe}",0')
                winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, "NeuroMood")
                winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
                winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
        except Exception:
            pass

    def _finalizar(self):
        exe_path = str(self._install_dir_done / "NeuroMood Hub Profesional.exe") if self._install_dir_done else ""
        icono = self._icon_dest_done or exe_path
        if self._install_dir_done and exe_path:
            if self.var_escritorio.get():
                try:
                    escritorio = Path(os.path.expanduser("~")) / "Desktop"
                    crear_acceso_directo(exe_path, str(escritorio / "NeuroMood Hub Profesional.lnk"), icono)
                except Exception:
                    pass
            if self.var_menu_inicio.get():
                try:
                    start_menu = (
                        Path(os.environ.get("APPDATA", ""))
                        / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "NeuroMood"
                    )
                    start_menu.mkdir(parents=True, exist_ok=True)
                    crear_acceso_directo(exe_path, str(start_menu / "NeuroMood Hub Profesional.lnk"), icono)
                except Exception:
                    pass
        self.destroy()

    def _abrir_carpeta(self):
        if self._install_dir_done and self._install_dir_done.exists():
            subprocess.Popen(["explorer", str(self._install_dir_done)])


if __name__ == "__main__":
    app = InstaladorPro()
    app.mainloop()
