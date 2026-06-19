from __future__ import annotations


def _capture_prompt(monkeypatch):
    import hub.ia_asistente as ia

    captured = {}
    monkeypatch.setattr(ia, "_ensure_provider", lambda: None)

    def _fake_llamar(prompt, sistema, fn_name, patient_id, on_result, on_error):
        captured["prompt"] = prompt
        captured["sistema"] = sistema
        captured["fn_name"] = fn_name
        captured["patient_id"] = patient_id

    monkeypatch.setattr(ia, "_llamar", _fake_llamar)
    return ia, captured


def test_generar_resumen_paciente_incluye_hasta_cinco_registros_recientes(monkeypatch):
    ia, captured = _capture_prompt(monkeypatch)
    datos = {
        "tcc": [
            {
                "fecha": f"2026-06-{19 - i:02d}",
                "hora": "10:00",
                "situacion": f"situacion-{i}",
                "emocion": "ansiedad",
                "intensidad": 6,
                "pensamiento": f"pensamiento-reciente-{i}",
                "respuesta_alternativa": f"respuesta-{i}",
            }
            for i in range(6)
        ],
        "avisos_disparados": [
            {
                "fecha": "2026-06-19",
                "hora": "09:00",
                "mensaje": "Tomar medicacion indicada",
                "cerrado": True,
            }
        ],
    }

    ia.generar_resumen_paciente(
        datos,
        "Paciente Test",
        lambda _text: None,
        lambda _err: None,
        patient_id="patient-1",
    )

    prompt = captured["prompt"]
    for i in range(5):
        assert f"pensamiento-reciente-{i}" in prompt
    assert "pensamiento-reciente-5" not in prompt
    assert "Avisos disparados" in prompt
    assert "Tomar medicacion indicada" in prompt


def test_generar_resumen_paciente_trunca_textos_largos(monkeypatch):
    ia, captured = _capture_prompt(monkeypatch)
    texto_largo = "situacion clinica " + ("muy larga " * 80)
    datos = {
        "tcc": [
            {
                "fecha": "2026-06-19",
                "hora": "10:00",
                "situacion": texto_largo,
                "emocion": "preocupacion",
                "pensamiento": "no voy a poder",
            }
        ]
    }

    ia.generar_resumen_paciente(
        datos,
        "Paciente Test",
        lambda _text: None,
        lambda _err: None,
        patient_id="patient-1",
    )

    prompt = captured["prompt"]
    assert texto_largo not in prompt
    assert "situacion clinica muy larga" in prompt
    assert "..." in prompt


def test_generar_resumen_paciente_excluye_campos_sensibles(monkeypatch):
    ia, captured = _capture_prompt(monkeypatch)
    datos = {
        "animo": [
            {
                "fecha": "2026-06-19",
                "hora": "10:00",
                "puntaje": 7,
                "nota": "registro valido",
                "id": "ROW_SECRET",
                "patient_id": "PID_SECRET",
                "email": "secreto@example.com",
                "auth_access_token": "TOKEN_SECRET",
                "api_key": "API_KEY_SECRET",
                "install_code": "INSTALL_SECRET",
                "password": "PASSWORD_SECRET",
            }
        ]
    }

    ia.generar_resumen_paciente(
        datos,
        "Paciente Test",
        lambda _text: None,
        lambda _err: None,
        patient_id="PID_ARG_SECRET",
    )

    prompt = captured["prompt"]
    assert "registro valido" in prompt
    for secret in (
        "ROW_SECRET",
        "PID_SECRET",
        "secreto@example.com",
        "TOKEN_SECRET",
        "API_KEY_SECRET",
        "INSTALL_SECRET",
        "PASSWORD_SECRET",
        "PID_ARG_SECRET",
    ):
        assert secret not in prompt


def test_generar_resumen_paciente_controla_tamano_total_del_prompt(monkeypatch):
    ia, captured = _capture_prompt(monkeypatch)
    texto = "contenido clinico " + ("extenso " * 400)
    datos = {
        "animo": [{"fecha": "2026-06-19", "nota": texto, "puntaje": 5} for _ in range(20)],
        "tcc": [{"fecha": "2026-06-19", "pensamiento": texto} for _ in range(20)],
        "checklist": [{"fecha": "2026-06-19", "descripcion": texto} for _ in range(20)],
        "actividades": [{"fecha": "2026-06-19", "actividad": texto} for _ in range(20)],
        "timer": [{"fecha": "2026-06-19", "nombre": texto, "notas": texto} for _ in range(20)],
        "dbt": [{"fecha": "2026-06-19", "nota": texto, "necesidad": texto} for _ in range(20)],
        "avisos_disparados": [
            {"fecha": "2026-06-19", "mensaje": texto} for _ in range(20)
        ],
    }

    ia.generar_resumen_paciente(
        datos,
        "Paciente Test",
        lambda _text: None,
        lambda _err: None,
        patient_id="patient-1",
    )

    assert len(captured["prompt"]) <= ia._MAX_PROMPT_CHARS
    assert "Contexto truncado" in captured["prompt"]
