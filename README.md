# NeuroMood / nm_suite

NeuroMood is a Windows desktop mental health and therapy suite built with Python 3.12 and PyQt6.

The project contains two main applications:

- NeuroMood Suite: patient-facing app.
- NeuroMood Hub: professional / therapist app.

## Documentation

This repository keeps the root documentation intentionally short. The three sources of truth live here:

- [AI_PROJECT_CONTEXT.md](./AI_PROJECT_CONTEXT.md) — full technical context, architecture, module map, build rules, UI conventions, Supabase notes, installer behavior, AI-agent instructions, and a summary of the 2026-05 audit and product decisions.
- [AUDITORIA_NEUROMOOD.md](./AUDITORIA_NEUROMOOD.md) — full audit done by code reading (no runtime). 11 parts following the master prompt, product decisions 2026-05-20/21, remote configurability matrix, F0-F9 phased roadmap, and answers to the 7 closing questions. Read this before touching Suite/Hub/DB.
- [PROMPTS_CODEX_IMPLEMENTACION.md](./PROMPTS_CODEX_IMPLEMENTACION.md) — 33 atomic prompts (F0 to F6) ready to copy/paste into Codex. One prompt = one concrete task = one reviewable diff, with allowed/forbidden files, validation, and acceptance criteria.

**Methodology note:** the audit is by reading, not by running. "Implemented in code" does **not** mean "verified at runtime on Windows". Before any clinical pilot, run the QA plan from Part 10 of the audit on real apps.

## Main folders

- `app/` — patient application (NeuroMood Suite).
- `hub/` — professional hub (NeuroMood Hub).
- `shared/` — shared UI, config, database, sync, theme, and utility code.
- `installers/` — installer and uninstaller sources.
- `db/` — Supabase schemas and DB resources.
- `assets/` — runtime images, icons, branding, and fonts.
- `AI_SCRIPTS/` — build, QA, capture, audit, and automation scripts.

## Install dependencies

    pip install -r requirements.txt

## Run in development

Patient app:

    python app/main_qt.py

Professional hub:

    python hub/main_qt.py

## Build executables

    python build_neuromood.py

Or on Windows:

    BUILD_NEUROMOOD.bat

## Secrets

Do not commit `.env`. Use `.env.example` as a template. See section 8 of [AI_PROJECT_CONTEXT.md](./AI_PROJECT_CONTEXT.md) for the full security rules.
