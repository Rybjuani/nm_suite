"""shared/text_overrides.py — Capa de textos globales de la Suite.

Permite que el profesional reemplace, de forma GLOBAL, cualquier texto que la
Suite muestra (Home, onboarding y los 8 módulos). Los overrides se guardan en
`hub_config` (scope='global', key con prefijo ``text.ovr.``) y se sincronizan al
cache local de cada paciente vía el pipeline de sync
(`shared.sync._importar_hub_config` → `shared.remote_config.replace_scopes`).

Mecanismo (sin tocar cada call-site):
    - Cada texto se identifica por ``(scope, texto_por_defecto)`` →
      ``override_key(scope, default)`` = ``text.ovr.<scope>.<sha1(default)[:10]>``.
      ``scope`` es la pantalla: "home", "onboarding" o el id de módulo
      ("animo", "rutina", ...).
    - En la Suite del paciente, ``apply_overrides(view, scope)`` recorre el árbol
      de widgets una vez (después de construir la vista) y reemplaza el texto de
      cada QLabel/QPushButton/checkbox y los placeholders de los inputs cuando hay
      un override para ese ``(scope, texto)``. Sin overrides en cache, es no-op.
    - En el Hub, ``collect_texts(view, scope)`` enumera los mismos textos para que
      el editor de "Configuración global de Suite" los haga editables.

Diseño: cero panics (cualquier error de DB cae a sin-overrides), sin estado
global mutable, y el reemplazo solo ocurre si existe un override (no cambia el
comportamiento por defecto de la Suite).
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Iterable, NamedTuple

from PyQt6.QtWidgets import (
    QCheckBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QWidget,
)

_log = logging.getLogger(__name__)

PREFIX = "text.ovr."

# Tipos de widget que llevan texto editable. El orden importa: QCheckBox/
# QRadioButton son QAbstractButton (no QPushButton), por eso se listan aparte.
_BUTTONISH = (QPushButton, QCheckBox, QRadioButton)
_PLACEHOLDER = (QLineEdit, QTextEdit, QPlainTextEdit)


class TextSite(NamedTuple):
    widget: QWidget
    scope: str
    kind: str  # "text" | "placeholder"
    default: str
    key: str


def override_key(scope: str, default_text: str) -> str:
    """Clave estable para un texto, derivada de la pantalla y el texto por defecto."""
    h = hashlib.sha1((default_text or "").encode("utf-8")).hexdigest()[:10]
    return f"{PREFIX}{scope}.{h}"


def _read_site(widget: QWidget) -> tuple[str, str] | None:
    """Devuelve (kind, texto) editable del widget, o None si no aplica."""
    try:
        if isinstance(widget, _BUTTONISH):
            txt = widget.text()
            if txt and txt.strip():
                return ("text", txt)
            return None
        if isinstance(widget, QLabel):
            txt = widget.text()
            # Saltar labels con HTML/imágenes o vacíos: el override es texto plano.
            if txt and txt.strip() and "<" not in txt:
                return ("text", txt)
            return None
        if isinstance(widget, _PLACEHOLDER):
            ph = widget.placeholderText()
            if ph and ph.strip():
                return ("placeholder", ph)
            return None
    except RuntimeError:
        # widget borrado durante el walk
        return None
    return None


def _iter_text_widgets(root: QWidget) -> Iterable[QWidget]:
    if root is None:
        return []
    widgets: list[QWidget] = [root]
    try:
        widgets.extend(root.findChildren(QWidget))
    except RuntimeError:
        return []
    return widgets


def collect_texts(root: QWidget, scope: str) -> list[TextSite]:
    """Enumera todos los textos editables bajo `root` (para el editor del Hub).

    De-duplica por (kind, texto): si el mismo texto aparece en varios widgets,
    todos comparten override (semántica global por texto). Se devuelve un
    TextSite por widget para poder actualizarlos todos en vivo.
    """
    sites: list[TextSite] = []
    for w in _iter_text_widgets(root):
        info = _read_site(w)
        if not info:
            continue
        kind, txt = info
        sites.append(TextSite(w, scope, kind, txt, override_key(scope, txt)))
    return sites


def apply_overrides(root: QWidget, scope: str, overrides: dict[str, str] | None = None) -> int:
    """Aplica los overrides globales a todos los textos bajo `root`.

    Debe llamarse UNA vez tras construir la vista (los textos están en su valor
    por defecto). Si `overrides` es None se leen del cache local. Devuelve la
    cantidad de textos reemplazados. Sin overrides → no-op (0).
    """
    if overrides is None:
        overrides = current_overrides()
    if not overrides:
        return 0
    replaced = 0
    for w in _iter_text_widgets(root):
        info = _read_site(w)
        if not info:
            continue
        kind, txt = info
        val = overrides.get(override_key(scope, txt))
        if val is None or val == txt:
            continue
        try:
            if kind == "text":
                w.setText(val)
            else:
                w.setPlaceholderText(val)
            replaced += 1
        except RuntimeError:
            continue
    return replaced


def current_overrides() -> dict[str, str]:
    """Lee los overrides globales (``text.ovr.*``) del cache local de la Suite."""
    try:
        from shared.db import obtener_conexion
    except Exception:
        return {}
    out: dict[str, str] = {}
    try:
        conn = obtener_conexion()
        try:
            rows = conn.execute(
                "SELECT key, value FROM remote_config_cache WHERE scope='global' AND key LIKE ?",
                (PREFIX + "%",),
            ).fetchall()
        finally:
            conn.close()
        for row in rows or []:
            raw = row["value"] if hasattr(row, "keys") else row[1]
            key = row["key"] if hasattr(row, "keys") else row[0]
            val = raw
            try:
                val = json.loads(raw)
            except (TypeError, ValueError):
                pass
            if val is not None:
                out[str(key)] = str(val)
    except Exception as exc:
        _log.debug("current_overrides: %s", exc)
    return out
