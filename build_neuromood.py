from __future__ import annotations

import argparse
import atexit
import base64
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


# ── Consola visual: banner + barras de progreso con gradiente ──────────────────
class BuildUI:
    """Salida de consola con gradientes truecolor y barras de progreso animadas.

    Degrada con elegancia en tres niveles:
      • TTY moderna + UTF-8 → barra sólida con gradiente, spinner, marco, %, tiempo.
      • `NM_BUILD_ASCII=1` o sin glifos → mismas barras con caracteres ASCII seguros.
      • Sin TTY (CI, redirección a archivo) → texto plano sin códigos ANSI.

    Cada fase ocupa una línea que se anima mientras corre el subproceso y se
    asienta con un check al terminar, conservando el porcentaje global.
    """

    # Indigo Profundo → lavanda/aqua (tokens V6) para el gradiente de las barras.
    GRAD_SUITE = ((124, 108, 255), (94, 224, 199))   # lavanda → aqua
    GRAD_HUB = ((56, 178, 168), (94, 224, 199))       # teal → aqua
    GRAD_OK = ((77, 200, 130), (94, 224, 199))        # verde → aqua
    GRAD_TITLE = ((124, 108, 255), (94, 224, 199))    # firma del producto

    # Tonos planos reutilizados (atenuados / neutros).
    _DIM = (74, 78, 104)        # track de la barra
    _MUTE = (122, 125, 150)     # texto secundario
    _INK = (236, 236, 251)      # texto principal
    _RULE = (66, 72, 100)       # líneas de marco

    # Spinner de círculos (Consolas/Cascadia); fallback ASCII si NM_BUILD_ASCII.
    _SPIN_UNI = "◐◓◑◒"
    _SPIN_ASCII = "|/-\\"
    # Bordes fraccionales: solo los que Consolas soporta universalmente (▏ omitido).
    _FRAC_UNI = " ▎▌▊"

    def __init__(self, total: int, enabled: bool | None = None) -> None:
        self.total = max(1, total)
        self.done = 0
        self._t0 = time.monotonic()
        self._ascii = os.environ.get("NM_BUILD_ASCII") == "1"
        if enabled is None:
            enabled = sys.stdout.isatty()
        self.enabled = enabled and self._enable_vt()
        # Glifos según modo (todos con respaldo seguro).
        if self._ascii:
            self.GLY_RUN, self.GLY_OK, self.GLY_ERR = ">", "+", "x"
            self.GLY_WARN, self.GLY_DOT, self.GLY_FULL = "*", ">", "#"
            self.GLY_EMPTY, self.SPINNER = "-", self._SPIN_ASCII
            self._frac = " "
        else:
            self.GLY_RUN, self.GLY_OK, self.GLY_ERR = "▶", "✓", "✗"
            self.GLY_WARN, self.GLY_DOT, self.GLY_FULL = "◉", "›", "█"
            self.GLY_EMPTY, self.SPINNER = "─", self._SPIN_UNI
            self._frac = self._FRAC_UNI
        if self.enabled:
            self._disable_quick_edit()
            sys.stdout.write("\033[?25l")  # ocultar cursor durante la animación
            sys.stdout.flush()
            atexit.register(self._restore_cursor)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @staticmethod
    def _enable_vt() -> bool:
        if os.name != "nt":
            return True
        try:
            import ctypes

            k = ctypes.windll.kernel32
            h = k.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if not k.GetConsoleMode(h, ctypes.byref(mode)):
                return False
            k.SetConsoleMode(h, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            return True
        except Exception:
            return False

    @staticmethod
    def _disable_quick_edit() -> None:
        """Desactiva Quick Edit Mode para que los clics no pasen la animación."""
        if os.name != "nt":
            return
        try:
            import ctypes
            k = ctypes.windll.kernel32
            h = k.GetStdHandle(-10)  # STD_INPUT_HANDLE
            mode = ctypes.c_uint32()
            if k.GetConsoleMode(h, ctypes.byref(mode)):
                # Elimina ENABLE_QUICK_EDIT (0x0040); preserva ENABLE_EXTENDED_FLAGS (0x0080)
                k.SetConsoleMode(h, (mode.value & ~0x0040) | 0x0080)
        except Exception:
            pass

    def _restore_cursor(self) -> None:
        if self.enabled:
            try:
                sys.stdout.write("\033[?25h")
                sys.stdout.flush()
            except Exception:
                pass

    @staticmethod
    def _lerp(a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    @staticmethod
    def _fg(rgb) -> str:
        return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"

    def _elapsed(self) -> str:
        s = int(time.monotonic() - self._t0)
        return f"{s // 60:d}:{s % 60:02d}"

    def _bar(self, frac: float, grad, width: int = 30, shimmer: float | None = None) -> str:
        """Barra sólida de gradiente con borde fraccional (sub-celda) y track tenue.

        El relleno usa bloques `█` coloreados con el gradiente; el límite usa
        un bloque parcial (`▏..▉`) para precisión sub-carácter; el resto es un
        track tenue. El `shimmer` agrega un brillo móvil sobre la zona llena.
        """
        frac = max(0.0, min(1.0, frac))
        exact = frac * width
        full = int(exact)
        rem = exact - full

        out = []
        # Tramo lleno: gradiente + shimmer opcional.
        for i in range(full):
            t = i / max(1, width - 1)
            r, g, b = self._lerp(grad[0], grad[1], t)
            if shimmer is not None:
                d = abs(t - shimmer)
                if d < 0.14:
                    boost = int(90 * (1 - d / 0.14))
                    r, g, b = min(255, r + boost), min(255, g + boost), min(255, b + boost)
            out.append(self._fg((r, g, b)) + self.GLY_FULL)
        # Celda fraccional en el límite (solo modo Unicode con glifos parciales).
        if full < width:
            if not self._ascii and rem > 0.08:
                t = full / max(1, width - 1)
                idx = max(1, min(len(self._frac) - 1, int(rem * len(self._frac))))
                out.append(self._fg(self._lerp(grad[0], grad[1], t)) + self._frac[idx])
                start_empty = full + 1
            else:
                start_empty = full
            # Track tenue para el resto.
            empties = width - start_empty
            if empties > 0:
                out.append(self._fg(self._DIM) + self.GLY_EMPTY * empties)
        return "".join(out) + "\033[0m"

    def _rule(self, width: int = 50) -> str:
        dash = "-" if self._ascii else "─"
        return self._fg(self._RULE) + dash * width + "\033[0m"

    def banner(self, mode_line: str) -> None:
        if not self.enabled:
            print("=" * 60)
            print(" NeuroMood — Build")
            print("=" * 60)
            print(mode_line)
            return
        title = "NeuroMood"
        sub = "Build"
        out = []
        for i, ch in enumerate(title):
            t = i / max(1, len(title) - 1)
            out.append("\033[1m" + self._fg(self._lerp(*self.GRAD_TITLE, t)) + ch)
        title_grad = "".join(out) + "\033[0m"
        bullet = self._fg(self.GRAD_TITLE[1]) + self.GLY_WARN + "\033[0m"
        print()
        print(f"  {bullet} {title_grad} {self._fg(self._MUTE)}{self.GLY_DOT} {sub}\033[0m")
        print("  " + self._rule())
        if mode_line.strip():
            print(f"  {self._fg(self._MUTE)}{mode_line}\033[0m")
        print()

    def _animate(self, label: str, grad) -> None:
        i = 0
        seg = 1.0 / self.total
        base = self.done * seg
        while not self._stop.is_set():
            spin = self.SPINNER[i % len(self.SPINNER)]
            shimmer = (i % 30) / 30.0
            # progreso aparente: rellena hasta ~80% del segmento actual mientras corre
            frac = base + seg * (0.15 + 0.65 * ((i % 40) / 40.0))
            bar = self._bar(frac, grad, shimmer=shimmer)
            pct = int(frac * 100)
            sys.stdout.write(
                f"\r  {self._fg(grad[1])}{spin}\033[0m {bar} "
                f"{self._fg(self._MUTE)}{pct:3d}%\033[0m  "
                f"{self._fg(self._INK)}{label}\033[0m"
                f"{self._fg(self._MUTE)}  {self._elapsed()}\033[0m\033[K"
            )
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)

    def phase(self, label: str, kind: str = "suite"):
        grad = {"hub": self.GRAD_HUB, "suite": self.GRAD_SUITE}.get(kind, self.GRAD_SUITE)
        return _Phase(self, label, grad)

    def finish_phase_ok(self, label: str, grad) -> None:
        self.done += 1
        if not self.enabled:
            print(f"  OK  {label}")
            return
        bar = self._bar(self.done / self.total, self.GRAD_OK)
        pct = int(self.done / self.total * 100)
        sys.stdout.write(
            f"\r  \033[1m{self._fg(self.GRAD_OK[1])}{self.GLY_OK}\033[0m {bar} "
            f"{self._fg(self._MUTE)}{pct:3d}%\033[0m  "
            f"{self._fg(self._INK)}{label}\033[0m"
            f"{self._fg(self._MUTE)}  {self._elapsed()}\033[0m\033[K\n"
        )
        sys.stdout.flush()

    def finish_phase_err(self, label: str) -> None:
        if not self.enabled:
            print(f"  FALLO  {label}")
            return
        sys.stdout.write(
            f"\r  \033[1m{self._fg((255, 138, 122))}{self.GLY_ERR}\033[0m  "
            f"{self._fg(self._INK)}{label}\033[0m\033[K\n"
        )
        sys.stdout.flush()

    def success(self, outputs: list[str]) -> None:
        self._restore_cursor()
        if not self.enabled:
            print("\nBuild listo:")
            for o in outputs:
                print(f"  {o}")
            return
        print()
        full_bar = self._bar(1.0, self.GRAD_OK)
        print(f"  {full_bar}  {self._fg(self._MUTE)}100%\033[0m")
        print(
            f"  \033[1m{self._fg(self.GRAD_OK[1])}{self.GLY_OK} BUILD COMPLETO\033[0m"
            f"{self._fg(self._MUTE)}   {self._elapsed()} total\033[0m"
        )
        print("  " + self._rule())
        for o in outputs:
            print(f"  {self._fg(self.GRAD_OK[1])}{self.GLY_DOT}\033[0m {self._fg(self._INK)}{o}\033[0m")
        print()

    def error(self, msg: str) -> None:
        self._restore_cursor()
        if not self.enabled:
            print(f"\nERROR: {msg}")
            return
        print(
            f"\n  \033[1m{self._fg((255, 138, 122))}{self.GLY_ERR} ERROR\033[0m  "
            f"{self._fg((255, 180, 170))}{msg}\033[0m\n"
        )

    def cancelled(self, msg: str = "Build cancelado") -> None:
        """Cancelación manual legítima: tono neutro ámbar, no es un error."""
        self._restore_cursor()
        if not self.enabled:
            print(f"\n{msg}")
            return
        print(f"\n  {self._fg((230, 180, 120))}{self.GLY_WARN} {msg}\033[0m\n")


class _Phase:
    def __init__(self, ui: BuildUI, label: str, grad) -> None:
        self.ui, self.label, self.grad = ui, label, grad

    def __enter__(self):
        if self.ui.enabled:
            self.ui._stop.clear()
            self.ui._thread = threading.Thread(
                target=self.ui._animate, args=(self.label, self.grad), daemon=True
            )
            self.ui._thread.start()
        else:
            print(f"  > {self.label} ...")
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.ui._thread is not None:
            self.ui._stop.set()
            self.ui._thread.join(timeout=1.0)
            self.ui._thread = None
        if exc_type is None:
            self.ui.finish_phase_ok(self.label, self.grad)
        else:
            self.ui.finish_phase_err(self.label)
        return False


def _detect_root() -> Path:
    """Permite ejecutar el builder tanto desde AI_SCRIPTS/ como desde la raíz del repo."""
    here = Path(__file__).resolve()
    candidates = [here.parent, here.parent.parent, Path.cwd().resolve()]
    for candidate in candidates:
        if (candidate / "app" / "main_qt.py").exists() and (candidate / "installers" / "nsis" / "neuromood_suite.nsi").exists():
            return candidate
    # fallback compatible con la estructura original: repo/AI_SCRIPTS/build_neuromood.py
    return here.parent.parent


ROOT = _detect_root()
DIST = ROOT / "dist"
BUILD = ROOT / "build"
LOG_FILE = ROOT / "build.log"
RUNTIME_ENV_DIR = BUILD / "runtime_env"

# UI de consola global (se inicializa en main()); None ⇒ prints planos.
UI: "BuildUI | None" = None
SUITE_RUNTIME_ENV = "build/runtime_env/suite/.env"
HUB_RUNTIME_ENV = "build/runtime_env/hub/.env"

SUITE_ENV_KEYS = (
    "SUPABASE_URL",
    "SUPABASE_KEY",
)
HUB_ENV_KEYS = SUITE_ENV_KEYS + (
    "SUPABASE_HUB_KEY",
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "OLLAMA_API_KEY",
    "OLLAMA_CLOUD_URL",
    "OPENAI_API_KEY",
)
OPTIONAL_ADD_DATA = {
    HUB_RUNTIME_ENV,
}
LABEL_ALIASES = {
    "NeuroMood Suite": "Suite Paciente",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def inside_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def clean_path(path: Path) -> None:
    if not inside_root(path):
        raise RuntimeError(f"Ruta fuera del proyecto: {path}")
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


def add_data(source: str, target: str) -> list[str]:
    return ["--add-data", f"{ROOT / source};{target}"]


def _read_root_env() -> dict[str, str]:
    """Lee .env local para generar configs runtime de instaladores sin loguear valores."""
    values: dict[str, str] = {}
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            text = line.strip()
            if not text or text.startswith("#") or "=" not in text:
                continue
            key, _, value = text.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key:
                values[key] = value
    for key in HUB_ENV_KEYS:
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def _looks_like_service_role_key(value: str) -> bool:
    """Detecta JWT Supabase service_role sin imprimir ni persistir el valor."""
    value = value.strip().strip("\"'")
    parts = value.split(".")
    if len(parts) < 2:
        return False
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("ascii"))
        data = json.loads(decoded.decode("utf-8"))
    except Exception:
        return False
    return data.get("role") == "service_role"


def _check_env_file() -> None:
    """Valida que el .env local tenga las variables necesarias antes de construir."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        raise RuntimeError(
            f"No existe .env en la raíz del proyecto ({rel(env_path)}).\n"
            "Creá un archivo .env con las variables requeridas antes de build:\n"
            "  SUPABASE_URL=https://tu-proyecto.supabase.co\n"
            "  SUPABASE_ANON_KEY=tu_anon_key\n"
            "El .env.example tiene las plantillas. Copialo y completalo:\n"
            "  copy .env.example .env"
        )
    values = _read_root_env()
    if not values.get("SUPABASE_URL"):
        raise RuntimeError(
            "SUPABASE_URL no está definida en .env. "
            "Agregá SUPABASE_URL=https://tu-proyecto.supabase.co"
        )
    for alias in ("SUPABASE_ANON_KEY", "SUPABASE_PUBLIC_KEY"):
        if values.get(alias) and not _looks_like_service_role_key(values[alias]):
            values["SUPABASE_KEY"] = values[alias]
            break
    if not values.get("SUPABASE_KEY"):
        raise RuntimeError(
            "No se encontró SUPABASE_KEY ni SUPABASE_ANON_KEY válida en .env.\n"
            "Agregá SUPABASE_ANON_KEY=tu_anon_key al .env y volvé a intentar."
        )
    if _looks_like_service_role_key(values["SUPABASE_KEY"]):
        raise RuntimeError(
            "SUPABASE_KEY (luego de resolver aliases) es una service_role key.\n"
            "Usá solo la anon key (role=anon) en builds distribuidos.\n"
            "La service_role key solo se usa localmente en el Hub.\n\n"
            "Agregá SUPABASE_ANON_KEY=tu_anon_key al .env y volvé a intentar."
        )


def _resolve_supabase_runtime_keys(values: dict[str, str]) -> None:
    """Separa claves Supabase por superficie sin loguear secretos.

    SUPABASE_KEY queda siempre como anon/public para Suite. SUPABASE_HUB_KEY
    puede contener la clave operativa del Hub profesional cuando está disponible.
    """
    hub_candidates = (
        values.get("SUPABASE_HUB_KEY"),
        values.get("SUPABASE_SERVICE_ROLE_KEY"),
        values.get("SUPABASE_SERVICE_KEY"),
        values.get("SUPABASE_KEY"),
    )
    for candidate in hub_candidates:
        if candidate and _looks_like_service_role_key(candidate):
            values["SUPABASE_HUB_KEY"] = candidate.strip().strip("\"'")
            break

    for alias in ("SUPABASE_ANON_KEY", "SUPABASE_PUBLIC_KEY", "SUPABASE_KEY"):
        if values.get(alias) and not _looks_like_service_role_key(values[alias]):
            values["SUPABASE_KEY"] = values[alias].strip().strip("\"'")
            break


def _validate_runtime_env_values(values: dict[str, str]) -> None:
    """Valida valores que se empaquetan en los .env runtime sin loguear secretos."""

    def _clean(key: str) -> str:
        value = (values.get(key) or "").strip().strip("\"'")
        if value:
            values[key] = value
        return value

    url = _clean("SUPABASE_URL")
    key = _clean("SUPABASE_KEY")
    hub_key = _clean("SUPABASE_HUB_KEY")

    missing = [name for name, value in (("SUPABASE_URL", url), ("SUPABASE_KEY", key)) if not value]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Faltan variables para generar el .env runtime: {joined}.\n"
            "El instalador no debe compilarse con credenciales Supabase incompletas."
        )

    if any(ch in url for ch in "\r\n") or any(ch in key for ch in "\r\n"):
        raise RuntimeError("SUPABASE_URL/SUPABASE_KEY contienen saltos de línea inválidos.")

    if not (url.startswith("https://") or url.startswith("http://")):
        raise RuntimeError("SUPABASE_URL debe comenzar con http:// o https://.")

    if _looks_like_service_role_key(key):
        raise RuntimeError(
            "SUPABASE_KEY (runtime) es una service_role key.\n"
            "Los instaladores solo pueden empaquetar la anon key."
        )

    if hub_key and not _looks_like_service_role_key(hub_key):
        raise RuntimeError("SUPABASE_HUB_KEY debe ser una service_role key o quedar vacía.")

    for optional_key in HUB_ENV_KEYS[len(SUITE_ENV_KEYS):]:
        optional_value = _clean(optional_key)
        if optional_value and any(ch in optional_value for ch in "\r\n"):
            raise RuntimeError(f"{optional_key} contiene saltos de línea inválidos.")


def _write_runtime_env(path: Path, keys: tuple[str, ...], values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={values[key]}" for key in keys if values.get(key)]
    if not lines and path.as_posix().endswith(HUB_RUNTIME_ENV):
        if path.exists():
            path.unlink()
        return
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


_NSIS_BMPS = {
    "suite_welcome.bmp": (164, 314),
    "suite_header.bmp": (150, 57),
    "hub_welcome.bmp": (164, 314),
    "hub_header.bmp": (150, 57),
}


def regenerate_nsis_assets(log, dry_run: bool = False) -> None:
    """Regenera los BMPs de marca de los installers desde los tokens reales.

    F6 "Índigo Calmado": los bitmaps salen de installers/nsis/
    generate_nsis_assets.py (que importa shared.theme) — un cambio de paleta
    nunca más deja los installers desfasados. Best-effort: si PIL falta o el
    generador falla, se usan los .bmp VERSIONADOS (warning, nunca rompe el
    build). Fallo duro SOLO si al final falta algún .bmp (makensis daría un
    error críptico).
    """
    assets_dir = ROOT / "installers" / "nsis" / "assets"
    if not dry_run:
        try:
            import importlib

            gen = importlib.import_module("installers.nsis.generate_nsis_assets")
            gen.main()
            from PIL import Image as _PILImage

            for name, expected in _NSIS_BMPS.items():
                got = _PILImage.open(assets_dir / name).size
                if got != expected:
                    raise RuntimeError(f"{name}: tamaño {got} != esperado {expected}")
            log.write("[nsis-assets] BMPs regenerados desde tokens (shared/theme.py)\n")
        except ImportError as exc:
            log.write(f"[nsis-assets] AVISO: PIL/generador no disponible ({exc}); se usan los BMP versionados.\n")
        except Exception as exc:
            log.write(f"[nsis-assets] AVISO: fallo el generador ({exc}); se usan los BMP versionados.\n")
    missing = [n for n in _NSIS_BMPS if not (assets_dir / n).exists()]
    if missing:
        raise RuntimeError(
            f"Faltan bitmaps NSIS en {rel(assets_dir)}: {', '.join(missing)} — "
            "makensis fallaría de forma críptica. Regenerá con "
            "installers\\nsis\\generate_nsis_assets.py o restaurá los versionados."
        )


def prepare_runtime_envs() -> None:
    """Genera .env temporales que los instaladores copiaran a AppData.

    CRÍTICO: estos archivos DEBEN existir cuando makensis compila los .nsi porque
    el !if /FileExists en cada script los detecta en tiempo de compilación.
    Si faltan, el instalador no embebe las credenciales → las apps no conectan a Supabase.
    """
    values = _read_root_env()

    _resolve_supabase_runtime_keys(values)

    _validate_runtime_env_values(values)

    # Suite (app del paciente, distribución pública): SOLO SUPABASE anon.
    # Nunca recibe API keys de IA — esas son del profesional.
    _write_runtime_env(ROOT / SUITE_RUNTIME_ENV, SUITE_ENV_KEYS, values)

    # Hub (herramienta del profesional): SUPABASE + API keys de IA, para que el
    # asistente IA funcione sin configuración manual. El Hub es la app del
    # clínico/dueño, no la app pública del paciente — por eso lleva las keys.
    _write_runtime_env(ROOT / HUB_RUNTIME_ENV, HUB_ENV_KEYS, values)
    if not any(values.get(k) for k in HUB_ENV_KEYS[len(SUITE_ENV_KEYS) + 1:]):
        print(
            "  AVISO: el .env raíz no tiene API keys de IA (GROQ/GEMINI/...). "
            "El asistente IA del Hub no funcionará hasta agregarlas al .env y recompilar."
        )

    # Verificación explícita: si los archivos no existen, el build debe fallar aquí,
    # no silenciosamente en NSIS donde sería difícil de diagnosticar.
    suite_env = ROOT / SUITE_RUNTIME_ENV
    hub_env = ROOT / HUB_RUNTIME_ENV
    if not suite_env.exists():
        raise RuntimeError(
            f"No se generó {rel(suite_env)} — el instalador Suite no tendrá credenciales Supabase."
        )
    # Hub env es opcional (puede no existir si NM_PACKAGE_RUNTIME_SECRETS no está activo
    # Y no hay creds base), pero si SUPABASE_URL y SUPABASE_KEY están disponibles,
    # debe existir.
    if values.get("SUPABASE_URL") and values.get("SUPABASE_KEY") and not hub_env.exists():
        raise RuntimeError(
            f"No se generó {rel(hub_env)} — el instalador Hub no tendrá credenciales Supabase."
        )


def _build_payload_zip(
    dest_dir: Path,
    zip_name: str,
    src_entries: list[tuple[Path, str]],
) -> Path:
    """Empaqueta carpetas/archivos en un único zip al lado del instalador.

    dest_dir: carpeta destino (típicamente dist/Instalador X/).
    zip_name: nombre del archivo zip (ej. "payload_suite.zip").
    src_entries: lista de pares (src_path, arcname_root). Por cada entrada,
        si src_path es un directorio se incluye recursivamente con arcname_root
        como prefijo dentro del zip; si es un archivo se incluye plano bajo
        arcname_root.

    Devuelve la ruta absoluta del zip creado. Lanza FileNotFoundError si
    alguna fuente falta — útil para abortar el build temprano.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / zip_name
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arcname_root in src_entries:
            src = Path(src)
            if not src.exists():
                raise FileNotFoundError(f"Fuente de payload inexistente: {src}")
            if src.is_dir():
                for child in src.rglob("*"):
                    if not child.is_file():
                        continue
                    rel = child.relative_to(src).as_posix()
                    arcname = f"{arcname_root}/{rel}" if arcname_root else rel
                    zf.write(child, arcname)
            else:
                arcname = f"{arcname_root}/{src.name}" if arcname_root else src.name
                zf.write(src, arcname)
    return zip_path


FINAL_LOGO_ASSETS = [
    "LOGO.png",
    "logos-dark.png",
    "logos-light.png",
    "logos-icon-dark.png",
    "logos-icon-light.png",
    "logo-dark.png",
    "logo-light.png",
    "logo-icon-dark.png",
    "logo-icon-light.png",
    "logo_light.png",
    "logo_dark.png",
    "app_icon.ico",
]


def final_asset_data() -> list[tuple[str, str]]:
    """Incluye assets finales en raíz y en assets/ para cubrir ambos estilos de lookup."""
    data = [("assets", "assets")]
    data.extend((f"assets/{name}", ".") for name in FINAL_LOGO_ASSETS)
    return data


def final_asset_requires() -> list[str]:
    # Los 4 plural son los que usa el mockup v3 como fuente de verdad.
    return [
        "assets/logos-dark.png",
        "assets/logos-light.png",
        "assets/logos-icon-dark.png",
        "assets/logos-icon-light.png",
    ]


@dataclass(frozen=True)
class BuildTarget:
    label: str
    name: str
    entry: str
    icon: str
    mode: str = "--onedir"
    add_data: list[tuple[str, str]] = field(default_factory=list)
    hidden_imports: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    clean_dist: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)


