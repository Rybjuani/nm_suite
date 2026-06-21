# Runbook

Flujo práctico para usar el Controlled Agent Harness.

## Pasos

### 1. Crear episodio

```powershell
.\scripts\start_episode.ps1 -Name "fix_clipping_hub" -Profile "nm_suite_safe_bugfix"
```

Esto crea `episodes/YYYYMMDD_HHMMSS_fix_clipping_hub/` con `EPISODE.md`, `evidence/`, `logs/`, `diffs/`.

### 2. Elegir perfil

Los perfiles viven en `profiles/`. Cada uno define reglas específicas para un tipo de tarea o repo.

- `generic_bugfix` — bugs pequeños
- `generic_refactor` — refactor conservador
- `generic_docs` — documentación
- `generic_visual_qa` — QA visual genérico
- `nm_suite_visual_qa` — QA visual para nm_suite
- `nm_suite_safe_bugfix` — bugfix puntual en nm_suite

### 3. Definir objetivo

Editar `EPISODE.md` en la carpeta del episodio. Escribir objetivo claro, acotado, verificable.

### 4. Definir presupuesto

En `EPISODE.md`, poner presupuesto máximo (tokens, tiempo, o intentos). Sin presupuesto = sin límite = sin control.

### 5. Definir archivos permitidos

En `EPISODE.md`, listar explícitamente qué archivos puede tocar el agente. Todo lo demás está prohibido.

### 6. Correr agente

Darle al agente:
1. El perfil: `profiles/<perfil>/PROFILE.md`
2. El episodio: `episodes/<episodio>/EPISODE.md`
3. Un prompt: `prompts/<prompt>.md`

No más. Seguir `LOAD_POLICY.md`.

### 7. Cerrar sesión

```powershell
.\scripts\close_episode.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"
```

### 8. Revisar evidencia

```powershell
.\scripts\summarize_diff.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"
```

Revisar:
- ¿Se respetó el scope?
- ¿Hay evidencia antes/después?
- ¿Queda deuda?

### 9. Decidir commit o rollback

Si todo está bien:

```powershell
git add <archivo1> <archivo2>   # explícito, nunca git add .
git commit -m "fix: descripción breve"
```

Si algo anda mal:

```powershell
git checkout -- .    # rollback de todo
# o
git checkout -- <archivo>   # rollback selectivo
```

### 10. Integrar al repo real

Recién después de la decisión. No antes.

## Ejemplo rápido

```powershell
# 1. Verificar estado
.\scripts\verify_git_state.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"

# 2. Crear episodio
.\scripts\start_episode.ps1 -Name "fix_clipping" -Profile "nm_suite_safe_bugfix"

# 3. Editar EPISODE.md con objetivo y scope

# 4. Correr agente con perfil + episodio + prompt

# 5. Cerrar
.\scripts\close_episode.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"

# 6. Revisar diff
.\scripts\summarize_diff.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"

# 7. Decidir: commit o rollback
```

## Regla

> No hay paso 10 sin paso 9. No se integra sin decidir.
