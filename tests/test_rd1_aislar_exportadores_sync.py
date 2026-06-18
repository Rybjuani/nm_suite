"""RD-1: aislar cada exportador de sync_inmediato y sync_completo.

Antes de este fix, ``sync_completo`` y ``sync_inmediato`` llamaban a los 8
``_exportar_*`` en secuencia dentro del mismo bloque ``try/except`` externo.
Si el primero (o cualquiera sin try interno) lanzaba, los siguientes no se
ejecutaban y, en ``sync_completo``, tampoco corrían los ``_importar_*``.

RD-1 introduce ``_ejecutar_exportadores`` que itera la lista de exportadores
con un ``try/except`` por cada uno:
- el error se registra con el nombre del exportador;
- el pipeline continúa con los restantes;
- el contrato global de retorno no se ve alterado.

Estos tests son de ejecución: reemplazan la maquinaria de red de ``shared.sync``
(``_get_client``, ``_paciente_desvinculado``, ``_upsert_paciente``) y los
propios ``_exportar_*`` por stubs controlados que registran el orden real de
llamada y permiten inyectar fallos puntuales.
"""
from __future__ import annotations

import logging

import pytest

import shared.sync as sync_module


# ─── Helpers ─────────────────────────────────────────────────────────────────


_EXPORTADOR_NAMES = [
    "_exportar_animo",
    "_exportar_respiracion",
    "_exportar_pensamientos",
    "_exportar_checklist",
    "_exportar_temporizador",
    "_exportar_recordatorios_log",
    "_exportar_activacion",
    "_exportar_dbt_practicas",
]

# Claves cortas que el pipeline registra en log y en _EXPORTADORES. Mantener
# sincronizadas con shared.sync._EXPORTADORES.
_EXPORTADOR_KEYS = [
    "animo",
    "respiracion",
    "pensamientos",
    "checklist",
    "temporizador",
    "recordatorios_log",
    "activacion",
    "dbt_practicas",
]

_IMPORTADOR_NAMES = [
    "_importar_rutina_modo",
    "_importar_routine_template",
    "_importar_tcc_templates",
    "_importar_timer_presets",
    "_importar_breathing_presets",
    "_importar_support_messages",
    "_importar_tareas_asignadas",
    "_importar_recordatorios_asignados",
    "_importar_permisos",
    "_importar_actividades",
    "_importar_hub_config",
]


class _CallTracker:
    """Registra el orden real de llamada a cada exportador/importador.

    Permite marcar un nombre como 'lanzar RuntimeError' para simular fallo.
    """

    def __init__(self):
        self.calls: list[str] = []
        self.raise_on: set[str] = set()

    def make_export_stub(self, name: str):
        # Exportadores comparten signature (sb, patient_id, desde).
        def _stub(sb, patient_id, desde):
            self.calls.append(name)
            if name in self.raise_on:
                raise RuntimeError(f"injected failure for {name}")

        return _stub

    def make_import_stub(self, name: str):
        # Importadores tienen signature (sb, patient_id) — sin 'desde'.
        def _stub(sb, patient_id):
            self.calls.append(name)

        return _stub


