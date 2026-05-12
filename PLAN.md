# Refactorización Integral NeuroMood V3 — Plan Final

## Contexto

NeuroMood V3 pasa de ser 7 apps sueltas a una **plataforma clínica unificada** con dos EXEs: uno para paciente (plataforma con módulos en cards) y uno para profesional (Hub con IA de asistencia). Identidad visual hybrid premium en todo. Eliminación de redundancias, sobre-funcionalidades y complejidad innecesaria.

---

## 1. Decisiones Arquitectónicas

| Decisión | Resolución |
|----------|------------|
| **Estructura** | Plataforma unificada: 1 EXE paciente (navegación por cards), 1 EXE Hub profesional |
| **IA** | ELIMINAR del paciente. IMPLEMENTAR en Hub como asistente del terapeuta (autocompletar, sugerir) |
| **Visualizador** | FUSIONAR en módulo Ánimo (ya no app separada) |
| **Identidad visual** | Hybrid premium en TODO (plataforma + Hub + instaladores + desinstaladores) |
| **Instaladores** | 4 archivos separados con módulo compartido `installer_common.py` |
| **Build system** | .bat y .spec refactorizados (2 EXEs paciente+Hub, no 7) |
| **Datos visuales** | El paciente ve lo mínimo funcional. Gráficos/estadísticas/historiales van al Hub |
| **Checklist vs Activación** | 2 módulos separados: Rutina (tareas fijas) + Actividades (sugerencias por ánimo) |
| **Concurrencia Hub** | 1 terapeuta → N pacientes. Supabase timestamps + RLS. Sin conflictos |
| **UI** | Rediseño premium integral: re-skin hybrid en todo + rediseño de módulos sobrecargados |
| **Escalabilidad** | Arquitectura modular para agregar/modificar herramientas sin tocar el core |

---

## 2. Evaluación Feature por Feature

### Módulo: Ánimo (ex-Termómetro + Visualizador)

| Feature actual | Valor clínico | Decisión |
|---------------|:---:|----------|
| Slider 1-10 + emojis + registrar | ALTO | **MANTENER** — core de monitoreo |
| Nota de contexto opcional | ALTO | **MANTENER** — enriquece el registro |
| "¿Cómo te sentís hoy?" con color dinámico | ALTO | **MANTENER** — feedback visual inmediato |
| Solo 1 registro por día (restricción) | MEDIO | **ELIMINAR restricción** — permitir múltiples (premisa original dice "registro diario", no "uno por día") |
| Historial consultable por paciente | BAJO | **MOVER AL HUB** — dato del profesional |
| Gráficos de evolución (línea + área) | BAJO | **MOVER AL HUB** — el paciente no los interpreta |
| Estadísticas (promedio, máximo, tendencia) | BAJO | **MOVER AL HUB** |
| Exportación PNG de gráficos | BAJO | **MOVER AL HUB** (como PDF) |
| Sugerencia automática de actividades al checklist | N/A | **ELIMINAR** — Ánimo solo registra ánimo, no sugiere ni conecta con otros módulos |
| Visualizador como app separada (664L) | REDUNDANTE | **ELIMINAR** — absorbido en Hub |
| Contador animado de promedio | NULO | **ELIMINAR** |

**Resultado paciente**: Slider + emoji + nota + botón Registrar. Limpio, rápido, sin ruido.

### Módulo: Respiración

| Feature actual | Valor clínico | Decisión |
|---------------|:---:|----------|
| Animación circular inhalar/retener/exhalar | ALTO | **MANTENER** — guía visual terapéutica |
| Técnica 4-7-8 | ALTO | **MANTENER** como default |
| Otras técnicas configurables | BAJO | **SIMPLIFICAR** — max 2-3 técnicas, no configurable por paciente |
| Duración configurable (1-15 min) | MEDIO | **MANTENER** simplificado (3/5/10 min presets) |
| Pausa y detener | ALTO | **MANTENER** |
| Contador de ciclos durante sesión | MEDIO | **MANTENER** — da sensación de progreso |
| Registro automático en DB | MEDIO | **MANTENER** (dato para el Hub) pero invisible al paciente |
| Historial de sesiones (visible al paciente) | BAJO | **MOVER AL HUB** |

**Resultado paciente**: Elegir duración (3/5/10 min) → Iniciar → Animación guía → Fin. Sin historial ni stats visibles.

