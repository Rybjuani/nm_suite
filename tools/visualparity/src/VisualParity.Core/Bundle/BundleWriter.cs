// VisualParity.Core/Bundle/BundleWriter.cs
//
// Fase 1 - VisualParity V3.1 Core.
// Writes a measurement-only bundle to disk and computes its integrity
// checksums. Does NOT decide closure. Does NOT invoke capture_v8.

using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace VisualParity.Core.Bundle;

/// <summary>
/// Represents a single surface measurement inside the bundle.
/// </summary>
public sealed class SurfaceMeasurement
{
    public string SurfaceKey { get; set; } = string.Empty;
    public SurfaceStatus Status { get; set; }
    public string? CanonicalPngSha256 { get; set; }
    public string? ActualPngSha256 { get; set; }
    public long? CanonicalBytes { get; set; }
    public long? ActualBytes { get; set; }
    public string? FailureReason { get; set; }
}

/// <summary>
/// Bundle envelope. Contains metadata + per-surface measurements + integrity
/// checksums. The harness v3 verifies this on consume.
/// </summary>
public sealed class VisualParityBundle
{
    public const string SchemaVersion = "visualparity.bundle.v1";
    public const string Eol = "lf";

    public string Schema { get; set; } = SchemaVersion;
    public string EolMode { get; set; } = Eol;
    public string GeneratedAtUtc { get; set; } = string.Empty;
    public string GitHead { get; set; } = string.Empty;
    public string VpBuildSha256 { get; set; } = string.Empty;
    public List<SurfaceMeasurement> Surfaces { get; set; } = new();
    public BundleChecksums? Checksums { get; set; }
}

public sealed class BundleChecksums
{
    public string BundleSha256 { get; set; } = string.Empty;
    public string BundleJsonSha256 { get; set; } = string.Empty;
}

/// <summary>
/// Writes bundles and computes checksums. The OutDir is wiped before write
/// to prevent stale-bundle attacks (VQA-AF-STALE-001).
/// </summary>
public static class BundleWriter
{
    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    };

    /// <summary>
    /// Writes bundle.json + integrity/checksums.json to outDir. Wipes outDir
    /// first. Returns the bundle_sha256 (hash of the actual bundle.json bytes).
    ///
    /// The Checksums field is OMITTED from bundle.json (set to null before
    /// serialization; WhenWritingNull drops it) to avoid a self-referential
    /// hash loop. The bundle_sha256 stored in integrity/checksums.json is the
    /// SHA256 of the actual bundle.json file bytes. The CLI verify-bundle
    /// command reads bundle_sha256 from checksums.json and compares it to the
    /// real hash of bundle.json, so tampering with bundle.json is detected.
    /// </summary>
    public static string Write(VisualParityBundle bundle, string outDir)
    {
        var outPath = Path.GetFullPath(outDir);
        if (Directory.Exists(outPath))
            Directory.Delete(outPath, recursive: true);
        Directory.CreateDirectory(outPath);
        Directory.CreateDirectory(Path.Combine(outPath, "integrity"));

        // Ensure Checksums is null so it is omitted from bundle.json. This
        // avoids the self-referential hash problem (bundle_sha256 inside
        // bundle.json would change the file's own hash).
        bundle.Checksums = null;

        // Serialize bundle.json (LF line endings for cross-platform stability).
        var bundleJson = JsonSerializer.Serialize(bundle, JsonOpts);
        bundleJson = bundleJson.Replace("\r\n", "\n").Replace("\r", "\n");
        var bundleJsonBytes = Encoding.UTF8.GetBytes(bundleJson);
        File.WriteAllBytes(Path.Combine(outPath, "bundle.json"), bundleJsonBytes);

        // Compute bundle_sha256 = SHA256 of the actual bundle.json file bytes.
        string bundleSha;
        using (var sha = SHA256.Create())
        {
            bundleSha = ToHex(sha.ComputeHash(bundleJsonBytes));
        }

        // bundle_json_sha256 is the same value (the bundle JSON IS bundle.json).
        string bundleJsonSha = bundleSha;

        // Write integrity/checksums.json referencing the actual file hash.
        var checksums = new
        {
            schema = "visualparity.checksums.v1",
            bundle_sha256 = bundleSha,
            bundle_json_sha256 = bundleJsonSha,
            files = new[]
            {
                new { path = "bundle.json", sha256 = bundleSha, bytes = bundleJsonBytes.Length },
            },
        };
        var checksumsJson = JsonSerializer.Serialize(checksums, JsonOpts);
        checksumsJson = checksumsJson.Replace("\r\n", "\n").Replace("\r", "\n");
        File.WriteAllText(Path.Combine(outPath, "integrity", "checksums.json"),
                          checksumsJson, new UTF8Encoding(false));

        // Populate Checksums on the in-memory object for callers that inspect it.
        bundle.Checksums = new BundleChecksums
        {
            BundleSha256 = bundleSha,
            BundleJsonSha256 = bundleJsonSha,
        };

        return bundleSha;
    }

    private static string ToHex(byte[] bytes)
    {
        var sb = new StringBuilder(bytes.Length * 2);
        foreach (var b in bytes)
            sb.Append(b.ToString("x2"));
        return sb.ToString();
    }
}
