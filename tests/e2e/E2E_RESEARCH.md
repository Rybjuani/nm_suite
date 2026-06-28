# E2E Research

Repo: `nm_suite`
Fecha de investigacion: 2026-06-28

## Fase 0 - Preflight

- Rama actual: `main`
- Ultimo commit: `30d09b8 docs(qa): registro de divergencias de diseno vs mockup canonico`
- Working tree inicial: `?? qa/_calibration_run_20260627/`
- Tests existentes: `.\.venv\Scripts\python.exe -m pytest tests -q`
- Resultado: `315 passed in 536.40s (0:08:56)`
- Nota: el primer intento con timeout de 124s expiro sin salida suficiente; el mismo comando paso con timeout amplio.

## Entry points

- Suite paciente: `app/main_qt.py`
  - Clase principal: `NeuroMoodApp(ThemeAwareWidgetMixin, QMainWindow)`.
  - Shell interno: `_ShellWidget(QWidget)`.
  - Cierre: `NeuroMoodApp._on_close(event)`.
  - QA/smoke: usa `visual_qa_enabled()`, `NM_QA_SMOKE`, `NM_TEST_FORCE_CLOSE`.
  - Sync: `_sync_background()` llama `shared.sync.sync_al_abrir`.

- Hub profesional: `hub/main_qt.py`
  - Clase principal: `NeuroMoodHub(ThemeAwareWidgetMixin, QMainWindow)`.
  - Shell interno: `_ShellWidget(QWidget)`.
  - Vista de pacientes: `PacientesView(QWidget)`.
  - QA/smoke: usa `visual_qa_enabled()`, `NM_QA_SMOKE`, `NM_TEST_FORCE_CLOSE`.

## Suite

### Home

- Archivo: `app/home_qt.py`
- Clase principal: `HomeView(QWidget)`.
- Clases auxiliares: `ModuleCard`, `_HeroBienestar`, `_ProximaSesionCard`.
- Subestados:
  - Hero con y sin animo del dia.
  - Grilla de modulos disponible/deshabilitada.
  - Proxima sesion visible/oculta.
- Acciones criticas:
  - Abrir modulos via callback `on_module_open`.
  - Boton de registro de animo en estado empty.
- Persistencia:
  - Lee configuracion local con `shared.db.leer_config`.
  - No persiste directamente.
- Dependencias externas:
  - `shared.visual_qa` para datos estables.
  - `ThemeManager`.
- Atributos privados utiles verificados:
  - `_cards`, `_grid`, `_hero`, `_session_card`, `_module_configs`, `_open_cb`, `_get_status`.

### Onboarding

- Archivo: `app/onboarding_qt.py`
- Clase principal: `OnboardingDialog(QDialog)`.
- Clase auxiliar: `_ConsentCheckBox(QCheckBox)`.
- Subestados:
  - Registro.
  - Login.
  - Recuperar acceso.
  - Consentimiento aceptado/no aceptado.
- Acciones criticas:
  - Signup, login, recuperacion de acceso.
  - Validaciones de nombre, email, password y consentimiento.
- Persistencia:
  - Guarda configuracion local y datos de identidad.
  - Upsert en tabla `patients`.
  - Insert/select en `legal_consents`.
- Dependencias externas:
  - `supabase.create_client`.
  - Config Supabase leida con `leer_config`.
- Atributos privados utiles verificados:
  - `_consent_check` conectado a `_sync_action_buttons`.
  - Botones y entradas deben buscarse por texto, placeholder o clase, porque el archivo no expone objectNames estables para todo.
- Regla de parcheo:
  - Parchear `supabase.create_client`.
  - Si aparecen imports top-level de `supabase_url`/`supabase_key`, parchear tambien en `app.onboarding_qt`.
  - Usar `leer_config`, no `obtener_config`.

### Animo

- Archivo: `app/modules/animo_qt.py`
- Clase principal: `ModuloAnimo(NMModule)`.
- Subestados:
  - Slider sin seleccion.
  - Nivel seleccionado.
  - Estado guardado/celebracion.
