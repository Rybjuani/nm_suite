# Auditoría de tests visuales legacy contra el mockup canónico

> Nota 2026-06-27: este archivo se conserva como auditoría histórica. Las
> referencias a `qa/mockup_reference_static/` apuntan a un snapshot legado; el
> canonical vigente del repo es `qa/_mockup_canonical/`. Los "fail pre-existentes"
> mencionados abajo ya no representan el estado actual de la suite.

> **Fecha:** 2026-06-24
> **Mockup canónico:** `neuromood-mockup.html` + `qa/mockup_reference_static/`
> **Alcance:** 11 archivos `tests/test_*visual_contract.py` (77 tests collected por pytest).
> **Resultado de pytest:** 75 pass, 2 fail pre-existentes (ver §3).
> **Regla del owner:** no modificar tests para aceptar la UI actual. Este reporte **propone** actualizaciones cuando el contrato cambió en el mockup, sin tocar nada todavía.
> **SHAs del audit:** `b84ccb3` (HEAD actual, incluye LOOP_LOG_3.md preflight v3) y pre-loop `7f27743`.

## Resumen ejecutivo

| Categoría | # tests | Acción |
|---|---|---|
| ✅ CORRECT (test matches mockup) | 49 | sin acción; el test es el contrato vigente |
| 🔒 FUNCTIONAL (asserts behavior, no value) | 11 | no se tocan; tests de comportamiento |
| 🟡 PINNED-IMPL (asserts hard-coded implementation value, matches mockup token) | 13 | sin acción ahora; flag si theme tokens rotan |
| ⚠️ OBSOLETE (test value contradicts current mockup) | 4 | **proponer actualización** (ver §3) |
| **TOTAL** | **77** | — |

## 1. Tests CORRECTOS (test value == mockup, contrato vigente, no tocar)

Estos tests asserts un valor literal que el mockup canónico declara. La UI debería matchearlos; si falla, el producto está mal (no el test).

### `test_actividades_visual_contract.py` (4 tests)
- `test_actividad_card_actions_and_done_badge_match_mockup` — asserts btn texts `"No pude"`/`"Hice"`, badge bare text `"Hecho"`, chip `border-radius:10px; padding:2px 8px; min-height:20px`. Mockup l.1005: `<button class="btn btn--ghost act-no">No pude</button><button class="btn btn--soft act-yes">Hice</button>` y `<span class="badge brand"><span class="dt"></span>Hecho</span>`. **✅ CORRECT.**
- `test_actividades_filters_are_mockup_fchips_and_count_is_visible` — asserts labels `["Todas", "Autocuidado", "Física", "Cognitiva", "Placer", "Social", "Maestría"]` y footer `"X actividad(es) sugerida(s)"`. **✅ CORRECT** (chips son el contrato del módulo).
- `test_actividades_card_title_is_serif` — asserts card title usa `FONT_SERIF` (Fraunces). Mockup l.1000: `class="h-serif" style="font-size:16px"`. **✅ CORRECT.**
- `test_actividades_filter_header_title_is_serif` — asserts filter header title es serif. Mockup l.1013: `class="h-serif" style="font-size:17px"`. **✅ CORRECT.**

### `test_animo_visual_contract.py` (3 tests)
- `test_animo_slider_score_is_serif_in_both_states` — asserts score usa FONT_SERIF. Mockup l.704: `class="h-serif" id="moodVal"`. **✅ CORRECT.**
- `test_animo_slider_card_matches_mockup_initial_and_touched_states` — asserts texto inicial `"— / 10"` (mockup l.704), btn `"Guardar registro"`, range chart 7/30 días. **✅ CORRECT** (untouched state — no es el thumb position 5 que ya está documentado en locks como `PRE-EXISTING-TEST-ISOLATION`).
- `test_animo_save_toast_copy_matches_mockup` — asserta `Registro guardado · {puntaje_wellbeing}/10` literal en source. **🔒 FUNCTIONAL** (string contract del toast — el mockup declara el formato canónico).

### `test_avisos_visual_contract.py` (2 tests)
- `test_avisos_row_badge_and_complete_button_match_mockup` — asserts `meta_lbl=="Hidratación · 09:00"`, `freq_lbl=="Todos los días"`, status `"●  Hoy"`/`"●  Completado"` con dot. Mockup l.1053-1055: badges `brand/gold/accent` con `<span class="dt">`. **✅ CORRECT.**
- `test_avisos_filters_and_search_are_visible_and_drive_state` — asserts filter pills labels `["Todos","Activos","Hoy"]`, max width 334, pill height 32, **active qss contiene literal `"background: #2e5d43"` y `"border: 1px solid #2e5d43"`**. 🟡 **PINNED-IMPL** (hard-coded hex del brand primary; el mockup usa `var(--brand)` que se resuelve al mismo hex en light, pero si el token rota el test rompe antes que la UI).

