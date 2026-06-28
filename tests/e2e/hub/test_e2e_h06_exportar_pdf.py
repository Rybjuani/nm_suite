from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.e2e_hub]


def _pdf_env(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (tmp_path / "Downloads").mkdir(exist_ok=True)


def test_genera_archivo_en_downloads(tmp_path, monkeypatch):
    from hub.exportar import _generar

    _pdf_env(tmp_path, monkeypatch)
    path = _generar(
        "Ana Paciente",
        "p1",
        {"animo": [{"fecha": "2026-06-01", "puntaje": 7, "nota": "Bien"}]},
        nombre_archivo="e2e_pdf.pdf",
    )

    assert Path(path).exists()
    assert Path(path).parent == tmp_path / "Downloads"
    assert Path(path).stat().st_size > 0


def test_con_datos_vacios_no_falla(tmp_path, monkeypatch):
    from hub.exportar import _generar

    _pdf_env(tmp_path, monkeypatch)
    path = _generar("Ana Paciente", "p1", {}, nombre_archivo="vacio.pdf")

    assert Path(path).exists()
    assert Path(path).stat().st_size > 0


def test_con_filtro_fechas(tmp_path, monkeypatch):
    from hub.exportar import _generar

    _pdf_env(tmp_path, monkeypatch)
    path = _generar(
        "Ana Paciente",
        "p1",
        {
            "timer": [
                {"fecha": "2026-06-01", "nombre": "Viejo", "duracion_min": 5},
                {"fecha": "2026-06-20", "nombre": "Nuevo", "duracion_min": 10},
            ]
        },
        secciones=["timer"],
        fecha_desde="2026-06-10",
        fecha_hasta="2026-06-30",
        nombre_archivo="filtrado.pdf",
    )

    assert Path(path).exists()
    assert Path(path).stat().st_size > 0
