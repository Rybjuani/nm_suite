# Load Policy

Este archivo evita que el harness se convierta en el problema que viene a resolver: contexto excesivo.

## Lectura obligatoria máxima por episodio

Un agente en un episodio sólo debe leer:

1. `profiles/<perfil>/PROFILE.md` — el perfil elegido
2. `episodes/<episodio>/EPISODE.md` — el episodio activo
3. Un único prompt de `prompts/` — el que corresponde al tipo de tarea

**Total: 3 archivos. No más.**

## Prohibido por defecto

- ❌ Leer todo el harness
- ❌ Leer todos los perfiles
- ❌ Leer todos los ejemplos
- ❌ Leer documentación histórica no solicitada
- ❌ Leer RUNBOOK, TASK_TYPES, o templates si no son el episodio activo
- ❌ Crear contexto global obligatorio (AGENTS.md, AI_CONTEXT.md, MEMORY.md, etc.)
- ❌ Cargar múltiples prompts en la misma sesión

## Si el agente necesita más contexto

1. Debe pedir permiso explícitamente.
2. Debe justificar por qué necesita el archivo adicional.
3. El humano aprueba o deniega.
4. Sólo después de aprobación puede leer el archivo adicional.

### Mecanismo `LOAD_EXTRA`

Bloque a incluir en el episodio cuando se necesita contexto extra:

```
LOAD_EXTRA:
  - path: <ruta exacta dentro del repo auditado>
    reason: <una línea, motivo concreto>
  - path: <ruta exacta>
    reason: <una línea>
```

Reglas:

- Paths exactos. Sin globs, sin `**`, sin `..`.
- Reason de una línea. Sin justificación larga ni links a docs externas.
- Requiere aprobación humana explícita, escrita en el canal.
- Sin aprobación, no se lee nada extra. Ni siquiera "para confirmar".
- Si se deniega, el episodio continúa con la carga mínima original o se cierra con `STOP_NOW`.
- La aprobación aplica sólo a los paths listados. Cualquier path adicional requiere nueva aprobación.
- `LOAD_EXTRA` nunca se usa para esquivar el scope del perfil. Si el path cae fuera del scope, es cambio de diseño: episodio aparte.

## Resolución de contradicciones

Si hay contradicción entre archivos:

1. **El episodio manda** sobre todo lo demás.
2. **El perfil manda** sobre el contrato y el README.
3. **El contrato manda** sobre el README.
4. **El README no es fuente operativa principal.**

## Regla de oro

> Menos contexto cargado = menos alucinación = menos riesgo.  
> Si no estás seguro de necesitarlo, no lo leas.