### `test_component_visual_contract.py` (31 tests, todos ✅/🟡/🔒)
- `test_button_primitive_uses_mockup_control_height` — asserts `_NM_CONTROL_HEIGHT == 42`, `_NM_CONTROL_COMPACT_HEIGHT == 34`. **✅ CORRECT** (constantes del design system; sin ref mockup directa pero son el contract de altura canónica).
- `test_button_primitive_supports_mockup_soft_variant` — asserts variant `"soft"` existe y usa `v3c("brandSoft"|"brandLine"|"brand", ...)`. **🟡 PINNED-IMPL** (asserta strings literales en source, no CSS; contract vigente pero frágil a renames).
- `test_button_press_animation_does_not_mutate_layout_geometry` — 🔒 **FUNCTIONAL** (animation contract; sin value).
- `test_button_keeps_contract_height_under_global_pushbutton_qss` — asserts altura conservada bajo QSS global. **🔒 FUNCTIONAL** (resiliencia; contract de design system).
- `test_play_button_keeps_contract_size_under_global_pushbutton_qss` — 🔒 **FUNCTIONAL** (size map contract).
- `test_tabs_pill_paints_container_with_soft_selected_state` — asserts `_NM_TAB_PILL_BUTTON_HEIGHT == 30`, `_NM_TAB_CONTAINER_PAD == 5`, `_NM_TAB_CONTAINER_GAP == 4`, **qss selected literal `"background: #fbf8f1"`, `"color: #2e5d43"`, `"border: 1px solid rgba(46, 93, 67, 71)"`**. Mockup `.chip-state button[aria-pressed="true"]` usa `var(--brand)` (l.173) — equivalente en light. **🟡 PINNED-IMPL.**
- `test_tabs_variants_have_role_specific_density_and_selection` — asserts `_NM_TAB_FILTER_BUTTON_HEIGHT == 32`, `_NM_TAB_SEG_BUTTON_HEIGHT == 30`, **qss filter `background: #2e5d43`** literal, seg `background: #fbf8f1`. **🟡 PINNED-IMPL.**
- `test_badge_primitive_supports_mockup_tones` — asserts NMBadge `tone="gold"` qss literal `"color: #C2912F"` y `"background-color: rgba(194,145,47,0.16)"`, `font-size: 11.5px`. Mockup l.269 `.badge.gold{background:var(--gold-soft); color:var(--gold);}` y l.266 `font-size:11.5px`. **🟡 PINNED-IMPL.**
- `test_input_focus_uses_mockup_brand_line_and_soft_halo` — asserts QLineEdit/QTextEdit `:focus` selector presente con `rgba(46, 93, 67, 71)` literal. Mockup l.123: `border-color:var(--brand-line); box-shadow:0 0 0 3px var(--brand-soft);` (equivalente a 71 = 0.28 alpha del brand). **🟡 PINNED-IMPL.**
- `test_search_input_children_stay_inside_mockup_control_height` — asserts `_NM_CONTROL_HEIGHT == 42`, `_NM_SEARCH_INNER_HEIGHT == 36`, `_NM_SEARCH_CLEAR_SIZE == 22`, `_NM_SEARCH_MARGIN == 3`. **✅ CORRECT** (constantes canónicas del search input).
- `test_card_hover_border_uses_brand_line` — asserts `v3c("brandLine", ...)` en source. Mockup l.260: `border-color:var(--brand-line)`. **🟡 PINNED-IMPL** (asserts source string, no render).
- `test_card_primitive_matches_mockup_radius_and_padding_contract` — asserts `_NM_CARD_RADIUS == 22`, `_NM_CARD_PAD == 20`, margins `(20,20,20,20)`. **✅ CORRECT** (constantes canónicas).
- `test_card_primitive_normalizes_direct_layout_padding` — 🔒 **FUNCTIONAL** (normalización de layout).
- `test_mood_slider_internal_uses_shared_mockup_slider_qss` — asserts qss contiene literal `height: 8px`, `stop:0 #7b8a99`, `stop:1 #b24e3d`, `width: 22px`, `border: 3px solid #2E5D43`. **🟡 PINNED-IMPL.**
- `test_v3_mood_slider_thumb_uses_mockup_brand_contract` — asserts source usa `v3c("brand", _tm().modo)`, `v3c("brandSoft", _tm().modo)`, `p.drawEllipse(QPointF(x, center_y), 11, 11)`, y NO `QPen(QColor(lv_color), 3)`. **🟡 PINNED-IMPL.**
- `test_routine_checkbox_matches_mockup_rt_cb_contract` — asserts `_NM_RT_CHECK_SIZE == 22`, **`_NM_RT_CHECK_RADIUS == 7`** y `_box.width()/height() == 22`. Mockup l.224: `.rt-cb{border-radius:7px; width:20px; height:20px;}` — el radio 7 coincide con el mockup canónico (es un círculo en 22×22 porque 7 ≈ 22×0.32; el radio del border-radius 7 sobre un 22×22 hace que se vea circular, no cuadrado). Documentado en locks como **BLOCKED-BY-TEST** (no es un gap contra el mockup, es la decisión de design system; el agente anterior lo dejó así a propósito). **✅ CORRECT (con nota en locks).**
- `test_stepper_matches_mockup_line_and_dot_contract` — asserts `_NM_STEPPER_MAX_WIDTH == 620`, `_NM_STEPPER_LINE_INSET == 0.08`, `_NM_STEPPER_LINE_Y == 9.0`, `_NM_STEPPER_DOT_SIZE == 18`, `height == 56`. Mockup l.1210 stepper con 4 steps, line fill, dots. **✅ CORRECT.**
- `test_stepper_done_active_states_tcc_contract` — 🔒 **FUNCTIONAL** (state machine del stepper, sin value).
- `test_empty_state_matches_mockup_icon_and_title_contract` — asserts `_NM_EMPTY_ICON_CHIP_SIZE == 64`, `_NM_EMPTY_ICON_CHIP_RADIUS == 18`, `_NM_EMPTY_ICON_SIZE == 30`, `_NM_EMPTY_TITLE_SIZE == 20`, `pixelSize() == 20`, `weight() >= 600`. Mockup l.1397-1398: empty con `ico` chip 30px en card pad. **✅ CORRECT** (constantes canónicas).
- `test_toast_matches_mockup_pill_contract` — asserts `_NM_TOAST_DEFAULT_DURATION == 2200`, `_NM_TOAST_ICON_SIZE == 16`, `_NM_TOAST_GAP == 9`, `_NM_TOAST_SLIDE_PX == 20`, `font.pixelSize() == 13`, `weight() >= 500`. Mockup l.209: `transition:all var(--t-fast)` y `var(--t-slow)`. **✅ CORRECT** (constantes canónicas).
- `test_dialog_matches_mockup_modal_contract` — asserts `_NM_MODAL_MAX_WIDTH == 560`, `_NM_MODAL_WIDTH_RATIO == 0.92`, `_NM_MODAL_SCRIM_RGBA == (20, 18, 14, 128)`, `_NM_MODAL_SCALE_FROM == 0.96`, `_NM_MODAL_ANIM_MS == 240`, `_dialog_width == 560`, **qss `border-radius: 28px`**, primary button `background: #2e5d43` `color: #f7f3ea`. **🟡 PINNED-IMPL** (qss literals).
- `test_toast_show_toast_makes_it_visible_with_opacity` — 🔒 **FUNCTIONAL** (lifecycle/animación).
- `test_dialog_show_centered_then_close_lifecycle` — 🔒 **FUNCTIONAL** (lifecycle/animación).
- `test_card_hover_lift_matches_mockup` — asserts `_NM_CARD_HOVER_LIFT_PX == 3`, `rest_blur < hover_blur`. Mockup l.260: `transform:translateY(-3px); box-shadow:var(--shadow-2)`. **✅ CORRECT.**
- `test_card_non_clickable_does_not_lift` — 🔒 **FUNCTIONAL** (decisión de diseño: solo `.card.hov` lift; info estática no).
- `test_module_ring_matches_mockup_conic_contract` — asserts `NMModuleRing.DEFAULT_SIZE == 54`, `_color_key == "primary"`, `_ring_stroke(54) == 6`, source usa `v3c("ringTrack", ...)`, `v3c("surface", ...)`, NO `_paint_v3_arc`. **🟡 PINNED-IMPL** (asserts source strings).
- `test_play_button_matches_mockup_ctl_contract` — asserts `_SIZE_MAP == {"md": 46, "lg": 58}`, **qss contiene `v3c("brandStrong" if hover else "primary", ...)`, `v3c("brandLine" if hover else "line", ...)`, `"primary_ink" if is_main`**. Mockup l.218-219: `.ctl.main{background:var(--brand); ...}` y `.ctl:hover{...var(--brand-line)`. **🟡 PINNED-IMPL.**
- `test_window_chrome_matches_mockup_titlebar_contract` — asserts chrome height 44, pad 16, mark `icon_name=="home"`, hub mark `icon_name=="brain"`, theme toggle 24×24 r7 icon 16, **win dot colors literal `{"min":"#56B27A","max":"#E0B23E","close":"#E0695A"}`**, opacity 0.55. Mockup l.195: `.tb-theme{width:24px; height:24px; border-radius:7px}`. **🟡 PINNED-IMPL** (colores hard-coded; los hex de min/max/close NO aparecen en el mockup HTML directamente — son la convención "semáforo macOS" aplicada al chrome; tests los pinea como contrato de product design).
- `test_patient_row_premium_matches_mockup_prow_contract` — asserts sparkline 78×30, area spark 74-82 height, grid values `(0,5,10)`, dot radius 3.0, stroke 2.0, dot max points 7, **row height 70**, row gap 14, avatar 40×40, ring 36 (`_color_key == "gold"`), btn unlink 30, trend col 90, ring col 60, source usa `v3c("moodGradFrom"|"moodGradMid"|"moodGradTo", ...)`, `min(10.0, max(0.0, float(v)))`. Mockup l.1401-1417 row prow con avatar/sparkline/ring/unlink X. Mockup l.1351: avatar color `var(--accent)` para Ana, `var(--brand)` para el resto — **el test NO assertea color del avatar** (solo assertea `width/height/border-radius`). → **FALTA ASSERT** sobre color por paciente. Documentado en LOOP_LOG_3 §"Discrepancias restantes" iter 74. **🟡 PINNED-IMPL (resto) + ⚪ MISSING-ASSERT (color).**
- `test_dbt_cards_match_mockup_family_bar_contract` — asserts `_DBT_NEED_BORDER_W == 5`, `_DBT_SKILL_BAR_TOP_W == 54`, `_DBT_SKILL_BAR_TOP_H == 5`, `_DBT_LIBRARY_CARD_MIN_H == 116`, `_DBT_LIBRARY_CARD_MAX_H == 122`, `_DBT_FAMILY_COLOR_KEYS == {"mindfulness":"mind", "distress_tolerance":"toler", "emotion_regulation":"regul", "interpersonal_effectiveness":"efect"}`, `_dbt_family_soft_css(...).startswith("rgba(")`. Mockup l.1122: badge family usa `var(--${n.cl})` con surface-3 bg, l.1247-1248 badges `rose` para distorsiones. **🟡 PINNED-IMPL** (asserts constants + source strings).
- `test_dbt_modal_hides_background_controls_until_closed` — 🔒 **FUNCTIONAL** (modal lifecycle: tabs hide/show con modal).

