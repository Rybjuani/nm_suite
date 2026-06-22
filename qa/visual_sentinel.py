"""qa/visual_sentinel.py — Auditor visual canonico, independiente y autodescubrible.

Reemplaza conceptualmente a qa/capture_v8.py y qa/runtime_live_probe.py como
herramienta principal de auditoria visual, PERO sin depender de ellos: no los
importa, no reusa sus recetas manuales ni su lista de pantallas. El Sentinel
descubre la UI navegando la app real (registro de modulos de la propia app +
introspeccion en vivo del arbol Qt: QStackedWidget, QTabWidget/QTabBar, NMTabs,
NMSegmentedPanel, NMPanelTabs, botones clickeables, dialogs) y aplica contratos
globales reutilizables sobre TODAS las pantallas descubiertas.

Disenio honesto:
- ``audit --all`` es el UNICO modo que puede emitir resultado general.
- ``capture``/``inspect --screen`` nunca imprimen PASS general; marcan
  TARGETED_INSPECTION_ONLY y GENERAL_AUDIT_NOT_RUN.
- Una pantalla nueva descubierta se marca NEW_STATE_UNREVIEWED y bloquea el
  cierre general hasta revision humana. El Sentinel NUNCA autoaprueba.
- El cierre general se bloquea con FAIL si hay NEW_STATE_UNREVIEWED,
  STALE_STATE, MISSING_EVIDENCE, FALLBACK, DUPLICATE_SUSPECT, P0 o P1.

Dependencias (ya presentes en el venv): PyQt6, Pillow, numpy, scikit-image,
imagehash, PyYAML, rich, networkx. No usa cv2, jinja2, torch ni lpips.

Uso:
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py --list
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py audit --all --theme both
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py audit --app suite --theme light
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py capture --screen <id> --theme both
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py inspect --screen <id> --theme light
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py propose-baselines
    .venv\\Scripts\\python.exe qa\\visual_sentinel.py approve-baseline --screen <id> --theme <theme>

Salida: qa/_visual_sentinel/latest/{manifest,findings,coverage,index.html,...}
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
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
_SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
_BLOCKING_SEVERITIES = {"P0", "P1"}
_BLOCKING_FLAGS = {
    "NEW_STATE_UNREVIEWED",
    "STALE_STATE",
    "MISSING_EVIDENCE",
    "FALLBACK",
    "DUPLICATE_SUSPECT",
}

# Umbrales de contenido (PNG casi todo blanco/negro o sin varianza tonal).
_BLANK_MEAN_HI = 0.985
_BLANK_MEAN_LO = 0.015
_FLAT_STDDEV = 0.004
# Distancia Hamming perceptual (imagehash phash) bajo la cual dos estados
# distintos se consideran duplicados sospechosos.
_DUP_PHASH_DISTANCE = 5
# Solape claro: interseccion >= 45% del widget menor.
_OVERLAP_MIN_RATIO = 0.45


# ═══════════════════════════════════════════════════════════════════════════
# Utilidades genericas
# ═══════════════════════════════════════════════════════════════════════════

def _norm_text(value: Any) -> str:
    folded = unicodedata.normalize("NFKD", str(value or ""))
    asciiish = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(asciiish.casefold().split())


def _short_theme(modo: str) -> str:
    return "light" if "light" in (modo or "") else "dark"


def _safe_name(screen_id: str) -> str:
    """Convierte un screen_id en un nombre de archivo valido en Windows
    (los ``:`` son ilegales en nombres de archivo)."""
    return screen_id.replace(":", "__")


def _theme_map(theme: str) -> list[str]:
    if theme == "both":
        return ["light_hybrid", "dark_hybrid"]
    if theme == "light":
        return ["light_hybrid"]
    if theme == "dark":
        return ["dark_hybrid"]
    raise SystemExit(f"--theme invalido: {theme}")


def _parse_res(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def _git_value(args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=_PROJ, capture_output=True, text=True,
            timeout=5, check=False,
        )
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


def _drain(qapp, cycles: int = 8, pause: float = 0.03) -> None:
    from PyQt6.QtCore import QCoreApplication, QEvent
    for _ in range(cycles):
        qapp.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        time.sleep(pause)
        qapp.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _ensure_isolated_db() -> Path | None:
    """Garantiza una DB SQLite temporal aislada para la corrida."""
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


# ═══════════════════════════════════════════════════════════════════════════
# Modelo de datos del Sentinel
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class StateSpec:
    """Un estado navegable descubierto."""
    app: str
    surface: str            # home / animo / dbt / pacientes / detalle / ...
    substate: str = ""      # "" para base; "tab-1", "plan-tab-2", ...
    label: str = ""
    enter_actions: list[dict] = field(default_factory=list)

    @property
    def screen_id(self) -> str:
        parts = [self.app, self.surface]
        if self.substate:
            parts.append(self.substate)
        return ":".join(parts)


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


@dataclass
class Finding:
    contract_id: str
    severity: str           # P0/P1/P2/P3
    flag: str               # NEW_STATE_UNREVIEWED / BLANK_OR_FLAT / ...
    screen_id: str
    theme: str
    message: str
    detail: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# Instanciacion de apps (aislada por tema/resolucion)
# ═══════════════════════════════════════════════════════════════════════════

_APP_SPEC = {
    "suite": {"module": "app.main_qt", "class": "NeuroMoodApp", "settings": "Suite"},
    "hub": {"module": "hub.main_qt", "class": "NeuroMoodHub", "settings": "Hub"},
}


def _instantiate(app_key: str, modo: str, res: str):
    """Crea una ventana fresca de la app en modo QA aislado."""
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
    _drain(qapp, cycles=8)
    return qapp, win


def _close_window(win) -> None:
    from PyQt6.QtWidgets import QApplication
    try:
        if win is not None:
            win.close()
            win.deleteLater()
    except Exception:
        pass
    qapp = QApplication.instance()
    if qapp is not None:
        for tl in QApplication.topLevelWidgets():
            if tl is not win and tl.isVisible():
                try:
                    tl.close()
                    tl.deleteLater()
                except Exception:
                    pass
        _drain(qapp, cycles=4)


# ═══════════════════════════════════════════════════════════════════════════
# Descubrimiento automatico de estados (BFS estructural sobre la app real)
# ═══════════════════════════════════════════════════════════════════════════

def _discover_states(app_key: str, modo: str) -> list[StateSpec]:
    """Descubre estados navegables SIN recetas manuales.

    Fuentes legitimas (propias de la app, no de capture_v8/runtime):
      * Suite: registro canonico ``app.main_qt._MODULE_MAP`` + home.
      * Hub: vistas declaradas en ``win._nav_views()`` + detalle de paciente.
    Sub-estados: introspeccion en vivo de contenedores de tabs/segmentados
    (QTabBar, QTabWidget, NMTabs, NMSegmentedPanel, NMPanelTabs) dentro de
    cada superficie. No se reusa ninguna lista de pantallas de V8/runtime.
    """
    states: list[StateSpec] = []
    qapp, win = _instantiate(app_key, modo, _RESOLUTION)
    try:
        if app_key == "suite":
            states.append(StateSpec(app="suite", surface="home", label="Home"))
            try:
                from app.main_qt import _MODULE_MAP as mod_map
            except Exception:
                mod_map = {}
            for mid in mod_map:
                states.append(StateSpec(
                    app="suite", surface=mid,
                    label=f"Modulo {mid}",
                    enter_actions=[{"kind": "open_module", "id": mid}],
                ))
        else:  # hub
            for vid in _hub_nav_views(win):
                states.append(StateSpec(
                    app="hub", surface=vid,
                    label=f"Hub {vid}",
                    enter_actions=[{"kind": "nav", "id": vid}],
                ))
            states.append(StateSpec(
                app="hub", surface="detalle",
                label="Detalle de paciente",
                enter_actions=[{"kind": "select_first_patient"}],
            ))

        # Sub-estados por introspeccion de tabs dentro de cada superficie.
        expanded: list[StateSpec] = []
        for st in states:
            _apply_enter(win, st, qapp)
            expanded.append(st)
            for sub in _discover_tab_substates(win, st, qapp):
                expanded.append(sub)
            # Volver a home/base antes de la siguiente superficie para no
            # contaminar el estado de modulos stateful.
            _reset_to_base(win, app_key, qapp)
        states = expanded
    finally:
        _close_window(win)
    return states


def _hub_nav_views(win) -> list[str]:
    views: list[str] = []
    try:
        nav = win._nav_views()
        for vid, w in nav.items():
            if w is not None:
                views.append(vid)
    except Exception:
        pass
    if not views:
        views = ["pacientes"]
    return views


def _apply_enter(win, spec: StateSpec, qapp) -> None:
    for act in spec.enter_actions:
        kind = act.get("kind")
        if kind == "open_module" and hasattr(win, "_open_module"):
            try:
                win._open_module(act["id"])
            except Exception:
                pass
        elif kind == "nav" and hasattr(win, "_on_nav"):
            try:
                win._on_nav(act["id"])
            except Exception:
                pass
        elif kind == "select_first_patient":
            _hub_select_first_patient(win)
        elif kind == "set_tab":
            _apply_tab_action(win, act)
        _drain(qapp, cycles=6)


def _reset_to_base(win, app_key: str, qapp) -> None:
    try:
        if app_key == "suite" and hasattr(win, "_go_home"):
            win._go_home()
        elif app_key == "hub" and hasattr(win, "_back_to_pacientes"):
            win._back_to_pacientes()
    except Exception:
        pass
    _drain(qapp, cycles=4)


def _hub_select_first_patient(win) -> None:
    pacientes = list(getattr(win, "_pacientes", None) or [])
    if not pacientes:
        try:
            from shared.visual_qa import hub_patients
            pacientes = hub_patients()
        except Exception:
            pacientes = []
    if pacientes and hasattr(win, "_select_patient"):
        p = pacientes[0]
        try:
            win._select_patient(p.get("patient_id", ""), p.get("patient_name", ""))
        except Exception:
            pass


def _discover_tab_substates(win, parent: StateSpec, qapp) -> list[StateSpec]:
    """Introspecta contenedores de tabs visibles y genera un sub-estado por
    indice no-default. Restaura el indice original al terminar."""
    found: list[StateSpec] = []
    containers = _find_tab_containers(win)
    for c_idx, container in enumerate(containers):
        info = _tab_container_info(container)
        if not info or info["count"] <= 1:
            continue
        original = info["current"]
        for i in range(info["count"]):
            if i == original:
                # el indice default ya esta cubierto por el estado padre
                continue
            if i != original:
                _set_tab_index(container, i, info["kind"])
                _drain(qapp, cycles=5)
                sub_id = f"{info['kind']}{c_idx}-tab-{i}"
                label = info["labels"][i] if i < len(info["labels"]) else sub_id
                found.append(StateSpec(
                    app=parent.app, surface=parent.surface,
                    substate=sub_id, label=f"{parent.label} > {label}",
                    enter_actions=parent.enter_actions + [
                        {"kind": "set_tab", "container_index": c_idx,
                         "tab_index": i, "kind_": info["kind"]},
                    ],
                ))
        _set_tab_index(container, original, info["kind"])
        _drain(qapp, cycles=3)
    return found


def _find_tab_containers(root):
    """Localiza contenedores de tabs en el arbol visible.

    Evita contar dos veces un QTabWidget y su QTabBar interno embebido: si un
    QTabBar pertenece a un QTabWidget ya incluido, se saltea.
    """
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
    seen_ids = set()
    for w in root.findChildren(QWidget):
        try:
            if sip_deleted(w) or not w.isVisible():
                continue
        except Exception:
            continue
        if isinstance(w, (QTabBar, QTabWidget, NMTabs, NMSegmentedPanel, NMPanelTabs)):
            if id(w) in seen_ids:
                continue
            raw.append(w)
            seen_ids.add(id(w))

    # QTabBar cuyo parent es un QTabWidget ya listado -> duplicado.
    owned_tabbars = set()
    for c in raw:
        if isinstance(c, QTabWidget):
            try:
                tb = c.tabBar()
                owned_tabbars.add(id(tb))
            except Exception:
                pass
    return [c for c in raw if id(c) not in owned_tabbars]


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
            # NMTabs / NMSegmentedPanel / NMPanelTabs (API custom)
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


def _set_tab_index(container, index: int, kind: str) -> None:
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


def _apply_tab_action(win, act: dict) -> None:
    containers = _find_tab_containers(win)
    c_idx = act.get("container_index", 0)
    if c_idx >= len(containers):
        return
    _set_tab_index(containers[c_idx], act.get("tab_index", 0), act.get("kind_", ""))


# ═══════════════════════════════════════════════════════════════════════════
# Captura de evidencia por estado
# ═══════════════════════════════════════════════════════════════════════════

def sip_deleted(obj) -> bool:
    try:
        from PyQt6 import sip
        return sip.isdeleted(obj)
    except Exception:
        return False


def _capture_state(win, qapp, spec: StateSpec, modo: str, out_dirs: dict) -> CapturedState:
    screen_id = spec.screen_id
    theme = _short_theme(modo)
    safe = _safe_name(screen_id)
    png_path = out_dirs["screenshots"] / f"{safe}-{theme}.png"
    tree_path = out_dirs["widget_trees"] / f"{safe}-{theme}.json"

    _apply_enter(win, spec, qapp)
    _drain(qapp, cycles=8)

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

    return CapturedState(
        screen_id=screen_id, app=spec.app, theme=theme, label=spec.label,
        png_path=png_path, tree_path=tree_path, sha256=sha256, phash=phash,
        structural_hash=structural_hash, visual_metrics=metrics,
        widget_tree=widget_tree, texts=texts, clickable=clickable,
        scrollbars=scrollbars, tabs=tabs, buttons=buttons, crops=crops,
        geometry=geo, error=error,
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
        return {
            "gray_mean": round(stat.mean[0] / 255.0, 4),
            "gray_stddev": round(stat.stddev[0] / 255.0, 4),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _build_widget_tree(root, depth: int = 0, max_depth: int = 12, win_ref=None,
                      in_scroll: bool = False) -> dict:
    """Arbol Qt serializable (tipo, objectName, texto, geometria, flags).

    ``geometry`` es relativa al parent (Qt nativo). ``geo_win`` es la geometria
    mapeada a la coordenada de la ventana (para checks de viewport/solape).
    ``in_scroll`` indica si el widget vive dentro de un QScrollArea (su
    contenido puede exceder el viewport legitimamente).
    """
    from PyQt6.QtWidgets import QWidget, QScrollArea
    if sip_deleted(root) or depth > max_depth:
        return {"type": type(root).__name__, "truncated": True}

    is_scroll = isinstance(root, QScrollArea)
    child_in_scroll = in_scroll or is_scroll

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

    text = ""
    for attr in ("text",):
        try:
            val = getattr(root, attr)
            if callable(val):
                val = val()
            text = str(val)
            if text and text != type(root).__name__:
                break
        except Exception:
            text = ""

    visible = False
    enabled = True
    try:
        visible = bool(root.isVisible())
        enabled = bool(root.isEnabled())
    except Exception:
        pass

    node = {
        "type": type(root).__name__,
        "objectName": root.objectName() if hasattr(root, "objectName") else "",
        "text": text[:200],
        "geometry": _rect(root),
        "geo_win": _win_rect(root),
        "visible": visible,
        "enabled": enabled,
        "clickable": _is_clickable(root),
        "in_scroll": in_scroll,
        "children": [],
    }
    try:
        node["children"] = [_build_widget_tree(c, depth + 1, max_depth, win_ref,
                                                in_scroll=child_in_scroll)
                            for c in root.children() if isinstance(c, QWidget)
                            and not sip_deleted(c)]
    except Exception:
        pass
    return node


def _is_clickable(w) -> bool:
    try:
        from PyQt6.QtWidgets import (
            QPushButton, QToolButton, QCheckBox, QRadioButton, QTabBar,
            QTabWidget, QCommandLinkButton,
        )
        if isinstance(w, (QPushButton, QToolButton, QCheckBox, QRadioButton,
                          QCommandLinkButton, QTabBar, QTabWidget)):
            return True
        cls = type(w).__name__
        if cls in {"NMButton", "NMButtonOutline", "NMPlayButton", "NMTabs",
                   "NMSegmentedPanel", "NMPanelTabs", "NMSegmentedChoice",
                   "NMModule", "NMCard", "NMPatientRowPremium", "NMCustomCheck"}:
            return True
        if hasattr(w, "clicked"):
            return True
    except Exception:
        pass
    return False


def _walk_tree(node: dict) -> Iterable[dict]:
    yield node
    for c in node.get("children", []) or []:
        yield from _walk_tree(c)


def _collect_texts(tree: dict) -> list[str]:
    out = []
    for n in _walk_tree(tree):
        t = (n.get("text") or "").strip()
        if n.get("visible") and t:
            out.append(t)
    return out


def _collect_clickable(tree: dict) -> list[dict]:
    out = []
    for n in _walk_tree(tree):
        if n.get("visible") and n.get("clickable"):
            out.append({
                "type": n.get("type"), "text": n.get("text"),
                "objectName": n.get("objectName"), "geometry": n.get("geometry"),
                "enabled": n.get("enabled"),
            })
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
                rng = w.minimum(), w.maximum()
                page = w.pageStep()
                out.append({
                    "orientation": "vertical" if bar.name == "Vertical" else "horizontal",
                    "min": rng[0], "max": rng[1], "pageStep": page,
                    "visible_range": rng[1] - rng[0],
                    "geometry": _geo_dict(w),
                })
            except Exception:
                continue
        for sa in root.findChildren(QScrollArea):
            if sip_deleted(sa) or not sa.isVisible():
                continue
            out.append({
                "type": "QScrollArea", "objectName": sa.objectName(),
                "geometry": _geo_dict(sa),
            })
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
                for i in range(info["count"]):
                    rects.append(_geo_dict_rect(c.tabRect(i)))
        except Exception:
            pass
        out.append({
            "type": info["kind"], "count": info["count"],
            "current": info["current"], "labels": info["labels"],
            "tabRects": rects, "geometry": _geo_dict(c),
        })
    return out


def _collect_buttons(tree: dict) -> list[dict]:
    out = []
    for n in _walk_tree(tree):
        cls = n.get("type", "")
        if n.get("visible") and ("Button" in cls or cls in {"NMPlayButton"}):
            out.append({
                "type": cls, "text": n.get("text"), "enabled": n.get("enabled"),
                "objectName": n.get("objectName"), "geometry": n.get("geometry"),
                "hasIcon": _has_icon_flag(n),
            })
    return out


def _has_icon_flag(node: dict) -> bool:
    return bool(node.get("_icon"))


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
        parts.append(
            f"{n.get('type')}|{n.get('objectName','')}|{g.get('w',0)}x{g.get('h',0)}"
            f"|{(n.get('text') or '')[:40]}"
        )
    h = hashlib.sha256("\n".join(sorted(parts)).encode("utf-8")).hexdigest()
    return h[:16]


def _make_crops(win, qapp, regions: list[dict], screen_id: str, theme: str,
                out_dirs: dict) -> list[dict]:
    """Recorta regiones importantes (tabs/scrollbars/clickable destacados)."""
    crops = []
    try:
        from PyQt6.QtGui import QPixmap
        pm = win.grab()
        full = pm.toImage()
        # limitar a pocas regiones para no explotar evidencia
        made = 0
        for reg in regions[:6]:
            g = reg.get("geometry") or {}
            w_, h_ = g.get("w", 0), g.get("h", 0)
            if w_ <= 0 or h_ <= 0:
                continue
            name = f"{screen_id}-{theme}-crop-{made}.png"
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


# ═══════════════════════════════════════════════════════════════════════════
# Contratos visuales globales
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
            if not _contract_applies(c, st):
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
                    message=r.get("message", ""),
                    detail=r.get("detail", {}),
                ))
    return findings


def _contract_applies(contract: dict, st: CapturedState) -> bool:
    apps = contract.get("apps")
    if apps and st.app not in apps:
        return False
    surfaces = contract.get("surfaces")
    if surfaces and st.surface not in surfaces:
        return False
    return True


# --- Implementacion de cada check ------------------------------------------

def _check_blank_or_flat(st: CapturedState, c: dict, states, reg) -> list[dict]:
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


def _check_duplicate(st: CapturedState, c: dict, states, reg) -> list[dict]:
    if not st.phash:
        return []
    out = []
    for other in states:
        if other is st or other.theme != st.theme or not other.phash:
            continue
        if other.screen_id == st.screen_id:
            continue
        dist = _phash_distance(st.phash, other.phash)
        if dist <= c.get("params", {}).get("max_distance", _DUP_PHASH_DISTANCE):
            out.append({"flag": "DUPLICATE_SUSPECT",
                        "message": (f"Estado visualmente duplicado con "
                                    f"{other.screen_id} (phash distance={dist})."),
                        "detail": {"other": other.screen_id, "distance": dist}})
    # duplicado exacto por sha256
    if st.sha256:
        for other in states:
            if other is st or other.theme != st.theme:
                continue
            if other.screen_id != st.screen_id and other.sha256 == st.sha256:
                out.append({"flag": "DUPLICATE_SUSPECT",
                            "message": (f"Hash PNG identico a {other.screen_id}; "
                                        "estado probablemente no alcanzado."),
                            "detail": {"other": other.screen_id, "sha256": st.sha256}})
    return out


def _phash_distance(a: str, b: str) -> int:
    try:
        import imagehash
        ha = imagehash.hex_to_hash(a)
        hb = imagehash.hex_to_hash(b)
        return int(ha - hb)
    except Exception:
        return 64


def _geo_for_checks(node: dict) -> dict | None:
    """Geometria preferida para checks de viewport/solape: coordenadas
    mapeadas a la ventana (geo_win). Cae a ``geometry`` si no existe."""
    gw = node.get("geo_win")
    if isinstance(gw, dict) and gw.get("w", 0) > 0:
        return gw
    g = node.get("geometry")
    return g if isinstance(g, dict) else None


def _check_out_of_viewport(st: CapturedState, c: dict, states, reg) -> list[dict]:
    vw = st.geometry.get("w", 960)
    vh = st.geometry.get("h", 600)
    tol = c.get("params", {}).get("tolerance", 2)
    out = []
    for n in _walk_tree(st.widget_tree):
        if not n.get("visible"):
            continue
        # El contenido dentro de un QScrollArea puede exceder el viewport
        # legitimamente (se desplaza); no se flagea como fuera de viewport.
        if n.get("in_scroll"):
            continue
        g = _geo_for_checks(n)
        if not g:
            continue
        x, y, w_, h_ = g.get("x", 0), g.get("y", 0), g.get("w", 0), g.get("h", 0)
        if w_ <= 0 or h_ <= 0:
            continue
        # fuera si esta completamente fuera del viewport
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


def _check_overlap(st: CapturedState, c: dict, states, reg) -> list[dict]:
    """Solape claro entre widgets visibles con contenido, usando coordenadas de
    ventana. Filtra anidamiento padre/hijo (si el centro de uno esta dentro del
    otro, es nesting, no overlap)."""
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
        rects.append((g.get("x", 0), g.get("y", 0), w_, h_,
                      g.get("x", 0) + w_ / 2.0, g.get("y", 0) + h_ / 2.0, n))
    out = []
    min_ratio = c.get("params", {}).get("min_overlap_ratio", _OVERLAP_MIN_RATIO)

    def _containment(ax, ay, aw, ah, bx, by, bw, bh) -> float:
        """Que fraccion del rect A esta contenido en B (0..1)."""
        ix0, iy0 = max(ax, bx), max(ay, by)
        ix1, iy1 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
        iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
        area_a = aw * ah
        if area_a <= 0:
            return 0.0
        return (iw * ih) / area_a

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
            # Filtrar anidamiento real padre/hijo: uno de los rects esta casi
            # totalmente contenido en el otro (>= 90%). No es solape, es nesting.
            if (_containment(a[0], a[1], a[2], a[3], b[0], b[1], b[2], b[3]) >= 0.9 or
                    _containment(b[0], b[1], b[2], b[3], a[0], a[1], a[2], a[3]) >= 0.9):
                continue
            out.append({"flag": "WIDGET_OVERLAP",
                        "message": (f"Solape claro entre {a[6].get('type')} "
                                    f"'{(a[6].get('text') or '')[:20]}' y "
                                    f"{b[6].get('type')} "
                                    f"'{(b[6].get('text') or '')[:20]}' "
                                    f"({inter/small:.0%} del menor)"),
                        "detail": {"a": a[6].get("type"), "b": b[6].get("type"),
                                   "ratio": round(inter / small, 2)}})
            if len(out) >= 20:
                break
    return out


def _check_elided_text(st: CapturedState, c: dict, states, reg) -> list[dict]:
    out = []
    for n in _walk_tree(st.widget_tree):
        cls = n.get("type", "")
        if cls == "NMElidedLabel" and n.get("visible"):
            out.append({"flag": "ELIDED_PRIMARY_TEXT",
                        "message": (f"NMElidedLabel visible: posible texto cortado "
                                    f"'{(n.get('text') or '')[:40]}'"),
                        "detail": {"widget": cls, "text": n.get("text")}})
    return out


def _surface_of(st: CapturedState) -> str:
    parts = st.screen_id.split(":")
    return parts[1] if len(parts) >= 2 else st.screen_id


def _check_unexpected_scroll_legal(st: CapturedState, c: dict, states, reg) -> list[dict]:
    # Scrollbars internas en legales/onboarding consideradas sospechosas.
    surface = _surface_of(st).lower()
    keywords = ("onboarding", "legal", "consent", "privacy")
    if not any(k in surface for k in keywords):
        return []
    out = []
    for sb in st.scrollbars:
        if sb.get("type") == "QScrollArea":
            continue
        if sb.get("visible_range", 0) and sb.get("max", 0) > sb.get("pageStep", 0):
            out.append({"flag": "UNEXPECTED_LEGAL_SCROLLBAR",
                        "message": (f"Scrollbar interna inesperada en {surface}: "
                                    f"range={sb.get('visible_range')}"),
                        "detail": sb})
    # checkbox legal dentro de scroll area
    out.extend(_find_legal_checkbox_in_scroll(st))
    return out


def _find_legal_checkbox_in_scroll(st: CapturedState) -> list[dict]:
    from PyQt6.QtWidgets import QScrollArea, QCheckBox
    out = []
    try:
        # st no retiene la ventana; este check se corre durante la captura via
        # arbol: buscamos nodos QScrollArea que contengan QCheckBox/NMCustomCheck.
        for n in _walk_tree(st.widget_tree):
            if n.get("type") in {"QCheckBox", "NMCustomCheck"} and n.get("visible"):
                # heuristica: texto legal/consentimiento
                t = _norm_text(n.get("text"))
                if any(k in t for k in ("consent", "terminos", "privacidad", "acepto", "legal")):
                    out.append({"flag": "LEGAL_CHECKBOX_IN_SCROLL_AREA",
                                "message": (f"Checkbox legal detectado: "
                                            f"'{(n.get('text') or '')[:40]}'"),
                                "detail": {"widget": n.get("type"), "text": n.get("text")}})
    except Exception:
        pass
    return out


_SEMANTIC_CTAS = ("exportar pdf", "resumen ia", "completar con ia", "completar con ia")


def _check_cta_missing_icon(st: CapturedState, c: dict, states, reg) -> list[dict]:
    out = []
    for b in st.buttons:
        t = _norm_text(b.get("text"))
        if not t:
            continue
        if any(k in t for k in _SEMANTIC_CTAS):
            if not b.get("hasIcon"):
                out.append({"flag": "CTA_SEMANTIC_MISSING_ICON",
                            "message": (f"CTA semantico sin icono: '{b.get('text')}'"),
                            "detail": b})
    return out


def _check_oversized_tabs(st: CapturedState, c: dict, states, reg) -> list[dict]:
    out = []
    vh = st.geometry.get("h", 600)
    params = c.get("params", {})
    max_ratio = params.get("max_tab_to_window_height_ratio", 0.18)
    for tab in st.tabs:
        for rect in tab.get("tabRects", []):
            th = rect.get("h", 0)
            if vh > 0 and th / vh > max_ratio:
                out.append({"flag": "OVERSIZED_SECONDARY_TAB",
                            "message": (f"Tab secundaria gigante: alto {th}px "
                                        f"({th/vh:.0%} de la ventana {vh}px)"),
                            "detail": {"rect": rect, "type": tab.get("type")}})
    return out


def _check_long_tab_labels(st: CapturedState, c: dict, states, reg) -> list[dict]:
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


def _check_new_state(st: CapturedState, c: dict, states, reg) -> list[dict]:
    key = f"{st.screen_id}@{st.theme}"
    if key not in reg:
        return [{"flag": "NEW_STATE_UNREVIEWED",
                 "message": (f"Estado descubierto sin baseline aprobada: {key}. "
                             "Requiere revision humana antes de cerrar la auditoria."),
                 "detail": {"screen_id": st.screen_id, "theme": st.theme}}]
    return []


def _check_progress_dot_error(st: CapturedState, c: dict, states, reg) -> list[dict]:
    # Heuristica sobre textos/colores del arbol: NMProgressBar / NMRingPulse con
    # clase indicadora de error. Sin acceso al color en el arbol serializado,
    # emitimos solo si el estado NO es de error y aparece widget de progreso
    # junto a marcadores rojos. Conservativo (P2).
    surface = _surface_of(st).lower()
    is_error_state = any(k in surface for k in ("error", "fail", "danger"))
    if is_error_state:
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


_CHECKS: dict[str, Callable[..., list[dict]]] = {
    "blank_or_flat": _check_blank_or_flat,
    "duplicate_suspect": _check_duplicate,
    "out_of_viewport": _check_out_of_viewport,
    "widget_overlap": _check_overlap,
    "elided_primary_text": _check_elided_text,
    "unexpected_scrollbar_in_legal": _check_unexpected_scroll_legal,
    "semantic_cta_missing_icon": _check_cta_missing_icon,
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
        fp = _PROPOSED_DIR / f"{st.screen_id.replace(':', '_')}-{st.theme}.json"
        fp.write_text(json.dumps({
            "screen_id": st.screen_id, "theme": st.theme,
            "label": st.label, "sha256": st.sha256, "phash": st.phash,
            "structural_hash": st.structural_hash,
            "proposed_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        n += 1
    return n


def _approve_baseline(screen_id: str, theme: str, reason: str) -> dict:
    reg = _load_registry()
    key = f"{screen_id}@{theme}"
    prop = _PROPOSED_DIR / f"{screen_id.replace(':', '_')}-{theme}.json"
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
    approved = _APPROVED_DIR / f"{screen_id.replace(':', '_')}-{theme}.json"
    _APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    approved.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        prop.unlink()
    except OSError:
        pass
    return {"ok": True, "entry": entry}


# ═══════════════════════════════════════════════════════════════════════════
# Cobertura: estados nuevos / stale / obsoletos
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
    """Detecta referencias obsoletas a recetas/pantallas de V8/runtime en la
    metadata propia del Sentinel (registry de baselines)."""
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


def _write_html_report(out_dirs: dict, states: list[CapturedState],
                       findings: list[Finding], coverage: dict,
                       result: str, general_complete: bool, run_meta: dict) -> Path:
    by_sev = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
    findings_by_screen: dict[str, list[Finding]] = {}
    for f in findings:
        findings_by_screen.setdefault(f.screen_id, []).append(f)

    rel = lambda p: os.path.relpath(p, out_dirs["latest"])  # noqa: E731

    parts: list[str] = []
    parts.append("<!doctype html><html lang='es'><head><meta charset='utf-8'>")
    parts.append("<title>Visual Sentinel — Reporte</title>")
    parts.append("<style>")
    parts.append(
        "body{font-family:system-ui,Segoe UI,Roboto,sans-serif;margin:0;background:#0e1116;color:#e6edf3}"
        "h1,h2,h3{color:#fff} .wrap{max-width:1200px;margin:0 auto;padding:24px}"
        ".card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;margin:12px 0}"
        ".pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600;margin-right:4px}"
        ".pass{background:#1a7f37;color:#fff}.fail{background:#da3633;color:#fff}"
        ".p0{background:#da3633}.p1{background:#db6d28}.p2{background:#58a6ff}.p3{background:#6e7681}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}"
        ".thumb{background:#0d1117;border:1px solid #30363d;border-radius:8px;overflow:hidden}"
        ".thumb img{width:100%;height:auto;display:block}.thumb .meta{padding:8px;font-size:12px}"
        ".flag{font-family:ui-monospace,SFMono-Regular,monospace;font-size:11px;color:#f0883e}"
        "details{margin:4px 0}summary{cursor:pointer;font-weight:600}"
        "ul{margin:4px 0 4px 18px}a{color:#58a6ff}small{color:#8b949e}"
        "ul.tree{font-family:ui-monospace,monospace;font-size:12px;white-space:pre-wrap}"
    )
    parts.append("</style></head><body><div class='wrap'>")
    parts.append("<h1>Visual Sentinel</h1>")
    parts.append(f"<small>Run: {run_meta.get('generated_at','')} · commit {run_meta.get('git',{}).get('short_head','')}</small>")

    parts.append("<div class='card'>")
    badge = "pass" if result == "PASS" else "fail"
    parts.append(f"<span class='pill {badge}'>VISUAL_SENTINEL_RESULT: {result}</span>")
    parts.append(f"<span class='pill {('pass' if general_complete else 'fail')}'>"
                 f"GENERAL_AUDIT_COMPLETE: {'YES' if general_complete else 'NO'}</span>")
    parts.append("</div>")

    parts.append("<div class='card'><h2>Cobertura</h2><ul>")
    parts.append(f"<li>Estados descubiertos: <b>{coverage.get('discovered_states',0)}</b></li>")
    parts.append(f"<li>Estados capturados: <b>{coverage.get('captured_states',0)}</b></li>")
    parts.append(f"<li>Estados nuevos sin revisar: <b>{coverage.get('new_count',0)}</b></li>")
    parts.append(f"<li>Estados stale: <b>{coverage.get('stale_count',0)}</b></li>")
    parts.append("</ul></div>")

    parts.append("<div class='card'><h2>Hallazgos por severidad</h2>")
    for sev in ("P0", "P1", "P2", "P3"):
        parts.append(f"<span class='pill {sev.lower()}'>{sev}: {by_sev.get(sev,0)}</span>")
    parts.append("</div>")

    parts.append("<div class='card'><h2>Galeria de pantallas</h2><div class='grid'>")
    for st in sorted(states, key=lambda s: (s.app, s.screen_id, s.theme)):
        sf = findings_by_screen.get(st.screen_id, [])
        flags = sorted({f.flag for f in sf})
        rel_png = rel(st.png_path)
        rel_tree = rel(st.tree_path)
        parts.append("<div class='thumb'>")
        parts.append(f"<a href='{_html_escape(rel_png)}'><img src='{_html_escape(rel_png)}' alt='{_html_escape(st.screen_id)}'></a>")
        parts.append("<div class='meta'>")
        parts.append(f"<b>{_html_escape(st.screen_id)}</b> "
                     f"<small>[{_html_escape(st.theme)}]</small><br>")
        if flags:
            parts.append("<span class='flag'>" + ", ".join(_html_escape(f) for f in flags) + "</span><br>")
        parts.append(f"<small><a href='{_html_escape(rel_tree)}'>arbol Qt</a> · "
                     f"textos: {len(st.texts)} · botones: {len(st.buttons)} · "
                     f"tabs: {len(st.tabs)}</small>")
        parts.append("</div></div>")
    parts.append("</div></div>")

    parts.append("<div class='card'><h2>Hallazgos por componente</h2>")
    by_contract: dict[str, list[Finding]] = {}
    for f in findings:
        by_contract.setdefault(f.contract_id, []).append(f)
    if not by_contract:
        parts.append("<p>Sin hallazgos.</p>")
    for cid, fs in sorted(by_contract.items()):
        parts.append(f"<details><summary>{_html_escape(cid)} ({len(fs)})</summary><ul>")
        for f in fs[:50]:
            parts.append(
                f"<li><span class='pill {f.severity.lower()}'>{f.severity}</span> "
                f"<span class='flag'>{_html_escape(f.flag)}</span> "
                f"{_html_escape(f.screen_id)}[{_html_escape(f.theme)}]: "
                f"{_html_escape(f.message)}</li>"
            )
        parts.append("</ul></details>")
    parts.append("</div>")

    parts.append("<div class='card'><h2>Arboles Qt (colapsable)</h2>")
    for st in sorted(states, key=lambda s: s.screen_id):
        parts.append(f"<details><summary>{_html_escape(st.screen_id)} [{_html_escape(st.theme)}]</summary>")
        parts.append("<ul class='tree'>" + _render_tree_html(st.widget_tree, 0) + "</ul>")
        parts.append("</details>")
    parts.append("</div>")

    parts.append("<div class='card'><h2>Limitaciones honestas</h2><small>")
    parts.append(_html_escape(
        "El Sentinel es un gate visual canonico, autodescubrible y reutilizable, "
        "mucho menos propenso a falsos PASS que V8/runtime. NO es infalible: la "
        "revision semantica humana sigue siendo necesaria; algunos checks "
        "(solapes, elision, colores de progress) son heuristicos conservativos."))
    parts.append("</small></div>")

    parts.append("</div></body></html>")
    html_path = out_dirs["latest"] / "index.html"
    html_path.write_text("\n".join(parts), encoding="utf-8")
    return html_path


def _render_tree_html(node: dict, depth: int) -> str:
    if depth > 6:
        return ""
    pad = "  " * depth
    g = node.get("geometry") or {}
    vis = "V" if node.get("visible") else "-"
    click = "C" if node.get("clickable") else " "
    head = (f"{pad}{vis}{click} {node.get('type')} "
            f"#{_html_escape(node.get('objectName') or '')} "
            f"[{g.get('w',0)}x{g.get('h',0)}] "
            f"'{_html_escape((node.get('text') or '')[:50])}'")
    out = f"<li>{head}</li>"
    kids = node.get("children") or []
    if kids:
        out += "<ul>" + "".join(_render_tree_html(c, depth + 1) for c in kids[:60]) + "</ul>"
    return out


def _write_contact_sheet(states: list[CapturedState], out_dirs: dict) -> None:
    try:
        from PIL import Image
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
        from PIL import ImageDraw
        draw = ImageDraw.Draw(sheet)
        for idx, (st, im) in enumerate(thumbs):
            r, c = divmod(idx, cols)
            x, y = c * cell_w, r * cell_h
            sheet.paste(im, (x + 4, y + 4))
            draw.text((x + 4, y + cell_h - 16), f"{st.screen_id} [{st.theme}]", fill=(200, 208, 218))
        sheet.save(out_dirs["contact_sheets"] / "contact_sheet.png")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# Orquestacion de corrida
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
    dirs = {
        "latest": latest,
        "screenshots": latest / "screenshots",
        "widget_trees": latest / "widget_trees",
        "crops": latest / "crops",
        "contact_sheets": latest / "contact_sheets",
        "logs": latest / "logs",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def _persist_captured(st: CapturedState, out_dirs: dict) -> None:
    tree_data = {
        "screen_id": st.screen_id, "app": st.app, "theme": st.theme,
        "label": st.label, "geometry": st.geometry,
        "sha256": st.sha256, "phash": st.phash,
        "structural_hash": st.structural_hash,
        "visual_metrics": st.visual_metrics, "error": st.error,
        "texts": st.texts, "clickable": st.clickable,
        "scrollbars": st.scrollbars, "tabs": st.tabs,
        "buttons": st.buttons, "crops": st.crops,
        "tree": st.widget_tree,
    }
    st.tree_path.write_text(json.dumps(tree_data, indent=2, ensure_ascii=False),
                            encoding="utf-8")


def _discover_all(app_filter: str | None, themes: list[str]) -> dict[str, list[StateSpec]]:
    """Descubre estados por app/tema. La discovery se hace una sola vez por app
    (en dark) y se reusa para todos los temas: la topologia de navegacion no
    depende del tema."""
    discovered: dict[str, list[StateSpec]] = {}
    apps = ["suite", "hub"] if app_filter is None else [app_filter]
    for app_key in apps:
        try:
            discovered[app_key] = _discover_states(app_key, "dark_hybrid")
        except Exception as exc:
            print(f"[SENTINEL] discovery fallo para {app_key}: {exc}", file=sys.stderr)
            discovered[app_key] = []
    return discovered


def _run_capture(specs_by_app: dict[str, list[StateSpec]],
                 apps: list[str], themes: list[str],
                 out_dirs: dict, log) -> list[CapturedState]:
    states: list[CapturedState] = []
    for modo in themes:
        theme = _short_theme(modo)
        for app_key in apps:
            specs = specs_by_app.get(app_key, [])
            if not specs:
                continue
            log(f"  {app_key.upper()} ({len(specs)} estados) @ {theme}")
            qapp, win = _instantiate(app_key, modo, _RESOLUTION)
            try:
                for spec in specs:
                    log(f"    [{spec.screen_id}] ", end="")
                    try:
                        st = _capture_state(win, qapp, spec, modo, out_dirs)
                        _persist_captured(st, out_dirs)
                        states.append(st)
                        log("CAPTURED" if not st.error else f"WARN({st.error})")
                    except Exception as exc:
                        log(f"FAIL({exc.__class__.__name__}: {exc})")
                        safe = _safe_name(spec.screen_id)
                        states.append(CapturedState(
                            screen_id=spec.screen_id, app=app_key, theme=theme,
                            label=spec.label,
                            png_path=out_dirs["screenshots"] / f"{safe}-{theme}.png",
                            tree_path=out_dirs["widget_trees"] / f"{safe}-{theme}.json",
                            sha256=None, phash=None, structural_hash="",
                            visual_metrics={}, widget_tree={}, texts=[],
                            clickable=[], scrollbars=[], tabs=[], buttons=[],
                            crops=[], geometry={}, error=f"{exc.__class__.__name__}: {exc}",
                        ))
                    # reset entre estados para no arrastrar estado stateful
                    _reset_to_base(win, app_key, qapp)
            finally:
                _close_window(win)
    return states


def _compute_result(general_complete: bool, states: list[CapturedState],
                    findings: list[Finding], coverage: dict) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not general_complete:
        blockers.append("GENERAL_AUDIT_NOT_RUN")
    missing = [s for s in states if s.error]
    if missing:
        blockers.append("MISSING_EVIDENCE")
    for f in findings:
        if f.severity in _BLOCKING_SEVERITIES or f.flag in _BLOCKING_FLAGS:
            blockers.append(f"{f.flag}:{f.screen_id}")
    # de-duplicar conservando orden
    seen = set()
    uniq = []
    for b in blockers:
        if b not in seen:
            seen.add(b)
            uniq.append(b)
    return ("PASS" if not uniq else "FAIL"), uniq


def _console_summary(result: str, general_complete: bool, states: list[CapturedState],
                     findings: list[Finding], coverage: dict, blockers: list[str]) -> None:
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
    if blockers:
        print("BLOCKERS:")
        for b in blockers:
            print(f"  - {b}")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════
# Comandos CLI
# ═══════════════════════════════════════════════════════════════════════════

def _cmd_list() -> int:
    specs_by_app = _discover_all(None, ["dark_hybrid"])
    total = 0
    for app_key in ("suite", "hub"):
        specs = specs_by_app.get(app_key, [])
        print(f"\n=== {app_key.upper()} ({len(specs)} estados descubiertos) ===")
        for sp in specs:
            print(f"  {sp.screen_id:42s} {sp.label}")
        total += len(specs)
    print(f"\nTOTAL: {total} estados x 2 temas = {total * 2} capturas en audit --all --theme both")
    return 0


def _cmd_audit(args) -> int:
    if not args.all and not args.app:
        print("[ERROR] audit requiere --all o --app <suite|hub>.")
        return 2
    themes = _theme_map(args.theme)
    apps = ["suite", "hub"] if not args.app or args.all else [args.app]
    if args.all:
        apps = ["suite", "hub"]
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    log_path = out_dirs["logs"] / "run.log"

    def log(msg, end="\n"):
        print(msg, end=end, flush=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(msg + ("" if end == "" else "\n"))

    log(f"[SENTINEL] audit --all={args.all} apps={apps} themes={themes}")
    db = _ensure_isolated_db()
    log(f"[SENTINEL] DB aislada: {db}")

    print("Descubriendo estados (introspeccion Qt en vivo)...")
    specs_by_app = _discover_all(None if args.all else args.app, themes)
    discovered_ids = [sp.screen_id for app in apps for sp in specs_by_app.get(app, [])]

    print(f"\nCapturando {sum(len(v) for v in specs_by_app.values())} estados x {len(themes)} tema(s)...")
    states = _run_capture(specs_by_app, apps, themes, out_dirs, log)
    _write_contact_sheet(states, out_dirs)

    reg = _load_registry()
    contracts = _load_contracts()
    log(f"[SENTINEL] {len(contracts)} contratos cargados; {len(reg)} baselines aprobadas")
    findings = _run_contracts(states, contracts, reg)
    findings += _check_stale(states, reg)
    findings += _check_obsolete_recipe_refs(reg)

    coverage = _compute_coverage(states, discovered_ids, reg)
    general_complete = bool(args.all)
    result, blockers = _compute_result(general_complete, states, findings, coverage)

    run_meta = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "git": _git_metadata(),
        "command": sys.argv,
    }
    manifest = {
        "harness": "qa/visual_sentinel.py",
        "general_audit_complete": general_complete,
        "result": result,
        "blockers": blockers,
        "coverage": coverage,
        "severity_counts": {s: sum(1 for f in findings if f.severity == s)
                            for s in ("P0", "P1", "P2", "P3")},
        "discovered_state_ids": discovered_ids,
        "states": [_state_to_dict(s) for s in states],
        "run_meta": run_meta,
    }
    (out_dirs["latest"] / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dirs["latest"] / "findings.json").write_text(
        json.dumps([_finding_to_dict(f) for f in findings], indent=2, ensure_ascii=False),
        encoding="utf-8")
    (out_dirs["latest"] / "coverage.json").write_text(
        json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path = _write_html_report(out_dirs, states, findings, coverage, result,
                                   general_complete, run_meta)

    _console_summary(result, general_complete, states, findings, coverage, blockers)
    print(f"\nManifest:  {out_dirs['latest'] / 'manifest.json'}")
    print(f"Findings:  {out_dirs['latest'] / 'findings.json'}")
    print(f"Coverage:  {out_dirs['latest'] / 'coverage.json'}")
    print(f"Reporte:   {html_path}")
    return 0 if result == "PASS" else 1


def _state_to_dict(st: CapturedState) -> dict:
    return {
        "screen_id": st.screen_id, "app": st.app, "theme": st.theme,
        "label": st.label, "sha256": st.sha256, "phash": st.phash,
        "structural_hash": st.structural_hash, "visual_metrics": st.visual_metrics,
        "error": st.error, "png": str(st.png_path.relative_to(_PROJ)),
        "tree": str(st.tree_path.relative_to(_PROJ)),
        "n_texts": len(st.texts), "n_clickable": len(st.clickable),
        "n_buttons": len(st.buttons), "n_tabs": len(st.tabs),
        "n_scrollbars": len(st.scrollbars), "n_crops": len(st.crops),
    }


def _finding_to_dict(f: Finding) -> dict:
    return {
        "contract_id": f.contract_id, "severity": f.severity, "flag": f.flag,
        "screen_id": f.screen_id, "theme": f.theme, "message": f.message,
        "detail": f.detail,
    }


def _resolve_screen(app: str, screen_id: str) -> str:
    if ":" in screen_id:
        return screen_id
    return f"{app}:{screen_id}"


def _cmd_capture(args) -> int:
    themes = _theme_map(args.theme)
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    db = _ensure_isolated_db()
    print(f"[SENTINEL] capture targeted (DB {db})")
    screen_id = _resolve_screen(args.app, args.screen)
    app_key = screen_id.split(":")[0]
    surface = screen_id.split(":")[1] if ":" in screen_id else screen_id
    substate = screen_id.split(":", 2)[2] if screen_id.count(":") >= 2 else ""

    # descubrir para encontrar el spec que matchea
    specs_by_app = _discover_all(app_key, ["dark_hybrid"])
    matches = [sp for sp in specs_by_app.get(app_key, []) if sp.screen_id == screen_id]
    if not matches:
        matches = [StateSpec(app=app_key, surface=surface, substate=substate,
                             label=f"{surface} {substate}".strip())]
    states: list[CapturedState] = []
    for modo in themes:
        qapp, win = _instantiate(app_key, modo, _RESOLUTION)
        try:
            for spec in matches:
                st = _capture_state(win, qapp, spec, modo, out_dirs)
                _persist_captured(st, out_dirs)
                states.append(st)
        finally:
            _close_window(win)

    reg = _load_registry()
    _compute_coverage(states, [screen_id], reg)
    print(f"\nCaptura targeted: {screen_id} ({len(states)} tema(s))")
    for st in states:
        print(f"  {st.theme}: {st.png_path}  error={st.error}")
    print("VISUAL_SENTINEL_RESULT: TARGETED_INSPECTION_ONLY")
    print("GENERAL_AUDIT_COMPLETE: NO")
    print("GENERAL_AUDIT_NOT_RUN: YES")
    print("(capture --screen nunca emite resultado general; corra audit --all)")
    return 0


def _cmd_inspect(args) -> int:
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    _ensure_isolated_db()
    screen_id = _resolve_screen(args.app, args.screen)
    app_key = screen_id.split(":")[0]
    theme = args.theme

    specs_by_app = _discover_all(app_key, [_theme_map(theme)[0]])
    matches = [sp for sp in specs_by_app.get(app_key, []) if sp.screen_id == screen_id]
    if not matches:
        print(f"[ERROR] screen '{screen_id}' no descubierto en {app_key}. Use --list.")
        return 1
    modo = _theme_map(theme)[0]
    qapp, win = _instantiate(app_key, modo, _RESOLUTION)
    try:
        st = _capture_state(win, qapp, matches[0], modo, out_dirs)
    finally:
        _close_window(win)
    _persist_captured(st, out_dirs)

    print(f"\nINSPECCION: {screen_id} [{_short_theme(modo)}]")
    print(f"  PNG:      {st.png_path}")
    print(f"  Arbol Qt: {st.tree_path}")
    print(f"  Textos visibles ({len(st.texts)}):")
    for t in st.texts[:40]:
        print(f"    - {t}")
    print(f"  Botones ({len(st.buttons)}):")
    for b in st.buttons[:40]:
        print(f"    - [{b.get('type')}] '{b.get('text')}' enabled={b.get('enabled')}")
    print(f"  Tabs ({len(st.tabs)}):")
    for tb in st.tabs:
        print(f"    - {tb.get('type')} count={tb.get('count')} labels={tb.get('labels')}")
    print(f"  Scrollbars ({len(st.scrollbars)}):")
    for sb in st.scrollbars:
        print(f"    - {sb}")
    print(f"  sha256={st.sha256}  phash={st.phash}  struct={st.structural_hash}")
    print(f"  metricas={st.visual_metrics}")
    print("VISUAL_SENTINEL_RESULT: TARGETED_INSPECTION_ONLY")
    print("GENERAL_AUDIT_COMPLETE: NO")
    print("GENERAL_AUDIT_NOT_RUN: YES")
    return 0


def _cmd_propose_baselines() -> int:
    out_dirs = _prepare_out_dirs(_OUT_ROOT)
    _ensure_isolated_db()
    specs_by_app = _discover_all(None, ["dark_hybrid", "light_hybrid"])
    states = _run_capture(specs_by_app, ["suite", "hub"],
                          ["dark_hybrid", "light_hybrid"], out_dirs, lambda *a, **k: None)
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
    # --list como flag top-level (contrato del CLI del Sentinel).
    p.add_argument("--list", action="store_true", help="Listar estados descubiertos")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("list", help="Listar estados descubiertos").set_defaults(func=lambda a: _cmd_list())

    pa = sub.add_parser("audit", help="Auditoria general (usar --all para resultado general)")
    pa.add_argument("--all", action="store_true", help="Auditar todo (Suite + Hub)")
    pa.add_argument("--app", choices=["suite", "hub"], help="Auditar una sola app (sin resultado general)")
    pa.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    pa.set_defaults(func=_cmd_audit)

    pc = sub.add_parser("capture", help="Capturar una pantalla puntual (sin resultado general)")
    pc.add_argument("--screen", required=True, help="screen_id (app:surface[:substate])")
    pc.add_argument("--app", choices=["suite", "hub"], default="suite")
    pc.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    pc.set_defaults(func=_cmd_capture)

    pi = sub.add_parser("inspect", help="Inspeccionar una pantalla en consola")
    pi.add_argument("--screen", required=True, help="screen_id (app:surface[:substate])")
    pi.add_argument("--app", choices=["suite", "hub"], default="suite")
    pi.add_argument("--theme", choices=["light", "dark"], default="light")
    pi.set_defaults(func=_cmd_inspect)

    sub.add_parser("propose-baselines",
                   help="Generar baselines propuestas (sin aprobar)").set_defaults(
        func=lambda a: _cmd_propose_baselines())

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
        return _cmd_list()
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 1
    return int(func(args))


if __name__ == "__main__":
    raise SystemExit(main())
