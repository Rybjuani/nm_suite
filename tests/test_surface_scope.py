from __future__ import annotations

import subprocess

from qa.surface_scope import (
    GLOBAL_FILE_PATHS,
    GLOBAL_TREE_PATHS,
    SOURCE_SCOPE_SCHEMA,
    SURFACE_SCOPE,
    VISUAL_ROOTS,
    build_source_scope,
    manifest_families,
    manifest_keys,
    mapped_visual_paths,
    source_scope_matches_revision,
    source_scope_stale,
    unmapped_visual_sources,
)


def _tracked_visual_paths() -> set[str]:
    proc = subprocess.run(
        ["git", "ls-files", *VISUAL_ROOTS],
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.replace("\\", "/") for line in proc.stdout.splitlines() if line}


def test_manifest_universe_has_complete_one_to_one_surface_scope():
    keys = manifest_keys()

    assert len(keys) == 116
    assert len(set(keys)) == 116
    assert len(manifest_families()) == 58
    assert set(manifest_families()) == set(SURFACE_SCOPE)


def test_every_declared_scope_path_exists_and_is_tracked():
    tracked = _tracked_visual_paths()
    declared = mapped_visual_paths()

    assert declared <= tracked
    assert all(paths for paths in SURFACE_SCOPE.values())


def test_scope_and_global_dependencies_cover_all_live_visual_sources():
    tracked = _tracked_visual_paths()

    assert len(tracked) == 104
    assert unmapped_visual_sources(tracked) == []


def test_unmapped_visual_source_blocks_new_app_or_hub_modules_only():
    changed = [
        "app/new_visual.py",
        "hub/new_panel.py",
        "shared/new_component.py",
        "assets/new-theme.png",
        "docs/readme.md",
    ]

    assert unmapped_visual_sources(changed) == ["app/new_visual.py", "hub/new_panel.py"]


def test_known_mapped_and_global_paths_are_not_reported():
    changed = [
        "app\\home_qt.py",
        "app/main_qt.py",
        "hub/pacientes_qt.py",
        "shared/components/cards.py",
        "assets/fonts/Inter-Variable.ttf",
    ]

    assert unmapped_visual_sources(changed) == []


def test_build_source_scope_records_git_blobs_and_global_trees():
    scope = build_source_scope("suite:home@light")

    assert scope["schema"] == SOURCE_SCOPE_SCHEMA
    assert scope["key"] == "suite:home@light"
    assert set(scope["surface_files"]) == {"app/home_qt.py"}
    assert set(scope["global_files"]) == set(GLOBAL_FILE_PATHS)
    assert set(scope["global_trees"]) == set(GLOBAL_TREE_PATHS)
    assert source_scope_matches_revision(scope, revision="HEAD") is True


def test_source_scope_staleness_is_exact_and_fail_closed():
    current = build_source_scope("suite:home@dark")
    changed = {
        **current,
        "surface_files": {"app/home_qt.py": "0" * 40},
    }

    assert source_scope_stale(current, current) is False
    assert source_scope_stale(changed, current) is True
    assert source_scope_stale(None, current) is True
