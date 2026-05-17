# AI_PROJECT_CONTEXT - NeuroMood

Actualizado: 2026-05-16

Este es el archivo único de contexto y documentación del proyecto para agentes IA, desarrolladores y mantenimiento futuro.

Regla obligatoria para agentes IA: leer este archivo antes de cambios amplios y escribir documentación nueva solamente aquí. No crear `README` alternativos, carpetas `docs/`, planes sueltos, auditorías sueltas ni manuales intermedios en la raíz. Los PDFs finales para distribución pueden vivir en la raíz, pero su fuente de verdad técnica queda resumida en este archivo.

Regla de orden del proyecto: mantener la raíz lo más limpia posible. No generar basura temporal, scripts de prueba, capturas, reportes, logs, specs, builds, zips ni archivos auxiliares sueltos en la raíz. Si un cambio necesita crear archivos nuevos, ubicarlos en una carpeta existente adecuada o crear una subcarpeta clara dentro del proyecto. Para scripts y automatizaciones usar siempre `AI_SCRIPTS/`.

Este archivo reemplaza y unifica la documentación suelta previa: README, contexto actualizado, manual de usuario, planes de acción, auditorías, guías UI/UX, notas de seguridad y checklist de distribución. La intención es que cualquier agente IA o desarrollador pueda leer un solo documento y entender el estado útil y vigente del proyecto.

## 1. Resumen Del Producto

NeuroMood V3 es una plataforma de bienestar mental para Windows construida en Python 3.12 y PyQt6. Tiene dos aplicaciones oficiales:

- NeuroMood Suite: app del paciente.
- NeuroMood Hub: app profesional para terapeutas/equipos clínicos.

También incluye instaladores y desinstaladores oficiales:

- Instalador Suite.
- Instalador Hub.
- Desinstalador Suite.
- Desinstalador Hub.

La identidad visual actual está basada en `neuromood_v3_all_screens.html`, con estética dark/light híbrida, tipografía DM Sans/Segoe UI según entorno, acentos teal/violeta, cards compactas, bordes suaves, pills, rings y componentes V3 compartidos.

## 2. Nombres Vigentes De Módulos Paciente

Estos son los nombres visibles que deben usarse en documentación, UI nueva y materiales finales:

| Nombre vigente | Nombre anterior / archivo |
|---|---|
| Termómetro Emocional | ex Ánimo / `app/modules/animo_qt.py` |
| Guía de Respiración Animada | ex Respiración / `app/modules/respiracion_qt.py` |
| Registro de Pensamientos (TCC) | ex TCC / `app/modules/registro_tcc_qt.py` |
| Checklist de Rutina Diaria | ex Rutina / `app/modules/rutina_qt.py` |
| Asistente de Activación Conductual | ex Actividades / `app/modules/actividades_qt.py` |
| Temporizador de Actividades | ex Timer / `app/modules/timer_qt.py` |
| Recordatorios de Bienestar | ex Avisos / `app/modules/avisos_qt.py` |

## 3. NeuroMood Suite - App Paciente

Entry point:

```text
app/main_qt.py
```

La Suite es una app PyQt6 con `QMainWindow`, header global compacto `NMHeader`, home `HomeView` y carga dinámica de módulos mediante `_MODULE_MAP`.

### Funcionalidad Para Usuario Final

La persona paciente usa NeuroMood Suite para registrar emociones, sostener rutinas, practicar respiración, trabajar pensamientos, recibir recordatorios, activar hábitos y usar temporizadores de actividad.

Herramientas:

- Termómetro Emocional: registra el estado emocional diario con puntuación y nota.
- Guía de Respiración Animada: guía pausas de respiración con ritmo visual.
- Registro de Pensamientos (TCC): ordena situación, emoción, pensamiento automático y respuesta alternativa.
- Checklist de Rutina Diaria: organiza tareas por mañana, tarde y noche.
- Asistente de Activación Conductual: sugiere actividades según el ánimo.
- Temporizador de Actividades: acompaña bloques de foco o acción concreta.
- Recordatorios de Bienestar: crea avisos locales para medicación, pausas, hábitos o indicaciones.

