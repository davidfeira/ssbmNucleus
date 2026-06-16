using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using HSDRaw;
using mexLib;
using mexLib.HsdObjects;
using mexLib.Types;
using mexLib.Utilties;

namespace MexCLI.Commands
{
    public static class AddFighterCommand
    {
        private static void FixSharedFile(
            MexWorkspace workspace,
            MexFighter.FighterFiles files,
            Func<MexFighter.FighterFiles, string?> getter,
            Action<MexFighter.FighterFiles, string?> setter)
        {
            string? current = getter(files);
            if (string.IsNullOrEmpty(current)) return;
            if (!current.Contains("_0")) return;

            // e.g. EfLgData_001.dat → EfLgData.dat
            int underscoreIdx = current.LastIndexOf('_');
            if (underscoreIdx < 0) return;
            string ext = Path.GetExtension(current);
            string original = current.Substring(0, underscoreIdx) + ext;

            string currentPath = workspace.GetFilePath(current);
            string originalPath = workspace.GetFilePath(original);

            // Only collapse onto the original when the two files are byte-identical.
            // A differing _00n copy is a genuine variant (e.g. a clone's modified
            // effect file) and must be kept — collapsing it would corrupt that fighter.
            if (File.Exists(originalPath) && File.Exists(currentPath) &&
                FilesAreIdentical(originalPath, currentPath))
            {
                // Original already exists and matches — use it, delete the duplicate
                File.Delete(currentPath);
                setter(files, original);
            }
        }

        private static bool FilesAreIdentical(string a, string b)
        {
            FileInfo fa = new(a), fb = new(b);
            if (fa.Length != fb.Length) return false;
            return File.ReadAllBytes(a).AsSpan().SequenceEqual(File.ReadAllBytes(b));
        }

        private static int ReadUInt32BE(byte[] data, int offset)
        {
            return data[offset] << 24 | data[offset + 1] << 16 | data[offset + 2] << 8 | data[offset + 3];
        }

        private static void WriteUInt32BE(byte[] data, int offset, int value)
        {
            data[offset] = (byte)(value >> 24);
            data[offset + 1] = (byte)(value >> 16);
            data[offset + 2] = (byte)(value >> 8);
            data[offset + 3] = (byte)value;
        }

        private static int RetargetEmbeddedSemCallsInFile(string filePath, int sourceBank, int targetBank, int scriptLimit)
        {
            if (!File.Exists(filePath) || sourceBank < 0 || targetBank < 0 || sourceBank == targetBank || scriptLimit <= 0)
                return 0;

            byte[] data = File.ReadAllBytes(filePath);
            int sourceBase = sourceBank * 10000;
            int targetBase = targetBank * 10000;
            int changed = 0;

            // Sound-script IDs are stored as 4-byte-aligned int32 fields in the
            // fighter's HSD structures, so only scan on 4-byte boundaries. A
            // byte-by-byte scan rewrites any 4 bytes that coincidentally fall in
            // the bank's narrow value range, corrupting unrelated data — this
            // crashed CDI King in-match (assertion "0" in mpcoll.c) because it
            // mangled animation/collision bytes that merely looked like calls.
            for (int offset = 0; offset <= data.Length - 4; offset += 4)
            {
                int value = ReadUInt32BE(data, offset);
                int script = value - sourceBase;
                if (script >= 0 && script < scriptLimit)
                {
                    WriteUInt32BE(data, offset, targetBase + script);
                    changed++;
                }
            }

            if (changed > 0)
                File.WriteAllBytes(filePath, data);

            return changed;
        }

        private static int RetargetCloneSoundCalls(MexWorkspace workspace, MexFighter fighter)
        {
            if (string.IsNullOrEmpty(fighter.Files.FighterDataSymbol))
                return 0;

            int sourceBank = -1;
            foreach (MexFighter existing in workspace.Project.Fighters)
            {
                if (existing.SoundBank == fighter.SoundBank)
                    continue;
                if (existing.SoundBank < 0 || existing.SoundBank >= workspace.Project.SoundGroups.Count)
                    continue;
                if (string.Equals(existing.Files.FighterDataSymbol, fighter.Files.FighterDataSymbol, StringComparison.OrdinalIgnoreCase))
                {
                    sourceBank = existing.SoundBank;
                    break;
                }
            }
            if (sourceBank < 0 || fighter.SoundBank < 0 || fighter.SoundBank >= workspace.Project.SoundGroups.Count)
                return 0;

            int sourceScripts = workspace.Project.SoundGroups[sourceBank].Scripts?.Count ?? 0;
            int targetScripts = workspace.Project.SoundGroups[fighter.SoundBank].Scripts?.Count ?? 0;
            int scriptLimit = Math.Min(sourceScripts, targetScripts);
            if (scriptLimit <= 0)
                return 0;

            // Only the main fighter data file holds sound-script IDs (the SFX
            // table and subaction sound events). The AJ file is pure animation
            // joint data; scanning it only yields false-positive rewrites that
            // corrupt animations, so leave it untouched.
            HashSet<string> files = new(StringComparer.OrdinalIgnoreCase)
            {
                fighter.Files.FighterDataPath,
            };

            int changed = 0;
            foreach (string path in files)
            {
                if (string.IsNullOrEmpty(path))
                    continue;
                changed += RetargetEmbeddedSemCallsInFile(
                    workspace.GetFilePath(path), sourceBank, fighter.SoundBank, scriptLimit);
            }
            return changed;
        }

