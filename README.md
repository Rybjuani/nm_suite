# NeuroMood / nm_suite
NeuroMood is a Windows desktop mental health and therapy suite built with Python 3.12 and PyQt6.
The project contains two main applications:
- NeuroMood Suite: patient-facing app.
- NeuroMood Hub: professional/therapist app.
## Main folders
- app/: patient application.
- hub/: professional hub.
- shared/: shared UI, config, database, sync, theme, and utility code.
- installers/: installer and uninstaller sources.
- db/: local database assets.
- assets/: runtime images, icons, branding, and fonts.
- REDESIGN/: design references, mockups, screenshots, and redesign sources.
## Build
Install dependencies:
    pip install -r requirements.txt
Run the patient app:
    python app/main_qt.py
Run the professional hub:
    python hub/main_qt.py
Build executables:
    python build_neuromood.py
or on Windows:
    BUILD_NEUROMOOD.bat
## Secrets
Do not commit .env.
Use .env.example as a template.
## Redesign workflow
The REDESIGN folder contains visual references only. It should be used to organize mockups, screenshots, Figma references, and UI redesign sources.
Runtime assets should live in assets/.
