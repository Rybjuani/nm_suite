# Task Types

Definición de tipos de tarea y sus reglas.

## audit_readonly

**Permisos:** Sólo lectura. No editar archivos.

**Riesgos:** Bajo. El agente no toca nada.

**Validación mínima:** Reporte de hallazgos separados en hechos / inferencias / no verificado.

**Stop rules especiales:**
- Cortar si el agente intenta editar cualquier archivo.
- Cortar si no produce hallazgos al 40% del presupuesto.

**Cuándo NO usarlo:** Cuando se necesita corregir algo. Usar `safe_bugfix` en su lugar.

---

## safe_bugfix

**Permisos:** Editar archivos dentro del scope. No crear archivos nuevos salvo autorización.

**Riesgos:** Medio. Toca código productivo.

**Validación mínima:**
- Reproducir el bug antes de corregir.
- Verificar que el fix no rompe nada existente.
- Diff acotado (pocos archivos).

**Stop rules especiales:**
- Cortar si el fix se expande a más archivos de los permitidos.
- Cortar si no puede reproducir el bug.
- Cortar si el diff crece más de lo esperado.

**Cuándo NO usarlo:** Para refactor, visual QA, o docs. Usar el tipo correspondiente.

---

## visual_qa

**Permisos:** Sólo lectura para inspección visual. Puede generar capturas de evidencia.

**Riesgos:** Bajo. No toca código.

**Validación mínima:**
- Comparación contra referencia.
- Matriz de defectos por severidad.
- Separación hechos / inferencias / no verificable.

**Stop rules especiales:**
- Cortar si declara "fiel" sin matriz de evidencia.
- Cortar si usa SSIM como excusa para ignorar divergencia visible.
- Cortar si mezcla clusters.

**Cuándo NO usarlo:** Para corregir bugs visuales. Usar `safe_bugfix` con perfil visual.

---

## refactor

**Permisos:** Editar archivos dentro del scope. No cambiar comportamiento observable.

**Riesgos:** Medio-alto. Puede introducir regresiones silenciosas.

**Validación mínima:**
- Tests existentes deben pasar antes y después.
- Diff acotado.
- No cambiar APIs públicas sin autorización.

**Stop rules especiales:**
- Cortar si cambia comportamiento observable.
- Cortar si mezcla refactor con features.
- Cortar si no hay tests para validar.

**Cuándo NO usarlo:** Si no hay tests. Si el cambio es un fix. Si mezcla concerns.

---

## docs

**Permisos:** Editar archivos de documentación. No tocar código.

**Riesgos:** Bajo. No afecta ejecución.

**Validación mínima:**
- No contradecir fuentes vigentes.
- No duplicar documentos existentes.
- Resumen ejecutivo antes que enciclopedia.

**Stop rules especiales:**
- Cortar si toca archivos de código.
- Cortar si el documento supera lo razonable para el objetivo.
- Cortar si duplica contenido existente.

**Cuándo NO usarlo:** Si el cambio requiere modificar código. Si es un release notes de deploy.

---

## release

**Permisos:** Editar build, dist, installers, versiones. Sólo con autorización explícita.

**Riesgos:** Alto. Toca artefactos de deploy.

**Validación mínima:**
- Version bump explícito.
- Build limpio.
- Tests pasando.
- Changelog actualizado.

**Stop rules especiales:**
- Cortar si no hay autorización explícita para release.
- Cortar si el build falla.
- Cortar si hay tests rotos.

**Cuándo NO usarlo:** Nunca sin autorización explícita del owner.

---

## cleanup

**Permisos:** Eliminar archivos temporales, imports no usados, dead code. No tocar lógica.

**Riesgos:** Medio. Puede romper imports implícitos.

**Validación mínima:**
- Tests pasando después del cleanup.
- No eliminar archivos referenciados dinámicamente.
- Diff revisionado manualmente.

**Stop rules especiales:**
- Cortar si toca lógica funcional.
- Cortar si elimina más de lo autorizado.
- Cortar si hay tests rotos después del cleanup.

**Cuándo NO usarlo:** Si el cleanup requiere entender lógica de negocio. Si no hay tests.
