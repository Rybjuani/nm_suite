// VisualParity.Core/Comparators/PixelDiff.cs
//
// Fase 1 - VisualParity V3.1 Core.
// Initial comparator: detects presence of diff via SHA256 byte equality.
// Pixel-level metrics (changed_pixel_ratio, bbox, mean_abs_diff) are deferred
// to a later fase. This is enough to emit NO_DIFF / SIZE_MISMATCH /
// MISSING_PAIR / DIFF_UNCLASSIFIED.

using VisualParity.Core.Bundle;
using VisualParity.Core.Pairing;

namespace VisualParity.Core.Comparators;

public static class PixelDiff
{
    /// <summary>
    /// Compare a pair and return a SurfaceMeasurement. Does NOT decide
    /// closure. Only emits measurement states.
    /// </summary>
    public static SurfaceMeasurement Compare(PngPair pair)
    {
        var m = new SurfaceMeasurement
        {
            SurfaceKey = pair.SurfaceKey,
            CanonicalPngSha256 = pair.CanonicalSha256,
            ActualPngSha256 = pair.ActualSha256,
            CanonicalBytes = pair.CanonicalBytes,
            ActualBytes = pair.ActualBytes,
        };

        if (pair.CanonicalPath is null || pair.ActualPath is null)
        {
            m.Status = SurfaceStatus.MissingPair;
            m.FailureReason = pair.CanonicalPath is null
                ? "canonical_png_missing"
                : "actual_png_missing";
            return m;
        }

        if (pair.CanonicalBytes != pair.ActualBytes)
        {
            m.Status = SurfaceStatus.SizeMismatch;
            m.FailureReason = $"size_mismatch:canonical={pair.CanonicalBytes},actual={pair.ActualBytes}";
            return m;
        }

        // Fase 1: byte equality only. If hashes match, NO_DIFF. If hashes
        // differ despite same size, the diff is unclassified until a later
        // fase adds pixel metrics.
        if (pair.CanonicalSha256 == pair.ActualSha256)
        {
            m.Status = SurfaceStatus.NoDiff;
            return m;
        }

        m.Status = SurfaceStatus.DiffUnclassified;
        m.FailureReason = "diff_present_byte_inequality_size_match";
        return m;
    }
}
