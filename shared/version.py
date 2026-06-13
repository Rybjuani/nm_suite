"""version.py — Versión oficial del producto NeuroMood (fuente única).

Consumida por:
  - shared/legal_contract.py  (constancia de consentimiento)
  - hub/main_qt.py · app/home_qt.py (caption "Acerca de" / Ajustes)
  - installers/nsis/common.nsh (NM_*_VERSION — actualizar a mano al subir
    de versión: NSIS no puede importar Python)
"""

NM_VERSION = "1.0.0"
