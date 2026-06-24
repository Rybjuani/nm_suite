"""qa/visual_sentinel.py — Auditor visual canonico, independiente y autodescubrible.

Visual Sentinel es un auditor visual GLOBAL, independiente, autodescubrible y
reutilizable para un repo dinamico. No depende de qa/capture_v8.py ni de
qa/runtime_live_probe.py (no los importa ni reusa su lista manual de pantallas),
ni de listas hardcodeadas de pantallas problematicas actuales. Tampoco tiene
reglas tipo "revisa esta pantalla especifica" o "busca este bug concreto": esas
sesgan auditorias futuras y quedan obsoletas rapido.

Como descubre la UI
-------------------
El Sentinel construye un **grafo de estados** caminando la UI real de Suite y
Hub por introspeccion Qt, SIN recetas manuales:

- top-level windows (QApplication.topLevelWidgets);
- QStackedWidget (incluido NMFadeWidget, que hereda de QStackedWidget):
  se identifica la superficie activa via currentWidget() de forma generica;
- QTabWidget / QTabBar / NMTabs / NMSegmentedPanel / NMPanelTabs (tabs y stack
  indexes);
- botones clickeables seguros (QPushButton, QToolButton, QCheckBox, NMButton,
  NMButtonOutline, NMPlayButton, NMCustomCheck, NMCard, NMModule);
- dialogs/modals (QDialog, NMDialog) detectados como sub-estados;
- checkboxes/toggles que cambian el estado (running/paused/completed/filtered).

El crawler es un BFS/DFS generico: en cada estado enumera "acciones seguras",
aplica cada una sobre una ventana fresca (replay del path de acciones), captura
el estado resultante y lo dedupe por hash estructural + visual (phash). Si el
hash cambia, es un nodo nuevo del grafo; si no, es un duplicado/salto y se
registra como edge skipeado. Asi descubre estados dinamicos (multi-step, tabs,
dialogs, toggles) aunque cambien nombres o cantidades de pantallas.

Las acciones se describen como ``locators`` serializables (tipo + objectName +
texto + indice), no como referencias a widgets: eso permite re-aplicarlas en
ventanas frescas y hace el crawler independiente de la identidad del widget.

Honestidad por diseno
---------------------
- ``audit --all`` es el UNICO modo que puede emitir resultado general.
- ``capture``/``inspect --screen`` nunca imprimen PASS general: marcan
  TARGETED_INSPECTION_ONLY y GENERAL_AUDIT_NOT_RUN, y no contaminan el resultado
  global.
- Una pantalla nueva se marca NEW_STATE_UNREVIEWED y bloquea el cierre general
  hasta revision humana. El Sentinel NUNCA autoaprueba.
- El cierre general es FAIL si hay NEW_STATE_UNREVIEWED, STALE_STATE,
  MISSING_EVIDENCE, FALLBACK, DUPLICATE_SUSPECT, P0 o P1 (con ``--strict``,
  tambien P2).

Dependencias (ya en el venv): PyQt6, Pillow, numpy, scikit-image, imagehash,
PyYAML, rich, networkx. No usa cv2, jinja2, torch ni lpips.

Uso:
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py --list
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py audit --all --theme both
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py audit --all --theme both --strict
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py audit --app suite --theme light
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py capture --screen <id> --theme both
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py inspect --screen <id> --theme light
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py propose-baselines
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py approve-baseline --screen <id> --theme <theme>

Salida: qa/_visual_sentinel/latest/{manifest,coverage,coverage_matrix,
ui_state_graph,findings,index.html, screenshots/, widget_trees/, crops/,
contact_sheets/, logs/}
"""

from __future__ import annotations

import argparse
import datetime
import gc
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import tempfile
import time
import traceback
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

_PROJ = Path(__file__).resolve().parent.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

# --- Aislamiento QA: datos demo + DB temporal --------------------------------
# QT_QPA_PLATFORM se configura en _configure_platform() / main() para usar
# la plataforma nativa en Windows (evita render tofu/cuadrados en offscreen).
os.environ.setdefault("NM_VISUAL_QA", "1")
os.environ.setdefault("NM_VISUAL_QA_NAME", "Juan Cruz")

# Salida de consola tolerante a Unicode en consolas Windows (cp1252): los textos
# visibles de la app contienen acentos/simbolos (▲, ✓, etc.).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

_CONTRACTS_DIR = _PROJ / "qa" / "visual_sentinel_contracts"
_OUT_ROOT = _PROJ / "qa" / "_visual_sentinel"
_BASELINES_ROOT = _PROJ / "qa" / "visual_sentinel_baselines"
_APPROVED_DIR = _BASELINES_ROOT / "approved"
_PROPOSED_DIR = _BASELINES_ROOT / "proposed"
_REGISTRY_PATH = _BASELINES_ROOT / "registry.json"

_RESOLUTION = "960x600"
_BLOCKING_FLAGS = {
    "NEW_STATE_UNREVIEWED", "STALE_STATE", "MISSING_EVIDENCE",
    "FALLBACK", "DUPLICATE_SUSPECT",
}

# Umbrales de contenido (PNG casi todo blanco/negro o sin varianza tonal).
_BLANK_MEAN_HI = 0.985
_BLANK_MEAN_LO = 0.015
_FLAT_STDDEV = 0.004
_DUP_PHASH_DISTANCE = 5
_OVERLAP_MIN_RATIO = 0.45

_FONT_DIAG_CACHE: dict | None = None

# Timer global (uno por proceso) que neutraliza modales nativos bloqueantes.
_MODAL_GUARD_TIMER = None

# Flag: stubs de dialogos nativos del OS ya instalados (idempotente).
_DIALOG_STUBS_DONE = False

# Watchdog: si una sola operacion del crawl no progresa en este tiempo, se aborta
# el proceso (red de seguridad dura contra cuelgues que escapen al modal guard).
_WATCHDOG_OP_TIMEOUT_SECS = 120.0

# Valores del argumento --platform que son conceptos del Sentinel, NO plugins Qt.
# Qt acepta: offscreen, windows, minimal (en Windows), xcb/cocoa en otros OS.
# 'native' y 'auto' nunca deben llegar a Qt como valor de QT_QPA_PLATFORM.
_INVALID_QT_PLATFORMS: frozenset[str] = frozenset({"native", "auto"})

# Caps del crawler (mode-dependientes).
_DEFAULT_MAX_STATES = 70
_DEFAULT_MAX_DEPTH = 4
_DEFAULT_MAX_BRANCH = 12
_STRICT_MAX_STATES = 130
_STRICT_MAX_DEPTH = 6

# Presupuesto de tiempo por (app, theme) — RED DE SEGURIDAD anti-cuelgue, no un
# limite operativo. Un crawl sano de ~70 estados con WA_DontShowOnScreen y sin
# disparar red termina en 1-3 min; el budget solo se alcanza si algo se cuelga
# patologicamente (red, modal que no cierra, loop de layout). Si se alcanza, el
# crawl corta limpio y emite CRAWL_TRUNCATED (FAIL honesto: cobertura parcial).
# Override por entorno NM_SENTINEL_TIME_BUDGET (segundos) para auditorias rapidas.
_DEFAULT_TIME_BUDGET_SECS = 300
_STRICT_TIME_BUDGET_SECS = 540

# Palabras que indican acciones destructivas/inseguras (filtro generico por
# semantica del control, no por pantalla). Se omiten y se loguean.
_UNSAFE_TEXT_KEYS = (
    "salir", "eliminar", "borrar", "quitar", "desvincular", "unlink",
    "delete", "remove", "logout", "cerrar sesion", "cerrar sesión",
    "cancelar cuenta", "reset total",
)
# Acciones de bajo valor visual que vuelven un control a su default: NO aportan
# un estado nuevo (el default ya se captura) y, cuando hay decenas de campos
# editables (config de textos globales), generan una explosion combinatoria que
# hunde el presupuesto del crawler en una sola rama y deja pantallas reales sin
# cubrir. Se omiten para repartir el presupuesto entre superficies distintas.
_RESET_TEXT_KEYS = ("restablecer", "restaurar", "reset")
# Controles de chrome / navegacion back que no aportan estados nuevos y gastan
# presupuesto: se omiten (no son destructivos, solo redundantes).
_CHROME_OBJECTNAMES = ("NMWindowChrome", "NMThemeToggle", "NMBackButton",
                       "NMCloseButton", "NMMinButton")
# Mismos controles identificables por CLASE: los botones privados del titlebar
# (_ChromeWinBtn min/max/close, _ChromeThemeToggle, _ChromeLogoMark) y la barra
# NMWindowChrome NO exponen objectName, asi que el filtro por objectName solo no
# los atrapa. Match por subcadena case-insensitive sobre type(w).__name__.
_CHROME_CLASS_HINTS = (
    "chromewinbtn", "chromethemetoggle", "chromelogo",
    "windowchrome", "titlebar", "winbtn",
    "backbutton", "closebutton", "minbutton", "maxbutton",
)
_BACK_TEXT_KEYS = ("volver", "atras", " atrás", "←", "back")
# Botones que disparan operaciones de red/IA reales en hilos daemon: se omiten
# porque (a) el resultado es no deterministico, (b) el hilo puede sobrevivir al
# cierre de la ventana y congestionar el event loop (lo vimos colgar el crawl),
# (c) los estados intermedios dependen de datos externos no reproducibles.
# Match por substring sobre el texto normalizado del control.
_NETWORK_ASYNC_KEYS = (
    "exportar",        # Exportar PDF/informe (async, abre dialogo de archivo)
    "generar",         # "Generar resumen", "Generando..."
    "completar con",   # "Completar con IA"
    "sincronizar",     # sync remoto
)
# Siglas/tokens aislados que siempre implican una llamada a IA (red). Se chequean
# como TOKEN (palabra completa), no substring, para no atrapar "guia"/"dia"/
# "familia". Cubre "Resumen IA", "Completar con IA", "Sugerir con I.A.", etc.
_NETWORK_ASYNC_TOKENS = ("ia", "i.a.", "ai")


# ═══════════════════════════════════════════════════════════════════════════
# Utilidades genericas
# ═══════════════════════════════════════════════════════════════════════════

def _norm_text(value: Any) -> str:
    folded = unicodedata.normalize("NFKD", str(value or ""))
    asciiish = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(asciiish.casefold().split())


def _short_theme(modo: str) -> str:
    return "light" if "light" in (modo or "") else "dark"


def _theme_map(theme: str) -> list[str]:
    if theme == "both":
        return ["light_hybrid", "dark_hybrid"]
    if theme == "light":
        return ["light_hybrid"]
    if theme == "dark":
        return ["dark_hybrid"]
    raise SystemExit(f"--theme invalido: {theme}")


def _safe_name(screen_id: str) -> str:
    """Convierte un screen_id en un nombre de archivo valido en Windows."""
    return screen_id.replace(":", "__").replace("/", "_").replace("\\", "_")


def _parse_res(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def _sanitize_label(s: str) -> str:
    s = _norm_text(s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:32] or "state"


def _git_value(args: list[str]) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=_PROJ, capture_output=True,
                              text=True, timeout=5, check=False)
    except Exception:
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _git_metadata() -> dict[str, Any]:
    tracked = _git_value(["status", "--short", "--untracked-files=no"])
    return {
        "head": _git_value(["rev-parse", "HEAD"]),
        "short_head": _git_value(["rev-parse", "--short", "HEAD"]),
        "branch": _git_value(["branch", "--show-current"]),
        "tracked_dirty": bool(tracked),
        "tracked_status": tracked.splitlines() if tracked else [],
    }


def _sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _drain(qapp, cycles: int = 8, pause: float = 0.025) -> None:
    from PyQt6.QtCore import QCoreApplication, QEvent
    if qapp is None:
        return
    for _ in range(cycles):
        qapp.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        time.sleep(pause)
        qapp.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _close_active_modals() -> None:
    """Cierra/rechaza cualquier modal NATIVO bloqueante actualmente activo.

    Cubre QDialog/QMessageBox/QFileDialog (activeModalWidget) y menus emergentes
    (activePopupWidget). Rechaza (NO acepta): cancelar es la opcion segura ante
    un dialog de confirmacion destructiva. Los NMDialog del producto son overlays
    no-modales y NO se tocan: el crawler los captura como sub-estados normales.
    """
    try:
        from PyQt6.QtWidgets import QApplication, QDialog
    except Exception:
        return
    try:
        for _ in range(5):
            w = QApplication.activeModalWidget()
            if w is None:
                break
            try:
                if isinstance(w, QDialog):
                    w.reject()
                else:
                    w.close()
            except Exception:
                try:
                    w.close()
                except Exception:
                    break
        pop = QApplication.activePopupWidget()
        if pop is not None:
            try:
                pop.close()
            except Exception:
                pass
    except Exception:
        pass


def _install_dialog_stubs() -> None:
    """Neutraliza dialogos NATIVOS/bloqueantes del OS durante el crawl.

    A diferencia de QDialog/QMessageBox (widgets Qt que el modal guard puede
    cerrar), los selectores nativos de archivo/color/fuente y los QMenu.exec()
    arrancan un loop del shell de Windows que el guard Qt-side NO alcanza: un
    boton que los abra cuelga el crawler para siempre. Estos stubs hacen que
    retornen "cancelado/vacio" de inmediato (opcion SEGURA: no escriben archivos
    ni cambian settings). Corre en el proceso aislado del Sentinel: no afecta a
    la app real del owner. Idempotente."""
    global _DIALOG_STUBS_DONE
    if _DIALOG_STUBS_DONE:
        return
    try:
        from PyQt6.QtWidgets import (QFileDialog, QColorDialog, QFontDialog,
                                     QInputDialog, QMenu)
        from PyQt6.QtGui import QColor, QFont
    except Exception:
        return

    def _stub(retval):
        return staticmethod(lambda *a, **k: retval)

    for cls, name, ret in (
        (QFileDialog, "getOpenFileName", ("", "")),
        (QFileDialog, "getOpenFileNames", ([], "")),
        (QFileDialog, "getSaveFileName", ("", "")),
        (QFileDialog, "getExistingDirectory", ""),
        (QColorDialog, "getColor", QColor()),
        (QFontDialog, "getFont", (QFont(), False)),
        (QInputDialog, "getText", ("", False)),
        (QInputDialog, "getMultiLineText", ("", False)),
        (QInputDialog, "getInt", (0, False)),
        (QInputDialog, "getDouble", (0.0, False)),
        (QInputDialog, "getItem", ("", False)),
    ):
        try:
            setattr(cls, name, _stub(ret))
        except Exception:
            pass
    # QMenu.exec()/exec_() bloquean en un popup-loop nativo: stub a None.
    for name in ("exec", "exec_"):
        try:
            setattr(QMenu, name, lambda self, *a, **k: None)
        except Exception:
            pass
    _DIALOG_STUBS_DONE = True


def _install_modal_guard(qapp) -> None:
    """Instala (una vez por proceso) un QTimer que cierra modales nativos.

    Un boton que abre un QDialog.exec()/QMessageBox.exec() arranca un event-loop
    anidado que, en este crawler headless, NUNCA recibe el cierre del usuario y
    cuelga el proceso para siempre. El QTimer sigue disparandose DENTRO de ese
    loop anidado, asi que rompe el bloqueo cerrando el modal. Critico para un
    repo dinamico: cualquier dialog nuevo queda neutralizado sin tocar el producto.
    """
    global _MODAL_GUARD_TIMER
    if _MODAL_GUARD_TIMER is not None:
        return
    try:
        from PyQt6.QtCore import QTimer
        t = QTimer()
        t.setInterval(500)
        t.timeout.connect(_close_active_modals)
        t.start()
        _MODAL_GUARD_TIMER = t
    except Exception:
        pass


class _Watchdog:
    """Aborta el proceso si una sola operacion del crawl no progresa en N seg.

    Red de seguridad DURA contra cuelgues que escapen al modal guard (deadlock
    en C++, red que ignora timeout, loop de layout). Un crawl sano patea el
    heartbeat en cada iteracion; si pasan >timeout sin latido, abortar con codigo
    != 0 es preferible a loopear para siempre. Corre en un thread daemon.
    """

    def __init__(self, op_timeout_s: float = _WATCHDOG_OP_TIMEOUT_SECS):
        self._timeout = float(op_timeout_s)
        self._last = time.monotonic()
        self._lock = threading.Lock()
        self._stopped = False
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="sentinel-watchdog")

    def start(self) -> "_Watchdog":
        self._thread.start()
        return self

    def beat(self) -> None:
        with self._lock:
            self._last = time.monotonic()

    def stop(self) -> None:
        self._stopped = True

    def _run(self) -> None:
        while not self._stopped:
            time.sleep(2.0)
            with self._lock:
                idle = time.monotonic() - self._last
            if not self._stopped and idle > self._timeout:
                print(f"[WATCHDOG] crawl sin progreso por {idle:.0f}s "
                      f"(> {self._timeout:.0f}s): abortando para no colgar. "
                      "Probable modal/operacion bloqueante no neutralizada.",
                      file=sys.stderr, flush=True)
                os._exit(75)


def _configure_platform(mode: str = "auto") -> None:
    """Configura QT_QPA_PLATFORM ANTES de crear QApplication.

    Debe llamarse desde main() antes de cualquier instanciacion Qt.

    IMPORTANTE: 'native' y 'auto' son modos del Sentinel, NO plugins Qt validos.
    En Windows el plugin nativo real se llama 'windows'. Esta funcion garantiza
    que QT_QPA_PLATFORM nunca contiene un valor invalido para Qt.

    mode="auto"      Windows sin CI → deja unset (Qt elige 'windows'/DirectWrite);
                     CI o Linux/Mac sin display → 'offscreen'.
    mode="native"    Deja unset siempre (Qt elige su backend nativo del OS).
    mode="offscreen" Fuerza 'offscreen' (headless, CI).
    """
    # Paso 1: sanear siempre. Si el entorno ya contiene un valor invalido para Qt
    # (heredado de un seteo anterior o de CI mal configurado), corregirlo primero.
    if os.environ.get("QT_QPA_PLATFORM") in _INVALID_QT_PLATFORMS:
        del os.environ["QT_QPA_PLATFORM"]

    # Paso 2: si ya hay un valor valido externo (conftest.py, CI...), solo se
    # sobreescribe cuando el modo lo pide explicitamente (offscreen).
    current = os.environ.get("QT_QPA_PLATFORM", "")

    if mode == "offscreen":
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        return

    if mode == "native":
        # 'native' no es plugin Qt: dejar unset para que Qt elija el backend del OS.
        # No sobreescribimos un valor externo valido ya presente.
        return

    # mode == "auto": si ya hay valor externo valido, respetarlo
    if current:
        return
    # Sin valor externo: Windows sin CI → nativo; resto → offscreen
    _ci = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "TF_BUILD",
           "BUILDKITE", "CIRCLECI", "TRAVIS")
    if sys.platform == "win32" and not any(os.environ.get(v) for v in _ci):
        return  # Windows sin CI → Qt elige 'windows' (DirectWrite)
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