        /// <summary>
        /// Merge per-pack Gecko codes bundled in the fighter zip as `codes.ini`
        /// into the project's codes, so installing a pack applies its own fixes
        /// (self-contained). E.g. Metal Mario ships a code that re-registers its
        /// cape article into the Fighter item runtime table (the tool rebuild
        /// otherwise loses that registration -> side-B "item not initialized").
        /// Deduped by compiled bytes so re-importing doesn't add duplicates.
        /// </summary>
        private static int MergePackCodes(MexWorkspace workspace, string fighterZipPath)
        {
            using FileStream stream = new(fighterZipPath, FileMode.Open);
            using System.IO.Compression.ZipArchive zip = new(stream);
            System.IO.Compression.ZipArchiveEntry? entry =
                zip.GetEntry("codes.ini") ?? zip.GetEntry("fighter_codes.ini");
            if (entry == null)
                return 0;

            byte[] data;
            using (Stream es = entry.Open())
            using (MemoryStream ms = new())
            {
                es.CopyTo(ms);
                data = ms.ToArray();
            }

            List<byte[]> existing = workspace.Project.Codes
                .Select(c => c.GetCompiled())
                .Where(b => b != null)
                .Select(b => b!)
                .ToList();

            int added = 0;
            foreach (MexCode code in CodeLoader.FromINI(data))
            {
                byte[]? comp = code.GetCompiled();
                if (comp == null)
                    continue;
                if (existing.Any(e => e.AsSpan().SequenceEqual(comp)))
                    continue;
                workspace.Project.Codes.Add(code);
                existing.Add(comp);
                added++;
            }
            return added;
        }

        /// <summary>
        /// Merge per-pack m-ex function patches bundled in the fighter zip under
        /// `patches/*.dat` into the project's Patches (saved to MxPt.dat, which
        /// m-ex loads + applies at boot). E.g. Metal Mario ships
        /// `patches/clone_engine.dat` — the m-ex function patch that redirects a
        /// clone's vanilla-kind article spawns (Mario cape = Fighter item 83,
        /// fireball = 48) to the clone's OWN article data. Without it, side-B/cape
        /// crashes with m-ex "item not initialized" (the vanilla FighterRuntime
        /// slot is null for a clone). clone_engine is generic (remaps by item slot,
        /// not fighter id), so ONE copy fixes every clone — hence dedupe by patch
        /// name: multiple clone packs won't add duplicates.
        /// </summary>
        private static int MergePackPatches(MexWorkspace workspace, string fighterZipPath)
        {
            using FileStream stream = new(fighterZipPath, FileMode.Open);
            using System.IO.Compression.ZipArchive zip = new(stream);

            int added = 0;
            foreach (System.IO.Compression.ZipArchiveEntry entry in zip.Entries)
            {
                if (entry.Name.Length == 0) continue;
                if (!entry.FullName.StartsWith("patches/", StringComparison.OrdinalIgnoreCase)) continue;
                if (!entry.Name.EndsWith(".dat", StringComparison.OrdinalIgnoreCase)) continue;

                byte[] data;
                using (Stream es = entry.Open())
                using (MemoryStream ms = new())
                {
                    es.CopyTo(ms);
                    data = ms.ToArray();
                }

                HSDRawFile f;
                try { f = new HSDRawFile(data); }
                catch { continue; }

                foreach (HSDRootNode r in f.Roots)
                {
                    if (r?.Data?._s == null) continue;
                    if (workspace.Project.Patches.Any(p =>
                        string.Equals(p.Name, r.Name, StringComparison.OrdinalIgnoreCase)))
                        continue;
                    workspace.Project.Patches.Add(new MexCodePatch(r.Name, new HSDFunctionDat()
                    {
                        _s = r.Data._s
                    })
                    {
                        Enabled = true
                    });
                    added++;
                }
            }
            return added;
        }