- Acciones criticas:
  - Seleccionar nivel de animo.
  - Guardar registro.
- Persistencia:
  - SQLite local para registros de animo.
  - Sync inmediato con `shared.sync.sync_inmediato_background` cuando no es visual QA.
- Dependencias externas:
  - `shared.visual_qa`.
  - `shared.sync`.
- Atributos privados utiles verificados:
  - Se debe verificar uso de `_v3_slider` antes de interactuar.
  - La regla del brief aplica: usar `set_level` si existe en el slider real.

### Respiracion

- Archivo: `app/modules/respiracion_qt.py`
- Clase principal: `ModuloRespiracion(NMModule)`.
- Clase auxiliar: `_BreathCircle`.
- Subestados:
  - Preset seleccionado.
  - Corriendo.
  - Pausado.
  - Detenido/finalizado.
- Acciones criticas:
  - Presets por botones `NMButtonOutline`.
  - Play/pause con `_btn_play`.
  - Reset con `_btn_reset`.
  - Stop con `_btn_stop`.
- Persistencia:
  - Guarda sesion respiracion local.
  - Sync inmediato en guardado si corresponde.
- Dependencias externas:
  - `shared.sync.sync_inmediato_background`.
- Atributos privados utiles verificados:
  - `_timer_id`, `_circle`, `_btn_reset`, `_btn_play`, `_btn_stop`, `_chip_inhala`, `_chip_manten`, `_chip_exhala`.

### Registro / TCC

- Archivo: `app/modules/registro_tcc_qt.py`
- Clase principal: `ModuloRegistroTCC(NMModule)`.
- Clases auxiliares: `_EmotionChip`, `_EmotionTile`, `_ResumenCard`, `_TipCard`.
- Subestados:
  - Paso emocion/situacion.
  - Paso pensamiento/distorsiones.
  - Paso respuesta alternativa.
  - Resumen/exito.
- Acciones criticas:
  - Elegir emocion.
  - Completar situacion, pensamiento y respuesta.
  - Avanzar/retroceder.
  - Guardar registro.
- Persistencia:
  - SQLite local para pensamiento/TCC.
  - Sync inmediato con `shared.sync.sync_inmediato_background` fuera de visual QA.
- Dependencias externas:
  - `shared.sync`.
  - Plantillas de TCC sincronizadas por `shared.sync`.
- Atributos privados utiles verificados:
  - `_txt_situacion`, `_txt_pensamiento`, `_txt_respuesta`, `_emotion_tiles`, `_btn_prev`, `_btn_next`, `_step`, `_data`.

### Rutina

- Archivo: `app/modules/rutina_qt.py`
- Clase principal: `ModuloRutina(NMModule)`.
- Clases auxiliares: `_HeroDayCard`, `_SectionCard`.
- Subestados:
  - Rutina con tareas.
  - Empty state.
  - Tareas completadas/no completadas.
  - Form de agregar tarea si existe en seccion.
- Acciones criticas:
  - Toggle de tarea con `NMCustomCheck`.
  - Agregar tarea manual desde `_SectionCard`.
- Persistencia:
  - Checklist local.
  - Sync inmediato al completar/agregar si corresponde.
- Dependencias externas:
  - `shared.visual_qa.routine_sections`.
  - `shared.sync.sync_inmediato_background`.
- Atributos privados utiles verificados:
  - `_hero_card`; secciones creadas como `_SectionCard`; checks `NMCustomCheck`.
- Nota de interaccion:
  - `NMCustomCheck` no tiene `.click()` publico confiable; usar `setChecked(...)` y emitir `toggled`.

### Actividades

- Archivo: `app/modules/actividades_qt.py`
- Clase principal: `ModuloActividades(NMModule)`.
- Clases auxiliares: `_CategoryRingTile`, `_CategoriesCard`, `_IntensityDots`, `_SuggestedCard`.
- Subestados:
  - Sugerencias presentes.
  - Empty state.
  - Filtro por categoria.
  - Actividad hecha/no pude.
- Acciones criticas:
  - Cambiar categoria.
  - Marcar actividad hecha/no pude.
