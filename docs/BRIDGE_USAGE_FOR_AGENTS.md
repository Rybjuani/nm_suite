# Bridge Usage for Agents

Cómo resolver un check visual usando el **Design-System Translation Bridge** en
lugar de fixes artesanales. Leer junto con `VISUAL_QA_AGENT_PROTOCOL.md` (manda
el protocolo; el bridge no lo reemplaza).

## Qué es y qué no es el bridge

- **Es** un diccionario trazable canonical CSS ↔ tokens/helpers/widgets Qt, para
  reusar patrones y no reinventar QSS por pantalla.
- **No es** un gate. No cierra checks, no cambia thresholds, no toca `qa/`.
  El cierre exige el gate técnico automatizado (ver § Flujo).

## Flujo para resolver una key del handoff

1. **Tomar la key** del `VISUAL_REPAIR_HANDOFF.md` (primer `[ ]` de arriba hacia
   abajo; es una cola, no un menú).

2. **Ubicar el origen con Graphify** (antes de abrir código a mano):

   ```powershell
   & "$env:USERPROFILE\.local\bin\graphify.exe" update .
   & "$env:USERPROFILE\.local\bin\graphify.exe" explain "<pantalla o componente>"
   & "$env:USERPROFILE\.local\bin\graphify.exe" path "NMCard" "app/home_qt.py"
   ```

   Si el entorno expone Graphify como slash command: `/graphify . --update`.

3. **Identificar la familia y el selector** en
   `CSS_TO_PYQT_EQUIVALENCE_MATRIX.md` (busca por la pantalla en
   "Keys → familias dominantes", luego por el selector en la familia).

4. **Clasificar la divergencia** con `QT_HTML_KNOWN_MISMATCHES.md`:
   - Si es **IRREDUCIBLE** (texto text-dense #20, sombra 3-capas #3, backdrop
     blur #17): no se cierra cambiando ese aspecto. Buscar las **flat-regions**
     reparables que cita el handoff.
   - Si es **WORKAROUND**: usar el helper/painter correcto (conic, radial, ring,
     elided, chevron SVG, etc.).
   - Si es **DECISIÓN-OWNER** (#10, #19): no "corregir" hacia el mockup.

5. **Reparar con el componente/token del catálogo** (`VISUAL_COMPONENT_CATALOG.md`):
   - Color/radio/sombra/fuente: SIEMPRE desde `shared.theme` vía `shared.theme_qt`
     (`C()`, `v3c()`, `qfont()`, `v3_font()`, `shadow_effect()`, …).
   - Geometría/variante: usar el componente `NM*` existente; no duplicar QSS local.

6. **Verificar con probes auxiliares** (no son cierre):

   ```powershell
   .\.venv\Scripts\python.exe qa\runtime_live_probe.py --app suite --view timer --theme light --mode offscreen
   .\.venv\Scripts\python.exe qa\vas_introspect.py --introspect   # SHADOW/RADIUS/GRADIENT
   ```

7. **Cerrar SOLO con el gate técnico automatizado** vía los wrappers
   `run_visual_item.ps1` / `run_visual_family.ps1`, que orquestan anti-fraud
   scan, captura con `NM_VAS_INTROSPECT=1`, comparador, y `vas_gate.py`:

   ```powershell
   .\qa\run_visual_item.ps1 -App <app> -View <view> -Theme <theme>
   ```

   Si se necesita invocar manualmente los pasos individuales:

   ```powershell
   $env:NM_VAS_INTROSPECT = "1"
   Remove-Item .\qa\_visual_auditor_spec\introspection.json -ErrorAction SilentlyContinue
   .\.venv\Scripts\python.exe qa\capture_v8.py --app <app> --view <view> --theme <theme> --out-dir qa\_captures_v8 --no-clean
   .\.venv\Scripts\python.exe qa\layered_visual_compare.py --canonical qa\_mockup_canonical --actual qa\_captures_v8 --out-dir reports\qa\layered_visual_compare_item --key "<app>:<view>@<theme>"
   .\.venv\Scripts\python.exe qa\vas_gate.py --key "<app>:<view>@<theme>"
   ```

   Cierre válido = anti-fraud CLEAN + `NM_VAS_INTROSPECT=1` +
   `REPORT_EVIDENCE_VALID: YES` + exact key `PASS` + `vas_gate.py` exit `0`.
   No existe cierre subjetivo: revisión manual, inspección visual del panel,
   "se ve bien", aceptación del owner, o human review **no** son evidencia de
   cierre (ver `VISUAL_QA_AGENT_PROTOCOL.md`).

## Reglas anti-fraude (heredadas del protocolo)

El bridge **no relaja** ninguna. En particular:

- Prohibido inyectar artefactos canónicos/referencia en runtime para pasar.
- Prohibido tocar comparador, thresholds, capturas, canónicas, reports.
- `ssim=1.0`/`mad=0.0` en superficie no trivial = `SUSPICIOUS_PERFECT_MATCH`,
  bloquea cierre.
- Las equivalencias del bridge deben **citar fuente canónica**. Una equivalencia
  sin línea del HTML canónico no autoriza ningún cambio.

## Anti-patrones que el bridge previene

| Anti-patrón | Qué hacer en su lugar |
|---|---|
| QSS inventado (`setStyleSheet("...#hardcoded...")`) | Token de `shared.theme` vía `theme_qt`; componente `NM*` |
| Color/medida hardcodeada | `C()`/`v3c()` + `V3_RADIUS`/`LAYOUT`/`V3_SHADOWS` |
| "Equivalencia" sin fuente canónica | Buscar el selector en la matriz; si no existe, agregarlo con su línea HTML |
| Componente local divergente (re-implementar una card) | Reusar el `NM*` del catálogo |
| Forzar paridad de una no-equivalencia irreducible | Clasificar con `QT_HTML_KNOWN_MISMATCHES.md`; reparar flat-regions |
| Bypass del bridge (cambiar threshold/canónica) | Prohibido (anti-fraude) |

## Mantener el bridge vivo

- Si aparece un selector canónico nuevo (al regenerar el mockup), agregar fila a
  la matriz con su línea HTML, su equivalente Qt y sus keys.
- Si se descubre una no-equivalencia Qt nueva, registrar `MISMATCH#n` con
  impacto (IRREDUCIBLE / WORKAROUND / DECISIÓN-OWNER).
- Tras tocar `app/`, `hub/`, `shared/`, correr `graphify update .` para que el
  grafo siga navegable.
- El contrato liviano `tests/test_design_bridge_contract.py` valida que el bridge
  no referencie tokens/archivos/keys inexistentes. Correr:

  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests\test_design_bridge_contract.py -q
  ```

## Navegación del grafo (Fase 4)

El grafo Graphify permite recorrer:

```
canonical selector  →  bridge entry (matriz)  →  componente NM* (catálogo)
                    →  tokens en shared.theme  →  pantalla (app/ | hub/)
                    →  tests/probes (qa/)       →  visual key (handoff)
```

Comandos útiles:

```powershell
& "$env:USERPROFILE\.local\bin\graphify.exe" explain "NMButton"
& "$env:USERPROFILE\.local\bin\graphify.exe" path "shared/theme.py" "app/modules/timer_qt.py"
& "$env:USERPROFILE\.local\bin\graphify.exe" query "que pinta el anillo de respiracion"
```
