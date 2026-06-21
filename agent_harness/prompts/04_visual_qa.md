# Prompt: Visual QA

Inspección visual. No editar código. Comparar contra referencia.

## Instrucciones

1. Leer el perfil asignado.
2. Leer el episodio asignado.
3. Comparar la pantalla/componente contra la referencia.
4. Reportar defectos por severidad y por cluster.

## Reglas

- **No SSIM como anestesia.** SSIM alto con divergencia visible = defecto, no éxito.
- **No "fiel" sin evidencia.** Declarar fidelidad requiere matriz por componente.
- **Separar hechos, inferencias y no verificables.** Cada hallazgo debe tener categoría.
- **Trabajar por clusters.** Una pantalla/componente por episodio.
- **No editar código.** Este prompt es read-only.
- **No hacer commit/push.**

## Categorías de severidad

- **Crítico:** Bloquea la visualización o funcionalidad de la pantalla.
- **Alto:** Degradación visual severa, texto ilegible, elementos superpuestos.
- **Medio:** Divergencia visible con workaround o impacto menor.
- **Bajo:** Detalles cosméticos, pixels de diferencia, espaciado menor.

## Salida esperada

```
## Cluster: (nombre)
## Referencia: (descripción o archivo de referencia)

### Defectos
| ID | Severidad | Descripción | Categoría | Evidencia |
|----|-----------|-------------|-----------|-----------|

### Resumen
- Críticos: X
- Altos: X
- Medios: X
- Bajos: X

### Hechos
- (listar)

### Inferencias
- (listar)

### No verificable
- (listar)

## Presupuesto usado: X%
## Decisión: (continuar / cerrar / pedir revisión)
```
