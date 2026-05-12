"""avisos_daemon.py — Daemon de recordatorios en bandeja del sistema.

Corre en un hilo daemon dentro del proceso de la app principal.
Revisa la tabla 'recordatorios' cada 30 segundos y dispara notificaciones
del sistema operativo cuando llega la hora configurada.
También ofrece un ícono en la bandeja con menú básico.
"""
import threading
import time
import datetime
import os
import sys

# Importación robusta para frozen / dev
if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base not in sys.path:
    sys.path.insert(0, _base)

try:
    import pystray
    from PIL import Image as PILImage
    _PYSTRAY_OK = True
except ImportError:
    _PYSTRAY_OK = False

try:
    from winotify import Notification, audio
    _WINOTIFY_OK = True
except ImportError:
    _WINOTIFY_OK = False

from shared.db import obtener_conexion

# Intervalo de revisión en segundos
_INTERVALO = 30

# Registro de notificaciones ya disparadas hoy: set de "HH:MM|rec_id"
_disparados: set = set()
_lock = threading.Lock()

# Referencia al ícono de bandeja (para poder detenerlo desde fuera)
_tray_icon = None


# ── Notificación ─────────────────────────────────────────────────────────────

def _notificar(mensaje: str, hora: str):
    """Muestra una notificación del sistema operativo."""
    # Intento 1: winotify (notificación nativa Windows 10/11)
    if _WINOTIFY_OK:
        try:
            toast = Notification(
                app_id="NeuroMood",
                title=f"⏰  Aviso — {hora}",
                msg=mensaje,
                duration="short",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            return
        except Exception:
            pass

    # Intento 2: plyer (cross-platform)
    try:
        from plyer import notification as plyer_notif
        plyer_notif.notify(
            title=f"NeuroMood — {hora}",
            message=mensaje,
            app_name="NeuroMood",
            timeout=8,
        )
        return
    except Exception:
        pass

    # Fallback: winsound beep
    try:
        import winsound
        winsound.Beep(880, 400)
    except Exception:
        pass


# ── Comprobación periódica ────────────────────────────────────────────────────

def _dia_actual_num() -> int:
    """Devuelve el número de día de la semana (1=Lunes … 7=Domingo)."""
    return datetime.datetime.now().weekday() + 1


def _hora_actual_str() -> str:
    now = datetime.datetime.now()
    return f"{now.hour:02d}:{now.minute:02d}"


def _en_silencio() -> bool:
    """Devuelve True si el horario actual está dentro del rango de silencio configurado."""
    try:
        conn = obtener_conexion()
        inicio = conn.execute(
            "SELECT valor FROM config WHERE clave='silencio_inicio'"
        ).fetchone()
        fin = conn.execute(
            "SELECT valor FROM config WHERE clave='silencio_fin'"
        ).fetchone()
        conn.close()
        if not inicio or not fin:
            return False
        hora_now = _hora_actual_str()
        h_ini = inicio[0] if isinstance(inicio, tuple) else inicio["valor"]
        h_fin = fin[0] if isinstance(fin, tuple) else fin["valor"]
        if h_ini <= h_fin:
            return h_ini <= hora_now < h_fin
        else:  # cruza medianoche
            return hora_now >= h_ini or hora_now < h_fin
    except Exception:
        return False


def _revisar():
    """Comprueba recordatorios y dispara los que correspondan."""
    if _en_silencio():
        return

    hora_now = _hora_actual_str()
    dia_now = _dia_actual_num()

    # Limpiar claves de días anteriores para evitar memory leak acumulativo
    hoy = datetime.date.today().isoformat()
    with _lock:
        stale = {c for c in _disparados if not c.startswith(hoy)}
        _disparados.difference_update(stale)

    try:
        conn = obtener_conexion()
        rows = conn.execute(
            "SELECT id, hora, mensaje, dias FROM recordatorios WHERE activo = 1"
        ).fetchall()
        conn.close()
    except Exception:
        return

    for row in rows:
        rec_id = row["id"] if hasattr(row, "keys") else row[0]
        hora = row["hora"] if hasattr(row, "keys") else row[1]
        mensaje = row["mensaje"] if hasattr(row, "keys") else row[2]
        dias_str = row["dias"] if hasattr(row, "keys") else row[3]

        if hora != hora_now:
            continue

        dias_activos = set((dias_str or "1,2,3,4,5,6,7").split(","))
        if str(dia_now) not in dias_activos:
            continue

        # Construir clave y verificar dentro del lock (elimina TOCTOU)
        with _lock:
            clave = f"{hoy}|{rec_id}|{hora}"
            if clave in _disparados:
                continue
            _disparados.add(clave)

        _notificar(mensaje, hora)
        _registrar_log(rec_id, hora, mensaje)


def _registrar_log(rec_id: int, hora: str, mensaje: str):
    """Guarda en DB que este recordatorio fue disparado."""
    try:
        import datetime as dt
        conn = obtener_conexion()
        conn.execute(
            "INSERT OR IGNORE INTO recordatorios_log (recordatorio_id, fecha, hora, mensaje) "
            "VALUES (?, ?, ?, ?)",
            (rec_id, dt.date.today().isoformat(), hora, mensaje),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _loop_revisar(stop_event: threading.Event):
    """Bucle principal del daemon: revisa cada _INTERVALO segundos."""
    while not stop_event.is_set():
        _revisar()
        stop_event.wait(_INTERVALO)


# ── Bandeja del sistema ───────────────────────────────────────────────────────

def _crear_icono_imagen() -> "PILImage.Image":
    """Devuelve la imagen del ícono. Usa NM_icon si existe, sino genera uno simple."""
    icon_path = os.path.join(_base, "NM_icon.ico")
    if os.path.exists(icon_path):
        try:
            return PILImage.open(icon_path).resize((64, 64))
        except Exception:
            pass
    # Ícono generado (círculo teal sobre fondo oscuro)
    img = PILImage.new("RGBA", (64, 64), (5, 9, 17, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=(0, 212, 200, 255))
    draw.ellipse((20, 20, 44, 44), fill=(5, 9, 17, 255))
    return img


def iniciar_bandeja(stop_event: threading.Event, on_abrir_app=None):
    """Inicia el ícono de bandeja en un hilo separado. No bloqueante."""
    if not _PYSTRAY_OK:
        return

    def _abrir():
        if on_abrir_app:
            on_abrir_app()

    def _salir(icon, item):
        stop_event.set()
        icon.stop()

    def _toggle_inicio(icon, item):
        _set_autostart(not _get_autostart())

    menu_items = []
    if on_abrir_app:
        menu_items.append(pystray.MenuItem("Abrir NeuroMood", _abrir, default=True))
    menu_items.append(pystray.MenuItem(
        "Iniciar con Windows",
        _toggle_inicio,
        checked=lambda item: _get_autostart(),
    ))
    menu_items.append(pystray.Menu.SEPARATOR)
    menu_items.append(pystray.MenuItem("Salir", _salir))

    global _tray_icon
    _tray_icon = pystray.Icon(
        "neuromood_avisos",
        icon=_crear_icono_imagen(),
        title="NeuroMood — Avisos activos",
        menu=pystray.Menu(*menu_items),
    )

    hilo = threading.Thread(target=_tray_icon.run, daemon=True, name="NM-Tray")
    hilo.start()


def detener_bandeja():
    global _tray_icon
    if _tray_icon:
        try:
            _tray_icon.stop()
        except Exception:
            pass
        _tray_icon = None


# ── Arranque con Windows ──────────────────────────────────────────────────────

def _get_autostart() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        )
        winreg.QueryValueEx(key, "NeuroMood")
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def _set_autostart(activar: bool):
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        if activar:
            exe = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
            winreg.SetValueEx(key, "NeuroMood", 0, winreg.REG_SZ, f'"{exe}"')
        else:
            try:
                winreg.DeleteValue(key, "NeuroMood")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass


# ── API pública ───────────────────────────────────────────────────────────────

_stop_event: threading.Event = None


def iniciar(on_abrir_app=None) -> threading.Event:
    """Inicia el daemon de avisos. Devuelve el stop_event para detenerlo."""
    global _stop_event
    _stop_event = threading.Event()

    # Hilo revisor
    hilo = threading.Thread(
        target=_loop_revisar,
        args=(_stop_event,),
        daemon=True,
        name="NM-AvisosDaemon",
    )
    hilo.start()

    # Bandeja del sistema
    iniciar_bandeja(_stop_event, on_abrir_app=on_abrir_app)

    return _stop_event


def detener():
    global _stop_event
    if _stop_event:
        _stop_event.set()
    detener_bandeja()
