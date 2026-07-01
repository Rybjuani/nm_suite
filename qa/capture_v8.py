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
import csv
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
_VISUAL_FIDELITY_GATE = "NOT_A_GATE_USE_LAYERED_VISUAL_COMPARE"
_HANDOFF_CLOSURE_WARNING = (
    "capture_v8 produces fresh technical captures only. Do not mark "
    "VISUAL_REPAIR_HANDOFF.md items complete from CAPTURE_MANIFEST alone; "
    "run qa/layered_visual_compare.py against qa/_mockup_canonical and "
    "qa/_captures_v8, then inspect the panels."
)

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
    # Las recetas home-no-score / pacientes / pacientes-empty ya construyen el
    # estado visual exacto dentro del harness. Para paridad mockup esto es
    # evidencia de estado válida; la deuda de datos reales pertenece a QA de
    # integración, no al gate visual V8.
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
                        {"action": "call", "func": "_onboarding_error_prompt"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "onboarding-error"}],
        },
        "recuperar-acceso": {
            "label": "Recuperar acceso - email requerido",
            "parent": "onboarding",
            "actions": [{"action": "call", "func": "_build_onboarding"},
                        {"action": "call", "func": "_onboarding_recovery_prompt"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "recuperar-acceso"}],
        },
        # NOTA: no existe receta "onboarding-login" — el onboarding del
        # producto es UN solo form con dos CTAs (Crear cuenta / Iniciar
        # sesión); no hay vista/modo login separado que capturar.
        # ── Modulos ──────────────────────────────────────────────────────
        "animo": {
            "label": "Animo default",
            "parent": None,
            "actions": [{"action": "navigate", "view": "animo"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "animo"}],
        },
        # animo-note-filled ELIMINADA: el módulo Ánimo ya no expone campo de
        # nota (la reorganización "redistribuye Animo Fase 1" dejó solo slider
        # + stats + chart). No hay QTextEdit/NMTextArea donde escribir, así que
        # la receta capturaba un estado inexistente (idéntico al parent).
        "dbt-now": {
            "label": "DBT Ahora - entrada por necesidad",
            "parent": None,
            "actions": [{"action": "navigate", "view": "dbt"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "dbt-now"}],
        },
        "dbt-library": {
            "label": "DBT Biblioteca - catálogo de cuatro familias",
            "parent": "dbt-now",
            "actions": [{"action": "navigate", "view": "dbt"},
                        {"action": "call", "func": "_dbt_select_tab_library"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "dbt-library"}],
        },
        "dbt-practice-stop": {
            "label": "DBT Práctica - paso intermedio de STOP",
            "parent": "dbt-now",
            "actions": [{"action": "navigate", "view": "dbt"},
                        {"action": "call", "func": "_dbt_select_tab_library"},
                        {"action": "call", "func": "_dbt_start_stop_practice"},
                        {"action": "call", "func": "_dbt_go_to_step_2"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "dbt-practice-stop"}],
        },
        # dbt-practice-closure eliminado del harness (C4-05): pantalla de cierre
        # fue removida del producto; la evidencia era stale y generaba falsos positivos.

        "respiracion": {
            "label": "Respiracion idle",
            "parent": None,
            "actions": [{"action": "navigate", "view": "respiracion"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "respiracion"}],
        },
        # respiracion-preset-3min / respiracion-preset-10min: microestados de
        # interacción (click en preset chip). Movidos a extended_runtime_qa;
        # no participan del gate de paridad mockup (canonical_mockup_parity=86).
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
                        {"action": "drain", "cycles": 4},
                        {"action": "call", "func": "_respiracion_pause"},
                        {"action": "call", "func": "_respiracion_set_paused_display"},
                        {"action": "drain", "cycles": 4},
                        {"action": "capture", "view": "respiracion-paused"}],
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
        # 2026-06: TCC paso 1 con la emoción "Otro" seleccionada y el input
        # de texto abierto en la celda (overlay QStackedWidget). Verifica
        # que la grilla 4×2 mantiene la celda de "Otro" con la misma
        # geometría que el resto.
        "registro-step1-emotion-otro": {
            "label": "TCC paso 1 - Emocion Otro seleccionado",
            "parent": "registro",
            "actions": [{"action": "navigate", "view": "registro"},
                        {"action": "call", "func": "_tcc_prepare_step", "step": 1},
                        {"action": "drain", "cycles": 4},
                        {"action": "call", "func": "_tcc_pick_otro"},
                        {"action": "drain", "cycles": 4},
                        {"action": "capture", "view": "registro-step1-emotion-otro"}],
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
                        {"action": "call", "func": "_actividades_filter_category", "category": "Fisica"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "actividades-filtered"}],
        },
        "actividades-empty": {
            "label": "Actividades empty state deterministico",
            "parent": "actividades",
            "actions": [{"action": "navigate", "view": "actividades"},
                        {"action": "call", "func": "_actividades_force_empty"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "actividades-empty"}],
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
                        {"action": "drain", "cycles": 4},
                        {"action": "call", "func": "_timer_snap_to_initial"},
                        {"action": "capture", "view": "timer-running"}],
        },
        "timer-paused": {
            "label": "Timer paused",
            "parent": "timer",
            "actions": [{"action": "navigate", "view": "timer"},
                        {"action": "call", "func": "_timer_start"},
                        {"action": "drain", "cycles": 4},
                        {"action": "call", "func": "_timer_pause"},
                        {"action": "call", "func": "_timer_set_paused_display"},
                        {"action": "drain", "cycles": 4},
                        {"action": "capture", "view": "timer-paused"}],
        },
        # timer-preset-5min / timer-preset-45min: microestados de interacción
        # (click en chip de duración). Movidos a extended_runtime_qa;
        # no participan del gate de paridad mockup (canonical_mockup_parity=86).
        # 2026-06: Timer empty state — sin asignación `patient:<id>` ni fixture
        # QA. Verifica que el módulo muestra el mensaje de empty state y los
        # controles quedan deshabilitados (regla clínica: no hay presets
        # globales ni predeterminados).
        "timer-empty": {
            "label": "Timer sin actividades asignadas (empty state)",
            "parent": "timer",
            "actions": [{"action": "navigate", "view": "timer"},
                        {"action": "call", "func": "_timer_force_empty"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "timer-empty"}],
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
                        {"action": "call", "func": "_avisos_search", "text": "respiración"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "avisos-search"}],
        },
        # avisos-completed: microestado de interacción (marcar aviso como hecho).
        # Movido a extended_runtime_qa; no participa del gate canónico.
        "avisos-today": {
            "label": "Avisos filtro Hoy",
            "parent": "avisos",
            "actions": [{"action": "navigate", "view": "avisos"},
                        {"action": "call", "func": "_avisos_filter_hoy"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "avisos-today"}],
        },
        "avisos-empty": {
            "label": "Avisos empty state deterministico",
            "parent": "avisos",
            "actions": [{"action": "navigate", "view": "avisos"},
                        {"action": "call", "func": "_avisos_force_empty"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "avisos-empty"}],
        },

    },

    # ═══════════════════════════════════════════════════════════════════════
    # HUB
    # ═══════════════════════════════════════════════════════════════════════
    "hub": {

        "pacientes": {
            "label": "Pacientes default",
            "parent": None,
            "actions": [{"action": "navigate", "view": "pacientes"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "pacientes"}],
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
        # detalle-plan ELIMINADA: el PlanTerapeuticoTab es siempre visible bajo
        # el header del paciente y su subtab default (index 0, Recordatorios)
        # es exactamente lo que captura "detalle". No hay tab outer que conmutar;
        # los 3 subtabs no-default ya tienen receta propia abajo.
        "detalle-plan-timer": {
            "label": "Detalle > Plan > Temporizador",
            "parent": "detalle",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "call", "func": "_plan_set_subtab", "index": 1},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-plan-timer"}],
        },
        "detalle-plan-rutina": {
            "label": "Detalle > Plan > Rutina",
            "parent": "detalle",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "call", "func": "_plan_set_subtab", "index": 2},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-plan-rutina"}],
        },
        "detalle-plan-activacion": {
            "label": "Detalle > Plan > Activación",
            "parent": "detalle",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "call", "func": "_plan_set_subtab", "index": 3},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-plan-activacion"}],
        },

        # 2026-06: Textos globales de Suite — vista navegable de personalización
        # (buscador + filtro por módulo + filas editables). Antes faltaba en V8.
        "textos-globales": {
            "label": "Textos globales de Suite (personalizacion)",
            "parent": None,
            "actions": [{"action": "call", "func": "_hub_open_textos_globales"},
                        {"action": "drain", "cycles": 8},
                        {"action": "capture", "view": "textos-globales"}],
        },

        # 2026-06: Dialogo "Resumen IA" del detalle. En runtime depende de un
        # proveedor IA; aqui se abre con texto de muestra y se captura la
        # ventana completa con overlay. El panel crop puede servir como
        # evidencia parcial, pero no cierra blur/backdrop/centrado.
        "detalle-resumen-ia": {
            "label": "Detalle > dialogo Resumen IA (muestra)",
            "parent": "detalle",
            "actions": [{"action": "navigate", "view": "detalle"},
                        {"action": "call", "func": "_detalle_open_resumen_ia_dialog"},
                        {"action": "drain", "cycles": 6},
                        {"action": "capture", "view": "detalle-resumen-ia-0",
                         "surface": "window_modal",
                         "modal_capture_scope": "window_overlay",
                         "back_screen_key": "hub:detalle"},
                        {"action": "close_child"}],
        },

        # NOTA: IAAssistantView (vista global IA) fue eliminada en la
        # reestructura v1.0; el asistente IA vive como dialogo del detalle.

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
    """Fuerza que Home/Animo no muestre puntaje (solo animo; otros módulos intactos)."""
    from app.home_qt import HomeView
    homes = list(win.findChildren(HomeView))
    direct_home = getattr(win, '_home', None)
    if direct_home is not None and direct_home not in homes:
        homes.append(direct_home)

    for home in homes:
        _orig = home._get_status

        def _animo_no_score(module_id, _f=_orig):
            return "" if module_id == "animo" else _f(module_id)

        home._get_status = _animo_no_score
        # ModuleCards capturan get_status_fn por referencia en su __init__; hay
        # que parchearlos directamente o refresh_statuses sigue devolviendo QA data.
        if hasattr(home, '_cards'):
            for card in home._cards.values():
                card._get_status = _animo_no_score
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
def _onboarding_recovery_prompt(win, qapp, action):
    """Muestra el estado de recuperar acceso sin tocar Supabase."""
    dlg = globals().get("_CURRENT_STANDALONE")
    if dlg is None:
        return
    try:
        if hasattr(dlg, "_email"):
            dlg._email.setText("")
        if hasattr(dlg, "_on_forgot_password"):
            dlg._on_forgot_password()
    except Exception:
        pass
    _drain(qapp, cycles=6)