### Módulo: Registro de Pensamientos (TCC)

| Feature actual | Valor clínico | Decisión |
|---------------|:---:|----------|
| Paso 1: Situación | ALTO | **MANTENER** |
| Paso 2: Emoción + intensidad | ALTO | **MANTENER** (simplificar: nombre de emoción + slider intensidad) |
| Paso 3: Pensamiento automático | ALTO | **MANTENER** |
| Paso 4: Respuesta alternativa | ALTO | **MANTENER** |
| 10 distorsiones cognitivas (catálogo) | ALTO | **MANTENER** — core TCC |
| Detección automática por keywords | MEDIO | **MANTENER** como sugerencia sutil |
| Evidencias a favor/en contra | MEDIO | **EVALUAR** — valioso en TCC avanzada pero pesado. MANTENER como paso opcional |
| Creencia antes/después (0-100%) | MEDIO | **SIMPLIFICAR** — solo mostrar si terapeuta lo habilita desde Hub |
| IA Groq feedback interactivo | ELIMINAR | **ELIMINAR** — no recomendado clínicamente |
| IA preguntas por sesión | ELIMINAR | **ELIMINAR** — usar preguntas fijas predecibles |
| Historial + buscador de registros | BAJO | **MOVER AL HUB** |
| Indicador visual de progreso (6 pasos) | ALTO | **MANTENER** — guía al paciente |
| 6 pasos (Situación, Emoción, Pensamiento, Análisis, Respuesta, Cierre) | MEDIO | **REDUCIR a 4-5** (unificar Análisis+Respuesta, eliminar Cierre separado) |

**Resultado paciente**: Wizard de 4 pasos claro: Situación → Emoción → Pensamiento (con distorsiones sugeridas) → Respuesta alternativa. Guardar. Sin historial visible.

### Módulo: Rutina (ex-Checklist)

| Feature actual | Valor clínico | Decisión |
|---------------|:---:|----------|
| 3 secciones: Mañana, Tarde, Noche | ALTO | **MANTENER** |
| Agregar/completar/eliminar tareas | ALTO | **MANTENER** |
| Tareas asignadas por terapeuta (Hub) | ALTO | **MANTENER** — premisa core |
| Sonido al completar | MEDIO | **MANTENER** — feedback positivo |
| Gráfico circular de progreso diario | BAJO | **SIMPLIFICAR** — solo texto "4/6 completadas" |
| Historial semanal navegable con barras | BAJO | **MOVER AL HUB** |
| Seguimiento de días consecutivos | BAJO | **ELIMINAR** — puede generar presión en pacientes depresivos |
| Estadísticas 30 días | BAJO | **MOVER AL HUB** |
| Nota del día | MEDIO | **MANTENER** — simple |
| Filtrado por nivel de ánimo | N/A | **ELIMINAR** — lógica de ánimo pertenece al módulo Actividades, no a Rutina |
| Pestaña "Propuestas" banco conductual | N/A | **MOVER** a módulo Actividades — pertenece al motor de activación, no a Rutina |
| Categorías (Logro, Placer, Autocuidado, Social) | MEDIO | **MANTENER** simplificado |

**Resultado paciente**: Lista del día (Mañana/Tarde/Noche) + checkbox + contador simple "4/6". Sin gráficos, sin seguimiento de días.

### Módulo: Timer (ex-Temporizador)

| Feature actual | Valor clínico | Decisión |
|---------------|:---:|----------|
| Cuenta regresiva visual | ALTO | **MANTENER** — premisa original |
| Sonido al finalizar | ALTO | **MANTENER** |
| 5 categorías (Relajación, Cognitiva, Física, Social, Autocuidado) | MEDIO | **MANTENER** |
| Presets terapéuticos configurables | MEDIO | **SIMPLIFICAR** — presets fijos del terapeuta, paciente solo elige |
| Duración configurable 1-30 min | ALTO | **MANTENER** |
| Pausar/Reanudar/Reiniciar | ALTO | **MANTENER** |
| Indicador circular de progreso | ALTO | **MANTENER** — visual motivador |
| Historial de sesiones + duraciones | BAJO | **MOVER AL HUB** |
| Bandeja del sistema (pystray) | MEDIO | **MANTENER** — permite usar otra app mientras corre |
| Editor de presets (paciente) | BAJO | **ELIMINAR** del paciente — solo edita el terapeuta |

