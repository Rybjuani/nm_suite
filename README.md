# NeuroMood / nm_suite

NeuroMood is a Windows desktop mental health and therapy suite built with Python 3.12 and PyQt6.

The project contains two main applications:

- NeuroMood Suite: patient-facing app.
- NeuroMood Hub: professional / therapist app.

## Documentation

This repository keeps the root documentation intentionally short.

For the full technical context, architecture notes, module map, build rules, UI conventions, Supabase notes, installer behavior, and AI-agent instructions, read:

- [AI_PROJECT_CONTEXT.md](./AI_PROJECT_CONTEXT.md)

For redesign references, mockups, screenshots, and visual exploration files, read:

- [REDESIGN/README.md](./REDESIGN/README.md)

## Main folders

- app/: patient application.
- hub/: professional hub.
- shared/: shared UI, config, database, sync, theme, and utility code.
- installers/: installer and uninstaller sources.
- db/: local database assets.
- assets/: runtime images, icons, branding, and fonts.
- REDESIGN/: design references, mockups, screenshots, and redesign sources.

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

Do not commit .env.

Use .env.example as a template.
