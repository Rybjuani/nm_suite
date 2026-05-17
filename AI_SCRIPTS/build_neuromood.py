from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
LOG_FILE = ROOT / "build.log"


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
    "shared.installer_common",
    "shared.utils",
]


APP_SUITE_IMPORTS = [
    "qtawesome",
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
    "app.home_qt",
    "app.avisos_daemon",
    "app.motor_activacion",
    "app.modules.animo_qt",
    "app.modules.respiracion_qt",
    "app.modules.registro_tcc_qt",
    "app.modules.rutina_qt",
    "app.modules.actividades_qt",
    "app.modules.timer_qt",
    "app.modules.avisos_qt",
]


HUB_IMPORTS = [
    "qtawesome",
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
    "scipy",
    "scipy.interpolate",
    "httpx",
    "postgrest",
    "gotrue",
    "shared.theme",
    "shared.theme_qt",
    "shared.components_qt",
    "shared.db",
    "shared.config",
    "shared.sync",
    "shared.identidad",
    "shared.utils",
    "shared.visual_qa",
    "hub.pacientes_qt",
    "hub.ia_asistente",
    "hub.exportar",
]


INSTALLER_IMPORTS = COMMON_SHARED_IMPORTS + [
    "win32com",
    "win32com.client",
    "pywintypes",
    "PIL",
    "qtawesome",
]


SUITE_INSTALLER_IMPORTS = INSTALLER_IMPORTS + [
    "supabase",
    "gotrue",
    "httpx",
    "postgrest",
    "shared.identidad",
    "shared.config",
    "sqlite3",
]


TARGETS = [
    BuildTarget(
        label="Suite Paciente",
        name="NeuroMood Suite",
        entry="app/main_qt.py",
        icon="assets/NM_icon.ico",
        add_data=[
            ("assets/LOGO.png", "."),
            ("assets/NM_icon.ico", "."),
            (".env", "."),
            ("shared", "shared"),
            ("app", "app"),
        ],
        hidden_imports=APP_SUITE_IMPORTS,
        requires=["assets/LOGO.png", "assets/NM_icon.ico", ".env", "app/main_qt.py"],
        clean_dist=["NeuroMood Suite"],
        provides=["dist/NeuroMood Suite/NeuroMood Suite.exe"],
    ),
    BuildTarget(
        label="NeuroMood Hub",
        name="NeuroMood Hub",
        entry="hub/main_qt.py",
        icon="assets/NM_icon.ico",
        add_data=[
            ("assets/LOGO.png", "."),
            ("assets/NM_icon.ico", "."),
            (".env", "."),
            ("shared", "shared"),
            ("hub", "hub"),
        ],
        hidden_imports=HUB_IMPORTS,
        requires=["assets/LOGO.png", "assets/NM_icon.ico", ".env", "hub/main_qt.py"],
        clean_dist=["NeuroMood Hub"],
        provides=["dist/NeuroMood Hub/NeuroMood Hub.exe"],
    ),
    BuildTarget(
        label="Desinstalador Suite",
        name="Desinstalador Suite",
        entry="installers/uninstaller.py",
        icon="assets/no_symbol.ico",
        add_data=[
            ("shared", "shared"),
            ("assets/no_symbol.ico", "."),
            ("assets/installer_icon.ico", "."),
            ("assets/LOGO.png", "."),
        ],
        hidden_imports=INSTALLER_IMPORTS,
        requires=[
            "installers/uninstaller.py",
            "assets/no_symbol.ico",
            "assets/installer_icon.ico",
            "assets/LOGO.png",
        ],
        clean_dist=["Desinstalador Suite"],
        provides=["dist/Desinstalador Suite/Desinstalador Suite.exe"],
    ),
    BuildTarget(
        label="Instalador Suite",
        name="Instalador Suite",
        entry="installers/installer.py",
        icon="assets/installer_icon.ico",
        add_data=[
            ("shared", "shared"),
            ("assets/installer_icon.ico", "."),
            ("assets/NM_icon.ico", "."),
            ("assets/no_symbol.ico", "."),
            ("assets/LOGO.png", "."),
            (".env", "."),
            ("dist/NeuroMood Suite", "NeuroMood Suite"),
            ("dist/Desinstalador Suite", "Desinstalador Suite"),
        ],
        hidden_imports=SUITE_INSTALLER_IMPORTS,
        requires=[
            "installers/installer.py",
            "assets/installer_icon.ico",
            "assets/NM_icon.ico",
            "assets/no_symbol.ico",
            "assets/LOGO.png",
            ".env",
            "dist/NeuroMood Suite/NeuroMood Suite.exe",
            "dist/Desinstalador Suite/Desinstalador Suite.exe",
        ],
        clean_dist=["Instalador Suite"],
        provides=["dist/Instalador Suite/Instalador Suite.exe"],
    ),
    BuildTarget(
        label="Desinstalador Hub",
        name="Desinstalador Hub",
        entry="installers/uninstaller_pro.py",
        icon="assets/NM_icon.ico",
        add_data=[
            ("shared", "shared"),
            ("assets/NM_icon.ico", "."),
            ("assets/installer_icon.ico", "."),
            ("assets/LOGO.png", "."),
        ],
        hidden_imports=INSTALLER_IMPORTS,
        requires=[
            "installers/uninstaller_pro.py",
            "assets/NM_icon.ico",
            "assets/installer_icon.ico",
            "assets/LOGO.png",
        ],
        clean_dist=["Desinstalador Hub"],
        provides=["dist/Desinstalador Hub/Desinstalador Hub.exe"],
    ),
    BuildTarget(
        label="Instalador Hub",
        name="Instalador Hub",
        entry="installers/installer_pro.py",
        icon="assets/installer_icon.ico",
        add_data=[
            ("shared", "shared"),
            ("assets/installer_icon.ico", "."),
            ("assets/NM_icon.ico", "."),
            ("assets/no_symbol.ico", "."),
            ("assets/LOGO.png", "."),
            (".env", "."),
            ("dist/NeuroMood Hub", "NeuroMood Hub"),
            ("dist/Desinstalador Hub", "Desinstalador Hub"),
        ],
        hidden_imports=INSTALLER_IMPORTS + ["shared.identidad"],
        requires=[
            "installers/installer_pro.py",
            "assets/installer_icon.ico",
            "assets/NM_icon.ico",
            "assets/no_symbol.ico",
            "assets/LOGO.png",
            ".env",
            "dist/NeuroMood Hub/NeuroMood Hub.exe",
            "dist/Desinstalador Hub/Desinstalador Hub.exe",
        ],
        clean_dist=["Instalador Hub"],
        provides=["dist/Instalador Hub/Instalador Hub.exe"],
    ),
]


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
    print(f"[{index}/{total}] {target.label}")
    missing = validate(target, planned_outputs if dry_run else set())
    if missing:
        raise RuntimeError("Faltan archivos requeridos: " + ", ".join(missing))
    for item in target.clean_dist:
        clean_path(DIST / item)
    clean_path(BUILD / target.name)
    clean_path(ROOT / f"{target.name}.spec")

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
    for source, dest in target.add_data:
        args.extend(add_data(source, dest))
    for hidden in sorted(set(target.hidden_imports)):
        args.extend(["--hidden-import", hidden])
    args.append(str(ROOT / target.entry))

    if dry_run:
        print("    OK preflight")
        return
    run_command(args, log)
    print("    OK")


