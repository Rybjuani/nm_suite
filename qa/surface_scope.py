#!/usr/bin/env python3
"""Source-scope registry and staleness helpers for visual surfaces.

The module is stdlib-only. Git object IDs, rather than working-tree bytes, are
recorded so a closure is tied to the exact committed source tree it measured.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CANONICAL_MANIFEST = Path("qa") / "_mockup_canonical" / "MANIFEST.json"
SOURCE_SCOPE_SCHEMA = "nm_suite.source_scope.v1"
VISUAL_ROOTS = ("app", "hub", "shared", "assets")

# Any change below these directories affects every visual surface. Prefix
# coverage also means newly-added shared/theme assets cannot slip through as an
# unmapped visual source.
GLOBAL_TREE_PATHS = ("shared", "assets")
GLOBAL_FILE_PATHS = (
    "app/__init__.py",
    "app/main_qt.py",
    "app/modules/__init__.py",
    "hub/__init__.py",
    "hub/editors/__init__.py",
    "hub/main_qt.py",
)


def _build_surface_scope() -> dict[str, tuple[str, ...]]:
    scope: dict[str, tuple[str, ...]] = {}

    def register(app: str, views: Iterable[str], *paths: str) -> None:
        normalized_paths = tuple(sorted(set(paths)))
        for view in views:
            key = f"{app}:{view}"
            if key in scope:
                raise RuntimeError(f"duplicate surface scope: {key}")
            scope[key] = normalized_paths

    register("suite", ("home", "home-no-score"), "app/home_qt.py")
    register(
        "suite",
        ("onboarding", "onboarding-error", "recuperar-acceso"),
        "app/onboarding_qt.py",
    )
    register("suite", ("animo",), "app/modules/animo_qt.py")
    register(
        "suite",
        (
            "dbt-library",
            "dbt-now",
            "dbt-practice-check-facts",
            "dbt-practice-dear-man",
            "dbt-practice-fast",
            "dbt-practice-give",
            "dbt-practice-non-judgmental",
            "dbt-practice-observe-describe",
            "dbt-practice-opposite-action",
            "dbt-practice-participate",
            "dbt-practice-please",
            "dbt-practice-problem-solving",
            "dbt-practice-radical-acceptance",
            "dbt-practice-self-soothe",
            "dbt-practice-stop",
            "dbt-practice-tipp",
            "dbt-practice-validation-limits",
            "dbt-practice-wise-mind",
        ),
        "app/modules/dbt_qt.py",
    )
    register(
        "suite",
        ("respiracion", "respiracion-paused", "respiracion-running"),
        "app/modules/respiracion_qt.py",
    )
    register(
        "suite",
        (
            "registro",
            "registro-step1-emotion",
            "registro-step1-emotion-otro",
            "registro-step2-distortions",
            "registro-step3-filled",
            "registro-success",
        ),
        "app/modules/registro_tcc_qt.py",
    )
    register(
        "suite",
        ("rutina", "rutina-add-task", "rutina-all-completed", "rutina-empty"),
        "app/modules/rutina_qt.py",
    )
    register(
        "suite",
        (
            "actividades",
            "actividades-empty",
            "actividades-filtered",
            "actividades-marked-hice",
        ),
        "app/modules/actividades_qt.py",
    )
    register(
        "suite",
        ("timer", "timer-empty", "timer-paused", "timer-running"),
        "app/modules/timer_qt.py",
    )
    register(
        "suite",
        ("avisos", "avisos-empty", "avisos-filter-activos", "avisos-search", "avisos-today"),
        "app/avisos_daemon.py",
        "app/modules/avisos_qt.py",
    )
    register("hub", ("pacientes", "pacientes-empty"), "hub/main_qt.py")
    register("hub", ("textos-globales",), "hub/config_global_texts.py")
    register(
        "hub",
        (
            "detalle",
            "detalle-plan-activacion",
            "detalle-plan-rutina",
            "detalle-plan-timer",
            "detalle-resumen-ia-0",
        ),
        "hub/exportar.py",
        "hub/ia_asistente.py",
        "hub/pacientes_qt.py",
        "hub/plan_terapeutico.py",
    )
    return dict(sorted(scope.items()))


SURFACE_SCOPE = _build_surface_scope()


class SurfaceScopeError(ValueError):
    pass


def normalize_repo_path(value: str | Path) -> str:
    path = str(value).replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return PurePosixPath(path).as_posix().lstrip("/")


def family_key(key: str) -> str:
    if not isinstance(key, str) or "@" not in key or ":" not in key:
        raise SurfaceScopeError(f"invalid visual key: {key!r}")
    family, theme = key.rsplit("@", 1)
    if theme not in {"light", "dark"}:
        raise SurfaceScopeError(f"invalid visual theme: {theme!r}")
    return family


def scope_paths_for_key(key: str) -> tuple[str, ...]:
    family = family_key(key)
    try:
        return SURFACE_SCOPE[family]
    except KeyError as exc:
        raise SurfaceScopeError(f"unmapped visual surface: {key}") from exc


def manifest_key(capture: Mapping[str, Any]) -> str:
    view = capture.get("view")
    theme = capture.get("theme")
    if not isinstance(view, str) or not isinstance(theme, str):
        raise SurfaceScopeError("manifest capture lacks view/theme")
    if view.startswith("suite-"):
        app, surface = "suite", view[len("suite-") :]
    elif view.startswith("hub-"):
        app, surface = "hub", view[len("hub-") :]
    else:
        raise SurfaceScopeError(f"unsupported manifest view: {view!r}")
    if not surface or theme not in {"light", "dark"}:
        raise SurfaceScopeError(f"invalid manifest capture: {view!r}@{theme!r}")
    return f"{app}:{surface}@{theme}"


def load_manifest(repo_root: Path = ROOT) -> dict[str, Any]:
    path = repo_root / CANONICAL_MANIFEST
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SurfaceScopeError(f"invalid canonical manifest: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("captures"), list):
        raise SurfaceScopeError("canonical manifest must contain captures[]")
    return payload


def manifest_keys(repo_root: Path = ROOT) -> tuple[str, ...]:
    keys = [manifest_key(capture) for capture in load_manifest(repo_root)["captures"]]
    if len(keys) != len(set(keys)):
        raise SurfaceScopeError("duplicate key in canonical manifest")
    return tuple(sorted(keys))


def manifest_families(repo_root: Path = ROOT) -> tuple[str, ...]:
    return tuple(sorted({family_key(key) for key in manifest_keys(repo_root)}))


def _git_object_id(repo_root: Path, revision: str, path: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", f"{revision}:{path}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        detail = proc.stderr.strip() or f"missing {revision}:{path}"
        raise SurfaceScopeError(f"cannot resolve git object: {detail}")
    return proc.stdout.strip()


def build_source_scope(
    key: str,
    *,
    repo_root: Path = ROOT,
    revision: str = "HEAD",
) -> dict[str, Any]:
    """Build the committed source provenance for one exact visual key."""

    paths = scope_paths_for_key(key)
    return {
        "schema": SOURCE_SCOPE_SCHEMA,
        "key": key,
        "surface_files": {
            path: _git_object_id(repo_root, revision, path) for path in paths
        },
        "global_files": {
            path: _git_object_id(repo_root, revision, path) for path in GLOBAL_FILE_PATHS
        },
        "global_trees": {
            path: _git_object_id(repo_root, revision, path) for path in GLOBAL_TREE_PATHS
        },
    }


def source_scope_stale(recorded: object, current: object) -> bool:
    """Return True for malformed or changed source provenance."""

    if not isinstance(recorded, Mapping) or not isinstance(current, Mapping):
        return True
    return dict(recorded) != dict(current)


def is_source_scope_stale(
    recorded: object,
    key: str,
    *,
    repo_root: Path = ROOT,
    revision: str = "HEAD",
) -> bool:
    try:
        current = build_source_scope(key, repo_root=repo_root, revision=revision)
    except SurfaceScopeError:
        return True
    return source_scope_stale(recorded, current)


def source_scope_matches_revision(
    recorded: object,
    *,
    repo_root: Path = ROOT,
    revision: str,
) -> bool:
    """Verify every recorded Git object against its historical revision."""

    if not isinstance(recorded, Mapping) or recorded.get("schema") != SOURCE_SCOPE_SCHEMA:
        return False
    for section in ("surface_files", "global_files", "global_trees"):
        values = recorded.get(section)
        if not isinstance(values, Mapping) or not values:
            return False
        for path, expected in values.items():
            if not isinstance(path, str) or not isinstance(expected, str):
                return False
            try:
                actual = _git_object_id(repo_root, revision, normalize_repo_path(path))
            except SurfaceScopeError:
                return False
            if actual != expected:
                return False
    return True


def is_visual_source(path: str | Path) -> bool:
    normalized = normalize_repo_path(path)
    return any(normalized == root or normalized.startswith(f"{root}/") for root in VISUAL_ROOTS)


def _is_globally_mapped(path: str) -> bool:
    if path in GLOBAL_FILE_PATHS:
        return True
    return any(path == root or path.startswith(f"{root}/") for root in GLOBAL_TREE_PATHS)


def mapped_visual_paths() -> set[str]:
    return {path for paths in SURFACE_SCOPE.values() for path in paths} | set(GLOBAL_FILE_PATHS)


def unmapped_visual_sources(changed_paths: Iterable[str | Path]) -> list[str]:
    """Return changed visual paths that no declared scope can account for."""

    mapped = mapped_visual_paths()
    unmapped: set[str] = set()
    for value in changed_paths:
        path = normalize_repo_path(value)
        if not is_visual_source(path):
            continue
        if path not in mapped and not _is_globally_mapped(path):
            unmapped.add(path)
    return sorted(unmapped)