### Autenticación E Instalación

El Instalador Suite usa Supabase Auth directo:

- Login: `sign_in_with_password`.
- Crear cuenta: `sign_up`.
- Restablecer contraseña: `reset_password_for_email`.

Restricciones vigentes:

- No usar Resend propio.
- No usar SMTP custom en código.
- No usar Google OAuth.
- No permitir “continuar sin cuenta”.
- No guardar contraseñas localmente.

El instalador guarda datos mínimos como `auth_user_id`, `patient_email`, `patient_id` e `install_code`.

### Aviso Legal Y Consentimiento De Uso

El Instalador Suite exige consentimiento legal después de login/registro exitoso y antes de instalar NeuroMood Suite. El consentimiento queda asociado a la cuenta autenticada.

Reglas vigentes:

- Título visible: `Aviso legal y consentimiento de uso`.
- Checkbox obligatorio: `Leí y acepto el aviso legal, el consentimiento de uso y el tratamiento de datos`.
- No se permite instalar si no existe consentimiento vigente.
- Se guarda constancia local separada en `%APPDATA%/NeuroMood/legal_consent.json`.
- Se registra constancia remota separada en Supabase, tabla `legal_consents`.
- No se mezcla con DB clínica, módulos, evolución ni sync clínico.
- Si cambia `DISCLAIMER_VERSION` o `PRIVACY_VERSION`, se solicita nueva aceptación.
- Si falla el registro remoto, el instalador muestra error y no continúa.

El texto legal presenta NeuroMood Suite como herramienta complementaria de bienestar, registro emocional, organización de hábitos y apoyo personal. No debe prometer diagnóstico, tratamiento, prevención, evaluación clínica automatizada, monitoreo clínico autónomo, detección de riesgo, decisión terapéutica automática ni atención de emergencias.

Tabla remota: `public.legal_consents` (creada en Supabase). Schema completo en `db/legal_consents.sql`.

Campos: `user_id`, `patient_id`, `email`, `accepted_at_utc`, `product_name`, `neuromood_suite_version`, `instalador_suite_version`, `disclaimer_version`, `privacy_version`, `disclaimer_text_hash`, `privacy_text_hash`, `consent_scope`, `status`, `created_at`.

Políticas RLS activas (la tabla tiene RLS habilitado, a diferencia del resto de tablas clínicas):

- `legal_consents_insert_own` — `to authenticated`, `with check (auth.uid() = user_id)`. Solo el paciente autenticado puede insertar su propio consentimiento.
- `legal_consents_select_own` — `to authenticated`, `using (auth.uid() = user_id)`. El paciente autenticado solo lee sus propios registros.
- `legal_consents_select_anon_hub` — `to anon`, `using (true)`. Permite al Hub leer consentimientos por `patient_id` usando la anon key (sin sesión auth), igual que el resto de tablas clínicas del proyecto.

El Hub no usa service_role. El INSERT está protegido por auth; el SELECT anon es el mismo modelo de acceso que usan todas las tablas clínicas del proyecto.

### Permisos Y Bloqueos

La Suite viene desbloqueada por defecto. El Hub puede bloquear o desbloquear módulos mediante permisos sincronizados.

Permisos locales:

```text
perm_checklist_manual
perm_checklist_activacion
perm_temporizador_manual
perm_recordatorios_manual
```

Si Supabase no envía un permiso explícito, la app asume desbloqueado. Si el Hub envía `False`, la Suite respeta el bloqueo.

## 4. NeuroMood Hub - App Profesional

Entry point:

```text
hub/main_qt.py
```

El NeuroMood Hub es una app PyQt6 para profesionales. Usa sidebar `NMHubSidebar`, header `NMHeader`, vistas internas con `NMFadeWidget` y componentes compartidos.

Vistas principales:

- Pacientes.
- Dashboard.
- IA Asistente.
- Config.

Archivos clave:

