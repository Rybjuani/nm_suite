# Security Notes - NeuroMood V3

## Password Handling (v3.1 - Junio 2026)

- **Hash**: PBKDF2-SHA256 con 100,000 iteraciones.
- **Salt**: `install_code` unico por instalacion. Sin `install_code` usa fallback `"NeuromoodV3"`.
- **Determinismo**: Misma password + salt produce el mismo hash. Compatible con Supabase y patient_id.
- **Storage**: `patient_pwd` en la tabla `config` de SQLite guarda hash PBKDF2, nunca texto plano.
- **Migration**: Si se detecta password en texto plano, `obtener_password_hash()` la convierte a PBKDF2 en el primer acceso valido.
- **patient_id**: Derivado de SHA-256 de `nombre + password + install_code`. No se puede revertir.
- **Supabase**: El campo `pwd` recibe el hash PBKDF2, no la password original.

## .env y Secretos

- Los scripts publicos `BUILD_INSTALLER.bat` y `BUILD_INSTALLER_PRO.bat` NO empaquetan `.env`.
- El `.env` de la raiz es solo para desarrollo local y esta en `.gitignore`; nunca se commitea.
- El instalador puede copiar un `.env` solo si existe como recurso bundleado en un build interno/manual. No usar esa ruta para builds publicos con credenciales reales.
- Las credenciales reales deben configurarse despues de la instalacion, fuera del instalador distribuible:
  - Paciente/sync: `%APPDATA%\NeuroMood\.env`, si se habilita sync.
  - Hub Profesional: `%APPDATA%\NeuroMoodPro\.env` o variables de entorno del sistema.
- El Hub Profesional requiere credenciales reales configuradas manualmente.

## Secretos requeridos

| Secreto | Quien lo necesita | Donde se configura |
|---|---|---|
| `SUPABASE_URL` | Hub Profesional / sync paciente | `%APPDATA%` o variables de entorno |
| `SUPABASE_KEY` | Hub Profesional / sync paciente | `%APPDATA%` o variables de entorno |
| `GROQ_API_KEY` | Hub Profesional (IA) | `%APPDATA%\NeuroMoodPro\.env` o variables de entorno |
| `GEMINI_API_KEY` | Hub Profesional (IA opcional) | `%APPDATA%\NeuroMoodPro\.env` o variables de entorno |
| `OPENCODE_API_KEY` | Hub Profesional (IA opcional) | `%APPDATA%\NeuroMoodPro\.env` o variables de entorno |
| `OLLAMA_API_KEY` | Hub Profesional (IA opcional) | `%APPDATA%\NeuroMoodPro\.env` o variables de entorno |
| `patient_pwd` | Paciente (sync) | SQLite, hasheado |
| `install_code` | Paciente (sync) | SQLite |

## Builds publicos

- El instalador paciente (`Instalador NeuroMood Suite.exe`) NO debe incluir `.env`.
- El instalador Hub (`Instalador NeuroMood Hub Pro.exe`) NO debe incluir `.env`.
- Antes de distribuir, verificar que `dist\Instalador NeuroMood Suite\_internal\.env` y `dist\Instalador NeuroMood Hub Pro\_internal\.env` no existan.
- Si se hizo un build interno con `.env` bundleado, limpiar `dist/`, regenerar instaladores con los scripts publicos y rotar claves si hubo exposicion.

## Recomendaciones

- Usar `.env.example` con placeholders para documentar que variables se necesitan.
- El `.env` real de desarrollo local nunca debe incluirse en builds de distribucion.
- Rotar claves de Supabase/IA si se sospecha exposicion.