@pytest.fixture
def sync_pipeline(monkeypatch):
    """Reemplaza toda la maquinaria de red de shared.sync por stubs.

    Devuelve un _CallTracker que el test puede inspeccionar y configurar
    (tracker.raise_on.add('_exportar_animo')) antes de llamar a la función
    de sync bajo prueba.
    """
    tracker = _CallTracker()

    # _get_client: retornar cualquier objeto truthy (no se toca la red).
    monkeypatch.setattr(sync_module, "_get_client", lambda **_kw: object(), raising=True)
    # _paciente_desvinculado: False (paciente activo).
    monkeypatch.setattr(sync_module, "_paciente_desvinculado", lambda sb, pid: False, raising=True)
    # _upsert_paciente: no-op.
    monkeypatch.setattr(sync_module, "_upsert_paciente", lambda *a, **kw: None, raising=True)
    # Identidad / config locales: valores fijos válidos.
    monkeypatch.setattr(sync_module, "obtener_patient_id", lambda: "test-pid-123", raising=True)
    monkeypatch.setattr(sync_module, "obtener_nombre_paciente", lambda: "Test", raising=True)
    monkeypatch.setattr(sync_module, "obtener_password_hash", lambda *a, **kw: "hash", raising=True)
    monkeypatch.setattr(sync_module, "leer_config", lambda key, default="": "", raising=True)
    monkeypatch.setattr(sync_module, "guardar_config", lambda *a, **kw: None, raising=True)

    # Exportadores: stubs controlados.
    for name in _EXPORTADOR_NAMES:
        monkeypatch.setattr(sync_module, name, tracker.make_export_stub(name), raising=True)
    # Importadores (solo relevantes para sync_completo): stubs no-op pero
    # registrados para poder verificar que el pipeline siguió tras el fallo.
    for name in _IMPORTADOR_NAMES:
        monkeypatch.setattr(sync_module, name, tracker.make_import_stub(name), raising=True)

    return tracker


# ─── sync_completo ───────────────────────────────────────────────────────────


def test_sync_completo_continua_tras_fallo_del_primer_exportador(sync_pipeline, caplog):
    """RD-1: si el primer exportador (_exportar_animo) lanza, los 7 restantes
    igualmente se ejecutan. Antes del fix, ninguno de los posteriores corría.
    """
    sync_pipeline.raise_on.add("_exportar_animo")

    with caplog.at_level(logging.WARNING, logger="NeuroMood.Sync"):
        result = sync_module.sync_completo()

    # El contrato global no debe romperse por un fallo parcial de exportación.
    assert result is True, (
        "sync_completo debe retornar True aunque un exportador falle aislado; "
        "el fallo parcial ya quedó registrado en el log."
    )
    # Los 8 exportadores deben haberse llamado exactamente una vez cada uno.
    export_calls = [c for c in sync_pipeline.calls if c.startswith("_exportar_")]
    assert export_calls == _EXPORTADOR_NAMES, (
        f"Orden/llamadas de exportadores incorrecto: {export_calls}. "
        "RD-1 exige que todos los exportadores se ejecuten aunque uno falle."
    )
    # El log debe registrar el exportador caído y el resumen.
    assert "Exportador 'animo' fallo" in caplog.text, (
        "El error del exportador debe registrarse con su nombre para auditoría."
    )
    assert "exportador(es) fallido(s)" in caplog.text, (
        "Debe emitirse un warning de resumen con la cantidad de fallidos."
    )


def test_sync_completo_continua_tras_fallo_intermedio(sync_pipeline):
    """RD-1: un fallo en _exportar_pensamientos (3ro) no impide que los 5
    posteriores se ejecuten, y los 2 anteriores también corrieron.
    """
    sync_pipeline.raise_on.add("_exportar_pensamientos")

    sync_module.sync_completo()

    export_calls = [c for c in sync_pipeline.calls if c.startswith("_exportar_")]
    assert export_calls == _EXPORTADOR_NAMES, (
        f"Todos los exportadores deben llamarse pese al fallo intermedio: {export_calls}"
    )
    # Y los importadores también deben haber corrido (RD-1: el try externo
    # ya no se rompe por un fallo de exportador).
    import_calls = [c for c in sync_pipeline.calls if c.startswith("_importar_")]
    assert import_calls == _IMPORTADOR_NAMES, (
        f"Los importadores deben correr todos tras el fallo aislado: {import_calls}"
    )


def test_sync_completo_multiples_exportadores_fallan(sync_pipeline, caplog):
    """RD-1: múltiples fallos simultáneos también se aíslan y registran."""
    sync_pipeline.raise_on.update({"_exportar_animo", "_exportar_dbt_practicas"})

    with caplog.at_level(logging.WARNING, logger="NeuroMood.Sync"):
        result = sync_module.sync_completo()

    assert result is True
    export_calls = [c for c in sync_pipeline.calls if c.startswith("_exportar_")]
    assert export_calls == _EXPORTADOR_NAMES
    assert "Exportador 'animo' fallo" in caplog.text
    assert "Exportador 'dbt_practicas' fallo" in caplog.text
    assert "2 exportador(es) fallido(s)" in caplog.text


