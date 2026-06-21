# Profile: NM Suite Safe Bugfix

Perfil para bugfix puntual en nm_suite.

## Repo

- **Nombre del repo:** nm_suite
- **Ruta local:** `C:\Users\nosom\Desktop\nm_suite`
- **Remoto:** `Rybjuani/nm_suite`
- **Rama operativa:** `main`

## Entorno

- **Shell:** PowerShell nativo. No Git Bash. No WSL.
- **Python:** `.\.venv\Scripts\python.exe`
- **No usar:** Git Bash, WSL, comandos Linux-only

## Reglas

1. **Verificar git primero.** Si el repo no está limpio, frenar.
2. **Reproducir el bug.** Sin reproducción, no hay fix.
3. **Tocar sólo archivos permitidos.** Listar en EPISODE.md explícitamente.
4. **Validar.** Tests, ejecución, verificación manual según corresponda.
5. **Commit chico.** Un commit, mensaje descriptivo, diff acotado.
6. **No push sin permiso.** Push = acción humana, nunca del agente.
7. **Cortar si el fix se expande.** Si empieza a tocar más archivos de los previstos, frenar.

## Prohibido

- `git add .`
- `git push` sin autorización
- Editar archivos fuera del scope
- Mezclar fix con refactor
- Tocar DB/sync/lógica clínica
- Tocar build/dist/installers
- Revivir funciones eliminadas
- Declarar "resuelto" sin evidencia
- Git Bash o WSL

## Validación mínima

- Bug reproducido antes del fix
- Fix aplicado y verificado
- Tests pasando (si existen)
- Diff acotado (idealmente 1-3 archivos)
- Evidencia antes/después
- Deuda restante listada

## Comandos de verificación

```powershell
cd C:\Users\nosom\Desktop\nm_suite
.\.venv\Scripts\python.exe -m pytest   # si aplica
git status -sb
git log --oneline -5
```

## Criterios de rollback

- El fix no resuelve el bug
- El fix rompe otra cosa
- El diff crece más de lo esperado
- No se puede validar
- Se tocaron archivos fuera del scope
