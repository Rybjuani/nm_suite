"""Contrato del catalogo semantico de textos globales de Suite."""

from __future__ import annotations

from shared.suite_text_catalog import suite_text_entries


def test_suite_text_catalog_contract():
    entries = suite_text_entries()
    keys = [entry.key for entry in entries]

    assert entries
    assert len(keys) == len(set(keys))
    assert all(key.startswith("text.") for key in keys)
    assert all(not key.startswith("text.ovr.") for key in keys)
    assert all(key.strip() == key and key for key in keys)
    assert all(entry.default.strip() for entry in entries)
    assert all(entry.max_chars >= len(entry.default) for entry in entries)
    assert all(entry.max_chars > 0 for entry in entries)
    assert all(entry.section.strip() for entry in entries)
    assert all(entry.field.strip() for entry in entries)
    assert [entry.order for entry in entries] == list(range(len(entries)))


def test_suite_text_catalog_has_required_surface_sections():
    sections = {entry.section for entry in suite_text_entries()}

    required = {
        "Chrome",
        "Home",
        "Onboarding",
        "Ánimo",
        "Respiración",
        "TCC",
        "Rutina",
        "Activación",
        "Temporizador",
        "Recordatorios",
        "DBT",
    }
    assert required <= sections
