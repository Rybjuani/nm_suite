
import sys

from shared.assets import (
    APP_ICON,
    INSTALLER_ICON,
    LOGO_DARK,
    LOGO_LIGHT,
    UNINSTALLER_ICON,
    obtener_ruta_asset,
)


class TestConstantesAssets:
    def test_constantes_definidas(self):
        assert isinstance(LOGO_LIGHT, str)
        assert isinstance(LOGO_DARK, str)
        assert isinstance(APP_ICON, str)
        assert isinstance(INSTALLER_ICON, str)
        assert isinstance(UNINSTALLER_ICON, str)

    def test_constantes_no_vacias(self):
        for name in [LOGO_LIGHT, LOGO_DARK, APP_ICON, INSTALLER_ICON, UNINSTALLER_ICON]:
            assert len(name) > 0


class TestObtenerRutaAsset:
    def test_devuelve_string(self):
        result = obtener_ruta_asset("app_icon.ico")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_asset_inexistente_devuelve_ruta(self):
        result = obtener_ruta_asset("no_existe_xyz.abc")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_frozen_flag_off(self):
        assert not getattr(sys, "frozen", False)
        result = obtener_ruta_asset(APP_ICON)
        assert isinstance(result, str)