- Persistencia:
  - Guarda resultados de activacion local.
  - Sync inmediato fuera de visual QA.
- Dependencias externas:
  - `shared.visual_qa.activity_suggestions`.
  - `shared.sync.sync_inmediato_background`.
- Atributos privados utiles verificados:
  - `_all_activities`, `_current_filter`, `_suggested_cards`, `_category_tabs`, `_grid_layout`, `_footer_lbl`.

### Timer

- Archivo: `app/modules/timer_qt.py`
- Clase principal: `ModuloTimer(NMModule)`.
- Clase auxiliar: `_TimerChip(NMButtonOutline)`.
- Subestados:
  - Sin preset/empty.
  - Preset seleccionado.
  - Corriendo.
  - Pausado.
  - Finalizado.
- Acciones criticas:
  - Elegir preset/duracion.
  - Play/pause con `_btn_play`.
  - Stop/reset con `_btn_reset`.
  - Finish/skip con `_btn_skip`.
- Persistencia:
  - Guarda sesion timer local.
  - Sync inmediato fuera de visual QA.
- Dependencias externas:
  - `shared.sync.sync_inmediato_background`.
  - `shared.visual_qa.timer_sessions`.
- Atributos privados utiles verificados:
  - `_current_categoria`, `_timer_id`, `_canvas`, `_btn_reset`, `_btn_play`, `_btn_skip`, `_ent_actividad`, `_input_container`, `_timer_card`.

### Avisos

- Archivo: `app/modules/avisos_qt.py`
- Clase principal: `ModuloAvisos(NMModule)`.
- Clases auxiliares: `_StepPill`, `_ReminderCardV3`.
- Subestados:
  - Lista de recordatorios.
  - Empty state.
  - Filtros/busqueda.
  - Recordatorio completado.
- Acciones criticas:
  - Completar aviso.
  - Filtrar activos/hoy/busqueda.
- Persistencia:
  - SQLite local.
  - Sync inmediato despues de completar fuera de visual QA.
- Dependencias externas:
  - `shared.visual_qa.reminder_rows`.
  - `shared.sync`.
- Atributos privados utiles verificados:
  - El modulo usa `visual_qa_enabled()` para evitar carga real y sync en varias rutas.

### DBT

- Archivo: `app/modules/dbt_qt.py`
- Clase principal: `ModuloDBT(NMModule)`.
- Clases auxiliares: `_NeedCard`, `_SkillCard`, `_StepProgressIndicator`, `_SkillPracticeView`, `_PracticeModalScrim`.
- Subestados:
  - Biblioteca de habilidades.
  - Seleccion de necesidad.
  - Practica actual.
  - Stop/finalizacion.
- Acciones criticas:
  - Elegir necesidad/habilidad.
  - Iniciar y detener practica.
- Persistencia:
  - Guarda `dbt_practice_records`.
  - Sync inmediato al guardar.
- Dependencias externas:
  - `shared.sync.sync_inmediato_background`.
- Atributos privados utiles verificados:
  - Usar clases y texto visible; no hay objectNames publicos suficientes para depender solo de nombres.

## Hub

### Pacientes

- Archivo: `hub/main_qt.py`
- Clase principal: `PacientesView(QWidget)`.
- Subestados:
  - Lista con pacientes.
  - Empty state.
  - Busqueda/filtro.
  - Estado sync stale/ok.
- Acciones criticas:
  - Seleccionar paciente.
  - Quitar/unlink paciente si aparece boton.
- Persistencia:
  - Lee tabla `patients`.
  - Update `patients.unlinked` al desvincular.
- Dependencias externas:
  - Supabase client.
  - `shared.visual_qa.hub_patients`.
- Atributos privados utiles verificados:
  - `_sync_table_card_height`, filas `NMPatientRowPremium`, callback `_on_select`.

### Detalle paciente

