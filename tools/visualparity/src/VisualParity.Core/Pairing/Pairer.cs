// VisualParity.Core/Pairing/Pairer.cs
//
// Fase 1 - VisualParity V3.1 Core.
// Pairs canonical and actual PNGs by surface_key and detects missing/size
// mismatch. Does NOT compute pixel diff in Fase 1 (that comes later). Does
// NOT decide closure.

using System.Security.Cryptography;
using System.Text;
using VisualParity.Core.Bundle;

namespace VisualParity.Core.Pairing;

public readonly record struct PngPair(
    string SurfaceKey,
    string? CanonicalPath,
    string? ActualPath,
    long? CanonicalBytes,
    long? ActualBytes,
    string? CanonicalSha256,
    string? ActualSha256);

public static class Pairer
{
    /// <summary>
    /// Enumerate the union of surface_keys present in canonicalDir and
    /// actualDir, where the surface_key is derived from the PNG filename
    /// stem (without theme suffix / dimensions suffix). For Fase 1 we use
    /// the full filename stem as the surface_key; harness v3 is responsible
    /// for canonical naming.
    /// </summary>
    public static IEnumerable<PngPair> Pair(string canonicalDir, string actualDir)
    {
        var canon = IndexPngs(canonicalDir);
        var actual = IndexPngs(actualDir);
        var keys = canon.Keys.Concat(actual.Keys).Distinct().OrderBy(k => k);
        foreach (var key in keys)
        {
            canon.TryGetValue(key, out var c);
            actual.TryGetValue(key, out var a);
            yield return new PngPair(
                SurfaceKey: key,
                CanonicalPath: c.Path,
                ActualPath: a.Path,
                CanonicalBytes: c.Bytes,
                ActualBytes: a.Bytes,
                CanonicalSha256: c.Sha256,
                ActualSha256: a.Sha256);
        }
    }

    private static Dictionary<string, (string Path, long Bytes, string Sha256)> IndexPngs(string dir)
    {
        var result = new Dictionary<string, (string, long, string)>(StringComparer.Ordinal);
        if (!Directory.Exists(dir))
            return result;
        foreach (var path in Directory.EnumerateFiles(dir, "*.png", SearchOption.TopDirectoryOnly))
        {
            var stem = Path.GetFileNameWithoutExtension(path);
            var info = new FileInfo(path);
            var sha = Sha256File(path);
            result[stem] = (path, info.Length, sha);
        }
        return result;
    }

    public static string Sha256File(string path)
    {
        using var sha = SHA256.Create();
        using var stream = File.OpenRead(path);
        var hash = sha.ComputeHash(stream);
        var sb = new StringBuilder(hash.Length * 2);
        foreach (var b in hash)
            sb.Append(b.ToString("x2"));
        return sb.ToString();
    }
}
