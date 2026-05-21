# AI_PROJECT_CONTEXT - NeuroMood

Actualizado: 2026-05-21 (rev: auditoría 2026-05 + prompts Codex + decisiones de producto 2026-05-20/21 + patrón hub_config 2 niveles + implementación F2 parcial + constructor PDF paramétrico)

Este es el archivo único de contexto y documentación del proyecto para agentes IA, desarrolladores y mantenimiento futuro.

Regla obligatoria para agentes IA: leer este archivo antes de cambios amplios y escribir documentación nueva solamente aquí. No crear `README` alternativos, carpetas `docs/`, planes sueltos ni manuales intermedios en la raíz. Los PDFs finales para distribución pueden vivir en la raíz, pero su fuente de verdad técnica queda resumida en este archivo.

**Excepciones documentadas a la regla de raíz:** dos artefactos auxiliares de auditoría/planificación viven en raíz por decisión explícita del cliente (2026-05-20/21) y se mantienen sincronizados con este archivo:

- [AUDITORIA_NEUROMOOD.md](AUDITORIA_NEUROMOOD.md) — auditoría completa por lectura del repo (3190 líneas) con las 11 partes del prompt maestro, decisiones de producto 2026-05-20/21, matriz de configurabilidad remota, plan por fases F0-F9, y respuestas directas a las 7 preguntas finales. Fuente de verdad de **qué se decidió y por qué**.
- [PROMPTS_CODEX_IMPLEMENTACION.md](PROMPTS_CODEX_IMPLEMENTACION.md) — 33 prompts atómicos por fase (F0-F6) listos para copiar/pegar a Codex. Cada prompt = una tarea concreta = un diff revisable, con archivos permitidos/prohibidos, validación y criterios de aceptación. Fuente de verdad de **cómo ejecutar**.

Cualquier cambio en estos archivos debe reflejarse acá (sección 15) y viceversa.

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

La identidad visual actual esta basada en `neuromood_v3_all_screens.html` y el handoff de diseno `neuromood/project/design_handoff_neuromood_v3/README.md`, con estetica dark/light hibrida, tipografia Plus Jakarta Sans principal, DM Sans fallback, acentos teal/violeta, cards compactas, bordes suaves, pills, rings, sombras, gradientes y componentes V3 compartidos.