**Resultado paciente**: Elegir preset (o custom) → Iniciar → Progreso circular → Suena al terminar. Sin historial visible.

### Módulo: Avisos (ex-Recordatorios)

| Feature actual | Valor clínico | Decisión |
|---------------|:---:|----------|
| Crear recordatorio con hora + días + mensaje | ALTO | **MANTENER** — premisa original |
| Notificación sonora | ALTO | **MANTENER** |
| Bandeja del sistema (pystray) | ALTO | **MANTENER** — fundamental para background |
| Horario de silencio | MEDIO | **MANTENER** — respetar descanso |
| Pausa/eliminación individual | ALTO | **MANTENER** |
| Log de recordatorios disparados | BAJO | **MOVER AL HUB** |
| Mensajes biblioteca predefinidos | BAJO | **SIMPLIFICAR** — solo si terapeuta los configura |
| Recordatorios remotos del terapeuta | ALTO | **MANTENER** — premisa core del Hub |
| Arranque con Windows (winreg) | MEDIO | **MANTENER** como opción |

**Resultado paciente**: Lista de avisos + crear/editar/eliminar + silencio. Funciona en background.

### Módulo: Actividades (Activación Conductual) — MÓDULO SEPARADO DE RUTINA

| Feature actual | Valor clínico | Decisión |
|---------------|:---:|----------|
| Sugerir actividades por ánimo | ALTO | **MANTENER** — card propia, se activa tras registro de ánimo |
| Banco de actividades editable | ALTO | **MANTENER** — solo el terapeuta edita (Hub) |
| 7 categorías con colores | MEDIO | **SIMPLIFICAR** a 4-5 relevantes |
| Análisis de patrones (analisis.py) | BAJO | **MOVER AL HUB** |
| Perfil de preferencias (perfil.py) | BAJO | **MOVER AL HUB** — terapeuta configura |
| Resultado: hecha/intentada/no_pude | ALTO | **MANTENER** — feedback conductual |

**Resultado paciente**: Card "Actividades" → muestra 2-3 sugerencias adaptativas según ánimo declarado. El paciente elige y reporta resultado. No es lo mismo que Rutina (tareas fijas del terapeuta).

**Diferencia clave con Rutina:**
- **Rutina** = prescripción directa del terapeuta. Estática. El paciente ejecuta.
- **Actividades** = sugerencias adaptativas del motor según energía/ánimo. Dinámicas. El paciente elige.

**Motor interno** (`app/motor_activacion.py`): alimenta la card de Actividades con sugerencias filtradas por `animo_min`/`animo_max` del banco. También alimenta al Hub con datos de adherencia y preferencias.

---

## 3. Arquitectura de la Plataforma Unificada

### 3.1 EXE Paciente: `NeuroMood.exe`

```
Ventana normal (ej. 800x600):
┌─────────────────────────────────────────────────────────┐
│  NeuroMood — Hola, [Nombre]                  [☀/☾] [?] │
│─────────────────────────────────────────────────────────│
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Ánimo     │  │   Respirar   │  │   Registro   │  │
│  │   [emoji]    │  │    ◯ 4-7-8   │  │    TCC 📝    │  │
│  │    7/10 ✔    │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Rutina    │  │ Actividades  │  │    Timer     │  │
│  │    4/6 ✓     │  │   2 suger.   │  │   ⏱ 5:00    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Avisos  🔔 3 activos                   │ │
│  └────────────────────────────────────────────────────┘ │
│                            neuromood.com.ar              │
└─────────────────────────────────────────────────────────┘

Ventana angosta (ej. 500x700):
┌───────────────────────────────┐
│  NeuroMood         [☀/☾] [?] │
│───────────────────────────────│
│  ┌────────────┐ ┌────────────┐│
│  │   Ánimo    │ │  Respirar  ││
│  └────────────┘ └────────────┘│
│  ┌────────────┐ ┌────────────┐│
│  │  Registro  │ │   Rutina   ││
│  └────────────┘ └────────────┘│
│  ┌────────────┐ ┌────────────┐│
│  │Actividades │ │   Timer    ││
│  └────────────┘ └────────────┘│
│  ┌────────────────────────────┐│
│  │     Avisos  🔔 3           ││
│  └────────────────────────────┘│
└───────────────────────────────┘
```

