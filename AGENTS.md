# Reglas de trabajo

- Trabajá en silencio: no narrés exploración, razonamiento ni avances. Reportá únicamente bloqueos reales y el cierre final, de forma breve.
- Usá Windows 10 y PowerShell nativo. No uses WSL, Git Bash ni comandos Unix incompatibles.
- Hacé cambios mínimos, cohesivos, reversibles y acordes con buenas prácticas. Antes de mover, eliminar o renombrar, verificá todos los consumidores.
- Priorizá soluciones sistémicas y componentes compartidos. No dupliques estilos, helpers o lógica en pantallas individuales cuando exista una abstracción común.
- No asumas que código, comentarios o tests existentes representan un canon inmutable. Contrastalos con la tarea actual y el comportamiento real.
- No amplíes el alcance ni aproveches una tarea para rediseñar, limpiar o refactorizar sectores no solicitados.
- No crees documentación, planes, reportes, backups, capturas, scratch, archivos temporales ni carpetas nuevas salvo pedido expreso o necesidad técnica imprescindible. No dejes basura en la raíz.
- No modifiques `.env`, `.venv`, secretos ni archivos generados.
- No ocultes errores con fallbacks, excepciones silenciosas o tests debilitados. Corregí la causa o reportá el bloqueo.
- No hagas commit ni push salvo indicación expresa.
- Al finalizar, informá brevemente: cambios realizados, archivos afectados, gates ejecutados y estado Git.
