
import importlib.util
import os
import sys

import pytest

# El subset estructural de CI instala sólo pytest. La suite local completa carga
# pytest-qt cuando está disponible y conserva sus fixtures Qt sin volverlos una
# dependencia del replay stdlib.
pytest_plugins = ["pytestqt"] if importlib.util.find_spec("pytestqt") else []

# Forzar plataforma offscreen ANTES de cualquier import de PyQt6.
# Sin esto, los tests que crean QApplication fallan en entornos sin display
# (CI, contenedores, SSH sin X). Los tests individuales ya lo seteaban con
# os.environ.setdefault; centralizarlo aca garantiza el orden para todos.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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
