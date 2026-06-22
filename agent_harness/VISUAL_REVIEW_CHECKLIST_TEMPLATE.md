# Visual Review Checklist Template

Usar para cualquier episodio de UI visual. Una fila por pantalla/estado/tema.

## Metadata

- **Episodio:**
- **Cluster:**
- **Commit/HEAD antes:**
- **Commit/HEAD despues:**
- **Reviewer:**
- **Fecha:**

## Reglas

- Captura generada no equivale a aprobacion visual.
- Probe/tests/ruff son soporte tecnico, no cierre visual.
- SSIM/MAD solo son senal auxiliar.
- P0/P1 abiertos bloquean el cierre salvo diferimiento owner explicito.
- Si no hay cambio de UI (por ejemplo C0-GATE-HARNESS), documentar "N/A sin superficie UI"
  y usar evidencia documental before/after.

## Checklist

| Pantalla | Estado | Tema | Captura before | Captura after | Defectos esperados | Resultado visual | Decision | Reviewer | Notas |
|---|---|---|---|---|---|---|---|---|---|
|  |  | light/dark |  |  |  | pass/fail/deferred | approved/rejected/deferred |  |  |

## Defectos P0/P1

| ID defecto | Estado final | Evidencia | Diferido por owner | Notas |
|---|---|---|---|---|
|  | resolved/deferred/open |  | yes/no |  |

## Decision final

- [ ] Aprobado visualmente
- [ ] Rechazado visualmente
- [ ] Diferido por owner
- [ ] No aplica: episodio sin superficie UI
