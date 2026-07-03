"""Contratos de orquestación del harness visual owner-directed.

Cubre los bugs de orquestación encontrados el 2026-07-03:

1. ``close_visual_key --preflight`` capturaba en ``qa/_captures_v8`` del
   working tree y luego su propio ``ensure_clean_for_closure`` abortaba con
   ``dirty_working_tree`` (el preflight se auto-ensuciaba).
2. ``run_visual_family.ps1`` corría UN ``vas_gate.py`` al final, pero
   ``capture_v8`` reescribe el sidecar por invocación → con N keys sólo la
   última quedaba gateada ("all 1 entries" con un set de 2).
3. ``run_visual_family.ps1`` / ``run_visual_item.ps1`` borraban el sidecar
   incluso con ``-SkipCapture`` (ninguna captura lo regenera → gate espurio).

Los tests de los .ps1 son contratos estructurales sobre el texto del script:
el e2e completo por modo es costo de captura real (ver
``WORKER_VISUAL_QA_FLOW.md`` §2.2); el modo family se ejercita e2e en cada
corrida real de reparación.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from qa import close_visual_key as cvk
from qa import target_scope as ts

ROOT = Path(__file__).resolve().parents[1]
FAMILY_PS1 = (ROOT / "qa" / "run_visual_family.ps1").read_text(encoding="utf-8")
ITEM_PS1 = (ROOT / "qa" / "run_visual_item.ps1").read_text(encoding="utf-8")


# ─── close_visual_key --preflight: aislamiento del working tree ─────────────


class _PreflightRecorder:
    def __init__(self):
        self.capture_dir: Path | None = None
        self.report_dir: Path | None = None
        self.sidecar: Path | None = None
        self.vas_key: str | None = None

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cvk, "run_anti_fraud", lambda repo_root: None)

        def fake_capture(repo_root, parsed, capture_dir):
            self.capture_dir = Path(capture_dir)

        def fake_locate(capture_dir, key):
            sidecar = Path(capture_dir).parent / "_visual_auditor_spec" / "introspection.json"
            return (
                Path(capture_dir) / "fake.png",
                Path(capture_dir) / "CAPTURE_MANIFEST.json",
                sidecar,
            )

        def fake_comparator(repo_root, parsed, capture_dir, report_dir):
            self.report_dir = Path(report_dir)
            return Path(report_dir) / "LAYERED_VISUAL_REPORT.json"

        def fake_vas(repo_root, key, sidecar_path):
            self.sidecar = Path(sidecar_path)
            self.vas_key = key

        monkeypatch.setattr(cvk, "run_capture", fake_capture)
        monkeypatch.setattr(cvk, "locate_capture_artifacts", fake_locate)
        monkeypatch.setattr(cvk, "run_comparator", fake_comparator)
        monkeypatch.setattr(cvk, "run_vas", fake_vas)


def test_preflight_default_runs_outside_scoped_repo_paths(monkeypatch, tmp_path):
    """Sin dirs explícitos, el preflight NO puede escribir bajo el repo:
    capturar en qa/_captures_v8 ensucia rutas scoped y el cierre posterior
    aborta con dirty_working_tree (bug 2026-07-03)."""
    rec = _PreflightRecorder()
    rec.install(monkeypatch)

    cvk.run_preflight(repo_root=tmp_path, key="suite:dbt-library@light")

    assert rec.capture_dir is not None
    resolved = rec.capture_dir.resolve()
    assert not str(resolved).startswith(str(tmp_path.resolve())), (
        "el preflight por defecto capturó dentro del repo — vuelve el "
        f"self-dirty dirty_working_tree: {resolved}"
    )
    assert rec.report_dir is not None
    assert not str(rec.report_dir.resolve()).startswith(str(tmp_path.resolve()))
    # El sidecar se resuelve relativo al padre del capture dir (contrato de
    # capture_v8), así que también debe quedar fuera del repo.
    assert rec.sidecar is not None
    assert not str(rec.sidecar.resolve()).startswith(str(tmp_path.resolve()))
    assert rec.vas_key == "suite:dbt-library@light"
    # El directorio temporal se limpia al salir del contexto.
    assert not rec.capture_dir.exists()


def test_preflight_respects_explicit_dirs(monkeypatch, tmp_path):
    """Con dirs explícitos (flags ocultos de test) el preflight los respeta."""
    rec = _PreflightRecorder()
    rec.install(monkeypatch)
    cap = tmp_path / "caps"
    rep = tmp_path / "rep"

    cvk.run_preflight(
        repo_root=tmp_path,
        key="suite:dbt-library@dark",
        capture_dir=cap,
        report_dir=rep,
    )

    assert rec.capture_dir == cap
    assert rec.report_dir == rep
    assert rep.exists()


# ─── run_visual_family.ps1: contratos estructurales ─────────────────────────


def _foreach_capture_loop(script: str) -> str:
    """Cuerpo del loop principal de capturas (desde su apertura hasta el
    bloque del keysFile)."""
    start = script.index("foreach ($row in $rows)")
    end = script.index("$keysFile = New-TemporaryFile")
    return script[start:end]


def test_family_runner_gates_vas_per_key_inside_capture_loop():
    """capture_v8 reescribe el sidecar por invocación: el gate VAS tiene que
    correr POR KEY dentro del loop, no una vez al final (bug: con N keys sólo
    la última quedaba validada)."""
    loop = _foreach_capture_loop(FAMILY_PS1)
    assert re.search(r"vas_gate\.py\s+--key", loop), (
        "run_visual_family.ps1 perdió el vas_gate.py --key por key dentro "
        "del loop de capturas"
    )


def test_family_runner_has_no_final_bare_vas_gate():
    """Un vas_gate.py sin --key/--sidecar al final sólo valida la última key
    capturada — da falsa cobertura para sets multi-key."""
    tail = FAMILY_PS1[FAMILY_PS1.index("$keysFile = New-TemporaryFile"):]
    for match in re.finditer(r"vas_gate\.py([^\r\n]*)", tail):
        args = match.group(1)
        assert "--key" in args or "--sidecar" in args, (
            f"vas_gate.py sin filtro por key fuera del loop: '{args.strip()}'"
        )


def test_family_runner_archives_per_key_introspection():
    """El sidecar vivo retiene sólo la última key; el runner debe archivar el
    de cada key para que §2.3 pueda auditarse por key."""
    assert "introspection" in FAMILY_PS1
    assert re.search(r"Copy-Item\s+\.\\qa\\_visual_auditor_spec\\introspection\.json", FAMILY_PS1)


@pytest.mark.parametrize(
    ("script", "name"),
    [(FAMILY_PS1, "run_visual_family.ps1"), (ITEM_PS1, "run_visual_item.ps1")],
)
def test_runners_do_not_delete_sidecar_when_skipping_capture(script, name):
    """Con -SkipCapture nada regenera el sidecar: borrarlo garantiza un fallo
    espurio (o una validación vacía) del gate VAS."""
    for match in re.finditer(
        r"Remove-Item\s+\.\\qa\\_visual_auditor_spec\\introspection\.json", script
    ):
        prefix = script[: match.start()]
        guard = prefix.rfind("if (-not $SkipCapture)")
        assert guard != -1, f"{name}: Remove-Item del sidecar sin guard -SkipCapture"
        # El guard tiene que ser el bloque abierto más cercano (sin un cierre
        # completo de bloque entre medio a nivel de columna 0/1).
        between = prefix[guard:]
        assert between.count("{") > between.count("}"), (
            f"{name}: el Remove-Item del sidecar quedó fuera del bloque "
            "-not $SkipCapture"
        )


def test_item_runner_gates_vas_with_key_filter():
    assert re.search(r"vas_gate\.py\s+--key", ITEM_PS1)


# ─── target_scope CLI: todos los modos owner-directed vía main() ────────────

CLI_HANDOFF = """## Checklist

