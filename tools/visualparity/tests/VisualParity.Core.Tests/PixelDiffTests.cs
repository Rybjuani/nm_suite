// VisualParity.Core.Tests/PixelDiffTests.cs
//
// Fase 1 - VisualParity V3.1 Core tests.
// Stdlib + xUnit. No closure logic tested here (VisualParity does not close).

using System.Security.Cryptography;
using VisualParity.Core.Bundle;
using VisualParity.Core.Comparators;
using VisualParity.Core.Pairing;

namespace VisualParity.Core.Tests;

public class PixelDiffTests : IDisposable
{
    private readonly string _tmpDir;

    public PixelDiffTests()
    {
        _tmpDir = Path.Combine(Path.GetTempPath(), "visualparity-tests-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_tmpDir);
    }

    public void Dispose()
    {
        if (Directory.Exists(_tmpDir))
            Directory.Delete(_tmpDir, recursive: true);
    }

    private string WritePng(string name, byte[] content)
    {
        var path = Path.Combine(_tmpDir, name);
        File.WriteAllBytes(path, content);
        return path;
    }

    [Fact]
    public void Same_Png_Bytes_Yields_NoDiff()
    {
        var png = new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x01, 0x02, 0x03 };
        var canon = WritePng("surface-a.png", png);
        var actual = WritePng("surface-a-actual.png", png);
        var pair = new PngPair(
            SurfaceKey: "surface-a",
            CanonicalPath: canon,
            ActualPath: actual,
            CanonicalBytes: png.Length,
            ActualBytes: png.Length,
            CanonicalSha256: Pairer.Sha256File(canon),
            ActualSha256: Pairer.Sha256File(actual));
        var m = PixelDiff.Compare(pair);
        Assert.Equal(SurfaceStatus.NoDiff, m.Status);
    }

    [Fact]
    public void Missing_Canonical_Yields_MissingPair()
    {
        var png = new byte[] { 0x89, 0x50, 0x4E, 0x47 };
        var actual = WritePng("surface-b.png", png);
        var pair = new PngPair(
            SurfaceKey: "surface-b",
            CanonicalPath: null,
            ActualPath: actual,
            CanonicalBytes: null,
            ActualBytes: png.Length,
            CanonicalSha256: null,
            ActualSha256: Pairer.Sha256File(actual));
        var m = PixelDiff.Compare(pair);
        Assert.Equal(SurfaceStatus.MissingPair, m.Status);
        Assert.Equal("canonical_png_missing", m.FailureReason);
    }

    [Fact]
    public void Missing_Actual_Yields_MissingPair()
    {
        var png = new byte[] { 0x89, 0x50, 0x4E, 0x47 };
        var canon = WritePng("surface-c.png", png);
        var pair = new PngPair(
            SurfaceKey: "surface-c",
            CanonicalPath: canon,
            ActualPath: null,
            CanonicalBytes: png.Length,
            ActualBytes: null,
            CanonicalSha256: Pairer.Sha256File(canon),
            ActualSha256: null);
        var m = PixelDiff.Compare(pair);
        Assert.Equal(SurfaceStatus.MissingPair, m.Status);
        Assert.Equal("actual_png_missing", m.FailureReason);
    }