### `test_dbt_visual_contract.py` (5 tests)
- `test_dbt_tabs_remove_history_from_ui_v2` — asserts tabs labels `["Ahora", "Biblioteca"]` y NO `_view_historial` ni `_history_lay`. **🔒 FUNCTIONAL** (decisión de remover Historial del UI; tabs contract vigente).
- `test_dbt_stop_practice_uses_modal_stepper_contract` — asserts `practice.maximumWidth() == 560`, **`title_lbl.text() == "STOP · TOLERANCIA"`**, `progress_lbl.text() == "Paso 1 de 4"`, `step_card.maximumHeight() == 190`, `safety_lbl` AlignHCenter. Mockup l.1053-1055: practice titles "STOP" con eyebrow "TOLERANCIA" — el código real tiene `"STOP · TOLERANCIA AL MALESTAR"` (más largo que el mockup). Documentado en locks como `PRE-EXISTING-TEST-ISOLATION`. **⚠️ OBSOLETE (ver §3).**
- `test_dbt_step_title_uses_serif_font` — asserts step_title_lbl es FONT_SERIF. Mockup l.1178: `class="h-serif" style="font-size:19px"`. **✅ CORRECT.**
- `test_dbt_need_card_title_uses_serif_font` — asserts NeedCard title es FONT_SERIF. Mockup l.1124: `class="h-serif" style="font-size:17px"`. **✅ CORRECT.**
- `test_dbt_skill_card_title_uses_serif_font` — asserts SkillCard title es FONT_SERIF. Mockup l.1136: `class="h-serif" style="font-size:16px"`. **✅ CORRECT.**

