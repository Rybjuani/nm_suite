# Ejemplo: Episodio Visual QA — NeuroMood

Ejemplo ficticio de un episodio de QA visual usando el harness.

## Contexto

- **Repo:** nm_suite
- **Perfil:** nm_suite_visual_qa
- **Prompt:** 04_visual_qa.md
- **Tipo de tarea:** visual_qa

## Episodio

```markdown
# Episode: visual_clipping_hub_pacientes

## Identificacion

- **ID episodio:** 20250615_143000_visual_clipping_hub
- **Fecha:** 2025-06-15 14:30:00
- **Repo objetivo:** C:\Users\nosom\Desktop\nm_suite
- **Perfil usado:** nm_suite_visual_qa
- **Agente/Modelo:** Claude Sonnet 4

## Objetivo

Verificar clipping visual en Hub Pacientes al resize de ventana a 1024x768.

## No objetivos

- No auditar otras pantallas
- No tocar codigo
- No verificar funcionalidad logica

## Presupuesto

- **Presupuesto maximo:** 50,000 tokens

## Scope

### Archivos permitidos

- (read-only, no tocar archivos)

### Archivos prohibidos

- Todos los archivos de codigo

## Plan

1. Abrir aplicacion con ventana a 1024x768
2. Navegar a Hub Pacientes
3. Comparar contra referencia
4. Documentar defectos visuales
5. Cerrar con matriz

## Ejecucion

### Hallazgos

| ID | Severidad | Componente | Descripcion | Categoria |
|----|-----------|------------|-------------|-----------|
| V001 | Alto | Hub Pacientes | Clipping en titulo al reducir ventana | Hecho |
| V002 | Medio | Sidebar | Texto se superpone con borde | Hecho |
| V003 | Bajo | Footer | Espaciado diferente a referencia | Inferencia |

### Evidencia

- Antes: captura referencia a 1440x900
- Despues: captura actual a 1024x768
- Divergencia visible en titulo y sidebar

## Validacion

- Capturas comparadas visualmente
- No se toco codigo (read-only)
- Matriz completa con 3 defectos

## Resultado

- **Diff stat:** N/A (read-only)
- **Archivos tocados:** Ninguno
- **Deuda restante:**
  - V001: Clipping en titulo (requiere fix CSS)
  - V002: Superposicion sidebar (requiere fix layout)
  - V003: Espaciado footer (baja prioridad)

## Decision final

- [x] Pedir revision
```

## Flujo usado

1. `.\scripts\verify_git_state.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"`
2. `.\scripts\start_episode.ps1 -Name "visual_clipping_hub" -Profile "nm_suite_visual_qa"`
3. Editar EPISODE.md con objetivo
4. Correr agente con perfil + episodio + `prompts/04_visual_qa.md`
5. `.\scripts\close_episode.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"`
6. Revisar evidencia
7. Decidir: crear episodio de fix para V001 y V002, deferir V003
