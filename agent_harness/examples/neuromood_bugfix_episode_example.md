# Ejemplo: Episodio Bugfix — NeuroMood

Ejemplo ficticio de un episodio de bugfix usando el harness.

## Contexto

- **Repo:** nm_suite
- **Perfil:** nm_suite_safe_bugfix
- **Prompt:** 02_fix_cluster.md
- **Tipo de tarea:** safe_bugfix

## Episodio

```markdown
# Episode: fix_clipping_hub_pacientes

## Identificacion

- **ID episodio:** 20250615_160000_fix_clipping_hub
- **Fecha:** 2025-06-15 16:00:00
- **Repo objetivo:** C:\Users\nosom\Desktop\nm_suite
- **Perfil usado:** nm_suite_safe_bugfix
- **Agente/Modelo:** Claude Sonnet 4

## Objetivo

Corregir clipping visual en titulo del Hub Pacientes a 1024x768.

## No objetivos

- No tocar sidebar (V002 del episodio visual)
- No tocar footer (V003)
- No refactorizar layout
- No hacer push

## Presupuesto

- **Presupuesto maximo:** 30,000 tokens

## Scope

### Archivos permitidos

- src/gui/hub_pacientes.py
- src/gui/styles/hub.css

### Archivos prohibidos

- Todo lo demas

## Estado inicial

- **Baseline antes:** main branch, sin cambios locales, commit abc1234

## Plan

1. Reproducir clipping a 1024x768
2. Identificar regla CSS causante
3. Aplicar fix minimo
4. Validar a 1024x768 y 1440x900
5. Cerrar con diff

## Ejecucion

### Cambios realizados

- `src/gui/styles/hub.css`: Cambiado `min-width: 1200px` a `min-width: 1024px` en `.hub-title`
- `src/gui/hub_pacientes.py`: Sin cambios (el problema era solo CSS)

### Validacion

- Clipping ya no ocurre a 1024x768
- Layout correcto a 1440x900 (sin regresion)
- Tests existentes: 12 pass, 0 fail
- No se tocaron archivos fuera del scope

### Evidencia

- Antes: titulo con clipping a 1024x768
- Despues: titulo visible completo a 1024x768
- Sin regresion a 1440x900

## Resultado

- **Diff stat:**
  hub.css | 1 +-
  1 file changed, 1 insertion, 1 deletion
- **Archivos tocados:** src/gui/styles/hub.css
- **Commit:** (pendiente autorizacion)
- **Deuda restante:**
  - V002 (sidebar) requiere episodio separado
  - V003 (footer) baja prioridad

## Decision final

- [ ] Commit (pendiente autorizacion del owner)
```

## Flujo usado

1. `.\scripts\verify_git_state.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"`
2. `.\scripts\start_episode.ps1 -Name "fix_clipping_hub" -Profile "nm_suite_safe_bugfix"`
3. Editar EPISODE.md con objetivo y scope
4. Correr agente con perfil + episodio + `prompts/02_fix_cluster.md`
5. Agente reproduce bug, identifica causa, aplica fix minimo
6. `.\scripts\close_episode.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"`
7. `.\scripts\summarize_diff.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"`
8. `prompts/05_review_before_commit.md` para revision pre-commit
9. Owner revisa y autoriza commit:
   ```powershell
   git add src/gui/styles/hub.css
   git commit -m "fix: clipping titulo Hub Pacientes a 1024x768"
   ```
10. No push sin autorizacion.