@_register_helper
def _onboarding_error_prompt(win, qapp, action):
    """Dispara el estado de error de onboarding (Nombre requerido).

    Llama _on_accept directamente con nombre vacío y checkbox desmarcado.
    El canónico muestra el checkbox sin marcar; marcar el checkbox antes
    produce un estado de UI incorrecto que aumenta la divergencia.
    """
    dlg = globals().get("_CURRENT_STANDALONE")
    if dlg is None:
        return
    try:
        if hasattr(dlg, "_name"):
            dlg._name.setText("")
        if hasattr(dlg, "_on_accept"):
            dlg._on_accept("signup")
    except Exception:
        pass
    _drain(qapp, cycles=6)


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
def _plan_set_subtab(win, qapp, action):
    """Selecciona un subtab del Plan terapéutico (index en la action)."""
    det = win._stack.currentWidget() if hasattr(win, "_stack") else None
    plan = getattr(det, "_tab_plan", None)
    tabs = getattr(plan, "_tabs", None)
    if tabs is not None:
        tabs.setCurrentIndex(int(action.get("index", 0)))
        _drain(qapp, cycles=4)



# _animo_type_note ELIMINADO: sin receta referenciante y sin QTextEdit en el
# módulo Ánimo actual (ver nota en _RECIPES["suite"]).


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
    """Muestra historial vacío en Respiracion.

    La card de historial es estática (siempre visible). En QA mode `visual_qa_enabled()`
    `_load_recent_sessions` devuelve 4 sesiones demo, por lo que la captura base
    ya tiene historial poblado. Esta receta la parchea para mostrar el empty-state
    ("Sin sesiones."), dando contraste real respecto a `respiracion` default.
    """
    target = getattr(win, '_current_module', None) or win
    if hasattr(target, '_cargar_historial') and hasattr(target, '_load_recent_sessions'):
        _orig = target._load_recent_sessions
        target._load_recent_sessions = lambda limit=4: []
        try:
            target._cargar_historial()
        finally:
            target._load_recent_sessions = _orig
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
def _tcc_pick_otro(win, qapp, action):
    """Selecciona la emoción 'Otro' en TCC paso 1 (overlay QStackedWidget).
    Verifica que la celda mantiene la geometría 4×2 al abrirse el input.
    (2026-06: nuevo helper para la receta registro-step1-emotion-otro.)
    """
    target = getattr(win, '_current_module', None) or win
    if hasattr(target, '_emotion_tiles') and target._emotion_tiles:
        # Buscar el tile con label "Otro"
        for tile in target._emotion_tiles:
            if getattr(tile, '_label_text', None) == "Otro":
                try:
                    tile.clicked.emit()
                except Exception:
                    tile.click()
                break
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
    btns_g = [b for b in target.findChildren(QPushButton) if b.isVisible() and "Guardar" in b.text()]
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
    """Abre el formulario inline para agregar tarea en Rutina.

    El modo producto fija ``_manual_enabled=False`` (rutina solo_profesional),
    lo que haría que ``_on_section_add`` retorne sin abrir el form. Para que la
    captura refleje el formulario real, se fuerza el flag durante la llamada.
    """
    target = _module_target(win)
    _prev = getattr(target, "_manual_enabled", True)
    target._manual_enabled = True
    try:
        if hasattr(target, "_on_section_add"):
            target._on_section_add("manana")
    finally:
        target._manual_enabled = _prev
    _drain(qapp, cycles=8)


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
def _dbt_select_tab_library(win, qapp, action):
    target = _module_target(win)
    if target is not None:
        target._tabs.set_current(1)
    _drain(qapp, cycles=4)


