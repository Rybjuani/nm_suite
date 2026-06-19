"""RC-3: límite de recordatorios asignados.

El handoff original RC-3 pedía aplicar ``.limit(50)`` al fetch de
``assigned_reminders`` en ``hub/pacientes_qt._fetch_patient_data``. Ese
cambio productivo fue introducido en S0-1 (commit 8b4f19a) junto con
``.order("hora", desc=False)`` y ``.eq("patient_id", pid)`` — el handoff
estaba desactualizado sobre este punto.

Este test de comportamiento captura la cadena Supabase real y comprueba
que el contrato RC-3 se mantiene:

- ``.limit(50)`` explícito sobre ``assigned_reminders`` (sin esto,
  PostgREST devolvería todo el histórico del paciente).
- ``.order("hora", desc=False)``: sin ORDER BY el LIMIT traería filas
  arbitrarias, no las más tempranas del día.
- ``.eq("patient_id", pid)``: filtrado por paciente (no fuga datos de
  otros pacientes).

No toca código productivo — solo protege contra regresiones futuras.
"""
from __future__ import annotations


# ─── Mock de Supabase que captura args reales de la cadena fluida ────────────


class _RecordingQuery:
    """Registra los argumentos de cada paso de la cadena fluida para una tabla.

    Soporta .select(columns).eq(col, val).order(col, desc=).limit(n).execute()
    que es la forma usada por _fetch_patient_data para assigned_reminders.
    """

    def __init__(self, parent: "_RecordingSB", table: str):
        self._parent = parent
        self._table = table

    def select(self, columns: str) -> "_RecordingQuery":
        self._parent.select_calls[self._table] = columns
        return self

    def eq(self, column: str, value) -> "_RecordingQuery":
        self._parent.eq_calls.setdefault(self._table, []).append((column, value))
        return self

    def order(self, column: str, desc: bool = False) -> "_RecordingQuery":
        self._parent.order_calls[self._table] = (column, desc)
        return self

    def limit(self, n: int) -> "_RecordingQuery":
        self._parent.limit_calls[self._table] = n
        return self

    def execute(self):
        class _Result:
            pass

        r = _Result()
        # assigned_reminders necesita devolver al menos una fila para que el
        # fetch no sea un no-op silencioso; el resto puede ser [].
        r.data = self._parent._rows.get(self._table, [])
        return r


class _RecordingSB:
    """Mock mínimo de cliente Supabase que captura args por tabla."""

    def __init__(self):
        self.select_calls: dict[str, str] = {}
        self.eq_calls: dict[str, list[tuple[str, object]]] = {}
        self.order_calls: dict[str, tuple[str, bool]] = {}
        self.limit_calls: dict[str, int] = {}
        self._rows: dict[str, list[dict]] = {
            "assigned_reminders": [
                {"id": 1, "hora": "09:00", "mensaje": "Tomar agua", "activa": True}
            ],
        }

    def table(self, name: str) -> _RecordingQuery:
        return _RecordingQuery(self, name)


def _make_view(sb):
    """Construye un DetallePacienteView sin llamar __init__ (evita Qt pesado)."""
    from hub.pacientes_qt import DetallePacienteView

    view = DetallePacienteView.__new__(DetallePacienteView)
    view._sb = sb
    view._pid = "test-pid-123"
    view._nombre = "Test"
    return view


# ─── Tests RC-3 ──────────────────────────────────────────────────────────────


def test_fetch_patient_data_aplica_limit_50_a_assigned_reminders(qapp):
    """RC-3: _fetch_patient_data aplica .limit(50) al fetch de
    assigned_reminders (introducido en S0-1, congelado por RC-3).

    Sin límite explícito, PostgREST devolvería todo el histórico del
    paciente — sin control de tamaño y con costos de red crecientes.
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    view._fetch_patient_data()

    assert "assigned_reminders" in sb.limit_calls, (
        "No se llamó a .limit() sobre assigned_reminders. "
        "RC-3 / S0-1 requiere un límite explícito."
    )
    assert sb.limit_calls["assigned_reminders"] == 50, (
        f"Límite de assigned_reminders alterado: esperado 50, "
        f"obtenido {sb.limit_calls['assigned_reminders']!r}. "
        "Si esto es intencional, actualizar el contrato documentado en RC-3."
    )


def test_fetch_patient_data_assigned_reminders_ordena_por_hora_asc(qapp):
    """RC-3 (no-regresión): el orden canónico de assigned_reminders es
    por 'hora' ascendente (introducido en S0-1 junto al límite).

    Sin ORDER BY, el LIMIT traería filas arbitrarias en lugar de las
    más tempranas del día — el orden cronológico es parte del contrato
    de presentación en el Hub.
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    view._fetch_patient_data()

    order = sb.order_calls.get("assigned_reminders")
    assert order == ("hora", False), (
        f"Orden de assigned_reminders alterado: esperado ('hora', False), "
        f"obtenido {order!r}. Sin ORDER BY el LIMIT traería filas arbitrarias."
    )


def test_fetch_patient_data_assigned_reminders_filtra_por_patient_id(qapp):
    """RC-3 (no-regresión): el fetch debe filtrar por patient_id del
    paciente actual — no traer recordatorios de otros pacientes.
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    view._fetch_patient_data()

    eq = sb.eq_calls.get("assigned_reminders", [])
    assert ("patient_id", "test-pid-123") in eq, (
        f"assigned_reminders no se filtra por patient_id correctamente: {eq!r}"
    )


def test_fetch_patient_data_assigned_reminders_no_es_ilimitado(qapp):
    """RC-3 (contrato negativo): el fetch de assigned_reminders no debe
    quedar sin .limit(). Cubre el caso de alguien que quite el .limit(50)
    creyendo que no se usa — el test explota si la llamada desaparece.
    """
    sb = _RecordingSB()
    view = _make_view(sb)

    view._fetch_patient_data()

    # Distinto del test del valor 50: este test explota si alguien
    # simplemente borra la línea .limit(...), incluso si después la
    # reemplaza por otro mecanismo.
    assert "assigned_reminders" in sb.limit_calls, (
        "El fetch de assigned_reminders perdió la llamada a .limit(). "
        "RC-3 exige un límite explícito."
    )
