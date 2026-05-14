using System;
using System.IO;
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

                using FileStream fs = new(outputPath, FileMode.Create);
                fighter.ToPackage(workspace, fs, options);

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
