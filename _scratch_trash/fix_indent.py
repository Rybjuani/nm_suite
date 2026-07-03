"""Re-indent the batch-mode code that the patch tool mis-indented.

The analyze_parser block (lines 2698-2715) and batch-mode block (lines 2773-2847)
both have one extra level of indentation. Fix them.
"""
from pathlib import Path
import re

p = Path("qa/visual_auditor_v3.py")
content = p.read_text(encoding="utf-8")

# 1. Fix the analyze_parser argparse block:
#    Old (wrong): 8-space leading lines on add_argument calls inside main()
#    New (right): 4-space leading lines
old1 = """    analyze_parser = sub.add_parser("analyze", help="Analyze surfaces")
        analyze_parser.add_argument("--all", action="store_true", help="Analyze all surfaces")
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

    sub.add_parser("queue", help="Generate prioritized queue")"""

new1 = """    analyze_parser = sub.add_parser("analyze", help="Analyze surfaces")
    analyze_parser.add_argument("--all", action="store_true", help="Analyze all surfaces")
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

    sub.add_parser("queue", help="Generate prioritized queue")"""

assert old1 in content, "analyze_parser block not found"
content = content.replace(old1, new1)

# 2. Fix the batch-mode block: each line is at 16 spaces, needs to be at 8.
#    The block starts after `        results: list[dict] = []` and ends before
#    `        # Save report` (which is correctly indented).
#    Easier: re-do the whole block atomically.

old2 = """        results: list[dict] = []

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
                print(f"[OK] Report saved to {report_path}")"""

new2 = """        results: list[dict] = []

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
        print(f"[OK] Report saved to {report_path}")"""

assert old2 in content, "batch-mode block not found"
content = content.replace(old2, new2)

p.write_text(content, encoding="utf-8")
print("OK -- both blocks re-indented")