COMMON_SHARED_IMPORTS = [
    "shared",
    "shared.theme",
    "shared.theme_qt",
    "shared.components_qt",
    "shared.utils",
]


APP_SUITE_IMPORTS = [
    "qtawesome",
    "PyQt6.QtSvg",            # v3: QSvgRenderer para icons_svg + NMMoodEmoji
    "PyQt6.QtNetwork",        # guard de instancia única (QLocalServer/QLocalSocket)
    "matplotlib",
    "pystray",
    "pystray._win32",
    "winotify",
    "PIL",
    "sqlite3",
    "shared.theme",
    "shared.theme_qt",
    "shared.components_qt",
    "shared.db",
    "shared.config",
    "shared.identidad",
    "shared.utils",
    "shared.visual_qa",
    "shared.icons_svg",
    "supabase",
    "app.home_qt",
    "app.avisos_daemon",
    "app.modules.animo_qt",
    "app.modules.respiracion_qt",
    "app.modules.registro_tcc_qt",
    "app.modules.rutina_qt",
    "app.modules.actividades_qt",
    "app.modules.timer_qt",
    "app.modules.avisos_qt",
    "app.modules.dbt_qt",  # módulo #7 — cargado dinámicamente vía importlib
]


HUB_IMPORTS = [
    "qtawesome",
    "PyQt6.QtSvg",            # v3: QSvgRenderer para icons_svg + NMMoodEmoji
    "PyQt6.QtNetwork",        # guard de instancia única (QLocalServer/QLocalSocket)
    "supabase",
    "pystray",
    "pystray._win32",
    "winotify",
    "PIL",
    "sqlite3",
    "groq",
    "google.generativeai",
    "openai",
    "pyqtgraph",
    "reportlab",
    "reportlab.lib",
    "reportlab.lib.pagesizes",
    "reportlab.lib.styles",
    "reportlab.lib.units",
    "reportlab.platypus",
    "numpy",
    "matplotlib",
    "httpx",
    "shared.theme",
    "shared.theme_qt",
    "shared.components_qt",
    "shared.db",
    "shared.config",
    "shared.sync",
    "shared.identidad",
    "shared.utils",
    "shared.visual_qa",
    "shared.icons_svg",
    "hub.pacientes_qt",
    "hub.ia_asistente",
    "hub.exportar",
    "hub.personalizacion_global",  # vista nueva (reestructura v1.0)
    "hub.plan_terapeutico",        # tab del detalle (reestructura v1.0)
    "hub.editors.text_overrides_editor",
    # tcc_template_editor eliminado en feat(hub-reorg-1): subtab Pensamientos borrado
]