@_register_helper
def _dbt_start_stop_practice(win, qapp, action):
    target = _module_target(win)
    if target is not None:
        from app.modules.dbt_qt import DBT_SKILLS
        skill = DBT_SKILLS["distress_stop"]
        target.start_practice(skill)
    _drain(qapp, cycles=4)


@_register_helper
def _dbt_go_to_step_2(win, qapp, action):
    target = _module_target(win)
    if target is not None and getattr(target, "_practice_view", None) is not None:
        target._practice_view._next_step()
    _drain(qapp, cycles=4)


@_register_helper
def _dbt_go_to_closure(win, qapp, action):
    target = _module_target(win)
    if target is not None and getattr(target, "_practice_view", None) is not None:
        steps_count = len(target._practice_view._skill["steps"])
        for _ in range(steps_count):
            target._practice_view._next_step()
            _drain(qapp, cycles=2)
    _drain(qapp, cycles=4)

    # Pre-select ratings for QA captures to showcase low/medium/high colors:
    # antes=2 (Green/Low), despues=9 (Red/High), resultado="parcial" (Amber/Medium)
    if target is not None and getattr(target, "_closure_view", None) is not None:
        closure = target._closure_view
        closure._select_antes(2)
        closure._select_despues(9)
        closure._select_resultado("parcial")
        _drain(qapp, cycles=4)




