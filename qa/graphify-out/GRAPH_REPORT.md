# Graph Report - qa  (2026-06-27)

## Corpus Check
- 49 files · ~931,329 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 729 nodes · 1008 edges · 59 communities (41 shown, 18 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3c61045b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 58|Community 58]]

## God Nodes (most connected - your core abstractions)
1. `_drain()` - 43 edges
2. `path` - 42 edges
3. `Visual Loop Log — iteración app real ↔ mockup` - 31 edges
4. `Iteraciones` - 30 edges
5. `_module_target()` - 20 edges
6. `Iteraciones` - 16 edges
7. `main()` - 14 edges
8. `Estado inicial (pre-loop)` - 14 edges
9. `COVERAGE GAPS AUDIT — nm_suite (post-calibración spec_generator)` - 13 edges
10. `1. Tests CORRECTOS (test value == mockup, contrato vigente, no tocar)` - 13 edges

## Surprising Connections (you probably didn't know these)
- `_ast_extract_dict_keys()` --references--> `path`  [EXTRACTED]
  capture_v8.py → pack canonico/generate_captures.js
- `_ast_extract_list_tuples_first()` --references--> `path`  [EXTRACTED]
  capture_v8.py → pack canonico/generate_captures.js
- `_ast_extract_add_section_ids()` --references--> `path`  [EXTRACTED]
  capture_v8.py → pack canonico/generate_captures.js
- `_sha256_file()` --references--> `path`  [EXTRACTED]
  capture_v8.py → pack canonico/generate_captures.js
- `_content_metrics()` --references--> `path`  [EXTRACTED]
  capture_v8.py → pack canonico/generate_captures.js

## Import Cycles
- 1-file cycle: `pack canonico/generate_captures.js -> pack canonico/generate_captures.js`

## Communities (59 total, 18 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (32): _ast_extract_add_section_ids(), _ast_extract_dict_keys(), _ast_extract_list_tuples_first(), _acceptance_status(), _capture_evidence_failures(), CaptureName, compare(), compare_legacy() (+24 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (40): 1.1 Introspección (renderer-independent), 1.1 Re-regeneración + cross-check, 1.1 Selectores mockup con `box-shadow`, 1.2 Cross-check contra inventario de introspección, 1.2 Verificador de imagen (image-based), 1.2 Áreas ciegas del VAS (no cubiertas), 1.3 Análisis de los 172 COLOR_MISMATCH, 1.3 Búsqueda de "TODO/FIXME/HACK" en código (+32 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (40): ndarray, _compute_gap(), _dominant_icon_color(), _dominant_text_color(), generate_spec_for_mockup(), _is_dark_image(), main(), _merge_regions_pct() (+32 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (30): Confirmación explícita final, Confirmación explícita final, Convención de entradas, DIFERIDOS cerrados en sesión 2026-06-24 v2 (LOOP_LOG_2.md), DIFERIDOS que quedan al cierre de v2 (con justificación explícita), Estado inicial (baseline pre-loop), Iter 30 — DBT Ahora: icono "Comunicarme con claridad", Iter 31 — Avisos: separador · antes de recurrencia (+22 more)