TARGETS = [
    BuildTarget(
        label="Suite Paciente",
        name="NeuroMood Suite",
        entry="app/main_qt.py",
        icon="assets/NM_icon.ico",
        add_data=final_asset_data() + [
            ("assets/NM_icon.ico", "."),
            ("assets/app_icon.ico", "."),
            ("assets/installer_icon.ico", "."),
            ("assets/no_symbol.ico", "."),
            ("assets/fonts", "assets/fonts"),
            ("shared", "shared"),
            ("app", "app"),
        ],
        hidden_imports=APP_SUITE_IMPORTS,
        requires=["assets/LOGO.png", "assets/NM_icon.ico", "app/main_qt.py"] + final_asset_requires(),
        clean_dist=["NeuroMood Suite"],
        provides=["dist/NeuroMood Suite/NeuroMood Suite.exe"],
    ),
    BuildTarget(
        label="NeuroMood Hub",
        name="NeuroMood Hub",
        entry="hub/main_qt.py",
        icon="assets/NM_icon.ico",
        add_data=final_asset_data() + [
            ("assets/NM_icon.ico", "."),
            ("assets/app_icon.ico", "."),
            ("assets/installer_icon.ico", "."),
            ("assets/no_symbol.ico", "."),
            ("assets/fonts", "assets/fonts"),
            ("shared", "shared"),
            ("hub", "hub"),
        ],
        hidden_imports=HUB_IMPORTS,
        requires=["assets/LOGO.png", "assets/NM_icon.ico", "hub/main_qt.py"] + final_asset_requires(),
        clean_dist=["NeuroMood Hub"],
        provides=["dist/NeuroMood Hub/NeuroMood Hub.exe"],
    ),
]

