"""qa/capture_v8.py — Exhaustive PyQt6 offscreen capture harness.

Descubre dinamicamente las superficies navegables de Suite y Hub
inspeccionando el codigo via AST. Ejecuta recetas de interaccion
intra-vista (clicks, texto, toggles, tabs) para capturar sub-estados, popups,
dialogos hijos y pantallas emergentes. Cubre estados vacio, demo, carga alta,
y todo lo navegable.

CREDENCIALES DE TEST (documentadas, via env vars con defaults):
    NM_TEST_NAME     = "Juan Cruz"
    NM_TEST_EMAIL    = "protegetua@gmail.com"
    NM_TEST_PASSWORD = "12345"
    NM_TEST_PIN      = "123456"

USO:
    .venv\\Scripts\\python.exe qa\\capture_v8.py --list
    .venv\\Scripts\\python.exe qa\\capture_v8.py --app suite --view animo-emotion-chips --theme dark
    .venv\\Scripts\\python.exe qa\\capture_v8.py --all   # regresion final completa

SALIDA: qa/_captures_v8/{app}-{view}-{theme}-{w}x{h}.png + CAPTURE_MANIFEST.json
"""

from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, Callable

_PROJ = Path(__file__).resolve().parent.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("NM_VISUAL_QA", "1")

_TEST_CREDS = {
    "NM_TEST_NAME": os.environ.get("NM_TEST_NAME", "Juan Cruz"),
    "NM_TEST_EMAIL": os.environ.get("NM_TEST_EMAIL", "protegetua@gmail.com"),
    "NM_TEST_PASSWORD": os.environ.get("NM_TEST_PASSWORD", "12345"),
    "NM_TEST_PIN": os.environ.get("NM_TEST_PIN", "123456"),
}

_DEFAULT_OUT = _PROJ / "qa" / "_captures_v8"
_DEFAULT_RES = ["960x600"]
_THEME_MAP = {"light": "light_hybrid", "dark": "dark_hybrid"}
_CHILD_PREFIX = "popup"

_STATUS_CAPTURED_VALID = "CAPTURED_VALID"
_STATUS_CAPTURE_FAILED = "CAPTURE_FAILED"
_STATUS_BLANK_OR_FLAT = "BLANK_OR_FLAT"
_STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH = "MAIN_CAPTURE_CONTRACT_MISMATCH"
_STATUS_DUPLICATE_SUSPECT = "DUPLICATE_SUSPECT"
_STATUS_WRONG_VIEW = "WRONG_VIEW"
_STATUS_FALLBACK = "FALLBACK"
_STATUS_REQUIRES_RUNTIME = "REQUIRES_RUNTIME"
_STATUS_REQUIRES_DATA_STATE = "REQUIRES_DATA_STATE"

_STATUS_PRIORITY = [
    _STATUS_CAPTURE_FAILED,
    _STATUS_BLANK_OR_FLAT,
    _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH,
    _STATUS_WRONG_VIEW,
    _STATUS_FALLBACK,
    _STATUS_DUPLICATE_SUSPECT,
    _STATUS_REQUIRES_RUNTIME,
    _STATUS_REQUIRES_DATA_STATE,
    _STATUS_CAPTURED_VALID,
]

# Umbrales de contenido: un PNG casi todo blanco/negro o sin varianza tonal
# no puede contar como evidencia válida de pantalla renderizada.
_BLANK_MEAN_HI = 0.985
_BLANK_MEAN_LO = 0.015
_FLAT_STDDEV = 0.004

_RECIPE_EVIDENCE_FLAGS: dict[tuple[str, str], dict[str, list[str]]] = {
    ("suite", "home-no-score"): {
        "flags": [_STATUS_REQUIRES_DATA_STATE],
        "notes": ["No-score depends on real persisted mood state; QA cache forcing is not product evidence."],
    },
    ("suite", "home-settings-open"): {
        "flags": [_STATUS_REQUIRES_RUNTIME, _STATUS_WRONG_VIEW],
        "notes": ["Settings overlay is a transient child state; static main-window capture can miss it."],
    },
    ("suite", "animo-stats-empty"): {
        "flags": [_STATUS_REQUIRES_DATA_STATE],
        "notes": ["Empty mood statistics require real absence of mood history; forced QA state is not product evidence."],
    },
    ("suite", "privacy-lock"): {
        "flags": [_STATUS_REQUIRES_RUNTIME],
        "notes": ["Standalone lock dialog does not prove the live lock route or dismissal lifecycle."],
    },
    ("suite", "privacy-lock-error"): {
        "flags": [_STATUS_REQUIRES_RUNTIME],
        "notes": ["Standalone lock error does not prove live lock route or failed-unlock lifecycle."],
    },
    ("suite", "pin-setup"): {
        "flags": [_STATUS_REQUIRES_RUNTIME],
        "notes": ["Standalone PIN setup does not prove invoked setup route, chrome, or lifecycle."],
    },
    ("hub", "dashboard"): {
        "flags": [_STATUS_REQUIRES_DATA_STATE],
        "notes": ["Dashboard uses QA/demo data; real data distribution is not established by this capture."],
    },
    ("hub", "dashboard-empty"): {
        "flags": [_STATUS_REQUIRES_DATA_STATE],
        "notes": ["Empty dashboard depends on real data absence; in-memory clearing can leave demo fragments."],
    },
    ("hub", "pacientes"): {
        "flags": [_STATUS_REQUIRES_DATA_STATE],
        "notes": ["Patient rows are QA/demo data; real patients state is not covered."],
    },
    ("hub", "pacientes-search"): {
        "flags": [_STATUS_REQUIRES_DATA_STATE],
        "notes": ["Search result quality depends on real patient records and empty-result state."],
    },
    ("hub", "pacientes-filter-activos"): {
        "flags": [_STATUS_REQUIRES_DATA_STATE],
        "notes": ["Filter state depends on real patient status distribution."],
    },
    ("hub", "pacientes-empty"): {
        "flags": [_STATUS_REQUIRES_DATA_STATE],
        "notes": ["Empty patients view depends on real data absence, not only QA in-memory clearing."],
    },
    ("hub", "editor-text-overrides"): {
        "flags": [_STATUS_REQUIRES_RUNTIME],
        "notes": ["Standalone editor capture does not prove Hub-launched chrome or close lifecycle."],
    },
    # editor-tcc-template ELIMINADA: el editor de plantilla TCC fue demolido
    # (reorganización user feedback — el Plan terapéutico asigna solo 4 módulos).
}


# ═══════════════════════════════════════════════════════════════════════════
# AST DYNAMIC DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════

def _ast_extract_dict_keys(filepath: Path, var_name: str) -> list[str]:
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    if isinstance(node.value, ast.Dict):
                        return [k.value if isinstance(k, ast.Constant) else str(k)
                                for k in node.value.keys if isinstance(k, ast.Constant)]
    return []


def _ast_extract_list_tuples_first(filepath: Path, var_name: str) -> list[str]:
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    if isinstance(node.value, ast.List):
                        r = []
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Tuple) and elt.elts:
                                first = elt.elts[0]
                                if isinstance(first, ast.Constant):
                                    r.append(first.value)
                        return r
    return []


def _ast_extract_add_section_ids(filepath: Path) -> list[str]:
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return []
    r = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            fname = func.id if isinstance(func, ast.Name) else (
                func.attr if isinstance(func, ast.Attribute) else None)
            if fname == "_add_section" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant):
                    r.append(first.value)
    return r


# ═══════════════════════════════════════════════════════════════════════════
# SUB-STATE RECIPE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

# Cada receta: {"label": str, "parent": str|None, "actions": [action_dict, ...]}
# action_dict keys: action, y segun accion: selector dicts o params.
#
# Acciones soportadas:
#   {"action": "navigate", "view": "id"}
#   {"action": "click", "text": "Boton"}
#   {"action": "click", "text_contains": "parcial"}
#   {"action": "click", "type": "QPushButton"}
#   {"action": "click", "object_name": "widget_name"}
#   {"action": "click", "at_index": 0, "type": "NMTabs"}
#   {"action": "toggle", "text_contains": "parcial"}
#   {"action": "type_text", "placeholder": "...", "text": "contenido"}
#   {"action": "type_text", "text_contains": "...", "text": "contenido"}
#   {"action": "set_tab", "tab_text": "Actividad"}
#   {"action": "set_tab_index", "index": 2}
#   {"action": "drain", "cycles": 6}
#   {"action": "call", "func": "_helper_name"}
#   {"action": "capture", "view": "id"}   (punto de captura)
#   {"action": "capture_child", "prefix": "popup_name"}  (captura ventana hija)
#   {"action": "close_child"}  (cierra ventana hija activa)

