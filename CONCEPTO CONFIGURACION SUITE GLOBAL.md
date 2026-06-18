El Concepto: "Configuración Global de Suite"
La idea es reemplazar el menú de personalización actual (que es una lista fría de campos) por una herramienta de edición visual directa (WYSIWYG)
. El profesional debe ver una réplica visual exacta de lo que ve el paciente, pero totalmente inerte y segura
.
1. El Cambio de Paradigma: De "Clon Funcional" a "Editor Declarativo"
Lo más importante que el agente debe entender es que no debe instanciar los módulos reales de la aplicación
.
Antes (Error): Se abría la app real, se cargaban tareas falsas y se intentaban bloquear los clics para que no borraran datos
.
Ahora (Tu Idea): Se debe crear un "Suite Text Preview". Es una vista que utiliza los mismos componentes visuales (botones, etiquetas, layouts), pero está desconectada de toda lógica clínica, temporizadores o bases de datos
.
2. Funcionalidades Clave
Navegación Total: El profesional puede recorrer todo el Suite (Home, Onboarding, módulos) como si fuera un paciente, pero en un estado "limpio" o global
.
Edición Directa: Al hacer clic en cualquier texto (títulos, botones, mensajes de ayuda), se abre un editor para modificarlo
.
Límites Inteligentes: Cada campo debe tener un límite de caracteres específico según su ubicación para no romper el diseño visual (layout)
.
Estados Simulados: Como muchos módulos aparecen vacíos si no hay tareas, el editor debe mostrar "datos neutros" (ej. "Actividad de ejemplo") solo para que el profesional vea dónde van los textos y pueda editarlos
.
Sincronización Real: Al guardar, los cambios se envían a todos los pacientes como overrides de texto, sin afectar su progreso individual
.
3. Reglas de Seguridad (El "Blindaje")
Para que la IA no rompa tu repositorio, debe seguir estas prohibiciones estrictas
:
No tocar la Base de Datos (DB): El editor no debe leer ni escribir en la base de datos real del paciente
.
Aislamiento de Módulos: No debe importar app.modules operativos para generar la vista previa
.
Sin Efectos Clínicos: Ninguna acción dentro de este modo (clics, teclado) puede generar registros médicos, completar tareas o activar alertas
.
Solo Texto: La persistencia solo debe guardar pares de "clave de texto" y "nuevo valor"
.
4. Plan de Acción para la IA (Fases sugeridas)
Puedes pedirle al agente que trabaje en este orden
:
Auditoría: Identificar todos los textos configurables en la Suite real y sus claves
.
Motor de Previsualización: Crear la infraestructura visual que no dependa de la lógica real
.
Migración por Pantallas: Ir habilitando la edición pantalla por pantalla (Home, luego Temporizador, etc.) verificando que no se rompa el diseño
.
Sistema de Guardado y Restauración: Implementar el botón "Guardar cambios" y el de "Restaurar por defecto" para volver a los textos originales
.
Resumen para el agente: "No construyas una app funcional; construye una maqueta interactiva que sirva exclusivamente para editar etiquetas de texto y guardarlas como configuraciones globales"
.