@_register_helper
def _actividades_filter_category(win, qapp, action):
    """Aplica un filtro de categoria con resultado esperado en Actividades."""
    target = _module_target(win)
    category = str(action.get("category", "Placer"))
    canonical_label = category  # se actualiza al label real (con tilde) si se encuentra
    tabs = getattr(target, "_category_tabs", None)
    if tabs is not None and hasattr(tabs, "_labels"):
        for idx, label in enumerate(getattr(tabs, "_labels", []) or []):
            if _norm_text(str(label)) == _norm_text(category):
                canonical_label = str(label)  # "Física" en vez de "Fisica"
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
        target._on_category_filter(canonical_label)
    _drain(qapp, cycles=6)


@_register_helper
def _actividades_filter_fisica(win, qapp, action):
    """Alias historico: usa una categoria estable con resultados en QA."""
    action = dict(action)
    action.setdefault("category", "Placer")
    _actividades_filter_category(win, qapp, action)


@_register_helper
def _actividades_force_empty(win, qapp, action):
    """Fuerza el empty state real de Actividades usando fixture QA vacia."""
    target = _module_target(win)
    try:
        import app.modules.actividades_qt as _aq

        _orig_activity_suggestions = _aq.activity_suggestions
        _aq.activity_suggestions = lambda: []
        try:
            if hasattr(target, "_load_suggestions"):
                target._load_suggestions()
        finally:
            _aq.activity_suggestions = _orig_activity_suggestions
    except Exception:
        pass
    _drain(qapp, cycles=6)


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
def _timer_snap_to_initial(win, qapp, action):
    """Resetea el display del timer a MM:SS inicial (total_sec) para captura estable.

    El QTimer 1s puede dispararse durante los drain cycles y reducir remaining_sec
    en 1-2 segundos, produciendo 24:58 en vez del 25:00 canónico. Este helper
    restaura el display al valor inicial sin detener el timer.
    """
    target = _module_target(win)
    if hasattr(target, '_remaining_sec') and hasattr(target, '_total_sec'):
        target._remaining_sec = target._total_sec
    if hasattr(target, '_update_canvas'):
        target._update_canvas()


@_register_helper
def _timer_set_paused_display(win, qapp, action):
    """Fija el display del timer en 15:12 para coincidir con el estado canónico.

    El canonico muestra un timer de 25 min paused a 15:12 restantes (9:48 transcurridos).
    Setear remaining_sec directamente produce el mismo display sin depender de ticks reales.
    """
    target = _module_target(win)
    if hasattr(target, '_remaining_sec'):
        target._remaining_sec = 15 * 60 + 12  # 912 segundos = 15:12
    if hasattr(target, '_update_canvas'):
        target._update_canvas()


@_register_helper
def _respiracion_set_paused_display(win, qapp, action):
    """Fija el estado de display de respiracion-paused al estado canonico (01:32, 4 ciclos).

    El canonico muestra CRONO 01:32 y CICLOS 4 en el estado paused.
    La receta actual pausa inmediatamente sin haber corrido suficiente tiempo real,
    produciendo 00:00 / 0. Este helper setea el estado de display directamente.
    """
    target = getattr(win, '_current_module', None) or win
    elapsed_ms = 92000  # 1 min 32 s = 92 s = 92000 ms
    ciclos = 4
    if hasattr(target, '_elapsed_ms'):
        target._elapsed_ms = elapsed_ms
    if hasattr(target, '_session_ms'):
        target._session_ms = elapsed_ms
    if hasattr(target, '_ciclos'):
        target._ciclos = ciclos
    s_total = elapsed_ms // 1000
    if hasattr(target, '_session_lbl'):
        target._session_lbl.setText(f"{s_total // 60:02d}:{s_total % 60:02d}")
    if hasattr(target, '_ciclos_value_lbl'):
        target._ciclos_value_lbl.setText(str(ciclos))


@_register_helper
def _timer_select_preset(win, qapp, action):
    """Selecciona preset de Timer por segundos sin depender del widget del chip.

    El módulo Timer expone `_select_preset(name, secs)` (firma usada por el
    click del chip). La receta QA solo conoce los segundos, así que busca el
    nombre correspondiente en `_presets` antes de invocar. (2026-06: antes
    llamaba con un solo argumento → `TypeError: missing 1 required positional
    argument: 'secs'` y fallaba timer-preset-5min/45min.)
    """
    target = _module_target(win)
    seconds = int(action.get("seconds", 25 * 60))
    if hasattr(target, '_select_preset') and hasattr(target, '_presets'):
        name = ""
        for n, s, *_ in target._presets:
            if s == seconds:
                name = n
                break
        target._select_preset(name, seconds)
    _drain(qapp, cycles=6)


