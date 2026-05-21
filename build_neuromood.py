from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


def _detect_root() -> Path:
    """Permite ejecutar el builder tanto desde AI_SCRIPTS/ como desde la raíz del repo."""
    here = Path(__file__).resolve()
    candidates = [here.parent, here.parent.parent, Path.cwd().resolve()]
    for candidate in candidates:
        if (candidate / "app" / "main_qt.py").exists() and (candidate / "installers" / "installer.py").exists():
            return candidate
    # fallback compatible con la estructura original: repo/AI_SCRIPTS/build_neuromood.py
    return here.parent.parent


ROOT = _detect_root()
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
    "shared.installer_common",
    "shared.utils",
]


APP_SUITE_IMPORTS = [
    "qtawesome",
    "PyQt6.QtSvg",            # v3: QSvgRenderer para icons_svg + NMMoodEmoji
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
    "PyQt6.QtSvg",            # v3: QSvgRenderer para icons_svg + NMMoodEmoji
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
]


INSTALLER_IMPORTS = COMMON_SHARED_IMPORTS + [
    "win32com",
    "win32com.client",
    "pywintypes",
    "PIL",
    "qtawesome",
    "shared.icons_svg",   # v3: catálogo SVG (opcional pero alineado con Suite/Hub)
]


SUITE_INSTALLER_IMPORTS = INSTALLER_IMPORTS + [
    "supabase",
    "httpx",
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
        add_data=final_asset_data() + [
            ("assets/NM_icon.ico", "."),
            ("assets/installer_icon.ico", "."),
            ("assets/no_symbol.ico", "."),
            ("assets/fonts", "assets/fonts"),
            (".env", "."),
            ("shared", "shared"),
            ("app", "app"),
        ],
        hidden_imports=APP_SUITE_IMPORTS,
        requires=["assets/LOGO.png", "assets/NM_icon.ico", ".env", "app/main_qt.py"] + final_asset_requires(),
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
            ("assets/installer_icon.ico", "."),
            ("assets/no_symbol.ico", "."),
            ("assets/fonts", "assets/fonts"),
            (".env", "."),
            ("shared", "shared"),
            ("hub", "hub"),
        ],
        hidden_imports=HUB_IMPORTS,
        requires=["assets/LOGO.png", "assets/NM_icon.ico", ".env", "hub/main_qt.py"] + final_asset_requires(),
        clean_dist=["NeuroMood Hub"],
        provides=["dist/NeuroMood Hub/NeuroMood Hub.exe"],
    ),
    BuildTarget(
        label="Desinstalador Suite",
        name="Desinstalador Suite",
        entry="installers/uninstaller.py",
        icon="assets/no_symbol.ico",
        add_data=final_asset_data() + [
            ("shared", "shared"),
            ("assets/no_symbol.ico", "."),
            ("assets/installer_icon.ico", "."),
            ("assets/NM_icon.ico", "."),
            ("assets/fonts", "assets/fonts"),
        ],
        hidden_imports=INSTALLER_IMPORTS,
        requires=[
            "installers/uninstaller.py",
            "assets/no_symbol.ico",
            "assets/installer_icon.ico",
            "assets/LOGO.png",
            *final_asset_requires(),
        ],
        clean_dist=["Desinstalador Suite"],
        provides=["dist/Desinstalador Suite/Desinstalador Suite.exe"],
    ),
    BuildTarget(
        label="Instalador Suite",
        name="Instalador Suite",
        entry="installers/installer.py",
        icon="assets/installer_icon.ico",
        add_data=final_asset_data() + [
            ("shared", "shared"),
            ("assets/installer_icon.ico", "."),
            ("assets/NM_icon.ico", "."),
            ("assets/no_symbol.ico", "."),
            ("assets/fonts", "assets/fonts"),
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
            *final_asset_requires(),
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
        add_data=final_asset_data() + [
            ("shared", "shared"),
            ("assets/NM_icon.ico", "."),
            ("assets/installer_icon.ico", "."),
            ("assets/no_symbol.ico", "."),
            ("assets/fonts", "assets/fonts"),
        ],
        hidden_imports=INSTALLER_IMPORTS,
        requires=[
            "installers/uninstaller_pro.py",
            "assets/NM_icon.ico",
            "assets/installer_icon.ico",
            "assets/LOGO.png",
            *final_asset_requires(),
        ],
        clean_dist=["Desinstalador Hub"],
        provides=["dist/Desinstalador Hub/Desinstalador Hub.exe"],
    ),
    BuildTarget(
        label="Instalador Hub",
        name="Instalador Hub",
        entry="installers/installer_pro.py",
        icon="assets/installer_icon.ico",
        add_data=final_asset_data() + [
            ("shared", "shared"),
            ("assets/installer_icon.ico", "."),
            ("assets/NM_icon.ico", "."),
            ("assets/no_symbol.ico", "."),
            ("assets/fonts", "assets/fonts"),
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
            *final_asset_requires(),
            "dist/NeuroMood Hub/NeuroMood Hub.exe",
            "dist/Desinstalador Hub/Desinstalador Hub.exe",
        ],
        clean_dist=["Instalador Hub"],
        provides=["dist/Instalador Hub/Instalador Hub.exe"],
    ),
]