def cleanup_generated(*, keep_build: bool) -> None:
    for spec in ROOT.glob("*.spec"):
        clean_path(spec)
    if not keep_build:
        clean_path(BUILD)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compila los EXE oficiales de NeuroMood V3.")
    parser.add_argument("--clean", action="store_true", help="Forzar cache limpio de PyInstaller.")
    parser.add_argument("--dry-run", action="store_true", help="Validar rutas sin compilar.")
    parser.add_argument("--keep-build", action="store_true", help="Conservar build/ para diagnostico.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    DIST.mkdir(exist_ok=True)
    BUILD.mkdir(exist_ok=True)
    LOG_FILE.write_text("NeuroMood V3 build log\n", encoding="utf-8")

    print("============================================================")
    print(" NeuroMood V3 - Build oficial")
    print("============================================================")
    print("Salida: dist/")
    print("Log: build.log")
    if args.clean:
        print("Modo: clean")
    if args.dry_run:
        print("Modo: dry-run")
    print("")

    try:
        with LOG_FILE.open("a", encoding="utf-8") as log:
            for index, target in enumerate(TARGETS, start=1):
                planned_outputs = {provided for prior in TARGETS[: index - 1] for provided in prior.provides}
                build_target(
                    index,
                    len(TARGETS),
                    target,
                    clean=args.clean,
                    dry_run=args.dry_run,
                    planned_outputs=planned_outputs,
                    log=log,
                )
        cleanup_generated(keep_build=args.keep_build)
    except Exception as exc:
        print("")
        print(f"ERROR: {exc}")
        print("Revisa build.log para el detalle tecnico.")
        cleanup_generated(keep_build=True)
        return 1

    print("")
    print("Build listo:")
    print(r"  dist\NeuroMood Suite\NeuroMood Suite.exe")
    print(r"  dist\NeuroMood Hub\NeuroMood Hub.exe")
    print(r"  dist\Desinstalador Suite\Desinstalador Suite.exe")
    print(r"  dist\Desinstalador Hub\Desinstalador Hub.exe")
    print(r"  dist\Instalador Suite\Instalador Suite.exe")
    print(r"  dist\Instalador Hub\Instalador Hub.exe")
    print("")
    print("Se limpiaron specs generados y build/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