_RECIPES: dict[str, dict[str, dict]] = {
    "suite": {
        # ── Home ──────────────────────────────────────────────────────────
        "home": {
            "label": "Home (con puntaje)",
            "parent": None,
            "actions": [{"action": "navigate", "view": "home"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "home"}],
        },
        "home-no-score": {
            "label": "Home sin puntaje de animo",
            "parent": "home",
            "actions": [{"action": "navigate", "view": "home"},
                        {"action": "call", "func": "_force_no_score"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "home-no-score"}],
        },
        "home-settings-open": {
            "label": "Home + panel ajustes abierto",
            "parent": "home",
            "actions": [{"action": "navigate", "view": "home"},
                        {"action": "call", "func": "_open_settings_over_home"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "home-settings-open"}],
        },

        # ── Onboarding / Auth ─────────────────────────────────────────────
        "onboarding": {
            "label": "Onboarding - form crear cuenta",
            "parent": None,
            "actions": [{"action": "call", "func": "_build_onboarding"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "onboarding"}],
        },
        "onboarding-error": {
            "label": "Onboarding - estado error",
            "parent": "onboarding",
            "actions": [{"action": "call", "func": "_build_onboarding"},
                        {"action": "click", "text_contains": "Crear"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "onboarding-error"}],
        },
        # NOTA: no existe receta "onboarding-login" — el onboarding del
        # producto es UN solo form con dos CTAs (Crear cuenta / Iniciar
        # sesión); no hay vista/modo login separado que capturar.
        "privacy-lock": {
            "label": "Privacy Lock - PIN entry",
            "parent": None,
            "actions": [{"action": "call", "func": "_build_privacy_lock"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "privacy-lock"}],
        },
        "privacy-lock-error": {
            "label": "Privacy Lock - error state",
            "parent": "privacy-lock",
            "actions": [{"action": "call", "func": "_build_privacy_lock"},
                        {"action": "call", "func": "_privacy_lock_wrong_pin"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "privacy-lock-error"}],
        },

        # ── Modulos ──────────────────────────────────────────────────────
        "animo": {
            "label": "Animo default",
            "parent": None,
            "actions": [{"action": "navigate", "view": "animo"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "animo"}],
        },
        "animo-emotion-chips": {
            "label": "Animo + chips emocion",
            "parent": "animo",
            "actions": [{"action": "navigate", "view": "animo"},
                        {"action": "call", "func": "_animo_toggle_chips"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "animo-emotion-chips"}],
        },
        "animo-note-filled": {
            "label": "Animo + nota escrita",
            "parent": "animo",
            "actions": [{"action": "navigate", "view": "animo"},
                        {"action": "call", "func": "_animo_type_note"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "animo-note-filled"}],
        },
        "animo-stats-empty": {
            "label": "Animo stats vacias",
            "parent": "animo",
            "actions": [{"action": "navigate", "view": "animo"},
                        {"action": "call", "func": "_animo_clear_stats"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "animo-stats-empty"}],
        },
        "evolucion": {
            "label": "Evolucion animica default",
            "parent": None,
            "actions": [{"action": "navigate", "view": "evolucion"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "evolucion"}],
        },
        "evolucion-sparse": {
            "label": "Evolucion sparse state (< 2 puntos — evidencia S13)",
            "parent": "evolucion",
            "actions": [{"action": "navigate", "view": "evolucion"},
                        {"action": "call", "func": "_evolucion_force_sparse"},
                        {"action": "drain", "cycles": 4},
                        {"action": "capture", "view": "evolucion-sparse"}],
        },

        "respiracion": {
            "label": "Respiracion idle",
            "parent": None,
            "actions": [{"action": "navigate", "view": "respiracion"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "respiracion"}],
        },
        "respiracion-preset-3min": {
            "label": "Respiracion preset 3 min",
            "parent": "respiracion",
            "actions": [{"action": "navigate", "view": "respiracion"},
                        {"action": "click", "text_contains": "3 min"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "respiracion-preset-3min"}],
        },
        "respiracion-preset-10min": {
            "label": "Respiracion preset 10 min",
            "parent": "respiracion",
            "actions": [{"action": "navigate", "view": "respiracion"},
                        {"action": "click", "text_contains": "10 min"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "respiracion-preset-10min"}],
        },
        "respiracion-running": {
            "label": "Respiracion running (inhala)",
            "parent": "respiracion",
            "actions": [{"action": "navigate", "view": "respiracion"},
                        {"action": "call", "func": "_respiracion_start_capture_phase"},
                        {"action": "drain", "cycles": 4},
                        {"action": "capture", "view": "respiracion-running"}],
        },
        "respiracion-paused": {
            "label": "Respiracion paused",
            "parent": "respiracion",
            "actions": [{"action": "navigate", "view": "respiracion"},
                        {"action": "call", "func": "_respiracion_start"},
                        {"action": "drain", "cycles": 8},
                        {"action": "call", "func": "_respiracion_pause"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "respiracion-paused"}],
        },
        "respiracion-historial": {
            "label": "Respiracion + historial",
            "parent": None,
            "actions": [{"action": "navigate", "view": "respiracion"},
                        {"action": "call", "func": "_respiracion_toggle_history"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "respiracion-historial"}],
        },

        "registro": {
            "label": "TCC paso 0 - Situacion vacia",
            "parent": None,
            "actions": [{"action": "navigate", "view": "registro"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "registro"}],
        },
        "registro-step1-emotion": {
            "label": "TCC paso 1 - Emocion",
            "parent": "registro",
            "actions": [{"action": "navigate", "view": "registro"},
                        {"action": "call", "func": "_tcc_prepare_step", "step": 1},
                        {"action": "drain", "cycles": 4},
                        {"action": "capture", "view": "registro-step1-emotion"}],
        },
        "registro-step2-distortions": {
            "label": "TCC paso 2 - distorsiones",
            "parent": "registro",
            "actions": [{"action": "navigate", "view": "registro"},
                        {"action": "call", "func": "_tcc_prepare_step", "step": 2},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "registro-step2-distortions"}],
        },
        "registro-step3-filled": {
            "label": "TCC paso 3 - Respuesta llena",
            "parent": "registro",
            "actions": [{"action": "navigate", "view": "registro"},
                        {"action": "call", "func": "_tcc_prepare_step", "step": 3},
                        {"action": "drain", "cycles": 4},
                        {"action": "capture", "view": "registro-step3-filled"}],
        },
        "registro-success": {
            "label": "TCC - pagina exito",
            "parent": "registro",
            "actions": [{"action": "navigate", "view": "registro"},
                        {"action": "call", "func": "_tcc_fill_and_guardar"},
                        {"action": "drain", "cycles": 10},
                        {"action": "capture", "view": "registro-success"}],
        },

        "rutina": {
            "label": "Rutina default (parcial)",
            "parent": None,
            "actions": [{"action": "navigate", "view": "rutina"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "rutina"}],
        },
        "rutina-all-completed": {
            "label": "Rutina 100% completada",
            "parent": "rutina",
            "actions": [{"action": "navigate", "view": "rutina"},
                        {"action": "call", "func": "_rutina_complete_all"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "rutina-all-completed"}],
        },
        "rutina-add-task": {
            "label": "Rutina + agregar tarea inline",
            "parent": "rutina",
            "actions": [{"action": "navigate", "view": "rutina"},
                        {"action": "call", "func": "_rutina_open_add_task"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "rutina-add-task"}],
        },
        "rutina-empty": {
            "label": "Rutina sin tareas asignadas — NMEmptyState (evidencia S09)",
            "parent": None,
            "actions": [{"action": "navigate", "view": "rutina"},
                        {"action": "call", "func": "_rutina_force_empty"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "rutina-empty"}],
        },

        "actividades": {
            "label": "Actividades default",
            "parent": None,
            "actions": [{"action": "navigate", "view": "actividades"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "actividades"}],
        },
        "actividades-marked-hice": {
            "label": "Actividades + marcada Hecho",
            "parent": "actividades",
            "actions": [{"action": "navigate", "view": "actividades"},
                        {"action": "click", "text_contains": "Hice"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "actividades-marked-hice"}],
        },
        "actividades-filtered": {
            "label": "Actividades + filtro con resultados",
            "parent": "actividades",
            "actions": [{"action": "navigate", "view": "actividades"},
                        {"action": "call", "func": "_actividades_filter_category", "category": "Placer"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "actividades-filtered"}],
        },

        "timer": {
            "label": "Timer idle",
            "parent": None,
            "actions": [{"action": "navigate", "view": "timer"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "timer"}],
        },
        "timer-running": {
            "label": "Timer running",
            "parent": "timer",
            "actions": [{"action": "navigate", "view": "timer"},
                        {"action": "call", "func": "_timer_start"},
                        {"action": "drain", "cycles": 12},
                        {"action": "capture", "view": "timer-running"}],
        },
        "timer-paused": {
            "label": "Timer paused",
            "parent": "timer",
            "actions": [{"action": "navigate", "view": "timer"},
                        {"action": "call", "func": "_timer_start"},
                        {"action": "drain", "cycles": 8},
                        {"action": "call", "func": "_timer_pause"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "timer-paused"}],
        },
        "timer-preset-5min": {
            "label": "Timer preset 5 min",
            "parent": "timer",
            "actions": [{"action": "navigate", "view": "timer"},
                        {"action": "call", "func": "_timer_select_preset", "seconds": 5 * 60},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "timer-preset-5min"}],
        },
        "timer-preset-45min": {
            "label": "Timer preset 45 min",
            "parent": "timer",
            "actions": [{"action": "navigate", "view": "timer"},
                        {"action": "call", "func": "_timer_select_preset", "seconds": 45 * 60},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "timer-preset-45min"}],
        },

        "avisos": {
            "label": "Avisos default",
            "parent": None,
            "actions": [{"action": "navigate", "view": "avisos"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "avisos"}],
        },
        # NOTA: no existe receta "avisos-form" — decisión de producto: el
        # paciente solo lee/marca recordatorios; el alta vive en el Hub.
        "avisos-filter-activos": {
            "label": "Avisos filtro Activos",
            "parent": "avisos",
            "actions": [{"action": "navigate", "view": "avisos"},
                        {"action": "call", "func": "_avisos_filter_activos"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "avisos-filter-activos"}],
        },
        "avisos-search": {
            "label": "Avisos con busqueda",
            "parent": "avisos",
            "actions": [{"action": "navigate", "view": "avisos"},
                        {"action": "call", "func": "_avisos_search", "text": "medic"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "avisos-search"}],
        },
        "avisos-completed": {
            "label": "Avisos + completado",
            "parent": "avisos",
            "actions": [{"action": "navigate", "view": "avisos"},
                        {"action": "call", "func": "_avisos_complete_first"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "avisos-completed"}],
        },

        # ── Dialogos standalone ───────────────────────────────────────────
        # NOTA: no existe receta "ajustes" standalone — _SettingsPanel suelto
        # renderizaba una franja de 380x30; la ruta real (modal sobre Home)
        # ya la cubre home-settings-open.
        "pin-setup": {
            "label": "Configurar PIN",
            "parent": None,
            "actions": [{"action": "call", "func": "_build_pin_setup"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "pin-setup"}],
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    # HUB
    # ═══════════════════════════════════════════════════════════════════════
    "hub": {
        "dashboard": {
            "label": "Dashboard default",
            "parent": None,
            "actions": [{"action": "navigate", "view": "dashboard"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "dashboard"}],
        },
        "dashboard-empty": {
            "label": "Dashboard sin pacientes",
            "parent": "dashboard",
            "actions": [{"action": "navigate", "view": "dashboard"},
                        {"action": "call", "func": "_clear_hub_patients"},
                        {"action": "navigate", "view": "dashboard"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "dashboard-empty"}],
        },

        "pacientes": {
            "label": "Pacientes default",
            "parent": None,
            "actions": [{"action": "navigate", "view": "pacientes"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "pacientes"}],
        },
        "pacientes-search": {
            "label": "Pacientes con busqueda",
            "parent": "pacientes",
            "actions": [{"action": "navigate", "view": "pacientes"},
                        {"action": "call", "func": "_pacientes_search"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "pacientes-search"}],
        },
        "pacientes-filter-activos": {
            "label": "Pacientes filtro Activos",
            "parent": "pacientes",
            "actions": [{"action": "navigate", "view": "pacientes"},
                        {"action": "click", "text": "Activos"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "pacientes-filter-activos"}],
        },
        "pacientes-filter-sin-registros": {
            "label": "Pacientes filtro Sin registros",
            "parent": "pacientes",
            "actions": [{"action": "navigate", "view": "pacientes"},
                        {"action": "click", "text": "Sin registros"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "pacientes-filter-sin-registros"}],
        },
        "pacientes-filter-sin-sync": {
            "label": "Pacientes filtro Sin sincronizacion reciente",
            "parent": "pacientes",
            "actions": [{"action": "navigate", "view": "pacientes"},
                        {"action": "click", "text": "Sin sincronización reciente"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "pacientes-filter-sin-sync"}],
        },
        "pacientes-empty": {
            "label": "Pacientes empty state",
            "parent": "pacientes",
            "actions": [{"action": "navigate", "view": "pacientes"},
                        {"action": "call", "func": "_clear_hub_patients"},
                        {"action": "navigate", "view": "pacientes"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "pacientes-empty"}],
        },

        "detalle": {
            "label": "Detalle paciente (overview)",
            "parent": None,
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "detalle"}],
        },
        "detalle-ia": {
            "label": "Detalle > IA tab",
            "parent": "detalle",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "set_tab", "tab_text": "IA"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-ia"}],
        },
        "detalle-registros": {
            "label": "Detalle > Registros tab",
            "parent": "detalle",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "set_tab", "tab_text": "Registros"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-registros"}],
        },
        "detalle-registros-bottom": {
            "label": "Detalle > Registros (scroll al final: lista de registros)",
            "parent": "detalle-registros",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "set_tab", "tab_text": "Registros"},
                        {"action": "call", "func": "_registros_scroll_bottom"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-registros-bottom"}],
        },
        "detalle-plan": {
            "label": "Detalle > Plan terapeutico tab (Recordatorios)",
            "parent": "detalle",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "set_tab", "tab_text": "Plan terapéutico"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-plan"}],
        },
        "detalle-ia-asignacion": {
            "label": "Detalle > IA > Asignación sugerida (borrador + aprobación)",
            "parent": "detalle-ia",
            "actions": [{"action": "navigate", "view": "detalle-ia"},
                        {"action": "call", "func": "_ia_scroll_to_asignacion"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-ia-asignacion"}],
        },
        "detalle-plan-timer": {
            "label": "Detalle > Plan > Temporizador",
            "parent": "detalle-plan",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "set_tab", "tab_text": "Plan terapéutico"},
                        {"action": "call", "func": "_plan_set_subtab", "index": 1},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-plan-timer"}],
        },
        "detalle-plan-rutina": {
            "label": "Detalle > Plan > Rutina",
            "parent": "detalle-plan",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "set_tab", "tab_text": "Plan terapéutico"},
                        {"action": "call", "func": "_plan_set_subtab", "index": 2},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-plan-rutina"}],
        },
        "detalle-plan-activacion": {
            "label": "Detalle > Plan > Activación",
            "parent": "detalle-plan",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "set_tab", "tab_text": "Plan terapéutico"},
                        {"action": "call", "func": "_plan_set_subtab", "index": 3},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-plan-activacion"}],
        },

        # NOTA: no existen recetas "ia*" — IAAssistantView fue eliminada en la
        # reestructura v1.0; la IA runtime vive en el tab IA del detalle de
        # paciente y la cubre la receta detalle-ia.

        "personalizacion": {
            "label": "Personalización > módulos (textos globales)",
            "parent": None,
            "actions": [{"action": "navigate", "view": "personalizacion"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "personalizacion"}],
        },
        "personalizacion-textos": {
            "label": "Personalización > editor de textos de un módulo",
            "parent": "personalizacion",
            "actions": [{"action": "navigate", "view": "personalizacion"},
                        {"action": "call", "func": "_personalizacion_open_editor"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "personalizacion-textos"}],
        },
        "sidebar-collapsed": {
            "label": "Hub sidebar collapsed",
            "parent": "dashboard",
            "actions": [{"action": "navigate", "view": "dashboard"},
                        {"action": "call", "func": "_sidebar_collapse"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "sidebar-collapsed"}],
        },

        "editor-text-overrides": {
            "label": "Editor Text Overrides",
            "parent": None,
            "actions": [{"action": "call", "func": "_build_editor_text_overrides"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "editor-text-overrides"}],
        },
        # editor-tcc-template ELIMINADA (editor demolido, user feedback).
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM HELPER FUNCTIONS (callable via {"action": "call", "func": "_name"})
# ═══════════════════════════════════════════════════════════════════════════