**Layout adaptativo (tipo app móvil):**
- Grid con `columnconfigure` weight para que las cards se expandan y llenen el espacio
- 7 cards impares: la última (Avisos) ocupa todo el ancho como banner horizontal
- Al redimensionar ventana: pasa de 3 columnas a 2 columnas automáticamente
- Cards tienen aspect ratio flexible — se estiran horizontalmente para evitar huecos
- Implementación: `CTkScrollableFrame` con cards que usan `grid` + `sticky="nsew"` + peso en columnas

- **Navegación**: Click en card → abre módulo. Botón ← volver al home.
- **Estado en cards**: Cada card muestra estado del día (ánimo registrado, tareas completadas, etc.)
- **Un solo proceso**: Todo corre en la misma ventana/proceso.
- **Background**: Avisos (recordatorios) sigue corriendo en bandeja cuando se cierra la ventana principal.
- **Sin modo ánimo bajo** — la UI es simple de base para todos los estados.
- **Sin disclaimer de crisis** — no se agrega.

### 3.2 Estructura de Archivos

```
Neuromood V3/
├── app/                             # Plataforma paciente
│   ├── main.py                      # Entry point: plataforma unificada
│   ├── home.py                      # Vista Home con cards
│   ├── modules/
│   │   ├── animo.py                 # Módulo Ánimo (slider + nota + registrar)
│   │   ├── respiracion.py           # Módulo Respiración (animación + timer)
│   │   ├── registro_tcc.py          # Módulo Registro de Pensamientos (wizard 4 pasos)
│   │   ├── rutina.py                # Módulo Rutina (checklist fija del terapeuta)
│   │   ├── actividades.py           # Módulo Actividades (sugerencias adaptativas por ánimo)
│   │   ├── timer.py                 # Módulo Timer
│   │   └── avisos.py               # Módulo Recordatorios
│   └── motor_activacion.py          # Motor interno (alimenta módulo Actividades)
├── hub/                             # Hub Profesional (Dashboard + Nav colapsable)
│   ├── main.py                      # Entry point: ventana + nav lateral + routing
│   ├── dashboard.py                 # Vista Dashboard (cards de todos los pacientes + sugerencias IA)
│   ├── pacientes.py                 # Gestión: alta, baja, códigos de vinculación
│   ├── detalle_paciente.py          # Vista detallada con tabs (Evolución | Asignar | Reportes)
│   ├── visualizacion.py             # Gráficos y estadísticas (absorbido del ex-Visualizador)
│   ├── asignaciones.py              # Asignar tareas, recordatorios, presets al paciente
│   ├── banco.py                     # Banco de actividades + plantillas + presets
│   ├── ia_asistente.py              # IA: autocompletar, sugerir, resumir datos
│   └── exportar.py                  # PDF, reportes
├── shared/
│   ├── theme.py                     # ← theme_hybrid.py (canónico)
│   ├── components.py                # ← components_hybrid.py (canónico)
│   ├── base_module.py               # Clase base para módulos de la plataforma
│   ├── db.py                        # SQLite con migraciones versionadas
│   ├── sync.py                      # Supabase (sin keys hardcoded)
│   ├── config.py                    # Lectura de .env para secrets
│   ├── identidad.py                 # ID paciente
│   ├── utils.py                     # Utilidades
│   └── installer_common.py          # Código compartido de instaladores
├── installer.py                     # Instalador Suite (refactorizado)
├── installer_pro.py                 # Instalador Hub (refactorizado)
├── uninstaller.py                   # Desinstalador Suite (refactorizado)
├── uninstaller_pro.py               # Desinstalador Hub (refactorizado)
├── installer.spec                   # Spec actualizado (1 EXE paciente)
├── installer_pro.spec               # Spec Hub
├── uninstaller.spec
├── uninstaller_pro.spec
├── BUILD_ALL.bat                    # Compila: NeuroMood.exe + HubProfesional.exe
├── BUILD_INSTALLER.bat              # Compila instalador paciente
├── BUILD_INSTALLER_PRO.bat          # Compila instalador Hub
├── tests/
│   ├── test_db.py
│   ├── test_sync.py
│   └── test_motor.py
├── _dev/                            # Solo desarrollo
│   └── previews/
├── LOGO.png
├── NM_icon.ico
├── installer_icon.ico
├── no_symbol.ico
├── requirements.txt
└── supabase_schema.sql
```

### 3.3 Archivos ELIMINADOS (limpieza total)

