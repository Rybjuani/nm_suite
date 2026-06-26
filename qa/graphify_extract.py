#!/usr/bin/env python3
"""Graphify code-graph generator — lightweight Python implementation.

Extracts a dependency graph from Python source files, producing a JSON file
that agents can consult to find which files import/reference a given symbol
without reading every file.

Output format (compatible with the graphify concept from PoC 1)::

    {
      "nodes": [{"id": "qa/diff_fidelity.py", "loc": 417, "classes": 3, ...}],
      "edges": [{"from": "qa/diff_fidelity.py", "to": "qa/odiff_runner.py", "type": "import"}],
      "stats": {"nodes": N, "edges": M, "estimated_tokens_saved_pct": X}
    }

Usage::

    .venv\\Scripts\\python.exe qa\\graphify_extract.py qa/ docs/graphify-out/graph.json
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path


def _module_to_path(module: str, base_dir: Path) -> Path | None:
    """Resolve a Python import module name to a file path relative to base_dir."""
    parts = module.split(".")
    # Try as package/__init__.py then as module.py
    for ext in (".py", os.path.join("__init__.py")):
        candidate = base_dir / os.path.join(*parts) if len(parts) > 1 else None
        if candidate:
            p = base_dir.joinpath(*parts).with_suffix("")
            if ext == ".py":
                p = base_dir.joinpath(*parts)
                if p.with_suffix(".py").exists():
                    return p.with_suffix(".py")
            else:
                init = base_dir.joinpath(*parts, "__init__.py")
                if init.exists():
                    return init
    # Simple: module.py
    p = base_dir.joinpath(*parts).with_suffix(".py")
    if p.exists():
        return p
    return None


def extract_graph(root_dir: Path) -> dict:
    """Walk root_dir for .py files and build the import graph."""
    py_files = sorted(root_dir.rglob("*.py"))
    nodes: list[dict] = []
    edges: list[dict] = []

    # Map relative paths for quick lookup
    rel_paths = {}
    for f in py_files:
        try:
            rel = f.relative_to(root_dir.parent)
        except ValueError:
            rel = f
        rel_paths[str(f)] = str(rel).replace("\\", "/")

    for py_file in py_files:
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue

        lines = source.count("\n") + 1
        classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        functions = sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))

        rel_path = rel_paths.get(str(py_file), str(py_file).replace("\\", "/"))
        nodes.append({
            "id": rel_path,
            "loc": lines,
            "classes": classes,
            "functions": functions,
        })

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                target_path = _module_to_path(node.module, root_dir)
                if target_path and target_path != py_file:
                    target_rel = rel_paths.get(str(target_path), str(target_path).replace("\\", "/"))
                    edges.append({
                        "from": rel_path,
                        "to": target_rel,
                        "type": "import",
                        "module": node.module,
                    })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    target_path = _module_to_path(alias.name, root_dir)
                    if target_path and target_path != py_file:
                        target_rel = rel_paths.get(str(target_path), str(target_path).replace("\\", "/"))
                        edges.append({
                            "from": rel_path,
                            "to": target_rel,
                            "type": "import",
                            "module": alias.name,
                        })

    # Estimate token savings: full source vs graph
    full_tokens = sum(n["loc"] * 8 for n in nodes)  # rough: ~8 tokens/line
    graph_tokens = len(json.dumps(nodes)) // 4 + len(json.dumps(edges)) // 4
    savings_pct = round((1 - graph_tokens / max(full_tokens, 1)) * 100, 1) if full_tokens else 0

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "estimated_full_tokens": full_tokens,
            "estimated_graph_tokens": graph_tokens,
            "estimated_tokens_saved_pct": savings_pct,
        },
    }


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python graphify_extract.py <source_dir> <output.json>")
        print("Example: python graphify_extract.py qa/ docs/graphify-out/graph.json")
        return 2
    root = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory")
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)

    graph = extract_graph(root)
    out.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    s = graph["stats"]
    print(f"Graph written to {out}")
    print(f"  Nodes: {s['nodes']}")
    print(f"  Edges: {s['edges']}")
    print(f"  Est. tokens saved: {s['estimated_tokens_saved_pct']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