_HELPERS: dict[str, Callable] = {}
_CURRENT_WIN = None  # set during capture session


def _register_helper(func):
    _HELPERS[func.__name__] = func
    return func


def _module_target(win):
    return getattr(win, '_current_module', None) or win


@_register_helper
def _force_no_score(win, qapp, action):
    """Fuerza que Home/Animo no muestre puntaje."""
    from app.home_qt import HomeView
    homes = list(win.findChildren(HomeView))
    direct_home = getattr(win, '_home', None)
    if direct_home is not None and direct_home not in homes:
        homes.append(direct_home)
    def _empty_status(module_id):
        return ""

    for home in homes:
        home._get_status = _empty_status
        # ModuleCards capturan get_status_fn por referencia en su __init__; hay
        # que parchearlos directamente o refresh_statuses sigue devolviendo QA data.
        if hasattr(home, '_cards'):
            for card in home._cards.values():
                card._get_status = _empty_status
        if hasattr(home, 'refresh_statuses'):
            home.refresh_statuses()
        if hasattr(home, '_hero'):
            home._hero.refresh()
            if hasattr(home._hero, '_stack'):
                home._hero._stack.setCurrentIndex(0)
        if hasattr(home, '_side'):
            home._side.update_wellbeing("")
    _drain(qapp, cycles=4)


@_register_helper
def _open_settings_over_home(win, qapp, action):
    """Abre el panel de ajustes sobre el Home."""
    from app.home_qt import _SettingsPanel
    panel = _SettingsPanel(win, getattr(win, '_modo', 'dark_hybrid'))
    panel.show()
    _drain(qapp, cycles=8)
    # La captura la hara' el caller despues de drain
    _HELPERS['_last_child'] = panel


@_register_helper
def _build_onboarding(win, qapp, action):
    """Construye OnboardingDialog standalone."""
    from app.onboarding_qt import OnboardingDialog
    dlg = OnboardingDialog(parent=None)
    # Tamaño natural del diálogo (como privacy-lock): forzarlo a 960x600 dejaba
    # la card recortada/desparramada y no representaba el modal real.
    dlg.show()
    _drain(qapp, cycles=6)
    globals()['_CURRENT_STANDALONE'] = dlg


@_register_helper
def _build_privacy_lock(win, qapp, action):
    """Construye PrivacyLockDialog standalone."""
    import app.privacy_lock_qt as privacy_lock

    # Standalone visual QA must not read/write the user's real AppData config.
    # Install an in-memory PIN state so privacy-lock-error actually exercises
    # the wrong-PIN UI instead of passing through because the real hash is empty.
    qa_config = {
        "privacy_lock_enabled": "1",
        "privacy_pin_hash": privacy_lock._hash_pwd(_TEST_CREDS["NM_TEST_PIN"]),
        "privacy_lock_until": "0",
        "patient_email": _TEST_CREDS["NM_TEST_EMAIL"],
    }
    privacy_lock.leer_config = lambda key, default="": qa_config.get(key, default)
    privacy_lock.guardar_config = lambda key, value: qa_config.__setitem__(key, value)
    privacy_lock.obtener_nombre_paciente = lambda: _TEST_CREDS["NM_TEST_NAME"]

    PrivacyLockDialog = privacy_lock.PrivacyLockDialog
    dlg = PrivacyLockDialog(parent=None)
    dlg._on_theme(getattr(win, '_modo', 'dark_hybrid'))
    dlg.show()
    _drain(qapp, cycles=6)
    globals()['_CURRENT_STANDALONE'] = dlg


@_register_helper
def _privacy_lock_wrong_pin(win, qapp, action):
    """Fuerza un PIN incorrecto en el dialog standalone activo."""
    dlg = globals().get('_CURRENT_STANDALONE')
    if dlg is None:
        return
    pin_input = getattr(dlg, "_pin_input", None)
    if pin_input is not None and hasattr(pin_input, "setText"):
        pin_input.setText("000000")
    unlock = getattr(dlg, "_on_unlock_clicked", None)
    if callable(unlock):
        unlock()
    _drain(qapp, cycles=4)


@_register_helper
def _build_pin_setup(win, qapp, action):
    """Construye _PINSetupDialog standalone."""
    from PyQt6.QtWidgets import QApplication
    from shared.theme_qt import stylesheet_base
    modo = getattr(win, '_modo', 'dark_hybrid') if win else 'dark_hybrid'
    qa = QApplication.instance()
    if qa:
        qa.setStyleSheet(stylesheet_base(modo))
    from app.home_qt import _PINSetupDialog
    dlg = _PINSetupDialog(None, modo)
    # Tamaño natural del diálogo (como privacy-lock); a 960x600 quedaba el
    # contenido pegado a la izquierda con ~75% del ancho vacío.
    dlg.show()
    _drain(qapp, cycles=6)
    globals()['_CURRENT_STANDALONE'] = dlg


def _wrap_standalone_canvas(editor, modo):
    """Host con el canvas del tema para editores que en producto viven
    embebidos (tab del detalle / Personalización). Sin esto el root del
    editor puede quedar translúcido y la captura standalone sale en negro."""
    from PyQt6.QtWidgets import QWidget, QVBoxLayout
    from shared.theme_qt import v3c
    host = QWidget()
    host.setObjectName("StandaloneCanvas")
    host.setStyleSheet(
        f"QWidget#StandaloneCanvas {{ background: {v3c('bg', modo).name()}; }}"
    )
    lay = QVBoxLayout(host)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(editor)
    return host


@_register_helper
def _ia_scroll_to_asignacion(win, qapp, action):
    """Scrollea el tab IA hasta la card 'Asignación sugerida'."""
    det = win._stack.currentWidget() if hasattr(win, "_stack") else None
    ia = getattr(det, "_tab_ia", None)
    scroll = getattr(ia, "_ia_scroll", None)
    if scroll is not None:
        bar = scroll.verticalScrollBar()
        bar.setValue(bar.maximum())
        _drain(qapp, cycles=4)


@_register_helper
def _registros_scroll_bottom(win, qapp, action):
    """Carga datos y scrollea el tab Registros hasta el final.

    La lista de registros (Termómetro/TCC/etc.) vive bajo el chart y queda
    fuera del viewport 960x600: sin scrollear no hay evidencia del badge de
    intensidad TCC (/10) ni del contenido recortado señalado en H13."""
    det = win._stack.currentWidget() if hasattr(win, "_stack") else None
    reg = getattr(det, "_tab_reg", None)
    if reg is None:
        return
    if hasattr(reg, "_cargar_datos"):
        reg._cargar_datos()
    # La carga puede ser asíncrona (señal _datos_loaded_signal): drená amplio y
    # re-fijá el scroll al máximo varias veces para absorber filas tardías.
    _drain(qapp, cycles=12)
    scroll = getattr(reg, "_scroll", None)
    if scroll is not None:
        bar = scroll.verticalScrollBar()
        for _ in range(4):
            bar.setValue(bar.maximum())
            _drain(qapp, cycles=3)


@_register_helper
def _plan_set_subtab(win, qapp, action):
    """Selecciona un subtab del Plan terapéutico (index en la action)."""
    det = win._stack.currentWidget() if hasattr(win, "_stack") else None
    plan = getattr(det, "_tab_plan", None)
    tabs = getattr(plan, "_tabs", None)
    if tabs is not None:
        tabs.setCurrentIndex(int(action.get("index", 0)))
        _drain(qapp, cycles=4)


@_register_helper
def _personalizacion_open_editor(win, qapp, action):
    """Abre el editor de textos del primer módulo en Personalización."""
    view = getattr(win, "_view_personalizacion", None)
    if view is not None and hasattr(view, "_open_editor"):
        view._open_editor("animo")
        _drain(qapp, cycles=6)