| Eliminado | Razón |
|-----------|-------|
| `apps/` (carpeta completa) | Reemplazada por `app/` (plataforma) y `hub/` |
| `apps/visualizador/` | Funcionalidad movida al Hub |
| `apps/pensamientos/ia.py` | IA eliminada del paciente |
| `shared/theme_hybrid.py` | Renombrado a `shared/theme.py` |
| `shared/components_hybrid.py` | Renombrado a `shared/components.py` |
| `shared/theme.py` (viejo) | Reemplazado |
| `shared/components.py` (viejo) | Reemplazado |
| 8 archivos `.spec` en apps/ | No usados |
| `_preview_neuromood.py` | Movido a `_dev/` |
| `_preview_fusion.py` | Movido a `_dev/` |
| `_preview_light.py` | Movido a `_dev/` |
| `README_MIGRACION.md` | Obsoleto post-migración |
| `dark-theme-tests.md` | Referencia obsoleta |
| `white-theme-tests.md` | Referencia obsoleta |
| `notion-visual-identity.md` | Referencia obsoleta |
| `IDENTIDAD_VISUAL.md` | Se regenera post-refactor |

### 3.4 Clase Base para Módulos

```python
# shared/base_module.py
class NMModule(ctk.CTkFrame):
    """Clase base para cada módulo de la plataforma paciente."""
    
    MODULE_TITLE: str
    MODULE_ICON: str  # emoji para la card del home
    
    def __init__(self, master, modo: str, theme_manager, on_back):
        super().__init__(master, fg_color="transparent")
        self.modo = modo
        self.tm = theme_manager
        self._on_back = on_back
        self._build_header()  # ← Volver + título
        self.build_ui()       # Template method
    
    def build_ui(self):
        raise NotImplementedError
    
    def get_card_status(self) -> str:
        """Estado para mostrar en la card del home (ej: '7/10 ✔')."""
        return ""
```

### 3.5 Hub Profesional — Dashboard + Nav Colapsable

```
┌───┬──────────────────────────────────────────────────┐
│📊 │  Dashboard — [N] pacientes activos                │
│👥 │                                                    │
│📝 │  ┌────────────┐ ┌────────────┐ ┌────────────┐    │
│🤖 │  │ María L.   │ │ Juan P.    │ │ Ana R.     │    │
│⚙️ │  │ Ánimo: 7   │ │ Ánimo: 4   │ │ Ánimo: 8   │    │
│   │  │ Rutina:78% │ │ Rutina:45% │ │ Rutina:90% │    │
│   │  └────────────┘ └────────────┘ └────────────┘    │
│   │                                                    │
│   │  🤖 Sugerencias IA:                               │
│   │  • Juan bajó adherencia → sugerir actividad fácil │
│   │  • María: subir dificultad actividades            │
│   │    [Aplicar] [Editar] [Descartar]                 │
└───┴──────────────────────────────────────────────────┘
```

**Nav lateral (colapsable a íconos)**:
- 📊 Dashboard (vista general de todos los pacientes)
- 👥 Pacientes (gestión: alta, baja, códigos)
- 📝 Asignar (tareas rutina + config activación + recordatorios + presets)
- 🤖 IA Asistente (configurar, ver historial de sugerencias)
- ⚙️ Config (banco de actividades, plantillas, ajustes)

**Flujo**: Dashboard → click en paciente → vista detallada con tabs (Evolución | Rutina | Activación | Reportes)

**Hub diferencia Rutina vs Activación:**
- Tab "Rutina": ver adherencia %, asignar/editar tareas fijas por sección (mañana/tarde/noche)
- Tab "Activación": ver sugerencias aceptadas/rechazadas, editar banco de actividades, ajustar rangos de ánimo, ver resultados (hecha/intentada/no_pude)

**IA en Hub** (`hub/ia_asistente.py`):
```python
"""
IA asistente para el terapeuta. NO interactúa con el paciente.
Usa Groq (llama3-70b) para:
1. Autocompletar datos de actividades/tareas al escribir
2. Sugerir acciones basadas en datos del paciente
3. Resumir evolución en lenguaje natural
4. Generar borradores de tareas/presets personalizados

El terapeuta SIEMPRE aprueba antes de que algo llegue al paciente.
Interfaz: sugerencia inline con [Aplicar] [Editar] [Descartar]
"""
```

---

## 4. Build System Refactorizado

### BUILD_ALL.bat