    [Fact]
    public void Different_Size_Yields_SizeMismatch()
    {
        var canon = WritePng("surface-d.png", new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x00 });
        var actual = WritePng("surface-d-actual.png", new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x00, 0x01, 0x02 });
        var pair = new PngPair(
            SurfaceKey: "surface-d",
            CanonicalPath: canon,
            ActualPath: actual,
            CanonicalBytes: 5,
            ActualBytes: 7,
            CanonicalSha256: Pairer.Sha256File(canon),
            ActualSha256: Pairer.Sha256File(actual));
        var m = PixelDiff.Compare(pair);
        Assert.Equal(SurfaceStatus.SizeMismatch, m.Status);
    }

    [Fact]
    public void Same_Size_Different_Bytes_Yields_DiffUnclassified()
    {
        var canon = WritePng("surface-e.png", new byte[] { 0x89, 0x50, 0x4E, 0x47, 0xAA });
        var actual = WritePng("surface-e-actual.png", new byte[] { 0x89, 0x50, 0x4E, 0x47, 0xBB });
        var pair = new PngPair(
            SurfaceKey: "surface-e",
            CanonicalPath: canon,
            ActualPath: actual,
            CanonicalBytes: 5,
            ActualBytes: 5,
            CanonicalSha256: Pairer.Sha256File(canon),
            ActualSha256: Pairer.Sha256File(actual));
        var m = PixelDiff.Compare(pair);
        Assert.Equal(SurfaceStatus.DiffUnclassified, m.Status);
    }

    [Fact]
    public void Bundle_Checksum_Stable_Across_Writes()
    {
        var png = new byte[] { 0x89, 0x50, 0x4E, 0x47 };
        var m = new SurfaceMeasurement
        {
            SurfaceKey = "surface-f",
            Status = SurfaceStatus.NoDiff,
            CanonicalPngSha256 = "abc",
            ActualPngSha256 = "abc",
            CanonicalBytes = png.Length,
            ActualBytes = png.Length,
        };
        var bundle1 = new VisualParityBundle
        {
            GeneratedAtUtc = "2026-01-01T00:00:00Z",
            GitHead = "deadbeef",
            VpBuildSha256 = "scaffold",
            Surfaces = new List<SurfaceMeasurement> { m },
        };
        var bundle2 = new VisualParityBundle
        {
            GeneratedAtUtc = "2026-01-01T00:00:00Z",
            GitHead = "deadbeef",
            VpBuildSha256 = "scaffold",
            Surfaces = new List<SurfaceMeasurement> { m },
        };
        var out1 = Path.Combine(_tmpDir, "out1");
        var out2 = Path.Combine(_tmpDir, "out2");
        var sha1 = BundleWriter.Write(bundle1, out1);
        var sha2 = BundleWriter.Write(bundle2, out2);
        Assert.Equal(sha1, sha2);
    }

    [Fact]
    public void Verify_Bundle_Fails_When_File_Altered()
    {
        var png = new byte[] { 0x89, 0x50, 0x4E, 0x47 };
        var m = new SurfaceMeasurement
        {
            SurfaceKey = "surface-g",
            Status = SurfaceStatus.NoDiff,
            CanonicalPngSha256 = "abc",
            ActualPngSha256 = "abc",
            CanonicalBytes = png.Length,
            ActualBytes = png.Length,
        };
        var bundle = new VisualParityBundle
        {
            GeneratedAtUtc = "2026-01-01T00:00:00Z",
            GitHead = "deadbeef",
            VpBuildSha256 = "scaffold",
            Surfaces = new List<SurfaceMeasurement> { m },
        };
        var outDir = Path.Combine(_tmpDir, "out-tamper");
        var bundleSha = BundleWriter.Write(bundle, outDir);
        var bundlePath = Path.Combine(outDir, "bundle.json");
        var original = File.ReadAllText(bundlePath);
        // Tamper: change a value inside bundle.json (e.g., surface_key).
        var tampered = original.Replace("surface-g", "surface-tampered");
        File.WriteAllText(bundlePath, tampered);
        var actualSha = Pairer.Sha256File(bundlePath);
        Assert.NotEqual(bundleSha, actualSha);
    }

    [Fact]
    public void Bundle_Sha256_Matches_Actual_File_Hash_And_Checksums_Json()
    {
        // Regression: BundleWriter.Write used to return a bundle_sha256 that
        // did NOT match the actual bundle.json file bytes on disk (self-
        // referential hash loop). This test verifies the fix: the returned
        // SHA, the SHA in integrity/checksums.json, and the SHA of the actual
        // bundle.json file must all be equal.
        var png = new byte[] { 0x89, 0x50, 0x4E, 0x47 };
        var m = new SurfaceMeasurement
        {
            SurfaceKey = "surface-h",
            Status = SurfaceStatus.NoDiff,
            CanonicalPngSha256 = "abc",
            ActualPngSha256 = "abc",
            CanonicalBytes = png.Length,
            ActualBytes = png.Length,
        };
        var bundle = new VisualParityBundle
        {
            GeneratedAtUtc = "2026-01-01T00:00:00Z",
            GitHead = "deadbeef",
            VpBuildSha256 = "scaffold",
            Surfaces = new List<SurfaceMeasurement> { m },
        };
        var outDir = Path.Combine(_tmpDir, "out-consistency");
        var returnedSha = BundleWriter.Write(bundle, outDir);

        var bundlePath = Path.Combine(outDir, "bundle.json");
        var checksumsPath = Path.Combine(outDir, "integrity", "checksums.json");

        // 1. The returned SHA must equal the hash of the actual file on disk.
        var actualFileSha = Pairer.Sha256File(bundlePath);
        Assert.Equal(returnedSha, actualFileSha);

        // 2. The bundle_sha256 in checksums.json must equal the returned SHA.
        var checksumsJson = File.ReadAllText(checksumsPath);
        using var doc = System.Text.Json.JsonDocument.Parse(checksumsJson);
        var storedSha = doc.RootElement.GetProperty("bundle_sha256").GetString();
        Assert.Equal(returnedSha, storedSha);

        // 3. The bundle.json must NOT contain a "checksums" field (it would
        //    reintroduce the self-referential loop). WhenWritingNull drops it.
        var bundleJson = File.ReadAllText(bundlePath);
        Assert.DoesNotContain("\"checksums\"", bundleJson);
    }
}