def _font_diagnostics(qapp) -> dict:
    """Diagnostico de fuentes post-carga. Detecta render roto en offscreen/Windows.

    Resultado incluido en el manifest y usado por el guardrail FONT_RENDER_BROKEN.
    """
    from PyQt6.QtGui import QFontInfo, QFont, QFontMetrics

    try:
        platform = qapp.platformName()
    except Exception:
        platform = os.environ.get("QT_QPA_PLATFORM", "unknown")

    try:
        import shared.fonts as _sf
        sans = _sf.FONT_SANS
        serif = _sf.FONT_SERIF
        mono = _sf.FONT_MONO
        available = list(_sf._AVAILABLE_FAMILIES)
    except Exception as exc:
        sans = serif = mono = f"<error: {exc}>"
        available = []

    try:
        app_font = qapp.font()
        app_font_family = app_font.family()
        resolved_family = QFontInfo(app_font).family()
    except Exception:
        app_font_family = resolved_family = "<error>"

    # Verificar metricas de glyphs de strings clave del ADN visual
    test_strings = {
        "NeuroMood": "NeuroMood",
        "Ánimo": "Ánimo",          # Ánimo
        "Respiración": "Respiración",  # Respiración
    }
    glyph_ok: dict[str, bool] = {}
    metrics_broken = False
    try:
        fm = QFontMetrics(QFont(sans, 14))
        for name, text in test_strings.items():
            ok = all(fm.horizontalAdvance(ch) > 0 for ch in text)
            glyph_ok[name] = ok
            if not ok:
                metrics_broken = True
    except Exception as exc:
        glyph_ok = {"error": str(exc)}
        metrics_broken = True

    # En Windows + offscreen, Qt no usa DirectWrite y el render suele producir tofu
    on_windows_offscreen = sys.platform == "win32" and platform == "offscreen"
    font_render_suspect = metrics_broken or on_windows_offscreen

    warnings: list[str] = []
    if on_windows_offscreen:
        warnings.append(
            "Windows + offscreen: font render puede producir cuadrados/tofu. "
            "Use --platform native o --platform auto para capturas canonicas."
        )
    if metrics_broken:
        warnings.append(f"Metricas de glyphs rotas para familia '{sans}': {glyph_ok}")

    return {
        "platform": platform,
        "app_font_family": app_font_family,
        "app_font_resolved": resolved_family,
        "available_families": available,
        "sans": sans,
        "serif": serif,
        "mono": mono,
        "glyph_metrics_ok": glyph_ok,
        "font_render_suspect": font_render_suspect,
        "warnings": warnings,
    }


def _ensure_isolated_db() -> Path | None:
    if os.environ.get("NEUROMOOD_TEST_DB"):
        return Path(os.environ["NEUROMOOD_TEST_DB"])
    tmp = Path(tempfile.mkdtemp(prefix="nm_sentinel_db_"))
    db_file = tmp / "sentinel_nm_data.db"
    os.environ["NEUROMOOD_TEST_DB"] = str(db_file)
    try:
        from shared.db import inicializar_tablas
        inicializar_tablas()
    except Exception as exc:
        print(f"[SENTINEL] DB init fallback (no critico en QA): {exc}", file=sys.stderr)
    return db_file


def sip_deleted(obj) -> bool:
    try:
        from PyQt6 import sip
        return sip.isdeleted(obj)
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Modelo de datos
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class StateSpec:
    """Espec legible de un estado (compatibilidad / modo puntual)."""
    app: str
    surface: str
    substate: str = ""
    label: str = ""

    @property
    def screen_id(self) -> str:
        parts = [self.app, self.surface]
        if self.substate:
            parts.append(self.substate)
        return ":".join(parts)


@dataclass
class DiscoveredNode:
    """Nodo del grafo de estados descubierto por el crawler."""
    node_id: str
    screen_id: str
    app: str
    theme: str
    label: str
    path: list[dict] = field(default_factory=list)   # acciones (locators) desde root
    stop_reason: str = ""


@dataclass
class CapturedState:
    screen_id: str
    app: str
    theme: str
    label: str
    png_path: Path
    tree_path: Path
    sha256: str | None
    phash: str | None
    structural_hash: str
    visual_metrics: dict
    widget_tree: dict
    texts: list[str]
    clickable: list[dict]
    scrollbars: list[dict]
    tabs: list[dict]
    buttons: list[dict]
    crops: list[dict]
    geometry: dict
    error: str | None = None
    node_id: str = ""
    path: list[dict] = field(default_factory=list)
    stop_reason: str = ""
    interactive_total: int = 0


@dataclass
class Finding:
    contract_id: str
    severity: str
    flag: str
    screen_id: str
    theme: str
    message: str
    detail: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# Crawler generico: locators, enumeracion de acciones seguras, apply, replay
# ═══════════════════════════════════════════════════════════════════════════

def _widget_text(w) -> str:
    for attr in ("text",):
        try:
            val = getattr(w, attr)
            if callable(val):
                val = val()
            s = str(val)
            if s and s != type(w).__name__:
                return s
        except Exception:
            continue
    return ""


def _derive_label_text(w) -> str:
    """Texto distintivo para el label/locator de un control.

    Si el widget no tiene texto propio (tarjetas/tiles cuyo titulo vive en un
    QLabel hijo, p.ej. ModuleCard del Suite), usa el primer QLabel descendiente
    con texto. Critico para que cards hermanas NO colapsen al MISMO label (y por
    ende al dedupe): sin esto, 8 modulos del home quedan como 'act:modulecard' y
    solo se explora 1."""
    txt = _widget_text(w)
    if txt:
        return txt
    try:
        from PyQt6.QtWidgets import QLabel
        for child in w.findChildren(QLabel):
            try:
                if not child.isVisible():
                    continue
                ct = child.text()
            except Exception:
                continue
            if ct and ct.strip():
                return ct
    except Exception:
        pass
    return ""


def _reimplements_mouse(w) -> bool:
    """True si una clase de PRODUCTO (no del binding PyQt) reimplementa un handler
    de mouse (press/release).

    Heuristica generica y autodescubrible: un widget cuya clase override
    mousePressEvent/mouseReleaseEvent es interactivo aunque no sea un QPushButton
    ni exponga senal 'clicked' (p.ej. ModuleCard navega via mouseReleaseEvent).
    No depende de una lista de nombres de clase, asi sobrevive a un repo que
    cambia seguido.

    Se recorre el MRO IGNORANDO las clases de PyQt6: el binding expone un wrapper
    de metodo distinto por clase (QFrame.mouseReleaseEvent is not
    QWidget.mouseReleaseEvent) aunque no cambie el comportamiento, lo que daria
    falsos positivos para todo QFrame/QLabel. Solo cuenta un override definido en
    codigo de la app (su __dict__)."""
    try:
        for klass in type(w).__mro__:
            if getattr(klass, "__module__", "").startswith("PyQt6"):
                continue
            if ("mouseReleaseEvent" in klass.__dict__
                    or "mousePressEvent" in klass.__dict__):
                return True
    except Exception:
        pass
    return False


def _is_clickable(w) -> bool:
    from PyQt6.QtWidgets import (
        QPushButton, QToolButton, QCheckBox, QRadioButton, QCommandLinkButton,
        QLabel,
    )
    try:
        if isinstance(w, (QPushButton, QToolButton, QCheckBox, QRadioButton,
                          QCommandLinkButton)):
            return True
    except Exception:
        pass
    cls = type(w).__name__
    if cls in {"NMButton", "NMButtonOutline", "NMPlayButton", "NMSegmentedChoice",
               "NMCustomCheck", "NMModule", "NMCard", "NMPatientRowPremium"}:
        return True
    if hasattr(w, "clicked"):
        return True
    # Heuristica generica y autodescubrible: un control clickeable custom (card/
    # tile que navega via mouseReleaseEvent, sin senal 'clicked') combina DOS
    # senales: (a) su clase reimplementa un handler de mouse y (b) declara cursor
    # pointing-hand. La conjuncion distingue un ModuleCard real de un contenedor
    # de drag (NMShellContent/_ShellWidget: reimplementan mouse pero cursor
    # normal) y de un badge estatico (cursor normal). No usa nombres de clase.
    try:
        from PyQt6.QtCore import Qt
        if (_reimplements_mouse(w) and not isinstance(w, QLabel)
                and w.cursor().shape() == Qt.CursorShape.PointingHandCursor):
            return True
    except Exception:
        pass
    return False


def _widget_has_icon(w) -> bool:
    """Icono real: QIcon del boton, hijo NMIcon, o atributo _icon_name."""
    try:
        ic = w.icon()
        if ic is not None and not ic.isNull():
            return True
    except Exception:
        pass
    if getattr(w, "_icon_name", None):
        return True
    try:
        from shared.components import NMIcon
        if any(isinstance(c, NMIcon) for c in w.children()):
            return True
    except Exception:
        pass
    return False


def _widget_locator(widget, root) -> dict:
    """Locator serializable: type + objectName + text + indice de ocurrencia."""
    cls = type(widget).__name__
    obj = ""
    try:
        obj = widget.objectName() or ""
    except Exception:
        pass
    text = _widget_text(widget)
    # indice entre widgets del mismo (type, objectName, text)
    try:
        peers = [w for w in root.findChildren(type(widget))
                 if (w.objectName() or "") == obj and _widget_text(w) == text]
    except Exception:
        peers = [widget]
    idx = peers.index(widget) if widget in peers else 0
    return {"type": cls, "objectName": obj, "text": text[:60], "index": idx}


def _find_by_locator(root, locator: dict):
    """Resuelve un locator a un widget vivo. None si no se encuentra."""
    from PyQt6.QtWidgets import QWidget
    cls = locator.get("type")
    obj = locator.get("objectName", "")
    text = locator.get("text", "")
    idx = int(locator.get("index", 0))
    matches = []
    for w in root.findChildren(QWidget):
        if type(w).__name__ != cls:
            continue
        try:
            wobj = w.objectName() or ""
        except Exception:
            wobj = ""
        if wobj != obj:
            continue
        if text and _widget_text(w)[:60] != text:
            continue
        if not w.isVisible():
            continue
        matches.append(w)
    if 0 <= idx < len(matches):
        return matches[idx]
    if matches:
        return matches[0]
    return None


def _find_tab_containers(root):
    """Localiza contenedores de tabs visibles. Evita doble conteo QTabWidget/QTabBar."""
    from PyQt6.QtWidgets import QWidget, QTabBar, QTabWidget
    try:
        from shared.components import NMTabs
    except Exception:
        NMTabs = ()
    try:
        from shared.adaptive_layout_qt import NMSegmentedPanel, NMPanelTabs
    except Exception:
        NMSegmentedPanel = NMPanelTabs = ()  # type: ignore[assignment]

    raw: list[Any] = []
    seen = set()
    try:
        for w in root.findChildren(QWidget):
            if sip_deleted(w) or not w.isVisible():
                continue
            if isinstance(w, (QTabBar, QTabWidget, NMTabs, NMSegmentedPanel, NMPanelTabs)):
                if id(w) not in seen:
                    raw.append(w)
                    seen.add(id(w))
    except Exception:
        pass
    owned = set()
    for c in raw:
        if isinstance(c, QTabWidget):
            try:
                owned.add(id(c.tabBar()))
            except Exception:
                pass
    return [c for c in raw if id(c) not in owned]


def _tab_container_info(container) -> dict | None:
    from PyQt6.QtWidgets import QTabBar, QTabWidget
    kind = type(container).__name__
    labels: list[str] = []
    count = 0
    current = 0
    try:
        if isinstance(container, QTabBar):
            count = container.count()
            current = container.currentIndex()
            labels = [container.tabText(i) for i in range(count)]
        elif isinstance(container, QTabWidget):
            tb = container.tabBar()
            count = container.count()
            current = container.currentIndex()
            labels = [tb.tabText(i) for i in range(count)]
        else:
            lbls = getattr(container, "_labels", None)
            if lbls is None:
                btns = getattr(container, "_buttons", None) or []
                lbls = [str(b.text()) for b in btns if hasattr(b, "text")]
            count = len(lbls)
            current = int(getattr(container, "_current", 0) or 0)
            labels = [str(x) for x in lbls]
    except Exception:
        return None
    if count <= 0:
        return None
    return {"count": count, "current": current, "labels": labels, "kind": kind}


def _set_tab_index(container, index: int) -> None:
    from PyQt6.QtWidgets import QTabBar, QTabWidget
    try:
        if isinstance(container, QTabBar):
            container.setCurrentIndex(index)
        elif isinstance(container, QTabWidget):
            container.setCurrentIndex(index)
        elif hasattr(container, "set_current"):
            container.set_current(index)
        elif hasattr(container, "setCurrentIndex"):
            container.setCurrentIndex(index)
        else:
            btns = getattr(container, "_buttons", None) or []
            stack = getattr(container, "_stack", None)
            if index < len(btns) and hasattr(btns[index], "setChecked"):
                btns[index].setChecked(True)
            if stack is not None and hasattr(stack, "setCurrentIndex"):
                stack.setCurrentIndex(index)
    except Exception:
        pass


def _active_surface_label(root) -> str:
    """Etiqueta generica de la superficie activa: clase del currentWidget del
    QStackedWidget primario (el de mayor area visible). Generico (deriva de los
    tipos de la app, no de una lista de pantallas)."""
    from PyQt6.QtWidgets import QStackedWidget
    try:
        stacks = [s for s in root.findChildren(QStackedWidget)
                  if not sip_deleted(s) and s.isVisible()]
        if not stacks:
            return _sanitize_label(type(root).__name__)
        # stack con mayor area visible = primario
        def _area(s):
            g = s.geometry()
            return g.width() * g.height()
        primary = max(stacks, key=_area)
        cw = primary.currentWidget()
        name = type(cw).__name__ if cw is not None else type(root).__name__
        # CamelCase -> kebab: HomeView -> home-view, ModuloAnimo -> modulo-animo
        kebab = re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()
        return _sanitize_label(kebab) or "root"
    except Exception:
        return "root"


def _chrome_ancestor(widget) -> bool:
    """True si el widget vive dentro de un NMWindowChrome (barra de titulo custom).

    Cualquier control clickeable ahi es chrome (min/max/close/theme toggle/back),
    no un estado funcional del producto: se omite para no capturar ruido de
    titlebar ni generar explosion combinatoria (theme toggle cambia el hash).
    """
    try:
        p = widget.parent()
    except Exception:
        return False
    while p is not None:
        try:
            pcls = type(p).__name__.lower()
            try:
                pobj = (p.objectName() or "").lower()
            except Exception:
                pobj = ""
        except Exception:
            return False
        if "windowchrome" in pcls or "windowchrome" in pobj:
            return True
        try:
            p = p.parent()
        except Exception:
            return False
    return False


def _semantic_text(widget, text_norm: str) -> str:
    """Texto semantico del control para el filtro de seguridad: combina el texto
    visible con tooltip, accessibleName/Description y objectName (normalizados).

    Critico para botones-ICONO sin texto cuyo proposito (destructivo/red/back)
    solo vive en el tooltip o el objectName (p.ej. NMRowUnlink: text='' pero
    tooltip='Quitar paciente del Hub' y objectName contiene 'unlink'). Sin esto,
    el crawler los clickearia y dispararia su dialog/accion bloqueante."""
    parts = [text_norm]
    for getter in ("toolTip", "accessibleName", "accessibleDescription",
                   "objectName"):
        try:
            fn = getattr(widget, getter, None)
            if callable(fn):
                extra = _norm_text(fn())
                if extra:
                    parts.append(extra)
        except Exception:
            pass
    return " ".join(parts)


def _is_unsafe(widget, text_norm: str) -> str | None:
    """Razon de inseguridad o None si es segura. Filtro generico por semantica
    del control (texto/tooltip/accessible/objectName/clase/ancestro chrome), no
    por pantalla."""
    try:
        obj = (widget.objectName() or "").lower()
    except Exception:
        obj = ""
    if any(k in obj for k in (k.lower() for k in _CHROME_OBJECTNAMES)):
        return "chrome-control"
    cls = type(widget).__name__.lower()
    if any(k in cls for k in _CHROME_CLASS_HINTS):
        return "chrome-control"
    if _chrome_ancestor(widget):
        return "chrome-control"
    sem = _semantic_text(widget, text_norm)
    if any(k in sem for k in _UNSAFE_TEXT_KEYS):
        return "destructive-text"
    if any(k in sem for k in _RESET_TEXT_KEYS):
        return "reset-low-value"
    if any(k in sem for k in _BACK_TEXT_KEYS):
        return "navigation-back"
    if any(k in sem for k in _NETWORK_ASYNC_KEYS):
        return "async-network"
    if any(tok in _NETWORK_ASYNC_TOKENS for tok in sem.split()):
        return "async-network"
    return None


def _enumerate_safe_actions(root, path: list[dict], opts: dict, log_omitted=None
                            ) -> list[dict]:
    """Enumera acciones seguras en el estado actual. Generico: tabs + clicks.

    Devuelve acciones serializables {kind, locator, label}. La prevencion de
    loops NO se hace por locator-en-el-path (eso romperia flujos multi-step
    donde el MISMO boton "Siguiente" avanza por estados distintos): se hace por
    dedupe de hash de estado al materializar (crawl_app). Acciones omitidas se
    loguean via ``log_omitted``.
    """
    from PyQt6.QtWidgets import QWidget
    actions: list[dict] = []
    max_branch = opts.get("max_branch", _DEFAULT_MAX_BRANCH)

    # --- Tabs / segmentados / stack indexes ---
    try:
        for container in _find_tab_containers(root):
            info = _tab_container_info(container)
            if not info or info["count"] <= 1:
                continue
            for i in range(info["count"]):
                if i == info["current"]:
                    continue
                lbl = info["labels"][i] if i < len(info["labels"]) else str(i)
                action = {
                    "kind": "tab",
                    "locator": _widget_locator(container, root),
                    "index": i,
                    "label": "tab:" + _sanitize_label(lbl),
                }
                actions.append(action)
                if len(actions) >= max_branch:
                    break
            if len(actions) >= max_branch:
                break
    except Exception:
        pass

    # --- Clicks / toggles seguros ---
    # Dedupe por label DENTRO del estado: controles con el mismo (tipo+texto)
    # producen el mismo resultado visual; explorar repetidos solo quema
    # presupuesto y genera capturas/DUPLICATE_SUSPECT en cascada (el dedupe por
    # hash posterior los colapsaria igual, pero materializar cada uno es caro).
    # Colapsa p.ej. 20x "Restablecer por defecto" -> 1. El dedupe es inline para
    # que max_branch limite acciones DISTINTAS, no copias del mismo control.
    seen_click_labels: set[str] = set()
    try:
        for w in root.findChildren(QWidget):
            if len(actions) >= max_branch:
                break
            if sip_deleted(w) or not w.isVisible() or not w.isEnabled():
                continue
            if not _is_clickable(w):
                continue
            # Texto distintivo: incluye el de un QLabel hijo para cards sin texto
            # propio (asi el filtro de seguridad y el dedupe distinguen hermanas).
            text = _derive_label_text(w)
            tnorm = _norm_text(text)
            reason = _is_unsafe(w, tnorm)
            if reason is not None:
                if callable(log_omitted):
                    log_omitted({
                        "at": _active_surface_label(root),
                        "widget": type(w).__name__, "text": text[:40],
                        "reason": reason,
                    })
                continue
            try:
                g = w.geometry()
                if g.width() < 12 or g.height() < 12:
                    continue
            except Exception:
                pass
            label_src = text if text else type(w).__name__
            label = "act:" + _sanitize_label(label_src)
            if label in seen_click_labels:
                continue
            seen_click_labels.add(label)
            locator = _widget_locator(w, root)
            action = {
                "kind": "click",
                "locator": locator,
                "label": label,
            }
            actions.append(action)
    except Exception:
        pass
    return actions