- Archivo: `hub/pacientes_qt.py`
- Clase principal: `DetallePacienteView(QWidget)`.
- Firma verificada: `DetallePacienteView(modo, sb, paciente_id, paciente_nombre, parent=None)`.
- Subestados:
  - Header paciente.
  - Tab plan terapeutico.
  - Dialog resumen IA.
  - Exportacion PDF busy/no busy.
- Acciones criticas:
  - Click `Resumen IA`.
  - Click `Exportar PDF`.
- Persistencia:
  - Lee tablas de datos clinicos por `patient_id`.
  - Lee `assigned_reminders`.
- Dependencias externas:
  - `hub.ia_asistente.generar_resumen_paciente`.
  - `hub.exportar.exportar_pdf`.
- Atributos privados utiles verificados:
  - `_modo`, `_sb`, `_pid`, `_nombre`, `_btn_exportar_pdf`, `_btn_resumen_ia`, `_tab_plan`, `_resumen_dialog`.

### Textos globales

- Archivo: `hub/config_global_texts.py`
- Clase principal: `TextosGlobalesSuiteView(QWidget)`.
- Clase fila: `_TextEntryRow(NMCard)`.
- Subestados:
  - Sin cambios.
  - Cambios pendientes.
  - Guardado correcto.
  - Error sin Supabase.
  - Restaurar fila.
  - Restaurar todos con confirmacion.
- Acciones criticas:
  - Editar `NMInput`/`NMTextArea`.
  - Guardar cambios.
  - Restaurar individual.
  - Restaurar todos.
- Persistencia:
  - Tabla `hub_config`, `scope="global"`.
  - Select `key,value`.
  - Delete overrides.
  - Upsert overrides con `on_conflict="scope,key"`.
- Dependencias externas:
  - `shared.suite_text_catalog.suite_text_by_key`.
  - Supabase client fakeable.
- Atributos privados utiles verificados:
  - `_rows`, `_rows_by_key`, `_catalog_by_key`, `_original_values`, `_sb`, `_search`, `_section_filter`, `_pending_badge`, `_restore_all`, `_save`.
  - En fila: `editor`, `_restore_btn`, `_dirty`, `_count_lbl`.

### Resumen IA

- Archivo: `hub/ia_asistente.py`
- Funciones principales:
  - `generar_resumen_paciente(datos, nombre, on_result, on_error, patient_id=None)`.
  - `generar_asignacion(modulo, datos, nombre, on_result, on_error, patient_id=None)`.
  - `autocompletar_actividad(nombre_parcial, on_result, on_error, patient_id=None)`.
- Subestados:
  - Provider disponible/no disponible.
  - Llamada exitosa.
  - Error LLM.
  - Auditoria IA.
- Persistencia:
  - Inserta/actualiza `ia_audit_log` si no esta en visual QA y hay cliente Supabase.
- Dependencias externas:
  - OpenAI-compatible provider via config/env.
  - Supabase para auditoria.
- Testing:
  - Parchear funciones publicas, no llamar red.

### Plan terapeutico

- Archivo: `hub/plan_terapeutico.py`
- Clase principal: `PlanTerapeuticoTab(QWidget)`.
- Firma verificada: `PlanTerapeuticoTab(modo, sb, pid, nombre, parent=None)`.
- Tabs:
  - `_PresetRecordatoriosTab(sb, pid, modo, nombre, parent=None)`.
  - `_PresetTimerTab(sb, pid, modo, nombre, parent=None)`.
  - `_PresetRutinaTab(sb, pid, modo, nombre, parent=None)`.
  - `_PresetActivacionTab(sb, pid, modo, parent=None)`.
- Atributos privados utiles verificados:
  - Plan: `_tabs`, `_sb`, `_pid`, `_modo`, `_nombre`.
  - Timer: `_ent_name`, `_ent_secs`, `_ent_cat`, `_save_btn`, `_cancel_btn`, `_ia_btn`, `_list_lay`, `_editing_id`.
  - Recordatorios: `_ent_hora`, `_ent_msg`, `_save_btn`, `_ia_btn`, `_list_lay`.
  - Rutina: `_ent_task`, `_combo_sec`, `_save_btn`, `_ia_btn`, `_list_lay`.
  - Activacion: `_ent_name`, `_ent_desc`, `_combo_cat`, `_combo_min`, `_combo_max`, `_save_btn`, `_ia_btn`, `_list_lay`.