# ── NSIS integration ──────────────────────────────────────────────────────────
# Rutas conocidas de makensis.exe para búsqueda sin necesidad de PATH configurado.
_NSIS_CANDIDATE_PATHS: list[Path] = [
    Path(r"C:\Program Files (x86)\NSIS\makensis.exe"),
    Path(r"C:\Program Files\NSIS\makensis.exe"),
]
# Scripts NSIS y rutas de salida de instaladores nativos.
_NSIS_NSI_SUITE: Path = Path("installers") / "nsis" / "neuromood_suite.nsi"
_NSIS_OUTPUT_SUITE: Path = Path("dist") / "NM_Suite_Setup.exe"
_NSIS_NSI_HUB: Path = Path("installers") / "nsis" / "neuromood_hub.nsi"
_NSIS_OUTPUT_HUB: Path = Path("dist") / "NM_Hub_Setup.exe"

# EXEs que NSIS empaqueta (generados por PyInstaller, prerequisito).
_SUITE_DIST_EXE: Path = Path("dist") / "NeuroMood Suite" / "NeuroMood Suite.exe"
_HUB_DIST_EXE: Path = Path("dist") / "NeuroMood Hub" / "NeuroMood Hub.exe"
# Labels que disparan la fase NSIS cuando se usa --only.
_SUITE_RELATED_LABELS: frozenset[str] = frozenset({"Suite Paciente", "NeuroMood Suite"})
_HUB_RELATED_LABELS: frozenset[str] = frozenset({"NeuroMood Hub"})


