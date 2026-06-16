
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def _clean_sensitive_env(monkeypatch):
    keys_sensitive = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_ANON_KEY",
        "SUPABASE_PUBLIC_KEY",
        "GROQ_API_KEY",
        "OPENAI_API_KEY",
    ]
    for key in keys_sensitive:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture(autouse=True)
def _clean_visual_qa_env(monkeypatch):
    # Importar qa.capture_v8 setea NM_VISUAL_QA=1 a nivel módulo; sin esta
    # limpieza el orden de colección decide si los tests ven datos demo.
    keys_visual_qa = [
        "NM_VISUAL_QA",
        "NM_DEMO_VISUAL",
        "NM_QA_VISUAL",
        "NM_VISUAL_QA_DEMO",
    ]
    for key in keys_visual_qa:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture(autouse=True, scope="function")
def isolated_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_nm_data.db"
    monkeypatch.setenv("NEUROMOOD_TEST_DB", str(db_file))

    # Initialize the temporary database tables
    from shared.db import inicializar_tablas
    inicializar_tablas()

    yield db_file
