# Plan de reconciliación canónica

> **Fase 0A skeleton — no runtime authority.** Este documento declara el
> plan para reconciliar `qa/pack canonico/` contra `qa/_mockup_canonical/`.
> **No se elimina ni modifica nada en Fase 0A.**

## Tesis

`nm_suite` tiene actualmente dos directorios que reclaman ser canon:

1. `qa/_mockup_canonical/` — 116 PNGs + `MANIFEST.json` + `README.md` +
   `INDICE_CAPTURAS.csv`. `MANIFEST.json` con paths Windows hardcoded
   (`C:\Users\nosom\Desktop\nm_suite\qa\pack canonico\...`).
2. `qa/pack canonico/` — contiene `generate_captures.js`,
   `neuromood-mockup_reparado.html`, `LEEME.md`, y un subdirectorio
   `capturas_test/` con otros 116 PNGs + `MANIFEST.json` + `INDICE_CAPTURAS.csv`.

Esta coexistencia es ambigua. V3.1 requiere **canon único** con paths
relativos.

## Regla (redline)

**No se elimina `qa/pack canonico/` hasta reconciliarlo contra
`qa/_mockup_canonical/`.** Primero se declara canon único con paths
relativos.

En Fase 0A, ambos directorios quedan intactos. La reconciliación se
ejecuta en Fase posterior (no 0A).

## Plan de reconciliación (a ejecutar en Fase posterior)

### Paso 1 — Declarar canon único

El canon canónico V3.1 vive en `qa/_mockup_canonical/`. Esto se declara en
`docs/VisualParity_V3_1/README.md` (rutas oficiales) y se confirma vía
owner decision #11.

### Paso 2 — Re-canonicalizar `MANIFEST.json`

`qa/_mockup_canonical/MANIFEST.json` se re-canonicaliza:

- Paths relativos (eliminar `C:\Users\nosom\Desktop\nm_suite\qa\pack canonico\...`).
- Mantener `mockup_sha256`, `total_captures`, `expected_captures`,
  `all_captured`, `all_sizes_match`, `themes`, `surfaces`, `captures[]`
  con `sha256` por archivo.
- Agregar campo `canonical_source: "qa/_mockup_canonical"` (paths relativos).

### Paso 3 — Comparar PNGs por `sha256`

Comparar cada PNG en `qa/_mockup_canonical/` contra el PNG con mismo
nombre en `qa/pack canonico/capturas_test/` por `sha256` (raw bytes, sin
EOL normalization — PNGs son binarios).

Resultado esperado: subconjunto duplicado (mismos PNGs en ambos
directorios). Si hay PNGs en `pack canonico/capturas_test/` no presentes
en `_mockup_canonical/`, se marcan como "assets únicos a migrar".

### Paso 4 — Comparar `MANIFEST.json` campo a campo

Comparar `qa/_mockup_canonical/MANIFEST.json` contra
`qa/pack canonico/capturas_test/MANIFEST.json`:

- `generator`, `mockup`, `mockup_sha256`, `generated_at`, `chromium`,
  `total_captures`, `expected_captures`, `all_captured`, `all_sizes_match`,
  `themes`, `surfaces`, `size_mismatches`, `dom_size_mismatches`.
- Para cada entrada en `captures[]`: `file`, `view`, `screen`, `state`,
  `surface`, `is_modal`, `theme`, `real_w`, `real_h`, `expected_w`,
  `expected_h`, `size_match`, `dom_w`, `dom_h`, `dom_size_match`,
  `capture_selector`, `sha256`, `bytes`.

Resultado esperado: idénticos salvo paths.

### Paso 5 — Comparar `generate_captures.js` y `neuromood-mockup_reparado.html`

Estos archivos viven en `qa/pack canonico/` (raíz). Verificar si
`qa/_mockup_canonical/` los referencia o los necesita.

- `neuromood-mockup_reparado.html` es el mockup HTML fuente. Si
  `_mockup_canonical/` no lo contiene pero `MANIFEST.json` lo referencia
  (`mockup: "neuromood-mockup_reparado.html"`), se debe migrar a
  `_mockup_canonical/`.
- `generate_captures.js` es el script que genera los PNGs desde el HTML.
  Si V3.1 necesita regenerar el canon (ej. tras cambios de diseño), se
  migra a `_mockup_canonical/`.

### Paso 6 — Migrar assets únicos (si los hay)

Si la reconciliación revela assets en `pack canonico/` no presentes en
`_mockup_canonical/`:

- Migrar con commit separado: `chore(canon): migrar assets únicos de pack
  canonico a _mockup_canonical`.
- Actualizar `MANIFEST.json` de `_mockup_canonical/` con las nuevas
  entradas.

### Paso 7 — Eliminar `pack canonico/` (tras reconciliación)

Si `pack canonico/` es subconjunto duplicado de `_mockup_canonical/`:

- Eliminar `pack canonico/` del working tree con commit separado:
  `chore(canon): eliminar pack canonico duplicado tras reconciliación`.
- Preservación forense vía bundle A+ (ver `MIGRATION_A_PLUS.md`).

### Paso 8 — Actualizar `MANIFEST.json` con paths relativos

Tras la eliminación de `pack canonico/`, `MANIFEST.json` de
`_mockup_canonical/` debe tener paths relativos y `mockup_path` apuntando
a `qa/_mockup_canonical/neuromood-mockup_reparado.html` (tras migrar el
HTML en Paso 5).

## Estado actual (Fase 0A)

| Item | Estado |
|---|---|
| Canon único declarado | Sí (`_mockup_canonical/` en `README.md` rutas oficiales) |
| `MANIFEST.json` re-canonicalizado | No (paths Windows hardcoded persisten) |
| Comparación PNGs por `sha256` | No ejecutada |
| Comparación `MANIFEST.json` campo a campo | No ejecutada |
| Comparación `generate_captures.js` + HTML | No ejecutada |
| Migración assets únicos | No ejecutada |
| Eliminación `pack canonico/` | No ejecutada |
| `pack canonico/` intacto | Sí |
| `_mockup_canonical/` intacto | Sí |

## Riesgos si se ejecuta mal

- **Eliminar `pack canonico/` sin reconciliar:** pérdida de assets únicos
  si los hay (ej. `generate_captures.js`, `neuromood-mockup_reparado.html`
  no están en `_mockup_canonical/`).
- **Mantener ambos directorios:** ambigüedad de canon; cualquier
  herramienta puede referenciar el equivocado.
- **No re-canonicalizar `MANIFEST.json`:** paths Windows hardcoded hacen
  el canon no cross-platform reproducible.
- **Mixed commit (reconciliación + eliminación + scaffold):** imposibilita
  revertir selectivamente.

## Owner decision requerida

Ver `PHASE_0A_DECISIONS.md` #11: confirmar canon único + qué hacer con
assets únicos.
