# Plan de corrección de discrepancias (por fases según gravedad)

Referencia canónica: `qa/mockup_reference_static/`. Detalle de hallazgos en
[DISCREPANCIAS_SENTINEL_VS_MOCKUP.md](DISCREPANCIAS_SENTINEL_VS_MOCKUP.md).

**Reglas:** el mockup estático es la referencia. NO tocar lógica clínica, DB/auth/sync/IA/PDF,
builder, instaladores ni `qa/mockup_reference_static`. Cambios solo de UI/estilos. Validar cada
fase capturando con el Sentinel y comparando contra el PNG del mockup. Commit por fase. No
declarar PASS visual global.

Comando de validación por módulo:
```powershell
.\.venv\Scripts\python.exe qa\visual_sentinel.py --platform auto audit --app <suite|hub> --theme light
```

---

## FASE 1 — Defecto funcional (bloqueante) 🔴

1. **Hub · Textos globales** — cada fila debe mostrar el valor actual DENTRO del input editable
   (como `light/Hub · Clínico/Configuración/Textos globales`), no como texto plano con un input
   vacío al lado. El contador `N/M` debe reflejar la longitud real (hoy marca `0/M`). El título de
   la vista debe decir "Textos globales" (el header de ventana puede seguir "Textos globales de Suite").

## FASE 2 — Inconsistencias de diseño sistemáticas 🟠

2. **Capitalización de headers de módulo** → sentence case:
   "Termómetro emocional", "Guía de respiración animada", "Temporizador de actividades",
   "Checklist de rutina diaria", "Asistente de activación conductual",
   "Registro de pensamientos (TCC)", "Recordatorios de bienestar". (DBT queda igual: sigla.)
3. **Segmented / chips seleccionados** — unificar el estado SELECCIONADO a verde oscuro relleno con
   texto claro (como Respiración y el mockup), eliminando la variante beige/clara en Termómetro
   ("7 días/30 días"), Temporizador ("25 min"; "Lectura/Pausa activa/Trabajo profundo") y
   Recordatorios ("Todos/Activos/Hoy"). Un solo estilo de "seleccionado".
4. **Checklist de rutina** — checkbox a la IZQUIERDA del texto (hoy a la derecha).

## FASE 3 — Pulido visual 🟡

5. **Guía de respiración** — pills de patrón con relleno de color (Inhalá=verde, Mantené=amarillo,
   Exhalá=naranja); CICLOS "0" en reposo (hoy "—").
6. **Termómetro emocional** — íconos de tarjetas "Progreso 7/30 días" = sparkle ✦; quitar dots
   blancos del slider.
7. **Recordatorios** — restaurar dot de color a la izquierda de cada badge (● Completado / ● Hoy / ● Activo).
8. **Registro TCC** — contador "0/500" dentro de la card (abajo izquierda).
9. **Home** — evitar wrap a 2 líneas de "Termómetro emocional" y "Registro de pensamientos".

## Fuera de alcance (no tratar como bug visual) ⚪

- Copy/voseo ("Arma" vs "Armá", subtítulos) → textos editables; decidir aparte.
- Estados capturados sin interacción (botón deshabilitado, thumb del slider, dots de progreso).
- Conteo "158 textos" vs "145" → diferencia de datos.

---

## Estado de ejecución

- [x] **Fase 1 — Textos globales** (commit tras `fd51354`): valor dentro del input editable,
  contador real (15/40…), título "Textos globales". Validado con captura vs mockup.
- [x] **Fase 2.2 — capitalización headers**: títulos de header de módulo del Suite a
  sentence case en `shared/suite_text_catalog.py` + fallback `_MODULE_UI_META` en
  `app/main_qt.py`. Los tabs del Hub (hardcodeados Title Case) NO se tocan: coinciden
  con su propio mockup. Validado con captura.
- [ ] Fase 2.3 — segmented seleccionado
- [ ] Fase 2.4 — checkbox rutina
- [ ] Fase 3 — pulido (5-9)

## Notas

- ⚠️ Defecto **pre-existente** (no de estas fases) detectado al correr la suite:
  `tests/test_hub_visual_contract.py::test_hub_activacion_empty_state_uses_compact_icon_card`
  falla — el empty state de Activación Conductual del Hub no expone el widget
  `ActivationEmptyState`. Revisar aparte (`hub/plan_terapeutico.py`).
