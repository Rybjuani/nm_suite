# Profile: Generic Refactor

Perfil conservador para refactor de código.

## Repo

- **Nombre del repo:** (completar por episodio)
- **Ruta local:** (completar por episodio)
- **Remoto:** (completar por episodio)
- **Rama operativa:** (completar por episodio)

## Reglas

1. **Refactor sólo con tests.** Si no hay tests que cubran el código, no refactorizar.
2. **No cambiar comportamiento.** El refactor no debe alterar outputs observables.
3. **Diff acotado.** Mover/renombrar es válido; reescribir no.
4. **Rollback claro.** Si algo falla, revertir inmediatamente.
5. **No mezclar refactor con features.** Un episodio = un tipo de cambio.

## Prohibido

- Refactorizar sin tests que validen
- Cambiar comportamiento observable
- Mezclar refactor con fix o feature
- Cambiar APIs públicas sin autorización
- `git add .`
- `git push` sin autorización
- Declarar "LGTM" sin tests pasando

## Validación mínima

- Tests pasando antes del refactor
- Tests pasando después del refactor
- Mismos outputs para mismas inputs
- Diff revisable y acotado
- No hay cambios fuera del scope

## Criterios de rollback

- Tests fallan después del refactor
- Comportamiento observable cambia
- El diff crece más de lo esperado
- No se puede verificar equivalencia
