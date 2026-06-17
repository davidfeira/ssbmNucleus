using System.IO.Compression;
using System.Text;
using System.Text.Json;
using mexLib;
using mexLib.AssetTypes;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// BATCH costume import. Opens the workspace ONCE, imports many costumes
    /// (across one or more fighters), then calls Save() ONCE.
    ///
    /// Why this is much faster than calling `import-costume` N times: each
    /// `import-costume` runs the full <see cref="MexWorkspace.Save"/>, which
    /// regenerates MxDt, PlCo, IfAll (stock icons), MnSlChr (all CSP portraits),
    /// MnSlMap, GmRst, trophies and recompiles codes.gct -- the entire build --
    /// every single call. Installing N skins therefore pays N full recompiles plus
    /// N workspace opens + N process starts. Batching collapses that to ONE.
    ///
    /// Usage: mexcli import-costumes &lt;project.mexproj&gt; &lt;manifest.json&gt;
    ///   manifest.json: { "Fox": ["a.zip","b.zip"], "C. Falcon": ["c.zip"] }
    ///   (keys are fighter name or internal-id; values are costume .zip paths)
    ///
    /// Two stacked speedups over N `import-costume` calls:
    ///   1. ONE amortized Save()/recompile for the whole batch (vs N).
    ///   2. The CSP/icon PNG decode (the expensive ImageSharp quantization) runs in
    ///      PARALLEL across all cores up-front (<see cref="ParallelDecode"/>), warming
    ///      <see cref="MexTextureAsset.DecodeCache"/>; the serial import below then
    ///      hits the cache instead of decoding inline. The FileManager mutations stay
    ///      strictly serial, so the output is byte-identical to N sequential imports
    ///      (validated full-tree via backend/parallel_diff_build.py + in-game boot).
    /// Measured ~7x faster than sequential on a mixed multi-fighter batch.
    /// </summary>
    public static class ImportCostumesCommand
    {
        private static int KirbyVanillaColorIndex(string fileName)
        {
            string stem = Path.GetFileNameWithoutExtension(fileName ?? "");
            if (!stem.StartsWith("PlKb") || stem.Length < 6)
                return -1;
            return stem.Substring(4, 2) switch
            {
                "Nr" => 0, "Ye" => 1, "Bu" => 2, "Re" => 3, "Gr" => 4, "Wh" => 5, _ => -1,
            };
        }

        private static void ApplyOriginalCostumeIndex(MexFighter fighter, MexCostume costume, StringBuilder log)
        {
            string jointSymbol = costume.File.JointSymbol;
            if (string.IsNullOrEmpty(jointSymbol))
                return;
            foreach (MexCostume existing in fighter.Costumes)
            {
                if (string.Equals(existing.File.JointSymbol, jointSymbol, StringComparison.Ordinal))
                {
                    costume.File.VisibilityIndex = existing.File.VisibilityIndex;
                    return;
                }
            }
        }

        private static void AddKirbyCapEntries(MexWorkspace workspace, MexCostume costume)
        {
            int colorIdx = KirbyVanillaColorIndex(costume.File.FileName);
            foreach (MexFighter f in workspace.Project.Fighters)
            {
                if (f.HasKirbyCostumes)
                {
                    var src = f.KirbyCostumes[colorIdx >= 0 && colorIdx < f.KirbyCostumes.Count ? colorIdx : 0];
                    f.KirbyCostumes.Add(new MexCostumeFile()
                    {
                        FileName = src.FileName,
                        JointSymbol = src.JointSymbol,
                        MaterialSymbol = src.MaterialSymbol,
                    });
                }
            }
        }

        private static (MexFighter?, int) FindFighter(MexWorkspace ws, string nameOrId)
        {
            if (int.TryParse(nameOrId, out int id) && id >= 0 && id < ws.Project.Fighters.Count)
                return (ws.Project.Fighters[id], id);
            for (int i = 0; i < ws.Project.Fighters.Count; i++)
                if (ws.Project.Fighters[i].Name.Equals(nameOrId, StringComparison.OrdinalIgnoreCase))
                    return (ws.Project.Fighters[i], i);
            return (null, -1);
        }

        /// <summary>
        /// Decode every CSP/icon PNG referenced by the manifest in parallel into
        /// <see cref="MexTextureAsset.DecodeCache"/>. Pure (no workspace mutation),
        /// so it is safe to run across all cores. A miss in the serial pass simply
        /// decodes inline -- this is a best-effort warm-up, never a correctness gate,
        /// so a bad/locked zip here is swallowed.
        /// </summary>
        private static void ParallelDecode(Dictionary<string, List<string>> manifest)
        {
            // Format/dimension templates -- read straight off a fresh costume so the
            // decode parameters can never drift from the real import path.
            MexCostume tpl = new();
            MexTextureAsset iconTpl = tpl.IconAsset;
            MexTextureAsset cspTpl = tpl.CSPAsset;

            var zips = manifest.Values.SelectMany(z => z)
                                      .Where(File.Exists)
                                      .Distinct()
                                      .ToList();

            Parallel.ForEach(zips, zipPath =>
            {
                try
                {
                    using FileStream fs = new(zipPath, FileMode.Open, FileAccess.Read);
                    using ZipArchive zip = new(fs, ZipArchiveMode.Read);
                    foreach (ZipArchiveEntry entry in zip.Entries)
                    {
                        MexTextureAsset? asset = entry.Name.ToLower() switch
                        {
                            "stc.png" or "stock.png" or "icon.png" => iconTpl,
                            "csp.png" or "portrait.png" or "select.png" => cspTpl,
                            _ => null,
                        };
                        if (asset == null)
                            continue;

                        using Stream es = entry.Open();
                        using MemoryStream ms = new();
                        es.CopyTo(ms);
                        byte[] bytes = ms.ToArray();

                        string dkey = asset.DecodeKey(bytes);
                        MexTextureAsset.DecodeCache!.GetOrAdd(dkey, _ => asset.DecodeImageBytes(bytes));
                    }
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"[predecode] {Path.GetFileName(zipPath)}: {ex.Message}");
                }
            });
        }

        public static int Execute(string[] args)
        {
            if (args.Length < 3)
            {
                Console.Error.WriteLine("Usage: mexcli import-costumes <project.mexproj> <manifest.json>");
                return 1;
            }
            string projectPath = args[1];
            string manifestPath = args[2];

            if (!File.Exists(manifestPath))
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = $"Manifest not found: {manifestPath}" }));
                return 1;
            }

            Dictionary<string, List<string>>? manifest;
            try
            {
                manifest = JsonSerializer.Deserialize<Dictionary<string, List<string>>>(File.ReadAllText(manifestPath));
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = $"Bad manifest: {ex.Message}" }));
                return 1;
            }
            if (manifest == null || manifest.Count == 0)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = "Empty manifest" }));
                return 1;
            }

            if (!MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out _) || workspace == null)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }));
                return 1;
            }

            var perFighter = new Dictionary<string, object>();
            int totalImported = 0, totalFailed = 0;

            // Arm the decode cache and pre-decode every CSP/icon PNG across all zips
            // in parallel (the heavy ImageSharp quantization). The serial import loop
            // below then hits the cache instead of decoding inline, so the FileManager
            // mutations stay strictly serial (byte-identical output) while the decode
            // is parallelized across cores. finally{} re-arms the single-import path.
            MexTextureAsset.DecodeCache = new();
            try
            {
                ParallelDecode(manifest);

                foreach (var (key, zips) in manifest)
                {
                    var (fighter, internalId) = FindFighter(workspace, key);
                    if (fighter == null)
                    {
                        perFighter[key] = new { error = "fighter not found", imported = 0 };
                        continue;
                    }
                    int imported = 0, failed = 0;
                    foreach (string zipPath in zips)
                    {
                        if (!File.Exists(zipPath)) { failed++; totalFailed++; continue; }
                        try
                        {
                            using FileStream zs = new(zipPath, FileMode.Open, FileAccess.Read);
                            StringBuilder log = new();
                            var costumes = MexCostume.FromZip(workspace, zs, log).ToList();
                            foreach (var costume in costumes)
                            {
                                ApplyOriginalCostumeIndex(fighter, costume, log);
                                fighter.Costumes.Add(costume);
                                if (internalId == 4)
                                    AddKirbyCapEntries(workspace, costume);
                            }
                            imported += costumes.Count;
                            totalImported += costumes.Count;
                        }
                        catch (Exception ex)
                        {
                            failed++; totalFailed++;
                            Console.Error.WriteLine($"[{key}] {Path.GetFileName(zipPath)}: {ex.Message}");
                        }
                    }
                    perFighter[fighter.Name] = new { imported, failed, totalCostumes = fighter.Costumes.Count };
                }

                // The single, amortized full recompile + write for the WHOLE batch.
                workspace.Save(null);
            }
            finally
            {
                MexTextureAsset.DecodeCache = null;
            }

            Console.WriteLine(JsonSerializer.Serialize(new
            {
                success = true,
                totalImported,
                totalFailed,
                perFighter,
            }, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
