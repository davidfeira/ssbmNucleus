using System;
using System.IO;
using System.IO.Compression;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class ExportFighterCommand
    {
        public static int Execute(string[] args)
        {
            try
            {
                if (args.Length < 4)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = "Invalid arguments",
                        usage = "mexcli export-fighter <project.mexproj> <fighter-index> <output.zip>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                int fighterIndex = int.Parse(args[2]);
                string outputPath = args[3];

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                if (fighterIndex < 0 || fighterIndex >= workspace.Project.Fighters.Count)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Fighter index {fighterIndex} out of range (0-{workspace.Project.Fighters.Count - 1})"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                MexFighter fighter = workspace.Project.Fighters[fighterIndex];

                MexFighter.FighterPackOptions options = new()
                {
                    ExportFiles = true,
                    ExportSoundBank = true,
                    ExportMedia = true,
                    ExportCostumes = true,
                };

                string? dir = Path.GetDirectoryName(outputPath);
                if (dir != null && !Directory.Exists(dir))
                    Directory.CreateDirectory(dir);

                using (FileStream fs = new(outputPath, FileMode.Create))
                    fighter.ToPackage(workspace, fs, options);

                // Append related files ToPackage missed: kirby cap/effect + any
                // files referenced by name inside the fighter .dat binary
                {
                    string filesDir = workspace.GetFilePath("");
                    if (Directory.Exists(filesDir))
                    {
                        HashSet<string> extraFiles = new(StringComparer.OrdinalIgnoreCase);

                        // Known metadata fields
                        if (!string.IsNullOrEmpty(fighter.Files.KirbyCapFileName))
                            extraFiles.Add(fighter.Files.KirbyCapFileName);
                        if (!string.IsNullOrEmpty(fighter.Files.KirbyEffectFile))
                            extraFiles.Add(fighter.Files.KirbyEffectFile);

                        // Scan fighter .dat binary for embedded .dat filename references
                        // Custom fighter code can load files at runtime by name (e.g. Meters.dat)
                        // Strategy: find ".dat\0" sequences, walk backwards to extract the filename
                        if (!string.IsNullOrEmpty(fighter.Files.FighterDataPath))
                        {
                            string datPath = Path.Combine(filesDir, fighter.Files.FighterDataPath);
                            if (File.Exists(datPath))
                            {
                                byte[] datBytes = File.ReadAllBytes(datPath);
                                byte[] pattern = { 0x2E, 0x64, 0x61, 0x74, 0x00 }; // ".dat\0"
                                for (int bi = 0; bi <= datBytes.Length - pattern.Length; bi++)
                                {
                                    if (datBytes[bi] != 0x2E || datBytes[bi + 1] != 0x64 ||
                                        datBytes[bi + 2] != 0x61 || datBytes[bi + 3] != 0x74 ||
                                        datBytes[bi + 4] != 0x00) continue;

                                    // Walk backwards from '.' to find filename start
                                    // Valid filename chars: A-Z, a-z, 0-9, _, -
                                    int start = bi - 1;
                                    while (start >= 0)
                                    {
                                        byte c = datBytes[start];
                                        if ((c >= (byte)'A' && c <= (byte)'Z') ||
                                            (c >= (byte)'a' && c <= (byte)'z') ||
                                            (c >= (byte)'0' && c <= (byte)'9') ||
                                            c == (byte)'_' || c == (byte)'-')
                                            start--;
                                        else
                                            break;
                                    }
                                    start++;

                                    int nameLen = bi + 4 - start;
                                    if (nameLen >= 5 && nameLen <= 64)
                                    {
                                        string candidate = System.Text.Encoding.ASCII.GetString(datBytes, start, nameLen);
                                        // Try progressively shorter prefixes until we find a real file
                                        for (int trim = 0; trim < candidate.Length - 5; trim++)
                                        {
                                            string sub = candidate.Substring(trim);
                                            if (char.IsUpper(sub[0]) && File.Exists(Path.Combine(filesDir, sub)))
                                            {
                                                extraFiles.Add(sub);
                                                break;
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        // Add matching files to ZIP
                        using FileStream zipFs = new(outputPath, FileMode.Open, FileAccess.ReadWrite);
                        using ZipArchive zip = new(zipFs, ZipArchiveMode.Update);
                        foreach (string fileName in extraFiles)
                        {
                            string filePath = Path.Combine(filesDir, fileName);
                            if (!File.Exists(filePath)) continue;
                            if (zip.GetEntry(fileName) != null) continue;
                            zip.CreateEntryFromFile(filePath, fileName, CompressionLevel.Fastest);
                        }
                    }
                }

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = fighter.Name,
                    index = fighterIndex,
                    costumeCount = fighter.Costumes.Count,
                    outputPath = outputPath
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = $"Failed to export fighter: {ex.Message}",
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
