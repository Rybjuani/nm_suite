"""
QA EXE capture runner for NeuroMood.

Runs compiled EXEs only:
- Instalador Suite
- Instalador Hub
- installed patient app, all modules in dark and light
- installed NeuroMood Hub, main views and patient detail options in dark and light
- Desinstalador Suite and Desinstalador Hub

The script does not inspect or analyze screenshots. It only captures active
windows to disk for manual comparison.

Default output:
  _test_screens/qa_exe_capture/<timestamp>/

Recommended:
  python "script tests/qa_exe_capture.py" --build
"""

from __future__ import annotations

import argparse
import ctypes
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from PIL import ImageGrab
except ImportError as exc:
    raise SystemExit(
        "Pillow is required for screenshots. Install project requirements first."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = ROOT / "_test_screens" / "qa_exe_capture"

SUITE_INSTALLER = ROOT / "dist" / "Instalador Suite" / "Instalador Suite.exe"
HUB_INSTALLER = ROOT / "dist" / "Instalador Hub" / "Instalador Hub.exe"

QA_ROOT = Path.home() / "NeuromoodV3_QA"
SUITE_DIR = QA_ROOT / "NeuroMood Suite"
HUB_DIR = QA_ROOT / "NeuroMood Hub"

SUITE_EXE = SUITE_DIR / "NeuroMood Suite.exe"
HUB_EXE = HUB_DIR / "NeuroMood Hub.exe"
SUITE_UNINSTALLER = SUITE_DIR / "Desinstalador Suite" / "Desinstalador Suite.exe"
HUB_UNINSTALLER = HUB_DIR / "Desinstalador Hub" / "Desinstalador Hub.exe"

REG_KEYS = {
    "suite": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodSuite",
    "hub": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NeuroMoodHub",
}


user32 = ctypes.windll.user32
try:
    user32.SetProcessDPIAware()
except Exception:
    pass

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


@dataclass
class RunContext:
    out_dir: Path
    appdata_dir: Path
    env: dict[str, str]
    keep_install: bool = False


def log(message: str) -> None:
    print(message, flush=True)


def require_file(path: Path, hint: str = "") -> None:
    if path.exists():
        return
    extra = f"\n{hint}" if hint else ""
    raise SystemExit(f"Missing required file: {path}{extra}")


def safe_rmtree(path: Path, allowed_roots: list[Path]) -> None:
    resolved = path.resolve()
    allowed = [root.resolve() for root in allowed_roots]
    if not any(str(resolved).lower().startswith(str(root).lower()) for root in allowed):
        raise RuntimeError(f"Refusing to delete outside QA roots: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved, ignore_errors=True)


def run_cmd(cmd: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    log(f"RUN {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def build_exes() -> None:
    run_cmd(["cmd", "/c", "BUILD_NEUROMOOD.bat"])


def reg_export(key: str, dest: Path) -> bool:
    result = subprocess.run(
        ["reg", "export", key, str(dest), "/y"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return result.returncode == 0


def reg_delete(key: str) -> None:
    subprocess.run(
        ["reg", "delete", key, "/f"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def reg_import(path: Path) -> None:
    if path.exists():
        subprocess.run(
            ["reg", "import", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )


def backup_registry(out_dir: Path) -> dict[str, bool]:
    backups: dict[str, bool] = {}
    reg_dir = out_dir / "_registry_backup"
    reg_dir.mkdir(parents=True, exist_ok=True)
    for name, key in REG_KEYS.items():
        backups[name] = reg_export(key, reg_dir / f"{name}.reg")
    return backups


def restore_registry(out_dir: Path, existed: dict[str, bool]) -> None:
    reg_dir = out_dir / "_registry_backup"
    for name, key in REG_KEYS.items():
        if existed.get(name):
            reg_import(reg_dir / f"{name}.reg")
        else:
            reg_delete(key)


def window_title(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def enum_windows(title_contains: str, pid: int | None = None) -> list[int]:
    found: list[int] = []
    needle = title_contains.lower()

    def cb(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = window_title(hwnd)
        if not title or needle not in title.lower():
            return True
        if pid is not None:
            proc_id = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
            if proc_id.value != pid:
                return True
        found.append(hwnd)
        return True

    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found


def wait_window(title_contains: str, pid: int | None = None, timeout: float = 45.0,
                required: bool = True) -> int | None:
    end = time.time() + timeout
    while time.time() < end:
        windows = enum_windows(title_contains, pid=pid)
        if windows:
            hwnd = windows[0]
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.2)
            return hwnd
        time.sleep(0.15)
    if required:
        raise RuntimeError(f"Window not found: {title_contains!r}, pid={pid}")
    return None


def rect(hwnd: int) -> RECT:
    r = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r


def click(hwnd: int, x: int, y: int, delay: float = 0.35) -> None:
    r = rect(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SetCursorPos(r.left + x, r.top + y)
    time.sleep(0.05)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.03)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(delay)


def click_next(hwnd: int) -> None:
    r = rect(hwnd)
    click(hwnd, max(20, (r.right - r.left) - 95), max(20, (r.bottom - r.top) - 34))


def click_back(hwnd: int) -> None:
    click(hwnd, 68, 54, delay=0.45)


def click_theme_toggle(hwnd: int) -> None:
    r = rect(hwnd)
    click(hwnd, max(20, (r.right - r.left) - 48), 54, delay=0.7)


def wheel(hwnd: int, x: int, y: int, delta: int) -> None:
    r = rect(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SetCursorPos(r.left + x, r.top + y)
    time.sleep(0.05)
    user32.mouse_event(0x0800, 0, 0, delta, 0)
    time.sleep(0.4)


def capture(hwnd: int, path: Path) -> None:
    image = None
    last_box = None
    for _ in range(25):
        user32.ShowWindow(hwnd, 9)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.12)
        r = rect(hwnd)
        last_box = (r.left, r.top, r.right, r.bottom)
        if (r.right - r.left) <= 20 or (r.bottom - r.top) <= 20:
            time.sleep(0.2)
            continue
        img = ImageGrab.grab(bbox=last_box)
        if img.size[0] > 20 and img.size[1] > 20:
            image = img
            break
        time.sleep(0.2)
    if image is None:
        raise RuntimeError(f"Cannot capture non-empty image for hwnd={hwnd}, bbox={last_box}")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    log(f"CAPTURE {path} {image.size[0]}x{image.size[1]}")


def wait_install_complete(label: str, exe_path: Path, min_internal_files: int = 150,
                          timeout: float = 180.0) -> None:
    end = time.time() + timeout
    stable = 0
    last_count = -1
    while time.time() < end:
        internal = exe_path.parent / "_internal"
        count = sum(1 for _ in internal.rglob("*")) if internal.exists() else 0
        if exe_path.exists() and count >= min_internal_files and count == last_count:
            stable += 1
        else:
            stable = 0
        last_count = count
        if stable >= 4:
            log(f"WAIT_INSTALL {label}: ok, internal_files={count}")
            return
        time.sleep(1.0)
    raise RuntimeError(f"Install did not stabilize: {label}, files={last_count}")


def launch(exe: Path, ctx: RunContext) -> subprocess.Popen:
    require_file(exe)
    return subprocess.Popen([str(exe)], cwd=str(exe.parent), env=ctx.env)


def stop_process(proc: subprocess.Popen) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=8)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def install_suite(ctx: RunContext) -> None:
    log("== Suite installer ==")
    proc = launch(SUITE_INSTALLER, ctx)
    hwnd = wait_window("NeuroMood Suite", pid=proc.pid)
    base = ctx.out_dir / "installers" / "suite"

    capture(hwnd, base / "00_welcome.png")
    click_next(hwnd)
    hwnd = wait_window("NeuroMood Suite", pid=proc.pid)
    capture(hwnd, base / "01_account_prefilled.png")
    click_next(hwnd)
    hwnd = wait_window("NeuroMood Suite", pid=proc.pid)
    capture(hwnd, base / "02_install_ready.png")
    click_next(hwnd)
    time.sleep(1.0)
    hwnd = wait_window("NeuroMood Suite", pid=proc.pid)
    capture(hwnd, base / "03_install_progress.png")

    wait_install_complete("suite", SUITE_EXE, min_internal_files=500)
    time.sleep(8.0)
    hwnd = wait_window("NeuroMood Suite", pid=proc.pid)
    capture(hwnd, base / "04_finished.png")
    click_next(hwnd)
    time.sleep(0.8)
    hwnd = wait_window("NeuroMood Suite", pid=proc.pid, timeout=3, required=False)
    if hwnd:
        capture(hwnd, base / "05_final_or_closing.png")
        click_next(hwnd)
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.terminate()
    require_file(SUITE_EXE, "Suite install did not create the expected EXE.")


def install_hub(ctx: RunContext) -> None:
    log("== Hub installer ==")
    proc = launch(HUB_INSTALLER, ctx)
    hwnd = wait_window("NeuroMood Hub", pid=proc.pid)
    base = ctx.out_dir / "installers" / "hub"

    capture(hwnd, base / "00_welcome.png")
    click_next(hwnd)
    hwnd = wait_window("NeuroMood Hub", pid=proc.pid)
    capture(hwnd, base / "01_path_prefilled.png")
    click_next(hwnd)
    hwnd = wait_window("NeuroMood Hub", pid=proc.pid)
    capture(hwnd, base / "02_supabase_prefilled.png")
    click_next(hwnd)
    hwnd = wait_window("NeuroMood Hub", pid=proc.pid)
    capture(hwnd, base / "03_install_ready.png")
    click_next(hwnd)
    time.sleep(1.0)
    hwnd = wait_window("NeuroMood Hub", pid=proc.pid)
    capture(hwnd, base / "04_install_progress.png")

    wait_install_complete("hub", HUB_EXE, min_internal_files=500)
    time.sleep(8.0)
    hwnd = wait_window("NeuroMood Hub", pid=proc.pid)
    capture(hwnd, base / "05_install_done.png")
    click_next(hwnd)
    time.sleep(0.8)
    hwnd = wait_window("NeuroMood Hub", pid=proc.pid)
    capture(hwnd, base / "06_final.png")
    click_next(hwnd)
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.terminate()
    require_file(HUB_EXE, "Hub install did not create the expected EXE.")


SUITE_CARD_CLICKS = [
    ("animo", 165, 220),
    ("respiracion", 450, 220),
    ("tcc", 725, 220),
    ("rutina", 165, 395),
    ("actividades", 450, 395),
    ("timer", 725, 395),
    ("avisos", 450, 525),
]


def open_suite_for_theme(ctx: RunContext, theme: str) -> tuple[subprocess.Popen, int]:
    proc = launch(SUITE_EXE, ctx)
    hwnd = wait_window("NeuroMood Suite", pid=proc.pid, timeout=60)
    time.sleep(2.0)
    if theme == "light":
        click_theme_toggle(hwnd)
        hwnd = wait_window("NeuroMood Suite", pid=proc.pid, timeout=10)
        time.sleep(0.8)
    return proc, hwnd


def capture_suite_home(theme: str, ctx: RunContext) -> None:
    proc, hwnd = open_suite_for_theme(ctx, theme)
    try:
        capture(hwnd, ctx.out_dir / "patient_app" / theme / "00_home.png")
    finally:
        stop_process(proc)


def capture_suite_module(theme: str, name: str, x: int, y: int,
                         ctx: RunContext) -> None:
    # Start a clean app instance for every module. This prevents the QA run from
    # getting stuck if a module header/back button changes visually.
    proc, hwnd = open_suite_for_theme(ctx, theme)
    try:
        click(hwnd, x, y, delay=1.0)
        hwnd = wait_window("NeuroMood Suite", pid=proc.pid, timeout=10)
        capture(hwnd, ctx.out_dir / "patient_app" / theme / f"module_{name}.png")
    finally:
        stop_process(proc)


def capture_suite_theme(theme: str, ctx: RunContext) -> None:
    capture_suite_home(theme, ctx)
    for name, x, y in SUITE_CARD_CLICKS:
        capture_suite_module(theme, name, x, y, ctx)


def capture_suite_app(ctx: RunContext) -> None:
    log("== Patient app ==")
    capture_suite_theme("dark", ctx)
    capture_suite_theme("light", ctx)


HUB_NAV = [
    ("pacientes", 95, 100),
    ("dashboard", 95, 135),
    ("ia", 95, 170),
    ("config", 95, 205),
]

HUB_DETAIL_TABS = [
    ("registros", 230, 335),
    ("asignar", 300, 335),
    ("banco", 365, 335),
    ("ia", 425, 335),
]


def capture_hub_main_views(hwnd: int, theme: str, ctx: RunContext) -> None:
    base = ctx.out_dir / "hub_pro" / theme
    for name, x, y in HUB_NAV:
        click(hwnd, x, y, delay=0.8)
        hwnd = wait_window("NeuroMood Hub", timeout=8)
        capture(hwnd, base / f"view_{name}.png")


def capture_hub_detail(hwnd: int, theme: str, ctx: RunContext) -> None:
    base = ctx.out_dir / "hub_pro" / theme / "patient_detail"
    click(hwnd, 95, 100, delay=0.7)
    hwnd = wait_window("NeuroMood Hub", timeout=8)
    click(hwnd, 350, 165, delay=1.0)
    hwnd = wait_window("NeuroMood Hub", timeout=10)
    capture(hwnd, base / "00_detail_default.png")
    for name, x, y in HUB_DETAIL_TABS:
        click(hwnd, x, y, delay=0.7)
        hwnd = wait_window("NeuroMood Hub", timeout=8)
        capture(hwnd, base / f"tab_{name}.png")
    click_back(hwnd)
    wait_window("NeuroMood Hub", timeout=8)


def capture_hub_app(ctx: RunContext) -> None:
    log("== NeuroMood Hub app ==")
    proc = launch(HUB_EXE, ctx)
    hwnd = wait_window("NeuroMood Hub", pid=proc.pid, timeout=60)
    time.sleep(2.0)

    capture_hub_main_views(hwnd, "dark", ctx)
    capture_hub_detail(hwnd, "dark", ctx)

    hwnd = wait_window("NeuroMood Hub", pid=proc.pid)
    click_theme_toggle(hwnd)
    hwnd = wait_window("NeuroMood Hub", pid=proc.pid)
    time.sleep(0.8)

    capture_hub_main_views(hwnd, "light", ctx)
    capture_hub_detail(hwnd, "light", ctx)

    try:
        proc.terminate()
        proc.wait(timeout=8)
    except Exception:
        proc.kill()


def capture_uninstaller(exe: Path, title_contains: str, name: str, ctx: RunContext) -> None:
    log(f"== Uninstaller {name} ==")
    require_file(exe)
    proc = subprocess.Popen([str(exe)], cwd=str(exe.parent), env=ctx.env)

    # The uninstaller may relaunch from TEMP, so search by title without PID.
    hwnd = wait_window(title_contains, timeout=60)
    base = ctx.out_dir / "uninstallers" / name
    time.sleep(1.0)
    capture(hwnd, base / "00_confirm.png")
    click_next(hwnd)
    time.sleep(0.8)

    for idx in range(1, 16):
        hwnd = wait_window(title_contains, timeout=3, required=False)
        if not hwnd:
            break
        capture(hwnd, base / f"{idx:02d}_progress_or_done.png")
        time.sleep(2.0)

    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


def cleanup_after_run(ctx: RunContext, registry_existed: dict[str, bool]) -> None:
    log("== Cleanup ==")
    restore_registry(ctx.out_dir, registry_existed)

    for link in [
        Path.home() / "Desktop" / "NeuroMood Suite.lnk",
        Path.home() / "Desktop" / "NeuroMood Hub.lnk",
    ]:
        try:
            if link.exists():
                link.unlink()
        except Exception as exc:
            log(f"WARN shortcut cleanup failed: {link}: {exc}")

    temp = Path(os.environ.get("TEMP", str(Path.home())))
    for pattern in ("_nm_desinstalar_*", "_nm_pro_desinstalar_*"):
        for path in temp.glob(pattern):
            safe_rmtree(path, [temp])

    if not ctx.keep_install:
        safe_rmtree(QA_ROOT, [QA_ROOT])
        safe_rmtree(ctx.appdata_dir, [ctx.out_dir])


def prepare_context(args: argparse.Namespace) -> RunContext:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out).resolve() if args.out else DEFAULT_OUT_ROOT / stamp
    appdata_dir = out_dir / "_appdata"

    if not args.no_clean_start:
        safe_rmtree(QA_ROOT, [QA_ROOT])
        safe_rmtree(appdata_dir, [out_dir])

    out_dir.mkdir(parents=True, exist_ok=True)
    appdata_dir.mkdir(parents=True, exist_ok=True)
    QA_ROOT.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update({
        "NM_VISUAL_QA": "1",
        "NM_TEST_FORCE_CLOSE": "1",
        "NM_QA_SUITE_INSTALL_DIR": str(SUITE_DIR),
        "NM_QA_HUB_INSTALL_DIR": str(HUB_DIR),
        "APPDATA": str(appdata_dir),
    })
    if args.patient_name:
        env["NM_VISUAL_QA_NAME"] = args.patient_name

    return RunContext(out_dir=out_dir, appdata_dir=appdata_dir, env=env,
                      keep_install=args.keep_install)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run NeuroMood compiled EXEs in visual QA mode and capture screenshots."
    )
    parser.add_argument("--build", action="store_true",
                        help="Rebuild Suite, Hub, installers and uninstallers before running.")
    parser.add_argument("--out", default="",
                        help="Output folder. Defaults to _test_screens/qa_exe_capture/<timestamp>.")
    parser.add_argument("--keep-install", action="store_true",
                        help="Do not remove the QA install folder at the end.")
    parser.add_argument("--no-clean-start", action="store_true",
                        help="Do not remove previous QA folders before starting.")
    parser.add_argument("--patient-name", default="juan cruz",
                        help="Name used by NM_VISUAL_QA in the patient app.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ctx = prepare_context(args)

    if args.build:
        build_exes()

    require_file(SUITE_INSTALLER, "Run BUILD_NEUROMOOD.bat or pass --build.")
    require_file(HUB_INSTALLER, "Run BUILD_NEUROMOOD.bat or pass --build.")

    registry_existed = backup_registry(ctx.out_dir)

    try:
        install_suite(ctx)
        install_hub(ctx)
        capture_suite_app(ctx)
        capture_hub_app(ctx)
        capture_uninstaller(SUITE_UNINSTALLER, "NeuroMood Suite", "suite", ctx)
        capture_uninstaller(HUB_UNINSTALLER, "NeuroMood Hub", "hub", ctx)
    finally:
        cleanup_after_run(ctx, registry_existed)

    log(f"DONE screenshots: {ctx.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