def test_sync_completo_no_loggea_errores_si_todos_ok(sync_pipeline, caplog):
    """RD-1 (no-regresión): si ningún exportador falla, el log no contiene
    el mensaje de error de exportador ni el warning de resumen.
    """
    with caplog.at_level(logging.WARNING, logger="NeuroMood.Sync"):
        result = sync_module.sync_completo()

    assert result is True
    assert "Exportador" not in caplog.text, (
        f"No debería haber log de fallo de exportador: {caplog.text!r}"
    )
    assert "exportador(es) fallido(s)" not in caplog.text


# ─── sync_inmediato ──────────────────────────────────────────────────────────


def test_sync_inmediato_continua_tras_fallo_de_exportador(sync_pipeline, caplog):
    """RD-1: el aislamiento también aplica a sync_inmediato."""
    sync_pipeline.raise_on.add("_exportar_respiracion")

    with caplog.at_level(logging.ERROR, logger="NeuroMood.Sync"):
        sync_module.sync_inmediato()

    export_calls = [c for c in sync_pipeline.calls if c.startswith("_exportar_")]
    assert export_calls == _EXPORTADOR_NAMES, (
        f"Todos los exportadores deben llamarse en sync_inmediato: {export_calls}"
    )
    assert "Exportador 'respiracion' fallo" in caplog.text


def test_sync_inmediato_no_rompe_si_primer_exportador_falla(sync_pipeline, caplog):
    """RD-1: el primer exportador es el más sensible (corta a todos los
    posteriores en el código pre-fix). Verificar específicamente ese caso.
    """
    sync_pipeline.raise_on.add("_exportar_animo")

    with caplog.at_level(logging.ERROR, logger="NeuroMood.Sync"):
        # No debe lanzar: sync_inmediato tiene su propio try externo pero
        # ahora los exportadores fallan aislados dentro de _ejecutar_exportadores.
        sync_module.sync_inmediato()

    export_calls = [c for c in sync_pipeline.calls if c.startswith("_exportar_")]
    assert export_calls == _EXPORTADOR_NAMES
    assert "Exportador 'animo' fallo" in caplog.text
    # El error genérico del caller ("Fallo al ejecutar sync_inmediato") NO
    # debe aparecer: el fallo del exportador fue contenido por el helper.
    assert "Fallo al ejecutar sync_inmediato" not in caplog.text


# ─── Contrato estructural: orden canónico del pipeline ───────────────────────


def test_orden_canonico_de_exportadores_constante():
    """RD-1: el orden del pipeline de exportadores es canónico y no debe
    cambiar silenciosamente. Si alguien reordena _EXPORTADORES, este test
    fuerza a revisar la decisión.
    """
    nombres = list(sync_module._EXPORTADORES)
    assert nombres == _EXPORTADOR_KEYS, (
        f"Orden canónico de exportadores alterado: {nombres}. "
        "Si esto es intencional, actualizar el contrato documentado."
    )


def test_todos_los_exportadores_estan_en_pipeline():
    """RD-1 (integridad): ningún exportador puede quedar fuera del pipeline
    al refactorizar a _ejecutar_exportadores.
    """
    nombres_en_pipeline = set(sync_module._EXPORTADORES)
    for expected in _EXPORTADOR_KEYS:
        assert expected in nombres_en_pipeline, (
            f"{expected} no está en _EXPORTADORES — se perdió al refactorizar."
        )


def test_exportadores_apuntan_a_funcion_correcta():
    """RD-1 (integridad): cada clave corta del pipeline debe resolver a una
    función ``_exportar_<clave>`` existente en el módulo (lookup runtime).
    """
    for key in sync_module._EXPORTADORES:
        expected_attr = f"_exportar_{key}"
        assert hasattr(sync_module, expected_attr) and callable(
            getattr(sync_module, expected_attr)
        ), (
            f"No existe función exportadora '{expected_attr}' cableada a la "
            f"clave '{key}' del pipeline."
        )
