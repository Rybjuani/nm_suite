# Harness Contract

Reglas universales. Sin excepción. Sin filosofía.

## Reglas

1. **No trabajar sin estado git inicial.** Si el repo no tiene git limpio, frenar.
2. **No editar fuera del scope.** Sólo archivos listados como permitidos en el episodio.
3. **No usar `git add .`.** Siempre agregar archivos explícitamente, uno por uno.
4. **No hacer push sin autorización.** Push = acción humana, nunca del agente.
5. **No declarar éxito sin evidencia.** Sin diff, sin validación, sin antes/después = no hay éxito.
   En UI visual, capturas generadas, probe OK y tests verdes son evidencia tecnica, no
   aprobacion visual.
6. **No mezclar clusters.** Un episodio = un cluster. Si aparecen otros, frenar y reportar.
7. **No tocar build/dist/installers** salvo que la tarea sea release explícito.
8. **No ocultar fallos.** Si algo falla, reportarlo. No silenciar errores.
9. **No seguir si no hay avance medible.** Si el agente gira sin progreso, cortar.
10. **No modificar lógica crítica sin autorización.** Lógica clínica, cálculos, validaciones = off-limits salvo permiso explícito.
11. **No ejecutar cambios destructivos.** No borrar datos, no dropear tablas, no forzar sobreescribir.
12. **Cerrar siempre con:**
    - Status final (commit / rollback / pendiente)
    - `git diff --stat`
    - Lista de archivos tocados
    - Validación ejecutada
    - Deuda restante
13. **Cierre visual trazado obligatorio.** Un episodio de UI visual solo puede cerrar si
    incluye checklist por pantalla/estado/tema con evidencia before/after y decision
    explicita. Ningun cluster visual puede cerrarse solo con tests verdes, SSIM/MAD,
    runtime probe o `capture_v8` exitoso.

## Regla especial UI V2

- `c0c692e` se conserva como cierre tecnico exitoso (probe/tests/capturas), pero queda
  invalidado como cierre visual: no es rollback, es reapertura de deuda compositiva.
- En UI V2, "capture_v8 genero PNG" significa que hay evidencia tecnica disponible; no
  significa que la pantalla sea aceptable.
- El gate final visual requiere checklist trazado y defectos P0/P1 resueltos o diferidos
  explicitamente por owner.

## Prioridad en caso de conflicto

1. Episodio (lo más específico)
2. Perfil (contexto del repo/tarea)
3. Este contrato (regla universal)
4. README (referencia general, no fuente operativa)

## Violaciones

Si el agente viola cualquier regla, la sesión se cierra inmediatamente con el prompt de emergencia (`prompts/06_stop_now.md`).
