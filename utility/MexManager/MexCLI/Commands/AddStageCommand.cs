using System;
using System.IO;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class AddStageCommand
    {
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
                        usage = "mexcli add-stage <project.mexproj> <stage.zip>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string stageZipPath = args[2];

                if (!File.Exists(stageZipPath))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Stage ZIP not found: {stageZipPath}"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                using FileStream stream = new(stageZipPath, FileMode.Open);
                var importError = MexStage.FromPackage(stream, workspace, out MexStage? stage);

                if (importError != null || stage == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = importError?.Message ?? "Failed to parse stage package"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // Extract any extra related files from the ZIP that FromPackage didn't handle
                // (dynamically loaded files like GrAcDy.dat, GrAcNt.dat, etc.)
                {
                    using FileStream stream2 = new(stageZipPath, FileMode.Open);
                    using System.IO.Compression.ZipArchive zip = new(stream2);
                    foreach (var entry in zip.Entries)
                    {
                        if (!entry.Name.EndsWith(".dat", StringComparison.OrdinalIgnoreCase))
                            continue;
                        if (entry.Name.Equals("stage.json", StringComparison.OrdinalIgnoreCase))
                            continue;
                        string destPath = workspace.GetFilePath(entry.Name);
                        if (File.Exists(destPath))
                            continue;
                        string? destDir = Path.GetDirectoryName(destPath);
                        if (destDir != null && !Directory.Exists(destDir))
                            Directory.CreateDirectory(destDir);
                        using Stream entryStream = entry.Open();
                        using FileStream outFile = new(destPath, FileMode.CreateNew);
                        entryStream.CopyTo(outFile);
                    }
                }

                int internalId = workspace.Project.AddStage(stage);
                int externalId = MexStageIDConverter.ToExternalID(internalId);

                // Find or create a "Custom" SSS page (page index 1+)
                if (workspace.Project.StageSelects.Count < 2)
                {
                    workspace.Project.StageSelects.Add(new MexStageSelect
                    {
                        Name = "Custom",
                    });
                }

                MexStageSelect customPage = workspace.Project.StageSelects[^1];

                customPage.StageIcons.Add(new MexStageSelectIcon
                {
                    StageID = externalId,
                    Status = MexStageSelectIcon.StageIconStatus.Unlocked,
                });

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = stage.Name,
                    internalId = internalId,
                    externalId = externalId,
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = $"Failed to add stage: {ex.Message}",
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
