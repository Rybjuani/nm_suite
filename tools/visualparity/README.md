# tools/visualparity/ — VisualParity Core/CLI

> **Fase 1 — measurement only. No runtime authority. No visual closure.**
>
> Este directorio contiene la solución .NET 8 de VisualParity Core/CLI.
> Mide y empaqueta. No decide cierre. No interpreta semántica `nm_suite`.
> No ejecuta `capture_v8.py`. No invoca agentes.

## Tesis

> **VisualParity mide y muestra. El harness decide.**

VisualParity produce métricas crudas y estados de medición. No decide
cierre. No interpreta semántica `nm_suite`. No ejecuta `capture_v8.py`.
No invoca agentes.

## Stack

- .NET 8
- CLI/Core primero (Fase 1 — este commit)
- WPF después (fase futura, sólo `review_annotation.json`)
- WinUI fuera de V3.1

## Estructura (Fase 1)

```
tools/visualparity/
├── VisualParity.sln                              # Solution .NET 8
├── src/
│   ├── VisualParity.Core/
│   │   ├── VisualParity.Core.csproj
│   │   ├── Bundle/
│   │   │   ├── SurfaceStatus.cs                  # NO_DIFF, MISSING_PAIR, SIZE_MISMATCH, DIFF_UNCLASSIFIED
│   │   │   └── BundleWriter.cs                   # Escribe bundle.json + integrity/checksums.json
│   │   ├── Comparators/
│   │   │   └── PixelDiff.cs                      # Comparación byte-equality inicial
│   │   └── Pairing/
│   │       └── Pairer.cs                         # Empareja CANON vs ACTUAL por filename stem
│   ├── VisualParity.CLI/
│   │   ├── VisualParity.CLI.csproj
│   │   └── Program.cs                            # Commands: compare, batch, verify-bundle
├── tests/
│   └── VisualParity.Core.Tests/
│       ├── VisualParity.Core.Tests.csproj
│       └── PixelDiffTests.cs                     # xUnit: NO_DIFF, MISSING_PAIR, SIZE_MISMATCH, DIFF_UNCLASSIFIED, bundle stable, tamper detect
├── phase0b/                                      # Validadores Fase 0B (no touched in Fase 1)
├── phase0d/                                      # Preflight Fase 0D (no touched in Fase 1)
├── visualparity.lock.json                        # Allowlist vp_build_sha256 (placeholder scaffold)
└── README.md                                     # Este archivo
```

## Comandos CLI (Fase 1)

```bash
# Comparar un par canonical/actual
visualparity compare <canonical.png> <actual.png> --out <dir> [--git-head <sha>]

# Comparar un manifest de pares
visualparity batch <manifest.json> --out <dir> [--git-head <sha>]

# Verificar bundle + checksums
visualparity verify-bundle <bundle_dir>
```

## Estados emitidos (Fase 1 — medición only)

- `NO_DIFF` — canonical y actual son byte-iguales.
- `MISSING_PAIR` — falta canonical o actual.
- `SIZE_MISMATCH` — tamaños difieren.
- `DIFF_UNCLASSIFIED` — mismo tamaño, hashes distintos. Pixel-level metrics vienen en fase posterior.

## Estados NO emitidos (los emite el harness v3)

`CLOSURE_ALLOWED`, `BLOCK`, `CLOSURE_PASS`, `HUMAN_REVIEWED_PASS`,
`HUMAN_REVIEWED_FAIL`, `LOW_DIFF`, `HIGH_DIFF`, `SUSPICIOUS`,
`NEAR_THRESHOLD`, `NON_DETERMINISTIC`, `MEASUREMENT_DISPUTE_CANDIDATE`.

`LOW_DIFF`/`HIGH_DIFF`/etc. llegarán en fases posteriores cuando el
comparator tenga pixel metrics. En Fase 1, cualquier diff es
`DIFF_UNCLASSIFIED` y el harness v3 lo mapea a `BLOCK`.

## Cómo construir y testear

```bash
cd tools/visualparity
dotnet build VisualParity.sln
dotnet test VisualParity.sln
```

Si `dotnet` no está disponible localmente, marcar `NOT_EXECUTABLE`. El
workflow CI `visual-parity-v3-governance.yml` instala `dotnet` vía
`setup-dotnet` action y corre los tests en `ubuntu-latest`.

## Límites (no negociables)

- VisualParity Core/CLI **no puede** invocar `qa/capture_v8.py`.
- VisualParity Core/CLI **no puede** invocar agentes.
- VisualParity Core/CLI **no puede** modificar handoff, policy, records.
- VisualParity Core/CLI **no puede** cerrar keys.
- VisualParity Core/CLI **no puede** usar bulk review.

## Lockfile

`visualparity.lock.json` contiene el allowlist de `vp_build_sha256`. En
Fase 1 es placeholder (`unbuilt-fase-1-scaffold`) porque el binario no
está construido. El harness v3 `bundle_verifier.py` trata cualquier
`vp_build_sha256` no en el allowlist como `BLOCK`.

Cuando el binario se construya en una fase posterior, reemplazar el
placeholder con el SHA256 real del binario publicado y bump
`lockfile_version`.

## Documentación relacionada

- `docs/VisualParity_V3_1/README.md` — tesis, alcance, no-go absolutos.
- `docs/VisualParity_V3_1/ARCHITECTURE.md` — separación de capas.
- `docs/VisualParity_V3_1/CORE_CLI_CONTRACT.md` — contrato Core/CLI (Fase 4).
- `docs/VisualParity_V3_1/POLICY.md` — reglas de cierre.
