
import os


from shared import config as config_module
from shared.config import _env_candidates, get, supabase_hub_key, supabase_key, supabase_url


class TestGet:
    def test_env_var_prioridad(self):
        os.environ["TEST_CONFIG_KEY"] = "from_env"
        result = get("TEST_CONFIG_KEY", "default_val")
        assert result == "from_env"
        del os.environ["TEST_CONFIG_KEY"]

    def test_default_cuando_falta(self):
        result = get("CLAVE_INEXISTENTE_XYZ_123", "fallback")
        assert result == "fallback"

    def test_default_cuando_vacio(self):
        result = get("CLAVE_INEXISTENTE_XYZ_123")
        assert result == ""


class TestSupabaseAccessors:
    def test_supabase_url_no_explota(self):
        result = supabase_url()
        assert isinstance(result, str)

    def test_supabase_key_no_explota(self):
        result = supabase_key()
        assert isinstance(result, str)

    def test_suite_key_prefiere_anon_sobre_service_role(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-key")
        config_module._cache.clear()

        assert supabase_key() == "anon-key"

    def test_hub_key_prefiere_clave_operativa(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
        monkeypatch.setenv("SUPABASE_HUB_KEY", "hub-key")
        config_module._cache.clear()

        assert supabase_hub_key() == "hub-key"

    def test_hub_key_fallback_a_anon(self, monkeypatch):
        monkeypatch.delenv("SUPABASE_HUB_KEY", raising=False)
        monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
        monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
        monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
        monkeypatch.setenv("SUPABASE_KEY", "anon-key")
        monkeypatch.setattr(config_module, "_cache", {"SUPABASE_KEY": "anon-key"})

        assert supabase_hub_key() == "anon-key"


class TestEnvCandidates:
    def test_devuelve_lista(self):
        candidates = _env_candidates()
        assert isinstance(candidates, list)

    def test_elementos_son_paths(self):
        candidates = _env_candidates()
        for c in candidates:
            assert hasattr(c, "exists")
