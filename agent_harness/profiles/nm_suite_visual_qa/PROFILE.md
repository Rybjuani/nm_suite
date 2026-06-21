# Profile: NM Suite Visual QA

Perfil específico para QA visual del repo nm_suite.

## Repo

- **Nombre del repo:** nm_suite
- **Ruta local:** `C:\Users\nosom\Desktop\nm_suite`
- **Remoto:** `Rybjuani/nm_suite`
- **Rama operativa:** `main`

## Entorno

- **Shell:** PowerShell nativo. No Git Bash. No WSL.
- **Python:** `.\.venv\Scripts\python.exe`
- **No usar:** Git Bash, WSL, comandos Linux-only

## Scope

### Prohibido tocar

- DB/sync/lógica clínica
- build/dist/installers (salvo release explícito)
- `git add .` — nunca
- `git push` sin autorización
- Revivir funciones eliminadas
- "Pulish global" o cambios masivos

### Permitido (por episodio)

- Listar explícitamente en cada EPISODE.md
- Siempre por clusters (una pantalla/componente por episodio)

## Reglas específicas

1. **Trabajar por clusters.** Una pantalla/componente por episodio.
2. **Cada fix debe bajar deuda verificable o no cuenta.** Si el fix no reduce deuda medible, no es un fix.
3. **No vender SSIM/font ceiling como éxito visual.** SSIM alto con divergencia visible = bug.
4. **No declarar fidelidad global sin matriz.** "Se ve fiel" sin evidencia por componente = inválido.
5. **Comparar contra referencia.** Si no hay referencia, pedir una.
6. **Separar hechos, inferencias y no verificables.**

## Categorías de hallazgo

- **Hecho:** Observable en captura, medible, reproducible.
- **Inferencia:** Basado en evidencia indirecta.
- **No verificable:** No se puede confirmar con datos disponibles.

## Validación mínima

- Captura antes/después del cluster
- Matriz de defectos por severidad
- Cada defecto categorizado
- Diff stat (si se tocó código)
- Deuda restante listada

## Comandos de verificación

```powershell
cd C:\Users\nosom\Desktop\nm_suite
.\.venv\Scripts\python.exe -m pytest   # si aplica
git status -sb
git log --oneline -5
```

## Criterios de rollback

- Divergencia visible sin reportar
- Cambios fuera del cluster asignado
- Fix que no baja deuda verificable

## Decisiones del owner

- No revivir funciones eliminadas
- No "pulish global"
- No push sin autorización explícita
- PowerShell nativo siempre
