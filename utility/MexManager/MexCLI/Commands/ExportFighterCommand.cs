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

                // Append any related files ToPackage missed (kirby cap, effects, etc.)
                {
                    string filesDir = workspace.GetFilePath("");
                    if (Directory.Exists(filesDir))
                    {
                        List<string> extraFiles = new();
                        // Kirby cap file
                        if (!string.IsNullOrEmpty(fighter.Files.KirbyCapFileName))
                        {
                            string kcf = Path.Combine(filesDir, fighter.Files.KirbyCapFileName);
                            if (File.Exists(kcf)) extraFiles.Add(kcf);
                        }
                        // Kirby effect file
                        if (!string.IsNullOrEmpty(fighter.Files.KirbyEffectFile))
                        {
                            string kef = Path.Combine(filesDir, fighter.Files.KirbyEffectFile);
                            if (File.Exists(kef)) extraFiles.Add(kef);
                        }

                        if (extraFiles.Count > 0)
                        {
                            using FileStream zipFs = new(outputPath, FileMode.Open, FileAccess.ReadWrite);
                            using ZipArchive zip = new(zipFs, ZipArchiveMode.Update);
                            foreach (string filePath in extraFiles)
                            {
                                string name = Path.GetFileName(filePath);
                                if (zip.GetEntry(name) != null) continue;
                                zip.CreateEntryFromFile(filePath, name, CompressionLevel.Fastest);
                            }
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
