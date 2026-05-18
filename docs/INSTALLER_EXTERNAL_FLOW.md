# Flujo de instalador externo (sin PyInstaller anidado)

> **Estado**: Fase 7 experimental. Opt-in con `--installer-mode external`.
> El modo nested (default) sigue funcionando exactamente igual que antes.

---

## 1. Problema que resuelve

Hasta Fase 6 los instaladores se compilaban empaquetando dentro de su propio
EXE las carpetas `dist/NeuroMood Suite/` y `dist/Desinstalador Suite/` (idem
Hub) vía PyInstaller `add_data`. Resultado:

- `Instalador Suite.exe` pesa ~250 MB.
- Doble-click → espera de 5–15 s mientras PyInstaller extrae todo el bundle
  a `%TEMP%\_MEIxxxxx\`.
- Mismo costo se repite cada vez que se abre el instalador.

Fase 7 produce en cambio:

- `Instalador Suite.exe` liviano (~20–30 MB, sin payload anidado).
- `payload_suite.zip` separado (~80–100 MB comprimido).
- Doble-click → instalador abre en < 1 s. La extracción del zip ocurre
  recién en el paso "Instalar".

---

## 2. Comandos de build

### Modo nested (default — comportamiento histórico)

```powershell
python build_neuromood.py
# o explícito:
python build_neuromood.py --installer-mode nested
```

Produce los 6 EXE como siempre, todo embebido.

### Modo external (Fase 7)

```powershell
# Build incremental requiere que Suite/Hub ya estén compilados
python build_neuromood.py --installer-mode external
```

Produce:

```
dist/
├── NeuroMood Suite/
│   └── NeuroMood Suite.exe
├── NeuroMood Hub/
│   └── NeuroMood Hub.exe
├── Desinstalador Suite/
├── Desinstalador Hub/
├── Instalador Suite/
│   ├── Instalador Suite.exe          ← liviano
│   └── payload_suite.zip             ← NUEVO, contiene Suite + Desinst Suite
└── Instalador Hub/
    ├── Instalador Hub.exe            ← liviano
    └── payload_hub.zip               ← NUEVO, contiene Hub + Desinst Hub
```

### Build selectivo en external

```powershell
# Solo regenerar el instalador Suite (requiere dist/NeuroMood Suite ya compilado)
python build_neuromood.py --only "Instalador Suite" --installer-mode external