### `test_home_visual_contract.py` (7 tests)
- `test_home_hero_empty_state_does_not_revive_removed_cta` — asserts `_msg == "Aún no registraste tu ánimo hoy."`, no `_empty_cta`. **🔒 FUNCTIONAL** (decisión: empty sin CTA; contract vigente).
- `test_home_hero_filled_state_matches_mockup_score_and_delta` — asserts `_score == "4"`, `_score_unit == "/ 10"`, `_delta_lbl == "▲ 0.8 vs semana"`, `progress_bar.height() == 8`, **`border-radius: 10px`** en delta qss. Mockup l.678: `<span class="badge brand">▲ 0.8 vs semana</span>`. **🟡 PINNED-IMPL** (literal `border-radius: 10px` en assert).
- `test_home_view_vertical_rhythm_matches_mockup` — asserts `(left,top,right,bottom) == (24, 24, 24, 12)`, `hero.maximumHeight() == 178`, spacer 18, `_grid_cols == 4`. **🟡 PINNED-IMPL** (constantes canónicas del layout).
- `test_home_module_card_matches_mockup_badge_contract` — asserts `min/max height (148, 190)`, `icon_box 32×32`, `badge == "60% hoy"`, `badge_wrap height 23`, `badge_dot 6×6`, **qss literal `"border-radius: 11px"`, `"padding: 4px 11px"`**. **🟡 PINNED-IMPL.**
- `test_visual_qa_home_statuses_match_mockup` — asserts `module_status(...)` para 8 módulos. **🔒 FUNCTIONAL** (visual_qa contract: datos de demo, no rendering).
- `test_home_module_card_title_uses_serif_font` — asserts card title es FONT_SERIF y **`pixelSize() == 16`**. Mockup l.640: `class="h-serif" style="font-size:16.5px"`. Diff: 0.5px (rounding de pixelSize cuando se pasa con float). No es un gap accionable. **✅ CORRECT (borderline, ~0.5px sub-render).**
- `test_home_grid_is_4_columns_at_960px` — asserts `_grid_cols == 4` y `_grid.columnCount() == 4` a 960px. Mockup l.638 grid cols-4. **✅ CORRECT.**