def normalize_label(label: str) -> str:
    return LABEL_ALIASES.get(label, label)


def validate(target: BuildTarget, planned_outputs: set[str]) -> list[str]:
    missing = []
    for item in target.requires:
        if item in planned_outputs:
            continue
        if not (ROOT / item).exists():
            missing.append(item)
    return missing




def run_command(args: list[str], log) -> None:
    log.write(" ".join(args) + "\n\n")
    log.flush()
    result = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"PyInstaller salio con codigo {result.returncode}")


def build_target(
    index: int,
    total: int,
    target: BuildTarget,
    *,
    clean: bool,
    dry_run: bool,
    planned_outputs: set[str],
    log,
) -> None:
    if UI is None or not UI.enabled:
        print(f"[{index}/{total}] {target.label}")
    log.write(f"[{index}/{total}] {target.label}\n")
    missing = validate(target, planned_outputs if dry_run else set())
    if missing:
        raise RuntimeError("Faltan archivos requeridos: " + ", ".join(missing))
    if dry_run:
        if UI is None or not UI.enabled:
            print("    OK preflight")
        return

    for item in target.clean_dist:
        clean_path(DIST / item)
    clean_path(BUILD / target.name)
    clean_path(ROOT / f"{target.name}.spec")

    effective_add_data = [
        pair for pair in target.add_data
        if pair[0] not in OPTIONAL_ADD_DATA or (ROOT / pair[0]).exists()
    ]

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        target.mode,
        "--windowed",
        "--optimize",
        "2",
        "--icon",
        str(ROOT / target.icon),
        "--distpath",
        str(DIST),
        "--workpath",
        str(BUILD),
        "--paths",
        str(ROOT),
        "--log-level",
        "WARN",
        "--name",
        target.name,
    ]
    if clean:
        args.insert(4, "--clean")
    for source, dest in effective_add_data:
        args.extend(add_data(source, dest))
    for hidden in sorted(set(target.hidden_imports)):
        args.extend(["--hidden-import", hidden])
    args.append(str(ROOT / target.entry))

    run_command(args, log)
    if UI is None or not UI.enabled:
        print("    OK")


