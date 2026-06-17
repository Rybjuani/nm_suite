"""Tests de shared.text_overrides — capa de textos globales de la Suite.

Cubre: clave estable, enumeración (collect_texts), aplicación (apply_overrides)
y lectura desde el cache local (current_overrides), aislando la DB vía APPDATA
temporal para no tocar el nm_data.db real.
"""

import pytest

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit

from shared.text_overrides import (
    PREFIX,
    apply_overrides,
    collect_texts,
    current_overrides,
    override_key,
)


@pytest.fixture
def db_temporal(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    appdata.mkdir()
    monkeypatch.setenv("APPDATA", str(appdata))
    from shared import db

    db.inicializar_tablas()
    # remote_config_cache puede no estar en el esquema base; garantizarla.
    conn = db.obtener_conexion()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS remote_config_cache "
        "(scope TEXT, key TEXT, value TEXT, fetched_at TEXT, PRIMARY KEY (scope, key))"
    )
    conn.commit()
    conn.close()
    return db


def _build_view(qapp):
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(QLabel("Hola"))
    lay.addWidget(QPushButton("Guardar registro"))
    inp = QLineEdit()
    inp.setPlaceholderText("Escribí algo…")
    lay.addWidget(inp)
    lay.addWidget(QLabel("<b>rico</b>"))  # HTML → se ignora
    return w, inp


def test_override_key_estable():
    assert override_key("home", "Hola") == override_key("home", "Hola")
    assert override_key("home", "Hola") != override_key("animo", "Hola")
    assert override_key("home", "Hola").startswith(PREFIX + "home.")


def test_collect_texts_encuentra_labels_botones_y_placeholders(qapp):
    w, _inp = _build_view(qapp)
    sites = collect_texts(w, "home")
    by_default = {s.default: s for s in sites}
    assert "Hola" in by_default and by_default["Hola"].kind == "text"
    assert "Guardar registro" in by_default
    assert "Escribí algo…" in by_default and by_default["Escribí algo…"].kind == "placeholder"
    # El label con HTML no se ofrece como editable.
    assert "<b>rico</b>" not in by_default
    assert "rico" not in by_default


def test_apply_overrides_reemplaza_solo_lo_que_corresponde(qapp):
    w, inp = _build_view(qapp)
    ov = {
        override_key("home", "Hola"): "Bienvenido",
        override_key("home", "Escribí algo…"): "Contanos tu día",
    }
    n = apply_overrides(w, "home", ov)
    assert n == 2
    labels = [c.text() for c in w.findChildren(QLabel)]
    assert "Bienvenido" in labels
    assert inp.placeholderText() == "Contanos tu día"
    # El botón sin override conserva su texto.
    assert any(b.text() == "Guardar registro" for b in w.findChildren(QPushButton))


def test_apply_overrides_sin_overrides_es_noop(qapp):
    w, _inp = _build_view(qapp)
    assert apply_overrides(w, "home", {}) == 0
    assert any(lbl.text() == "Hola" for lbl in w.findChildren(QLabel))


def test_current_overrides_lee_del_cache(db_temporal, qapp):
    key = override_key("home", "Hola")
    conn = db_temporal.obtener_conexion()
    conn.execute(
        "INSERT OR REPLACE INTO remote_config_cache (scope, key, value, fetched_at) "
        "VALUES ('global', ?, ?, '2026-01-01')",
        (key, '"Buenas"'),
    )
    conn.commit()
    conn.close()

    ov = current_overrides()
    assert ov.get(key) == "Buenas"

    # End-to-end: apply_overrides(None) toma los overrides del cache.
    w, _inp = _build_view(qapp)
    apply_overrides(w, "home")
    assert any(lbl.text() == "Buenas" for lbl in w.findChildren(QLabel))
