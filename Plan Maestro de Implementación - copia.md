Fase 1: Auditoría y Catálogo de Textos (Sin cambios en el código)
Objetivo: Identificar qué hay que proteger y qué hay que configurar.
Exploración: El agente debe inspeccionar el repositorio (específicamente hub/config_global_suite.py, shared/text_overrides.py y los módulos en app/modules/)
.
Identificación: Localizar dónde se activan actualmente datos falsos (NM_VISUAL_QA) y dónde se instancian módulos reales para eliminarlos luego
.
Catálogo: Crear una lista de todos los textos estáticos editables y sus claves (ej: text.module.timer.empty_title)
.
Entregable: Un informe con los riesgos detectados y el mapa de textos antes de tocar una sola línea de código
.
Fase 2: Blindaje de la Suite Real (Corrección del Temporizador)
Objetivo: Asegurar que la aplicación que usan los pacientes sea robusta antes de crear el editor.
Pantalla Empty del Temporizador: Modificar app/modules/timer_qt.py para que, si no hay tareas asignadas, muestre un estado vacío real y no intente cargar la interfaz de conteo
.
Consistencia: Asegurar que el Temporizador se comporte como los otros módulos (Rutina, Activación), mostrando un mensaje de "Esperando asignación"
.
Entregable: Capturas de la Suite real funcionando correctamente en estado vacío
.
Fase 3: El Motor de Previsualización Seguro (Arquitectura)
Objetivo: Construir la infraestructura donde el profesional editará los textos sin riesgos.
Creación de suite_text_preview.py: Un nuevo archivo que construya widgets visuales pero inertes
.
Aislamiento Total: Prohibir explícitamente en este motor el acceso a la Base de Datos, timers (QTimer), y lógica de sincronización
.
Datos Neutros: Implementar un sistema que muestre "Actividades de ejemplo" que no sean editables ni se guarden, solo para que el profesional vea el diseño
.
Entregable: Una pantalla de prueba que demuestre que se puede ver la interfaz sin ejecutar lógica clínica
.
Fase 4: Migración Iterativa de Pantallas
Objetivo: Habilitar la edición visual pantalla por pantalla.
Migración por bloques: Implementar la previsualización y edición de:
Home y Onboarding
.
Módulos asignables (Recordatorios, Temporizador, Rutina, Activación)
.
Límites de Caracteres: Configurar límites específicos para cada campo para que el texto nunca rompa el layout de 960x600
.
Modos duales: Cada módulo debe tener dos vistas en el editor: "Interfaz" (con datos neutros) y "Estado vacío"
.
Entregable: Matriz de textos editables y capturas de cada estado
.
Fase 5: Persistencia y Sincronización Global
Objetivo: Que los cambios se guarden y lleguen a los pacientes de forma segura.
Sistema de Overrides: Conectar el botón "Guardar cambios" para que solo persista pares de clave:valor en shared/text_overrides.py
.
Botón Restaurar: Implementar la función que borra todos los cambios y devuelve la Suite a sus textos originales
.
Validación de No-Interferencia: Confirmar que guardar un texto no borra el progreso de ningún paciente real
.
Fase 6: Limpieza y QA Final
Objetivo: Eliminar el código antiguo y validar la seguridad.
Eliminación: Retirar _CloneDB y cualquier rastro de la implementación anterior que usaba módulos reales bloqueados
.
Pruebas de Estrés: Verificar que al hacer clic frenéticamente o usar el teclado en el preview no se genere ninguna entrada en la base de datos
.
Validación Visual: Comprobar que en 960x600 el diseño sea perfecto y no existan huecos muertos en la parte superior
.