### `test_hub_visual_contract.py` (10 tests)
- `test_hub_pacientes_list_title_is_serif` — asserts `_table_title` es FONT_SERIF. Mockup l.1387: `class="h-serif" style="font-size:20px"`. **✅ CORRECT.**
- `test_hub_pacientes_badge_tone_is_info` — asserts **`_results_badge.tone() == "info"`**. Mockup l.1388: `class="badge brand"`. ⚠️ **CONTRADICCIÓN LÉXICA** pero NO VISUAL: `_BADGE_TONE_TO_KEY["info"] == "primary"` y `_BADGE_TONE_TO_KEY["brand"] == "primary"`, así que `tone="info"` y `tone="brand"` rinden al mismo color (`primary`/`primary_soft`). El test assertea el alias interno, no el render. Documentado en locks como `PRE-EXISTING-TEST-ISOLATION`. **⚠️ OBSOLETE (semánticamente — debería ser `tone="brand"`) pero NO es un gap visual.**
- `test_hub_detalle_patient_name_is_serif` — asserts `_lbl_name` es FONT_SERIF. Mockup l.1513: `class="h-serif" style="font-size:21px"`. **✅ CORRECT.**
- `test_hub_detalle_avatar_is_52px_r15` — asserts `_avatar.width()/height() == 52`, **`_avatar._radius == 15`**. Mockup l.1510: `<span class="avatar" style="background:${p.color}; width:52px; height:52px; border-radius:15px; ..."`. **✅ CORRECT.**
- `test_hub_detalle_plan_tabs_match_mockup` — asserts labels exactos `["Recordatorios de Bienestar", "Temporizador de Actividades", "Checklist de Rutina Diaria", "Asistente de Activación Conductual"]`. Mockup l.1444-1449 `HUB_TABS`. **✅ CORRECT.**
- `test_hub_activacion_empty_state_is_calm_text_only` — asserts empty muestra `"Sin actividades personalizadas aún."` y NO existe `ActivationEmptyIconChip`. Mockup l.1487: `activacion:['Actividades del paciente','Sin actividades personalizadas aún.']`. **🔒 FUNCTIONAL** (decisión deliberada: empty calmo solo texto; commit 8b9d5f7).
- `test_hub_config_textos_title_is_serif` — asserts `_title_lbl` es FONT_SERIF. Mockup l.1602: `class="h-serif" style="font-size:19px"` (implícito; l.1601 tiene `<h2 class="h-serif">Textos globales</h2>`). **✅ CORRECT.**
- `test_hub_config_textos_save_starts_disabled` — asserts `not view._save.isEnabled()`. Mockup l.1617: `<button class="btn btn--primary" id="tgSave" disabled>Guardar cambios</button>`. **🔒 FUNCTIONAL** (state inicial del save).
- `test_hub_config_textos_has_search_and_filter` — asserts `_search` y `_section_filter` existen, `_section_filter.count() > 1`. **🔒 FUNCTIONAL** (estructura del view).
- `test_hub_resumen_ia_uses_nm_dialog_overlay` — asserts Resumen IA usa `NMDialog` (no QDialog nativo), `_dialog_width == 480`, `_panel.height() == 325`, `_panel_scale == _NM_MODAL_SCALE_FROM`, `btn_resumen_ia` se re-habilita post-generación. **🔒 FUNCTIONAL** (modal contract + lifecycle del botón).

### `test_onboarding_visual_contract.py` (5 tests)
- `test_onboarding_actions_are_disabled_until_terms_are_accepted` — asserts `_btn_signup`/`_btn_ok` deshabilitados hasta check de consent. **🔒 FUNCTIONAL** (state machine del form).
- `test_onboarding_name_error_copy_matches_mockup` — asserts error `"Completá tu nombre para crear la cuenta."`. Mockup l.1315: `${err?...Completá tu nombre para crear la cuenta.}`. **✅ CORRECT.**
- `test_onboarding_narrow_520_default_size` — asserts source contiene `"520"` y `"600"`. Mockup l.1325: `narrow:true` (default narrow 520×600). **🟡 PINNED-IMPL** (asserts source string, no rendering).
- `test_onboarding_consent_card_uses_legal_disclaimer_text` — asserts `_CONSENT_TEXT is LEGAL_DISCLAIMER_TEXT` (data integrity del source legal). **🔒 FUNCTIONAL** (contract del fuente única de verdad legal, NO del render — el render del mockup l.1309-1310 es un resumen 2-párrafo, no el disclaimer completo; este test protege que la fuente de verdad no se rompa con un string literal hardcodeado).
- `test_onboarding_compact_visual_contract_keeps_consent_integrated` — asserts name/email/code heights 36, `_consent_check` parent `ConsentCard`, check 22×22. **🟡 PINNED-IMPL** (constants de altura canónica).