La migracion v3 aplica la paleta `V3_LIGHT`/`V3_DARK` (teal #5eead4, violet #c084fc, bg #060912 dark / #eef2f8 light) con bridge legacy transparente via `_bridge_dark()`/`_bridge_light()`. El sistema de espacio usa `V3_SPACE` (md=12, lg=16, xl=24) expuesto como `V3_SP`.

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

La Suite es una app PyQt6 con `QMainWindow`, ventana ideal 1320x860 (minimo 1100x720). El fondo shell usa gradiente diagonal `bg+bgAlt` con 3 blobs radiales (teal, violet, cyan) pintados via `paint_shell_background()`. Header global `NMHeader` con modo `home_mode=True` para greeting/subtitle/streak; los modulos usan `set_context_title()` para el header contextual. Home `HomeView` y carga dinamica de modulos mediante `_MODULE_MAP`.

Efectos visuales aplicados:
- NMCard: drop shadow (blur 30 dark / 12 light) + hover elevation + glassmorphism translucido en dark
- NMButton gradient: drop shadow teal (blur 30 dark / 20 light)
- _LogoLabel: doble glow en dark (teal + violet radial) + logos tematicos
- NMFocusArc: glow blur en arco de progreso
- Toggle: glow track al activarse
- Shell: gradiente diagonal + 3 blobs radiales

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

El NeuroMood Hub es una app PyQt6 para profesionales, ventana ideal 1360x920 (minimo 1120x760). Fondo shell con gradiente + blobs igual que Suite. Usa sidebar `NMHubSidebar` a 240px (version colapsada tambien 240px) con iconos SVG via `nm_icon()` (`users`, `dashboard`, `ai`, `cog`) en lugar de emojis raw. Header `NMHeader`, vistas internas con `NMFadeWidget` y componentes compartidos.

La sidebar tiene boton collapse/expand con flechas SVG (`arrowLeft`/`arrowRight`) y orbe de sync con animacion de pulso (`NMSyncOrb`).

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

Todos los instaladores usan `InstallerShell` como base comun (`shared/installer_common.py`). Cambios recientes:

- Logo: carga `logos-dark.png` (siempre dark mode).
- Footer: botones gradient teal->violet, altura 56px premium.
- Stepper: compacto (circulos 18px, fuente 9px) + `NMInstallStepper` v3.

### Instalador Suite

Archivo: `installers/installer.py`
Tamaño: 820x660 fijo.
Pasos: Bienvenida, Cuenta, Consentimiento, Instalar, Finalizar.

### Instalador Hub

Archivo: `installers/installer_pro.py`
Tamaño: 820x660 fijo.
Pasos: Bienvenida, Ruta, Instalar, Finalizar.

### Desinstalador Suite

Archivo: `installers/uninstaller.py`
Tamaño: 760x620 fijo.
Pasos: Confirmar, Eliminando, Finalizado.

### Desinstalador Hub

Archivo: `installers/uninstaller_pro.py`
Tamaño: 760x620 fijo.
Pasos: Confirmar, Eliminando, Finalizado.

**Nota técnica de rescate (2026-05-18):** Se corrigió un bug crítico de runtime en `uninstaller_pro.py` donde el constructor de `_ProUninstWorker` no aceptaba el parámetro `conservar`, causando un TypeError. La lógica ahora respeta correctamente la opción de "Conservar mis datos", evitando la eliminación de la carpeta de configuración en AppData si el usuario lo solicita.

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

Schemas SQL vigentes en `db/`:

```text
db/supabase_schema.sql       Tablas clínicas (patients, mood_records, breathing_sessions,
                              thought_records, checklist_completions, timer_sessions,
                              reminder_logs, assigned_tasks, assigned_reminders,
                              activity_bank, patient_activities). RLS deshabilitado.
db/legal_consents.sql        Tabla legal_consents con RLS habilitado y 3 políticas.
                              Versionado por código (decisión 5 — NO editable desde UI).
db/fix_supabase_rls.sql      Migración de RLS para tablas clínicas (deshabilitar).
db/hub_config_schema.sql     Tabla hub_config para configurabilidad remota 2 niveles
                              (F2.0.A — ver §15.6). Una sola tabla con scope
                              'global' o 'patient:<patient_id>'. RLS deshabilitado.
db/feature_schemas.sql       8 tablas para entidades complejas que NO caben en
                              hub_config (lifecycle propio / FK / estructura
                              compleja): tcc_templates, routine_templates,
                              patient_routine_template, breathing_presets_remote,
                              timer_presets_remote, support_messages,
                              ia_audit_log, ia_chat_history. Más ALTER
                              patients.rutina_modo (opción C, decisión 2026-05-21).
                              RLS deshabilitado. F2.1.A.
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

Tokens base + paletas canonicas v3:

- `V3_LIGHT`: paleta clara (bg #eef2f8, accent teal #14b8a6).
- `V3_DARK`: paleta oscura (bg #060912, accent teal #5eead4).
- `V3_SPACE`: espacio (md=12, lg=16, xl=24, xxl=32, xxxl=48).
- `V3_RADIUS`: radios (sm=6, md=10, lg=14, xl=18, xxl=22, pill=999).
- `V3_SHADOWS`: sombras para QGraphicsDropShadowEffect (sm, md, card, glow).
- `V3_GRADIENTS`: paradas del gradiente firma teal->violet.
- `MOOD_PALETTE`: 10 niveles emocionales (NMMoodEmoji, V3MoodSlider).
- `COLORS["dark_hybrid"]` / `COLORS["light_hybrid"]`: bridge legacy -> v3 via `_bridge_dark()` / `_bridge_light()`.
- `TYPOGRAPHY`: Plus Jakarta Sans como fuente primaria, JetBrains Mono para datos.

### `shared/theme_qt.py`

Helpers Qt + nuevas funciones:

- `C()` / `v3c()` / `qcolor()` / `qfont()` / `sp()` (usa `V3_SP`).
- `v3_shadow()`: crea QGraphicsDropShadowEffect desde V3_SHADOWS.
- `v3_linear_gradient()`: gradiente firma teal->violet.
- `paint_shell_background()`: fondo de ventana con gradiente diagonal + 3 blobs radiales.
- `nm_icon()`: icono SVG via `icons_svg.py` con fallback a QtAwesome.
- `_load_premium_fonts()`: carga Plus Jakarta Sans (4 pesos) + JetBrains Mono (2 pesos) desde `assets/fonts/`.

### `shared/components_qt.py`

Componentes V3 reutilizables (54+ widgets). Cambios recientes:

- **NMCard**: drop shadow + hover elevation + glassmorphism translucido en dark.
- **NMButton**: variante gradient con drop shadow teal.
- **NMHeader**: `home_mode=True` para greeting/subtitle/streak + logos tematicos.
- **NMSidebar**: logo `logos-icon-{light,dark}.png` con sombra ajustada.
- **NMHubSidebar**: 240px, iconos SVG via `nm_icon()`, recoloreo por tema.
- **_LogoLabel**: logos `logos-light.png`/`logos-dark.png` + doble glow dark.
- **NMFocusArc**: glow blur en arco de progreso.
- **NMToggle**: glow track al activarse.
- **_SidebarItem**: fondo accent en activo.

### `shared/icons_svg.py`

Catalogo de 65+ iconos SVG nativos. Usado por `nm_icon()` con prioridad sobre QtAwesome.

### `shared/installer_common.py`

Clase base `InstallerShell` para los 4 instaladores. Logo `logos-dark.png`, footer con botones gradient, stepper compacto + `NMInstallStepper` v3.

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
Handoff de diseno: `neuromood/project/design_handoff_neuromood_v3/README.md`.

### Paleta V3 (activa)

El sistema usa `V3_LIGHT` y `V3_DARK` como paletas canonicas, con bridge legacy `COLORS["dark_hybrid"]` / `COLORS["light_hybrid"]` que mapea claves viejas (`accent`, `bg_primary`, etc.) a valores v3.

| Token | Dark | Light |
|---|---|---|
| bg | `#060912` | `#eef2f8` |
| accent (teal) | `#5eead4` | `#14b8a6` |
| violet | `#c084fc` | `#a855f7` |
| text | `#f1f5f9` | `#0f172a` |
| surface | `rgba(18,25,45,0.7)` | `#ffffff` |

### Efectos visuales aplicados

**Glassmorphism + cards**
- **NMCard**: surface translúcida (dark `rgba(18,28,45,200)` / light `rgba(255,255,255,235)`) + top specular highlight (línea blanca arriba con clip al rounded rect: 28α dark / 180α light) + drop shadow v3 + hover elevation (border `borderSoft → borderStrong`).
- **`glow=True`**: halo concéntrico teal (alpha 96 light / 120 dark) + overlay gradient teal→violet al 10% (solo dark) + drop shadow preset `ring` (light) / `glow` (dark).
- **NMSettingsSection**: misma estructura — drop shadow + top specular highlight + selector `QWidget#NMSettingsSection` específico (evita herencia de border a hijos QLabel).
- **NMCalmBadge**: selector `QWidget#NMCalmBadge` específico para que el border de la card no se propague a los 3 QLabel internos (Calm/N/BPM unificados).

**Botones**
- **NMButton gradient**: drop shadow teal (blur 30 dark / 20 light, alpha 100/55) + scale 0.97 press 100ms.
- **NMButton secondary**: drop shadow neutra sutil (blur 12 dark / 8 light, alpha 80/18).
- **NMButton ghost**: drop shadow mínima (blur 6 dark / 4 light, alpha 50/10).
- **NMPlayButton circular**: drop shadow `sm` (v3_shadow) + surface neutro + border `borderSoft → borderStrong` hover.

**Rings**
- **NMModuleRing**: glow radial teal detrás del arco cuando `pct>0.05` (alpha 70 dark / 30 light) + gradient firma fluyendo a lo largo del arco (no QConicalGradient sino multi-segmento lerp).
- **NMFocusArc** (Suite Respiración/Timer big ring 340): aura radial teal + glow blur teal+violet detrás del arco (ambos temas) + gradient firma fluyendo + halo exterior.
- **NMCycleRing** (Respiración decorativo): contorno gradient firma v3.

**Inputs**
- **NMInput**: `focusInEvent` aplica QGraphicsDropShadowEffect teal glow (16 blur dark / 12 light, alpha 120/70). `focusOutEvent` lo quita.

**Logo**
- **_LogoLabel**: doble glow en dark (teal blur 8 + violet radial). Carga `logos-light.png`/`logos-dark.png`/`logos-icon-*.png`.

**Animaciones**
- **Theme transition 350ms crossfade**: `ThemeManager.switch_mode(modo, animate=True)` toma snapshot QPixmap de cada top-level visible, lo overlay como QLabel, emite `theme_changed`, anima opacity 1→0 con OutCubic. Lock `_transitioning` anti-reentrancia. Opt-out con `animate=False`.
- **NMTypingDots**: 3 dots con sin wave + offset Y `-4px` + alpha 0.4→1.0 + stagger 150ms entre dots (~30fps). Spec README v3 exacta.
- **Hover en cards**: border-color + shadow expansion (blur+offset). Sin scale ni movimiento horizontal.
- **Click en buttons**: scale 0.97 sobre 100ms (`_animate_press_scale`).
- **Breath circle**: `circle_radius`, `glow_alpha`, `text_opacity` como pyqtProperty animadas en cada fase.
- **Sync orb**: pulso animado (alpha oscilante 70-255).

**Shell**
- **Shell windows** (`paint_shell_background`): gradient diagonal `bg+bgAlt` + 3 blobs radiales:
  - dark: teal 25% / violet 22% / cyan 18% (alphas)
  - light: teal 32% / violet 28% / cyan 22% (subidos del 0.12/0.10/0.06 inicial para visibilidad)
- **Sidebar items**: fondo accent (alpha 18) en estado activo.

### Assets de logo

```
assets/logos-light.png       - logo completo para light theme
assets/logos-dark.png        - logo completo para dark theme
assets/logos-icon-light.png  - solo brain para sidebar light
assets/logos-icon-dark.png   - solo brain para sidebar dark
assets/LOGO.png              - fuente original (no usar directamente en UI nueva)
```

### Fuentes

Cargadas desde `assets/fonts/` via `_load_premium_fonts()` en `shared/theme_qt.py`:

- **Plus Jakarta Sans** (primary v3): Regular, Medium, SemiBold, Bold (.ttf) — desde github tokotype
- **DM Sans** (fallback secundario): Regular, Medium, Bold (.ttf) — desde jsdelivr mirror de googlefonts/dm-fonts
- **JetBrains Mono** (timers, IDs, log instalador): Regular, Bold (.ttf) — desde github JetBrains

El loader prefiere Plus Jakarta Sans → DM Sans → Inter → Satoshi. Si ninguna está, cae al sistema (Segoe UI en Windows). Las 9 TTFs se empaquetan en los 6 EXEs (Suite, Hub, 2 Instaladores, 2 Desinstaladores) via `("assets/fonts", "assets/fonts")` en `add_data`.

### Escala de espacio (V3_SP)

```python
V3_SP = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32, "xxxl": 48}
```

Accesible via `sp()` en `theme_qt.py` y `V3_SP` directamente.

### Componentes clave (lista completa)

- `NMWelcomeBar`, `NMStreakBadge`, `NMEmojiPicker`
- `NMPhaseChip`, `NMCycleRing`, `NMCalmBadge`
- `NMTCCStepper`, `NMHeatBar`, `NMDistortionBadge`
- `NMRoutineSection`, `NMCustomCheck`, `NMDayNote`
- `NMMoodContextHeader`, `NMCategoryFilter`, `NMActivityCard`
- `NMPresetChip`, `NMFocusArc`, `NMSessionHistory`, `NMAvisoCard`
- `NMProgressLine`, `NMHubSidebar`, `NMFeaturedCard`, `NMModuleRing`
- `NMPatientRow`, `NMSyncOrb`, `NMSettingsSection`, `NMConfigRow`
- `NMInstallProgress`, `NMInstallStepper`, `NMDataPreserveCard`
- `NMMoodEmoji` (nuevo), `V3MoodSlider` (nuevo), `NMPlayButton` (nuevo)
- `NMIcon` (nuevo, SVG via `nm_icon()`), `NMStatusChip`, `NMSectionCard`
- `NMFormField`, `NMSegmentedChoice`, `NMInput`, `NMToggle`
- `NMChatBubble`, `NMTypingDots`, `NMProviderChip`, `NMQuickAction`
- `NMPatientContext`, `NMToast`, `NMEmptyState`, `NMSkeleton`

## 10. Build Y Distribución

El build debe ejecutarse desde un único BAT oficial:

```text
BUILD_NEUROMOOD.bat
```

Estado vigente desde 2026-05-21 (prompt F0.2.B):

- `BUILD_NEUROMOOD.bat` existe en la raíz y es el launcher oficial. Es un dispatcher delgado: detecta Python (venv activo → `.venv`/`venv` local → `py -3.12` → `py -3` → `python` global) y delega a `build_neuromood.py` raíz pasando todos los flags (`%*`).
- `BUILDER_NUEVO_RAPIDO.bat` queda como **alias temporal** de `BUILD_NEUROMOOD.bat --installer-mode external`, con un `echo [DEPRECATED]` al inicio. Se removerá en un release futuro.
- `BUILDER_VIEJO_LENTO.bat` fue eliminado (legacy).
- `AI_SCRIPTS/build_neuromood.py` fue eliminado (duplicado obsoleto). El único `build_neuromood.py` vigente vive en la raíz del repo.

Salidas esperadas (nombres exactos del build):

```text
dist/NeuroMood Suite/NeuroMood Suite.exe
dist/NeuroMood Hub/NeuroMood Hub.exe
dist/Instalador Suite/Instalador Suite.exe
dist/Instalador Hub/Instalador Hub.exe
dist/Desinstalador Suite/Desinstalador Suite.exe
dist/Desinstalador Hub/Desinstalador Hub.exe
```

Orden de compilacion: Suite -> Hub -> Desinstalador Suite -> Instalador Suite (requiere Suite + Desinstalador) -> Desinstalador Hub -> Instalador Hub (requiere Hub + Desinstalador Hub).

Reglas:

- Limpiar `.spec` al finalizar.
- Limpiar `build/` al finalizar.
- Mantener salida de consola limpia.
- Compilar EXEs finales/oficiales.
- No dejar scripts auxiliares en raíz.
- La lógica de build vive en `build_neuromood.py` (raíz del repo, 20KB); el `.bat` solo delega.
- Hidden imports criticos agregados: `shared.icons_svg`, `shared.visual_qa`, `PyQt6.QtSvg` (para QSvgRenderer del catálogo SVG y NMMoodEmoji).
- Add-data para assets: `assets/fonts/` empaquetado en los 6 targets (Suite, Hub, 2 instaladores, 2 desinstaladores) para que las fuentes premium carguen en EXEs compilados.
- `shared.icons_svg` también en INSTALLER_IMPORTS por consistencia con Suite/Hub (aunque los wizards no usan NMIcon directamente, mantiene el módulo disponible).
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
- `AI_SCRIPTS/_capture_v3_screens.py`: captura PNG de las 11 pantallas v3 (Suite + Hub) en dark + light a `_qa_output/v3_capture/`. Usa subprocess-per-screen (un crash no detiene los demás) y `_ShellWindow` wrapper que pinta `paint_shell_background` para reproducir el look real del runtime. Útil para diff visual contra el mockup HTML del bundle (`neuromood/project/design_handoff_neuromood_v3/NeuroMood Redesign.html`).

### Fidelidad v3 actual

Score estimado: **~97%** vs spec del README handoff v3.

| Área | Score | Notas |
|---|---:|---|
| Tokens foundation (V3_LIGHT/DARK, MOOD_PALETTE, V3_SPACE/RADIUS/SHADOWS/GRADIENTS, TYPOGRAPHY, bridge legacy) | 100% | — |
| Componentes core (NMCard/Button/Ring/Icon/MoodEmoji/Slider/PlayButton/Toggle/ChatBubble/SettingsSection/Input/Tabs) | 98% | NMConfigRow cubierto por NMSettingsSection |
| Glassmorphism + background (shell gradient, blobs, cards translúcidas, top highlight, shadows) | 90% | Sin QGraphicsBlurEffect real (alpha-simulado, decisión consciente por costo runtime) |
| Animaciones (theme crossfade 350ms, hover, press scale 0.97, breath circle, sync orb, typing dots stagger) | 95% | — |
| Pantallas Suite (8 pantallas reescritas con v3 nativo) | 95% | — |
| Pantallas Hub (Pacientes/IA/Config reescritos; Detalle hereda vía bridge) | 85% | 4 tabs DetallePaciente no refactorizadas profundo (heredan tokens v3 vía bridge) |
| Installer / Uninstaller (QSS v3, shell unificado, gradient firma) | 90% | 5+3 page builders heredan QSS, no rescritos individualmente |
| Fuentes premium (Plus Jakarta Sans + DM Sans + JetBrains Mono) | 100% | 9 TTFs cargados via QFontDatabase |
| Sistema iconos SVG (63 iconos + fallback qta + stroke proporcional) | 95% | Lista del README handoff completa |

Validación runtime (`_runtime_smoke.py`): 41/41 OK — 27 imports + 3 fuentes + 63 iconos + 10 niveles MoodEmoji + 6 entry points (Suite/Hub/2 instaladores/2 desinstaladores) construyen sin errores.

Capturas evidencia: 22 PNGs en `_qa_output/v3_capture/` (11 pantallas × dark + light).

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

- Leé primero este archivo, después [AUDITORIA_NEUROMOOD.md](AUDITORIA_NEUROMOOD.md) si vas a tocar Suite/Hub/DB.
- Si vas a implementar una tarea concreta, mirá [PROMPTS_CODEX_IMPLEMENTACION.md](PROMPTS_CODEX_IMPLEMENTACION.md) — puede haber un prompt atómico ya escrito (F0.1.A, F2.0.B, etc.).
- No crees scripts en raíz; usá `AI_SCRIPTS/`.
- No revivas `docs/`, `script tests/` ni carpetas duplicadas.
- No agregues documentación suelta: actualizá este archivo (excepción documentada: los 2 docs nuevos auxiliares ya mencionados arriba).
- No dejes `.spec`, `build/`, `__pycache__` ni outputs temporales.
- No modifiques áreas sensibles sin necesidad clara.

## 15. Auditoría 2026-05 + Decisiones De Producto 2026-05-20/21

Este bloque resume el estado vigente tras la auditoría completa documentada en [AUDITORIA_NEUROMOOD.md](AUDITORIA_NEUROMOOD.md). Cualquier discrepancia entre los archivos: este resumen manda en alto nivel, el .md de auditoría manda en detalle/citas.

### 15.1 Aviso metodológico

La auditoría 2026-05 se hizo **por lectura del código local** (no por ejecución). Cuando se dice "Implementado en código" significa que existe en el repo con sintaxis válida y lógica coherente, pero **NO que el runtime fue verificado en Windows**. Aspectos como animaciones, glow, daemon de bandeja, notificaciones SO, endpoints IA reales, RLS Supabase real, instaladores empacados, SmartScreen, autostart son `NO VERIFICADO EN EJECUCIÓN` o `NO VERIFICABLE SIN EJECUTAR`. Antes de cualquier piloto clínico hay que correr el plan de QA (Parte 10 del .md de auditoría) con apps reales.

### 15.2 Las 8 decisiones de producto vinculantes

Fijadas por el cliente entre 2026-05-20 y 2026-05-21. Se aplican a Partes 7, 8, 9 y al mega plan F0-F9 de la auditoría:

1. ❌ "Modo familiar/cuidador" → ✅ **"Modo privacidad del paciente"** (PIN al abrir Suite, para PCs compartidas). Reusa PBKDF2 ya implementado en `shared/identidad.py`. Implementación en fase F3 (ver prompt `F3.A`).
2. ❌ Diario TEC/ketamina — descartado (sensibilidad clínica/legal alta).
3. ❌ Modo bajo ánimo automático — descartado (sin lógica automática basada en umbrales). Reemplazo: configurabilidad remota en 2 niveles (global del equipo + por paciente).
4. ❌ IA de redacción TCC para paciente — descartado (ética terapéutica). Reemplazo: plantillas TCC configurables por profesionales desde Hub.
5. ❌ Editor de consentimiento legal editable desde Hub — descartado (rompe trazabilidad legal). Los consentimientos siguen versionados en código + `db/legal_consents.sql` + instalador.
6. ❌ Reentrenamiento de prompts IA desde UI — descartado (riesgo legal). Prompts IA quedan versionados en `hub/ia_asistente.py` + tabla `ia_audit_log` para auditoría de outputs (no edición).
7. ❌ Panel de adherencia poblacional con semáforo — descartado (ausencia de uso ≠ baja adherencia). Reemplazo: panel neutral de actividad reciente, sin etiquetas tipo "riesgo"/"crítico".
8. 🔄 Card no-cerrable de indicaciones del profesional — ajustada (mala UX). Versión final: indicación destacada minimizable + estado leída/no leída, sin bloquear UI.

### 15.3 NeuroMood Ánimo Loop — aclaración importante

La regla "sin automatismos por umbrales emocionales" (decisión 3) **NO aplica** a las 3 apps que la Propuesta Base pide explícitamente conectadas por la variable ÁNIMO declarada manualmente por el paciente:

- **Termómetro Emocional** (registra 1-10).
- **Visualizador Evolución Anímica** (gráfica histórica — vive en Hub Tab Registros + mini-stats en Suite + F1 agrega mini-visualizador semanal en Home).
- **Asistente de Activación Conductual** (propone actividades cuyos rangos `animo_min`/`animo_max` define el profesional desde Hub Tab Banco).

Estas 3 apps SÍ usan la variable ánimo, **declarada conscientemente** por el paciente. No es automatismo oculto — es el corazón explícito del producto. Decisión interpretativa documentada: la Propuesta Base habla de "nivel de energía"; el equipo y el practicante acordaron usar ÁNIMO (no se mide ni registra energía como variable separada).

### 15.4 Las 4 brechas críticas detectadas

1. **Configurabilidad remota desde Hub: casi inexistente.** Todo el contenido clínicamente sensible está hardcoded (textos, plantillas TCC, presets respiración 4-7-8, presets timer, secciones rutina, mensajes apoyo, etiquetas ánimo, distorsiones, categorías). Resolución: F2.0-F2.6 con patrón general `hub_config` 2 niveles (ver §15.6).
2. **ConfigView del Hub es lectura pura** ([hub/main_qt.py:562-707](hub/main_qt.py)). Botón "+ Nuevo paciente" sin handler ([hub/main_qt.py:453-455](hub/main_qt.py)). Resolución: F2.0.D + F4.A.
3. **IA sin audit trail clínico.** Multiproveedor funciona pero outputs no persisten. Cero trazabilidad. Resolución: F4.B (tabla `ia_audit_log` + persistencia chat).
4. **🔴 Tags semáforo en el Hub contradicen decisión 7.** Dashboard "Adherencia alta/Riesgo bajo/Agenda al día" + filtro Pacientes "Atención" (adherence<40%). **BLOQUEANTE de aprobación clínica.** Resolución: F0.1.A + F0.1.B (prompts ya escritos).

### 15.5 Interpretaciones específicas de la Propuesta Base (decisión 2026-05-21)

Estos 3 ajustes alinean el producto con la lectura literal de la Propuesta Base que el cliente confirmó:

- **Timer (ítem 3):** "delimitar actividades terapéuticas por tiempo" → el profesional define presets desde Hub. Hoy el paciente elige libre. **NO cumple esta interpretación.** Acción en F2.2.A/B. El permiso `perm_temporizador_manual` pasa a significar "puede usar custom además de los presets asignados".
- **Avisos (ítem 2):** "mensajes de apoyo a horarios fijos determinados por el equipo" → biblioteca de mensajes + plantillas remotas. Hoy el paciente crea libre. **Parcial.** Acción en F2.2.C/D. Además, mover autostart Windows del módulo Avisos al Home Suite como ajuste general (F3.B).
- **Rutina (ítem 6):** opción C — sistema híbrido 3 estados por paciente, configurable desde Hub: `solo_profesional` / `mixto` (default) / `solo_paciente`. Reusa campo `origen` ya implementado en `checklist_tareas`. Acción en F2.3.A/B/C.

### 15.6 Patrón arquitectónico general `hub_config` 2 niveles

**Toda configurabilidad remota** del Hub se piensa con este patrón único (subsección 9.4.A de la auditoría):

```
Capa 1: scope='global'          → vale para todo el equipo
        │
        ▼ override por paciente
Capa 2: scope='patient:<id>'    → sobrescribe solo para ese paciente
```

Implementación:

- Tabla única `hub_config (scope, key, value JSONB, updated_at, updated_by, version)` con UNIQUE `(scope, key)`. Schema en `db/hub_config_schema.sql` (a crear en F2.0.A).
- Util `shared/remote_config.py` con `t(key, default, patient_id=None)` que aplica jerarquía `patient:<id>` → `global` → `default` hardcoded. Cache local en SQLite (`remote_config_cache`).
- Sync extendido con `_importar_hub_config(patient_id)` siguiendo el patrón existente en `shared/sync.py`.
- ConfigView del Hub reestructurada en 2 secciones: "Configuración del equipo" (global) + "Configuración por paciente" (sub-tab en Detalle Paciente).

**Scope de `hub_config` — qué SÍ y qué NO va acá:** solo settings/overrides simples (key/value JSONB liviano). NO van: registros clínicos, consentimientos, banco de actividades, mensajes leídos/no leídos, `ia_audit_log`, reportes, ni entidades con lifecycle propio (FK, sync direccional, append-only, plantillas complejas tipo `tcc_templates`/`routine_templates`). Esas viven en tablas dedicadas (`db/feature_schemas.sql`, a crear en F2.0.A/F2.1.A).

### 15.7 Mega plan por fases (resumen)

Detalle completo en Parte 11 de [AUDITORIA_NEUROMOOD.md](AUDITORIA_NEUROMOOD.md). Prompts atómicos en [PROMPTS_CODEX_IMPLEMENTACION.md](PROMPTS_CODEX_IMPLEMENTACION.md).

- **F0.1 🔴 BLOQUEANTE** — Eliminar tags semáforo del Hub (Dashboard + filtro Atención). 1-2 días.
- **F0.2** — Limpieza repo (REDESIGN/, scripts legacy raíz, `BUILD_NEUROMOOD.bat` consolidado). 2-3 días.
- **F2.0** — Patrón general `hub_config` + util `remote_config.py` + ConfigView reestructurada. **Base de toda configurabilidad.** 1-2 semanas.
- **F2.1** — Schemas Supabase para entidades complejas + tablas cache SQLite. 1 semana.
- **F2.2** — Timer profesional + Avisos plantillas equipo (interpretación Propuesta Base). 1-2 semanas.
- **F2.3** — Rutina sistema 3 estados (opción C). 1-2 semanas.
- **F2.4** — Editores Hub: plantillas TCC + text overrides genérico. 2-3 semanas.
- **F2.5** — Migración progresiva strings hardcoded → `t(key, default)` por módulo (8 sprints A-H).
- **F2.6** — Constructor de informes paramétrico. 1 semana.
- **F3** — Modo privacidad paciente + Settings panel en Home (con autostart movido) + mini-visualizador semanal. 1-2 semanas.
- **F4** — Gestión real de pacientes desde Hub + audit log IA + persistencia chat + panel actividad neutral. 2-3 semanas.
- **F5** — Sync, permisos y seguridad (RLS audit, logs sin PII, anon key audit). 1-2 semanas.
- **F6** — QA e instaladores production-ready (smoke tests CI, consent offline, doc firma código). 1 semana.
- **F7** — Piloto clínico con 3-5 pacientes reales (proceso, no código). 3-4 semanas.
- **F8** — Ajustes post-feedback (iteración vía Hub sin recompilar — si surge código, agregar prompt al .md de prompts).
- **F9** — Release 1.0.

Tiempo total estimado: **5-7 meses** al release con margen. Camino agresivo: 4-5 meses.

### 15.8 Áreas críticas no editables sin permiso explícito

- `db/legal_consents.sql` — versionado legal, decisión 5.
- `installers/installer.py` líneas de consent (`LEGAL_DISCLAIMER_TEXT`, `DISCLAIMER_VERSION`, `PRIVACY_VERSION`) — decisión 5.
- `hub/ia_asistente.py` prompts del sistema (`_IDIOMA`, sistemas de cada función) — decisión 6. Solo `temperature`, `max_tokens`, `provider_preference` pueden ir a `hub_config`.
- `.env`, `SUPABASE_KEY`, `service_role` — seguridad inmutable (sección 8).

### 15.9 Estado de implementación F2 al 2026-05-21

Estado documentado por cambios de código, no por QA completo en builds empaquetados. Antes de uso clínico hay que validar Suite/Hub en Windows real con datos Supabase de prueba.

- **F2.1.B**: `shared/db.py` crea caches SQLite locales para `tcc_templates_cache`, `routine_templates_cache`, `breathing_presets_cache`, `timer_presets_cache` y `support_messages_cache` con `IF NOT EXISTS`, manteniendo migración idempotente.
- **F2.2.A-D**: Timer Suite puede leer presets desde cache local con fallback hardcoded; Hub agrega editores para presets de timer y biblioteca de mensajes; Avisos Suite puede sugerir mensajes desde `support_messages_cache` y respetar permiso manual.
- **F2.3.A-C**: Rutina Suite respeta `rutina_modo` (`solo_profesional`, `mixto`, `solo_paciente`) y muestra badge para tareas manuales; sync importa modo/plantillas; Hub agrega editor/asignador de plantillas de rutina.
- **F2.4.A-B**: Hub suma editores en `hub/editors/` para plantillas TCC y overrides de texto `hub_config` (`text.*`), integrados desde ConfigView o Detalle Paciente según corresponda.
- **F2.5.A**: Home Suite inicia migración de strings UI a `shared.remote_config.t(key, default)` preservando defaults locales.
- **F2.6**: `hub/exportar.py` acepta `secciones`, rango de fechas y nombre de archivo; `_TabRegistros` abre un modal con checklist de Ánimo, Respiración, TCC, Checklist, Timer y Recordatorios. Sin selección programática (`secciones=None`) preserva el comportamiento histórico de exportar todo.

Validaciones puntuales ejecutadas durante implementación:

- `python -m py_compile hub\exportar.py hub\pacientes_qt.py`
- Generación de PDF de prueba con solo Ánimo + TCC y extracción de texto con `PyPDF2`, confirmando ausencia de las otras cuatro secciones.
