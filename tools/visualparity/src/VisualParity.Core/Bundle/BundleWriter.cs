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
    /// first. Returns the final bundle_sha256.
    /// </summary>
    public static string Write(VisualParityBundle bundle, string outDir)
    {
        var outPath = Path.GetFullPath(outDir);
        if (Directory.Exists(outPath))
            Directory.Delete(outPath, recursive: true);
        Directory.CreateDirectory(outPath);
        Directory.CreateDirectory(Path.Combine(outPath, "integrity"));

        // Serialize once (LF line endings) for stable hashing.
        var bundleJson = JsonSerializer.Serialize(bundle, JsonOpts);
        bundleJson = bundleJson.Replace("\r\n", "\n").Replace("\r", "\n");
        var bundleJsonBytes = Encoding.UTF8.GetBytes(bundleJson);

        // Compute bundle_json_sha256 (over the serialized JSON bytes).
        string bundleJsonSha;
        using (var sha = SHA256.Create())
        {
            bundleJsonSha = ToHex(sha.ComputeHash(bundleJsonBytes));
        }

        // Compute bundle_sha256 (over the bundle.json file bytes themselves).
        string bundleSha;
        using (var sha = SHA256.Create())
        {
            bundleSha = ToHex(sha.ComputeHash(bundleJsonBytes));
        }

        bundle.Checksums = new BundleChecksums
        {
            BundleSha256 = bundleSha,
            BundleJsonSha256 = bundleJsonSha,
        };

        // Re-serialize with checksums filled in, then recompute bundle_sha256
        // so the recorded value matches the file on disk.
        var finalJson = JsonSerializer.Serialize(bundle, JsonOpts);
        finalJson = finalJson.Replace("\r\n", "\n").Replace("\r", "\n");
        var finalBytes = Encoding.UTF8.GetBytes(finalJson);

        string finalBundleSha;
        using (var sha = SHA256.Create())
        {
            finalBundleSha = ToHex(sha.ComputeHash(finalBytes));
        }

        // Overwrite checksums with the final value (idempotent: bundle_json
        // hash does not change because checksums field value is deterministic
        // for the same input bytes).
        bundle.Checksums.BundleSha256 = finalBundleSha;

        // Final write.
        finalJson = JsonSerializer.Serialize(bundle, JsonOpts);
        finalJson = finalJson.Replace("\r\n", "\n").Replace("\r", "\n");
        File.WriteAllText(Path.Combine(outPath, "bundle.json"), finalJson, new UTF8Encoding(false));

        var checksums = new
        {
            schema = "visualparity.checksums.v1",
            bundle_sha256 = finalBundleSha,
            bundle_json_sha256 = bundleJsonSha,
            files = new[]
            {
                new { path = "bundle.json", sha256 = finalBundleSha, bytes = finalBytes.Length },
            },
        };
        var checksumsJson = JsonSerializer.Serialize(checksums, JsonOpts);
        checksumsJson = checksumsJson.Replace("\r\n", "\n").Replace("\r", "\n");
        File.WriteAllText(Path.Combine(outPath, "integrity", "checksums.json"),
                          checksumsJson, new UTF8Encoding(false));

        return finalBundleSha;
    }

    private static string ToHex(byte[] bytes)
    {
        var sb = new StringBuilder(bytes.Length * 2);
        foreach (var b in bytes)
            sb.Append(b.ToString("x2"));
        return sb.ToString();
    }
}