### Community 4 - "Community 4"
Cohesion: 0.10
Nodes (30): _actividades_force_empty(), _avisos_complete_first(), _avisos_filter_activos(), _avisos_filter_hoy(), _avisos_force_empty(), _avisos_search(), _dbt_go_to_closure(), _dbt_go_to_step_2() (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (30): Iter 10 — Animo stat card: value + subtitle copy, Iter 11 — Rutina banner: subtitle copy, Iter 12 — Activación conductual: voseo + "de forma", Iter 13 — DBT: "superar la crisis" (artículo), Iter 14 — Home: glow radial en hero card, Iter 15 — Respiración: chips de duración centrados, Iter 16 — DBT: copy "Acción opuesta" y "DEAR MAN", Iter 17 — (sin commit separado — incluido en iter 16) (+22 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (26): Confirmación explícita al cierre de sesión anterior (parcial), Convención de entradas, DIFERIDOS cerrados en sesión 2026-06-24 v2 (LOOP_LOG_2.md), DIFERIDOS que quedan al cierre de v2 (con justificación explícita), Estado inicial (baseline pre-loop), Estado inicial (pre-loop), Iter 1 — Avisos search: tab pill activo "Todos" sobre-estirado (106 → 72 px), Iter 47 — Home hero glow con color brand (visible) (+18 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (26): _apply_global_style(), _capture_app_session(), _capture_contract(), _capture_matrix_in_subprocesses(), _clean_output(), _discover_all_view_ids(), _format_size(), _git_metadata() (+18 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (24): 1. Distribución de Decisiones, 2. Causa Raíz #1: Guardrail de BBox Dominante (Líneas 553, 992-1152), 3. Causa Raíz #2: Clasificación Demasiado Defensiva en Tema Light (Líneas 1004-1024), 4. Causa Raíz #3: CHROME_MISMATCH No Produce Decision Accionable (Líneas 1046-1053), 5. Causa Raíz #4: changed_pixel_ratio No Se Usa en la Decisión, 6. Causa Raíz #5: diff_fidelity vs V3 No Está Integrado, 7. Propuestas de Fix, 8. Conclusiones (+16 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (22): _detalle_open_resumen_ia_dialog(), _matrix_review_result(), _matrix_rows(), _md_cell(), _plan_set_subtab(), qa/capture_v8.py — Exhaustive PyQt6 offscreen capture harness.  Descubre dinam, Abre el dialogo 'Resumen IA' del detalle con texto de muestra.      En runtime, Selecciona un subtab del Plan terapéutico (index en la action). (+14 more)

### Community 10 - "Community 10"
Cohesion: 0.16
Nodes (21): Any, Host con el canvas del tema para editores que en producto viven     embebidos (, _wrap_standalone_canvas(), QWidget, audit_tree(), _contract_card_shadow(), _contract_gradient_when_specified(), _contract_playbutton_shadow() (+13 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (35): 10.1. Método, 10.2. Hallazgo central: spec-staleness FPs, 10.3. Casos con divergencia real (no spec-staleness), 10.4. SHADOW_MISMATCH — detección insuficiente en dark mode, 10.5. Conclusión y estado de Option 2, 10. Deep-dive dark theme COLOR_MISMATCH — diagnóstico definitivo (2026-06-27), 11.1. Baseline → resultado, 11.2. Fixes implementados en qa/spec_generator.py (+27 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (23): Capturas V8, cProfile (top tottime durante construcción de ventana), DB init (no medido en QA mode, análisis estático), Event loop blocks, Fase 1 — Mediciones baseline, Fase 2 — Fixes descartados (sin evidencia suficiente o fuera de scope), Fase 2 — Fixes planificados (en orden de mayor impacto), Fase 4 — Registro de fixes (+15 more)

### Community 13 - "Community 13"
Cohesion: 0.09
Nodes (21): Consolidación cross-log (verificación final 2026-06-24 v2), Convención de entradas, DIFERIDOS CERRADOS en esta sesión, DIFERIDOS cerrados por iteración v2 (62–73), DIFERIDOS QUE QUEDAN (con justificación de no acción), DIFERIDOS únicos (consolidado de los 3 logs al cierre de v2), Estado inicial, Iter 62 — Avisos: "Salud" category color danger → brand (visible) (+13 more)

### Community 14 - "Community 14"
Cohesion: 0.31
Nodes (8): analyze(), find_avatar_orange_row(), find_first_green_row(), find_horizontal_borders(), Mide SOLO coordenadas Y de los bloques principales: - top del header paciente (h, Devuelve lista de filas con borde horizontal (>= min_run pixeles diferentes)., Encuentra primera fila donde aparece el botón verde primario., Avatar típico: rounded square color naranja/marrón.     Buscar pixel naranja (R>

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (19): 1. Tests CORRECTOS (test value == mockup, contrato vigente, no tocar), 2. Tests FUNCTIONALES (asserts behavior, no value — no tocar nunca), 3. Tests OBSOLETOS (test value contradice mockup — proponer actualización, NO aplicar todavía), 4. Tests PINNED-IMPL (asserts literales de CSS/source — frágil a theme rotation), 5. Conclusión, Auditoría de tests visuales legacy contra el mockup canónico, Resumen ejecutivo, `test_actividades_visual_contract.py` (4 tests) (+11 more)

### Community 16 - "Community 16"
Cohesion: 0.24
Nodes (10): Namespace, cmd_verify(), cmd_verify_all(), ColorSpec, Divergence, _load_specs(), Run every applicable check for one component.          Returns (checks_passed, d, RegionSpec (+2 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (18): Aplicación del template no-vision del skill, Bloqueador para entrar al loop, Ciclo 1 — surface `suite:avisos-search:light` (turno 4), Ciclo 2 — surface `suite:respiracion-idle:light` (REVERTIDO), Ciclos, Commits de la sesión, Commits de la sesión (actualizado), Decisión (+10 more)

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (15): 1. Home (suite-home-*, suite-home-no-score-*), 2. Actividades (suite-actividades-*), 3. DBT Library (suite-dbt-library-*), 4. Avisos Search (suite-avisos-search-*), 5. Registro Success (suite-registro-success-*), 6. Onboarding / Recuperar (suite-onboarding-*, suite-recuperar-acceso-*), Coherencia entre estados hermanos, Comandos (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (13): Contexto de la pasada, Discrepancias Sentinel (app real) vs mockup canónico, Leyenda de gravedad, Listado por superficie (12 principales, light), Patrones sistemáticos, Síntesis, Estado de ejecución, FASE 1 — Defecto funcional (bloqueante) 🔴 (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (14): Cierre de sesión (al pausar), Convención de entradas, DIFERIDOS únicos consolidados (heredados de v1+v2, sin fix aplicado en esta sesión aún), Estado inicial (baseline pre-loop), Fase de migración controlada de tests obsoletos (post-audit), Iter 74 — Audit preflight Hub · Pacientes (sin código; baseline + observación), Iter 75 — Migración test_rutina_add_done_and_empty_states_match_mockup (mockup l.929), Iter 76 — Migración test_registro_tcc_stepper_otro_and_final_cta_match_mockup (mockup l.1241+l.1261) (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (13): all_captured, all_sizes_match, captures, expected_captures, generator, mockup, size_mismatches, surfaces (+5 more)

### Community 22 - "Community 22"
Cohesion: 0.15
Nodes (14): _actividades_filter_category(), _actividades_filter_fisica(), _execute_actions(), _find_widget(), _is_dialog_or_auxiliary_widget(), _navigate_hub(), _navigate_suite(), _norm_text() (+6 more)

### Community 23 - "Community 23"
Cohesion: 0.14
Nodes (13): all_captured, all_sizes_match, captures, expected_captures, generator, mockup, size_mismatches, surfaces (+5 more)

### Community 24 - "Community 24"
Cohesion: 0.22
Nodes (8): Calibración honesta odiff (puntos owner 1+3), Deuda real encontrada, Fase 5 — Cierre (5.D: cerrar y mantener), Gates por fase, OCR (punto owner 5), Pendiente owner, RESTRUCTURE_RESULTS — Fase 4 (medición), Timing (86 superficies, app constante)

### Community 25 - "Community 25"
Cohesion: 0.15
Nodes (12): Aclaración, Archivos de herramienta, Commits de esta limpieza, Outputs regenerables (ya estaban gitignored, borrados del disco), Por qué se elimina, Qué NO se conserva (eliminado), Qué se conserva, Qué se eliminó (+4 more)

### Community 26 - "Community 26"
Cohesion: 0.21
Nodes (12): _append_flag(), _append_note(), _apply_content_validation(), _choose_status(), _classify_initial_result(), _content_metrics(), _finalize_evidence(), _mark_duplicate_groups() (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.32
Nodes (12): _drain(), _git_head(), main(), _navigate(), _probe_one(), qa/runtime_live_probe.py — read-only runtime evidence probe.  Distinta de `qa/, _run_child(), _short() (+4 more)

### Community 28 - "Community 28"
Cohesion: 0.25
Nodes (10): captureView(), crypto, fs, parseSize(), pngDims(), puppeteer, sha256(), sleep() (+2 more)

### Community 29 - "Community 29"
Cohesion: 0.22
Nodes (8): Confirmación, Diagnóstico inicial, Estado final, Estado inicial (2026-06-24), Iteraciones, Iteración 1 — 13 aliases V8→mockup, LOOP_LOG_5.md — Reducción de MISSING_REFERENCE en Sentinel audit-mockup, SHA inicial

### Community 30 - "Community 30"
Cohesion: 0.33
Nodes (5): Auditoría visual POST-FIX — pantalla por pantalla vs mockup, Conclusión honesta (sin PASS global), Corrección posterior (Pacientes), Severidad, Tabla

### Community 31 - "Community 31"
Cohesion: 0.33
Nodes (5): Ciclos, Convenciones, Estado inicial, LOOP_LOG_4 — Reducción controlada de discrepancias visuales, Meta

### Community 33 - "Community 33"
Cohesion: 0.43
Nodes (6): classify_preliminary(), load_fidelity(), load_vas(), main(), Cross-gate matrix: odiff FIDELITY_REPORT vs visual_auditor_spec report.  Classif, Return preliminary classification string.

### Community 34 - "Community 34"
Cohesion: 0.33
Nodes (5): Category B — odiff PASS + VAS FAIL (critical zone), Cross-Gate Matrix: odiff vs VAS, Full Matrix, Summary, Top 10 Critical Surfaces

### Community 35 - "Community 35"
Cohesion: 0.40
Nodes (4): find_card_left_edge(), find_card_right_edge(), Encuentra el último pixel de la form col empezando desde x_start., Encuentra el primer pixel del body card desde x_start.

### Community 42 - "Community 42"
Cohesion: 0.50
Nodes (3): card_edges_per_row(), Encuentra los bordes de las cards principales (hero, tabs, body cards). Estrateg, Encuentra los x donde la fila cruza un borde de card (cambio de color sostenido)

### Community 44 - "Community 44"
Cohesion: 0.50
Nodes (3): find_left_card_edge(), Medir el padding lateral REAL del canonical en todas las superficies hub-detalle, Encuentra el primer pixel que NO es bg-ventana empezando desde x=0.

## Knowledge Gaps
- **332 isolated node(s):** `generator`, `mockup`, `total_captures`, `expected_captures`, `all_captured` (+327 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `path` connect `Community 0` to `Community 2`, `Community 7`, `Community 9`, `Community 16`, `Community 22`, `Community 26`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `generate_spec_for_mockup()` connect `Community 2` to `Community 0`, `Community 10`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Why does `_finalize_evidence()` connect `Community 26` to `Community 0`, `Community 9`, `Community 10`, `Community 7`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **What connects `generator`, `mockup`, `total_captures` to the rest of the system?**
  _415 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.13445378151260504 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.04878048780487805 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.0859465737514518 - nodes in this community are weakly interconnected._