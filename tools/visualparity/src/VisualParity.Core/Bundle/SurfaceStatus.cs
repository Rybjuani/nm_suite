// VisualParity.Core/Bundle/SurfaceStatus.cs
//
// Fase 1 - VisualParity V3.1 Core.
// Measurement-only surface states. The harness v3 maps these to closure
// actions; VisualParity itself never decides closure.

namespace VisualParity.Core.Bundle;

/// <summary>
/// Measurement-only surface status emitted by VisualParity. The harness
/// v3 consumes these and decides ALLOW / BLOCK / HUMAN_REVIEW_REQUIRED.
/// </summary>
public enum SurfaceStatus
{
    /// <summary>Canonical and actual PNGs are byte-identical.</summary>
    NoDiff,

    /// <summary>Canonical or actual PNG is missing for the surface key.</summary>
    MissingPair,

    /// <summary>Canonical and actual PNGs have different byte sizes.</summary>
    SizeMismatch,

    /// <summary>
    /// Diff exists but is not yet classified into LOW/HIGH/SUSPICIOUS.
    /// Initial Fase 1 state: the comparator only detects presence of diff,
    /// not magnitude. Classification comes in a later fase with pixel
    /// metrics.
    /// </summary>
    DiffUnclassified,
}
