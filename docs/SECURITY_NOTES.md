# Security Notes — NeuroMood V3

## Password Handling (v3.1 — Junio 2026)

- **Hash**: SHA-256 determinista (misma contraseña → mismo hash).
- **Storage**: `patient_pwd` en `config` table de SQLite usa hash, nunca texto plano.
- **Migration**: Si se detecta password en texto plano (no 64 chars hex), se convierte automáticamente al primer acceso vía `obtener_password_hash()`.
- **patient_id**: Derivado de SHA-256 de `nombre + password + install_code`. No se puede revertir.
- **Supabase**: Se envía el hash (no la contraseña original).

## .env y Secretos

- `.env` se empaqueta DENTRO del instalador (`BUILD_INSTALLER.bat` y `BUILD_INSTALLER_PRO.bat`).
- **NUNCA** poner credenciales reales de producción en el `.env` que se usa para compilar el instalador paciente.
- El `.env` bundled en el instalador debe tener valores placeholder o vacíos:
  ```
  SUPABASE_URL=
  SUPABASE_KEY=
  ```
- Las credenciales reales solo deben configurarse después de la instalación, en `%APPDATA%\NeuroMood\.env`.
- El Hub Profesional requiere credenciales reales configuradas manualmente.
- `.env` está en `.gitignore` — nunca se commitea.

## Secretos requeridos

| Secreto | Quién lo necesita | Dónde se configura |
|---|---|---|
| `SUPABASE_URL` | Hub Profesional | `.env` en raíz del Hub |
| `SUPABASE_KEY` | Hub Profesional | `.env` en raíz del Hub |
| `GROQ_KEY` | Hub Profesional (IA) | `.env` en raíz del Hub |
| `patient_pwd` | Paciente (sync) | SQLite, hasheado |
| `install_code` | Paciente (sync) | SQLite |

## Builds públicos

- El instalador paciente (`Instalador NeuroMood Suite.exe`) incluye `.env` bundled.
- **Verificar** que el `.env` usado para build NO tenga credenciales reales.
- El instalador Hub **NO** incluye credenciales — el profesional las configura manualmente.

## Recomendaciones

- Usar `.env.example` con placeholders para documentar qué variables se necesitan.
- El `.env` real de desarrollo local nunca debe incluirse en builds de distribución.
- Rotar claves de Supabase si se sospecha exposición.
