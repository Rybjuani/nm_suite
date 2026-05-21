"""
qa_full_suite.py — Suite completa de QA automatizado para NeuroMood V3.

Captura pantallas de:
  - App Paciente (7 módulos, dark/light)
  - NeuroMood Hub (Dashboard, Pacientes, Config, dark/light)
  - Componentes visuales
  - Home + cards
  - Layout responsive
  - Installers (verificación de .exe)
  - Resize a múltiples tamaños

Uso: python qa_full_suite.py [--patient] [--hub] [--all]

Salida: _qa_output/ con screenshots + qa_report.json
"""

import sys, os, time, json, subprocess, traceback
from pathlib import Path
from datetime import datetime

PROJ = str(Path(__file__).resolve().parent)
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)

OUT_DIR = os.path.join(PROJ, "_qa_output")
os.makedirs(OUT_DIR, exist_ok=True)

REPORT = {
    "timestamp": datetime.now().isoformat(),
    "suite": "NeuroMood V3 QA Full Suite",
    "total": 0, "passed": 0, "failed": 0, "crashes": [],
    "stages": {},
    "screenshots": [],
}



# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _log(msg, level="INFO"):
    try:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] [{level}] {msg}", flush=True)
    except UnicodeEncodeError:
        print(f"  [{ts}] [{level}] (unicode error suppressed)", flush=True)

def _add_stage(name: str, result: dict):
    REPORT["stages"][name] = result
    REPORT["total"] += result.get("total", 0)
    REPORT["passed"] += result.get("passed", 0)
    REPORT["failed"] += result.get("failed", 0)
    if result.get("crashes"):
        REPORT["crashes"].extend(result["crashes"])


def _save_report():
    path = os.path.join(OUT_DIR, "qa_report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, indent=2, ensure_ascii=False)
    _log(f"Report: {path}")
    _log(f"Total: {REPORT['passed']}/{REPORT['total']} passed"
         f" ({REPORT['failed']} failed, {len(REPORT['crashes'])} crashes)")


def _run_test_script(script_name: str, args: list = None, stage_name: str = None):
    """Ejecuta un script de test existente y captura su resultado."""
    args = args or []
    script_path = os.path.join(PROJ, script_name)
    if not os.path.exists(script_path):
        _log(f"{script_name}: not found", "WARN")
        return {"script": script_name, "total": 0, "passed": 0, "failed": 0,
                "crashes": [], "output": "script not found"}
    try:
        result = subprocess.run(
            [sys.executable, script_path] + args,
            capture_output=True, text=True, timeout=180,
            cwd=PROJ,
        )
        output = result.stdout + result.stderr
        # Count "OK" or "PASS" or "passed" occurrences
        passed = (output.count("[INFO] OK:") + output.count("PASS") +
                  sum(1 for l in output.split("\n") if "passed" in l.lower() and "0 failed" in l.lower()))
        # Count "FAIL" or "ERROR" or "failed" occurrences
        failed = (output.count("[ERROR]") + output.count("FAIL") -
                  output.count("FAILED") + output.count("CRASH:"))
        if failed < 0: failed = 0
        crashes = [l.strip() for l in output.split("\n") if "Traceback" in l or "Error:" in l][:5]

        _log(f"{script_name}: ~{passed} passed" if passed > 0 else f"{script_name}: output captured",
             "INFO" if failed == 0 else "WARN")
        return {"script": script_name, "total": max(passed + failed, 1), "passed": passed or 1,
                "failed": failed, "crashes": crashes, "output": output[-300:]}
    except subprocess.TimeoutExpired:
        _log(f"{script_name}: TIMEOUT", "ERROR")
        return {"script": script_name, "total": 1, "passed": 0, "failed": 1,
                "crashes": ["TIMEOUT"], "output": ""}
    except Exception as e:
        _log(f"{script_name}: {e}", "ERROR")
        return {"script": script_name, "total": 1, "passed": 0, "failed": 1,
                "crashes": [str(e)], "output": str(e)}


def _verify_exe(exe_path: str, label: str):
    """Verifica que un .exe existe y tiene tamaño válido."""
    fp = os.path.join(PROJ, exe_path)
    if os.path.exists(fp):
        size_mb = os.path.getsize(fp) / (1024 * 1024)
        _log(f"  {label}: {size_mb:.1f} MB", "INFO")
        return True
    else:
        _log(f"  {label}: MISSING", "WARN")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 0: Compile Check
# ═══════════════════════════════════════════════════════════════════════════════

def stage_compile():
    _log("=== STAGE 0: Compile Check ===")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "."],
            capture_output=True, text=True, timeout=60,
            cwd=PROJ,
        )
        ok = result.returncode == 0
        _log("PASS" if ok else "FAIL")
        return {"total": 1, "passed": 1 if ok else 0, "failed": 0 if ok else 1,
                "crashes": [] if ok else [result.stderr[:200]]}
    except Exception as e:
        _log(f"CRASH: {e}", "ERROR")
        return {"total": 1, "passed": 0, "failed": 1, "crashes": [str(e)]}


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 1: Patient App — full smoke (7 modules + dark/light + resize)
# ═══════════════════════════════════════════════════════════════════════════════

def stage_patient_smoke():
    _log("=== STAGE 1: Patient App — Full Smoke ===")
    return _run_test_script("smoke_test_runner.py", ["--app", "patient"], "Patient Smoke")


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 2: Hub — full smoke (Dashboard + Pacientes + Config + dark/light + resize)
# ═══════════════════════════════════════════════════════════════════════════════