def _apply_action(root, action: dict, qapp) -> bool:
    """Aplica una accion sobre el widget vivo. Devuelve True si aplico."""
    try:
        if action.get("kind") == "tab":
            container = _find_by_locator(root, action["locator"])
            if container is None:
                return False
            _set_tab_index(container, int(action.get("index", 0)))
            _drain(qapp, cycles=5)
            return True
        # click / toggle
        w = _find_by_locator(root, action["locator"])
        if w is None:
            return False
        clicked = False
        for method in ("click",):
            fn = getattr(w, method, None)
            if callable(fn):
                try:
                    fn()
                    clicked = True
                    break
                except Exception:
                    continue
        if not clicked:
            sig = getattr(w, "clicked", None)
            if sig is not None:
                try:
                    sig.emit()
                    clicked = True
                except Exception:
                    pass
        if not clicked and hasattr(w, "setChecked"):  # checkbox/toggle fallback
            try:
                w.setChecked(not w.isChecked())
                if hasattr(w, "toggled"):
                    w.toggled.emit(w.isChecked())
                clicked = True
            except Exception:
                pass
        if not clicked and _reimplements_mouse(w):
            # Fallback final: sintetizar press+release en el centro del widget.
            # Cubre cards/tiles que navegan via mouseReleaseEvent custom y no
            # exponen click()/clicked (p.ej. ModuleCard del Suite home).
            try:
                from PyQt6.QtCore import Qt, QPointF, QEvent
                from PyQt6.QtGui import QMouseEvent
                center = w.rect().center()
                gpos = w.mapToGlobal(center)
                lpos = QPointF(float(center.x()), float(center.y()))
                gposf = QPointF(float(gpos.x()), float(gpos.y()))
                for etype in (QEvent.Type.MouseButtonPress,
                              QEvent.Type.MouseButtonRelease):
                    ev = QMouseEvent(etype, lpos, gposf,
                                     Qt.MouseButton.LeftButton,
                                     Qt.MouseButton.LeftButton,
                                     Qt.KeyboardModifier.NoModifier)
                    qapp.sendEvent(w, ev)
                clicked = True
            except Exception:
                pass
        _drain(qapp, cycles=5)
        return clicked
    except Exception:
        return False


def _replay_path(root, path: list[dict], qapp) -> bool:
    """Re-aplica una secuencia de acciones (locators) sobre una raiz fresca."""
    for action in path:
        if not _apply_action(root, action, qapp):
            return False
    return True


# ═══════════════════════════════════════════════════════════════════════════
# Instanciacion de apps
# ═══════════════════════════════════════════════════════════════════════════

_APP_SPEC = {
    "suite": {"module": "app.main_qt", "class": "NeuroMoodApp", "settings": "Suite"},
    "hub": {"module": "hub.main_qt", "class": "NeuroMoodHub", "settings": "Hub"},
}


def _instantiate(app_key: str, modo: str, res: str = _RESOLUTION):
    import importlib
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QSize, QSettings

    # Pasar solo el nombre del ejecutable a QApplication: Qt parsea sys.argv
    # buscando --platform <plugin> y otros flags Qt-propios; si recibe
    # --platform auto/native buscaria plugins Qt inexistentes y falla.
    _safe_argv = [sys.argv[0] if sys.argv else "visual_sentinel"]
    qapp = QApplication.instance() or QApplication(_safe_argv)
    qapp.setQuitOnLastWindowClosed(False)
    _install_dialog_stubs()      # stubea file/color/menu nativos (cuelgan el crawl)
    _install_modal_guard(qapp)   # cierra QDialog/QMessageBox modales Qt-side
    try:
        from shared.fonts import load_fonts
        load_fonts()
    except Exception:
        pass
    global _FONT_DIAG_CACHE
    if _FONT_DIAG_CACHE is None:
        _FONT_DIAG_CACHE = _font_diagnostics(qapp)
        for _diag_warn in _FONT_DIAG_CACHE.get("warnings", []):
            print(f"[SENTINEL FONT] {_diag_warn}", file=sys.stderr)
    try:
        from shared.theme_qt import stylesheet_base, app_palette
        qapp.setPalette(app_palette(modo))
        qapp.setStyleSheet(stylesheet_base(modo))
    except Exception:
        pass

    spec = _APP_SPEC[app_key]
    QSettings("NeuroMood", spec["settings"]).setValue("ui/theme", modo)
    module = importlib.import_module(spec["module"])
    WindowClass = getattr(module, spec["class"])
    win = WindowClass()
    # No tapar la pantalla del owner ni robar foco: la ventana se "muestra"
    # logicamente (procesa show/polish/layout y renderiza con el backend nativo
    # de Windows = DirectWrite, sin tofu) pero NUNCA se mapea en el escritorio.
    # win.grab() funciona igual sobre el backing store. Critico para correr
    # auditorias mientras el owner usa la app real sin interrupciones.
    from PyQt6.QtCore import Qt
    win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    win.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
    win.show()
    if hasattr(win, "ensurePolished"):
        win.ensurePolished()
    _drain(qapp, cycles=10)
    w, h = _parse_res(res)
    try:
        win.setMinimumSize(QSize(0, 0))
        win.setMaximumSize(QSize(16777215, 16777215))
        win.setFixedSize(QSize(w, h))
        lay = win.layout()
        if lay:
            lay.activate()
    except Exception:
        pass
    _drain(qapp, cycles=6)
    return qapp, win


def _quiesce_widget(win) -> None:
    """Detiene todos los QTimer y QAbstractAnimation vivos de la ventana.

    Se usa (1) ANTES de capturar — congela la UI en un frame estatico: el grab()
    de un widget con una animacion activa (modulos animados como la Guia de
    Respiracion) puede provocar access violation, y ademas da capturas no
    deterministas (a media animacion); y (2) en el teardown — si un timer dispara
    despues de borrar la ventana, toca widgets C++ ya destruidos y crashea."""
    if win is None:
        return
    from PyQt6.QtCore import QTimer, QAbstractAnimation
    try:
        for t in win.findChildren(QTimer):
            try:
                t.stop()
            except Exception:
                pass
        for an in win.findChildren(QAbstractAnimation):
            try:
                an.stop()
            except Exception:
                pass
    except Exception:
        pass