# ── Fase 7: mapa de payloads externos por instalador ───────────────────────────
# Cuando --installer-mode external, estos pares (src, name_dentro_del_zip) se
# excluyen de add_data y se empacan después de PyInstaller como zip adyacente.
_INSTALLER_PAYLOAD_MAP: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "Instalador Suite": (
        "payload_suite.zip",
        [
            ("dist/NeuroMood Suite", "NeuroMood Suite"),
            ("dist/Desinstalador Suite", "Desinstalador Suite"),
        ],
    ),
    "Instalador Hub": (
        "payload_hub.zip",
        [
            ("dist/NeuroMood Hub", "NeuroMood Hub"),
            ("dist/Desinstalador Hub", "Desinstalador Hub"),
        ],
    ),
}


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
    installer_mode: str = "nested",
) -> None:
    print(f"[{index}/{total}] {target.label}")
    missing = validate(target, planned_outputs if dry_run else set())
    if missing:
        raise RuntimeError("Faltan archivos requeridos: " + ", ".join(missing))
    if dry_run:
        print("    OK preflight")
        return

    for item in target.clean_dist:
        clean_path(DIST / item)
    clean_path(BUILD / target.name)
    clean_path(ROOT / f"{target.name}.spec")

    # Fase 7: en modo external, excluir del bundle las carpetas que irán al zip
    effective_add_data = list(target.add_data)
    if installer_mode == "external" and target.label in _INSTALLER_PAYLOAD_MAP:
        _, payload_entries = _INSTALLER_PAYLOAD_MAP[target.label]
        payload_sources = {src for src, _ in payload_entries}
        effective_add_data = [
            pair for pair in effective_add_data if pair[0] not in payload_sources
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
    print("    OK")

    # Fase 7: si modo external y target es un instalador, generar payload zip
    if installer_mode == "external" and target.label in _INSTALLER_PAYLOAD_MAP:
        zip_name, payload_entries = _INSTALLER_PAYLOAD_MAP[target.label]
        dest_dir = DIST / target.name
        src_resolved = [(ROOT / src, arc) for src, arc in payload_entries]
        zip_path = _build_payload_zip(dest_dir, zip_name, src_resolved)
        print(f"    OK payload externo: {rel(zip_path)}")


def cleanup_generated(*, keep_build: bool) -> None:
    for spec in ROOT.glob("*.spec"):
        clean_path(spec)
    if not keep_build:
        clean_path(BUILD)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compila los EXE oficiales de NeuroMood V3.")
    parser.add_argument("--clean", action="store_true", help="Forzar cache limpio de PyInstaller.")
    parser.add_argument("--clean-all", action="store_true", help="Borrar dist/, build/ y specs antes de compilar todo.")
    parser.add_argument("--dry-run", action="store_true", help="Validar rutas sin compilar.")
    parser.add_argument("--keep-build", action="store_true", help="Conservar build/ para diagnostico.")
    parser.add_argument("--only", action="append", default=[], metavar="LABEL",
                        help="Solo construir estos targets por label (puede repetirse)")
    parser.add_argument("--skip", action="append", default=[], metavar="LABEL",
                        help="No construir estos targets")
    parser.add_argument("--installer-mode", choices=["nested", "external"], default="nested",
                        help="nested (default): empaqueta Suite/Hub dentro del instalador via PyInstaller. "
                             "external: genera un payload_*.zip al lado del instalador (Fase 7).")
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
    if args.clean_all:
        print("Modo: clean-all")
    if args.dry_run:
        print("Modo: dry-run")
    print(f"Installer mode: {args.installer_mode}")
    print("")

    targets_to_build = TARGETS
    if args.only:
        targets_to_build = [t for t in TARGETS if t.label in args.only]
    if args.skip:
        targets_to_build = [t for t in targets_to_build if t.label not in args.skip]
    if not targets_to_build:
        print("No hay targets para construir.")
        return 0

    try:
        with LOG_FILE.open("a", encoding="utf-8") as log:
            for index, target in enumerate(targets_to_build, start=1):
                # Calculate planned outputs using the full TARGETS list
                target_idx = TARGETS.index(target)
                planned_outputs = {provided for prior in TARGETS[:target_idx] for provided in prior.provides}
                build_target(
                    index,
                    len(targets_to_build),
                    target,
                    clean=args.clean,
                    dry_run=args.dry_run,
                    planned_outputs=planned_outputs,
                    log=log,
                    installer_mode=args.installer_mode,
                )
        cleanup_generated(keep_build=args.keep_build)
    except Exception as exc:
        print("")
        print(f"ERROR: {exc}")
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
    return 1 if hidden_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
