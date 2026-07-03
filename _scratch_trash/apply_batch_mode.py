"""Apply batch-mode edits to qa/visual_auditor_v3.py atomically, with EXACT
indentation. Bypasses the patch tool which keeps adding 4 spaces to my new content.
"""
from pathlib import Path

p = Path("qa/visual_auditor_v3.py")
content = p.read_text(encoding="utf-8")

# --- Edit 1: add datetime import ---
old1 = "from dataclasses import asdict, dataclass, field\nfrom pathlib import Path\nfrom typing import Any, Literal\n"
new1 = "from dataclasses import asdict, dataclass, field\nfrom datetime import datetime\nfrom pathlib import Path\nfrom typing import Any, Literal\n"
assert old1 in content, "Edit 1 not found"
assert content.count(old1) == 1
content = content.replace(old1, new1)

# --- Edit 2: add 3 argparse flags on analyze_parser ---
# old has 4 spaces indent on the add_argument lines (correct level inside main())
# new has 4 spaces for the first line, then 8 for body of multi-line args
old2 = """    analyze_parser.add_argument("--all", action="store_true", help="Analyze all surfaces")
    analyze_parser.add_argument("--surface", type=str, help="Analyze one surface")
"""
new2 = """    analyze_parser.add_argument("--all", action="store_true", help="Analyze all surfaces")
    analyze_parser.add_argument("--surface", type=str, help="Analyze one surface")
    analyze_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-surface stdout; only summary line at end.",
    )
    analyze_parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip surfaces already analyzed in .hermes/qa_progress.json (regenerated each run).",
    )
    analyze_parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Append per-surface status to this file. Created if missing.",
    )
"""
assert old2 in content, "Edit 2 not found"
assert content.count(old2) == 1
content = content.replace(old2, new2)

# --- Edit 3: replace the per-surface loop block ---
# old has 8 spaces for body inside `if args.command == "analyze":` block
# new keeps that 8-space level for the outer scaffolding, and inner try/except goes deeper
old3 = """        results: list[dict] = []

        for pairing in pairings:
            print(f"Analyzing {pairing.surface_key}...")
            result = analyze_surface(pairing, _OUT_DIR, manifest_lookup)
            results.append(result)

        # Save report
        report_path = _OUT_DIR / "report.json"
        report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Report saved to {report_path}")
"""
new3 = """        results: list[dict] = []

        # --- Batch mode setup: progress persistence + log file + quiet stdout ---
        progress_path = Path(".hermes") / "qa_progress.json"
        done: set[str] = set()
        if args.resume and progress_path.exists():
            try:
                done = set(json.loads(progress_path.read_text(encoding="utf-8")).get("done", []))
            except Exception:
                done = set()

        log_fp = None
        if args.log_file:
            args.log_file.parent.mkdir(parents=True, exist_ok=True)
            log_fp = open(args.log_file, "a", encoding="utf-8")

        started_at = datetime.utcnow().isoformat()
        if log_fp:
            log_fp.write(
                f"[{started_at}] === analyze started (quiet={args.quiet}, resume={args.resume}, "
                f"surfaces={len(pairings)}) ===\\n"
            )
            log_fp.flush()

        def emit(msg: str) -> None:
            if not args.quiet:
                print(msg)
            if log_fp:
                log_fp.write(f"[{datetime.utcnow().isoformat()}] {msg}\\n")
                log_fp.flush()

        surfaces_to_analyze = [p.surface_key for p in pairings]

        try:
            for pairing in pairings:
                surface_key = pairing.surface_key
                if args.resume and surface_key in done:
                    emit(f"[skip] {surface_key} (already done)")
                    continue
                emit(f"Analyzing {surface_key}...")
                try:
                    result = analyze_surface(pairing, _OUT_DIR, manifest_lookup)
                    results.append(result)
                    if args.resume:
                        done.add(surface_key)
                        # Persist progress immediately so a Ctrl-C doesn't lose it.
                        progress_path.parent.mkdir(parents=True, exist_ok=True)
                        progress_path.write_text(
                            json.dumps(
                                {
                                    "done": sorted(done),
                                    "updated_at": datetime.utcnow().isoformat() + "Z",
                                },
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                    emit(f"[OK] {surface_key}")
                except Exception as e:
                    emit(f"[FAIL] {surface_key}: {e}")
                    if not args.resume:
                        raise
                    # with --resume: log and continue, do not abort the batch
                    continue
        finally:
            if log_fp:
                log_fp.write(
                    f"[{datetime.utcnow().isoformat()}] === analyze finished "
                    f"({len(results)}/{len(surfaces_to_analyze)} completed) ===\\n"
                )
                log_fp.flush()
                log_fp.close()

        # Save report
        report_path = _OUT_DIR / "report.json"
        report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Report saved to {report_path}")
"""
assert old3 in content, "Edit 3 not found"
assert content.count(old3) == 1
content = content.replace(old3, new3)

p.write_text(content, encoding="utf-8")
print("OK -- all 3 edits applied atomically with exact indentation")