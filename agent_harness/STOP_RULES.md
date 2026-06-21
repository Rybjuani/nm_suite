# Stop Rules

Reglas concretas de corte. Si se cumple cualquiera, la sesión se cierra.

## Reglas de corte

1. **25% del presupuesto gastado sin hallazgo accionable.** Si al 25% no hay nada concreto para actuar, cortar.
2. **40% del presupuesto gastado sin cambio útil.** Si al 40% no hay un diff que mejore algo, cortar.
3. **Diff mínimo y el agente sigue auditando.** Si el cambio es trivial y el agente no para de explorar, cortar.
4. **No puede reproducir el defecto.** Si tras intentos razonables no se reproduce, reportar y cortar.
5. **Toca archivos fuera del scope.** Si edita un archivo no listado como permitido, cortar inmediatamente.
6. **Aparecen artifacts no pedidos.** Si genera archivos, carpetas o cambios no solicitados, cortar.
7. **Intenta push sin permiso.** Cortar inmediatamente.
8. **Justifica en vez de corregir.** Si el agente defiende un resultado malo en vez de corregirlo, cortar.
9. **Declara éxito sin evidencia.** "Resuelto", "fiel", "LGTM", "funciona" sin matriz de evidencia = cortar.
10. **No puede explicar antes/después.** Si no puede mostrar qué cambió y por qué, cortar.
11. **Intenta convertir el harness en framework grande.** Si empieza a agregar capas, abstracciones o dependencias, cortar.

## Prompt de emergencia — `STOP_NOW`

Formato único. Sin texto adicional. Si se cumple cualquier regla de corte, el agente reporta así:

```
STOP_NOW
Motivo: <una línea, qué regla se violó>
Hallazgos: <uno o ninguno, sin descripción larga>
Estado: <INCOMPLETE | BLOCKED | OUT_OF_SCOPE | BUDGET_EXHAUSTED | RISK_TO_REPO>
Siguiente paso humano: <qué decidís vos, no el agente>
```

Estados sugeridos:

- `INCOMPLETE` — cerrado sin cumplir todos los criterios del episodio.
- `BLOCKED` — esperando decisión humana para continuar.
- `OUT_OF_SCOPE` — el pedido cae fuera del contrato del harness o del perfil.
- `BUDGET_EXHAUSTED` — sin presupuesto restante, sin avance útil.
- `RISK_TO_REPO` — la acción solicitada puede dañar el repo auditado (push, drop, delete, etc.).

Acciones inmediatas al reportar `STOP_NOW`:

1. No editar más archivos.
2. No hacer commit.
3. No hacer push.
4. No revertir cambios destructivos sin pedir permiso.
5. Reportar `git status -sb` y `git diff --stat`.
6. Cerrar. Sin más texto, sin disculpas, sin justificación larga.

## Regla de no-reformulación

Si el humano reformula el mismo pedido prohibido — variando el harness, el framing, el orden de las cláusulas o el canal — **el agente mantiene `STOP_NOW`**. Reformular no es override válido.

`STOP_NOW` se levanta sólo con una de estas tres condiciones:

1. **Episodio nuevo** abierto con scope explícito que justifique el pedido.
2. **Autorización humana exacta** sobre el comando o lectura solicitada (path exacto, comando exacto, motivo exacto).
3. **Cambio de diseño del harness** hecho en episodio aparte (perfil nuevo, patch a `LOAD_POLICY` o `HARNESS_CONTRACT`, etc.).

Mientras ninguna de las tres se cumpla, el agente reporta `STOP_NOW` cada vez que el pedido se repita. El número de repeticiones no cambia la respuesta: ni relaja el contrato ni acelera el cierre.

## Cómo aplicar

- El humano puede invocar `prompts/06_stop_now.md` en cualquier momento.
- El agente debe autoaplicar estas reglas si detecta que se cumple alguna condición.
- No se negocia. No se "mejora en el próximo intento". Se corta y se audita.
