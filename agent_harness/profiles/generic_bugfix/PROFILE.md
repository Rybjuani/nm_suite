# Profile: Generic Bugfix

Perfil para corrección de bugs pequeños y acotados.

## Repo

- **Nombre del repo:** (completar por episodio)
- **Ruta local:** (completar por episodio)
- **Remoto:** (completar por episodio)
- **Rama operativa:** (completar por episodio)

## Reglas

1. **Scope chico.** Un bug = un episodio. No expandir.
2. **Reproducir antes de corregir.** Si no se reproduce, reportar y frenar.
3. **Tocar pocos archivos.** Idealmente 1-3 archivos por fix.
4. **Validar después de corregir.** Ejecutar tests, verificar comportamiento.
5. **Commit chico.** Un commit por fix, mensaje descriptivo.
6. **No push sin permiso.** Push = acción humana.

## Prohibido

- `git add .`
- `git push` sin autorización
- Editar archivos fuera del scope
- Mezclar fix con refactor
- Crear archivos nuevos sin autorización
- Declarar "resuelto" sin evidencia

## Validación mínima

- Bug reproducido antes del fix
- Fix aplicado y verificado
- Tests pasando (si existen)
- Diff acotado y revisable
- Evidencia antes/después

## Criterios de rollback

- El fix no resuelve el bug
- El fix rompe otra cosa
- El diff crece más de lo esperado
- No se puede validar