```
Antes: compila 7 EXEs paciente + 1 Hub = 8 builds
Ahora: compila 1 EXE paciente (NeuroMood.exe) + 1 Hub (HubProfesional.exe) = 2 builds
```

Reducción de tiempo de compilación: ~75%

### installer.spec

```
Antes: bundlea 6 EXEs + desinstalador dentro del instalador
Ahora: bundlea 1 EXE (NeuroMood.exe) + desinstalador
```

Reducción de tamaño del instalador: significativa (1 EXE en vez de 6).

### Cambios clave:

| Archivo | Cambio |
|---------|--------|
| `BUILD_ALL.bat` | De 7 pyinstaller calls a 2. Hidden imports actualizados. |
| `BUILD_INSTALLER.bat` | Verifica 1 EXE en vez de 6. |
| `installer.spec` | datas: solo NeuroMood.exe + desinstalador |
| `installer.py` | Sin selector de apps (se instala completa). Theme hybrid. |
| `uninstaller.py` | NM_PROCESOS: solo "NeuroMood.exe". Theme hybrid. |

---

## 5. Simplificaciones del Instalador

Con plataforma unificada, el instalador se simplifica enormemente:

**Antes**: 5 páginas (Bienvenida → Registro → Selección de apps → Instalación → Finalizar)
**Ahora**: 4 páginas (Bienvenida → Registro → Instalación → Finalizar)

Se elimina la página de "Selección de apps" — se instala toda la plataforma como unidad.

---

## 6. Roadmap por Fases

### FASE 0: Seguridad + Limpieza (2-3 días)

- [ ] Extraer credenciales Supabase a .env
- [ ] Crear `shared/config.py` (lector de secrets)
- [ ] Eliminar `apps/pensamientos/ia.py` y toda referencia Groq en paciente
- [ ] Eliminar los 8 .spec de apps/
- [ ] Mover `_preview_*.py` a `_dev/`
- [ ] Eliminar archivos de referencia obsoletos
- [ ] Rotar keys Supabase comprometidas
- [ ] Agregar `.env` a `.gitignore`

### FASE 1: Identidad Visual + installer_common (1 semana)

- [ ] Swap: `theme_hybrid.py` → `shared/theme.py`, `components_hybrid.py` → `shared/components.py`
- [ ] Eliminar theme.py y components.py viejos
- [ ] Crear `shared/installer_common.py`
- [ ] Migrar los 4 instaladores/desinstaladores al theme hybrid
- [ ] Verificar compilación de instaladores

### FASE 2: Plataforma Paciente Unificada (2-3 semanas)

- [ ] Crear `app/main.py` — ventana principal con navegación cards
- [ ] Crear `app/home.py` — grid de cards con estado
- [ ] Crear `shared/base_module.py` — clase base
- [ ] Migrar Ánimo: `app/modules/animo.py` (solo slider + nota + registrar)
- [ ] Migrar Respiración: `app/modules/respiracion.py` (animación + presets simples)
- [ ] Migrar Registro TCC: `app/modules/registro_tcc.py` (wizard 4 pasos, sin IA)
- [ ] Migrar Rutina: `app/modules/rutina.py` (checklist fija: mañana/tarde/noche + checkbox)
- [ ] Crear Actividades: `app/modules/actividades.py` (sugerencias adaptativas por ánimo)
- [ ] Migrar Timer: `app/modules/timer.py` (countdown + presets)
- [ ] Migrar Avisos: `app/modules/avisos.py` (recordatorios + bandeja sistema)
- [ ] Crear `app/motor_activacion.py` (motor que alimenta módulo Actividades)
- [ ] Integrar ThemeManager global
- [ ] Verificar todo funciona como plataforma unificada (7 cards)

### FASE 3: Hub Profesional Refactorizado (1-2 semanas)

- [ ] Refactorizar `hub/main.py` — UI intuitiva, flujo claro
- [ ] Crear `hub/visualizacion.py` — gráficos/estadísticas (lo que se sacó del paciente)
- [ ] Crear `hub/ia_asistente.py` — autocompletar + sugerir + resumir
- [ ] Migrar asignaciones (tareas, recordatorios, presets)
- [ ] Migrar gestión de pacientes
- [ ] Migrar exportación PDF

### FASE 4: Build System + Instaladores (3-5 días)