@_register_helper
def _build_editor_text_overrides(win, qapp, action):
    from hub.editors.text_overrides_editor import TextOverridesEditor
    modo = getattr(win, '_modo', 'dark_hybrid') if win else 'dark_hybrid'
    editor = TextOverridesEditor(None, modo=modo)
    from PyQt6.QtCore import QSize
    host = _wrap_standalone_canvas(editor, modo)
    host.setFixedSize(QSize(960, 600))
    host.show()
    _drain(qapp, cycles=6)
    globals()['_CURRENT_STANDALONE'] = host


@_register_helper
def _animo_toggle_chips(win, qapp, action):
    """Toggleea chips de emocion en Animo."""
    target = getattr(win, '_current_module', None) or win
    from PyQt6.QtWidgets import QPushButton
    buttons = [w for w in target.findChildren(QPushButton) if hasattr(w, 'isCheckable') and w.isCheckable()]
    for btn in buttons[:3]:
        try:
            btn.setChecked(True)
            btn.clicked.emit(True)
        except Exception:
            pass
    _drain(qapp, cycles=4)


@_register_helper
def _animo_type_note(win, qapp, action):
    """Escribe nota en Animo."""
    target = getattr(win, '_current_module', None) or win
    from PyQt6.QtWidgets import QTextEdit
    text_edits = target.findChildren(QTextEdit)
    if text_edits:
        text_edits[0].setPlainText("Hoy me siento bastante bien. Tuve un dia productivo en el trabajo y pude manejar la ansiedad con ejercicios de respiracion.")
        text_edits[0].textChanged.emit()
    _drain(qapp, cycles=4)


@_register_helper
def _respiracion_start(win, qapp, action):
    """Inicia la respiracion."""
    target = getattr(win, '_current_module', None) or win
    if hasattr(target, '_start'):
        target._start()
    _drain(qapp, cycles=6)


@_register_helper
def _respiracion_start_capture_phase(win, qapp, action):
    """Inicia respiracion y captura durante inhala."""
    target = getattr(win, '_current_module', None) or win
    if hasattr(target, '_start'):
        target._start()
    _drain(qapp, cycles=4)


@_register_helper
def _respiracion_pause(win, qapp, action):
    """Pausa la respiracion."""
    target = getattr(win, '_current_module', None) or win
    if hasattr(target, '_pause'):
        target._pause()
    _drain(qapp, cycles=4)


@_register_helper
def _respiracion_toggle_history(win, qapp, action):
    """Abre/cierra historial de respiracion."""
    target = getattr(win, '_current_module', None) or win
    if hasattr(target, '_btn_hist_toggle') and target._btn_hist_toggle is not None:
        target._btn_hist_toggle.setChecked(True)
    if hasattr(target, '_toggle_history'):
        target._toggle_history()
    _drain(qapp, cycles=6)


@_register_helper
def _tcc_pick_first_emotion(win, qapp, action):
    """Selecciona la primera emocion en TCC paso 1."""
    target = getattr(win, '_current_module', None) or win
    if hasattr(target, '_emotion_tiles') and target._emotion_tiles:
        tile = target._emotion_tiles[0]
        try:
            tile.clicked.emit()
        except Exception:
            tile.click()
    _drain(qapp, cycles=4)


@_register_helper
def _tcc_type_distortion_text(win, qapp, action):
    """Escribe texto con distorsiones en TCC paso 2."""
    target = getattr(win, '_current_module', None) or win
    from PyQt6.QtWidgets import QTextEdit
    texts = target.findChildren(QTextEdit)
    for t in texts:
        if t.isVisible():
            t.setPlainText("Siento que nunca voy a mejorar y que siempre voy a fracasar en todo. Es catastrofico pensar en el futuro. Nadie me entiende ni me valora.")
            t.textChanged.emit()
            break
    _drain(qapp, cycles=6)


@_register_helper
def _tcc_type_response(win, qapp, action):
    """Escribe respuesta racional en TCC paso 3."""
    target = getattr(win, '_current_module', None) or win
    from PyQt6.QtWidgets import QTextEdit
    texts = target.findChildren(QTextEdit)
    for t in texts:
        if t.isVisible():
            t.setPlainText("Se que estos pensamientos son distorsiones cognitivas. He mejorado en muchas areas y tengo personas que me apoyan. Manana sera un mejor dia.")
            t.textChanged.emit()
            break
    _drain(qapp, cycles=4)


def _tcc_set_text(widget, text: str) -> None:
    widget.setPlainText(text)
    try:
        widget.textChanged.emit()
    except TypeError:
        try:
            widget.textChanged.emit(text)
        except Exception:
            pass
    except Exception:
        pass


@_register_helper
def _tcc_prepare_step(win, qapp, action):
    """Prepara un paso TCC con datos validos sin depender de clicks rechazados."""
    target = _module_target(win)
    try:
        step = max(0, min(3, int(action.get("step", 0))))
    except Exception:
        step = 0

    situation = str(action.get(
        "situation",
        "Discusion con companero de trabajo sobre fechas de entrega.",
    ))
    thought = str(action.get(
        "thought",
        "Nunca voy a poder cumplir con los plazos; siempre fallo y todo va a salir mal.",
    ))
    response = str(action.get(
        "response",
        "He cumplido plazos antes. Puedo separar este problema de mi valor personal y pedir ayuda.",
    ))

    data = getattr(target, "_data", None)
    if isinstance(data, dict):
        data["situacion"] = situation
        data.setdefault("intensidad", 5)

    if hasattr(target, "_txt_situacion"):
        _tcc_set_text(target._txt_situacion, situation)

    if step >= 1:
        label = action.get("emotion")
        if not label and getattr(target, "_emotion_tiles", None):
            tile = target._emotion_tiles[0]
            if hasattr(tile, "label_text"):
                label = tile.label_text()
        if not label:
            label = "Ansiedad"
        if hasattr(target, "_on_emotion_picked"):
            target._on_emotion_picked(str(label))
        elif isinstance(data, dict):
            data["emocion"] = str(label)

    if step >= 2:
        if isinstance(data, dict):
            data["pensamiento"] = thought
        if hasattr(target, "_txt_pensamiento"):
            _tcc_set_text(target._txt_pensamiento, thought)
        if hasattr(target, "_detect_distortions"):
            target._detect_distortions(None)

    if step >= 3:
        if isinstance(data, dict):
            data["respuesta"] = response
        if hasattr(target, "_txt_respuesta"):
            _tcc_set_text(target._txt_respuesta, response)

    if hasattr(target, "_step"):
        target._step = step
    if hasattr(target, "_show_step"):
        target._show_step()
    if hasattr(target, "_resumen") and isinstance(data, dict):
        target._resumen.update_data(data)
    _drain(qapp, cycles=6)


@_register_helper
def _tcc_fill_and_guardar(win, qapp, action):
    """Completa todos los pasos del TCC y guarda."""
    target = getattr(win, '_current_module', None) or win
    from PyQt6.QtWidgets import QTextEdit, QPushButton
    # Step 0: Situacion
    texts0 = [t for t in target.findChildren(QTextEdit) if t.isVisible()]
    if texts0:
        texts0[0].setPlainText("Discusion con companero de trabajo sobre fechas de entrega.")
        texts0[0].textChanged.emit()
    _drain(qapp, cycles=2)
    # Siguiente
    btns = [b for b in target.findChildren(QPushButton) if b.isVisible() and b.text() == "Siguiente"]
    if btns:
        btns[0].click()
    _drain(qapp, cycles=3)
    # Step 1: Emocion
    if hasattr(target, '_emotion_tiles') and target._emotion_tiles:
        tile = target._emotion_tiles[0]
        try:
            tile.clicked.emit()
        except Exception:
            tile.click()
    _drain(qapp, cycles=2)
    btns = [b for b in target.findChildren(QPushButton) if b.isVisible() and b.text() == "Siguiente"]
    if btns:
        btns[0].click()
    _drain(qapp, cycles=3)
    # Step 2: Pensamiento
    texts2 = [t for t in target.findChildren(QTextEdit) if t.isVisible()]
    if texts2:
        texts2[0].setPlainText("Nunca voy a poder cumplir con los plazos, siempre fallo.")
        texts2[0].textChanged.emit()
    _drain(qapp, cycles=4)
    btns = [b for b in target.findChildren(QPushButton) if b.isVisible() and b.text() == "Siguiente"]
    if btns:
        btns[0].click()
    _drain(qapp, cycles=3)
    # Step 3: Respuesta
    texts3 = [t for t in target.findChildren(QTextEdit) if t.isVisible()]
    if texts3:
        texts3[0].setPlainText("He cumplido plazos antes. Puedo organizarme mejor esta vez.")
        texts3[0].textChanged.emit()
    _drain(qapp, cycles=2)
    # Guardar
    btns_g = [b for b in target.findChildren(QPushButton) if b.isVisible() and b.text() == "Guardar"]
    if btns_g:
        btns_g[0].click()
    _drain(qapp, cycles=8)


@_register_helper
def _rutina_complete_all(win, qapp, action):
    """Marca todas las tareas de rutina como completadas."""
    target = _module_target(win)
    from PyQt6.QtWidgets import QCheckBox
    checkboxes = [w for w in target.findChildren(QCheckBox) if w.isVisible()]
    for cb in checkboxes:
        try:
            cb.setChecked(True)
            cb.clicked.emit(True)
        except Exception:
            pass
    try:
        from shared.components import NMCustomCheck
        custom_checks = [
            w for w in target.findChildren(NMCustomCheck)
            if w.isVisible()
        ]
        for cb in custom_checks:
            cb.set_checked(True)
            cb.toggled.emit(True)
    except Exception:
        pass
    _drain(qapp, cycles=6)


@_register_helper
def _rutina_open_add_task(win, qapp, action):
    """Abre el formulario inline para agregar tarea en Rutina."""
    target = _module_target(win)
    if hasattr(target, '_on_new_task_hero'):
        target._on_new_task_hero()
    elif hasattr(target, '_on_section_add'):
        target._on_section_add("manana")
    _drain(qapp, cycles=6)


@_register_helper
def _rutina_force_empty(win, qapp, action):
    """Fuerza rutina a estado vacío (sin tareas) — evidencia visual S09."""
    import app.modules.rutina_qt as _rq
    target = _module_target(win)
    _orig = _rq.routine_sections
    _rq.routine_sections = lambda: {}
    try:
        target._load_visual_qa_tasks()
    finally:
        _rq.routine_sections = _orig
    _drain(qapp, cycles=6)


@_register_helper
def _evolucion_force_sparse(win, qapp, action):
    """Fuerza evolucion a sparse state (0 puntos válidos) — evidencia visual S13."""
    import shared.utils as _su
    target = _module_target(win)
    _orig = _su.get_valence_series
    _su.get_valence_series = lambda days: ([], [])
    try:
        target._load_tab_data(0)
    finally:
        _su.get_valence_series = _orig
    _drain(qapp, cycles=4)


@_register_helper
def _actividades_filter_category(win, qapp, action):
    """Aplica un filtro de categoria con resultado esperado en Actividades."""
    target = _module_target(win)
    category = str(action.get("category", "Placer"))
    tabs = getattr(target, "_category_tabs", None)
    if tabs is not None and hasattr(tabs, "_labels"):
        for idx, label in enumerate(getattr(tabs, "_labels", []) or []):
            if _norm_text(str(label)) == _norm_text(category):
                try:
                    tabs._current = idx
                    for btn_idx, btn in enumerate(getattr(tabs, "_btns", []) or []):
                        btn.setChecked(btn_idx == idx)
                    if hasattr(tabs, "_style_buttons"):
                        tabs._style_buttons()
                except Exception:
                    pass
                break
    if hasattr(target, '_on_category_filter'):
        target._on_category_filter(category)
    _drain(qapp, cycles=6)


