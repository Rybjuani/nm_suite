// VisualParity.CLI/Program.cs
//
// Fase 1 - VisualParity V3.1 CLI entrypoint.
// Commands: compare, batch, verify-bundle.
// Measurement only. No closure. No policy. No capture_v8 invocation.
// Uses a minimal manual arg parser to avoid external NuGet dependencies
// in Fase 1.

using System.Text.Json;
using VisualParity.Core.Bundle;
using VisualParity.Core.Comparators;
using VisualParity.Core.Pairing;

namespace VisualParity.CLI;

public static class Program
{
    public static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            PrintUsage();
            return 2;
        }

        return args[0] switch
        {
            "compare" => RunCompare(args.AsSpan(1)),
            "batch" => RunBatch(args.AsSpan(1)),
            "verify-bundle" => RunVerifyBundle(args.AsSpan(1)),
            "-h" or "--help" or "help" => PrintUsage(),
            _ => UnknownCommand(args[0]),
        };
    }

    private static int PrintUsage()
    {
        Console.Error.WriteLine("VisualParity V3.1 CLI - measurement only. No closure.");
        Console.Error.WriteLine("Usage:");
        Console.Error.WriteLine("  visualparity compare <canonical.png> <actual.png> --out <dir> [--git-head <sha>]");
        Console.Error.WriteLine("  visualparity batch <manifest.json> --out <dir> [--git-head <sha>]");
        Console.Error.WriteLine("  visualparity verify-bundle <bundle_dir>");
        return 0;
    }

    private static int UnknownCommand(string cmd)
    {
        Console.Error.WriteLine($"ERROR: unknown command: {cmd}");
        PrintUsage();
        return 2;
    }

    private static int RunCompare(ReadOnlySpan<string> args)
    {
        if (args.Length < 2)
        {
            Console.Error.WriteLine("ERROR: compare requires <canonical> <actual> --out <dir>");
            return 2;
        }
        var canonical = args[0];
        var actual = args[1];
        string? outDir = null;
        var gitHead = string.Empty;
        for (int i = 2; i < args.Length; i++)
        {
            if (args[i] == "--out" && i + 1 < args.Length) { outDir = args[++i]; }
            else if (args[i] == "--git-head" && i + 1 < args.Length) { gitHead = args[++i]; }
        }
        if (outDir is null)
        {
            Console.Error.WriteLine("ERROR: --out required");
            return 2;
        }
        if (!File.Exists(canonical))
        {
            Console.Error.WriteLine($"ERROR: canonical not found: {canonical}");
            return 2;
        }
        if (!File.Exists(actual))
        {
            Console.Error.WriteLine($"ERROR: actual not found: {actual}");
            return 2;
        }

        var canonInfo = new FileInfo(canonical);
        var actualInfo = new FileInfo(actual);
        var pair = new PngPair(
            SurfaceKey: Path.GetFileNameWithoutExtension(canonical),
            CanonicalPath: canonical,
            ActualPath: actual,
            CanonicalBytes: canonInfo.Length,
            ActualBytes: actualInfo.Length,
            CanonicalSha256: Pairer.Sha256File(canonical),
            ActualSha256: Pairer.Sha256File(actual));
        var measurement = PixelDiff.Compare(pair);
        var bundle = BuildBundle(new[] { measurement }, gitHead);
        var bundleSha = BundleWriter.Write(bundle, outDir);

        Console.WriteLine($"compare: surface={measurement.SurfaceKey} status={measurement.Status}");
        Console.WriteLine($"bundle_sha256={bundleSha}");
        Console.WriteLine($"out={outDir}");
        return 0;
    }

    private static int RunBatch(ReadOnlySpan<string> args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("ERROR: batch requires <manifest> --out <dir>");
            return 2;
        }
        var manifestPath = args[0];
        string? outDir = null;
        var gitHead = string.Empty;
        for (int i = 1; i < args.Length; i++)
        {
            if (args[i] == "--out" && i + 1 < args.Length) { outDir = args[++i]; }
            else if (args[i] == "--git-head" && i + 1 < args.Length) { gitHead = args[++i]; }
        }
        if (outDir is null)
        {
            Console.Error.WriteLine("ERROR: --out required");
            return 2;
        }
        if (!File.Exists(manifestPath))
        {
            Console.Error.WriteLine($"ERROR: manifest not found: {manifestPath}");
            return 2;
        }

        var manifestJson = File.ReadAllText(manifestPath);
        using var doc = JsonDocument.Parse(manifestJson);
        if (!doc.RootElement.TryGetProperty("pairs", out var pairsEl))
        {
            Console.Error.WriteLine("ERROR: manifest missing 'pairs' array.");
            return 2;
        }

        var measurements = new List<SurfaceMeasurement>();
        foreach (var pairEl in pairsEl.EnumerateArray())
        {
            var canonical = pairEl.GetProperty("canonical").GetString()!;
            var actual = pairEl.GetProperty("actual").GetString()!;
            var key = pairEl.TryGetProperty("surface_key", out var keyEl)
                ? keyEl.GetString()!
                : Path.GetFileNameWithoutExtension(canonical);

            if (!File.Exists(canonical) || !File.Exists(actual))
            {
                measurements.Add(new SurfaceMeasurement
                {
                    SurfaceKey = key,
                    Status = SurfaceStatus.MissingPair,
                    FailureReason = "canonical_or_actual_missing",
                });
                continue;
            }

            var pair = new PngPair(
                SurfaceKey: key,
                CanonicalPath: canonical,
                ActualPath: actual,
                CanonicalBytes: new FileInfo(canonical).Length,
                ActualBytes: new FileInfo(actual).Length,
                CanonicalSha256: Pairer.Sha256File(canonical),
                ActualSha256: Pairer.Sha256File(actual));
            measurements.Add(PixelDiff.Compare(pair));
        }

        var bundle = BuildBundle(measurements, gitHead);
        var bundleSha = BundleWriter.Write(bundle, outDir);

        Console.WriteLine($"batch: surfaces={measurements.Count}");
        Console.WriteLine($"bundle_sha256={bundleSha}");
        Console.WriteLine($"out={outDir}");
        return 0;
    }

    private static int RunVerifyBundle(ReadOnlySpan<string> args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("ERROR: verify-bundle requires <bundle_dir>");
            return 2;
        }
        var bundleDir = args[0];
        var bundlePath = Path.Combine(bundleDir, "bundle.json");
        var checksumsPath = Path.Combine(bundleDir, "integrity", "checksums.json");
        if (!File.Exists(bundlePath))
        {
            Console.Error.WriteLine($"FAIL: bundle.json missing: {bundlePath}");
            return 1;
        }
        if (!File.Exists(checksumsPath))
        {
            Console.Error.WriteLine($"FAIL: integrity/checksums.json missing: {checksumsPath}");
            return 1;
        }

        var actualBundleSha = Pairer.Sha256File(bundlePath);
        using var checksumDoc = JsonDocument.Parse(File.ReadAllText(checksumsPath));
        var expectedBundleSha = checksumDoc.RootElement.GetProperty("bundle_sha256").GetString();

        if (!string.Equals(actualBundleSha, expectedBundleSha, StringComparison.OrdinalIgnoreCase))
        {
            Console.Error.WriteLine("FAIL: bundle_sha256 mismatch");
            Console.Error.WriteLine($"  expected: {expectedBundleSha}");
            Console.Error.WriteLine($"  actual:   {actualBundleSha}");
            return 1;
        }

        Console.WriteLine("verify-bundle: PASS");
        Console.WriteLine($"bundle_sha256={actualBundleSha}");
        return 0;
    }

    private static VisualParityBundle BuildBundle(List<SurfaceMeasurement> measurements, string gitHead)
    {
        return new VisualParityBundle
        {
            GeneratedAtUtc = DateTime.UtcNow.ToString("o"),
            GitHead = gitHead,
            VpBuildSha256 = "unbuilt-fase-1-scaffold",
            Surfaces = measurements,
        };
    }
}
