using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using mexLib;
using mexLib.Types;

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

            HashSet<string> files = new(StringComparer.OrdinalIgnoreCase)
            {
                fighter.Files.FighterDataPath,
                fighter.Files.AnimFile,
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
                int soundCallsRetargeted = RetargetCloneSoundCalls(workspace, fighter);

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
                workspace.Project.CharacterSelect.FighterIcons.Add(new MexCharacterSelectIcon
                {
                    Fighter = externalId,
                });

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = fighter.Name,
                    internalId = internalId,
                    externalId = externalId,
                    costumeCount = fighter.Costumes.Count,
                    soundCallsRetargeted = soundCallsRetargeted
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