        public static int Execute(string[] args)
        {
            try
            {
                if (args.Length < 3)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = "Invalid arguments",
                        usage = "mexcli add-fighter <project.mexproj> <fighter.zip>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string fighterZipPath = args[2];

                if (!File.Exists(fighterZipPath))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Fighter ZIP not found: {fighterZipPath}"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // Import fighter from ZIP
                MexFighter? fighter;
                {
                    using FileStream stream = new(fighterZipPath, FileMode.Open);
                    var importError = MexFighter.FromPackage(workspace, stream, out fighter);

                    if (importError != null || fighter == null)
                    {
                        Console.WriteLine(JsonSerializer.Serialize(new
                        {
                            success = false,
                            error = importError?.Message ?? "Failed to parse fighter package"
                        }, new JsonSerializerOptions { WriteIndented = true }));
                        return 1;
                    }
                }

                // FromPackage doesn't extract fighter data files — do it manually
                {
                    using FileStream stream2 = new(fighterZipPath, FileMode.Open);
                    using System.IO.Compression.ZipArchive zip = new(stream2);
                    fighter.Files.FromPackage(workspace, zip);

                    // Also extract any remaining .dat files (kirby cap, effects, etc.)
                    foreach (var entry in zip.Entries)
                    {
                        if (entry.Name.Length == 0) continue;
                        if (!entry.Name.EndsWith(".dat", StringComparison.OrdinalIgnoreCase)) continue;
                        // `patches/*.dat` are m-ex function patches (e.g. clone_engine),
                        // not loose game files — they go into Project.Patches (MxPt.dat)
                        // via MergePackPatches, so don't extract them as standalone files.
                        if (entry.FullName.StartsWith("patches/", StringComparison.OrdinalIgnoreCase)) continue;
                        string destPath = workspace.GetFilePath(entry.Name);
                        if (File.Exists(destPath)) continue;
                        string? destDir = Path.GetDirectoryName(destPath);
                        if (destDir != null && !Directory.Exists(destDir))
                            Directory.CreateDirectory(destDir);
                        using Stream entryStream = entry.Open();
                        using FileStream outFile = new(destPath, FileMode.CreateNew);
                        entryStream.CopyTo(outFile);
                    }
                }

                // Fix shared files: FromPackage renames files with _001 suffix via
                // GetUniqueFilePath when a file already exists. But if the original
                // file is identical (shared resource like effect files), we should
                // use the original instead of the duplicate.
                FixSharedFile(workspace, fighter.Files, f => f.EffectFile, (f, v) => f.EffectFile = v);
                FixSharedFile(workspace, fighter.Files, f => f.KirbyEffectFile, (f, v) => f.KirbyEffectFile = v);
                FixSharedFile(workspace, fighter.Files, f => f.KirbyCapFileName, (f, v) => f.KirbyCapFileName = v);

                // Internal index 34 is a broken slot in m-ex — insert a NONE placeholder
                // if this addition would land there, then add the real fighter after it.
                int insertIndex = workspace.Project.Fighters.Count - 6;
                if (insertIndex == 34)
                {
                    MexFighter noneFighter = new() { Name = "NONE" };
                    workspace.Project.AddNewFighter(noneFighter);
                }

                // Compute the external ID before adding (same as AddNewFighter does internally)
                int internalId = workspace.Project.Fighters.Count - 6;
                int externalId = MexFighterIDConverter.ToExternalID(internalId, workspace.Project.Fighters.Count);

                // Add fighter to project (shifts existing CSS icon references)
                workspace.Project.AddNewFighter(fighter);

                // Add a CSS icon for the new fighter
                int cssSfxId = FighterAudioHelpers.ResolveCssSfxId(workspace, fighter.AnnouncerCall);
                MexCharacterSelectIcon icon = new()
                {
                    Fighter = externalId,
                };
                if (cssSfxId >= 0)
                    icon.SFXID = cssSfxId;
                workspace.Project.CharacterSelect.FighterIcons.Add(icon);

                // Merge any per-pack Gecko codes the fighter ships (self-contained fixes).
                int packCodesMerged = MergePackCodes(workspace, fighterZipPath);
                // Merge any per-pack m-ex function patches (e.g. clone_engine.dat) so
                // a clone's cape/fireball articles work (-> MxPt.dat in the ISO).
                int packPatchesMerged = MergePackPatches(workspace, fighterZipPath);

                workspace.Save(null);
                int soundCallsRetargeted = RetargetCloneSoundCalls(workspace, fighter);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = fighter.Name,
                    internalId = internalId,
                    externalId = externalId,
                    costumeCount = fighter.Costumes.Count,
                    cssSfxId = cssSfxId,
                    soundCallsRetargeted = soundCallsRetargeted,
                    packCodesMerged = packCodesMerged,
                    packPatchesMerged = packPatchesMerged
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = $"Failed to add fighter: {ex.Message}",
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