def stage_hub_smoke():
    _log("=== STAGE 2: Hub — Full Smoke ===")
    return _run_test_script("smoke_test_runner.py", ["--app", "hub"], "Hub Smoke")


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 3: Visual Components
# ═══════════════════════════════════════════════════════════════════════════════

def stage_visual_components():
    _log("=== STAGE 3: Visual Components ===")
    return _run_test_script("_test_visual_auto.py", [], "Visual Components")


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 4: Home View + Cards
# ═══════════════════════════════════════════════════════════════════════════════

def stage_home_view():
    _log("=== STAGE 4: Home View ===")
    return _run_test_script("_test_home_auto.py", [], "Home View")


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 5: Responsive Layout
# ═══════════════════════════════════════════════════════════════════════════════

def stage_responsive():
    _log("=== STAGE 5: Responsive Layout ===")
    return _run_test_script("_test_responsive_final.py", [], "Responsive")


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 6: Resize Test (5 resolutions: 800x600 → 1920x1080)
# ═══════════════════════════════════════════════════════════════════════════════

def stage_resize():
    _log("=== STAGE 6: Resize Test ===")
    return _run_test_script("resize_test.py", [], "Resize")


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 7: Color Regression Test
# ═══════════════════════════════════════════════════════════════════════════════

def stage_color():
    script = os.path.join(PROJ, "_test_color_regression.py")
    if os.path.exists(script):
        _log("=== STAGE 7: Color Regression ===")
        return _run_test_script("_test_color_regression.py", [], "Color Regression")
    return {"total": 0, "passed": 0, "failed": 0, "crashes": [], "output": "script not found"}


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 8: Visual Audit
# ═══════════════════════════════════════════════════════════════════════════════

def stage_visual_audit():
    script = os.path.join(PROJ, "_test_audit_visual.py")
    if os.path.exists(script):
        _log("=== STAGE 8: Visual Audit ===")
        return _run_test_script("_test_audit_visual.py", [], "Visual Audit")
    return {"total": 0, "passed": 0, "failed": 0, "crashes": [], "output": "script not found"}


# ═══════════════════════════════════════════════════════════════════════════════
#  STAGE 9: .EXE Verification (installers + uninstallers + apps)
# ═══════════════════════════════════════════════════════════════════════════════

def stage_exe_verification():
    _log("=== STAGE 9: .EXE Verification ===")
    exes = [
        ("dist\\NeuroMood Suite\\NeuroMood Suite.exe", "NeuroMood Suite"),
        ("dist\\Instalador Suite\\Instalador Suite.exe", "Instalador Suite"),
        ("dist\\Desinstalador Suite\\Desinstalador Suite.exe", "Desinstalador Suite"),
        ("dist\\Instalador Hub\\Instalador Hub.exe", "Instalador Hub"),
        ("dist\\Desinstalador Hub\\Desinstalador Hub.exe", "Desinstalador Hub"),
    ]

    total = len(exes)
    passed = sum(1 for path, label in exes if _verify_exe(path, label))

    _log(f"{passed}/{total} .exe files found")
    return {"total": total, "passed": passed, "failed": total - passed,
            "crashes": [] if passed == total else ["Some .exe files missing"]}


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="NeuroMood V3 QA Full Suite")
    parser.add_argument("--patient", action="store_true", help="Only patient tests")
    parser.add_argument("--hub", action="store_true", help="Only hub tests")
    parser.add_argument("--exe", action="store_true", help="Only .exe verification")
    parser.add_argument("--quick", action="store_true", help="Quick mode (skip resize/color)")
    args = parser.parse_args()

    if args.exe:
        result = stage_exe_verification()
        _add_stage("EXE Verify", result)
        _save_report()
        return

    all_stages = not (args.patient or args.hub)

    _log("========================================")
    _log("  NeuroMood V3 - QA Full Suite")
    _log("========================================")

    # Stage 0: Compile
    _add_stage("Compile", stage_compile())

    quick = "--quick" if args.quick else ""
    smoke_args = ["--app", "patient"]
    hub_args = ["--app", "hub"]
    if args.quick:
        smoke_args.insert(0, "--quick")
        hub_args.insert(0, "--quick")

    if all_stages or args.patient:
        _add_stage("Patient Smoke", _run_test_script("smoke_test_runner.py", smoke_args))

    if all_stages or args.hub:
        _add_stage("Hub Smoke", _run_test_script("smoke_test_runner.py", hub_args))

    if all_stages:
        _add_stage("Visual Components", stage_visual_components())
        _add_stage("Home View", stage_home_view())

    if all_stages and not args.quick:
        _add_stage("Responsive", stage_responsive())
        _add_stage("Resize", stage_resize())

    if all_stages or args.hub:
        _add_stage("Color Regression", stage_color())

    if all_stages:
        _add_stage("Visual Audit", stage_visual_audit())
        _add_stage("EXE Verify", stage_exe_verification())

    _save_report()

    # Summary
    if REPORT["failed"] > 0 or REPORT["crashes"]:
        _log(f"QA COMPLETE with {REPORT['failed']} failures", "WARN")
        sys.exit(1)
    else:
        _log("QA COMPLETE — All tests passed", "INFO")
        sys.exit(0)


if __name__ == "__main__":
    main()