- [ ] Reescribir BUILD_ALL.bat (2 EXEs: NeuroMood.exe + HubProfesional.exe)
- [ ] Actualizar BUILD_INSTALLER.bat
- [ ] Actualizar BUILD_INSTALLER_PRO.bat
- [ ] Actualizar los 4 .spec de root
- [ ] Simplificar installer.py (sin página de selección de apps)
- [ ] Verificar compilación + instalación end-to-end
- [ ] Verificar desinstalación end-to-end

### FASE 5: Testing + Estabilización (1 semana)

- [ ] Tests unitarios para db.py, sync.py, motor_activacion.py
- [ ] Smoke test: compilar → instalar → usar cada módulo → desinstalar
- [ ] Verificar sync paciente↔Hub
- [ ] Actualizar README
- [ ] Documentar build process

**Total estimado: ~6-7 semanas**

---

## 7. Escalabilidad

La nueva arquitectura permite:

| Operación futura | Cómo se logra |
|------------------|---------------|
| Agregar nuevo módulo al paciente | Crear `app/modules/nuevo.py` que hereda `NMModule` + registrar en home.py |
| Modificar flujo de un módulo | Editar solo ese archivo de módulo |
| Actualizar identidad visual | Cambiar `shared/theme.py` — se propaga a todo |
| Agregar funcionalidad al Hub | Nuevo archivo en `hub/` |
| Cambiar de Supabase a otro backend | Solo modificar `shared/sync.py` |
| Agregar soporte de idiomas | i18n en un archivo central, módulos lo consumen |
| Migrar de CustomTkinter a otro framework | Los módulos tienen lógica separada de UI vía `base_module.py` |
| Updates al paciente | Un solo EXE a reemplazar |

---

## 8. Rediseño UI Premium

Cada módulo recibe tratamiento visual según su estado actual:

| Módulo | Nivel de rediseño | Detalle |
|--------|:-----------------:|---------|
| Respiración | **Rediseño pro** | Pantalla inmersiva: animación central grande, presets como pills seleccionables (no dropdown), feedback háptico visual al cambiar fase, progreso de sesión sutil. Sin chrome innecesario. |
| Ánimo | **Rediseño pro** | Slider reimaginado: más grande, con gradiente de color dinámico, emoji animado que acompaña al valor. Nota como textarea expandible. Feedback visual inmediato al registrar. Sin stats. |
| Timer | **Rediseño pro** | Pantalla centrada en el countdown: arco de progreso grande y limpio, preset selector como chips horizontales, controles (pausa/stop) como íconos minimalistas. Sin historial. |
| Registro TCC | **Rediseño completo** | De 6 pasos a 4. Wizard con indicador de progreso elegante, un paso por pantalla, transiciones suaves. Cards para distorsiones (no lista plana). Sin IA. |
| Rutina | **Rediseño completo** | Tres secciones colapsables (Mañana/Tarde/Noche) con animación al completar. Checkbox con micro-animación + sonido. Contador "4/6" como badge premium. Sin gráficos, sin seguimiento de días. |
| Actividades | **Nuevo — diseño pro** | Cards de actividad sugerida con categoría coloreada, descripción corta, y 3 botones de resultado (hecha/intentada/no pude) con feedback visual. |
| Avisos | **Rediseño pro** | Cada recordatorio como card individual (no lista plana): icono + hora + días + toggle pausa. Crear/editar en modal limpio. |
| Hub | **Rediseño completo** | Dashboard + nav colapsable + cards pacientes + IA inline + tabs por paciente. |
| Instaladores (4) | **Rediseño completo** | De paleta hardcoded a hybrid. Wizard pages con transiciones, componentes premium. Via `installer_common.py`. |

**Filosofía de diseño**: Cada pantalla tiene un propósito claro y un foco visual principal. Sin clutter, sin opciones que no se usan, sin información que no aporta al momento. Producto clínico profesional = simple, elegante, funcional.

**Componentes hybrid reutilizados** (ya existen en `components_hybrid.py`):
- `CardFrame` → cards del home + cards de pacientes en Hub
- `HeaderFrame` → header de cada módulo con botón volver
- `BotonPrimario` / `BotonSecundario` → acciones
- `BadgeLabel` → estados, contadores
- `InputTexto` / `AreaTexto` → formularios
- `NMToplevel` → diálogos
- `aplicar_captionbar()` → integración nativa Windows
- `ThemeManager` → switch dark/light reactivo sin reiniciar

---