### Family A (2)

- [ ] `suite:open-a1@light` - severity=high; changed=0.30
- [ ] `suite:open-a2@light` - severity=medium; changed=0.15

### Family B (1)

- [ ] `hub:open-b1@dark` - severity=medium; changed=0.08
"""


@pytest.fixture()
def cli_handoff(tmp_path):
    path = tmp_path / "HANDOFF.md"
    path.write_text(CLI_HANDOFF, encoding="utf-8")
    return path


def _run_cli(capsys, *argv: str) -> list[str]:
    rc = ts.main(list(argv))
    assert rc == 0, f"target_scope CLI falló para {argv}"
    out = capsys.readouterr().out
    return [line for line in out.splitlines() if line.strip()]


def test_cli_next_key(cli_handoff, capsys):
    lines = _run_cli(capsys, "--mode", "next-key", "--handoff", str(cli_handoff))
    assert lines == ["suite:open-a1@light"]


def test_cli_first_n_and_batch_agree(cli_handoff, capsys):
    first = _run_cli(capsys, "--mode", "first-n", "--n", "2", "--handoff", str(cli_handoff))
    batch = _run_cli(capsys, "--mode", "batch", "--n", "2", "--handoff", str(cli_handoff))
    assert first == batch == ["suite:open-a1@light", "suite:open-a2@light"]


def test_cli_family_plan_rows_feed_family_runner(cli_handoff, capsys):
    """El contrato --plan es la interfaz con run_visual_family.ps1: filas
    app,view,theme,key parseables por el loop del runner."""
    rows = _run_cli(capsys, "--mode", "family", "--plan", "--handoff", str(cli_handoff))
    assert rows == [
        "suite,open-a1,light,suite:open-a1@light",
        "suite,open-a2,light,suite:open-a2@light",
    ]
    for row in rows:
        parts = row.split(",")
        assert len(parts) == 4
        assert parts[3] == f"{parts[0]}:{parts[1]}@{parts[2]}"


def test_cli_all_open_keys(cli_handoff, capsys):
    lines = _run_cli(capsys, "--mode", "all-open-keys", "--handoff", str(cli_handoff))
    assert lines == ["suite:open-a1@light", "suite:open-a2@light", "hub:open-b1@dark"]


def test_cli_explicit_list(cli_handoff, capsys):
    lines = _run_cli(
        capsys,
        "--mode",
        "explicit-list",
        "--keys",
        "hub:open-b1@dark, suite:open-a1@light",
        "--handoff",
        str(cli_handoff),
    )
    assert lines == ["hub:open-b1@dark", "suite:open-a1@light"]


def test_cli_explicit_list_rejects_unknown_key(cli_handoff, capsys):
    rc = ts.main(
        ["--mode", "explicit-list", "--keys", "suite:nope@light", "--handoff", str(cli_handoff)]
    )
    assert rc == 1
    assert "keys_not_open_or_unknown" in capsys.readouterr().err


# ─── capture_v8: resolución de views de diálogo a receta productora ─────────


def test_capture_v8_resolves_dialog_view_to_producing_recipe(tmp_path):
    """`--view` con el view canónico de un diálogo indexado (producido DENTRO
    de otra receta, ej. `detalle-resumen-ia-0` ← receta `detalle-resumen-ia`)
    debe resolver a la receta productora. Los flujos per-key (runners, close,
    replay) invocan con el view de la KEY canónica — sin el fallback ninguna
    key de diálogo podía capturarse per-key (bug 2026-07-03)."""
    proc = subprocess.run(
        [
            sys.executable,
            "qa/capture_v8.py",
            "--app",
            "hub",
            "--view",
            "detalle-resumen-ia-0",
            "--theme",
            "light",
            "--no-clean",
            "--out-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    assert (tmp_path / "hub-detalle-resumen-ia-0-light-960x600.png").exists(), (
        "la receta productora no generó el PNG con el nombre canónico de la key"
    )
