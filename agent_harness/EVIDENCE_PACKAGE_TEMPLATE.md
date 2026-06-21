# Evidence Package Template

Evidencia mínima requerida para cerrar un episodio.

## Obligatorio

### Estado del repo

- `git status -sb`
- `git log --oneline -5`
- `git diff --stat`
- `git diff --name-only`

### Tests

- Tests ejecutados y resultado (pass/fail/skip)
- Si no hay tests, justificar por qué

### Antes / Después

- Estado antes del cambio (captura, log, descripción)
- Estado después del cambio (captura, log, descripción)
- Diferencia observable

### Archivos tocados

- Lista completa de archivos modificados/creados/eliminados

## Condicional

### Capturas (si aplica)

- Para tareas visuales: captura antes y después
- Nombrar: `evidence/<episodio>_before_<componente>.png`
- Nombrar: `evidence/<episodio>_after_<componente>.png`

### Defectos

- Defectos bajados (corregidos con validación)
- Defectos no resueltos (con justificación)

### Riesgos

- Riesgos identificados durante la sesión
- Riesgos remanentes después del cierre

## Decisión recomendada

- [ ] Commit — evidencia completa, sin deuda crítica
- [ ] Rollback — problemas detectados, mejor revertir
- [ ] Pedir revisión — evidencia parcial, necesita ojo humano
- [ ] Descartar — episodio sin resultados útiles

## Regla

> Sin evidencia = sin éxito. Sin diff = sin cambio. Sin validación = sin cierre.