## 9. Concurrencia y Sincronización

**Modelo**: 1 terapeuta → N pacientes (vinculación por código único).

**Flujo de datos**:
- Paciente ESCRIBE → registros de ánimo, pensamientos, rutina completada, actividades
- Hub LEE → datos del paciente para visualización y análisis
- Hub ESCRIBE → asignaciones (tareas, recordatorios, presets)
- Paciente LEE → asignaciones del terapeuta

**Sin conflictos**: No hay escritura concurrente al mismo recurso. Supabase `updated_at` + RLS garantizan consistencia.

**Escalabilidad futura** (si se necesita co-terapia): Supabase Realtime puede notificar cambios.

---

## 10. Compliance y Seguridad

| Requisito | Implementación | Fase |
|-----------|----------------|:----:|
| Credenciales no en código | .env + shared/config.py | 0 |
| IA no interactúa con paciente | Eliminada | 0 |
| Datos del paciente protegidos | RLS en Supabase + .env | 0 |
| Terapeuta aprueba antes de enviar | UI del Hub con [Aplicar/Editar/Descartar] | 3 |

---

## 11. Riesgos y Mitigaciones

| Riesgo | Prob. | Impacto | Mitigación |
|--------|:-----:|:-------:|------------|
| Keys comprometidas en git | ALTA | CRÍTICO | Rotar en Fase 0 |
| Regresión funcional al unificar | MEDIA | ALTO | Migrar módulo por módulo, testear cada uno |
| Complejidad de navegación en plataforma unificada | BAJA | MEDIO | Cards son simples; un click = un módulo |
| Recordatorios dejan de funcionar sin bandeja | MEDIA | ALTO | Mantener pystray; plataforma puede cerrarse sin matar proceso de avisos |
| Build time aumenta por EXE grande | BAJA | BAJO | PyInstaller --onefile; UPX compression |
| CustomTkinter limita diseño de cards | MEDIA | MEDIO | Cards son CTkFrames con hover — ya probado en hybrid |

---

## 12. Verificación End-to-End

| Fase | Verificación |
|------|-------------|
| 0 | Apps arrancan sin keys en código. ia.py no existe. |
| 1 | Instaladores muestran paleta hybrid. Caption bar correcta Win10/11. |
| 2 | `python app/main.py` → Home con 7 cards → cada módulo funciona → volver al home. Datos se guardan en SQLite. |
| 3 | `python hub/main.py` → Ver pacientes → Estadísticas/gráficos → IA autocompleta → Asignar tarea. |
| 4 | `BUILD_ALL.bat` genera 2 EXEs. `BUILD_INSTALLER.bat` genera instalador funcional. Instalación + desinstalación OK. |
| 5 | `pytest tests/ -v` pasa. Sync funcional. |

---

## Archivos Críticos — Resumen

| Archivo | Acción | Fase |
|---------|--------|:----:|
| `shared/sync.py` | Extraer credenciales | 0 |
| `apps/pensamientos/ia.py` | ELIMINAR | 0 |
| 8 `.spec` en apps/ | ELIMINAR | 0 |
| `shared/theme_hybrid.py` → `shared/theme.py` | Renombrar | 1 |
| `shared/components_hybrid.py` → `shared/components.py` | Renombrar | 1 |
| NUEVO: `shared/installer_common.py` | Crear | 1 |
| NUEVO: `shared/config.py` | Crear | 0 |
| 4 instaladores/desinstaladores | Refactorizar con installer_common + hybrid | 1 |
| NUEVO: `app/main.py` | Plataforma unificada paciente | 2 |
| NUEVO: `app/home.py` | Vista Home con cards | 2 |
| NUEVO: `shared/base_module.py` | Clase base módulos | 2 |
| NUEVO: `app/modules/*.py` (7 archivos) | Módulos de la plataforma (incl. actividades.py separado de rutina.py) | 2 |
| NUEVO: `hub/ia_asistente.py` | IA para terapeuta | 3 |
| `hub/main.py` (ex hub_profesional) | Refactorizar UI + absorber estadísticas | 3 |
| `BUILD_ALL.bat` | Reescribir (2 EXEs) | 4 |
| `installer.spec` | Actualizar (1 EXE + desinstalador) | 4 |
| `installer.py` | Simplificar (sin selección de apps) | 4 |
| `apps/` (carpeta completa) | ELIMINAR al final de Fase 2 | 2 |
