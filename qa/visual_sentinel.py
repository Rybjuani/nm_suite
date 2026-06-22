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
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
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

# --- Aislamiento QA: offscreen + datos demo + DB temporal --------------------
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
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

# Caps del crawler (mode-dependientes).
_DEFAULT_MAX_STATES = 70
_DEFAULT_MAX_DEPTH = 4
_DEFAULT_MAX_BRANCH = 12
_STRICT_MAX_STATES = 130
_STRICT_MAX_DEPTH = 6

# Palabras que indican acciones destructivas/inseguras (filtro generico por
# semantica del control, no por pantalla). Se omiten y se loguean.
_UNSAFE_TEXT_KEYS = (
    "salir", "eliminar", "borrar", "quitar", "desvincular", "unlink",
    "delete", "remove", "logout", "cerrar sesion", "cerrar sesión",
    "cancelar cuenta", "reset total",
)
# Controles de chrome / navegacion back que no aportan estados nuevos y gastan
# presupuesto: se omiten (no son destructivos, solo redundantes).
_CHROME_OBJECTNAMES = ("NMWindowChrome", "NMThemeToggle", "NMBackButton",
                       "NMCloseButton", "NMMinButton")
_BACK_TEXT_KEYS = ("volver", "atras", " atrás", "←", "back")


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


def _is_clickable(w) -> bool:
    from PyQt6.QtWidgets import (
        QPushButton, QToolButton, QCheckBox, QRadioButton, QCommandLinkButton,
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


def _is_unsafe(widget, text_norm: str) -> str | None:
    """Razon de inseguridad o None si es segura. Filtro generico por semantica
    del control (texto/objectName), no por pantalla."""
    try:
        obj = (widget.objectName() or "").lower()
    except Exception:
        obj = ""
    if any(k in obj for k in (k.lower() for k in _CHROME_OBJECTNAMES)):
        return "chrome-control"
    if any(k in text_norm for k in _UNSAFE_TEXT_KEYS):
        return "destructive-text"
    if any(k in text_norm for k in _BACK_TEXT_KEYS):
        return "navigation-back"
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
    try:
        for w in root.findChildren(QWidget):
            if len(actions) >= max_branch:
                break
            if sip_deleted(w) or not w.isVisible() or not w.isEnabled():
                continue
            if not _is_clickable(w):
                continue
            text = _widget_text(w)
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
            locator = _widget_locator(w, root)
            label_src = text if text else type(w).__name__
            action = {
                "kind": "click",
                "locator": locator,
                "label": "act:" + _sanitize_label(label_src),
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

    qapp = QApplication.instance() or QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)
    try:
        from shared.fonts import load_fonts
        load_fonts()
    except Exception:
        pass
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


def _close_window(win) -> None:
    from PyQt6.QtWidgets import QApplication
    qapp = QApplication.instance()
    try:
        if win is not None:
            win.close()
            win.deleteLater()
    except Exception:
        pass
    if qapp is not None:
        for tl in QApplication.topLevelWidgets():
            if tl is not win and tl.isVisible():
                try:
                    tl.close()
                    tl.deleteLater()
                except Exception:
                    pass
        _drain(qapp, cycles=3)


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

    nodes: list[CapturedState] = []
    edges: list[dict] = []
    omitted: list[dict] = []
    seen_sig: dict[str, str] = {}      # sig -> screen_id
    used_screen_ids: set[str] = set()
    used_labels: dict[str, int] = {}

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
        nonlocal nodes
        qapp, win = _instantiate(app_key, modo)
        try:
            ok = _replay_path(win, path, qapp)
            if not ok:
                omitted.append({"at": "<replay>", "path_len": len(path),
                                "reason": "locator-no-resolvio"})
                return None
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
                return None
            st.node_id = sid
            seen_sig[sig] = sid
            nodes.append(st)
            if parent_id:
                edges.append({"from": parent_id, "to": sid, "via": via})
            return st
        finally:
            _close_window(win)

    # BFS con frontera acotada (DFS para seguir flujos multi-step primero)
    frontier: list[tuple[list[dict], str, dict | None]] = [([], "", None)]
    while frontier and len(nodes) < max_states:
        path, parent_id, via = frontier.pop()
        node = _materialize(path, parent_id, via)
        if node is None:
            continue
        if len(path) >= max_depth:
            node.stop_reason = "max_depth"
            continue
        # enumerar hijos en una ventana fresca ya descartada; re-materializar
        # solo para enumerar seria costoso: re-usamos el nodo recien capturado
        # abriendo una ventana efimera.
        qapp2, win2 = _instantiate(app_key, modo)
        try:
            _replay_path(win2, path, qapp2)
            child_actions = _enumerate_safe_actions(
                win2, path, opts, log_omitted=_log_omit)
        finally:
            _close_window(win2)
        # para evitar explosion, limitamos pushes y priorizamos diversidad
        for action in child_actions:
            child_path = path + [action]
            frontier.append((child_path, node.node_id, action))
        if len(frontier) > max_states * 6:
            # podamos la frontera conservando los caminos mas profundos
            frontier.sort(key=lambda x: len(x[0]))
            frontier = frontier[-max_states * 3:]

    graph = {
        "app": app_key, "theme": theme,
        "nodes": [_node_summary(n) for n in nodes],
        "edges": edges,
        "omitted_actions": omitted,
        "crawl_opts": {"max_states": max_states, "max_depth": max_depth},
        "discovered_count": len(nodes),
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
    if strict:
        return {"max_states": _STRICT_MAX_STATES,
                "max_depth": _STRICT_MAX_DEPTH,
                "max_branch": _DEFAULT_MAX_BRANCH}
    return {"max_states": _DEFAULT_MAX_STATES,
            "max_depth": _DEFAULT_MAX_DEPTH,
            "max_branch": _DEFAULT_MAX_BRANCH}


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
    """Crawl rapido para ubicar el path que produce un screen_id dado."""
    nodes, _ = crawl_app(app_key, modo, opts, out_dirs,
                         log=lambda *a, **k: None)
    for n in nodes:
        if n.screen_id == screen_id:
            return DiscoveredNode(node_id=n.node_id, screen_id=n.screen_id,
                                  app=n.app, theme=n.theme, label=n.label,
                                  path=n.path)
    return None


def _cmd_capture(args) -> int:
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    _ensure_isolated_db()
    themes = _theme_map(args.theme)
    screen_id = _resolve_screen(args.app, args.screen)
    app_key = screen_id.split(":")[0]
    opts = _crawl_opts(False)
    print(f"[SENTINEL] capture targeted (sin resultado general)")
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
    if getattr(args, "list", False):
        return _cmd_list(args)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 1
    return int(func(args))


if __name__ == "__main__":
    raise SystemExit(main())
