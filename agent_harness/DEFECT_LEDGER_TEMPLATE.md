# Defect Ledger Template

Copiar y usar para registrar defectos por cluster.

## Formato

| ID | Severidad | Módulo/Pantalla | Evidencia | Causa sospechada | Estado | Commit corrige | Validación | Deuda restante |
|----|-----------|-----------------|-----------|------------------|--------|----------------|------------|----------------|
| D001 | | | | | | | | |
| D002 | | | | | | | | |

## Severidades

- **Crítico:** Bloquea funcionalidad principal. No se puede usar.
- **Alto:** Degradación severa. Se puede usar pero con impacto importante.
- **Medio:** Defecto visible con workaround.
- **Bajo:** Defecto menor, cosmético o de borde.

## Estados

- **Open:** Detectado, sin corrección.
- **In progress:** En corrección.
- **Fixed:** Corregido, con commit y validación.
- **Deferred:** Pospuesto con justificación.
- **Wontfix:** No se corregirá con justificación.

## Reglas

- Un defecto = una fila.
- No cerrar sin validación.
- No cerrar sin commit que lo corrija.
- Si se defiere, justificar en "Deuda restante".