@_register_helper
def _actividades_filter_fisica(win, qapp, action):
    """Alias historico: usa una categoria estable con resultados en QA."""
    action = dict(action)
    action.setdefault("category", "Placer")
    _actividades_filter_category(win, qapp, action)


@_register_helper
def _timer_start(win, qapp, action):
    """Inicia el timer."""
    target = _module_target(win)
    if hasattr(target, '_start'):
        target._start()
    _drain(qapp, cycles=4)


@_register_helper
def _timer_pause(win, qapp, action):
    """Pausa el timer."""
    target = _module_target(win)
    if hasattr(target, '_pause'):
        target._pause()
    _drain(qapp, cycles=4)


@_register_helper
def _timer_select_preset(win, qapp, action):
    """Selecciona preset de Timer por segundos sin depender del widget del chip."""
    target = _module_target(win)
    seconds = int(action.get("seconds", 25 * 60))
    if hasattr(target, '_select_preset'):
        target._select_preset(seconds)
    _drain(qapp, cycles=6)


@_register_helper
def _avisos_filter_activos(win, qapp, action):
    """Aplica filtro Activos en Avisos."""
    target = _module_target(win)
    rows = list(getattr(target, '_all_rows', []) or [])
    if rows:
        row = rows[-1]
        if hasattr(row, "get"):
            row["activo"] = 0
    if hasattr(target, '_on_filter_changed'):
        target._on_filter_changed("activos")
    _drain(qapp, cycles=6)


@_register_helper
def _avisos_search(win, qapp, action):
    """Escribe busqueda en Avisos."""
    target = _module_target(win)
    text = str(action.get("text", "medicacion")).lower()
    if hasattr(target, '_search_edit'):
        target._search_edit.setText(text)
    if hasattr(target, '_on_search'):
        target._on_search(text)
    _drain(qapp, cycles=6)


@_register_helper
def _avisos_complete_first(win, qapp, action):
    """Marca un aviso pendiente como completado en estado QA."""
    target = _module_target(win)
    rows = list(getattr(target, '_all_rows', []) or [])
    if rows:
        target_row = next(
            (row for row in rows if hasattr(row, "get") and not row.get("done")),
            rows[0],
        )
        if hasattr(target_row, "get"):
            target_row["done"] = True
        total = len(rows)
        done = sum(1 for row in rows if hasattr(row, "get") and row.get("done"))
        if hasattr(target, '_day_progress'):
            target._day_progress.set_stats(done, total)
        if hasattr(target, '_render_reminders'):
            target._render_reminders()
    _drain(qapp, cycles=8)


@_register_helper
def _clear_hub_patients(win, qapp, action):
    """Limpia la lista de pacientes del Hub para estados vacios.

    force_recreate=True es OBLIGATORIO: con la cache de vistas, el refresh
    suave solo reasigna _pacientes al DashboardView ya construido y este
    decide su empty-state EN EL CONSTRUCTOR — sin recrear, dashboard-empty
    capturaba el dashboard lleno."""
    if hasattr(win, '_pacientes'):
        win._pacientes = []
    if hasattr(win, '_refresh_all_views'):
        win._refresh_all_views(force_recreate=True)
    _drain(qapp, cycles=6)


@_register_helper
def _pacientes_search(win, qapp, action):
    """Escribe busqueda en Pacientes."""
    from shared.components import NMSearchInput
    for search_widget in win.findChildren(NMSearchInput):
        if search_widget.isVisible():
            search_widget.set_text("Ana")
            search_widget.text_changed.emit("Ana")
            break
    _drain(qapp, cycles=6)


@_register_helper
def _animo_clear_stats(win, qapp, action):
    """Vacía las stats de Animo por la rama real del producto: serie de
    valencia sin valores (usuario sin registros) → chart vacío y stats en
    '—' via _cargar_grafico/_refresh_insights reales."""
    target = _module_target(win)
    if hasattr(target, '_get_valence_series'):
        target._get_valence_series = lambda: ([None] * 7, [None] * 7)
    if hasattr(target, '_load_streak'):
        target._load_streak = lambda: 0
    if hasattr(target, '_cargar_grafico'):
        target._cargar_grafico()
    if hasattr(target, '_refresh_insights'):
        target._refresh_insights()
    _drain(qapp, cycles=6)


@_register_helper
def _sidebar_collapse(win, qapp, action):
    """Colapsa sidebar del Hub."""
    if hasattr(win, 'set_sidebar_collapsed'):
        win.set_sidebar_collapsed(True)
    _drain(qapp, cycles=6)


# ═══════════════════════════════════════════════════════════════════════════
# WIDGET FINDER
# ═══════════════════════════════════════════════════════════════════════════

def _norm_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value or "")
    asciiish = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return asciiish.casefold().strip()


def _find_widget(root, selector: dict) -> Any | None:
    """Busca un widget en la jerarquia de `root` que cumpla el selector."""
    from PyQt6.QtWidgets import QWidget
    widgets = root.findChildren(QWidget) if root else []
    candidates = list(widgets)

    if "type" in selector:
        type_name = selector["type"]
        candidates = [w for w in candidates if type(w).__name__ == type_name]

    if "text" in selector:
        t = _norm_text(selector["text"])
        candidates = [
            w for w in candidates
            if hasattr(w, 'text') and _norm_text(w.text()) == t
        ]

    if "text_contains" in selector:
        t = _norm_text(selector["text_contains"])
        candidates = [
            w for w in candidates
            if hasattr(w, 'text') and t in _norm_text(w.text())
        ]

    if "object_name" in selector:
        n = selector["object_name"]
        candidates = [w for w in candidates if w.objectName() == n]

    if "placeholder" in selector:
        ph = _norm_text(selector["placeholder"])
        candidates = [
            w for w in candidates
            if hasattr(w, 'placeholderText')
            and ph in _norm_text(w.placeholderText())
        ]

    if "visible" in selector:
        candidates = [w for w in candidates if w.isVisible()]

    if "at_index" in selector and "type" in selector:
        candidates = candidates[selector["at_index"]:selector["at_index"] + 1]

    if "property" in selector:
        pn, pv = selector["property"]
        candidates = [w for w in candidates if w.property(pn) == pv]

    return candidates[0] if candidates else None


# ═══════════════════════════════════════════════════════════════════════════
# CORE ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def _short_theme(modo: str) -> str:
    return "light" if "light" in modo else "dark"