```text
hub/main_qt.py
hub/pacientes_qt.py
hub/ia_asistente.py
hub/exportar.py
```

### Funcionalidad Para Profesionales

El profesional puede:

- Ver pacientes sincronizados.
- Abrir dashboard clínico de un paciente.
- Revisar registros de los siete módulos.
- Asignar tareas o recordatorios remotos.
- Usar IA con contexto clínico.
- Exportar reportes PDF.
- Revisar estado de sincronización.

### Estado Legal / Consentimiento

El detalle de paciente en NeuroMood Hub muestra una tarjeta mínima `Estado legal / Consentimiento` consultando `legal_consents`.

Muestra únicamente:

- Estado: vigente, pendiente, revocado o desactualizado.
- Fecha UTC de aceptación.
- Versión del disclaimer.
- Versión de privacidad.
- Versión de NeuroMood Suite.
- Hash del texto aceptado.

Incluye botón `Descargar constancia`, que genera un PDF legal separado de la exportación clínica. Si no hay consentimiento vigente, el Hub muestra advertencia y deshabilita tabs de detalle para evitar visualización profesional hasta regularizar.

### Configuración Automática

El Hub ya no pide URL ni API Key manualmente en el instalador ni en una pantalla de setup. Lee credenciales desde `.env` con este orden:

1. `%APPDATA%/NeuroMood/.env`
2. `%APPDATA%/NeuroMoodHub/.env`
3. Carpeta del ejecutable
4. Raíz del proyecto en modo desarrollo
5. Variables de entorno del sistema

El Instalador Hub copia `.env` a `%APPDATA%/NeuroMoodHub/.env` y lo marca como oculto. En la UI se informa configuración automática y credenciales protegidas/no incluidas, sin exponer valores reales.

## 5. Instaladores Y Desinstaladores

### Instalador Suite

Archivo:

```text
installers/installer.py
```

Pasos:

```text
Bienvenida
Cuenta
Consentimiento
Instalar
Finalizar
```

Responsabilidades:

- Autenticar o crear cuenta con Supabase Auth.
- Instalar el bundle de Suite.
- Copiar desinstalador.
- Registrar uninstall en Windows.
- Crear identidad mínima local.
- Inicializar permisos locales desbloqueados.

### Instalador Hub

Archivo:

```text
installers/installer_pro.py
```

Pasos:

```text
Bienvenida
Ruta
Instalar
Finalizar
```

El antiguo paso manual de Supabase fue eliminado. La configuración se resuelve por `.env` empaquetado/copiadito a AppData.

### Desinstaladores

Archivos:

```text
installers/uninstaller.py
installers/uninstaller_pro.py
```

Pasos:

```text
Confirmar
Eliminando
Finalizado
```

La conservación/eliminación de datos debe seguir siendo opcional para el usuario. Los desinstaladores deben eliminar residuos de instalación, accesos directos y registro de Windows. Los datos locales se tratan según la decisión del usuario.

## 6. Arquitectura De Carpetas Vigente

```text
app/          App paciente
hub/          NeuroMood Hub
shared/       Código compartido
installers/   Instaladores y desinstaladores
assets/       Logo e iconos
db/           Esquema Supabase y recursos DB
AI_SCRIPTS/   Scripts de build, QA, utilidades y automatización
dist/         Salida de EXEs oficiales
```

La raíz debe mantenerse limpia. No crear scripts sueltos, logs, capturas, reportes, zips, specs, builds ni archivos auxiliares temporales en la raíz: usar `AI_SCRIPTS/`, `dist/` o una subcarpeta específica según corresponda.

Manuales PDF finales vigentes en raíz:

```text
Manual_Usuario_Profesional_NeuroMood.pdf
Manual_Tecnico_Descriptivo_NeuroMood.pdf
```

Estos PDFs son artefactos de distribución. Si cambia su contenido, regenerarlos desde `AI_SCRIPTS/generate_neuromood_manuals.py` y actualizar el resumen técnico relevante en este archivo.

## 7. Shared

### `shared/theme.py`

Tokens base:

