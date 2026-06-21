# Prompt: Close Session

Cerrar la sesión actual. No más análisis. No más ediciones.

## Instrucciones

1. No editar más archivos.
2. No hacer más análisis.
3. Mostrar estado final del repo.

## Salida obligatoria

```
## Cierre de sesión

### Git status
(pegar salida de git status -sb)

### Diff stat
(pegar salida de git diff --stat)

### Archivos tocados
(listar archivos modificados/creados/eliminados)

### Validación
(qué se verificó, resultado)

### Deuda restante
(qué falta, si algo)

### Decisión
- [ ] Commit (si hay autorización)
- [ ] Rollback
- [ ] Pedir revisión
- [ ] Pendiente de autorización para commit/push
```

## Reglas

- No commit salvo autorización explícita.
- No push bajo ninguna circunstancia sin autorización.
- No agregar archivos nuevos en el cierre.
- Si hay archivos fuera de scope, reportarlo como advertencia.