- Persistencia:
  - Timer: `timer_presets_remote`, `scope=f"patient:{pid}"`.
  - Recordatorios: `assigned_reminders`, `patient_id=pid`.
  - Rutina: `assigned_tasks`, `patient_id=pid`.
  - Activacion: `patient_activities`, `patient_id=pid`, campos `animo_min`/`animo_max`.
- Dependencias externas:
  - `hub.ia_asistente.generar_asignacion`.
  - `hub.ia_asistente.autocompletar_actividad`.

### Exportar PDF

- Archivo: `hub/exportar.py`
- Funciones:
  - `_generar(...)` para generacion directa.
  - `exportar_pdf(...)` lanza thread y puede llamar `os.startfile`.
  - `generar_constancia_consentimiento(...)`.
- Subestados:
  - Con datos.
  - Sin datos.
  - Filtro por fechas.
- Persistencia:
  - Escribe PDF en carpeta de usuario/descargas.
- Dependencias externas:
  - `reportlab`.
- Testing:
  - Para E2E llamar directo a `_generar`.
  - Setear `HOME=tmp_path`; no parchear `os.path.expanduser` si rompe reportlab.

## QA visual

- Archivo: `shared/visual_qa.py`
- `visual_qa_enabled()` devuelve True si alguna env var esta en valor verdadero:
  - `NM_VISUAL_QA`
  - `NM_DEMO_VISUAL`
  - `NM_QA_VISUAL`
  - `NM_VISUAL_QA_DEMO`
- Valores verdaderos: `1`, `true`, `yes`, `on`, `visual`, `demo`, `qa`.

### Que skipea o sustituye con `NM_VISUAL_QA=1`

- `app/main_qt.py`:
  - Marca `_visual_qa`.
  - Evita onboarding obligatorio en bootstrap.
  - En cierre, combinado con `NM_QA_SMOKE`/`NM_TEST_FORCE_CLOSE`, evita dialogos de cierre.
- `hub/main_qt.py`:
  - Usa pacientes demo y metricas demo.
  - Evita rutas reales de boot/conexion donde corresponde.
  - `NM_VISUAL_QA_HUB_VIEW` puede elegir vista inicial.
- `hub/ia_asistente.py`:
  - No audita en Supabase cuando visual QA esta activo.
- `app/home_qt.py`:
  - Usa hora estable y datos demo de estado.
  - Disponibilidad de modulos se fuerza estable.
- `app/modules/animo_qt.py`:
  - Usa datos/estado estables; evita persistencia/sync en rutas QA.
- `app/modules/respiracion_qt.py`:
  - Evita sync inmediato en guardado QA.
- `app/modules/registro_tcc_qt.py`:
  - Evita sync inmediato en guardado QA.
- `app/modules/rutina_qt.py`:
  - Usa `routine_sections()` demo y evita sync.
- `app/modules/actividades_qt.py`:
  - Usa sugerencias demo y evita sync.
- `app/modules/timer_qt.py`:
  - Usa sesiones/presets demo y evita sync/sonido segun ruta.
- `app/modules/avisos_qt.py`:
  - Evita carga real inicial y sync; usa `reminder_rows()` demo.
- `shared/utils.py`, `shared/theme_manager.py`:
  - Ajustan comportamiento para visual QA estable.

### Que no skipea necesariamente

- Render Qt real: widgets, layouts, estilos y senales siguen siendo reales.
- Persistencia local en modulos cuando el test no setea `NM_VISUAL_QA`.
- Llamadas a Supabase/IA si el test instancia vistas fuera de visual QA y no aplica fakes.
- `exportar._generar` escribe archivo real.
- `shared.sync` real si se invoca fuera de visual QA y no se parchea.

## Componentes NM

### NMButton

