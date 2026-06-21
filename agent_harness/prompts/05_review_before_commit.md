# Prompt: Review Before Commit

Revisar cambios antes de hacer commit. No commitear automáticamente.

## Instrucciones

1. Revisar el diff generado.
2. Verificar que se respeta el scope del episodio.
3. Confirmar que los tests pasan (si existen).
4. Listar riesgos.
5. Sugerir commit o rollback.

## Checklist

- [ ] ¿El diff toca sólo archivos permitidos en el episodio?
- [ ] ¿El diff toca sólo el cluster asignado?
- [ ] ¿Los tests pasan?
- [ ] ¿No hay archivos artifacts no pedidos?
- [ ] ¿No hay rutas prohibidas (build/, dist/, installer/, .zip, .exe)?
- [ ] ¿Hay evidencia antes/después?
- [ ] ¿La deuda restante está documentada?

## Salida esperada

```
## Revisión pre-commit

### Diff stat
(pegar salida de git diff --stat)

### Archivos tocados vs. permitidos
| Archivo | ¿Permitido? | ¿En scope? |
|---------|-------------|------------|

### Tests
- Resultado: (pass/fail/skip/no hay tests)

### Riesgos
- (listar riesgos identificados)

### Veredicto
- [ ] ✅ Commit sugerido — scope correcto, tests pasan, sin riesgos críticos
- [ ] ⚠️ Commit con advertencias — (detallar)
- [ ] ❌ Rollback sugerido — (detallar por qué)
- [ ] 🔍 Pedir revisión humana — (detallar por qué)
```

## Regla

> No commitear sin revisión. No pushear sin autorización.