def cleanup_generated(*, keep_build: bool) -> None:
    for spec in ROOT.glob("*.spec"):
        clean_path(spec)
    if not keep_build:
        clean_path(BUILD)


# ── NSIS helpers ──────────────────────────────────────────────────────────────

def find_makensis() -> Path | None:
    """Busca makensis.exe en rutas conocidas de NSIS y en PATH del sistema."""
    for candidate in _NSIS_CANDIDATE_PATHS:
        if candidate.exists():
            return candidate
    found = shutil.which("makensis.exe") or shutil.which("makensis")
    return Path(found) if found else None


def build_nsis_installer(
    *,
    app_name: str,
    output_name: str,
    nsi_rel: Path,
    output_rel: Path,
    dist_exe_rel: Path,
    dry_run: bool,
    log,
) -> Path:
    """Compila un instalador NSIS con makensis.

    Prerequisito (no dry-run): el EXE de la app debe existir en dist/.
    dry_run=True: valida makensis y el .nsi sin invocar el compilador.
    Devuelve la ruta esperada del EXE de salida en ambos modos.
    Lanza RuntimeError con mensaje claro si makensis no está instalado.
    """
    nsi = ROOT / nsi_rel
    output_exe = ROOT / output_rel

    if UI is None or not UI.enabled:
        print(f"[NSIS] {app_name}  ->  {output_name}")
    log.write(f"[NSIS] {app_name}  ->  {output_name}\n")

    makensis = find_makensis()
    if makensis is None:
        raise RuntimeError(
            "makensis.exe no encontrado. Instala NSIS desde:\n"
            "  https://nsis.sourceforge.io/\n"
            "Rutas buscadas:\n"
            + "\n".join(f"  {p}" for p in _NSIS_CANDIDATE_PATHS)
        )

    if not nsi.exists():
        raise RuntimeError(f"Script NSIS no encontrado: {rel(nsi)}")

    if dry_run:
        if UI is None or not UI.enabled:
            print(f"    makensis: {makensis}")
            print(f"    NSI:      {rel(nsi)}")
            print(f"    OUT:      {rel(output_exe)}")
            print(f"    OK preflight (NSIS {app_name})")
        return output_exe

    dist_exe = ROOT / dist_exe_rel
    if not dist_exe.exists():
        raise RuntimeError(
            f"Prerequisito NSIS ausente: {rel(dist_exe)}\n"
            f"Ejecuta primero el target de app '{app_name}' para generar dist/."
        )

    output_exe.parent.mkdir(parents=True, exist_ok=True)
    log.write(f"\n[NSIS] makensis {nsi}\n\n")
    log.flush()
    result = subprocess.run(
        [str(makensis), nsi.name],
        cwd=nsi.parent,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"makensis salio con codigo {result.returncode}. Revisa build.log.")

    if UI is None or not UI.enabled:
        print(f"    OK  ->  {rel(output_exe)}")
    log.write(f"    OK  ->  {rel(output_exe)}\n")
    return output_exe