- Archivo: `shared/components/buttons.py`.
- Clase base: `QPushButton`.
- Senales: `clicked` heredada.
- objectName: `NMButton_<variant>`.
- accessibleName: texto del boton.
- En tests: buscar por clase `NMButton`/`QPushButton`, texto o `accessibleName`; usar `qtbot.mouseClick` o `.click()`.

### NMInput

- Archivo: `shared/components/buttons.py`.
- Clase base: `QLineEdit`.
- Senales: `textChanged` heredada.
- objectName: `NMInput`.
- accessibleName: placeholder.
- En tests: buscar por placeholder/accesible; usar `clear()` + `setText()` o `qtbot.keyClicks`.

### NMTextArea

- Archivo: `shared/components/buttons.py`.
- Clase base: `QTextEdit`.
- Senales: `textChanged` heredada.
- objectName: no se fija explicitamente en el rg relevante.
- accessibleName: placeholder o `Text area`.
- En tests: usar `setPlainText()` y drenar eventos.

### NMSearchInput

- Archivo: `shared/components/buttons.py`.
- Clase base: `QWidget` compuesto con editor interno.
- Senales: `text_changed(str)`, `returned(str)`.
- objectName: no estable en el contenedor.
- accessibleName: `Buscar`.
- En tests: encontrar clase `NMSearchInput`, luego su `QLineEdit` interno o usar API publica `text()/setText` si existe.

### NMTabs

- Archivo: `shared/components/buttons.py`.
- Clase base: `QWidget` compuesto.
- Senales: `changed(int, str)`.
- objectName: no estable.
- accessibleName: no estable.
- En tests: buscar botones hijos por texto o llamar `set_current(index)`.

### NMDialog

- Archivo: `shared/components/dialogs.py`.
- Clase base: `QWidget`.
- Senales: `closed`.
- objectName: panel interno `NMDialogPanel`.
- En tests: buscar ventanas top-level por clase `NMDialog`; botones de footer son `NMButton`/`NMButtonOutline`.

### NMToast

- Archivo: `shared/components/feedback.py`.
- Clase base: `QWidget`.
- Senales: no publica relevante.
- objectName: `NMToast_<variant>`.
- accessibleName: `NMToast {variant}: {message}`.
- En tests: leer `accessibleName`; no depender de QLabel hijo.

### NMCustomCheck

- Archivo: `shared/components/session.py`.
- Clase base: `QWidget`.
- Senales: `toggled(bool)`.
- objectName: no estable.
- accessibleName: texto.
- En tests: usar `setChecked(...)` y emitir/esperar `toggled`; no depender de `.click()`.

### NMPlayButton

- Archivo: `shared/components/inputs.py`.
- Clase base: `QPushButton`.
- Senales: `clicked` heredada.
- objectName: `NMPlayButton`.
- accessibleName: se setea en usos concretos; respiracion actualiza play/pause con `setAccessibleName`.
- En tests: buscar por clase o accessibleName; interactuar con `.click()` o `qtbot.mouseClick`.

### NMEmptyState

- Archivo: `shared/components/overlays.py`.
- Clase base: `QWidget`.
- Senales: `cta_primary_clicked`, `cta_secondary_clicked`.
- objectName: no estable en el rg relevante.
- En tests: buscar por clase `NMEmptyState` y labels/botones hijos.

### NMCard

- Archivo: `shared/components/cards.py`.
- Clase base: `QFrame`.
- Senales: `clicked`.
- objectName: `NMCard`.
- accessibleName: no generico.
- En tests: si `clickable=True`, emitir `clicked` directo cuando no haya metodo publico mejor.

## Riesgos de testing detectados

- Varias vistas tienen pocos objectNames estables; conviene Page Objects con fallback por texto, clase y accessibleName.
- Visual QA evita muchas rutas de persistencia/sync; los E2E de persistencia deben usar fakes sin `NM_VISUAL_QA` o verificar solo render con QA.
- Las funciones IA son callback-based y pueden usar threads; los fakes deben llamar callbacks de forma controlada.
- `exportar_pdf` no es ideal para tests por thread y `os.startfile`; usar `_generar`.
- Los tests existentes son lentos; E2E debe mantenerse enfocado.
