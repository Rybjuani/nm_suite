# Profile: Generic Visual QA

Perfil genérico para QA visual.

## Repo

- **Nombre del repo:** (completar por episodio)
- **Ruta local:** (completar por episodio)
- **Remoto:** (completar por episodio)
- **Rama operativa:** (completar por episodio)

## Reglas

1. **Comparar contra referencia.** Si no hay referencia, pedir una. No inventar.
2. **No declarar fidelidad global sin matriz.** "Se ve bien" no es evidencia.
3. **No usar métricas como excusa si hay divergencia visible.** SSIM alto + divergencia visible = bug, no éxito.
4. **Separar hechos, inferencias y no verificables.** Cada hallazgo debe tener categoría.
5. **Trabajar por clusters.** Un cluster = una pantalla/componente por episodio.

## Categorías de hallazgo

- **Hecho:** Observable, medible, reproducible.
- **Inferencia:** Basado en evidencia pero no directamente observable.
- **No verificable:** No se puede confirmar con los datos disponibles.

## Prohibido

- Declarar "fiel" sin matriz de evidencia
- Usar SSIM como anestesia para ignorar problemas visibles
- Mezclar clusters en un solo episodio
- Editar código (este perfil es read-only)
- `git push`
- Generalizar desde un solo dato

## Validación mínima

- Captura antes/después (si aplica)
- Matriz de defectos por severidad
- Cada defecto categorizado (hecho/inferencia/no verificable)
- Cluster bien definido
- No hay divergencias visuales sin reportar

## Criterios de rollback

- No aplica (perfil read-only). Se cierra la sesión y se reporta.