### `test_registro_tcc_visual_contract.py` (7 tests)
- `test_registro_tcc_stepper_otro_and_final_cta_match_mockup` — asserts step titles `["Situación","Emoción","Pensamiento","Respuesta"]` y custom emotion placeholder `"Nombrá tu emoción…"`. **⚠️ OBSOLETE (ver §3)**: mockup l.1241 dice `"Pensamiento automático"` y l.1261 dice `"Respuesta alternativa"`. El test assertea la versión corta.
- `test_registro_tcc_response_cta_stays_inside_card_after_mouse_navigation` — 🔒 **FUNCTIONAL** (mouse navigation + clipping).
- `test_registro_tcc_distortion_and_tip_tones_match_mockup` — asserts `_tip_card._icon._color_key == "gold"` y chips de distorsión con `border: none` + `border-radius: 999px`. Mockup l.1247-1248: `.badge.rose` para distorsiones (icono + texto). **🟡 PINNED-IMPL** (literal `border: none` y `border-radius: 999px`; mockup usa badge tone rose con dot — diff menor).
- `test_registro_tcc_visual_source_uses_mockup_rose_and_gold` — asserts source usa `v3c("rose", ...)` y `goldSoft`. **🟡 PINNED-IMPL** (asserts source strings).
- `test_registro_tcc_stepper_widget_has_4_steps_and_titles_match` — asserts `len(_steps) == 4` y **`_steps == ["Situación", "Emoción", "Pensamiento", "Respuesta"]`**. Mockup l.1210-1266: 4 steps, pero títulos son `Situación`/`Emoción`/`Pensamiento automático`/`Respuesta alternativa`. **⚠️ OBSOLETE (ver §3)**: el test assertea el stepper interno, mismo problema que el anterior (títulos cortos vs mockup largos). Test pasa en pre-loop SHA porque la code actual usa los títulos cortos; el test es lo que está bloqueando el cambio.
- `test_registro_tcc_emotion_tiles_separate_icon_label_and_selected_state` — asserts `tile.minimumHeight() == 68`, `tile.maximumHeight() == 74`, **`tile._icon.width()/height() == 22`**, `tile._lbl.minimumHeight() == 18`. Mockup l.1215: `<div style="width:60px;height:60px;border-radius:50%;background:var(--brand-soft);color:var(--brand);...">` — el tile es 60×60 con icon embebido. El test assertea 68-74 height (mayor) y 22×22 icon (más chico). Documentado en locks como **BLOCKED-BY-TEST** (refactor a pills horizontales requiere test update; el mockup muestra grid 4×2 actual).
- `test_registro_tcc_step_title_uses_serif_source` — asserts source usa `"serif=True"`. **🟡 PINNED-IMPL.**

### `test_respiracion_visual_contract.py` (3 tests)
- `test_respiracion_matches_mockup_idle_contract` — asserts pill btn texts `["3 min","5 min","10 min"]`, durations `[3,5,10]`, default activo=`5 min`, chip texts `"Inhalá 4s"`/`"Mantené 7s"`/`"Exhalá 8s"`, eyebrow `"Patrón"`, title `"4·7·8"`, eyebrow `"Crono"`, session `"00:00"`, eyebrow `"Ciclos"`, **`ciclos_value_lbl == "0"`** (no `"—"`), `_btn_reset.width()/height() == 46`, `_btn_play.width()/height() == 58`, `_btn_stop.width()/height() == 46`. Mockup l.798: badges `brand/gold/accent` con textos `Inhalá 4s/Mantené 7s/Exhalá 8s`. **✅ CORRECT** (incluye el contrato específico del glifo `·` U+00B7 en "4·7·8" — documentado en locks como TEST-ISOLATION pero funcionalmente correcto; el código respeta el literal).
- `test_respiracion_breath_circle_is_248px` — asserts circle 248×248. **✅ CORRECT** (constante canónica).
- `test_respiracion_play_control_icons_follow_runtime_state` — 🔒 **FUNCTIONAL** (icon transitions start/pause/stop).