def _close_window(win) -> None:
    """Cierra la ventana y libera a fondo los objetos C++ Qt.

    El crawler instancia una ventana fresca por nodo (decenas por crawl). Si el
    teardown no libera de verdad, los widgets/modales/popups huerfanos se acumulan
    entre instanciaciones y agotan handles GDI/memoria -> access violation. Por
    eso: (1) se detienen timers/animaciones de la ventana, (2) se cierran TODOS
    los top-levels (no solo los visibles: modales y popups ocultos tambien),
    (3) se procesa DeferredDelete a fondo y (4) se fuerza gc.collect()."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QCoreApplication, QEvent
    qapp = QApplication.instance()
    # Detener timers/animaciones vivos de la ventana: si disparan tras el teardown
    # tocan widgets ya borrados (causa tipica de crash en apps con NMFadeWidget).
    _quiesce_widget(win)
    try:
        if win is not None:
            win.close()
            win.deleteLater()
    except Exception:
        pass
    if qapp is not None:
        try:
            for tl in list(QApplication.topLevelWidgets()):
                if tl is win:
                    continue
                try:
                    tl.close()
                    tl.deleteLater()
                except Exception:
                    pass
        except Exception:
            pass
        # Procesar DeferredDelete a fondo para liberar los objetos C++ de verdad.
        for _ in range(6):
            qapp.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            qapp.processEvents()
        gc.collect()


# ═══════════════════════════════════════════════════════════════════════════
# Crawler de la app: BFS generico con fresh-window-per-node + replay
# ═══════════════════════════════════════════════════════════════════════════

def crawl_app(app_key: str, modo: str, opts: dict,
              out_dirs: dict, log=print) -> tuple[list[CapturedState], dict]:
    """Crawl generico de una app. Construye el grafo de estados descubriendo
    acciones seguras en vivo y replayandolas en ventanas frescas.

    Devuelve (estados_capturados, grafo). El grafo trae nodes/edges/omitted.
    """
    theme = _short_theme(modo)
    max_states = int(opts.get("max_states", _DEFAULT_MAX_STATES))
    max_depth = int(opts.get("max_depth", _DEFAULT_MAX_DEPTH))
    time_budget = float(opts.get("time_budget_secs", _DEFAULT_TIME_BUDGET_SECS))
    deadline = time.monotonic() + time_budget
    truncated_by_time = False

    nodes: list[CapturedState] = []
    edges: list[dict] = []
    omitted: list[dict] = []
    seen_sig: dict[str, str] = {}      # sig -> screen_id
    used_screen_ids: set[str] = set()

    def _log_omit(rec):
        omitted.append(rec)

    def _unique_screen_id(base: str) -> str:
        sid = base
        if sid in used_screen_ids:
            n = 2
            while f"{sid}~{n}" in used_screen_ids:
                n += 1
            sid = f"{sid}~{n}"
        used_screen_ids.add(sid)
        return sid

    def _materialize(path, parent_id, via):
        """Instancia una ventana fresca, replaya el path, captura el estado y
        (si no se alcanzo max_depth) enumera las acciones hijas EN LA MISMA
        ventana ya en el estado capturado. Devuelve (estado, acciones_hijas).

        Enumerar aqui — y no en una segunda instanciacion — evita re-instanciar
        y re-replayar cada nodo solo para listar sus hijos (~2x menos ventanas).
        Es seguro: _capture_state solo lee/graba (no muta la navegacion)."""
        nonlocal nodes
        qapp, win = _instantiate(app_key, modo)
        try:
            ok = _replay_path(win, path, qapp)
            if not ok:
                omitted.append({"at": "<replay>", "path_len": len(path),
                                "reason": "locator-no-resolvio"})
                return None, []
            # capturar
            surface = _active_surface_label(win)
            label_parts = [surface] + [a.get("label", "") for a in path]
            human = "/".join(p for p in label_parts if p).replace(":", "/")
            base_sid = f"{app_key}:{surface}"
            if len(path) == 0:
                sid = _unique_screen_ids_label(base_sid, used_screen_ids)
            else:
                # id legible: app:surface/act:.../tab:...
                tail = "/".join(a.get("label", "step") for a in path)
                sid = _unique_screen_ids_label(f"{app_key}:{surface}/{tail}",
                                               used_screen_ids)
            st = _capture_state(win, qapp, app_key, modo, out_dirs,
                                screen_id=sid, label=human, path=path)
            _persist_captured(st, out_dirs)
            sig = st.structural_hash + "|" + (st.phash or "")
            if sig in seen_sig:
                edges.append({"from": parent_id, "to": seen_sig[sig],
                              "via": via, "skipped": "duplicate"})
                return None, []
            st.node_id = sid
            seen_sig[sig] = sid
            nodes.append(st)
            if parent_id:
                edges.append({"from": parent_id, "to": sid, "via": via})
            # enumerar hijos en la misma ventana viva (estado == capturado)
            child_actions: list[dict] = []
            if len(path) < max_depth:
                child_actions = _enumerate_safe_actions(
                    win, path, opts, log_omitted=_log_omit)
            return st, child_actions
        finally:
            _close_window(win)

    # BFS por NIVELES (cola FIFO, pop del frente): cubre todas las superficies de
    # un nivel (p.ej. los 8 modulos del home) antes de profundizar. Para un repo
    # del que se quieren "todas las pantallas", la amplitud rinde mas cobertura
    # por segundo que hundirse en una rama (un DFS gastaria el presupuesto en los
    # sub-tabs del primer modulo y dejaria los demas modulos sin visitar).
    # Watchdog: aborta el proceso si una sola iteracion cuelga (red de seguridad
    # dura por encima del modal guard y del presupuesto de tiempo).
    watchdog = _Watchdog().start()
    frontier: list[tuple[list[dict], str, dict | None]] = [([], "", None)]
    try:
        while frontier and len(nodes) < max_states:
            watchdog.beat()
            if time.monotonic() > deadline:
                truncated_by_time = True
                log(f"  [TIME_BUDGET] {app_key}@{theme}: corte tras {len(nodes)} "
                    f"estados al alcanzar {time_budget:.0f}s (cobertura PARCIAL).")
                break
            path, parent_id, via = frontier.pop(0)
            if os.environ.get("NM_SENTINEL_TRACE"):
                _tail = "/".join(a.get("label", "?") for a in path) or "(root)"
                print(f"[TRACE] {app_key}@{theme} depth={len(path)} "
                      f"nodes={len(nodes)} -> {_tail}", file=sys.stderr, flush=True)
            node, child_actions = _materialize(path, parent_id, via)
            if node is None:
                continue
            if len(path) >= max_depth:
                node.stop_reason = "max_depth"
                continue
            # Dentro del nivel, primero los tabs/superficies y luego los botones:
            # si el presupuesto corta a mitad de nivel, se priorizo la cobertura
            # de superficies distintas sobre los controles de una sola pantalla.
            tabs = [a for a in child_actions if a.get("kind") == "tab"]
            clicks = [a for a in child_actions if a.get("kind") != "tab"]
            for action in tabs + clicks:
                child_path = path + [action]
                frontier.append((child_path, node.node_id, action))
            if len(frontier) > max_states * 6:
                # podamos conservando los caminos MENOS profundos (BFS: el proximo
                # nivel a cubrir) para no sacrificar amplitud de superficies.
                frontier.sort(key=lambda x: len(x[0]))
                frontier = frontier[:max_states * 3]
    finally:
        watchdog.stop()

    graph = {
        "app": app_key, "theme": theme,
        "nodes": [_node_summary(n) for n in nodes],
        "edges": edges,
        "omitted_actions": omitted,
        "crawl_opts": {"max_states": max_states, "max_depth": max_depth,
                       "time_budget_secs": time_budget},
        "discovered_count": len(nodes),
        "truncated_by_time": truncated_by_time,
        "frontier_remaining": len(frontier),
    }
    return nodes, graph


def _unique_screen_ids_label(base: str, used: set[str]) -> str:
    # recorta ids muy largos y los hace unicos
    base = base[:80]
    if base not in used:
        used.add(base)
        return base
    # si colisiona, anade corto hash del path
    short = hashlib.sha1(base.encode("utf-8")).hexdigest()[:6]
    cand = f"{base[:60]}~{short}"
    while cand in used:
        cand = f"{base[:60]}~{short}{len(used)}"
    used.add(cand)
    return cand


def _node_summary(n: CapturedState) -> dict:
    return {
        "node_id": n.node_id, "screen_id": n.screen_id, "app": n.app,
        "theme": n.theme, "label": n.label,
        "path": [a.get("label", "") for a in n.path],
        "structural_hash": n.structural_hash, "phash": n.phash,
        "sha256": n.sha256, "stop_reason": n.stop_reason,
        "error": n.error,
        "main_texts": (n.texts or [])[:6],
        "interactive_widgets": n.interactive_total,
        "png": str(n.png_path.relative_to(_PROJ)) if not n.error else None,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Captura de evidencia por estado
# ═══════════════════════════════════════════════════════════════════════════

def _capture_state(win, qapp, app_key: str, modo: str, out_dirs: dict,
                   screen_id: str, label: str, path: list[dict]) -> CapturedState:
    theme = _short_theme(modo)
    safe = _safe_name(screen_id)
    png_path = out_dirs["screenshots"] / f"{safe}-{theme}.png"
    tree_path = out_dirs["widget_trees"] / f"{safe}-{theme}.json"

    error: str | None = None
    try:
        if not win.isVisible():
            win.show()
        _drain(qapp, cycles=3)
        # Congelar animaciones/timers antes del grab: evita access violation al
        # capturar modulos animados y hace la captura determinista.
        _quiesce_widget(win)
        _drain(qapp, cycles=2)
        pm = win.grab()
        ok = pm.save(str(png_path))
        if not ok:
            error = "grab().save() devolvio False"
    except Exception as exc:
        error = f"{exc.__class__.__name__}: {exc}"

    sha256 = _sha256_file(png_path) if png_path.exists() else None
    phash = _compute_phash(png_path) if png_path.exists() else None
    metrics = _content_metrics(png_path)
    widget_tree = _build_widget_tree(win, win_ref=win)
    texts = _collect_texts(widget_tree)
    clickable = _collect_clickable(widget_tree)
    scrollbars = _collect_scrollbars(win)
    tabs = _collect_tabs(win)
    buttons = _collect_buttons(widget_tree)
    crops = _make_crops(win, qapp, clickable + scrollbars + tabs, safe, theme, out_dirs)
    geo = _window_geometry(win)
    structural_hash = _structural_hash(widget_tree)
    interactive_total = sum(1 for n in _walk_tree(widget_tree)
                            if n.get("visible") and n.get("clickable"))

    return CapturedState(
        screen_id=screen_id, app=app_key, theme=theme, label=label,
        png_path=png_path, tree_path=tree_path, sha256=sha256, phash=phash,
        structural_hash=structural_hash, visual_metrics=metrics,
        widget_tree=widget_tree, texts=texts, clickable=clickable,
        scrollbars=scrollbars, tabs=tabs, buttons=buttons, crops=crops,
        geometry=geo, error=error, path=path, interactive_total=interactive_total,
    )


def _compute_phash(path: Path) -> str | None:
    try:
        import imagehash
        from PIL import Image
        with Image.open(path) as img:
            return str(imagehash.phash(img.convert("RGB")))
    except Exception:
        return None


def _content_metrics(path: Path) -> dict:
    try:
        from PIL import Image, ImageStat
        with Image.open(path) as img:
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
        return {"gray_mean": round(stat.mean[0] / 255.0, 4),
                "gray_stddev": round(stat.stddev[0] / 255.0, 4)}
    except Exception as exc:
        return {"error": str(exc)}


def _build_widget_tree(root, depth: int = 0, max_depth: int = 11, win_ref=None,
                      in_scroll: bool = False, in_dialog: bool = False) -> dict:
    """Arbol Qt serializable.

    ``geometry`` es relativa al parent (Qt nativo). ``geo_win`` es la geometria
    mapeada a la coordenada de la ventana. ``in_scroll``/``in_dialog`` indican
    si el widget vive dentro de un QScrollArea / QDialog. ``has_icon`` indica
    presencia real de icono.
    """
    from PyQt6.QtWidgets import QWidget, QScrollArea, QDialog
    if sip_deleted(root) or depth > max_depth:
        return {"type": type(root).__name__, "truncated": True}

    is_scroll = isinstance(root, QScrollArea)
    is_dialog = isinstance(root, QDialog)
    child_in_scroll = in_scroll or is_scroll
    child_in_dialog = in_dialog or is_dialog

    def _rect(w):
        try:
            r = w.geometry()
            return {"x": r.x(), "y": r.y(), "w": r.width(), "h": r.height()}
        except Exception:
            return {}

    def _win_rect(w):
        if win_ref is None or sip_deleted(win_ref):
            return None
        try:
            from PyQt6.QtCore import QPoint
            r = w.geometry()
            tl = w.mapTo(win_ref, QPoint(0, 0))
            return {"x": tl.x(), "y": tl.y(), "w": r.width(), "h": r.height()}
        except Exception:
            return None

    node = {
        "type": type(root).__name__,
        "objectName": root.objectName() if hasattr(root, "objectName") else "",
        "text": _widget_text(root)[:200],
        "geometry": _rect(root),
        "geo_win": _win_rect(root),
        "visible": bool(root.isVisible()) if hasattr(root, "isVisible") else False,
        "enabled": bool(root.isEnabled()) if hasattr(root, "isEnabled") else True,
        "clickable": _is_clickable(root),
        "has_icon": _widget_has_icon(root),
        "in_scroll": in_scroll,
        "in_dialog": in_dialog,
        "children": [],
    }
    try:
        node["children"] = [_build_widget_tree(c, depth + 1, max_depth, win_ref,
                                                child_in_scroll, child_in_dialog)
                            for c in root.children() if isinstance(c, QWidget)
                            and not sip_deleted(c)]
    except Exception:
        pass
    return node


def _walk_tree(node: dict) -> Iterable[dict]:
    yield node
    for c in node.get("children", []) or []:
        yield from _walk_tree(c)


def _collect_texts(tree: dict) -> list[str]:
    return [(n.get("text") or "").strip()
            for n in _walk_tree(tree)
            if n.get("visible") and (n.get("text") or "").strip()]


def _collect_clickable(tree: dict) -> list[dict]:
    out = []
    for n in _walk_tree(tree):
        if n.get("visible") and n.get("clickable"):
            out.append({"type": n.get("type"), "text": n.get("text"),
                        "objectName": n.get("objectName"),
                        "geometry": n.get("geometry"), "has_icon": n.get("has_icon"),
                        "enabled": n.get("enabled")})
    return out


def _collect_scrollbars(root) -> list[dict]:
    from PyQt6.QtWidgets import QScrollBar, QScrollArea
    out = []
    try:
        for w in root.findChildren(QScrollBar):
            if sip_deleted(w) or not w.isVisible():
                continue
            try:
                bar = w.orientation()
                out.append({
                    "orientation": "vertical" if bar.name == "Vertical" else "horizontal",
                    "min": w.minimum(), "max": w.maximum(), "pageStep": w.pageStep(),
                    "visible_range": w.maximum() - w.minimum(),
                    "geometry": _geo_dict(w),
                })
            except Exception:
                continue
        for sa in root.findChildren(QScrollArea):
            if sip_deleted(sa) or not sa.isVisible():
                continue
            out.append({"type": "QScrollArea", "objectName": sa.objectName(),
                        "geometry": _geo_dict(sa)})
    except Exception:
        pass
    return out


def _collect_tabs(root) -> list[dict]:
    out = []
    for c in _find_tab_containers(root):
        info = _tab_container_info(c)
        if not info:
            continue
        rects = []
        try:
            from PyQt6.QtWidgets import QTabBar
            if isinstance(c, QTabBar):
                rects = [_geo_dict_rect(c.tabRect(i)) for i in range(info["count"])]
        except Exception:
            pass
        out.append({"type": info["kind"], "count": info["count"],
                    "current": info["current"], "labels": info["labels"],
                    "tabRects": rects, "geometry": _geo_dict(c)})
    return out


def _collect_buttons(tree: dict) -> list[dict]:
    out = []
    for n in _walk_tree(tree):
        cls = n.get("type", "")
        if n.get("visible") and ("Button" in cls or cls in {"NMPlayButton"}):
            out.append({"type": cls, "text": n.get("text"),
                        "enabled": n.get("enabled"),
                        "objectName": n.get("objectName"),
                        "geometry": n.get("geometry"),
                        "has_icon": n.get("has_icon")})
    return out


def _geo_dict(w) -> dict:
    try:
        r = w.geometry()
        return {"x": r.x(), "y": r.y(), "w": r.width(), "h": r.height()}
    except Exception:
        return {}


def _geo_dict_rect(r) -> dict:
    try:
        return {"x": r.x(), "y": r.y(), "w": r.width(), "h": r.height()}
    except Exception:
        return {}


def _window_geometry(win) -> dict:
    try:
        r = win.geometry()
        return {"x": r.x(), "y": r.y(), "w": r.width(), "h": r.height()}
    except Exception:
        return {}


def _structural_hash(tree: dict) -> str:
    parts = []
    for n in _walk_tree(tree):
        if not n.get("visible"):
            continue
        g = n.get("geometry") or {}
        parts.append(f"{n.get('type')}|{n.get('objectName','')}|{g.get('w',0)}x{g.get('h',0)}"
                     f"|{(n.get('text') or '')[:40]}")
    return hashlib.sha256("\n".join(sorted(parts)).encode("utf-8")).hexdigest()[:16]


def _make_crops(win, qapp, regions: list[dict], safe: str, theme: str,
                out_dirs: dict) -> list[dict]:
    crops = []
    try:
        pm = win.grab()
        full = pm.toImage()
        made = 0
        for reg in regions[:6]:
            g = reg.get("geometry") or {}
            w_, h_ = g.get("w", 0), g.get("h", 0)
            if w_ <= 0 or h_ <= 0:
                continue
            name = f"{safe}-{theme}-crop-{made}.png"
            outp = out_dirs["crops"] / name
            try:
                sub = full.copy(max(0, g.get("x", 0)), max(0, g.get("y", 0)), w_, h_)
                sub.save(str(outp))
                crops.append({"file": name, "region": reg})
                made += 1
            except Exception:
                continue
    except Exception:
        pass
    return crops


def _persist_captured(st: CapturedState, out_dirs: dict) -> None:
    tree_data = {
        "screen_id": st.screen_id, "app": st.app, "theme": st.theme,
        "label": st.label, "node_id": st.node_id, "path": st.path,
        "geometry": st.geometry, "sha256": st.sha256, "phash": st.phash,
        "structural_hash": st.structural_hash, "visual_metrics": st.visual_metrics,
        "error": st.error, "stop_reason": st.stop_reason,
        "texts": st.texts, "clickable": st.clickable,
        "scrollbars": st.scrollbars, "tabs": st.tabs, "buttons": st.buttons,
        "crops": st.crops, "tree": st.widget_tree,
    }
    st.tree_path.write_text(json.dumps(tree_data, indent=2, ensure_ascii=False),
                            encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# Contratos visuales globales (genericos, por componente/rol, no por pantalla)
# ═══════════════════════════════════════════════════════════════════════════

def _load_contracts() -> list[dict]:
    import yaml
    contracts: list[dict] = []
    if not _CONTRACTS_DIR.exists():
        return contracts
    files = sorted(_CONTRACTS_DIR.rglob("*.yaml")) + sorted(_CONTRACTS_DIR.rglob("*.yml"))
    for fp in files:
        try:
            data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            print(f"[SENTINEL] contrato ilegible {fp}: {exc}", file=sys.stderr)
            continue
        block = data.get("contracts", []) if isinstance(data, dict) else []
        for c in block:
            c["_source"] = str(fp.relative_to(_PROJ))
            contracts.append(c)
    return contracts


def _run_contracts(states: list[CapturedState], contracts: list[dict],
                   approved_registry: dict) -> list[Finding]:
    findings: list[Finding] = []
    for st in states:
        for c in contracts:
            check_name = c.get("check")
            fn = _CHECKS.get(check_name)
            if fn is None:
                continue
            try:
                results = fn(st, c, states, approved_registry)
            except Exception as exc:
                findings.append(Finding(
                    contract_id=c.get("id", "?"), severity="P2",
                    flag="CONTRACT_ERROR", screen_id=st.screen_id, theme=st.theme,
                    message=f"Contrato {check_name} fallo: {exc}",
                    detail={"traceback": traceback.format_exc(limit=2)},
                ))
                continue
            for r in results:
                findings.append(Finding(
                    contract_id=c.get("id", check_name or "?"),
                    severity=c.get("severity", "P2"),
                    flag=r.get("flag", c.get("id", "").upper()),
                    screen_id=st.screen_id, theme=st.theme,
                    message=r.get("message", ""), detail=r.get("detail", {}),
                ))
    return findings


# --- Implementacion de checks (todos genericos) ----------------------------

def _geo_for_checks(node: dict) -> dict | None:
    gw = node.get("geo_win")
    if isinstance(gw, dict) and gw.get("w", 0) > 0:
        return gw
    g = node.get("geometry")
    return g if isinstance(g, dict) else None


def _surface_of(st: CapturedState) -> str:
    parts = st.screen_id.split(":")
    if len(parts) >= 2:
        rest = parts[1]
        return rest.split("/")[0]
    return st.screen_id


def _check_blank_or_flat(st, c, states, reg) -> list[dict]:
    if st.error or not st.visual_metrics or "error" in st.visual_metrics:
        return [{"flag": "MISSING_EVIDENCE",
                 "message": f"Sin evidencia valida: {st.error or st.visual_metrics}"}]
    mean = st.visual_metrics.get("gray_mean", 0.5)
    stddev = st.visual_metrics.get("gray_stddev", 1.0)
    if mean > _BLANK_MEAN_HI or mean < _BLANK_MEAN_LO or stddev < _FLAT_STDDEV:
        return [{"flag": "BLANK_OR_FLAT",
                 "message": (f"Pantalla blank/flat (mean={mean}, stddev={stddev}). "
                             "No puede contar como evidencia de estado renderizado."),
                 "detail": {"mean": mean, "stddev": stddev}}]
    return []


def _check_duplicate(st, c, states, reg) -> list[dict]:
    if not st.phash:
        return []
    out = []
    max_d = c.get("params", {}).get("max_distance", _DUP_PHASH_DISTANCE)
    for other in states:
        if other is st or other.theme != st.theme or not other.phash:
            continue
        if other.screen_id == st.screen_id:
            continue
        dist = _phash_distance(st.phash, other.phash)
        if dist <= max_d:
            out.append({"flag": "DUPLICATE_SUSPECT",
                        "message": (f"Estado visualmente duplicado con "
                                    f"{other.screen_id} (phash distance={dist})."),
                        "detail": {"other": other.screen_id, "distance": dist}})
    if st.sha256:
        for other in states:
            if other is st or other.theme != st.theme:
                continue
            if other.screen_id != st.screen_id and other.sha256 == st.sha256:
                out.append({"flag": "DUPLICATE_SUSPECT",
                            "message": (f"Hash PNG identico a {other.screen_id}; "
                                        "estado probablemente no alcanzado (fallback)."),
                            "detail": {"other": other.screen_id, "sha256": st.sha256}})
    return out


def _phash_distance(a: str, b: str) -> int:
    try:
        import imagehash
        return int(imagehash.hex_to_hash(a) - imagehash.hex_to_hash(b))
    except Exception:
        return 64


def _check_out_of_viewport(st, c, states, reg) -> list[dict]:
    vw = st.geometry.get("w", 960)
    vh = st.geometry.get("h", 600)
    tol = c.get("params", {}).get("tolerance", 2)
    out = []
    for n in _walk_tree(st.widget_tree):
        if not n.get("visible") or n.get("in_scroll"):
            continue
        g = _geo_for_checks(n)
        if not g:
            continue
        x, y, w_, h_ = g.get("x", 0), g.get("y", 0), g.get("w", 0), g.get("h", 0)
        if w_ <= 0 or h_ <= 0:
            continue
        if x + w_ < tol or y + h_ < tol or x > vw - tol or y > vh - tol:
            if n.get("text") or n.get("clickable"):
                out.append({"flag": "OUT_OF_VIEWPORT",
                            "message": (f"Widget visible fuera del viewport: "
                                        f"{n.get('type')} '{(n.get('text') or '')[:30]}' "
                                        f"en ({x},{y},{w_},{h_}) ventana {vw}x{vh}"),
                            "detail": {"widget": n.get("type"),
                                       "geo_win": g, "viewport": [vw, vh]}})
        if len(out) >= 30:
            break
    return out


def _check_overlap(st, c, states, reg) -> list[dict]:
    rects = []
    for n in _walk_tree(st.widget_tree):
        if not n.get("visible") or not (n.get("text") or n.get("clickable")):
            continue
        g = _geo_for_checks(n)
        if not g:
            continue
        w_, h_ = g.get("w", 0), g.get("h", 0)
        if w_ <= 4 or h_ <= 4:
            continue
        rects.append((g.get("x", 0), g.get("y", 0), w_, h_, n))
    out = []
    min_ratio = c.get("params", {}).get("min_overlap_ratio", _OVERLAP_MIN_RATIO)

    def _containment(ax, ay, aw, ah, bx, by, bw, bh) -> float:
        ix0, iy0 = max(ax, bx), max(ay, by)
        ix1, iy1 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
        iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
        area_a = aw * ah
        return (iw * ih) / area_a if area_a > 0 else 0.0

    for i in range(len(rects)):
        if len(out) >= 20:
            break
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
            ix1, iy1 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
            iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
            if iw <= 0 or ih <= 0:
                continue
            inter = iw * ih
            small = min(a[2] * a[3], b[2] * b[3])
            if small <= 0 or inter / small < min_ratio:
                continue
            if (_containment(a[0], a[1], a[2], a[3], b[0], b[1], b[2], b[3]) >= 0.9 or
                    _containment(b[0], b[1], b[2], b[3], a[0], a[1], a[2], a[3]) >= 0.9):
                continue
            out.append({"flag": "WIDGET_OVERLAP",
                        "message": (f"Solape claro entre {a[4].get('type')} "
                                    f"'{(a[4].get('text') or '')[:20]}' y "
                                    f"{b[4].get('type')} "
                                    f"'{(b[4].get('text') or '')[:20]}' "
                                    f"({inter/small:.0%} del menor)"),
                        "detail": {"a": a[4].get("type"), "b": b[4].get("type"),
                                   "ratio": round(inter / small, 2)}})
            if len(out) >= 20:
                break
    return out


def _check_elided_text(st, c, states, reg) -> list[dict]:
    out = []
    for n in _walk_tree(st.widget_tree):
        if n.get("type") == "NMElidedLabel" and n.get("visible"):
            out.append({"flag": "ELIDED_PRIMARY_TEXT",
                        "message": (f"NMElidedLabel visible: posible texto cortado "
                                    f"'{(n.get('text') or '')[:40]}'"),
                        "detail": {"widget": n.get("type"), "text": n.get("text")}})
    return out


def _check_primary_button_missing_icon(st, c, states, reg) -> list[dict]:
    """Generico: un boton de rol primario (objectName NMButton_gradient, variante
    primaria del design system) deberia portar icono. Deriva del ROL (objectName
    del componente), no de labels de pantallas actuales."""
    out = []
    primary_marker = c.get("params", {}).get("primary_objectname_marker",
                                             "NMButton_gradient")
    for b in st.buttons:
        obj = (b.get("objectName") or "")
        if obj == primary_marker and not b.get("has_icon"):
            out.append({"flag": "PRIMARY_BUTTON_MISSING_ICON",
                        "message": (f"Boton primario ({obj}) sin icono: "
                                    f"'{(b.get('text') or '')[:40]}'"),
                        "detail": b})
    return out


# Alias retrocompatible (tests). Delega en el check generico por rol.
def _check_cta_missing_icon(st, c, states, reg) -> list[dict]:
    return _check_primary_button_missing_icon(st, c, states, reg)


def _check_control_without_metadata(st, c, states, reg) -> list[dict]:
    """Generico: control clickeable sin metadata visual suficiente (sin texto,
    sin icono, sin accessibleName/objectName). Probablemente opaco para auditoria."""
    out = []
    for n in _walk_tree(st.widget_tree):
        if not (n.get("visible") and n.get("clickable")):
            continue
        has_text = bool((n.get("text") or "").strip())
        has_icon = bool(n.get("has_icon"))
        obj = (n.get("objectName") or "").strip()
        if not has_text and not has_icon and not obj:
            out.append({"flag": "CONTROL_WITHOUT_VISUAL_METADATA",
                        "message": (f"Control {n.get('type')} sin texto, icono ni "
                                    f"objectName: imposible auditar su rol."),
                        "detail": {"type": n.get("type"),
                                   "geometry": n.get("geometry")}})
        if len(out) >= 20:
            break
    return out


def _check_checkbox_in_scroll_area(st, c, states, reg) -> list[dict]:
    """Generico estructural: cualquier checkbox/toggle dentro de un QScrollArea.
    Cubre el patron "consentimiento legal dentro de scroll" sin nombrar pantallas."""
    out = []
    for n in _walk_tree(st.widget_tree):
        if (n.get("type") in {"QCheckBox", "NMCustomCheck", "NMSegmentedChoice"}
                and n.get("visible") and n.get("in_scroll")):
            out.append({"flag": "CHECKBOX_IN_SCROLL_AREA",
                        "message": (f"Checkbox dentro de scroll area: "
                                    f"'{(n.get('text') or '')[:40]}' "
                                    "(el control afirmativo debe quedar fijo, no dentro de scroll)."),
                        "detail": {"type": n.get("type"), "text": n.get("text")}})
    return out


def _check_dialog_internal_scrollbar(st, c, states, reg) -> list[dict]:
    """Generico: scrollbar interna dentro de un dialogo cuyo contenido excede el
    body (posible truncamiento legal/terminos)."""
    out = []
    for sb in st.scrollbars:
        if sb.get("type") == "QScrollArea":
            continue
        if sb.get("max", 0) > sb.get("pageStep", 0) and sb.get("visible_range", 0) > 0:
            # solo si pertenece a un dialogo: lo inferimos buscando el scrollbar
            # dentro de in_dialog via arbol
            out.append({"flag": "DIALOG_INTERNAL_SCROLLBAR",
                        "message": (f"Scrollbar interna con rango > page "
                                    f"(max={sb.get('max')}, page={sb.get('pageStep')}): "
                                    "posible contenido truncado en un dialogo."),
                        "detail": sb})
            if len(out) >= 10:
                break
    return out


def _check_dialog_without_close(st, c, states, reg) -> list[dict]:
    """Generico: dialogo (QDialog/NMDialog) sin boton de cierre visible."""
    out = []
    for n in _walk_tree(st.widget_tree):
        if n.get("type") in {"QDialog", "NMDialog", "NMModal"} and n.get("visible"):
            # buscar un descendiente clickeable con rol de cierre
            has_close = False
            for child in _walk_tree(n):
                if not child.get("visible") or not child.get("clickable"):
                    continue
                t = _norm_text(child.get("text"))
                obj = (child.get("objectName") or "").lower()
                if any(k in t for k in ("cerrar", "x", "cancelar", "close", "ok",
                                        "aceptar", "entendido")) or "close" in obj:
                    has_close = True
                    break
            if not has_close:
                out.append({"flag": "DIALOG_WITHOUT_VISIBLE_CLOSE",
                            "message": (f"Dialogo {n.get('type')} sin control de "
                                        "cierre visible/clickeable."),
                            "detail": {"type": n.get("type")}})
    return out


def _check_new_state(st, c, states, reg) -> list[dict]:
    key = f"{st.screen_id}@{st.theme}"
    if key not in reg:
        return [{"flag": "NEW_STATE_UNREVIEWED",
                 "message": (f"Estado descubierto sin baseline aprobada: {key}. "
                             "Requiere revision humana antes de cerrar la auditoria."),
                 "detail": {"screen_id": st.screen_id, "theme": st.theme}}]
    return []


def _check_progress_dot_error(st, c, states, reg) -> list[dict]:
    surface = _surface_of(st).lower()
    if any(k in surface for k in ("error", "fail", "danger")):
        return []
    out = []
    for n in _walk_tree(st.widget_tree):
        if n.get("type") in {"NMProgressBar", "NMRingPulse"} and n.get("visible"):
            obj = (n.get("objectName") or "").lower()
            if "error" in obj or "warning" in obj or "danger" in obj:
                out.append({"flag": "PROGRESS_DOT_ERROR_COLOR",
                            "message": (f"Widget de progreso con nombre de error/warning "
                                        f"fuera de estado de error: {n.get('type')} "
                                        f"#{n.get('objectName')}"),
                            "detail": n})
    return out


def _check_oversized_tabs(st, c, states, reg) -> list[dict]:
    out = []
    vh = st.geometry.get("h", 600)
    max_ratio = c.get("params", {}).get("max_tab_to_window_height_ratio", 0.18)
    for tab in st.tabs:
        for rect in tab.get("tabRects", []):
            th = rect.get("h", 0)
            if vh > 0 and th / vh > max_ratio:
                out.append({"flag": "OVERSIZED_SECONDARY_TAB",
                            "message": (f"Tab gigante: alto {th}px "
                                        f"({th/vh:.0%} de la ventana {vh}px) "
                                        "(rompe densidad por proporcion)."),
                            "detail": {"rect": rect, "type": tab.get("type")}})
    return out


def _check_long_tab_labels(st, c, states, reg) -> list[dict]:
    out = []
    max_len = c.get("params", {}).get("max_label_chars", 22)
    for tab in st.tabs:
        for lbl in tab.get("labels", []):
            if len(str(lbl)) > max_len:
                out.append({"flag": "LONG_TAB_LABEL",
                            "message": (f"Tab con label largo ({len(str(lbl))} chars): "
                                        f"'{str(lbl)[:40]}'"),
                            "detail": {"label": lbl, "type": tab.get("type")}})
    return out


def _check_font_render_broken(states: list[CapturedState],
                              font_diag: dict | None) -> list[Finding]:
    """Guardrail P0: bloquea el resultado si el render de fuentes es defectuoso.

    Se activa cuando se detecta Windows + offscreen (Qt no usa DirectWrite en ese
    modo y produce cuadrados/tofu) o cuando las metricas de glyphs del ADN visual
    estan rotas (NeuroMood, Animo, Respiracion). Un resultado PASS con capturas
    tofu no es evidencia valida.
    """
    if not font_diag or not font_diag.get("font_render_suspect"):
        return []
    warnings_txt = " ".join(font_diag.get("warnings", []))
    first_sid = states[0].screen_id if states else "global"
    return [Finding(
        contract_id="font_render_guardrail",
        severity="P0",
        flag="FONT_RENDER_BROKEN",
        screen_id=first_sid,
        theme="global",
        message=(
            "Render de fuentes defectuoso: capturas pueden contener tofu/cuadrados. "
            + warnings_txt
        ),
        detail={
            "platform": font_diag.get("platform"),
            "sans": font_diag.get("sans"),
            "available_families": font_diag.get("available_families"),
            "glyph_metrics_ok": font_diag.get("glyph_metrics_ok"),
            "warnings": font_diag.get("warnings"),
        },
    )]


_CHECKS: dict[str, Callable[..., list[dict]]] = {
    "blank_or_flat": _check_blank_or_flat,
    "duplicate_suspect": _check_duplicate,
    "out_of_viewport": _check_out_of_viewport,
    "widget_overlap": _check_overlap,
    "elided_primary_text": _check_elided_text,
    "primary_button_missing_icon": _check_primary_button_missing_icon,
    "semantic_cta_missing_icon": _check_cta_missing_icon,
    "control_without_visual_metadata": _check_control_without_metadata,
    "checkbox_in_scroll_area": _check_checkbox_in_scroll_area,
    "dialog_internal_scrollbar": _check_dialog_internal_scrollbar,
    "dialog_without_visible_close": _check_dialog_without_close,
    "oversized_secondary_tabs": _check_oversized_tabs,
    "long_tab_labels": _check_long_tab_labels,
    "new_state_unreviewed": _check_new_state,
    "progress_dot_error_color": _check_progress_dot_error,
}


# ═══════════════════════════════════════════════════════════════════════════
# Baselines y registro aprobado
# ═══════════════════════════════════════════════════════════════════════════

def _load_registry() -> dict:
    if _REGISTRY_PATH.exists():
        try:
            return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_registry(reg: dict) -> None:
    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REGISTRY_PATH.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")


def _propose_baselines(states: list[CapturedState]) -> int:
    reg = _load_registry()
    _PROPOSED_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for st in states:
        key = f"{st.screen_id}@{st.theme}"
        if key in reg:
            continue
        fp = _PROPOSED_DIR / f"{_safe_name(st.screen_id)}-{st.theme}.json"
        fp.write_text(json.dumps({
            "screen_id": st.screen_id, "theme": st.theme, "label": st.label,
            "sha256": st.sha256, "phash": st.phash,
            "structural_hash": st.structural_hash,
            "proposed_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        n += 1
    return n


def _approve_baseline(screen_id: str, theme: str, reason: str) -> dict:
    reg = _load_registry()
    key = f"{screen_id}@{theme}"
    prop = _PROPOSED_DIR / f"{_safe_name(screen_id)}-{theme}.json"
    if not prop.exists():
        return {"ok": False, "error": f"No hay baseline propuesta en {prop}"}
    data = json.loads(prop.read_text(encoding="utf-8"))
    entry = {
        "screen_id": screen_id, "theme": theme,
        "sha256": data.get("sha256"), "phash": data.get("phash"),
        "structural_hash": data.get("structural_hash"),
        "approved_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "commit": _git_value(["rev-parse", "HEAD"]),
        "reason": reason,
    }
    reg[key] = entry
    _save_registry(reg)
    _APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    approved = _APPROVED_DIR / f"{_safe_name(screen_id)}-{theme}.json"
    approved.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        prop.unlink()
    except OSError:
        pass
    return {"ok": True, "entry": entry}


# ═══════════════════════════════════════════════════════════════════════════
# Cobertura + matriz de cobertura
# ═══════════════════════════════════════════════════════════════════════════

def _compute_coverage(states: list[CapturedState], discovered_ids: list[str],
                      reg: dict) -> dict:
    discovered_keys = {f"{s.screen_id}@{s.theme}" for s in states}
    approved_keys = set(reg.keys())
    new_keys = sorted(discovered_keys - approved_keys)
    stale_keys = sorted(approved_keys - discovered_keys)
    return {
        "discovered_states": len(states),
        "captured_states": sum(1 for s in states if not s.error),
        "discovered_keys": sorted(discovered_keys),
        "approved_keys": sorted(approved_keys),
        "new_state_unreviewed": new_keys,
        "stale_states": stale_keys,
        "new_count": len(new_keys),
        "stale_count": len(stale_keys),
    }


def _build_coverage_matrix(states: list[CapturedState], graphs: dict[str, dict],
                           findings: list[Finding]) -> dict:
    """Matriz de cobertura global. NO compara contra V8 (V8 no es dependencia ni
    target oficial). Resume lo que el crawler cubrio y lo que omitio."""
    by_screen = {}
    for f in findings:
        by_screen.setdefault(f.screen_id, []).append(f)
    total_interactive = sum(s.interactive_total for s in states)
    n_captured = sum(1 for s in states if not s.error)
    n_dup = sum(1 for f in findings if f.flag == "DUPLICATE_SUSPECT")
    n_blank = sum(1 for f in findings if f.flag == "BLANK_OR_FLAT")
    all_omitted: list[dict] = []
    all_edges = []
    modals = 0
    tabs_explored = 0
    for g in graphs.values():
        all_omitted.extend(g.get("omitted_actions", []))
        all_edges.extend(g.get("edges", []))
        for n in g.get("nodes", []):
            tabs_explored += sum(1 for e in n.get("path", [])
                                 if isinstance(e, str) and e.startswith("tab:"))
    # stack indexes explorados = tabs_explored (cada tab es un stack index)
    rows = []
    for s in sorted(states, key=lambda x: (x.app, x.screen_id, x.theme)):
        fs = by_screen.get(s.screen_id, [])
        rows.append({
            "screen_id": s.screen_id, "app": s.app, "theme": s.theme,
            "label": s.label,
            "captured": not s.error,
            "reason_if_missing": s.error or "",
            "interactive_widgets": s.interactive_total,
            "tabs": len(s.tabs),
            "findings": len(fs),
            "max_severity": _max_sev(fs),
            "stop_reason": s.stop_reason,
            "path_depth": len(s.path),
            "duplicate": any(f.flag == "DUPLICATE_SUSPECT" for f in fs),
            "fallback": any(f.flag == "DUPLICATE_SUSPECT"
                            and "fallback" in f.message.lower() for f in fs),
        })
    skipped_edges = [e for e in all_edges if e.get("skipped")]
    return {
        "summary": {
            "discovered_states": len(states),
            "captured_states": n_captured,
            "missing_evidence": sum(1 for s in states if s.error),
            "duplicate_suspects": n_dup,
            "blank_or_flat": n_blank,
            "total_interactive_widgets_seen": total_interactive,
            "modal_dialogs_detected": modals,
            "tabs_or_stack_indexes_explored": tabs_explored,
            "edges_total": len(all_edges),
            "edges_skipped_duplicate": len(skipped_edges),
            "actions_omitted": len(all_omitted),
            "interactive_coverage_pct": round(100 * n_captured / max(1, len(states)), 1),
        },
        "rows": rows,
        "omitted_actions": all_omitted,
        "unexplored": {
            "stop_reasons": sorted({s.stop_reason for s in states if s.stop_reason}),
            "note": ("Estados que requieren manipulacion de datos reales o red "
                     "(ej. empty/error forzados sin affordance de UI) no son "
                     "autodescubribles por el crawler generico."),
        },
    }


def _max_sev(fs: list[Finding]) -> str:
    if not fs:
        return ""
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return min((f.severity for f in fs), key=lambda s: order.get(s, 9))


def _check_stale(states: list[CapturedState], reg: dict) -> list[Finding]:
    discovered_keys = {f"{s.screen_id}@{s.theme}" for s in states}
    out = []
    for key in sorted(set(reg.keys()) - discovered_keys):
        screen_id, theme = key.rsplit("@", 1)
        out.append(Finding(
            contract_id="stale_state_registry", severity="P1",
            flag="STALE_STATE", screen_id=screen_id, theme=theme,
            message=(f"Estado aprobado que ya no se descubre: {key}. "
                     "Pantalla desaparecida o navegacion rota."),
            detail={"key": key},
        ))
    return out


def _check_crawl_truncated(graphs: dict[str, dict]) -> list[Finding]:
    """P1 si algun crawl se corto por presupuesto de tiempo: la cobertura es
    PARCIAL (pueden faltar estados sin descubrir), por lo que NO puede emitirse
    un PASS general honesto. Mantiene al Sentinel honesto cuando una app se
    vuelve patologicamente lenta o entra en un flujo que no converge."""
    out = []
    for key, g in graphs.items():
        if not g.get("truncated_by_time"):
            continue
        budget = g.get("crawl_opts", {}).get("time_budget_secs", 0)
        out.append(Finding(
            contract_id="crawl_time_budget", severity="P1",
            flag="CRAWL_TRUNCATED", screen_id=key, theme=g.get("theme", "?"),
            message=(f"Crawl {key} truncado por presupuesto de tiempo "
                     f"({budget:.0f}s) con {g.get('discovered_count', 0)} estados "
                     f"y {g.get('frontier_remaining', 0)} pendientes: cobertura "
                     "PARCIAL, no es auditoria completa. Suba NM_SENTINEL_TIME_BUDGET "
                     "o investigue por que el crawl no converge."),
            detail={"discovered": g.get("discovered_count"),
                    "frontier_remaining": g.get("frontier_remaining"),
                    "time_budget_secs": budget},
        ))
    return out


def _check_obsolete_recipe_refs(reg: dict) -> list[Finding]:
    out = []
    legacy_markers = ("capture_v8", "runtime_live_probe", "popup-", "-v8")
    for key, entry in reg.items():
        blob = json.dumps(entry).lower()
        if any(m in blob for m in legacy_markers):
            out.append(Finding(
                contract_id="obsolete_recipe_reference", severity="P2",
                flag="OBSOLETE_RECIPE_REFERENCE", screen_id=entry.get("screen_id", "?"),
                theme=entry.get("theme", "?"),
                message=(f"Baseline {key} referencia receta/pantalla obsoleta "
                         "(capture_v8/runtime). Limpiar el registro."),
                detail={"key": key},
            ))
    return out


# ═══════════════════════════════════════════════════════════════════════════
# Reporte HTML
# ═══════════════════════════════════════════════════════════════════════════

_MOCKUP_MANIFEST = _PROJ / "qa" / "mockup_reference_static" / "manifest.json"
_CAPTURE_ROOT = _PROJ / "qa" / "_captures_v8"

# Banderas y severidades del modo "test visual Nº1" (registry mockup→captura real).
# Estas reglas son DURAS: el Sentinel NUNCA emite PASS global si el registry
# está incompleto (regla 7 del owner). Cada bandera tiene severidad P0/P1 y
# un mensaje que cita la regla violated para que el log de auditoría sea
# trazable al spec.
_FLAG_REGISTRY_INCOMPLETE = "REGISTRY_INCOMPLETE"
_FLAG_MISSING_CAPTURE = "MISSING_CAPTURE"           # mockup reference sin captura real
_FLAG_MISSING_REFERENCE = "MISSING_REFERENCE"       # captura real sin referencia mockup
_FLAG_COVERAGE_GAP = "COVERAGE_GAP"                 # clase de taxonomía sin entradas
_FLAG_PER_SURFACE_REGRESSION = "PER_SURFACE_REGRESSION"  # phash dist > threshold

# Umbral de phash distance para considerar regresión visual. 10 = diferencia
# significativa en estructura/composición (puede ser render diff por fuente
# faltante o un cambio real de layout). El owner puede ajustar.
_PHASH_REGRESSION_THRESHOLD = 10


def _load_mockup_manifest() -> list[dict]:
    """Carga ``qa/mockup_reference_static/manifest.json`` y devuelve la lista
    de superficies de referencia. Si el manifest no existe, devuelve lista
    vacía (modo degradado: Sentinel emite REGISTRY_INCOMPLETE P0).
    """
    if not _MOCKUP_MANIFEST.exists():
        return []
    try:
        data = json.loads(_MOCKUP_MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data.get("items", [])


def _load_latest_captures() -> dict[tuple, dict]:
    """Lee el batch actual de capturas V8 y devuelve el dict
    ``{(app, view, theme) -> {"png": Path, "iter": str, ...}}`` con la
    captura más reciente por (app, view, theme).

    Fuentes (en orden de prioridad, la última gana):
      1. Manifests históricos ``qa/_captures_v8/iter*/CAPTURE_MANIFEST.json``,
         ordenados por número real de iter (no lexicográfico: ``iter100``
         es más reciente que ``iter89`` porque 100 > 89).
      2. Manifest raíz ``qa/_captures_v8/CAPTURE_MANIFEST.json`` generado
         por ``qa/capture_v8.py --all`` (batch actual). Este manifest es
         la fuente canónica porque ``--all`` regenera los PNGs in-place
         y deja el manifest a la raíz. Los iter dirs previos se ignoran
         si el root manifest está presente y es válido.

    El root manifest tiene PRIORIDAD: si un (app, view, theme) aparece
    en ambos, gana el root. Esto es intencional — refleja la corrida
    más reciente del harness.
    """
    out: dict[tuple, dict] = {}
    if not _CAPTURE_ROOT.exists():
        return out

    def _iter_number(name: str) -> int:
        """Extrae el número real de un nombre 'iterNN' (e.g. 'iter89' -> 89,
        'iter89_baseline' -> 89, 'iter100' -> 100). Lexicográfico falla:
        'iter100' < 'iter89' porque '1' < '8' en ASCII; numérico es la
        verdad cronológica.
        """
        m = re.match(r"iter(\d+)", name)
        return int(m.group(1)) if m else -1

    def _load_manifest(manifest_path: Path, source: str) -> list[dict]:
        """Carga un CAPTURE_MANIFEST.json y devuelve la lista de entries
        exitosos. Errores de parseo o manifests vacíos retornan [].
        """
        if not manifest_path.exists():
            return []
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        out_entries: list[dict] = []
        for entry in data.get("results", []):
            if not entry.get("success", False):
                continue
            key = (entry.get("app", ""), entry.get("view", ""), entry.get("theme", ""))
            if not all(key):
                continue
            out_entries.append((key, entry, manifest_path.parent))
        return out_entries

    # 1. Iter dirs históricos (ordenados por número real, ascendente).
    #    El último procesado GANA en el dict → iter con número mayor
    #    override los anteriores.
    iter_dirs = sorted(
        [d for d in _CAPTURE_ROOT.iterdir()
         if d.is_dir() and d.name.startswith("iter")],
        key=lambda d: _iter_number(d.name),
    )
    for iter_dir in iter_dirs:
        entries = _load_manifest(iter_dir / "CAPTURE_MANIFEST.json", iter_dir.name)
        for key, entry, base_dir in entries:
            png_name = entry.get("file", "")
            png_path = base_dir / png_name
            if not png_path.exists():
                continue
            out[key] = {
                "png": png_path,
                "iter": base_dir.name,
                "view": entry.get("view", ""),
                "app": entry.get("app", ""),
                "theme": entry.get("theme", ""),
                "size_bytes": entry.get("size_bytes", 0),
                "evidence_contract": entry.get("evidence_contract", ""),
            }

    # 2. Root manifest (batch actual del harness). PROCESADO AL FINAL
    #    para que sobrescriba cualquier iter dir previo. Los PNGs del
    #    root manifest están directamente en _CAPTURE_ROOT (no en
    #    subdir).
    root_manifest = _CAPTURE_ROOT / "CAPTURE_MANIFEST.json"
    entries = _load_manifest(root_manifest, "root")
    for key, entry, _base_dir in entries:
        png_name = entry.get("file", "")
        png_path = _CAPTURE_ROOT / png_name
        if not png_path.exists():
            continue
        out[key] = {
            "png": png_path,
            "iter": "root",  # marca semántica del batch actual
            "view": entry.get("view", ""),
            "app": entry.get("app", ""),
            "theme": entry.get("theme", ""),
            "size_bytes": entry.get("size_bytes", 0),
            "evidence_contract": entry.get("evidence_contract", ""),
        }

    return out


def _classify_mockup_taxonomy(item: dict) -> dict:
    """Asigna la taxonomía de superficie declarada por el owner para una
    entrada del manifest. Devuelve dict con clases en las que la entrada
    cuenta (puede contar en varias, p.ej. "detalle" cuenta como
    pantallas/subpantallas).

    Taxonomía mockup-enumerable (regla 2 del owner):
      - producto/app   → manifest.product
      - módulos        → manifest.group
      - pantallas/vistas → manifest.screen_id (vista principal)
      - subpantallas/vistas secundarias/detalles
                        → screen_id "detalle"/"dbt-practice-stop" con
                          state_id != "default" (tabs, modals)
                        O screen_id con sufijo "-"
      - estados/variantes → manifest.state_id (cuando != "default")

    Taxonomía NO-enumerable-en-mockup (la descubre el crawler):
      - componentes / modales / toasts / navegación
        → estas clases NO se auditan en modo registry (audit-mockup);
          se auditan en modo crawler (audit --all) que sí las
          introspecciona en vivo. Si la regla 2 las exigiera acá
          siempre serían GAP (el mockup no las enumera), lo que
          bloquearía PASS en un modo que no tiene cómo cubrirlas.
    """
    screen_id = item.get("screen_id", "")
    state_id = item.get("state_id", "default")
    classes = {"producto/app", "módulos", "pantallas/vistas"}
    # Subpantallas: tabs o modals dentro de detalle, o screen_id con sufijo
    if state_id != "default" and screen_id in ("detalle", "dbt-practice-stop"):
        classes.add("subpantallas/vistas secundarias/detalles")
    if "-" in screen_id and any(screen_id.startswith(p)
                                 for p in ("detalle", "registro-step")):
        classes.add("subpantallas/vistas secundarias/detalles")
    if state_id != "default":
        classes.add("estados/variantes")
    return {"classes": sorted(classes)}


def _build_mockup_to_capture_registry(
        mockup_items: list[dict],
        captures: dict[tuple, dict],
) -> dict:
    """Construye el registry mockup→captura real. Join por
    (theme, screen_id, state_id) → (app, view, theme).

    Estrategia de view_id:
      - screen_id == "dbtlib" → view "dbt-library"
      - screen_id == "dbtnow" → view "dbt-now"
      - screen_id == "dbt-practice-stop" → view "dbt-practice-stop"
      - state_id == "default" → view = screen_id
      - state_id != "default" → view = f"{screen_id}-{state_id}"
      - Fallback: probar ambos patterns.

    Devuelve:
    {
      "mockup_count": 86,
      "capture_count": N,
      "matched": [...],          # per-surface con mockup+real
      "missing_capture": [...],  # mockup sin captura
      "missing_reference": [...],# captura sin mockup
      "per_surface": {
        "<key>": {
          "mockup_path": "...",
          "capture_path": "...",
          "phash_distance": int|None,
          "status": "MATCH|MINOR_DIFF|REGRESSION|MISSING_CAPTURE|MISSING_REFERENCE",
          "surface_classes": [...],
          "screen_id": "...",
          "state_id": "...",
          "theme": "...",
          "app": "...",
          "view": "...",
        }
      },
      "taxonomy_coverage": {
        "<class>": {"mockup_count": N, "capture_count": M, "status": "OK|GAP"}
      }
    }
    """
    # Mapeo de screen_id mockup → posibles view_ids de V8
    _SCREEN_TO_VIEW = {
        "dbtlib": ["dbt-library"],
        "dbtnow": ["dbt-now"],
        "textos": ["textos-globales"],
        "recuperar": ["recuperar-acceso"],
    }

    # Mapeo de (screen_id, state_id) mockup → posibles view_ids de V8.
    # Cubre aliases semanticos donde el state_id del mockup no se deriva
    # mecanicamente de la convencion "{screen_id}-{state_id}" de V8.
    _STATE_VIEW_ALIASES = {
        ("home", "noscore"): ["home-no-score"],
    }

    def _candidate_views(screen_id: str, state_id: str) -> list[str]:
        """Devuelve los view_ids V8 candidatos para una entrada mockup."""
        key = (screen_id, state_id)
        if key in _STATE_VIEW_ALIASES:
            return _STATE_VIEW_ALIASES[key]
        if screen_id in _SCREEN_TO_VIEW:
            return _SCREEN_TO_VIEW[screen_id]
        if state_id == "default":
            return [screen_id]
        # Probar screen_id-state_id primero, luego screen_id solo
        return [f"{screen_id}-{state_id}", screen_id]

    def _app_for_product(product: str) -> str:
        return "hub" if "Hub" in product else "suite"

    registry = {
        "mockup_count": len(mockup_items),
        "capture_count": len(captures),
        "matched": [],
        "missing_capture": [],
        "missing_reference": [],
        "per_surface": {},
        "taxonomy_coverage": {},
    }

    # 1. Indexar capturas por (app, view, theme) para join O(1)
    cap_by_view = captures

    # 2. Join mockup → capture
    matched_keys: set[tuple] = set()
    taxonomy_classes: dict[str, dict] = {}

    for item in mockup_items:
        screen_id = item.get("screen_id", "")
        state_id = item.get("state_id", "default")
        theme = item.get("theme", "light")
        app = _app_for_product(item.get("product", ""))
        candidates = _candidate_views(screen_id, state_id)

        matched_cap = None
        matched_view = None
        for view in candidates:
            key = (app, view, theme)
            if key in cap_by_view:
                matched_cap = cap_by_view[key]
                matched_view = view
                break

        surface_classes = _classify_mockup_taxonomy(item)["classes"]
        for cls in surface_classes:
            taxonomy_classes.setdefault(cls, {"mockup_count": 0, "capture_count": 0})
            taxonomy_classes[cls]["mockup_count"] += 1

        if matched_cap:
            matched_keys.add((app, matched_view, theme))
            key = f"{app}:{screen_id}:{state_id}@{theme}"
            registry["per_surface"][key] = {
                "mockup_path": str(_PROJ / "qa" / "mockup_reference_static"
                                   / item.get("relative_path", "")),
                "capture_path": str(matched_cap["png"]),
                "phash_distance": None,  # se calcula en _compute_per_surface_diff
                "status": "MATCH",  # provisional; se actualiza tras diff
                "surface_classes": surface_classes,
                "screen_id": screen_id,
                "state_id": state_id,
                "theme": theme,
                "app": app,
                "view": matched_view,
            }
            registry["matched"].append(key)
            for cls in surface_classes:
                taxonomy_classes[cls]["capture_count"] += 1
        else:
            key = f"{app}:{screen_id}:{state_id}@{theme}"
            registry["per_surface"][key] = {
                "mockup_path": str(_PROJ / "qa" / "mockup_reference_static"
                                   / item.get("relative_path", "")),
                "capture_path": "",
                "phash_distance": None,
                "status": "MISSING_CAPTURE",
                "surface_classes": surface_classes,
                "screen_id": screen_id,
                "state_id": state_id,
                "theme": theme,
                "app": app,
                "view": candidates[0] if candidates else screen_id,
            }
            registry["missing_capture"].append(key)

    # 3. Capturas sin referencia mockup
    for (app, view, theme), cap in cap_by_view.items():
        if (app, view, theme) in matched_keys:
            continue
        key = f"{app}:{view}@{theme}"
        registry["per_surface"][key] = {
            "mockup_path": "",
            "capture_path": str(cap["png"]),
            "phash_distance": None,
            "status": "MISSING_REFERENCE",
            "surface_classes": ["pantallas/vistas"],  # heurística; surfaced como componente del producto
            "screen_id": view,
            "state_id": "default",
            "theme": theme,
            "app": app,
            "view": view,
        }
        registry["missing_reference"].append(key)

    # 4. Taxonomía: status por clase
    for cls, counts in taxonomy_classes.items():
        if counts["mockup_count"] > 0 and counts["capture_count"] == 0:
            counts["status"] = "GAP"
        else:
            counts["status"] = "OK"
    registry["taxonomy_coverage"] = taxonomy_classes

    return registry


def _compute_per_surface_diff(registry: dict) -> None:
    """Calcula phash distance mockup↔captura por superficie y actualiza
    status. Mutates registry["per_surface"][key] in place.

    Clasificación por umbral:
      - phash_distance <= 5    → MATCH
      - phash_distance <= 10   → MINOR_DIFF (variación de render, fuente, etc.)
      - phash_distance > 10    → REGRESSION (cambio estructural significativo)

    Si la superficie ya está en MISSING_CAPTURE o MISSING_REFERENCE, no
    calcula diff.
    """
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        # Si las dependencias no están, deja status como MATCH provisional
        return

    for key, surface in registry.get("per_surface", {}).items():
        if surface["status"] in ("MISSING_CAPTURE", "MISSING_REFERENCE"):
            continue
        mockup_p = Path(surface["mockup_path"])
        capture_p = Path(surface["capture_path"])
        if not mockup_p.exists() or not capture_p.exists():
            continue
        try:
            m_hash = imagehash.phash(Image.open(mockup_p).convert("RGB"))
            c_hash = imagehash.phash(Image.open(capture_p).convert("RGB"))
            dist = int(m_hash - c_hash)
        except Exception:
            dist = None
        surface["phash_distance"] = dist
        if dist is None:
            surface["status"] = "MATCH"  # no se pudo medir
        elif dist <= 5:
            surface["status"] = "MATCH"
        elif dist <= _PHASH_REGRESSION_THRESHOLD:
            surface["status"] = "MINOR_DIFF"
        else:
            surface["status"] = "REGRESSION"


def _check_registry_completeness(registry: dict) -> list[Finding]:
    """Regla 3 + 4: Falla P0 si hay MISSING_CAPTURE o MISSING_REFERENCE."""
    findings: list[Finding] = []
    for key, surface in registry.get("per_surface", {}).items():
        if surface["status"] == "MISSING_CAPTURE":
            findings.append(Finding(
                contract_id="mockup_registry_completeness", severity="P0",
                flag=_FLAG_MISSING_CAPTURE,
                screen_id=key, theme=surface["theme"],
                message=(f"[REGLA 4] Mockup reference sin captura real: "
                         f"{surface['mockup_path']} (view esperado: "
                         f"{surface['app']}:{surface['view']}, theme "
                         f"{surface['theme']})."),
                detail={"mockup_path": surface["mockup_path"],
                        "expected_view": surface["view"],
                        "app": surface["app"],
                        "screen_id": surface["screen_id"],
                        "state_id": surface["state_id"]},
            ))
        elif surface["status"] == "MISSING_REFERENCE":
            findings.append(Finding(
                contract_id="mockup_registry_completeness", severity="P0",
                flag=_FLAG_MISSING_REFERENCE,
                screen_id=key, theme=surface["theme"],
                message=(f"[REGLA 3] Captura real sin referencia mockup: "
                         f"{surface['capture_path']} (view: {surface['view']}, "
                         f"theme {surface['theme']})."),
                detail={"capture_path": surface["capture_path"],
                        "view": surface["view"],
                        "app": surface["app"]},
            ))
    return findings


def _check_coverage_breadth(registry: dict) -> list[Finding]:
    """Regla 2: Falla P0 si una clase de la taxonomía del owner está GAP.

    SOLO audita las clases enumerables en el mockup manifest (regla 2 cubre
    producto/app, módulos, pantallas, subpantallas, estados). Las clases
    componentes/modales/toasts/navegación NO se enumeran en el mockup; las
    audita el modo ``audit --all`` (con crawler en vivo), no el modo
    registry. Ver ``_classify_mockup_taxonomy``.
    """
    findings: list[Finding] = []
    taxonomy = registry.get("taxonomy_coverage", {})
    # Clases enumerables-en-mockup (regla 2 del owner, subset aplicable al registry)
    mockup_enumerable_taxonomy = [
        "producto/app", "módulos", "pantallas/vistas",
        "subpantallas/vistas secundarias/detalles",
        "estados/variantes",
    ]
    # Clases descubiertas-por-crawler (regla 2 cubre, pero el registry no las enumera)
    # Las listamos en una sección informativa P3 (no bloqueante) para que el
    # log sea trazable, sin bloquear PASS en modo audit-mockup.
    crawler_only_taxonomy = [
        "componentes", "modales", "toasts", "navegación",
    ]
    for cls in mockup_enumerable_taxonomy:
        info = taxonomy.get(cls, {"mockup_count": 0, "capture_count": 0, "status": "GAP"})
        if info.get("status") == "GAP":
            findings.append(Finding(
                contract_id="coverage_breadth", severity="P0",
                flag=_FLAG_COVERAGE_GAP,
                screen_id=cls, theme="*",
                message=(f"[REGLA 2] Taxonomía '{cls}' no cubierta por el "
                         f"registry: {info.get('mockup_count', 0)} referencias "
                         f"mockup, {info.get('capture_count', 0)} capturas "
                         f"reales."),
                detail={"taxonomy_class": cls,
                        "mockup_count": info.get("mockup_count", 0),
                        "capture_count": info.get("capture_count", 0),
                        "audit_scope": "registry-mockup"},
            ))
    for cls in crawler_only_taxonomy:
        # Informativo: el mockup no enumera esta clase; debe ser cubierta
        # por el crawler (audit --all). En modo audit-mockup emitimos un
        # P3 informativo para que el log registre que la cobertura depende
        # del otro modo.
        info = taxonomy.get(cls, {"mockup_count": 0, "capture_count": 0, "status": "GAP"})
        findings.append(Finding(
            contract_id="coverage_breadth_crawler_only", severity="P3",
            flag=f"{_FLAG_COVERAGE_GAP}_CRAWLER_ONLY",
            screen_id=cls, theme="*",
            message=(f"[REGLA 2/INFO] Taxonomía '{cls}' no enumerable en "
                     f"mockup manifest; se audita con ``audit --all`` "
                     f"(crawler en vivo). Estado actual registry: "
                     f"{info.get('mockup_count', 0)} refs mockup, "
                     f"{info.get('capture_count', 0)} capturas."),
            detail={"taxonomy_class": cls,
                    "mockup_count": info.get("mockup_count", 0),
                    "capture_count": info.get("capture_count", 0),
                    "audit_scope": "crawler-only"},
        ))
    return findings


def _check_per_surface_regression(registry: dict) -> list[Finding]:
    """Regla 5 + 6: P1 si phash distance > threshold (REGRESSION)."""
    findings: list[Finding] = []
    for key, surface in registry.get("per_surface", {}).items():
        if surface["status"] == "REGRESSION":
            findings.append(Finding(
                contract_id="per_surface_fidelity", severity="P1",
                flag=_FLAG_PER_SURFACE_REGRESSION,
                screen_id=key, theme=surface["theme"],
                message=(f"[REGLA 5+6] Regresión visual en superficie {key}: "
                         f"phash distance={surface['phash_distance']} > "
                         f"threshold={_PHASH_REGRESSION_THRESHOLD}."),
                detail={"phash_distance": surface["phash_distance"],
                        "threshold": _PHASH_REGRESSION_THRESHOLD,
                        "mockup_path": surface["mockup_path"],
                        "capture_path": surface["capture_path"]},
            ))
    return findings


def _classify_registry(registry: dict) -> dict:
    """Regla 6: separa los 4 buckets canónicos para el log.

    - accepted_changes: MATCH + MINOR_DIFF (no requieren acción)
    - new_unreviewed_states: capturas sin mockup ref (MISSING_REFERENCE)
    - regressions: REGRESSION (phash > threshold)
    - missing: MISSING_CAPTURE (mockup sin captura)
    """
    out = {"accepted_changes": [], "new_unreviewed_states": [],
           "regressions": [], "missing": []}
    for key, surface in registry.get("per_surface", {}).items():
        st = surface["status"]
        if st in ("MATCH", "MINOR_DIFF"):
            out["accepted_changes"].append(key)
        elif st == "MISSING_REFERENCE":
            out["new_unreviewed_states"].append(key)
        elif st == "REGRESSION":
            out["regressions"].append(key)
        elif st == "MISSING_CAPTURE":
            out["missing"].append(key)
    return out


def _html_escape(s: Any) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _write_html_report(out_dirs, states, findings, coverage, matrix, result,
                       general_complete, run_meta) -> Path:
    by_sev = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
    findings_by_screen: dict[str, list[Finding]] = {}
    for f in findings:
        findings_by_screen.setdefault(f.screen_id, []).append(f)
    rel = lambda p: os.path.relpath(p, out_dirs["latest"])  # noqa: E731

    parts: list[str] = []
    parts.append("<!doctype html><html lang='es'><head><meta charset='utf-8'>")
    parts.append("<title>Visual Sentinel — Reporte</title><style>")
    parts.append(
        "body{font-family:system-ui,Segoe UI,Roboto,sans-serif;margin:0;background:#0e1116;color:#e6edf3}"
        "h1,h2,h3{color:#fff}.wrap{max-width:1240px;margin:0 auto;padding:24px}"
        ".card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;margin:12px 0}"
        ".pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600;margin:2px}"
        ".pass{background:#1a7f37}.fail{background:#da3633}"
        ".p0{background:#da3633}.p1{background:#db6d28}.p2{background:#58a6ff}.p3{background:#6e7681}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px}"
        ".thumb{background:#0d1117;border:1px solid #30363d;border-radius:8px;overflow:hidden}"
        ".thumb img{width:100%;height:auto;display:block}.thumb .meta{padding:8px;font-size:12px}"
        ".flag{font-family:ui-monospace,SFMono-Regular,monospace;font-size:11px;color:#f0883e}"
        "details{margin:4px 0}summary{cursor:pointer;font-weight:600}"
        "ul{margin:4px 0 4px 18px}a{color:#58a6ff}small{color:#8b949e}"
        "table{border-collapse:collapse;width:100%;font-size:12px}"
        "th,td{border:1px solid #30363d;padding:4px 6px;text-align:left}"
    )
    parts.append("</style></head><body><div class='wrap'>")
    parts.append("<h1>Visual Sentinel</h1>")
    parts.append(f"<small>Run: {run_meta.get('generated_at','')} · commit "
                 f"{run_meta.get('git',{}).get('short_head','')} · crawler generico</small>")

    parts.append("<div class='card'>")
    badge = "pass" if result == "PASS" else "fail"
    parts.append(f"<span class='pill {badge}'>VISUAL_SENTINEL_RESULT: {result}</span>")
    parts.append(f"<span class='pill {('pass' if general_complete else 'fail')}'>"
                 f"GENERAL_AUDIT_COMPLETE: {'YES' if general_complete else 'NO'}</span>")
    s = matrix.get("summary", {})
    parts.append(f"<span class='pill p3'>estados: {s.get('discovered_states',0)}</span>")
    parts.append(f"<span class='pill p3'>capturados: {s.get('captured_states',0)}</span>")
    parts.append(f"<span class='pill p3'>tabs/index explorados: {s.get('tabs_or_stack_indexes_explored',0)}</span>")
    parts.append(f"<span class='pill p3'>acciones omitidas: {s.get('actions_omitted',0)}</span>")
    parts.append("</div>")

    parts.append("<div class='card'><h2>Cobertura</h2><ul>")
    parts.append(f"<li>Descubiertos: <b>{coverage.get('discovered_states',0)}</b></li>")
    parts.append(f"<li>Capturados: <b>{coverage.get('captured_states',0)}</b></li>")
    parts.append(f"<li>Nuevos sin revisar: <b>{coverage.get('new_count',0)}</b></li>")
    parts.append(f"<li>Stale: <b>{coverage.get('stale_count',0)}</b></li>")
    parts.append(f"<li>Cobertura de estados: <b>{s.get('interactive_coverage_pct',0)}%</b></li>")
    parts.append("</ul></div>")

    parts.append("<div class='card'><h2>Hallazgos por severidad</h2>")
    for sev in ("P0", "P1", "P2", "P3"):
        parts.append(f"<span class='pill {sev.lower()}'>{sev}: {by_sev.get(sev,0)}</span>")
    parts.append("</div>")

    parts.append("<div class='card'><h2>Galeria de pantallas descubiertas</h2><div class='grid'>")
    for st in sorted(states, key=lambda x: (x.app, x.screen_id, x.theme)):
        sf = findings_by_screen.get(st.screen_id, [])
        flags = sorted({f.flag for f in sf})
        rel_png = rel(st.png_path) if st.png_path.exists() else ""
        rel_tree = rel(st.tree_path)
        parts.append("<div class='thumb'>")
        if rel_png:
            parts.append(f"<a href='{_html_escape(rel_png)}'><img src='{_html_escape(rel_png)}' alt='{_html_escape(st.screen_id)}'></a>")
        parts.append("<div class='meta'>")
        parts.append(f"<b>{_html_escape(st.screen_id)}</b> <small>[{_html_escape(st.theme)}]</small><br>")
        parts.append(f"<small>{_html_escape(st.label)}</small><br>")
        if flags:
            parts.append("<span class='flag'>" + ", ".join(_html_escape(f) for f in flags) + "</span><br>")
        parts.append(f"<small><a href='{_html_escape(rel_tree)}'>arbol Qt</a> · "
                     f"interactivo: {st.interactive_total} · botones: {len(st.buttons)} · "
                     f"tabs: {len(st.tabs)}</small>")
        parts.append("</div></div>")
    parts.append("</div></div>")

    parts.append("<div class='card'><h2>Matriz de cobertura</h2>")
    parts.append("<table><tr><th>screen_id</th><th>app</th><th>theme</th>"
                 "<th>capturado</th><th>interactivo</th><th>tabs</th><th>hallazgos</th>"
                 "<th>sev</th><th>stop</th></tr>")
    for r in matrix.get("rows", [])[:400]:
        parts.append(
            f"<tr><td>{_html_escape(r['screen_id'])}</td><td>{_html_escape(r['app'])}</td>"
            f"<td>{_html_escape(r['theme'])}</td><td>{'ok' if r['captured'] else _html_escape(r['reason_if_missing'])}</td>"
            f"<td>{r['interactive_widgets']}</td><td>{r['tabs']}</td>"
            f"<td>{r['findings']}</td><td>{_html_escape(r['max_severity'])}</td>"
            f"<td>{_html_escape(r['stop_reason'])}</td></tr>")
    parts.append("</table></div>")

    parts.append("<div class='card'><h2>Hallazgos por contrato</h2>")
    by_contract: dict[str, list[Finding]] = {}
    for f in findings:
        by_contract.setdefault(f.contract_id, []).append(f)
    if not by_contract:
        parts.append("<p>Sin hallazgos.</p>")
    for cid, fs in sorted(by_contract.items()):
        parts.append(f"<details><summary>{_html_escape(cid)} ({len(fs)})</summary><ul>")
        for f in fs[:80]:
            parts.append(
                f"<li><span class='pill {f.severity.lower()}'>{f.severity}</span> "
                f"<span class='flag'>{_html_escape(f.flag)}</span> "
                f"{_html_escape(f.screen_id)}[{_html_escape(f.theme)}]: "
                f"{_html_escape(f.message)}</li>")
        parts.append("</ul></details>")
    parts.append("</div>")

    parts.append("<div class='card'><h2>Acciones omitidas por seguridad</h2><ul>")
    om = matrix.get("omitted_actions", [])
    if not om:
        parts.append("<li>(ninguna)</li>")
    for o in om[:120]:
        parts.append(f"<li>{_html_escape(o.get('at',''))} · {_html_escape(o.get('widget',''))} "
                     f"'{_html_escape(o.get('text',''))}' — {_html_escape(o.get('reason',''))}</li>")
    parts.append("</ul></div>")

    parts.append("<div class='card'><h2>Limitaciones honestas</h2><small>")
    parts.append(_html_escape(
        "Crawler generico: descubre estados por introspeccion Qt y probing de "
        "afordancias reales (clicks/tabs/checkboxes/dialogs). NO es infalible: "
        "estados que requieren datos reales, red o manipulaciones fuera de la UI "
        "(ej. empty/error forzados sin boton) no son autodescubribles y figuran "
        "como no explorados. Algunos checks (solape, elision, color de progress) "
        "son heuristicos. La revision semantica humana sigue siendo necesaria."))
    parts.append("</small></div>")

    parts.append("</div></body></html>")
    html_path = out_dirs["latest"] / "index.html"
    html_path.write_text("\n".join(parts), encoding="utf-8")
    return html_path


def _write_contact_sheet(states: list[CapturedState], out_dirs: dict) -> None:
    try:
        from PIL import Image, ImageDraw
        thumbs = []
        for st in sorted(states, key=lambda s: (s.app, s.screen_id, s.theme)):
            if st.png_path.exists():
                im = Image.open(st.png_path).convert("RGB")
                im.thumbnail((240, 150))
                thumbs.append((st, im))
        if not thumbs:
            return
        cols = 4
        rows = (len(thumbs) + cols - 1) // cols
        cell_w, cell_h = 240, 170
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (13, 17, 23))
        draw = ImageDraw.Draw(sheet)
        for idx, (st, im) in enumerate(thumbs):
            r, c = divmod(idx, cols)
            x, y = c * cell_w, r * cell_h
            sheet.paste(im, (x + 4, y + 4))
            draw.text((x + 4, y + cell_h - 16),
                      f"{st.screen_id[:28]} [{st.theme}]", fill=(200, 208, 218))
        sheet.save(out_dirs["contact_sheets"] / "contact_sheet.png")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# Orquestacion
# ═══════════════════════════════════════════════════════════════════════════

def _prepare_out_dirs(out_root: Path) -> dict:
    latest = out_root / "latest"
    if latest.exists():
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive = out_root / "runs" / stamp
        try:
            shutil.move(str(latest), str(archive))
        except Exception:
            shutil.rmtree(latest, ignore_errors=True)
    dirs = {"latest": latest, "screenshots": latest / "screenshots",
            "widget_trees": latest / "widget_trees", "crops": latest / "crops",
            "contact_sheets": latest / "contact_sheets", "logs": latest / "logs"}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def _crawl_opts(strict: bool) -> dict:
    budget = _STRICT_TIME_BUDGET_SECS if strict else _DEFAULT_TIME_BUDGET_SECS
    env_budget = os.environ.get("NM_SENTINEL_TIME_BUDGET", "").strip()
    if env_budget:
        try:
            budget = max(15, int(float(env_budget)))
        except ValueError:
            pass
    if strict:
        return {"max_states": _STRICT_MAX_STATES,
                "max_depth": _STRICT_MAX_DEPTH,
                "max_branch": _DEFAULT_MAX_BRANCH,
                "time_budget_secs": budget}
    return {"max_states": _DEFAULT_MAX_STATES,
            "max_depth": _DEFAULT_MAX_DEPTH,
            "max_branch": _DEFAULT_MAX_BRANCH,
            "time_budget_secs": budget}


def _compute_result(general_complete: bool, states: list[CapturedState],
                    findings: list[Finding], coverage: dict,
                    strict: bool) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not general_complete:
        blockers.append("GENERAL_AUDIT_NOT_RUN")
    if any(s.error for s in states):
        blockers.append("MISSING_EVIDENCE")
    blocking_sevs = {"P0", "P1", "P2"} if strict else {"P0", "P1"}
    for f in findings:
        if f.severity in blocking_sevs or f.flag in _BLOCKING_FLAGS:
            blockers.append(f"{f.flag}:{f.screen_id}")
    seen = set()
    uniq = []
    for b in blockers:
        if b not in seen:
            seen.add(b)
            uniq.append(b)
    return ("PASS" if not uniq else "FAIL"), uniq


def _console_summary(result, general_complete, states, findings, coverage, matrix,
                     blockers) -> None:
    by_sev = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
    print("\n" + "=" * 60)
    print(f"VISUAL_SENTINEL_RESULT: {result}")
    print(f"GENERAL_AUDIT_COMPLETE: {'YES' if general_complete else 'NO'}")
    print(f"DISCOVERED_STATES: {coverage.get('discovered_states', 0)}")
    print(f"CAPTURED_STATES: {coverage.get('captured_states', 0)}")
    print(f"NEW_STATE_UNREVIEWED: {coverage.get('new_count', 0)}")
    print(f"STALE_STATES: {coverage.get('stale_count', 0)}")
    print(f"P0: {by_sev.get('P0', 0)}")
    print(f"P1: {by_sev.get('P1', 0)}")
    print(f"P2: {by_sev.get('P2', 0)}")
    s = matrix.get("summary", {})
    print(f"TABS_OR_STACK_INDEXES_EXPLORED: {s.get('tabs_or_stack_indexes_explored', 0)}")
    print(f"ACTIONS_OMITTED: {s.get('actions_omitted', 0)}")
    if blockers:
        print("BLOCKERS:")
        for b in blockers[:40]:
            print(f"  - {b}")
    print("=" * 60)


def _state_to_dict(st: CapturedState) -> dict:
    return {
        "screen_id": st.screen_id, "app": st.app, "theme": st.theme,
        "label": st.label, "node_id": st.node_id,
        "sha256": st.sha256, "phash": st.phash,
        "structural_hash": st.structural_hash, "visual_metrics": st.visual_metrics,
        "error": st.error, "stop_reason": st.stop_reason,
        "png": str(st.png_path.relative_to(_PROJ)),
        "tree": str(st.tree_path.relative_to(_PROJ)),
        "interactive_total": st.interactive_total,
        "n_texts": len(st.texts), "n_buttons": len(st.buttons),
        "n_tabs": len(st.tabs), "n_scrollbars": len(st.scrollbars),
        "n_crops": len(st.crops), "path": st.path,
    }


def _finding_to_dict(f: Finding) -> dict:
    return {"contract_id": f.contract_id, "severity": f.severity, "flag": f.flag,
            "screen_id": f.screen_id, "theme": f.theme, "message": f.message,
            "detail": f.detail}


# ═══════════════════════════════════════════════════════════════════════════
# Comandos CLI
# ═══════════════════════════════════════════════════════════════════════════

def _cmd_list(args) -> int:
    opts = _crawl_opts(getattr(args, "strict", False))
    print("Descubriendo estados (crawler generico, introspeccion Qt en vivo)...")
    total = 0
    for app_key in ("suite", "hub"):
        out_dirs = _prepare_out_dirs(_OUT_ROOT)
        nodes, graph = crawl_app(app_key, "dark_hybrid", opts, out_dirs,
                                 log=lambda *a, **k: None)
        print(f"\n=== {app_key.upper()} ({len(nodes)} estados descubiertos) ===")
        for n in nodes:
            print(f"  {n.screen_id:55s} {n.label[:50]}")
        total += len(nodes)
        # limpiar output efimero del --list
        try:
            shutil.rmtree(_OUT_ROOT / "latest", ignore_errors=True)
        except Exception:
            pass
    print(f"\nTOTAL descubierto: {total} estados (crawler generico, sin recetas manuales)")
    print("Nota: --list usa tema dark; audit --all captura ambos temas.")
    return 0


def _cmd_audit(args) -> int:
    if not args.all and not args.app:
        print("[ERROR] audit requiere --all o --app <suite|hub>.")
        return 2
    strict = bool(getattr(args, "strict", False))
    themes = _theme_map(args.theme)
    apps = ["suite", "hub"] if args.all else [args.app]
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    log_path = out_dirs["logs"] / "run.log"

    def log(msg, end="\n"):
        print(msg, end=end, flush=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(msg + ("" if end == "" else "\n"))

    log(f"[SENTINEL] audit --all={args.all} apps={apps} themes={themes} strict={strict}")
    db = _ensure_isolated_db()
    log(f"[SENTINEL] DB aislada: {db}")

    opts = _crawl_opts(strict)
    all_states: list[CapturedState] = []
    graphs: dict[str, dict] = {}
    discovered_ids: list[str] = []

    for modo in themes:
        for app_key in apps:
            log(f"  CRAWL {app_key.upper()} @ {_short_theme(modo)} "
                f"(caps: states={opts['max_states']}, depth={opts['max_depth']})")
            nodes, graph = crawl_app(app_key, modo, opts, out_dirs, log=log)
            graphs[f"{app_key}@{_short_theme(modo)}"] = graph
            all_states.extend(nodes)
            discovered_ids.extend(n.screen_id for n in nodes)

    _write_contact_sheet(all_states, out_dirs)

    reg = _load_registry()
    contracts = _load_contracts()
    log(f"[SENTINEL] {len(contracts)} contratos cargados; {len(reg)} baselines aprobadas")
    findings = _run_contracts(all_states, contracts, reg)
    findings += _check_stale(all_states, reg)
    findings += _check_obsolete_recipe_refs(reg)
    findings += _check_crawl_truncated(graphs)
    findings += _check_font_render_broken(all_states, _FONT_DIAG_CACHE)
    if _FONT_DIAG_CACHE:
        log(f"[SENTINEL FONT] platform={_FONT_DIAG_CACHE.get('platform')} "
            f"sans={_FONT_DIAG_CACHE.get('sans')} "
            f"available={len(_FONT_DIAG_CACHE.get('available_families', []))} families "
            f"suspect={_FONT_DIAG_CACHE.get('font_render_suspect')}")

    coverage = _compute_coverage(all_states, discovered_ids, reg)
    matrix = _build_coverage_matrix(all_states, graphs, findings)

    # grafo global combinado
    state_graph = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "apps": apps, "themes": [_short_theme(m) for m in themes],
        "graphs_by_run": {k: {"nodes": g["nodes"], "edges": g["edges"],
                              "omitted_actions": g["omitted_actions"],
                              "discovered_count": g["discovered_count"]}
                          for k, g in graphs.items()},
        "node_count": len(all_states),
    }

    general_complete = bool(args.all)
    result, blockers = _compute_result(general_complete, all_states, findings,
                                       coverage, strict)

    run_meta = {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "git": _git_metadata(), "command": sys.argv, "strict": strict}
    manifest = {
        "harness": "qa/visual_sentinel.py", "general_audit_complete": general_complete,
        "result": result, "strict": strict, "blockers": blockers,
        "coverage": coverage, "coverage_matrix_summary": matrix.get("summary", {}),
        "severity_counts": {s: sum(1 for f in findings if f.severity == s)
                            for s in ("P0", "P1", "P2", "P3")},
        "discovered_state_ids": discovered_ids,
        "states": [_state_to_dict(s) for s in all_states], "run_meta": run_meta,
        "font_diagnostics": _FONT_DIAG_CACHE or {},
    }
    (out_dirs["latest"] / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dirs["latest"] / "coverage.json").write_text(
        json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dirs["latest"] / "coverage_matrix.json").write_text(
        json.dumps(matrix, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dirs["latest"] / "ui_state_graph.json").write_text(
        json.dumps(state_graph, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dirs["latest"] / "findings.json").write_text(
        json.dumps([_finding_to_dict(f) for f in findings], indent=2, ensure_ascii=False),
        encoding="utf-8")
    html_path = _write_html_report(out_dirs, all_states, findings, coverage, matrix,
                                   result, general_complete, run_meta)

    _console_summary(result, general_complete, all_states, findings, coverage,
                     matrix, blockers)
    print(f"\nManifest:        {out_dirs['latest'] / 'manifest.json'}")
    print(f"Coverage:        {out_dirs['latest'] / 'coverage.json'}")
    print(f"Coverage matrix: {out_dirs['latest'] / 'coverage_matrix.json'}")
    print(f"State graph:     {out_dirs['latest'] / 'ui_state_graph.json'}")
    print(f"Findings:        {out_dirs['latest'] / 'findings.json'}")
    print(f"Reporte:         {html_path}")
    return 0 if result == "PASS" else 1


def _resolve_screen(app: str, screen_id: str) -> str:
    if ":" in screen_id:
        return screen_id
    return f"{app}:{screen_id}"


def _find_node_by_screen(app_key: str, screen_id: str, modo: str,
                         opts: dict, out_dirs: dict) -> DiscoveredNode | None:
    """Crawl rapido para ubicar el path que produce un screen_id dado.

    Intenta primero coincidencia exacta; luego acepta el primer nodo cuyo
    screen_id comienza con screen_id + ':' o screen_id + '/' (el usuario puede
    abreviar, p.ej. 'suite:home' para 'suite:home-view').
    """
    nodes, _ = crawl_app(app_key, modo, opts, out_dirs,
                         log=lambda *a, **k: None)
    # 1. coincidencia exacta
    for n in nodes:
        if n.screen_id == screen_id:
            return DiscoveredNode(node_id=n.node_id, screen_id=n.screen_id,
                                  app=n.app, theme=n.theme, label=n.label,
                                  path=n.path)
    # 2. prefijo con separador: 'suite:home' encuentra 'suite:home-view',
    #    'suite:home/tab-...' pero NO 'suite:homeostasis'.
    _sep = frozenset("-:/~")
    for n in nodes:
        sid = n.screen_id
        if (sid.startswith(screen_id) and len(sid) > len(screen_id)
                and sid[len(screen_id)] in _sep):
            return DiscoveredNode(node_id=n.node_id, screen_id=n.screen_id,
                                  app=n.app, theme=n.theme, label=n.label,
                                  path=n.path)
    return None




def _cmd_audit_mockup(args) -> int:
    """Modo "test visual Nº1" — registry mockup→captura real con reglas duras.

    No ejecuta el crawler completo (eso puede tardar 5+ min). Solo corre las
    8 reglas del spec del owner sobre el join entre el mockup manifest y
    las últimas capturas V8. Es el modo pensado para gate de CI visual.

    Reglas implementadas (ver qa/LEGACY_TESTS_AUDIT.md y memoria):
      1. Registry completo mockup→captura real
      2. Cubre producto/app, módulos, pantallas, subpantallas, estados,
         componentes, modales, toasts y navegación
      3. Falla si hay superficies sin referencia (MISSING_REFERENCE)
      4. Falla si hay referencia sin captura real (MISSING_CAPTURE)
      5. Diff visual por superficie (phash mockup↔captura)
      6. Separa accepted / new_unreviewed / regressions / missing
      7. PASS bloqueado si registry incompleto (REGISTRY_INCOMPLETE)
      8. HTML report con columnas mockup | captura real | diff
    """
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    log_path = out_dirs["logs"] / "run.log"

    def log(msg, end="\n"):
        print(msg, end=end, flush=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(msg + ("" if end == "" else "\n"))

    log(f"[SENTINEL-MOCKUP] audit-mockup --phash-threshold={args.phash_threshold}")
    log(f"[SENTINEL-MOCKUP] mockup manifest: {_MOCKUP_MANIFEST}")
    log(f"[SENTINEL-MOCKUP] capture root: {_CAPTURE_ROOT}")

    # 1. Cargar manifest mockup y últimas capturas V8
    mockup_items = _load_mockup_manifest()
    captures = _load_latest_captures()
    log(f"[SENTINEL-MOCKUP] mockup items: {len(mockup_items)} · "
        f"v8 captures (latest per view): {len(captures)}")

    if not mockup_items:
        log("[SENTINEL-MOCKUP][ERROR] mockup manifest vacío o ausente; "
            "no se puede construir el registry. Regla 1 violated.")
        return 2

    # 2. Construir registry mockup→captura
    registry = _build_mockup_to_capture_registry(mockup_items, captures)
    log(f"[SENTINEL-MOCKUP] registry: matched={len(registry['matched'])} "
        f"missing_capture={len(registry['missing_capture'])} "
        f"missing_reference={len(registry['missing_reference'])}")

    # 3. Diff por superficie (regla 5)
    _compute_per_surface_diff(registry)

    # 4. Clasificar (regla 6)
    classification = _classify_registry(registry)
    log(f"[SENTINEL-MOCKUP] classification: "
        f"accepted={len(classification['accepted_changes'])} "
        f"new_unreviewed={len(classification['new_unreviewed_states'])} "
        f"regressions={len(classification['regressions'])} "
        f"missing={len(classification['missing'])}")

    # 5. Findings (reglas 2, 3, 4, 5+6)
    findings: list[Finding] = []
    findings += _check_registry_completeness(registry)   # reglas 3, 4
    findings += _check_coverage_breadth(registry)         # regla 2
    findings += _check_per_surface_regression(registry)   # regla 5+6

    # 6. Regla 7: si el registry está incompleto, agregar un P0 explícito
    # REGISTRY_INCOMPLETE para que el PASS global quede bloqueado.
    registry_incomplete = bool(registry["missing_capture"]
                                or registry["missing_reference"])
    if registry_incomplete:
        n_missing = len(registry["missing_capture"])
        n_unref = len(registry["missing_reference"])
        findings.append(Finding(
            contract_id="registry_completeness_gate", severity="P0",
            flag=_FLAG_REGISTRY_INCOMPLETE, screen_id="*", theme="*",
            message=(f"[REGLA 7] Registry incompleto: "
                     f"{n_missing} mockup refs sin captura real + "
                     f"{n_unref} capturas reales sin referencia. "
                     f"PASS global BLOQUEADO."),
            detail={"missing_capture": n_missing,
                    "missing_reference": n_unref},
        ))

    # 7. Resultado: PASS solo si 0 blockers P0/P1
    by_sev = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
    blockers_p0 = by_sev["P0"]
    blockers_p1 = by_sev["P1"]
    result = "PASS" if (blockers_p0 == 0 and blockers_p1 == 0) else "FAIL"
    log(f"[SENTINEL-MOCKUP] resultado: {result} (P0={blockers_p0} P1={blockers_p1} P2={by_sev['P2']} P3={by_sev['P3']})")

    # 8. Persistir artefactos
    run_meta = {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "git": _git_metadata(),
                "phash_threshold": args.phash_threshold,
                "registry_summary": {
                    "mockup_count": registry["mockup_count"],
                    "capture_count": registry["capture_count"],
                    "matched": len(registry["matched"]),
                    "missing_capture": len(registry["missing_capture"]),
                    "missing_reference": len(registry["missing_reference"]),
                    "taxonomy_coverage": registry["taxonomy_coverage"],
                },
                "classification": classification}

    (out_dirs["latest"] / "registry.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dirs["latest"] / "findings.json").write_text(
        json.dumps([_finding_to_dict(f) for f in findings], indent=2, ensure_ascii=False),
        encoding="utf-8")
    (out_dirs["latest"] / "classification.json").write_text(
        json.dumps(classification, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dirs["latest"] / "manifest.json").write_text(
        json.dumps({"command": "audit-mockup", "result": result, "findings_by_sev": by_sev,
                    "registry_summary": run_meta["registry_summary"],
                    "classification": classification,
                    "generated_at": run_meta["generated_at"],
                    "git": run_meta["git"]}, indent=2, ensure_ascii=False),
        encoding="utf-8")

    # 9. HTML report con columnas mockup | real | diff
    _write_html_report_mockup(out_dirs, registry, classification, findings, result, run_meta)

    # 10. Console summary
    print()
    print("=" * 64)
    print(f"VISUAL_SENTINEL_MOCKUP_RESULT: {result}")
    print(f"REGISTRY_COMPLETE: {'YES' if not registry_incomplete else 'NO'}")
    print(f"MOCKUP_ITEMS: {registry['mockup_count']}")
    print(f"V8_CAPTURES_LATEST: {registry['capture_count']}")
    print(f"MATCHED: {len(registry['matched'])}")
    print(f"MISSING_CAPTURE: {len(registry['missing_capture'])}")
    print(f"MISSING_REFERENCE: {len(registry['missing_reference'])}")
    print(f"REGRESSIONS: {len(classification['regressions'])}")
    print(f"NEW_UNREVIEWED: {len(classification['new_unreviewed_states'])}")
    print(f"P0: {by_sev['P0']}  P1: {by_sev['P1']}  P2: {by_sev['P2']}  P3: {by_sev['P3']}")
    if registry["taxonomy_coverage"]:
        print("TAXONOMY_COVERAGE:")
        for cls, info in sorted(registry["taxonomy_coverage"].items()):
            print(f"  {cls:50s}  mockup={info.get('mockup_count', 0):3d}  "
                  f"capture={info.get('capture_count', 0):3d}  {info.get('status', '?')}")
    print("=" * 64)
    if blockers_p0 or blockers_p1:
        print("BLOCKERS:")
        for f in findings:
            if f.severity in ("P0", "P1"):
                print(f"  [{f.severity}] {f.flag}: {f.screen_id} — {f.message[:120]}")
    print(f"\nHTML report: {out_dirs['latest'] / 'index_mockup.html'}")
    return 0 if result == "PASS" else 1


def _write_html_report_mockup(out_dirs: dict, registry: dict, classification: dict,
                              findings: list[Finding], result: str, run_meta: dict) -> Path:
    """Regla 8: HTML report con columnas mockup | captura real | diff por superficie."""
    rel = lambda p: os.path.relpath(p, out_dirs["latest"])  # noqa: E731
    by_sev = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1

    parts: list[str] = []
    parts.append("<!doctype html><html lang='es'><head><meta charset='utf-8'>")
    parts.append("<title>Visual Sentinel — Registry Mockup↔Captura</title><style>")
    parts.append(
        "body{font-family:system-ui,Segoe UI,Roboto,sans-serif;margin:0;background:#0e1116;color:#e6edf3}"
        "h1,h2,h3{color:#fff}.wrap{max-width:1640px;margin:0 auto;padding:24px}"
        ".card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;margin:12px 0}"
        ".pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600;margin:2px}"
        ".pass{background:#1a7f37}.fail{background:#da3633}.warn{background:#db6d28}"
        ".p0{background:#da3633}.p1{background:#db6d28}.p2{background:#58a6ff}.p3{background:#6e7681}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:14px}"
        ".triple{background:#0d1117;border:1px solid #30363d;border-radius:8px;overflow:hidden}"
        ".triple .meta{padding:8px;font-size:12px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px}"
        ".triple .imgs{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0;background:#000}"
        ".triple .imgs>div{position:relative}"
        ".triple .imgs img{width:100%;height:auto;display:block;aspect-ratio:16/10;object-fit:cover}"
        ".triple .imgs .lbl{position:absolute;top:4px;left:4px;background:rgba(0,0,0,.7);color:#fff;"
        "padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600}"
        ".triple .status{font-family:ui-monospace,SFMono-Regular,monospace;font-size:11px;font-weight:700}"
        "table{border-collapse:collapse;width:100%;font-size:12px}"
        "th,td{border:1px solid #30363d;padding:4px 6px;text-align:left}"
        "small{color:#8b949e}"
        "details{margin:4px 0}summary{cursor:pointer;font-weight:600}"
        "ul{margin:4px 0 4px 18px}"
    )
    parts.append("</style></head><body><div class='wrap'>")
    parts.append("<h1>Visual Sentinel — Registry Mockup↔Captura</h1>")
    parts.append(f"<small>Run: {run_meta.get('generated_at', '')} · commit "
                 f"{run_meta.get('git', {}).get('short_head', '')} · phash threshold "
                 f"{run_meta.get('phash_threshold', '')}</small>")

    # Header badges
    badge = "pass" if result == "PASS" else "fail"
    parts.append("<div class='card'>")
    parts.append(f"<span class='pill {badge}'>REGISTRY_AUDIT_RESULT: {result}</span>")
    s = run_meta.get("registry_summary", {})
    parts.append(f"<span class='pill {'pass' if not s.get('missing_capture') and not s.get('missing_reference') else 'fail'}'>"
                 f"REGISTRY_COMPLETE: {'YES' if not s.get('missing_capture') and not s.get('missing_reference') else 'NO'}</span>")
    parts.append(f"<span class='pill p3'>mockup items: {s.get('mockup_count', 0)}</span>")
    parts.append(f"<span class='pill p3'>v8 capturas: {s.get('capture_count', 0)}</span>")
    parts.append(f"<span class='pill p3'>matched: {s.get('matched', 0)}</span>")
    parts.append(f"<span class='pill p0'>missing_capture: {s.get('missing_capture', 0)}</span>")
    parts.append(f"<span class='pill p0'>missing_reference: {s.get('missing_reference', 0)}</span>")
    parts.append("</div>")

    # Hallazgos por severidad
    parts.append("<div class='card'><h2>Hallazgos por severidad</h2>")
    for sev in ("P0", "P1", "P2", "P3"):
        parts.append(f"<span class='pill {sev.lower()}'>{sev}: {by_sev.get(sev, 0)}</span>")
    parts.append("</div>")

    # Taxonomía
    parts.append("<div class='card'><h2>Cobertura de taxonomía (regla 2)</h2><table>")
    parts.append("<tr><th>clase</th><th>mockup_count</th><th>capture_count</th><th>status</th></tr>")
    for cls, info in sorted((registry.get("taxonomy_coverage") or {}).items()):
        st = info.get("status", "?")
        pill_cls = "fail" if st == "GAP" else "pass"
        parts.append(f"<tr><td>{_html_escape(cls)}</td>"
                     f"<td>{info.get('mockup_count', 0)}</td>"
                     f"<td>{info.get('capture_count', 0)}</td>"
                     f"<td><span class='pill {pill_cls}'>{st}</span></td></tr>")
    parts.append("</table></div>")

    # Clasificación (regla 6)
    parts.append("<div class='card'><h2>Clasificación por superficie (regla 6)</h2>")
    for bucket, label in [("accepted_changes", "Cambios aceptados (MATCH + MINOR_DIFF)"),
                          ("new_unreviewed_states", "Estados nuevos sin revisar (MISSING_REFERENCE)"),
                          ("regressions", "Regresiones (REGRESSION)"),
                          ("missing", "Faltantes (MISSING_CAPTURE)")]:
        keys = classification.get(bucket, [])
        parts.append(f"<details {'open' if keys else ''}>"
                     f"<summary>{label} ({len(keys)})</summary><ul>")
        for k in keys[:200]:
            parts.append(f"<li><code>{_html_escape(k)}</code></li>")
        if len(keys) > 200:
            parts.append(f"<li>… y {len(keys) - 200} más</li>")
        parts.append("</ul></details>")
    parts.append("</div>")

    # Grid 3-columna: mockup | captura real | diff
    parts.append("<div class='card'><h2>Per-surface: mockup | captura real | diff (regla 5+8)</h2>")
    parts.append("<div class='grid'>")
    # Ordenar: primero MISSING, luego REGRESSION, luego MATCH/MINOR_DIFF
    order = {"MISSING_CAPTURE": 0, "MISSING_REFERENCE": 1, "REGRESSION": 2,
             "MINOR_DIFF": 3, "MATCH": 4}
    sorted_surfaces = sorted(registry.get("per_surface", {}).items(),
                              key=lambda kv: (order.get(kv[1]["status"], 9), kv[0]))
    for key, surface in sorted_surfaces:
        st = surface["status"]
        st_pill_cls = {"MATCH": "pass", "MINOR_DIFF": "warn", "REGRESSION": "fail",
                       "MISSING_CAPTURE": "fail", "MISSING_REFERENCE": "fail"}.get(st, "p3")
        phash_d = surface.get("phash_distance")
        phash_str = f"phash={phash_d}" if phash_d is not None else "phash=n/a"
        parts.append("<div class='triple'>")
        parts.append("<div class='imgs'>")
        # Mockup
        if surface["mockup_path"]:
            rel_m = rel(surface["mockup_path"])
            parts.append(f"<div><span class='lbl'>MOCKUP</span>"
                         f"<img src='{_html_escape(rel_m)}' alt='mockup' "
                         f"onerror=\"this.style.opacity=.2;this.alt='(missing)'\"></div>")
        else:
            parts.append("<div><span class='lbl'>MOCKUP</span>"
                         "<div style='aspect-ratio:16/10;background:#222;display:grid;place-items:center;color:#666'>"
                         "<small>(no ref)</small></div></div>")
        # Captura real
        if surface["capture_path"]:
            rel_c = rel(surface["capture_path"])
            parts.append(f"<div><span class='lbl'>REAL</span>"
                         f"<img src='{_html_escape(rel_c)}' alt='real' "
                         f"onerror=\"this.style.opacity=.2;this.alt='(missing)'\"></div>")
        else:
            parts.append("<div><span class='lbl'>REAL</span>"
                         "<div style='aspect-ratio:16/10;background:#222;display:grid;place-items:center;color:#666'>"
                         "<small>(no capture)</small></div></div>")
        # Diff: placeholder visual (chip con phash distance)
        diff_color = {"MATCH": "#1a7f37", "MINOR_DIFF": "#db6d28",
                      "REGRESSION": "#da3633", "MISSING_CAPTURE": "#da3633",
                      "MISSING_REFERENCE": "#da3633"}.get(st, "#6e7681")
        parts.append(f"<div style='background:{diff_color};aspect-ratio:16/10;"
                     "display:grid;place-items:center;color:#fff;font-weight:700'>"
                     f"<div style='text-align:center'>"
                     f"<div style='font-size:18px'>{st}</div>"
                     f"<div style='font-size:11px;margin-top:4px'>{phash_str}</div>"
                     f"</div></div>")
        parts.append("</div>")  # /imgs
        # Meta
        parts.append("<div class='meta'>")
        parts.append(f"<b>{_html_escape(key)}</b>")
        parts.append(f"<span class='pill {st_pill_cls}'>{st}</span>")
        parts.append(f"<small>{_html_escape(' · '.join(surface.get('surface_classes', [])))}</small>")
        parts.append("</div>")
        parts.append("</div>")  # /triple
    parts.append("</div></div>")

    # Hallazgos detallados
    parts.append("<div class='card'><h2>Hallazgos detallados</h2>")
    by_flag: dict[str, list[Finding]] = {}
    for f in findings:
        by_flag.setdefault(f.flag, []).append(f)
    if not by_flag:
        parts.append("<p>Sin hallazgos.</p>")
    for flag, fs in sorted(by_flag.items()):
        parts.append(f"<details open><summary>{_html_escape(flag)} ({len(fs)})</summary><ul>")
        for f in fs[:100]:
            parts.append(
                f"<li><span class='pill {f.severity.lower()}'>{f.severity}</span> "
                f"<code>{_html_escape(f.screen_id)}</code> "
                f"[{_html_escape(f.theme)}]: {_html_escape(f.message)}</li>")
        if len(fs) > 100:
            parts.append(f"<li>… y {len(fs) - 100} más</li>")
        parts.append("</ul></details>")
    parts.append("</div>")

    parts.append("</div></body></html>")
    html_path = out_dirs["latest"] / "index_mockup.html"
    html_path.write_text("\n".join(parts), encoding="utf-8")
    return html_path


def _cmd_capture(args) -> int:
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    _ensure_isolated_db()
    themes = _theme_map(args.theme)
    screen_id = _resolve_screen(args.app, args.screen)
    app_key = screen_id.split(":")[0]
    opts = _crawl_opts(False)
    print("[SENTINEL] capture targeted (sin resultado general)")
    node = _find_node_by_screen(app_key, screen_id, themes[0], opts, out_dirs)
    if node is None:
        print(f"[ERROR] screen '{screen_id}' no descubierto por el crawler. Use --list.")
        return 1
    states: list[CapturedState] = []
    for modo in themes:
        qapp, win = _instantiate(app_key, modo)
        try:
            ok = _replay_path(win, node.path, qapp)
            if not ok:
                states.append(_error_state(screen_id, app_key, modo, node.label,
                                           out_dirs, "replay fallo"))
                continue
            st = _capture_state(win, qapp, app_key, modo, out_dirs,
                                screen_id=screen_id, label=node.label, path=node.path)
            _persist_captured(st, out_dirs)
            states.append(st)
        finally:
            _close_window(win)
    print(f"\nCaptura targeted: {screen_id} ({len(states)} tema(s))")
    for st in states:
        print(f"  {st.theme}: {st.png_path}  error={st.error}")
    print("VISUAL_SENTINEL_RESULT: TARGETED_INSPECTION_ONLY")
    print("GENERAL_AUDIT_COMPLETE: NO")
    print("GENERAL_AUDIT_NOT_RUN: YES")
    print("(capture --screen nunca emite resultado general; corra audit --all)")
    return 0


def _error_state(screen_id, app_key, modo, label, out_dirs, err) -> CapturedState:
    theme = _short_theme(modo)
    safe = _safe_name(screen_id)
    return CapturedState(
        screen_id=screen_id, app=app_key, theme=theme, label=label,
        png_path=out_dirs["screenshots"] / f"{safe}-{theme}.png",
        tree_path=out_dirs["widget_trees"] / f"{safe}-{theme}.json",
        sha256=None, phash=None, structural_hash="", visual_metrics={},
        widget_tree={}, texts=[], clickable=[], scrollbars=[], tabs=[],
        buttons=[], crops=[], geometry={}, error=err)


def _cmd_inspect(args) -> int:
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    _ensure_isolated_db()
    screen_id = _resolve_screen(args.app, args.screen)
    app_key = screen_id.split(":")[0]
    modo = _theme_map(args.theme)[0]
    opts = _crawl_opts(False)
    node = _find_node_by_screen(app_key, screen_id, modo, opts, out_dirs)
    if node is None:
        print(f"[ERROR] screen '{screen_id}' no descubierto por el crawler. Use --list.")
        return 1
    qapp, win = _instantiate(app_key, modo)
    try:
        _replay_path(win, node.path, qapp)
        st = _capture_state(win, qapp, app_key, modo, out_dirs,
                            screen_id=screen_id, label=node.label, path=node.path)
    finally:
        _close_window(win)
    _persist_captured(st, out_dirs)
    print(f"\nINSPECCION: {screen_id} [{_short_theme(modo)}]")
    print(f"  path:     {' > '.join(a.get('label','') for a in node.path) or '(root)'}")
    print(f"  PNG:      {st.png_path}")
    print(f"  Arbol Qt: {st.tree_path}")
    print(f"  Textos visibles ({len(st.texts)}):")
    for t in st.texts[:40]:
        print(f"    - {t}")
    print(f"  Botones ({len(st.buttons)}):")
    for b in st.buttons[:40]:
        print(f"    - [{b.get('type')}] '{b.get('text')}' obj={b.get('objectName')} icon={b.get('has_icon')} enabled={b.get('enabled')}")
    print(f"  Tabs ({len(st.tabs)}):")
    for tb in st.tabs:
        print(f"    - {tb.get('type')} count={tb.get('count')} labels={tb.get('labels')}")
    print(f"  Scrollbars ({len(st.scrollbars)}):")
    for sb in st.scrollbars:
        print(f"    - {sb}")
    print(f"  interactive_total={st.interactive_total}")
    print(f"  sha256={st.sha256}  phash={st.phash}  struct={st.structural_hash}")
    print(f"  metricas={st.visual_metrics}")
    print("VISUAL_SENTINEL_RESULT: TARGETED_INSPECTION_ONLY")
    print("GENERAL_AUDIT_COMPLETE: NO")
    print("GENERAL_AUDIT_NOT_RUN: YES")
    return 0


def _cmd_propose_baselines(args) -> int:
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    _ensure_isolated_db()
    opts = _crawl_opts(False)
    states: list[CapturedState] = []
    for app_key in ("suite", "hub"):
        for modo in ("dark_hybrid", "light_hybrid"):
            nodes, _ = crawl_app(app_key, modo, opts, out_dirs,
                                 log=lambda *a, **k: None)
            states.extend(nodes)
    n = _propose_baselines(states)
    print(f"Baselines propuestas generadas: {n}")
    print(f"Directorio: {_PROPOSED_DIR}")
    print("Ninguna fue aprobada. Use approve-baseline --screen <id> --theme <theme>.")
    return 0


def _cmd_approve_baseline(args) -> int:
    screen_id = _resolve_screen(args.app, args.screen)
    res = _approve_baseline(screen_id, args.theme, args.reason or "manual approval")
    if res.get("ok"):
        print(f"Baseline aprobada: {screen_id}@{args.theme}")
        print(f"  commit: {res['entry'].get('commit')}")
        print(f"  fecha:  {res['entry'].get('approved_at')}")
        print(f"  motivo: {res['entry'].get('reason')}")
        return 0
    print(f"[ERROR] {res.get('error')}")
    return 1


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="visual_sentinel",
        description="Auditor visual canonico, independiente y autodescubrible.",
    )
    p.add_argument("--list", action="store_true", help="Listar estados descubiertos")
    p.add_argument(
        "--platform", choices=["offscreen", "native", "auto"], default="auto",
        help=("Plataforma Qt para capturas: auto usa native en Windows sin CI "
              "(evita tofu/cuadrados), offscreen en CI/headless (default: auto)"),
    )
    sub = p.add_subparsers(dest="command")

    sub.add_parser("list", help="Listar estados descubiertos").set_defaults(func=_cmd_list)

    pa = sub.add_parser("audit", help="Auditoria general (usar --all para resultado general)")
    pa.add_argument("--all", action="store_true", help="Auditar todo (Suite + Hub)")
    pa.add_argument("--app", choices=["suite", "hub"], help="Auditar una sola app")
    pa.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    pa.add_argument("--strict", action="store_true",
                    help="Cobertura maxima y P0/P1/P2 bloqueantes")
    pa.set_defaults(func=_cmd_audit)

    pc = sub.add_parser("capture", help="Capturar una pantalla puntual (sin resultado general)")
    pc.add_argument("--screen", required=True, help="screen_id (app:surface[/...])")
    pc.add_argument("--app", choices=["suite", "hub"], default="suite")
    pc.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    pc.set_defaults(func=_cmd_capture)

    # Modo "test visual Nº1" — registry mockup→captura real con reglas duras.
    # No requiere el crawler completo: usa el mockup manifest + las últimas
    # capturas V8 + los contracts existentes. Pensado para correr en <30s
    # y servir de gate de CI visual.
    pm = sub.add_parser(
        "audit-mockup",
        help=("Auditoría registry mockup→captura real con reglas duras "
              "(reglas 1-8 del owner). Modo rápido, sin crawler completo."),
    )
    pm.add_argument("--phash-threshold", type=int, default=_PHASH_REGRESSION_THRESHOLD,
                    help=f"Umbral phash distance para REGRESSION (default: {_PHASH_REGRESSION_THRESHOLD})")
    pm.add_argument("--strict", action="store_true",
                    help="(reservado) cualquier P0/P1/P2 bloqueante")
    pm.set_defaults(func=_cmd_audit_mockup)

    pi = sub.add_parser("inspect", help="Inspeccionar una pantalla en consola")
    pi.add_argument("--screen", required=True, help="screen_id (app:surface[/...])")
    pi.add_argument("--app", choices=["suite", "hub"], default="suite")
    pi.add_argument("--theme", choices=["light", "dark"], default="light")
    pi.set_defaults(func=_cmd_inspect)

    sub.add_parser("propose-baselines",
                   help="Generar baselines propuestas (sin aprobar)").set_defaults(
        func=_cmd_propose_baselines)

    pb = sub.add_parser("approve-baseline", help="Aprobar una baseline propuesta")
    pb.add_argument("--screen", required=True)
    pb.add_argument("--app", choices=["suite", "hub"], default="suite")
    pb.add_argument("--theme", choices=["light", "dark"], required=True)
    pb.add_argument("--reason", default="", help="Motivo de la aprobacion")
    pb.set_defaults(func=_cmd_approve_baseline)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _configure_platform(getattr(args, "platform", "auto"))  # antes de cualquier Qt
    if getattr(args, "list", False):
        return _cmd_list(args)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 1
    return int(func(args))


if __name__ == "__main__":
    raise SystemExit(main())
