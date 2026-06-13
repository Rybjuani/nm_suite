
import base64
import json


import pytest


from build_neuromood import (
    _looks_like_service_role_key,
    _resolve_supabase_runtime_keys,
    _validate_runtime_env_values,
)


def _make_jwt(payload: dict) -> str:
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("ascii")).decode("ascii").rstrip("=")
    return f"header.{payload_b64}.signature"


class TestLooksLikeServiceRoleKey:
    def test_service_role_detectado(self):
        jwt = _make_jwt({"role": "service_role"})
        assert _looks_like_service_role_key(jwt) is True

    def test_anon_no_es_service_role(self):
        jwt = _make_jwt({"role": "anon"})
        assert _looks_like_service_role_key(jwt) is False

    def test_payload_sin_role(self):
        jwt = _make_jwt({"sub": "123456"})
        assert _looks_like_service_role_key(jwt) is False

    def test_vacio(self):
        assert _looks_like_service_role_key("") is False

    def test_no_jwt_string_normal(self):
        assert _looks_like_service_role_key("supabase_key_abc123") is False

    def test_no_jwt_partes_insuficientes(self):
        assert _looks_like_service_role_key("solo.dos") is False

    def test_jwt_malformado(self):
        assert _looks_like_service_role_key("not.valid==.jwt") is False

    def test_con_whitespace(self):
        jwt = _make_jwt({"role": "service_role"})
        assert _looks_like_service_role_key(f"  {jwt}  ") is True

    def test_con_comillas(self):
        jwt = _make_jwt({"role": "service_role"})
        assert _looks_like_service_role_key(f'"{jwt}"') is True


class TestValidateRuntimeEnvValues:
    def test_acepta_url_y_anon_key(self):
        jwt = _make_jwt({"role": "anon"})
        values = {"SUPABASE_URL": " https://demo.supabase.co ", "SUPABASE_KEY": f" '{jwt}' "}

        _validate_runtime_env_values(values)

        assert values["SUPABASE_URL"] == "https://demo.supabase.co"
        assert values["SUPABASE_KEY"] == jwt

    @pytest.mark.parametrize(
        ("values", "msg"),
        [
            ({"SUPABASE_KEY": "anon"}, "SUPABASE_URL"),
            ({"SUPABASE_URL": "https://demo.supabase.co"}, "SUPABASE_KEY"),
            ({"SUPABASE_URL": "demo.supabase.co", "SUPABASE_KEY": "anon"}, "http://"),
        ],
    )
    def test_rechaza_runtime_env_incompleto_o_url_invalida(self, values, msg):
        with pytest.raises(RuntimeError, match=msg):
            _validate_runtime_env_values(values)

    def test_rechaza_service_role_runtime(self):
        jwt = _make_jwt({"role": "service_role"})
        values = {"SUPABASE_URL": "https://demo.supabase.co", "SUPABASE_KEY": jwt}

        with pytest.raises(RuntimeError, match="service_role"):
            _validate_runtime_env_values(values)

    def test_acepta_service_role_solo_para_hub(self):
        anon = _make_jwt({"role": "anon"})
        service = _make_jwt({"role": "service_role"})
        values = {
            "SUPABASE_URL": "https://demo.supabase.co",
            "SUPABASE_KEY": anon,
            "SUPABASE_HUB_KEY": service,
        }

        _validate_runtime_env_values(values)

        assert values["SUPABASE_KEY"] == anon
        assert values["SUPABASE_HUB_KEY"] == service

    def test_rechaza_hub_key_no_service_role(self):
        anon = _make_jwt({"role": "anon"})
        values = {
            "SUPABASE_URL": "https://demo.supabase.co",
            "SUPABASE_KEY": anon,
            "SUPABASE_HUB_KEY": anon,
        }

        with pytest.raises(RuntimeError, match="SUPABASE_HUB_KEY"):
            _validate_runtime_env_values(values)

    @pytest.mark.parametrize(
        "values",
        [
            {"SUPABASE_URL": "https://demo.supabase.co\nX=1", "SUPABASE_KEY": "anon"},
            {"SUPABASE_URL": "https://demo.supabase.co", "SUPABASE_KEY": "anon\nX=1"},
            {
                "SUPABASE_URL": "https://demo.supabase.co",
                "SUPABASE_KEY": "anon",
                "OPENAI_API_KEY": "sk-demo\nX=1",
            },
        ],
    )
    def test_rechaza_saltos_de_linea_en_runtime_env(self, values):
        with pytest.raises(RuntimeError, match="saltos de línea"):
            _validate_runtime_env_values(values)


class TestResolveSupabaseRuntimeKeys:
    def test_separa_suite_anon_y_hub_service_role(self):
        anon = _make_jwt({"role": "anon"})
        service = _make_jwt({"role": "service_role"})
        values = {
            "SUPABASE_URL": "https://demo.supabase.co",
            "SUPABASE_KEY": service,
            "SUPABASE_ANON_KEY": anon,
        }

        _resolve_supabase_runtime_keys(values)

        assert values["SUPABASE_KEY"] == anon
        assert values["SUPABASE_HUB_KEY"] == service
