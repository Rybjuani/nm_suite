# Controlled Agent Harness

## Qué es

Un harness externo, pequeño y modular para controlar sesiones de agentes de programación con disciplina, bajo costo y cierre verificable.

## Para qué sirve

- Define reglas claras antes de que el agente trabaje.
- Limita lo que el agente puede leer, tocar y decidir.
- Exige evidencia antes de declarar éxito.
- Permite cerrar sesiones limpiamente: commit o rollback.

## Qué problema evita

- Agentes que leen todo el contexto y se pierden.
- Documentación gigante que nadie revisa y que se contradice.
- Sesiones sin presupuesto, sin scope, sin stop rules.
- Cambios fuera de scope, push no autorizado, mezcla de clusters.
- Declaraciones de éxito sin evidencia verificable.

## Por qué es externo al repo real

- El harness no es parte del producto. Es herramienta de control.
- Si vive dentro del repo, el agente lo carga como contexto permanente.
- Externo = el agente sólo carga lo que el episodio necesita.
- El repo real permanece limpio de artefactos de control.

## Por qué NO debe convertirse en memoria gigante

- Si el harness crece, replica el problema que viene a resolver.
- Cada archivo debe ser breve, específico y por episodio.
- La regla central: **el agente no lee todo el harness; lee sólo perfil + episodio + prompt.**

## Flujo básico

1. **Elegir perfil** → `profiles/<perfil>/PROFILE.md`
2. **Crear episodio** → `scripts/start_episode.ps1 -Name <nombre> -Profile <perfil>`
3. **Dar prompt** → usar uno de `prompts/` según tipo de tarea
4. **Correr agente** → el agente trabaja dentro del scope definido
5. **Cerrar sesión** → `scripts/close_episode.ps1 -RepoPath <ruta>`
6. **Auditar evidencia** → revisar diff, archivos tocados, validación
7. **Decidir** → commit o rollback
8. **Integrar** → recién después de la decisión, integrar al repo real

## Regla central

> El agente no lee todo el harness.  
> Lee sólo: **perfil + episodio + un prompt.**  
> Si necesita más contexto, debe pedir permiso.

## Estructura

```
nm_agent_harness/
  README.md                  ← este archivo
  HARNESS_CONTRACT.md        ← reglas universales
  LOAD_POLICY.md             ← qué lee el agente (y qué no)
  STOP_RULES.md              ← reglas de corte
  RUNBOOK.md                 ← flujo práctico
  TASK_TYPES.md              ← tipos de tarea
  PROFILE_TEMPLATE.md        ← template de perfil
  EPISODE_TEMPLATE.md        ← template de episodio
  DEFECT_LEDGER_TEMPLATE.md  ← template de defectos
  DECISION_LOG_TEMPLATE.md   ← template de decisiones
  EVIDENCE_PACKAGE_TEMPLATE.md ← template de evidencia
  profiles/                  ← perfiles por repo/tarea
  prompts/                   ← prompts reusables
  scripts/                   ← scripts PowerShell
  examples/                  ← ejemplos de episodios
```

## Scripts

| Script | Uso |
|--------|-----|
| `verify_git_state.ps1` | Verificar estado git del repo objetivo |
| `start_episode.ps1` | Crear carpeta de episodio con template |
| `close_episode.ps1` | Mostrar estado final del episodio |
| `summarize_diff.ps1` | Resumen de cambios con advertencias |
| `check_harness_size.ps1` | Verificar que el harness no creció demasiado |

## Principio

El harness es permanente.  
El perfil es reusable.  
El episodio es descartable.