def build_nsis_suite(*, dry_run: bool, log) -> Path:
    return build_nsis_installer(
        app_name="NeuroMood Suite",
        output_name="NM_Suite_Setup.exe",
        nsi_rel=_NSIS_NSI_SUITE,
        output_rel=_NSIS_OUTPUT_SUITE,
        dist_exe_rel=_SUITE_DIST_EXE,
        dry_run=dry_run,
        log=log,
    )


def build_nsis_hub(*, dry_run: bool, log) -> Path:
    return build_nsis_installer(
        app_name="NeuroMood Hub",
        output_name="NM_Hub_Setup.exe",
        nsi_rel=_NSIS_NSI_HUB,
        output_rel=_NSIS_OUTPUT_HUB,
        dist_exe_rel=_HUB_DIST_EXE,
        dry_run=dry_run,
        log=log,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compila los EXE oficiales de NeuroMood.")
    parser.add_argument("--clean", action="store_true", help="Forzar cache limpio de PyInstaller.")
    parser.add_argument("--clean-all", action="store_true", help="Borrar dist/, build/ y specs antes de compilar todo.")
    parser.add_argument("--dry-run", action="store_true", help="Validar rutas sin compilar.")
    parser.add_argument("--keep-build", action="store_true", help="Conservar build/ para diagnostico.")
    parser.add_argument("--only", action="append", default=[], metavar="LABEL",
                        help="Solo construir estos targets por label (puede repetirse)")
    parser.add_argument("--skip", action="append", default=[], metavar="LABEL",
                        help="No construir estos targets")
    parser.add_argument("--distribution-only", action="store_true",
                        help="Generar solo instaladores NSIS desde apps ya existentes en dist/.")
    parser.add_argument("--installers-only", action="store_true",
                        help="Alias de --distribution-only.")
    parser.add_argument("--installer-mode", choices=("external", "nsis"), default="external",
                        help="Compatibilidad QA: 'external' usa el backend NSIS oficial.")
    return parser.parse_args()


def main() -> int:
    # UTF-8 en consola para gradientes, box-drawing y acentos (evita 'charmap').
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except Exception:
            pass

    args = parse_args()
    distribution_only = args.distribution_only or args.installers_only

    if find_makensis() is None:
        raise RuntimeError(
            "makensis.exe no encontrado en el sistema.\n"
            "Para compilar el instalador oficial se requiere NSIS.\n"
            "Rutas buscadas:\n"
            + "\n".join(f"  {p}" for p in _NSIS_CANDIDATE_PATHS)
        )

    if distribution_only and args.clean_all:
        print("ERROR: --clean-all no se puede combinar con --distribution-only.")
        print("Ese modo necesita reutilizar dist/NeuroMood Suite y dist/NeuroMood Hub.")
        return 1

    if args.clean_all:
        clean_path(DIST)
        clean_path(BUILD)
        for spec in ROOT.glob("*.spec"):
            clean_path(spec)

    if not distribution_only:
        _check_env_file()

    BUILD.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(parents=True, exist_ok=True)
    prepare_runtime_envs()
    LOG_FILE.write_text("NeuroMood build log\n", encoding="utf-8")

    only_labels = [normalize_label(label) for label in args.only]
    skip_labels = [normalize_label(label) for label in args.skip]
    should_nsis_suite = (
        (not only_labels or any(lbl in _SUITE_RELATED_LABELS for lbl in only_labels))
        and not any(lbl in _SUITE_RELATED_LABELS for lbl in skip_labels)
    )
    should_nsis_hub = (
        (not only_labels or any(lbl in _HUB_RELATED_LABELS for lbl in only_labels))
        and not any(lbl in _HUB_RELATED_LABELS for lbl in skip_labels)
    )

    targets_to_build = TARGETS
    if distribution_only:
        targets_to_build = []
    if only_labels:
        targets_to_build = [t for t in targets_to_build if t.label in only_labels]
    if skip_labels:
        targets_to_build = [t for t in targets_to_build if t.label not in skip_labels]
    if not targets_to_build and not (should_nsis_suite or should_nsis_hub):
        print("No hay targets para construir.")
        return 0

    def _kind(label: str) -> str:
        return "hub" if "Hub" in label else "suite"

    total_phases = len(targets_to_build) + int(should_nsis_suite) + int(should_nsis_hub)

    global UI
    UI = BuildUI(total_phases)

    mode_bits = []
    if args.clean:
        mode_bits.append("clean")
    if args.clean_all:
        mode_bits.append("clean-all")
    if args.dry_run:
        mode_bits.append("dry-run")
    if distribution_only:
        mode_bits.append("distribution-only")
    mode_line = "Salida: dist/ · Log: build.log · NSIS oficial"
    if mode_bits:
        mode_line += "  ·  modo: " + ", ".join(mode_bits)
    UI.banner(mode_line)

    nsis_outputs: list[Path] = []

    try:
        with LOG_FILE.open("a", encoding="utf-8") as log:
            planned_outputs: set[str] = set()
            for index, target in enumerate(targets_to_build, start=1):
                with UI.phase(f"Compilando {target.name}", _kind(target.label)):
                    build_target(
                        index,
                        len(targets_to_build),
                        target,
                        clean=args.clean,
                        dry_run=args.dry_run,
                        planned_outputs=planned_outputs,
                        log=log,
                    )
                planned_outputs.update(target.provides)

            # ── Native installer step (NSIS) ──────────────────────────────────
            if should_nsis_suite or should_nsis_hub:
                regenerate_nsis_assets(log=log, dry_run=args.dry_run)
            if should_nsis_suite:
                with UI.phase("Instalador NSIS · NeuroMood Suite", "suite"):
                    nsis_outputs.append(build_nsis_suite(dry_run=args.dry_run, log=log))
            if should_nsis_hub:
                with UI.phase("Instalador NSIS · NeuroMood Hub", "hub"):
                    nsis_outputs.append(build_nsis_hub(dry_run=args.dry_run, log=log))

        cleanup_generated(keep_build=args.keep_build)
    except KeyboardInterrupt:
        if UI is not None:
            UI.cancelled("Build cancelado por el usuario.")
        else:
            print("\nBuild cancelado por el usuario.")
        cleanup_generated(keep_build=True)
        return 130
    except Exception as exc:
        UI.error(str(exc))
        print("Revisa build.log para el detalle tecnico.")
        cleanup_generated(keep_build=True)
        return 1

    # Verificar que PyInstaller no emitió errores de hidden imports (sale con código 0 igualmente)
    hidden_errors = []
    try:
        log_text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
        for line in log_text.splitlines():
            if "ERROR: Hidden import" in line or "hidden import not found" in line.lower():
                hidden_errors.append(line.strip())
    except Exception:
        pass
    if hidden_errors:
        print("")
        print("ADVERTENCIA — hidden imports no encontrados (revisar dependencias):")
        for e in hidden_errors:
            print(f"  {e}")
        print("")

    outputs = [provided for target in targets_to_build for provided in target.provides]
    outputs += [rel(exe) for exe in nsis_outputs]
    UI.success(outputs)
    return 1 if hidden_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