def _parse_res(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def _parse_scale(value: str) -> float:
    try:
        scale = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--scale must be a number") from exc
    if scale <= 0 or scale > 4:
        raise argparse.ArgumentTypeError("--scale must be greater than 0 and no more than 4")
    return scale


def _scale_suffix(scale: float) -> str:
    if abs(scale - 1.0) < 0.0001:
        return ""
    scaled = int(round(scale * 100))
    return f"-scale{scaled}"


def _format_size(width: float, height: float) -> str:
    return f"{int(round(width))}x{int(round(height))}"


def _capture_contract(scale: float, is_dialog_or_auxiliary: bool) -> str:
    if is_dialog_or_auxiliary:
        return "natural_dialog"
    if abs(scale - 1.0) < 0.0001:
        return "main_base"
    if abs(scale - 1.25) < 0.0001:
        return "main_scale125"
    return "main_scaled_other"


def _is_dialog_or_auxiliary_widget(widget, main_window=None) -> bool:
    from PyQt6.QtWidgets import QDialog

    if widget is None:
        return False
    if isinstance(widget, QDialog):
        return True
    try:
        if widget.objectName() == "StandaloneCanvas":
            return False
    except Exception:
        pass
    if main_window is not None and widget is not main_window and hasattr(widget, "isWindow"):
        try:
            if not widget.isWindow():
                return False
            parent = widget.parentWidget()
            while parent is not None:
                if parent == main_window:
                    return True
                parent = parent.parentWidget()
        except Exception:
            return False
    return False


def _size_tuple(value: str | None) -> tuple[int, int] | None:
    if not value or "x" not in value:
        return None
    left, right = value.lower().split("x", 1)
    try:
        return int(round(float(left))), int(round(float(right)))
    except ValueError:
        return None


def _pixel_logical_dpr_coherent(result: dict, tolerance: int = 2) -> bool:
    logical = _size_tuple(result.get("captured_logical_resolution"))
    pixel = _size_tuple(result.get("captured_pixel_resolution") or result.get("actual_resolution") or result.get("resolution"))
    try:
        dpr = float(result.get("device_pixel_ratio") or 1.0)
    except (TypeError, ValueError):
        return False
    if logical is None or pixel is None or dpr <= 0:
        return False
    expected_w = int(round(logical[0] * dpr))
    expected_h = int(round(logical[1] * dpr))
    return abs(expected_w - pixel[0]) <= tolerance and abs(expected_h - pixel[1]) <= tolerance


def _append_flag(result: dict, flag: str, note: str | None = None) -> None:
    flags = result.setdefault("evidence_flags", [])
    if flag not in flags:
        flags.append(flag)
    if note:
        _append_note(result, note)


def _append_note(result: dict, note: str | None = None) -> None:
    if note:
        notes = result.setdefault("evidence_notes", [])
        if note not in notes:
            notes.append(note)


def _choose_status(flags: list[str]) -> str:
    if not flags:
        return _STATUS_CAPTURED_VALID
    for status in _STATUS_PRIORITY:
        if status in flags:
            return status
    return flags[0]


def _sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _git_value(args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=_PROJ,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _git_metadata() -> dict[str, Any]:
    tracked_status = _git_value(["status", "--short", "--untracked-files=no"])
    return {
        "head": _git_value(["rev-parse", "HEAD"]),
        "short_head": _git_value(["rev-parse", "--short", "HEAD"]),
        "branch": _git_value(["branch", "--show-current"]),
        "tracked_dirty": bool(tracked_status),
        "tracked_status": tracked_status.splitlines() if tracked_status else [],
    }


def _classify_initial_result(result: dict) -> None:
    result.setdefault("evidence_flags", [])
    result.setdefault("evidence_notes", [])
    result["technical_capture_valid"] = False
    result["state_evidence_valid"] = False

    if not result.get("success"):
        _append_flag(result, _STATUS_CAPTURE_FAILED)
        result["capture_status"] = _STATUS_CAPTURE_FAILED
        return

    requested = result.get("requested_logical_resolution") or result.get("requested_resolution")
    captured_logical = result.get("captured_logical_resolution") or result.get("actual_resolution") or result.get("resolution")
    scale = float(result.get("requested_scale_factor") or 1.0)
    is_dialog_or_auxiliary = bool(result.get("is_dialog_or_auxiliary") or result.get("is_child_dialog"))
    contract = result.get("evidence_contract") or _capture_contract(scale, is_dialog_or_auxiliary)
    logical_match = requested == captured_logical
    metadata_coherent = _pixel_logical_dpr_coherent(result)

    result["evidence_contract"] = contract
    if contract == "main_base":
        result["technical_capture_valid"] = bool(abs(scale - 1.0) < 0.0001 and logical_match and metadata_coherent)
    elif contract == "main_scale125":
        result["technical_capture_valid"] = bool(abs(scale - 1.25) < 0.0001 and logical_match and metadata_coherent)
    elif contract == "natural_dialog":
        result["technical_capture_valid"] = bool(is_dialog_or_auxiliary and metadata_coherent)
    else:
        result["technical_capture_valid"] = False

    if contract != "natural_dialog" and not logical_match:
        _append_flag(
            result,
            _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH,
            f"Main-view logical capture size {captured_logical} differs from requested {requested}.",
        )
    elif contract == "main_base" and abs(scale - 1.0) >= 0.0001:
        _append_flag(result, _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH, "main_base requires requested scale 1.0.")
    elif contract == "main_scale125" and abs(scale - 1.25) >= 0.0001:
        _append_flag(result, _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH, "main_scale125 requires requested scale 1.25.")
    elif contract in {"main_base", "main_scale125"} and not metadata_coherent:
        _append_flag(result, _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH, "Main-view logical/pixel/DPR metadata is incoherent.")
    elif contract == "natural_dialog":
        if not is_dialog_or_auxiliary:
            _append_flag(result, _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH, "natural_dialog requires explicit dialog or auxiliary capture context.")
        elif not metadata_coherent:
            _append_flag(result, _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH, "Natural dialog logical/pixel/DPR metadata is incoherent.")
        elif result["technical_capture_valid"]:
            _append_note(
                result,
                "Natural dialog capture accepted as technical evidence; inspect for complete content, clipping, overlap, and accessible controls.",
            )
    elif contract == "main_scaled_other":
        _append_note(
            result,
            "Diagnostic scaled capture only; this scale does not satisfy the current QA gate without an expressly authorized contract.",
        )
    else:
        _append_note(
            result,
            f"Unsupported capture contract '{contract}' is inspectable but does not satisfy the current QA gate.",
        )

    if str(result.get("view", "")).startswith(_CHILD_PREFIX):
        _append_flag(
            result,
            _STATUS_REQUIRES_RUNTIME,
            "Residual popup capture needs live route validation before visual conclusions.",
        )

    meta = _RECIPE_EVIDENCE_FLAGS.get((result.get("app"), result.get("view")))
    if meta:
        for flag in meta.get("flags", []):
            _append_flag(result, flag)
        for note in meta.get("notes", []):
            _append_note(result, note)


def _content_metrics(path: Path) -> dict[str, Any]:
    """Métricas de contenido del PNG: media y desvío tonal en escala de grises.

    No aprueba nada visualmente; solo detecta capturas vacías/planas/corruptas.
    """
    try:
        from PIL import Image, ImageStat

        with Image.open(path) as img:
            img.load()
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
        return {
            "gray_mean": round(stat.mean[0] / 255.0, 4),
            "gray_stddev": round(stat.stddev[0] / 255.0, 4),
        }
    except Exception as exc:  # corrupto / ilegible
        return {"error": str(exc)}


def _apply_content_validation(results: list[dict], out_dir: Path) -> None:
    for result in results:
        fname = result.get("file")
        if not result.get("success") or not fname:
            continue
        metrics = _content_metrics(out_dir / fname)
        result["content_metrics"] = metrics
        if "error" in metrics:
            result["technical_capture_valid"] = False
            _append_flag(
                result,
                _STATUS_BLANK_OR_FLAT,
                f"PNG ilegible/corrupto: {metrics['error']}",
            )
            continue
        mean = metrics["gray_mean"]
        stddev = metrics["gray_stddev"]
        if mean > _BLANK_MEAN_HI or mean < _BLANK_MEAN_LO or stddev < _FLAT_STDDEV:
            result["technical_capture_valid"] = False
            _append_flag(
                result,
                _STATUS_BLANK_OR_FLAT,
                f"Captura vacía o sin varianza (mean={mean}, stddev={stddev}).",
            )


def _mark_duplicate_groups(results: list[dict], out_dir: Path) -> list[dict]:
    by_hash: dict[str, list[dict]] = {}
    for result in results:
        fname = result.get("file")
        if not result.get("success") or not fname:
            continue
        digest = _sha256_file(out_dir / fname)
        result["sha256"] = digest
        if digest:
            by_hash.setdefault(digest, []).append(result)

    groups = []
    group_id = 0
    for digest, members in by_hash.items():
        if len(members) < 2:
            continue
        group_id += 1
        member_ids = [
            f"{m.get('app')}/{m.get('view')}/{m.get('theme')}"
            for m in members
        ]
        group = {
            "id": group_id,
            "sha256": digest,
            "count": len(members),
            "members": member_ids,
            "files": [m.get("file") for m in members],
        }
        groups.append(group)
        for member in members:
            member["duplicate_group_id"] = group_id
            member["duplicate_group_members"] = member_ids
            _append_flag(
                member,
                _STATUS_DUPLICATE_SUSPECT,
                "Exact PNG hash is shared with another screen/theme/state.",
            )
            parent = (
                _RECIPES
                .get(str(member.get("app")), {})
                .get(str(member.get("view")), {})
                .get("parent")
            )
            if parent and any(
                other.get("app") == member.get("app")
                and other.get("theme") == member.get("theme")
                and other.get("view") == parent
                for other in members
            ):
                _append_flag(
                    member,
                    _STATUS_FALLBACK,
                    "Exact duplicate of its declared parent recipe; state was not visually reached.",
                )
    return groups


def _finalize_evidence(results: list[dict], out_dir: Path) -> dict[str, Any]:
    for result in results:
        _classify_initial_result(result)

    _apply_content_validation(results, out_dir)
    duplicate_groups = _mark_duplicate_groups(results, out_dir)

    for result in results:
        flags = result.get("evidence_flags", [])
        result["capture_status"] = _choose_status(flags)
        result["state_evidence_valid"] = (
            result.get("success")
            and result.get("technical_capture_valid")
            and result["capture_status"] == _STATUS_CAPTURED_VALID
        )

    status_counts: dict[str, int] = {}
    for result in results:
        status = result.get("capture_status", _STATUS_CAPTURE_FAILED)
        status_counts[status] = status_counts.get(status, 0) + 1

    unique_hashes = {
        result.get("sha256")
        for result in results
        if result.get("sha256")
    }
    return {
        "semantic_visual_review": "NOT_RUN",
        "visual_review_outcome": "REVIEW_INCOMPLETE",
        "technical_capture_only": True,
        "state_valid_capture_count": sum(
            1 for result in results if result.get("state_evidence_valid")
        ),
        "technical_valid_capture_count": sum(
            1 for result in results if result.get("technical_capture_valid")
        ),
        "technical_960_capture_count": sum(
            1 for result in results
            if (
                result.get("technical_capture_valid")
                and result.get("requested_logical_resolution", result.get("requested_resolution")) == "960x600"
                and result.get("captured_logical_resolution", result.get("actual_resolution")) == "960x600"
            )
        ),
        "main_base_capture_count": sum(
            1 for result in results if result.get("evidence_contract") == "main_base"
        ),
        "main_scale125_capture_count": sum(
            1 for result in results if result.get("evidence_contract") == "main_scale125"
        ),
        "natural_dialog_capture_count": sum(
            1 for result in results if result.get("evidence_contract") == "natural_dialog"
        ),
        "main_scaled_other_capture_count": sum(
            1 for result in results if result.get("evidence_contract") == "main_scaled_other"
        ),
        "unsupported_contract_count": sum(
            1 for result in results
            if result.get("evidence_contract") not in {"main_base", "main_scale125", "natural_dialog", "main_scaled_other"}
        ),
        "invalid_or_unsupported_contract_count": sum(
            1 for result in results
            if (
                result.get("evidence_contract") == "main_scaled_other"
                or result.get("evidence_contract") not in {"main_base", "main_scale125", "natural_dialog"}
                or _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH in result.get("evidence_flags", [])
            )
        ),
        "contract_mismatch_count": sum(
            1 for result in results
            if _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH in result.get("evidence_flags", [])
        ),
        "unique_hash_count": len(unique_hashes),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_groups": duplicate_groups,
        "status_counts": status_counts,
        "requires_runtime": [
            result.get("file") for result in results
            if _STATUS_REQUIRES_RUNTIME in result.get("evidence_flags", [])
        ],
        "requires_data_state": [
            result.get("file") for result in results
            if _STATUS_REQUIRES_DATA_STATE in result.get("evidence_flags", [])
        ],
        "wrong_view_or_fallback": [
            result.get("file") for result in results
            if (
                _STATUS_WRONG_VIEW in result.get("evidence_flags", [])
                or _STATUS_FALLBACK in result.get("evidence_flags", [])
            )
        ],
        "main_capture_contract_mismatch": [
            result.get("file") for result in results
            if _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH in result.get("evidence_flags", [])
        ],
        "blank_or_flat": [
            result.get("file") for result in results
            if _STATUS_BLANK_OR_FLAT in result.get("evidence_flags", [])
        ],
    }


def _drain(app, cycles: int = 10, pause: float = 0.04) -> None:
    from PyQt6.QtCore import QCoreApplication, QEvent
    for _ in range(cycles):
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        time.sleep(pause)
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _apply_global_style(modo: str):
    from PyQt6.QtWidgets import QApplication
    from shared.theme_qt import stylesheet_base
    qa = QApplication.instance()
    if qa:
        qa.setStyleSheet(stylesheet_base(modo))


def _execute_actions(win, actions: list[dict], qapp, app_key: str,
                     modo: str, res: str, out_dir: Path,
                     results: list, captured_views: set, scale: float):
    """Ejecuta una secuencia de acciones sobre win, capturando en puntos
    marcados con action=capture."""
    for act in actions:
        action_type = act.get("action", "")
        target_win = globals().get('_CURRENT_STANDALONE') or win

        if action_type == "navigate":
            view_id = act["view"]
            if app_key == "suite":
                _navigate_suite(win, view_id, qapp)
            else:
                _navigate_hub(win, view_id, qapp)
            _drain(qapp, cycles=6)

        elif action_type == "click":
            widget = _find_widget(target_win, act)
            if widget and not getattr(widget, 'isVisible', lambda: False)():
                widget = None
            if widget:
                try:
                    widget.click()
                except Exception:
                    try:
                        widget.clicked.emit()
                    except Exception:
                        try:
                            widget.setChecked(True)
                        except Exception:
                            pass
            _drain(qapp, cycles=4)

        elif action_type == "set_tab":
            tab_text = act.get("tab_text", "")
            from PyQt6.QtWidgets import QTabBar
            tabs = target_win.findChildren(QTabBar)
            for tb in tabs:
                for i in range(tb.count()):
                    if tab_text in (tb.tabText(i) or ''):
                        tb.setCurrentIndex(i)
                        break
            # Tambien buscar NMTabs (custom)
            from shared.components import NMTabs
            for child in target_win.findChildren(NMTabs):
                if hasattr(child, 'set_current') and hasattr(child, '_labels'):
                    for i, label in enumerate(child._labels):
                        if _norm_text(tab_text) in _norm_text(label):
                            child.set_current(i)
                            break
            from shared.adaptive_layout_qt import NMSegmentedPanel
            for child in target_win.findChildren(NMSegmentedPanel):
                for i, btn in enumerate(getattr(child, "_buttons", []) or []):
                    if hasattr(btn, "text") and _norm_text(tab_text) in _norm_text(btn.text()):
                        stack = getattr(child, "_stack", None)
                        if stack is not None and hasattr(stack, "setCurrentIndex"):
                            stack.setCurrentIndex(i)
                        btn.setChecked(True)
                        break
            _drain(qapp, cycles=4)

        elif action_type == "type_text":
            widget = _find_widget(target_win, act)
            if widget and hasattr(widget, 'setText'):
                widget.setText(act.get("text", ""))
                if hasattr(widget, 'textChanged'):
                    widget.textChanged.emit(act.get("text", ""))
            elif widget and hasattr(widget, 'setPlainText'):
                widget.setPlainText(act.get("text", ""))
            _drain(qapp, cycles=3)

        elif action_type == "drain":
            _drain(qapp, cycles=act.get("cycles", 6))

        elif action_type == "call":
            func_name = act.get("func", "")
            func = _HELPERS.get(func_name)
            if func:
                func(win, qapp, act)

        elif action_type == "capture":
            view_id = act["view"]
            if view_id in captured_views:
                continue
            captured_views.add(view_id)
            is_auxiliary = _is_dialog_or_auxiliary_widget(target_win, win)
            r = _grab_save(target_win, app_key, view_id, modo, res, out_dir, scale, is_auxiliary)
            if r:
                results.append(r)

        elif action_type == "capture_child":
            prefix = act.get("prefix", _CHILD_PREFIX)
            _scan_and_capture_children(win, qapp, app_key, prefix, modo, res, out_dir, results, captured_views, scale)

        elif action_type == "close_child":
            from PyQt6.QtWidgets import QApplication
            for tl in QApplication.topLevelWidgets():
                if tl != win and tl.isVisible() and hasattr(tl, 'close'):
                    try:
                        tl.close()
                        tl.deleteLater()
                    except Exception:
                        pass


def _navigate_suite(win, view_id: str, qapp) -> None:
    if view_id == "home":
        if hasattr(win, "_go_home"):
            win._go_home()
    elif hasattr(win, "_open_module"):
        win._open_module(view_id)
    _drain(qapp)


def _navigate_hub(win, view_id: str, qapp) -> None:
    # Detalle tabs
    if view_id in ("detalle", "detalle-ia", "detalle-registros", "detalle-plan"):
        if hasattr(win, "_stack"):
            # Quitar y destruir cualquier widget en el stack que sea de tipo DetallePacienteView para evitar acumulacion
            from hub.pacientes_qt import DetallePacienteView
            i = 0
            while i < win._stack.count():
                w = win._stack.widget(i)
                if isinstance(w, DetallePacienteView):
                    win._stack.removeWidget(w)
                    w.deleteLater()
                else:
                    i += 1
        if hasattr(win, "_on_nav"):
            win._on_nav("pacientes")
        pacientes = list(getattr(win, "_pacientes", None) or [])
        if not pacientes:
            try:
                from shared.visual_qa import hub_patients
                pacientes = hub_patients()
            except Exception:
                pacientes = []
        if pacientes and hasattr(win, "_select_patient"):
            p = pacientes[0]
            win._select_patient(p.get("patient_id", ""), p.get("patient_name", ""))
        det = getattr(win, "_stack", None)
        if det and hasattr(det, "currentWidget"):
            det = det.currentWidget()
        if det is not None and hasattr(det, "_tabs"):
            _tab_map = {
                "detalle-ia": "_tab_ia",
                "detalle-registros": "_tab_reg",
                "detalle-plan": "_tab_plan",
            }
            tab_attr = _tab_map.get(view_id)
            if tab_attr and hasattr(det, tab_attr):
                det._tabs.setCurrentWidget(getattr(det, tab_attr))
    elif hasattr(win, "_on_nav"):
        win._on_nav(view_id)
    _drain(qapp)


def _grab_save(win, app_key: str, view_id: str, modo: str, res: str, out_dir: Path,
               scale: float, is_dialog_or_auxiliary: bool) -> dict | None:
    from PyQt6.QtWidgets import QApplication  # noqa: F811
    w, h = _parse_res(res)
    st = _short_theme(modo)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not win.isVisible():
        win.show()
    _drain(QApplication.instance(), cycles=4)

    try:
        pm = win.grab()
        real_w = pm.width()
        real_h = pm.height()
        dpr = float(pm.devicePixelRatio()) if hasattr(pm, "devicePixelRatio") else 1.0
        if dpr <= 0:
            dpr = 1.0
        if hasattr(pm, "deviceIndependentSize"):
            logical_size = pm.deviceIndependentSize()
            logical_w = float(logical_size.width())
            logical_h = float(logical_size.height())
        else:
            logical_w = real_w / dpr
            logical_h = real_h / dpr
        captured_logical = _format_size(logical_w, logical_h)
        captured_pixel = f"{real_w}x{real_h}"
        requested_logical = f"{w}x{h}"
        contract = _capture_contract(scale, is_dialog_or_auxiliary)
        suffix = _scale_suffix(scale)
        fname = f"{app_key}-{view_id}-{st}-{real_w}x{real_h}{suffix}.png"
        out_path = out_dir / fname
        ok = pm.save(str(out_path))
        return {"file": fname, "app": app_key, "view": view_id, "theme": st,
                "resolution": f"{real_w}x{real_h}",
                "requested_resolution": f"{w}x{h}",
                "requested_logical_resolution": requested_logical,
                "captured_logical_resolution": captured_logical,
                "captured_pixel_resolution": captured_pixel,
                "device_pixel_ratio": dpr,
                "requested_scale_factor": scale,
                "evidence_contract": contract,
                "success": ok,
                "size_bytes": out_path.stat().st_size if ok and out_path.exists() else 0,
                "is_dialog_or_auxiliary": is_dialog_or_auxiliary,
                "is_child_dialog": is_dialog_or_auxiliary,
                "actual_resolution": f"{real_w}x{real_h}"}
    except Exception as e:
        suffix = _scale_suffix(scale)
        fname = f"{app_key}-{view_id}-{st}-{w}x{h}{suffix}.png"
        return {"file": fname, "app": app_key, "view": view_id, "theme": st,
                "requested_resolution": f"{w}x{h}",
                "requested_logical_resolution": f"{w}x{h}",
                "requested_scale_factor": scale,
                "evidence_contract": _capture_contract(scale, is_dialog_or_auxiliary),
                "is_dialog_or_auxiliary": is_dialog_or_auxiliary,
                "is_child_dialog": is_dialog_or_auxiliary,
                "success": False, "error": str(e)}


def _scan_and_capture_children(win, qapp, app_key: str, prefix: str, modo: str,
                                res: str, out_dir: Path, results: list,
                                captured_views: set, scale: float) -> int:
    """Escanea ventanas hijas/popups visibles de la app actual y las captura."""
    from PyQt6.QtWidgets import QApplication, QDialog
    count = 0
    for tl in QApplication.topLevelWidgets():
        if tl == win or not tl.isVisible():
            continue
        # Filtrar por parentesco para no mezclar Suite/Hub
        is_child = False
        p = tl.parentWidget()
        while p is not None:
            if p == win:
                is_child = True
                break
            p = p.parentWidget()
        
        # O por modulo de procedencia (app.* para suite, hub.* para hub)
        module_name = tl.__class__.__module__
        belongs_to_app = module_name.startswith(app_key) or module_name.startswith("app.") if app_key == "suite" else module_name.startswith("hub")

        if (is_child or belongs_to_app) and isinstance(tl, QDialog):
            child_id = f"{prefix}-{count}"
            if child_id in captured_views:
                continue
            captured_views.add(child_id)
            r = _grab_save(tl, app_key, child_id, modo, res, out_dir, scale, True)
            if r:
                results.append(r)
                count += 1
    return count


# ═══════════════════════════════════════════════════════════════════════════
# CAPTURE SESSION
# ═══════════════════════════════════════════════════════════════════════════

def _capture_app_session(app_key: str, recipes: dict, modo: str, resolutions: list[str],
                         out_dir: Path, results: list, timeouts: dict, scale: float) -> None:
    """Ejecuta capturas aisladas por receta para una app + tema.

    Cada receta abre una ventana nueva. Esto evita que estados destructivos
    como pacientes-empty, dashboard-empty o formularios inline contaminen las
    recetas siguientes y mantiene V8 alineado con runtime_live_probe.
    """
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtCore import QSettings, QSize

    qapp = QApplication.instance()
    if not qapp:
        return
    qapp.setQuitOnLastWindowClosed(False)

    _apply_global_style(modo)

    spec = {
        "suite": {"module": "app.main_qt", "class": "NeuroMoodApp", "settings": "Suite"},
        "hub": {"module": "hub.main_qt", "class": "NeuroMoodHub", "settings": "Hub"},
    }[app_key]

    QSettings("NeuroMood", spec["settings"]).setValue("ui/theme", modo)
    module = importlib.import_module(spec["module"])
    WindowClass = getattr(module, spec["class"])

    for res in resolutions:
        w, h = _parse_res(res)
        for view_id, recipe in recipes.items():
            win = None
            captured_views: set[str] = set()

            print(f"    [{view_id}] ", end="", flush=True)
            try:
                QSettings("NeuroMood", spec["settings"]).setValue("ui/theme", modo)
                _apply_global_style(modo)
                win = WindowClass()
                win.show()
                if hasattr(win, "ensurePolished"):
                    win.ensurePolished()
                _drain(qapp, cycles=10)

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

                actions = recipe.get("actions", [])
                before_count = len(results)
                _execute_actions(win, actions, qapp, app_key, modo, res,
                                 out_dir, results, captured_views, scale)
                for r in results[before_count:]:
                    r["isolation_scope"] = "fresh_window_per_recipe"
                if view_id in captured_views:
                    print("CAPTURED")
                else:
                    print("NO_CAPTURE_POINT")
            except Exception as exc:
                import traceback
                msg = str(exc)[:100]
                print(f"FAIL ({msg})")
                results.append({
                    "file": None, "app": app_key, "view": view_id,
                    "theme": _short_theme(modo), "success": False,
                    "requested_resolution": res,
                    "requested_logical_resolution": res,
                    "requested_scale_factor": scale,
                    "evidence_contract": _capture_contract(scale, False),
                    "is_dialog_or_auxiliary": False,
                    "isolation_scope": "fresh_window_per_recipe",
                    "error": f"{exc.__class__.__name__}: {msg}",
                    "traceback": traceback.format_exc()[:1500],
                })
            finally:
                _old_standalone = globals().get('_CURRENT_STANDALONE')
                if _old_standalone is not None:
                    try:
                        _old_standalone.close()
                        _old_standalone.deleteLater()
                    except Exception:
                        pass
                    globals()['_CURRENT_STANDALONE'] = None
                if win is not None:
                    try:
                        win.close()
                        win.deleteLater()
                    except Exception:
                        pass
                for tl in QApplication.topLevelWidgets():
                    if tl != win and tl.isVisible():
                        try:
                            tl.close()
                            tl.deleteLater()
                        except Exception:
                            pass
                _drain(qapp, cycles=6)


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def _list_all() -> None:
    for app_key in ("suite", "hub"):
        recipes = _RECIPES.get(app_key, {})
        print(f"\n=== {app_key.upper()} ({len(recipes)} recipes) ===")
        for vid, rcp in sorted(recipes.items()):
            parent = rcp.get("parent", "-")
            label = rcp.get("label", "")
            print(f"  {vid:40s} parent={str(parent):20s} {label}")
    total = len(_RECIPES.get("suite", {})) + len(_RECIPES.get("hub", {}))
    print(f"\nTOTAL: {total} recipes x 2 themes = {total * 2} captures")


def _clean_output(out_dir: Path) -> int:
    if not out_dir.exists():
        return 0
    count = sum(1 for _ in out_dir.rglob("*") if _.is_file())
    if count > 0:
        trash_root = _PROJ / "_scratch_trash"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        trash_run_dir = trash_root / f"captures_v8_{timestamp}"
        try:
            trash_run_dir.mkdir(parents=True, exist_ok=True)
            for item in out_dir.iterdir():
                shutil.move(str(item), str(trash_run_dir / item.name))
            print(f"[OUTPUT_ROTATED] {count} archivos viejos movidos a {trash_run_dir}")
        except Exception as e:
            # Fallback a rmtree si falla la movida
            shutil.rmtree(out_dir, ignore_errors=True)
            out_dir.mkdir(parents=True, exist_ok=True)
            print(f"[OUTPUT_REMOVED] Falló mover a _scratch_trash ({e}). {count} archivos eliminados de {out_dir}")
    return count



def _discover_all_view_ids() -> list[tuple[str, str]]:
    """Retorna todos los view_ids para --all. Suite + Hub."""
    ids = []
    for app_key in ("suite", "hub"):
        for vid in _RECIPES.get(app_key, {}):
            ids.append((app_key, vid))
    return ids


def _select_recipes(targets: list[tuple[str, str]], app_filter: str | None) -> dict[str, dict]:
    """Devuelve recetas por app respetando filtro y targets normalizados."""
    selected: dict[str, dict] = {"suite": {}, "hub": {}}
    target_set = set(targets)
    for app_key in ("suite", "hub"):
        if app_filter and app_filter != app_key:
            continue
        selected[app_key] = {
            view_id: recipe
            for view_id, recipe in _RECIPES.get(app_key, {}).items()
            if (app_key, view_id) in target_set
        }
    return selected


def _selected_target_count(selected: dict[str, dict]) -> int:
    return sum(len(recipes) for recipes in selected.values())


def _run_child_capture(app_key: str, view_id: str, theme_label: str, res: str,
                       out_dir: Path, scale: float) -> tuple[int, list[dict], str]:
    """Ejecuta una receta en un proceso Qt propio y devuelve resultados."""
    manifest_path = out_dir / "CAPTURE_MANIFEST.json"
    try:
        if manifest_path.exists():
            manifest_path.unlink()
    except Exception:
        pass

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--app", app_key,
        "--view", view_id,
        "--theme", theme_label,
        "--res", res,
        "--out-dir", str(out_dir),
        "--scale", str(scale),
        "--no-clean",
        "--_child-single",
    ]
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env.setdefault("NM_VISUAL_QA", "1")
    env["QT_SCALE_FACTOR"] = str(scale)
    env["NM_V8_CHILD"] = "1"

    completed = subprocess.run(
        cmd,
        cwd=str(_PROJ),
        env=env,
        text=True,
        capture_output=True,
        timeout=240,
    )

    output = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
    if completed.returncode == 0 and manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            child_results = manifest.get("results", [])
            for result in child_results:
                result["isolation_scope"] = "subprocess_per_recipe"
            return completed.returncode, child_results, output
        except Exception as exc:
            return 1, [], f"{output}\nmanifest read error: {exc}"

    return completed.returncode, [], output


def _capture_matrix_in_subprocesses(selected: dict[str, dict], themes: list[str],
                                    resolutions: list[str], out_dir: Path, scale: float) -> list[dict]:
    """Alinea V8 con runtime_live_probe: proceso fresco por vista x tema x res."""
    results: list[dict] = []
    for modo in themes:
        theme_label = _short_theme(modo)
        print(f"\n--- {theme_label.upper()} ---")
        for app_key in ("suite", "hub"):
            recipes = selected.get(app_key, {})
            if not recipes:
                continue
            print(f"  {app_key.upper()} ({len(recipes)} recipes)")
            for view_id in recipes:
                for res in resolutions:
                    print(f"    [{view_id}] ", end="", flush=True)
                    code, child_results, output = _run_child_capture(
                        app_key, view_id, theme_label, res, out_dir, scale
                    )
                    if child_results:
                        results.extend(child_results)
                        if all(r.get("success") for r in child_results):
                            print("CAPTURED")
                        else:
                            print("FAIL")
                    else:
                        print("FAIL")
                        results.append({
                            "file": None,
                            "app": app_key,
                            "view": view_id,
                            "theme": theme_label,
                            "success": False,
                            "requested_resolution": res,
                            "requested_logical_resolution": res,
                            "requested_scale_factor": scale,
                            "evidence_contract": _capture_contract(scale, False),
                            "is_dialog_or_auxiliary": False,
                            "isolation_scope": "subprocess_per_recipe",
                            "error": f"child process returned {code}",
                            "traceback": output[:1500],
                        })
    return results


def main() -> int:
    p = argparse.ArgumentParser(description="Exhaustive V8 PyQt6 offscreen capture harness")
    p.add_argument("--app", choices=["suite", "hub"])
    p.add_argument("--view", default="")
    p.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    p.add_argument("--res", action="append", default=[])
    p.add_argument("--all", action="store_true", help="Regresion final completa: captura todas las recetas de Suite+Hub")
    p.add_argument("--list", action="store_true", help="Listar recetas registradas")
    p.add_argument(
        "--clean",
        action="store_true",
        help="Limpiar antes de capturar; si se usa sin --all/--view, solo limpia.",
    )
    p.add_argument("--no-clean", action="store_true", help="No limpiar antes de capturar")
    p.add_argument("--out-dir", default=str(_DEFAULT_OUT))
    p.add_argument("--scale", type=_parse_scale, default=1.0, help="Qt scale factor for capture subprocesses (for example: 1.25)")
    p.add_argument("--_child-single", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    scale = float(args.scale)
    os.environ["QT_SCALE_FACTOR"] = str(scale)

    if args.list:
        _list_all()
        return 0

    # Targets
    targets: list[tuple[str, str]] = []
    if args.all:
        targets = _discover_all_view_ids()
    elif args.view:
        app_key = args.app or "suite"
        view_name = args.view
        if app_key == "hub" and view_name.startswith("hub-") and view_name not in _RECIPES[app_key]:
            view_name = view_name[4:]
        if app_key == "suite" and view_name.startswith("suite-") and view_name not in _RECIPES[app_key]:
            view_name = view_name[6:]
        
        if view_name in _RECIPES.get(app_key, {}):
            targets = [(app_key, view_name)]
        else:
            print(f"[ERROR] Vista '{args.view}' no encontrada en {app_key}. Usa --list.")
            return 1
    elif args.clean:
        _clean_output(out_dir)
        return 0
    else:
        p.print_help()
        return 1

    if not targets:
        print("[ERROR] Sin vistas. Usa --view para una modificacion puntual o --all para regresion final completa.")
        return 1

    # Clean
    if not args.no_clean:
        _clean_output(out_dir)

    themes = ["light_hybrid", "dark_hybrid"] if args.theme == "both" else [_THEME_MAP[args.theme]]
    resolutions = args.res or _DEFAULT_RES

    selected = _select_recipes(targets, args.app)
    suite_recipes = selected["suite"]
    hub_recipes = selected["hub"]
    expected_recipe_captures = _selected_target_count(selected) * len(themes) * len(resolutions)

    print(f"\n{'='*60}")
    print("CAPTURE V8 — Exhaustive Harness")
    print(f"Suite recipes: {len(suite_recipes)} | Hub recipes: {len(hub_recipes)}")
    print(f"Themes: {len(themes)} | Scale: {scale:g} | Output: {out_dir}")
    print(f"{'='*60}\n")

    results: list[dict] = []
    start = time.time()

    if args._child_single:
        from PyQt6.QtWidgets import QApplication
        _qapp = QApplication.instance() or QApplication(sys.argv)
        _qapp.setQuitOnLastWindowClosed(False)
        from shared.fonts import load_fonts
        load_fonts()

        for modo in themes:
            theme_label = _short_theme(modo)
            print(f"\n--- {theme_label.upper()} ---")

            if suite_recipes:
                print(f"  SUITE ({len(suite_recipes)} recipes)")
                _capture_app_session("suite", suite_recipes, modo, resolutions, out_dir, results, {}, scale)

            if hub_recipes:
                print(f"  HUB ({len(hub_recipes)} recipes)")
                _capture_app_session("hub", hub_recipes, modo, resolutions, out_dir, results, {}, scale)
    else:
        results = _capture_matrix_in_subprocesses(selected, themes, resolutions, out_dir, scale)

    elapsed = time.time() - start
    success = sum(1 for r in results if r.get("success"))
    failed = sum(1 for r in results if not r.get("success"))
    total = len(results)
    evidence_summary = _finalize_evidence(results, out_dir)
    state_valid = evidence_summary["state_valid_capture_count"]
    technical_valid = evidence_summary["technical_valid_capture_count"]
    technical_960 = evidence_summary["technical_960_capture_count"]

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"  Saved captures:       {success}")
    print(f"  Failed captures:      {failed}")
    print(f"  Total results:        {total}")
    print(f"  Technical evidence:   {technical_valid}")
    print(f"  Technical 960x600:    {technical_960}")
    print(f"  State-valid evidence: {state_valid}")
    print(f"  Time:                 {elapsed:.1f}s")
    print(f"{'='*60}")

    manifest = {
        "harness": "capture_v8.py",
        "generated_at": datetime.datetime.now().isoformat(),
        "git": _git_metadata(),
        "command": sys.argv,
        "cwd": str(_PROJ),
        "isolation_scope": "fresh_window_per_recipe" if args._child_single else "subprocess_per_recipe",
        "auto_residual_popup_capture": False,
        "success": success,
        "failed": failed,
        "total": total,
        "expected_recipe_captures": expected_recipe_captures,
        "elapsed_seconds": round(elapsed, 1),
        "themes": [_short_theme(t) for t in themes],
        "resolutions": resolutions,
        "requested_scale_factor": scale,
        "output_dir": str(out_dir),
        "evidence_summary": evidence_summary,
        "results": results,
    }
    manifest_path = out_dir / "CAPTURE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nManifest: {manifest_path}")

    print("\n" + "=" * 60)
    print("TECHNICAL_CAPTURE_ONLY")
    print("Semantic visual review: NOT_RUN")
    print("Visual review outcome: REVIEW_INCOMPLETE")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