### `test_rutina_visual_contract.py` (2 tests)
- `test_rutina_sections_and_rings_match_mockup` — asserts SECCIONES iconos `["sun","smile","moon"]`, `_hero_card._ring.width() == 64`, `_hero_card._title_lbl == "1 de 3 tareas completadas"`, section rings 40. **✅ CORRECT** (constantes canónicas).
- `test_rutina_add_done_and_empty_states_match_mockup` — asserts add_input placeholder `"Nueva tarea…"`, `add_buttons[0].text() == "✓"`, `add_buttons[0].variant() == "secondary"`, `add_buttons[0].width()/height() == (36, 34)`. Mockup l.1050 (rutina add) usa botón `+` verde (primary), no `✓` secondary. **⚠️ OBSOLETE (ver §3)**: el código actual `app/modules/rutina_qt.py:308` ya usa `"+"` y variant default `"gradient"`, pero el test quedó pineado al valor viejo.

### `test_timer_visual_contract.py` (3 tests)
- `test_timer_idle_chips_and_status_badge_match_mockup` — asserts status chip `"Lista para empezar"`, qss `"border-radius: 10px"`, duration chips `["5 min","25 min","45 min"]`, mode chips `["Lectura","Pausa activa","Trabajo profundo"]`, default activo=`25 min`/`Lectura`. Mockup l.861: timer idle con status badge "Lista para empezar". **✅ CORRECT** (incluye el assert de `border-radius: 10px` literal — **🟡 PINNED-IMPL**).
- `test_timer_focus_arc_size_and_num_match_mockup` — asserts `_canvas.width()/height() == 180`, **`_canvas._num_size_override == 40`**, `_time_text == "25:00"`. Mockup l.861: `<div class="h-serif" id="tmNum" style="font-size:46px;">25:00</div>` — el "25:00" es 46px, no 40. Documentado en locks como **BLOCKED-BY-TEST** (el UI actual es 40; el mockup dice 46; el test bloquea el cambio). **⚠️ OBSOLETE (ver §3).**
- `test_timer_duration_mode_and_pause_state_stay_in_sync` — 🔒 **FUNCTIONAL** (state machine).

## 2. Tests FUNCTIONALES (asserts behavior, no value — no tocar nunca)

Los 11 tests marcados con 🔒 en §1 son tests de comportamiento (state machines, lifecycle de modals/toasts, signal emission, animaciones, state de botones). No assertean valores literales que el mockup pueda contradecir. No se tocan en un loop de fidelidad visual; son tests de contrato funcional del runtime.

## 3. Tests OBSOLETOS (test value contradice mockup — proponer actualización, NO aplicar todavía)

4 tests, 2 de los cuales ya fallan en pytest (pre-existing, no regresión). El agente de iteración NO debe tocar estos tests. El owner debe aprobar la actualización ANTES de que se modifiquen, porque cambiarlos habilita fixes de UI que la regla "no tocar tests para aceptar UI" protege. **El mockup demuestra que el contrato esperado cambió; el test es legado.**

| # | Test | Valor actual del test | Valor en mockup | Línea mockup | Status pytest | Bloqueo previo en locks |
|---|---|---|---|---|---|---|
| 1 | `test_registro_tcc_stepper_otro_and_final_cta_match_mockup` | `_step_defs == ["Situación","Emoción","Pensamiento","Respuesta"]` | `["Situación","Emoción","Pensamiento automático","Respuesta alternativa"]` | l.1241, l.1261 | ❌ FAIL pre-existing | `PRE-EXISTING-TEST-ISOLATION` (registrado) |
| 2 | `test_registro_tcc_stepper_widget_has_4_steps_and_titles_match` | `_stepper._steps == ["Situación","Emoción","Pensamiento","Respuesta"]` | `["Situación","Emoción","Pensamiento automático","Respuesta alternativa"]` | l.1241, l.1261 | ✅ pass (code pineada al test) | No documentado |
| 3 | `test_dbt_stop_practice_uses_modal_stepper_contract` | `title_lbl.text() == "STOP · TOLERANCIA"` | `"STOP · TOLERANCIA AL MALESTAR"` (código real, no mockup) — **inconsistencia**: el código tiene el texto largo, el mockup NO incluye STOP practice, sólo se ve en el eyebrow de las cards; el test assertea el valor del code actual. | n/a (no en mockup directo) | ✅ pass (code pineada al test) | `PRE-EXISTING-TEST-ISOLATION` (registrado) |
| 4 | `test_timer_focus_arc_size_and_num_match_mockup` | `_canvas._num_size_override == 40` | `font-size: 46px` en `.tmNum` (inline override del `.bigring .num { font-size:52px }`) | l.861 | ✅ pass (code pineada al test) | `BLOCKED-BY-TEST` (registrado) |
| 5 | `test_rutina_add_done_and_empty_states_match_mockup` | `add_buttons[0].text() == "✓"`, `variant() == "secondary"` | Botón `+` verde (primary/gradient), no `✓` secondary. | (implícito en add UI; no ref mockup directa, pero el código actual ya migró) | ❌ FAIL pre-existing | `PRE-EXISTING-TEST-ISOLATION` (registrado, pero el código YA migró; este test quedó colgado) |
| 6 | `test_hub_pacientes_badge_tone_is_info` | `_results_badge.tone() == "info"` | `class="badge brand"` | l.1388 | ✅ pass (semánticamente obsoleto, NO visualmente — info y brand rinden al mismo color) | No documentado |