- Colores.
- Tipografía.
- Radios.
- Espaciados.
- Tamaños.

### `shared/theme_qt.py`

Helpers Qt:

- `C()`
- `qfont()`
- `sp()`
- `app_palette()`
- `stylesheet_base()`

### `shared/components_qt.py`

Componentes V3 reutilizables: headers, sidebars, cards, inputs, botones, pickers, steppers, progress, componentes Hub, componentes de instalador.

Regla visual: usar componentes NeuroMood antes que widgets Qt crudos cuando exista equivalente.

### `shared/db.py`

SQLite local:

```text
%APPDATA%/NeuroMood/nm_data.db
```

### `shared/sync.py`

Sincronización con Supabase:

- Exporta datos del paciente.
- Importa permisos/asignaciones.
- Registra/actualiza paciente.
- Usa lazy loading para no romper si Supabase no está disponible.

### `shared/config.py`

Única puerta de lectura para:

```text
SUPABASE_URL
SUPABASE_KEY
```

También puede servir a proveedores IA desde Hub.

### `shared/visual_qa.py`

Fixtures visuales solo con flags explícitos:

```text
NM_VISUAL_QA=1
NM_DEMO_VISUAL=1
NM_QA_VISUAL=1
```

No debe afectar producción.

## 8. Seguridad

Reglas obligatorias:

- No hardcodear secretos en código.
- No distribuir `service_role`.
- Si se empaqueta `.env`, debe contener solo `SUPABASE_URL` y `SUPABASE_KEY` pública/anon.
- Las contraseñas se manejan por Supabase Auth.
- El Instalador Suite no guarda contraseñas localmente.
- El Hub no muestra URL/API Key reales en UI.
- No tocar DB/sync/auth/config/identidad sin revisión.

Áreas sensibles:

```text
shared/db.py
shared/sync.py
shared/config.py
shared/identidad.py
```

## 9. Design System Y UI

Fuente visual principal: `neuromood_v3_all_screens.html`.

Tokens principales:

- Dark: fondos slate/navy, texto claro, cards compactas.
- Light: fondo `#f8fafc`, superficies blancas, bordes suaves.
- Acentos: teal `#14b8a6`, indigo `#6366f1`, violet `#a855f7`.
- Estados: success, warning, error.

Componentes clave:

- `NMWelcomeBar`
- `NMStreakBadge`
- `NMEmojiPicker`
- `NMPhaseChip`
- `NMCycleRing`
- `NMTCCStepper`
- `NMHeatBar`
- `NMRoutineSection`
- `NMCustomCheck`
- `NMMoodContextHeader`
- `NMCategoryFilter`
- `NMActivityCard`
- `NMPresetChip`
- `NMFocusArc`
- `NMSessionHistory`
- `NMAvisoCard`
- `NMProgressLine`
- `NMHubSidebar`
- `NMFeaturedCard`
- `NMModuleRing`
- `NMPatientRow`
- `NMSyncOrb`
- `NMSettingsSection`
- `NMInstallProgress`
- `NMInstallStepper`
- `NMDataPreserveCard`

## 10. Build Y Distribución

El build debe ejecutarse desde un único BAT oficial:

```text
BUILD_NEUROMOOD.bat
```

Salidas esperadas:

```text
dist/NeuroMood Suite/NeuroMood Suite.exe
dist/NeuroMood Hub/NeuroMood Hub.exe
dist/Instalador Suite/Instalador Suite.exe
dist/Instalador Hub/Instalador Hub.exe
dist/Desinstalador Suite/Desinstalador Suite.exe
dist/Desinstalador Hub/Desinstalador Hub.exe
```

Reglas:

- Limpiar `.spec` al finalizar.
- Limpiar `build/` al finalizar.
- Mantener salida de consola limpia.
- Compilar EXEs finales/oficiales.
- No dejar scripts auxiliares en raíz.
- La lógica de build vive en `AI_SCRIPTS/build_neuromood.py`; el `.bat` solo delega.
- Para validar sin compilar: `BUILD_NEUROMOOD.bat --dry-run`.
- Para forzar cache limpia de PyInstaller: `BUILD_NEUROMOOD.bat --clean`.
- `dist/` se conserva como carpeta de salida; `build/` es temporal y no debe quedar versionada.

