# Distribution Checklist - NeuroMood V3

## Build preflight

- Crear un entorno limpio con Python 3.12.
- Instalar dependencias con `pip install -r requirements.txt`.
- Ejecutar `python -m compileall .`.
- Ejecutar `BUILD_ALL.bat`.
- Ejecutar `BUILD_INSTALLER.bat`.
- Ejecutar `BUILD_INSTALLER_PRO.bat`.
- Confirmar que no exista `.env` dentro de:
  - `dist\Instalador NeuroMood Suite\_internal\`
  - `dist\Instalador NeuroMood Hub Pro\_internal\`

## Windows limpio sin Python

1. Ejecutar `Instalador NeuroMood Suite.exe`.
2. Abrir `NeuroMood Suite.exe` desde la carpeta instalada.
3. Ejecutar `Instalador NeuroMood Hub Pro.exe`.
4. Abrir `NeuroMood Hub Pro.exe` desde la carpeta instalada.
5. Verificar accesos directos en Escritorio y Menu Inicio.
6. Configurar credenciales reales del Hub en `%APPDATA%\NeuroMoodPro\.env`.
7. Probar reconexion Supabase desde el Hub.
8. Desinstalar Suite con `Desinstalador NeuroMood.exe`.
9. Desinstalar Hub Pro con `Desinstalador NeuroMood Hub Pro.exe`.
10. Verificar limpieza de `%APPDATA%\NeuroMood\` y `%APPDATA%\NeuroMoodPro\`.

## Riesgos a revisar antes de publicar

- Rotar claves si algun build previo incluyo `.env` dentro del instalador.
- Probar instaladores en una VM sin Python y sin dependencias del entorno dev.
- Revisar `build.log` si una limpieza previa falla por archivos bloqueados.