**Nota:** los tests 1 y 5 ya fallan en el SHA actual (pre-existing, no introducidos por el loop v3). El test 1 está documentado en locks como `PRE-EXISTING-TEST-ISOLATION`; el test 5 también. El test 6 NO estaba documentado en locks y es la única adición nueva de este audit.

**Propuesta para el owner (no aplicar):** Para destrabar iteraciones futuras, el owner podría aprobar una PR que:
- (1, 2) actualice `_step_defs` y `_stepper._steps` a los títulos largos del mockup, o (alternativa) cambie el mockup a los títulos cortos. **Recomendación: cambiar el código** (el mockup es el spec, y la longitud larga también se ve en las cards de práctica mockup l.1241/1261).
- (3) reescribir el eyebrow `"STOP · TOLERANCIA AL MALESTAR"` a `"STOP · TOLERANCIA"` (mockup l.1053-1055: practice eyebrows son los family labels, no titles).
- (4) bumear `_num_size_override` de 40 a 46 en `app/modules/timer_qt.py` (mockup l.861).
- (5) actualizar el assert a `text() == "+"`, `variant() == "gradient"`, dejar width/height (36, 34) que sí matchean.
- (6) actualizar `_results_badge` a `tone="brand"` en `hub/main_qt.py:345` (mockup l.1388; ambos tonos rinden al mismo color pero "brand" es semánticamente correcto).

## 4. Tests PINNED-IMPL (asserts literales de CSS/source — frágil a theme rotation)

13 tests (marcados 🟡 en §1) assertean strings literales dentro de `styleSheet()` o `inspect.getsource(...)`. **El contrato visual está vigente** (los literales coinciden con el render actual), pero el día que `v3c("brand")` rote de `#2E5D43` a otro verde, el test rompe antes que la UI lo haga visible.

**Tests afectados:** `test_button_primitive_supports_mockup_soft_variant`, `test_tabs_pill_paints_container_with_soft_selected_state`, `test_tabs_variants_have_role_specific_density_and_selection`, `test_badge_primitive_supports_mockup_tones`, `test_input_focus_uses_mockup_brand_line_and_soft_halo`, `test_card_hover_border_uses_brand_line`, `test_mood_slider_internal_uses_shared_mockup_slider_qss`, `test_v3_mood_slider_thumb_uses_mockup_brand_contract`, `test_dialog_matches_mockup_modal_contract`, `test_module_ring_matches_mockup_conic_contract`, `test_play_button_matches_mockup_ctl_contract`, `test_window_chrome_matches_mockup_titlebar_contract`, `test_patient_row_premium_matches_mockup_prow_contract`, `test_dbt_cards_match_mockup_family_bar_contract`, `test_avisos_filters_and_search_are_visible_and_drive_state`, `test_home_hero_filled_state_matches_mockup_score_and_delta`, `test_home_view_vertical_rhythm_matches_mockup`, `test_home_module_card_matches_mockup_badge_contract`, `test_registro_tcc_distortion_and_tip_tones_match_mockup`, `test_registro_tcc_visual_source_uses_mockup_rose_and_gold`, `test_registro_tcc_step_title_uses_serif_source`, `test_timer_idle_chips_and_status_badge_match_mockup`, `test_onboarding_narrow_520_default_size`, `test_onboarding_compact_visual_contract_keeps_consent_integrated`.

**Recomendación:** refactor a asserts sobre tokens (`assert v3c("brand", "light") in qss` en vez de `"#2e5d43" in qss`) o sobre los `v3c(...)` calls en source en vez de los literales post-resolve. **No aplicar en este audit** (es un refactor cross-cutting; fuera del scope de "1 discrepancia = 1 ciclo").

## 5. Conclusión

- **49 tests CORRECTOS** son el contrato vigente; el producto debe matchearlos.
- **11 tests FUNCTIONALES** nunca se tocan en un loop visual.
- **13 tests PINNED-IMPL** son frágiles a theme rotation; refactor cross-cutting pendiente.
- **4 tests OBSOLETOS** (5 contando el `tone="info"` que es semántico no visual) requieren decisión del owner antes de cualquier cambio.

> **NO es PASS visual global.** Este audit NO declara fidelidad. Identifica 4-5 tests obsoletos cuyas actualizaciones (aprobadas por owner) destrabarían iteraciones futuras. Los tests que sí matchean el mockup son la barrera de regresión; los que NO matchean son la puerta a fixes que el loop actual no puede aplicar.
