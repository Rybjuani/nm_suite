# Prompt: Audit ReadOnly

Modo auditoría. Sólo lectura. No editar nada.

## Instrucciones

1. Leer el perfil asignado.
2. Leer el episodio asignado.
3. Auditar el objetivo del episodio sin editar archivos.
4. Reportar hallazgos separados en tres categorías:
   - **Hechos:** Observable, medible, reproducible.
   - **Inferencias:** Basado en evidencia pero no directamente observable.
   - **No verificado:** No se puede confirmar con los datos disponibles.
5. Cerrar con una matriz de hallazgos.

## Reglas

- No editar archivos.
- No crear archivos.
- No ejecutar cambios.
- No hacer commit.
- No hacer push.
- Si necesitas más contexto, pedir permiso.
- Si no encuentras nada accionable al 40% del presupuesto, reportar y cerrar.

## Salida esperada

```
## Hallazgos

### Hechos
- (listar)

### Inferencias
- (listar)

### No verificado
- (listar)

## Matriz de hallazgos
| ID | Categoría | Descripción | Severidad | Acción sugerida |
|----|-----------|-------------|-----------|-----------------|

## Presupuesto usado: X%
## Decisión: (continuar / cerrar / pedir revisión)
```