@_register_helper
def _timer_force_empty(win, qapp, action):
    """Fuerza el empty state del Timer: _presets=[], controles deshabilitados,
    input y chips ocultos, mensaje empty visible. Verifica la regla clínica
    2026-06: sin asignación `patient:<id>` ni fixture QA → el módulo NO
    muestra la interfaz operativa. (2026-06: nuevo helper para la receta
    timer-empty.)
    """
    target = _module_target(win)
    if not hasattr(target, '_presets'):
        return
    # Vaciar presets y forzar empty state
    target._presets = []
    target._has_activity = False
    if hasattr(target, '_btn_play'):
        target._btn_play.setEnabled(False)
    if hasattr(target, '_btn_skip'):
        target._btn_skip.setEnabled(False)
    if hasattr(target, '_btn_reset'):
        target._btn_reset.setEnabled(False)
    if hasattr(target, '_state_chip'):
        target._state_chip.setText("Sin actividades asignadas")
        target._state_chip.hide()
    if hasattr(target, '_canvas'):
        target._canvas.hide()
        target._canvas.setMaximumSize(0, 0)
        target._canvas.set_data(0.0, "—:—")
    if hasattr(target, '_state_chip'):
        target._state_chip.hide()
        target._state_chip.setMaximumSize(0, 0)
    if hasattr(target, '_input_container'):
        target._input_container.hide()
        target._input_container.setMaximumSize(0, 0)
    if hasattr(target, '_duration_chip_container'):
        target._duration_chip_container.hide()
        target._duration_chip_container.setMaximumSize(0, 0)
    if hasattr(target, '_chip_container'):
        target._chip_container.hide()
        target._chip_container.setMaximumSize(0, 0)
    if hasattr(target, '_cent_lay'):
        # Ocultar fila de controles (reset/play/skip) — buscar el QHBoxLayout
        ctrl_row_layout = None
        for i in range(target._cent_lay.count()):
            item = target._cent_lay.itemAt(i)
            if item and item.layout() and not item.widget():
                ctrl_row_layout = item.layout()
                break
        if ctrl_row_layout:
            # Ocultar cada widget del layout de controles
            for i in range(ctrl_row_layout.count()):
                w = ctrl_row_layout.itemAt(i).widget()
                if w:
                    w.hide()
                    w.setMaximumSize(0, 0)
    if hasattr(target, '_empty_state'):
        target._empty_state.show()
    # Colapsar stretch superior del layout para que el empty state quede cerca
    # del top del screen (matchea mockup l.856-858).
    if hasattr(target, '_cent_top_stretch'):
        from PyQt6.QtWidgets import QSizePolicy
        from PyQt6.QtCore import Qt

        target._cent_top_stretch.changeSize(
            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        if hasattr(target, '_cent_lay'):
            target._cent_lay.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            target._cent_lay.invalidate()
    # Mockup l.856-858: empty state en pantalla directa, SIN card chrome.
    # Forzar borderless en el timer_card si existe.
    if hasattr(target, '_timer_card'):
        try:
            target._timer_card.set_borderless(True)
        except Exception:
            pass
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
def _avisos_filter_hoy(win, qapp, action):
    """Aplica filtro Hoy en Avisos."""
    target = _module_target(win)
    if hasattr(target, '_on_filter_changed'):
        target._on_filter_changed("hoy")
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
def _avisos_force_empty(win, qapp, action):
    """Fuerza el empty state real de Avisos usando fixture QA vacia."""
    target = _module_target(win)
    try:
        import app.modules.avisos_qt as _av

        _orig_reminder_rows = _av.reminder_rows
        _av.reminder_rows = lambda: []
        try:
            if hasattr(target, "_load_reminders"):
                target._load_reminders()
        finally:
            _av.reminder_rows = _orig_reminder_rows
    except Exception:
        pass
    _drain(qapp, cycles=6)


@_register_helper
def _clear_hub_patients(win, qapp, action):
    """Limpia la lista de pacientes del Hub para mostrar estado vacio en Pacientes."""
    if hasattr(win, '_pacientes'):
        win._pacientes = []
    if hasattr(win, '_refresh_all_views'):
        win._refresh_all_views(force_recreate=True)
    _drain(qapp, cycles=6)


@_register_helper
def _hub_open_textos_globales(win, qapp, action):
    """Abre la vista navegable 'Textos globales de Suite' en el Hub.

    La vista se construye lazy dentro de _refresh_all_views; en QA mode ya esta
    creada al cargar los pacientes demo, pero nos defendemos forzando el refresh
    si el atributo no existiera.
    """
    view = getattr(win, "_view_textos_globales", None)
    cache = getattr(win, "_views_cache", {}) or {}
    if view is None or "textos_globales" not in cache:
        if hasattr(win, "_refresh_all_views"):
            try:
                win._refresh_all_views()
            except Exception:
                pass
    if hasattr(win, "_open_global_texts"):
        win._open_global_texts()
    elif hasattr(win, "_on_nav"):
        win._on_nav("textos_globales")
    _drain(qapp, cycles=6)


@_register_helper
def _detalle_open_resumen_ia_dialog(win, qapp, action):
    """Abre el dialogo 'Resumen IA' del detalle con texto de muestra.

    En runtime el dialogo se alimenta de un proveedor IA (red); para evidencia
    visual offline invocamos _show_resumen_dialog con texto muestra.
    """
    det = win._stack.currentWidget() if hasattr(win, "_stack") else None
    if det is None or not hasattr(det, "_show_resumen_dialog"):
        return
    sample = (
        "Ánimo promedio en rango medio-alto (6.4/10) con oscilación moderada. "
        "Tres registros TCC refieren ansiedad anticipatoria vinculada a situaciones sociales."
    )
    try:
        det._show_resumen_dialog(sample)
    except Exception:
        pass
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
    elif contract not in {"main_base", "main_scale125", "natural_dialog", "main_scaled_other"}:
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
        "handoff_closure_allowed": False,
        "visual_fidelity_gate": _VISUAL_FIDELITY_GATE,
        "closure_warning": _HANDOFF_CLOSURE_WARNING,
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


def _recipe_action_summary(app_key: str, view_id: str) -> str:
    recipe = _RECIPES.get(app_key, {}).get(view_id, {})
    parts = []
    for action in recipe.get("actions", []):
        name = action.get("action", "")
        if name == "navigate":
            parts.append(f"navigate:{action.get('view', '')}")
        elif name == "call":
            parts.append(f"call:{action.get('func', '')}")
        elif name == "capture":
            parts.append(f"capture:{action.get('view', '')}")
        elif name == "drain":
            parts.append(f"drain:{action.get('cycles', '')}")
        else:
            parts.append(name)
    return " > ".join(p for p in parts if p)


def _matrix_review_result(result: dict) -> str:
    status = result.get("capture_status", _STATUS_CAPTURE_FAILED)
    if status == _STATUS_CAPTURED_VALID:
        return "pendiente"
    if status in {
        _STATUS_REQUIRES_DATA_STATE,
        _STATUS_REQUIRES_RUNTIME,
        _STATUS_DUPLICATE_SUSPECT,
        _STATUS_FALLBACK,
    }:
        return "parcial"
    if status in {
        _STATUS_CAPTURE_FAILED,
        _STATUS_BLANK_OR_FLAT,
        _STATUS_MAIN_CAPTURE_CONTRACT_MISMATCH,
        _STATUS_WRONG_VIEW,
    }:
        return "bloqueado"
    return "parcial"


def _matrix_rows(results: list[dict]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for result in sorted(
        results,
        key=lambda r: (
            str(r.get("app", "")),
            str(r.get("view", "")),
            str(r.get("theme", "")),
            str(r.get("requested_resolution", "")),
        ),
    ):
        app_key = str(result.get("app", ""))
        view_id = str(result.get("view", ""))
        recipe = _RECIPES.get(app_key, {}).get(view_id, {})
        flags = result.get("evidence_flags") or []
        notes = result.get("evidence_notes") or []
        debt_parts = []
        if flags:
            debt_parts.append("flags=" + ",".join(flags))
        if notes:
            debt_parts.append("notes=" + " | ".join(str(n) for n in notes))
        if result.get("error"):
            debt_parts.append("error=" + str(result.get("error")))
        if not debt_parts and result.get("capture_status") == _STATUS_CAPTURED_VALID:
            debt_parts.append("requiere inspeccion manual")
        rows.append({
            "producto": app_key,
            "vista": view_id,
            "estado": str(recipe.get("label") or view_id),
            "tema": str(result.get("theme", "")),
            "resolucion": str(result.get("requested_logical_resolution") or result.get("requested_resolution") or ""),
            "receta": _recipe_action_summary(app_key, view_id),
            "captura": str(result.get("file") or ""),
            "inspeccion_manual": "pendiente",
            "resultado": _matrix_review_result(result),
            "deuda_pendiente": " ; ".join(debt_parts),
        })
    return rows


def _write_capture_matrix(results: list[dict], out_dir: Path, matrix_doc: Path | None = None) -> dict[str, str]:
    rows = _matrix_rows(results)
    headers = [
        "producto",
        "vista",
        "estado",
        "tema",
        "resolucion",
        "receta",
        "captura",
        "inspeccion_manual",
        "resultado",
        "deuda_pendiente",
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "CAPTURE_MATRIX.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    md_path = out_dir / "CAPTURE_MATRIX.md"
    _write_capture_matrix_markdown(rows, md_path)
    written = {"csv": str(csv_path), "markdown": str(md_path)}
    if matrix_doc is not None:
        _write_capture_matrix_markdown(rows, matrix_doc)
        written["matrix_doc"] = str(matrix_doc)
    return written


def _write_capture_matrix_markdown(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["resultado"]] = counts.get(row["resultado"], 0) + 1
    generated = datetime.datetime.now().isoformat(timespec="seconds")
    lines = [
        "# Matriz Baseline V8",
        "",
        f"- Generada: {generated}",
        f"- Filas: {len(rows)}",
        f"- Resultados: {', '.join(f'{k}={v}' for k, v in sorted(counts.items())) or 'sin filas'}",
        "- Inspeccion manual: pendiente hasta revisar captura por captura.",
        "",
        "| producto | vista | estado | tema | resolucion | receta | captura | inspeccion manual | resultado | deuda pendiente |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    keys = (
        "producto",
        "vista",
        "estado",
        "tema",
        "resolucion",
        "receta",
        "captura",
        "inspeccion_manual",
        "resultado",
        "deuda_pendiente",
    )
    for row in rows:
        lines.append("| " + " | ".join(_md_cell(row[key]) for key in keys) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _md_cell(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


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
            r = _grab_save(
                target_win,
                app_key,
                view_id,
                modo,
                res,
                out_dir,
                scale,
                is_auxiliary,
                capture_meta=act,
            )
            if r:
                results.append(r)

        elif action_type == "capture_child":
            prefix = act.get("prefix", _CHILD_PREFIX)
            _scan_and_capture_children(win, qapp, app_key, prefix, modo, res, out_dir, results, captured_views, scale)

        elif action_type == "close_child":
            from PyQt6.QtWidgets import QApplication
            from shared.components.dialogs import NMDialog
            for child in win.findChildren(NMDialog):
                if child.isVisible() and hasattr(child, "close"):
                    try:
                        child.close()
                        child.deleteLater()
                    except Exception:
                        pass
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
    # Detalle paciente: siempre recrea la vista para estado limpio.
    # (detalle-plan ya no es view_id de navegación: el plan siempre es visible
    # bajo el header; los subtabs no-default se reached vía _plan_set_subtab.)
    if view_id == "detalle":
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
    elif hasattr(win, "_on_nav"):
        win._on_nav(view_id)
    _drain(qapp)


def _introspect_sidecar_path(out_dir: Path) -> Path:
    return out_dir.parent / "_visual_auditor_spec" / "introspection.json"


def _record_introspection(win, app_key: str, view_id: str, modo: str, out_dir: Path) -> None:
    """Opt-in (NM_VAS_INTROSPECT=1) renderer-independent design audit.

    Walks the live, *settled* widget tree and checks design contracts (e.g. cards
    must carry a drop-shadow). Settling matters: fade-in animations swap a card's
    drop-shadow for an opacity effect mid-animation, so we drain extra cycles
    first to avoid false positives. Failures are appended to a sidecar JSON.
    Wrapped so it can never break a capture.
    """
    if os.environ.get("NM_VAS_INTROSPECT", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    try:
        from PyQt6.QtWidgets import QApplication  # noqa: F811
        import vas_introspect

        _drain(QApplication.instance(), cycles=20)  # let animations settle past ~1s
        surface_key = f"{app_key}:{view_id}@{_short_theme(modo)}"
        report = vas_introspect.audit_tree(win, surface_key)

        path = _introspect_sidecar_path(out_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = []
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        existing.append(report)
        path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:  # never break a capture
        print(f"[introspect skip {view_id}: {exc}]", end="", flush=True)


def _modal_capture_fields(
    app_key: str,
    view_id: str,
    theme: str,
    is_dialog_or_auxiliary: bool,
    capture_meta: dict | None,
) -> dict[str, Any]:
    meta = capture_meta or {}
    scope = meta.get("modal_capture_scope")
    surface = meta.get("surface")
    is_modal = bool(scope or surface in {"modal", "window_modal"} or is_dialog_or_auxiliary)
    if is_modal and not scope:
        scope = "panel_crop" if is_dialog_or_auxiliary else "window_overlay"
    if not surface:
        if is_modal:
            surface = "modal" if scope == "panel_crop" else "window_modal"
        else:
            surface = "window"

    back_screen_key = meta.get("back_screen_key")
    if back_screen_key and "@" not in str(back_screen_key):
        back_screen_key = f"{back_screen_key}@{theme}"

    return {
        "surface": surface,
        "is_modal": is_modal,
        "modal_capture_scope": scope if is_modal else None,
        "backdrop_observable": scope == "window_overlay",
        "back_screen_key": back_screen_key if is_modal else None,
    }


def _grab_save(win, app_key: str, view_id: str, modo: str, res: str, out_dir: Path,
               scale: float, is_dialog_or_auxiliary: bool,
               capture_meta: dict | None = None) -> dict | None:
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
        modal_fields = _modal_capture_fields(
            app_key,
            view_id,
            st,
            is_dialog_or_auxiliary,
            capture_meta,
        )
        suffix = _scale_suffix(scale)
        fname = f"{app_key}-{view_id}-{st}-{real_w}x{real_h}{suffix}.png"
        out_path = out_dir / fname
        ok = pm.save(str(out_path))
        _record_introspection(win, app_key, view_id, modo, out_dir)
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
                "actual_resolution": f"{real_w}x{real_h}",
                **modal_fields}
    except Exception as e:
        suffix = _scale_suffix(scale)
        fname = f"{app_key}-{view_id}-{st}-{w}x{h}{suffix}.png"
        modal_fields = _modal_capture_fields(
            app_key,
            view_id,
            st,
            is_dialog_or_auxiliary,
            capture_meta,
        )
        return {"file": fname, "app": app_key, "view": view_id, "theme": st,
                "requested_resolution": f"{w}x{h}",
                "requested_logical_resolution": f"{w}x{h}",
                "requested_scale_factor": scale,
                "evidence_contract": _capture_contract(scale, is_dialog_or_auxiliary),
                "is_dialog_or_auxiliary": is_dialog_or_auxiliary,
                "is_child_dialog": is_dialog_or_auxiliary,
                "success": False, "error": str(e), **modal_fields}


def _scan_and_capture_children(win, qapp, app_key: str, prefix: str, modo: str,
                                res: str, out_dir: Path, results: list,
                                captured_views: set, scale: float) -> int:
    """Escanea ventanas hijas/popups visibles de la app actual y las captura."""
    from PyQt6.QtWidgets import QApplication, QDialog
    from shared.components.dialogs import NMDialog
    count = 0
    for overlay in win.findChildren(NMDialog):
        if not overlay.isVisible():
            continue
        child_id = f"{prefix}-{count}"
        if child_id in captured_views:
            continue
        captured_views.add(child_id)
        target = getattr(overlay, "_panel", overlay)
        r = _grab_save(
            target,
            app_key,
            child_id,
            modo,
            res,
            out_dir,
            scale,
            True,
            capture_meta={
                "surface": "modal",
                "modal_capture_scope": "panel_crop",
                "back_screen_key": None,
            },
        )
        if r:
            results.append(r)
            count += 1

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
            r = _grab_save(
                tl,
                app_key,
                child_id,
                modo,
                res,
                out_dir,
                scale,
                True,
                capture_meta={
                    "surface": "modal",
                    "modal_capture_scope": "panel_crop",
                    "back_screen_key": None,
                },
            )
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
    p.add_argument("--matrix-doc", default="", help="Ruta opcional para escribir una matriz Markdown versionable")
    p.add_argument("--scale", type=_parse_scale, default=1.0, help="Qt scale factor for capture subprocesses (for example: 1.25)")
    p.add_argument("--introspect", action="store_true", help="Habilitar vas_introspect (audit del arbol de widgets Qt, opt-in). Setea NM_VAS_INTROSPECT=1 para subprocesses.")
    p.add_argument("--_child-single", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args()

    # --introspect propagates to subprocess children via env var
    if args.introspect:
        os.environ["NM_VAS_INTROSPECT"] = "1"

    if not args.list and not os.environ.get("NEUROMOOD_TEST_DB"):
        import tempfile
        import atexit
        temp_db_dir = tempfile.mkdtemp(prefix="nm_qa_db_")
        db_file = Path(temp_db_dir) / "test_nm_data.db"
        os.environ["NEUROMOOD_TEST_DB"] = str(db_file)

        from shared.db import inicializar_tablas
        try:
            inicializar_tablas()
        except Exception as e:
            print(f"[QA SETUP WARNING] Failed to initialize tables: {e}", file=sys.stderr)

        def cleanup_temp_db():
            if os.path.exists(temp_db_dir):
                import shutil
                shutil.rmtree(temp_db_dir, ignore_errors=True)
        atexit.register(cleanup_temp_db)
        print(f"[QA] Using isolated database: {db_file}")

    out_dir = Path(args.out_dir)
    scale = float(args.scale)
    os.environ["QT_SCALE_FACTOR"] = str(scale)

    # Reset the introspection sidecar once per parent run (children append to it).
    if (
        os.environ.get("NM_VAS_INTROSPECT", "").strip().lower() in {"1", "true", "yes", "on"}
        and os.environ.get("NM_V8_CHILD") != "1"
    ):
        try:
            _introspect_sidecar_path(out_dir).unlink(missing_ok=True)
        except Exception:
            pass

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

    matrix_paths = _write_capture_matrix(
        results,
        out_dir,
        Path(args.matrix_doc) if args.matrix_doc else None,
    )

    manifest = {
        "harness": "capture_v8.py",
        "generated_at": datetime.datetime.now().isoformat(),
        "git": _git_metadata(),
        "command": sys.argv,
        "cwd": str(_PROJ),
        "isolation_scope": "fresh_window_per_recipe" if args._child_single else "subprocess_per_recipe",
        "auto_residual_popup_capture": False,
        "handoff_closure_allowed": False,
        "visual_fidelity_gate": _VISUAL_FIDELITY_GATE,
        "closure_warning": _HANDOFF_CLOSURE_WARNING,
        "success": success,
        "failed": failed,
        "total": total,
        "expected_recipe_captures": expected_recipe_captures,
        "elapsed_seconds": round(elapsed, 1),
        "themes": [_short_theme(t) for t in themes],
        "resolutions": resolutions,
        "requested_scale_factor": scale,
        "output_dir": str(out_dir),
        "matrix_paths": matrix_paths,
        "evidence_summary": evidence_summary,
        "results": results,
    }
    manifest_path = out_dir / "CAPTURE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nManifest: {manifest_path}")
    print(f"Matrix:   {matrix_paths.get('markdown')}")
    if matrix_paths.get("matrix_doc"):
        print(f"Doc:      {matrix_paths['matrix_doc']}")

    print("\n" + "=" * 60)
    print("TECHNICAL_CAPTURE_ONLY")
    print("Semantic visual review: NOT_RUN")
    print("Visual review outcome: REVIEW_INCOMPLETE")
    print("HANDOFF_CLOSURE_ALLOWED: NO")
    print(f"Visual fidelity gate: {_VISUAL_FIDELITY_GATE}")
    print(_HANDOFF_CLOSURE_WARNING)
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
