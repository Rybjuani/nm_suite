"""
uninstaller.py — NeuroMood Suite Uninstaller
Compilar con: pyinstaller uninstaller.spec
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

try:
    from shared.installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        recurso, aplicar_captionbar_installer,
    )
except ImportError:
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from installer_common import (
        BG_PRIMARY, BG_SECONDARY, BG_SURFACE, ACCENT, ACCENT_HOVER,
        TEXT_PRIMARY, TEXT_SEC, TEXT_TERT, BORDER, SUCCESS, WARNING_C, ERROR_C,
        recurso, aplicar_captionbar_installer,
    )

NM_PROCESOS = [
    "NeuroMood.exe",
]

APPS_NOMBRES = [
    "NeuroMood",
]


def detectar_install_dir() -> str:
    if "--install-dir" in sys.argv:
        idx = sys.argv.index("--install-dir")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMood",
        ) as k:
            val, _ = winreg.QueryValueEx(k, "InstallLocation")
            if val:
                return val
    except Exception:
        pass
    self_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    txt = self_dir / "install_path.txt"
    if txt.exists():
        return txt.read_text(encoding="utf-8").strip()
    return str(self_dir)


def matar_procesos_neuromood(install_dir: str):
    for proc_name in NM_PROCESOS:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", proc_name],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
        except Exception:
            pass
    try:
        escaped = install_dir.replace("\\", "\\\\")
        result = subprocess.run(
            ["wmic", "process", "where",
             f"ExecutablePath like '{escaped}%'",
             "get", "ProcessId"],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
        for line in result.stdout.splitlines():
            pid = line.strip()
            if pid.isdigit():
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5,
                )
    except Exception:
        pass


def eliminar_registro_windows():
    import winreg
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMood"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            winreg.DeleteKey(hive, key_path)
        except Exception:
            pass


def eliminar_accesos():
    escritorio = Path(os.path.expanduser("~")) / "Desktop"
    start_menu = (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "NeuroMood"
    )
    # Borrar por nombre exacto
    for nombre in APPS_NOMBRES:
        try:
            (escritorio / f"{nombre}.lnk").unlink(missing_ok=True)
        except Exception:
            pass
    # Borrar también cualquier .lnk residual con nombre corrupto (encoding anterior)
    try:
        for lnk in escritorio.glob("*.lnk"):
            target = ""
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                target = shell.CreateShortcut(str(lnk)).TargetPath
            except Exception:
                pass
            if "NeuroMood" in target or "neuromood" in target.lower():
                lnk.unlink(missing_ok=True)
    except Exception:
        pass
    # Borrar carpeta completa del menú inicio
    try:
        shutil.rmtree(str(start_menu), ignore_errors=True)
    except Exception:
        pass


def cerrar_explorer_en(carpeta: str):
    try:
        ps_cmd = (
            '(New-Object -ComObject Shell.Application).Windows() | '
            'Where-Object { $_.LocationURL -match "' +
            carpeta.replace("\\", "/").replace(" ", "%20") +
            '" } | ForEach-Object { $_.Quit() }'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
    except Exception:
        pass


def vaciar_carpeta(carpeta: str):
    """Borra el contenido interno archivo por archivo vía shell antes de que el bat borre el directorio raíz."""
    if not Path(carpeta).exists():
        return
    subprocess.run(
        f'del /f /s /q "{carpeta}\\*"',
        shell=True, capture_output=True, timeout=30,
    )
    subprocess.run(
        f'for /d %x in ("{carpeta}\\*") do @rd /s /q "%x"',
        shell=True, capture_output=True, timeout=30,
    )


def lanzar_bat_limpieza(install_dir: str, appdata_dir: str, eliminar_appdata: bool = True):
    """
    Escribe un bat en %TEMP% que borra install_dir y opcionalmente appdata_dir,
    más el exe temporal. El proceso ya corre desde TEMP.
    """
    temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
    temp_exe = str(Path(temp_dir) / "_nm_desinstalar.exe")
    bat = Path(temp_dir) / "_nm_cleanup.bat"
    lines = [
        "@echo off",
        f'cd /d "{temp_dir}"',
        "ping 127.0.0.1 -n 5 > nul",
        f'rd /s /q "{install_dir}" 2>nul',
    ]
    if eliminar_appdata:
        lines.append(f'rd /s /q "{appdata_dir}" 2>nul')
    lines += [
        f'del /f /q "{temp_exe}" 2>nul',
        'del /f /q "%~f0"',
    ]
    try:
        bat.write_text("\r\n".join(lines), encoding="ascii")
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(
            None, "open", "cmd.exe", f'/c "{bat}"', temp_dir, 0
        )
    except Exception:
        pass


def relanzar_desde_temp() -> bool:
    """
    Si el exe NO está corriendo desde %TEMP%, se auto-copia ahí y relanza
    con --install-dir y --from-temp, luego retorna True para que el original salga.
    Así el proceso activo no tiene ningún handle a install_dir ni AppData.
    """
    if not getattr(sys, "frozen", False):
        return False
    if "--from-temp" in sys.argv:
        return False

    temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
    self_exe = sys.executable
    temp_exe = str(Path(temp_dir) / "_nm_desinstalar.exe")

    if os.path.normcase(self_exe) == os.path.normcase(temp_exe):
        return False

    install_dir = detectar_install_dir()
    try:
        shutil.copy2(self_exe, temp_exe)
        subprocess.Popen([temp_exe, "--install-dir", install_dir, "--from-temp"])
        return True
    except Exception:
        return False


class DesinstaladorNeuroMood(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Desinstalar — NeuroMood")
        self.geometry("480x340")
        self.resizable(False, False)
        self.configure(fg_color=BG_PRIMARY)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 480) // 2
        y = (self.winfo_screenheight() - 340) // 2
        self.geometry(f"480x340+{x}+{y}")

        try:
            self.iconbitmap(recurso("no_symbol.ico"))
        except Exception:
            pass
        self.after(100, lambda: aplicar_captionbar_installer(self))

        self._install_dir = detectar_install_dir()
        self._construir_ui()

    def _construir_ui(self):
        header = ctk.CTkFrame(self, fg_color=BG_SECONDARY, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        try:
            img = Image.open(recurso("LOGO.png")).convert("RGBA")
            img.thumbnail((120, 40), Image.LANCZOS)
            self._logo_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            ctk.CTkLabel(header, image=self._logo_ctk, text="").pack(side="left", padx=20, pady=8)
        except Exception:
            ctk.CTkLabel(header, text="NeuroMood", font=("Segoe UI", 14, "bold"),
                         text_color=TEXT_PRIMARY).pack(side="left", padx=20)
        ctk.CTkFrame(header, height=1, fg_color=BORDER).pack(side="bottom", fill="x")

        self.body = ctk.CTkFrame(self, fg_color=BG_PRIMARY)
        self.body.pack(fill="both", expand=True, padx=28, pady=16)

        self._mostrar_confirmacion()

    def _limpiar_body(self):
        for w in self.body.winfo_children():
            w.destroy()

    def _mostrar_confirmacion(self):
        self._limpiar_body()
        self._conservar_datos = ctk.BooleanVar(value=True)

        ctk.CTkLabel(self.body, text="Desinstalar NeuroMood",
                     font=("Segoe UI", 16, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            self.body,
            text=(
                "Se eliminarán los archivos de instalación de NeuroMood\n"
                f"de tu computadora.\n\nCarpeta: {self._install_dir}"
            ),
            font=("Segoe UI", 12), text_color=TEXT_SEC, justify="left", anchor="w",
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkCheckBox(
            self.body,
            text="Conservar mis datos personales (registros, historial y configuración)",
            variable=self._conservar_datos,
            font=("Segoe UI", 11),
            text_color=TEXT_SEC,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            border_color=BORDER,
            checkmark_color="#FFFFFF",
        ).pack(anchor="w", pady=(0, 20))

        btn_row = ctk.CTkFrame(self.body, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        ctk.CTkButton(
            btn_row, text="Cancelar", width=110, height=34,
            fg_color="transparent", border_width=2, border_color=ACCENT,
            text_color=ACCENT, hover_color=BG_SURFACE, font=("Segoe UI", 12),
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="Desinstalar", width=130, height=34,
            fg_color=ERROR_C, hover_color="#C83040",
            text_color=TEXT_PRIMARY, font=("Segoe UI", 12, "bold"),
            command=self._iniciar_desinstalacion,
        ).pack(side="right")

    def _iniciar_desinstalacion(self):
        self._conservar = self._conservar_datos.get()
        self._limpiar_body()

        ctk.CTkLabel(self.body, text="Desinstalando...",
                     font=("Segoe UI", 16, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 12))

        self._pbar = ctk.CTkProgressBar(self.body, height=6, fg_color=BORDER,
                                        progress_color=ACCENT, corner_radius=3)
        self._pbar.pack(fill="x", pady=(0, 8))
        self._pbar.set(0)

        self._status = ctk.CTkLabel(self.body, text="Preparando...",
                                    font=("Segoe UI", 11), text_color=TEXT_TERT, anchor="w")
        self._status.pack(anchor="w")

        threading.Thread(target=self._desinstalar, daemon=True).start()

    def _set(self, progress: float, text: str):
        def _update():
            self._pbar.set(progress)
            self._status.configure(text=text)
        self.after(0, _update)

    def _desinstalar(self):
        try:
            self._set(0.10, "Cerrando aplicaciones...")
            matar_procesos_neuromood(self._install_dir)
            time.sleep(1.5)

            self._set(0.25, "Eliminando accesos directos...")
            eliminar_accesos()

            self._set(0.45, "Limpiando registro de Windows...")
            eliminar_registro_windows()

            self._set(0.60, "Cerrando Explorer...")
            cerrar_explorer_en(self._install_dir)
            time.sleep(0.5)

            appdata_nm = str(Path(os.environ.get("APPDATA", "")) / "NeuroMood")

            self._set(0.75, "Eliminando archivos de instalación...")
            vaciar_carpeta(self._install_dir)

            if not self._conservar:
                self._set(0.85, "Eliminando datos de usuario...")
                vaciar_carpeta(appdata_nm)

            self._set(0.90, "Finalizando...")
            lanzar_bat_limpieza(self._install_dir, appdata_nm, eliminar_appdata=not self._conservar)

            self._set(1.0, "¡Desinstalación completada!")
            time.sleep(1.0)
            os._exit(0)

        except Exception as e:
            self._set(0, f"Error: {e}")


if __name__ == "__main__":
    if relanzar_desde_temp():
        sys.exit(0)
    app = DesinstaladorNeuroMood()
    app.mainloop()
