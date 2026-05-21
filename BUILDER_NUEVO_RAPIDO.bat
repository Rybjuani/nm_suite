@echo off
REM ============================================================================
REM BUILDER_NUEVO_RAPIDO.bat — ALIAS TEMPORAL DE COMPATIBILIDAD
REM ============================================================================
REM Este script queda como atajo del modo external (payload .zip junto al
REM instalador). El launcher oficial ahora es BUILD_NEUROMOOD.bat.
REM
REM Migracion sugerida:
REM   antes:  BUILDER_NUEVO_RAPIDO.bat
REM   ahora:  BUILD_NEUROMOOD.bat --installer-mode external
REM
REM Este alias se removera en un release futuro (post F0.2.B + 1).
REM ============================================================================

echo [DEPRECATED] BUILDER_NUEVO_RAPIDO.bat es un alias temporal de
echo              BUILD_NEUROMOOD.bat --installer-mode external
echo              Migrar al launcher oficial cuando puedas.
echo.

call "%~dp0BUILD_NEUROMOOD.bat" --installer-mode external %*
exit /b %errorlevel%
