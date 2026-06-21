# Prompt: Fix Cluster

Corregir un cluster específico. No mezclar.

## Instrucciones

1. Leer el perfil asignado.
2. Leer el episodio asignado.
3. Identificar el objetivo del cluster.
4. Reproducir el problema (si aplica).
5. Corregir sólo los archivos permitidos en el episodio.
6. Validar la corrección.
7. Cerrar con evidencia antes/después.

## Reglas

- **Objetivo:** Sólo el cluster asignado. Nada más.
- **Archivos permitidos:** Sólo los listados en EPISODE.md.
- **Presupuesto:** Respetar el máximo definido.
- **Validación:** Verificar que el fix funciona y no rompe nada.
- **Stop rules:** Aplicar STOP_RULES.md si corresponde.
- **No mezclar clusters.** Si aparece otro problema, reportar y frenar.
- **Evidencia antes/después.** Sin evidencia = no hay fix.

## Presupuesto

- Si se gasta más de 25% sin hallazgo accionable → reportar.
- Si se gasta más de 40% sin cambio útil → cerrar sesión.

## Salida esperada

```
## Cluster: (nombre)
## Objetivo: (descripción)
## Archivos tocados: (lista)
## Validación: (qué se verificó y resultado)
## Evidencia antes: (estado previo)
## Evidencia después: (estado posterior)
## Diff stat: (resumen)
## Deuda restante: (si aplica)
## Decisión: (commit / rollback / pedir revisión)
```