## 11. QA Y Scripts

Carpeta única de scripts:

```text
AI_SCRIPTS/
```

Regla explícita: todo agente IA debe buscar scripts reutilizables en `AI_SCRIPTS/` antes de crear uno nuevo. Si necesita crear o modificar automatizaciones, pruebas, auditorías, capturas, generadores o utilidades de mantenimiento, debe hacerlo dentro de `AI_SCRIPTS/` y no en la raíz.

Tipos de scripts admitidos:

- Build automatizado.
- QA de EXEs.
- Smoke tests.
- Capturas visuales.
- Resize tests.
- Auditorías.
- Generación de documentación.

No usar más `script tests/` ni scripts sueltos en raíz.

Scripts vigentes:

- `AI_SCRIPTS/build_neuromood.py`: build oficial completo.
- `AI_SCRIPTS/generate_neuromood_manuals.py`: generación de los dos manuales PDF finales.
- `AI_SCRIPTS/qa_exe_capture.py`: capturas QA de EXEs.
- `AI_SCRIPTS/qa_full_suite.py`: recorrido QA amplio.
- `AI_SCRIPTS/smoke_test_runner.py`: smoke tests.
- `AI_SCRIPTS/_audit_scan.py`, `AI_SCRIPTS/_audit_mockup_grid.py`, `AI_SCRIPTS/_test_color_regression.py`: auditorías visuales/técnicas puntuales.
- `AI_SCRIPTS/_test_home_auto.py`, `AI_SCRIPTS/_test_responsive_final.py`, `AI_SCRIPTS/_test_visual_auto.py`, `AI_SCRIPTS/resize_test.py`, `AI_SCRIPTS/ui_crawler.py`: pruebas visuales y de navegación.

## 12. Auditorías Y Planes Históricos Consolidados

La auditoría antigua señalaba 134 problemas potenciales, principalmente:

- Recursos Qt sin limpiar.
- Excepciones silenciosas.
- Señales sin desconectar.
- Código duplicado de theme.
- Uso excesivo de estilos directos.

Estado actual: esta auditoría se conserva solo como referencia histórica. Antes de actuar sobre ella, validar contra el código vigente, porque parte del proyecto fue modificado en pasadas posteriores de fidelidad visual, QA y build.

Prioridad vigente:

1. Mantener UI fiel al mockup HTML.
2. Mantener instaladores/desinstaladores funcionales.
3. Mantener seguridad de Auth/Supabase.
4. Evitar tocar DB/sync/config/identidad salvo que sea estrictamente necesario.
5. Mantener raíz limpia y scripts concentrados en `AI_SCRIPTS/`.

## 13. Manual Para Usuario Final

NeuroMood V3 acompaña el bienestar emocional con una app para pacientes y un Hub para profesionales.

El paciente usa NeuroMood Suite para registrar emociones, hacer respiración guiada, trabajar pensamientos, sostener rutinas, recibir recordatorios, activar hábitos y usar temporizadores.

El profesional usa NeuroMood Hub para ver evolución, revisar registros, asignar tareas, enviar recordatorios y apoyarse en IA.

La instalación es guiada:

- Suite: requiere cuenta con email y contraseña.
- NeuroMood Hub: instala sin pedir configuración técnica manual.
- Desinstaladores: permiten quitar apps y decidir sobre datos locales.

## 14. Notas Para Agentes IA

Cuando trabajes en este proyecto:

- Leé primero este archivo.
- No crees scripts en raíz; usá `AI_SCRIPTS/`.
- No revivas `docs/`, `script tests/` ni carpetas duplicadas.
- No agregues documentación suelta: actualizá este archivo.
- No dejes `.spec`, `build/`, `__pycache__` ni outputs temporales.
- No modifiques áreas sensibles sin necesidad clara.