# Skip de un instalador
python build_neuromood.py --skip "Instalador Hub" --installer-mode external
```

---

## 3. Cómo funciona en runtime

Cada instalador (`installer.py`, `installer_pro.py`) tiene una helper
`_external_payload_root()` que:

1. Si **NO** estamos `frozen` → devuelve `None`, comportamiento idéntico al
   modo dev de siempre.
2. Si estamos `frozen` y existe `payload_suite.zip` (o `payload_hub.zip`)
   junto a `sys.executable` → lo extrae **una sola vez** a
   `%TEMP%\NM_payload_<pid>_<ts>\` y devuelve esa ruta.
3. Si no encuentra el zip → devuelve `None` y `ruta_app_bundled()` cae al
   flujo `_MEIPASS` clásico (modo nested).

La extracción se registra con `atexit` para borrar el `%TEMP%` cuando
termina el instalador.

`ruta_app_bundled()` / `ruta_bundled()` ahora consultan primero el payload
externo y luego `_MEIPASS`. Esto significa que un mismo binario funciona
en ambos modos:

- Si está al lado de un `payload_*.zip` → modo external.
- Si no → modo nested (lee de `_MEIPASS` como antes).

---

## 4. Distribución

| Modo | Archivos a entregar al usuario | Tamaño aprox |
|---|---|---|
| nested | `Instalador Suite.exe` | ~250 MB |
| external | `Instalador Suite.exe` + `payload_suite.zip` | ~25 MB + ~80 MB |

> El usuario debe descargar AMBOS archivos y dejarlos en la misma carpeta
> antes de hacer doble-click. Si falta el zip, el instalador aborta con
> error claro en el log del paso "Instalar".

Para release sugerencia:

- Empaquetar ambos en un único `NeuroMood-Suite-Setup-v1.0.zip` para que
  el usuario solo haga 1 descarga.
- O wrapper futuro Inno Setup minimal que oculte ambos archivos en un solo
  `.exe` autoextraíble.

---

## 5. Validaciones obligatorias

Antes de mergear `feature/installer-no-nested-pyinstaller` a `refactor-master`:

| # | Validación | Comando |
|---|---|---|
| V1 | Compileall | `python -m compileall .` |
| V2 | Build Suite | `python build_neuromood.py --only "Suite Paciente"` |
| V3 | Build Hub | `python build_neuromood.py --only "NeuroMood Hub"` |
| V4 | Build desinstaladores | `python build_neuromood.py --only "Desinstalador Suite" --only "Desinstalador Hub"` |
| V5 | Build instalador nested (regresión) | `python build_neuromood.py --only "Instalador Suite" --installer-mode nested` |
| V6 | Build instalador external (nuevo) | `python build_neuromood.py --only "Instalador Suite" --installer-mode external` |
| V7 | `payload_suite.zip` existe | `Test-Path "dist/Instalador Suite/payload_suite.zip"` |
| V8 | Instalar en máquina/VM limpia | Doble-click `dist/Instalador Suite/Instalador Suite.exe` con el zip al lado |
| V9 | Suite abre post-install | Doble-click acceso directo de escritorio |
| V10 | Hub abre post-install | Idem Hub |
| V11 | `.env` quedó en `%APPDATA%` | `Test-Path "$env:APPDATA\NeuroMood\.env"` |
| V12 | Accesos directos creados | Revisar Desktop y `Start Menu\Programs\NeuroMood\` |
| V13 | Manifest `.neuromood_install_manifest.json` presente | `Test-Path "<install_dir>\.neuromood_install_manifest.json"` |
| V14 | Uninstall conservando datos | Ejecutar `Desinstalador Suite.exe`, marcar "Conservar datos" → `%APPDATA%\NeuroMood\` persiste, install_dir vacío |
| V15 | Uninstall borrando datos | Idem sin marcar → `%APPDATA%\NeuroMood\` también desaparece |
| V16 | Comparar tamaños | `Get-Item "dist/Instalador Suite/*" \| Select Name,Length` |
| V17 | Comparar tiempo doble-click → primera ventana | `Measure-Command { Start-Process "...Instalador Suite.exe" -Wait }` en ambos modos |

---

## 6. Rollback

### Inmediato (sin git)

Volver al modo nested no requiere revertir código:

```powershell
python build_neuromood.py --installer-mode nested
```

Esto regenera los 6 EXE en el formato histórico. El binario nuevo del
instalador funciona en ambos modos: si no encuentra `payload_*.zip` al
lado cae automáticamente al flujo `_MEIPASS`.

### Permanente (revert de commits)

Si se decide abandonar el flujo externo, revert en orden inverso (último
commit primero):

```powershell
git revert <commit-4-docs>
git revert <commit-3-flag>
git revert <commit-2-installers-runtime>
git revert <commit-1-zip-helper>
```

Cada commit toca pocos archivos sin solapar; los reverts son limpios.

---

## 7. Riesgos conocidos

| Riesgo | Mitigación |
|---|---|
| Usuario mueve el `.exe` sin el zip | `_external_payload_root()` devuelve `None`, instalador cae a `_MEIPASS`. Como en modo external no hay payload en `_MEIPASS`, la copia del paso "Instalar" falla con `FileNotFoundError` claro en el log. **Mejora pendiente**: detectar este caso explícitamente y mostrar "Falta payload_suite.zip junto al instalador. Volvé a descargar el paquete completo." |
| Antivirus marca el zip como sospechoso | Firmar el zip con el mismo cert del exe en la fase de release (fuera del scope de Fase 7). |
| Permisos en `%TEMP%` insuficientes | Mismo path que ya usa `_MEIPASS` hoy. Si falla uno, falla el otro. |
| Olvido de regenerar el zip cuando se recompila Suite/Hub | El bucle de `main()` regenera el zip cada vez que se construye el target del instalador en modo external. |

---

## 8. Sin cambios en

- `shared/db.py`, `shared/identidad.py`, `shared/config.py`, `shared/components_qt.py`
- `app/modules/*`, `hub/pacientes_qt.py`
- `installers/uninstaller.py`, `installers/uninstaller_pro.py` (los 4
  marcadores que `_es_ruta_neuromood()` busca se siguen escribiendo en
  `install_dir` igual que antes)
- `requirements.txt` (zipfile es stdlib)
- UI visual de los instaladores (cero modificación)
- Flujo de auth/Supabase del instalador Suite (cero modificación)
- Flujo de sync
