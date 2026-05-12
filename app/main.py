"""main.py — NeuroMood Plataforma Unificada (entry point paciente)."""
import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
from shared.theme import COLORS, TYPOGRAPHY
from shared.components import ThemeManager, aplicar_captionbar
from shared.db import inicializar_tablas
from shared.identidad import obtener_nombre_paciente

from app.home import HomeView
from app import avisos_daemon


class NeuroMoodApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self._modo = "dark_hybrid"
        self.tm = ThemeManager(self, self._modo)

        inicializar_tablas()
        nombre = obtener_nombre_paciente() or "Paciente"

        # Sincronizar con Supabase al abrir (en background, no bloquea)
        self.after(500, self._sync_background)

        self.title(f"NeuroMood — Hola, {nombre}")
        self.geometry("820x620")
        self.minsize(500, 500)
        c = COLORS[self._modo]
        self.configure(fg_color=c["bg_primary"])

        self._center_window(820, 620)
        self._apply_icon()
        self.after(100, lambda: aplicar_captionbar(self, self._modo))

        self._current_module = None
        self._build_header(nombre, c)
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(fill="both", expand=True)

        self._home = HomeView(
            self._container, self._modo,
            on_module_open=self._open_module,
            get_status_fn=self._get_module_status,
        )
        self._home.pack(fill="both", expand=True)

        # Iniciar daemon de avisos en background
        self._avisos_stop = avisos_daemon.iniciar(on_abrir_app=self._restaurar_ventana)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _apply_icon(self):
        try:
            icon_path = os.path.join(_base, "NM_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

    def _build_header(self, nombre, c):
        header = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=48, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text=f"NeuroMood — Hola, {nombre}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=c["text_primary"],
        ).pack(side="left", padx=16, pady=8)

        self._theme_btn = ctk.CTkButton(
            header, text="☀", width=36, height=36,
            fg_color="transparent", hover_color=c["bg_surface"],
            text_color=c["text_secondary"],
            font=(TYPOGRAPHY["font_family"], 16),
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="right", padx=12, pady=6)

    def _toggle_theme(self):
        if "dark" in self._modo:
            self._modo = "light_hybrid"
            ctk.set_appearance_mode("light")
            self._theme_btn.configure(text="☾")
        else:
            self._modo = "dark_hybrid"
            ctk.set_appearance_mode("dark")
            self._theme_btn.configure(text="☀")

        c = COLORS[self._modo]
        self.configure(fg_color=c["bg_primary"])
        self.tm.switch_mode(self._modo)
        self._home.set_modo(self._modo)
        self.after(50, lambda: aplicar_captionbar(self, self._modo))

    def _open_module(self, module_id: str):
        module_map = {
            "animo": ("app.modules.animo", "ModuloAnimo"),
            "respiracion": ("app.modules.respiracion", "ModuloRespiracion"),
            "registro": ("app.modules.registro_tcc", "ModuloRegistroTCC"),
            "rutina": ("app.modules.rutina", "ModuloRutina"),
            "actividades": ("app.modules.actividades", "ModuloActividades"),
            "timer": ("app.modules.timer", "ModuloTimer"),
            "avisos": ("app.modules.avisos", "ModuloAvisos"),
        }
        if module_id not in module_map:
            return

        mod_path, cls_name = module_map[module_id]
        try:
            import importlib
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name)
        except (ImportError, AttributeError) as e:
            from shared.components import mostrar_mensaje
            mostrar_mensaje(self, "Módulo no disponible",
                           f"El módulo '{module_id}' aún no está implementado.\n{e}",
                           tipo="info", modo=self._modo)
            return

        self._home.pack_forget()
        self._current_module = cls(
            self._container, self._modo, self.tm,
            on_back=self._back_to_home,
        )
        self._current_module.pack(fill="both", expand=True)
        self._current_module.on_enter()

    def _back_to_home(self):
        if self._current_module:
            self._current_module.on_leave()
            self._current_module.destroy()
            self._current_module = None
        self._home.pack(fill="both", expand=True)
        self._home.refresh_statuses()

    def _sync_background(self):
        try:
            from shared.sync import sync_al_abrir
            import threading
            threading.Thread(target=sync_al_abrir, daemon=True).start()
        except Exception:
            pass

    def _on_close(self):
        """Al cerrar la ventana, minimiza a bandeja si hay avisos activos."""
        try:
            from shared.db import obtener_conexion
            conn = obtener_conexion()
            n = conn.execute("SELECT COUNT(*) FROM recordatorios WHERE activo=1").fetchone()[0]
            conn.close()
        except Exception:
            n = 0
        if n > 0 and avisos_daemon._PYSTRAY_OK:
            self.withdraw()  # Ocultar en vez de cerrar
        else:
            avisos_daemon.detener()
            self.destroy()

    def _restaurar_ventana(self):
        """Trae la ventana al frente desde la bandeja."""
        self.deiconify()
        self.lift()
        self.focus_force()

    def _get_module_status(self, module_id: str) -> str:
        try:
            from shared.db import obtener_conexion
            from shared.utils import fecha_hoy
            conn = obtener_conexion()
            hoy = fecha_hoy()
            result = ""
            if module_id == "animo":
                row = conn.execute(
                    "SELECT puntaje FROM termometro WHERE fecha=? ORDER BY hora DESC LIMIT 1", (hoy,)
                ).fetchone()
                result = f"{row[0]}/10 ✔" if row else ""
            elif module_id == "respiracion":
                n = conn.execute(
                    "SELECT COUNT(*) FROM respiracion WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} sesión{'es' if n>1 else ''} ✔" if n else ""
            elif module_id == "registro":
                n = conn.execute(
                    "SELECT COUNT(*) FROM pensamientos WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} registro{'s' if n>1 else ''} ✔" if n else ""
            elif module_id == "rutina":
                total = conn.execute("SELECT COUNT(*) FROM checklist_tareas").fetchone()[0]
                done = conn.execute(
                    "SELECT COUNT(*) FROM checklist_completadas WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{done}/{total} ✔" if total else ""
            elif module_id == "actividades":
                n = conn.execute(
                    "SELECT COUNT(*) FROM activacion WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} actividad{'es' if n>1 else ''} ✔" if n else ""
            elif module_id == "timer":
                n = conn.execute(
                    "SELECT COUNT(*) FROM actividades_temporizador WHERE fecha=?", (hoy,)
                ).fetchone()[0]
                result = f"{n} sesión{'es' if n>1 else ''} ✔" if n else ""
            elif module_id == "avisos":
                n = conn.execute(
                    "SELECT COUNT(*) FROM recordatorios WHERE activo=1"
                ).fetchone()[0]
                result = f"{n} activo{'s' if n>1 else ''}" if n else ""
            conn.close()
            return result
        except Exception:
            pass
        return ""


def main():
    app = NeuroMoodApp()
    app.mainloop()


if __name__ == "__main__":
    main()
