using System;
using System.IO;
using System.IO.Compression;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class ExportStageCommand
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
                        usage = "mexcli export-stage <project.mexproj> <stage-index> <output.zip>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                int stageIndex = int.Parse(args[2]);
                string outputPath = args[3];

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                if (stageIndex < 0 || stageIndex >= workspace.Project.Stages.Count)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Stage index {stageIndex} out of range (0-{workspace.Project.Stages.Count - 1})"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                MexStage stage = workspace.Project.Stages[stageIndex];

                MexStage.StagePackOptions options = new()
                {
                    ExportFiles = true,
                    ExportSound = true,
                };

                string? dir = Path.GetDirectoryName(outputPath);
                if (dir != null && !Directory.Exists(dir))
                    Directory.CreateDirectory(dir);

                // First do the standard export
                using (FileStream fs = new(outputPath, FileMode.Create))
                    MexStage.ToPackage(fs, workspace, stage, options);

                // Then append any related files the stage code loads dynamically
                // (e.g., GrAc.dat → GrAcDy.dat, GrAcNt.dat, GrAcVBlanca.dat, ...)
                if (stage.FileName != null)
                {
                    string stem = Path.GetFileNameWithoutExtension(stage.FileName.TrimStart('/'));
                    string filesDir = workspace.GetFilePath("");
                    if (Directory.Exists(filesDir))
                    {
                        HashSet<string> alreadyPacked = new(StringComparer.OrdinalIgnoreCase);
                        alreadyPacked.Add(stage.FileName.TrimStart('/'));
                        foreach (string f in stage.AdditionalFiles)
                            alreadyPacked.Add(f.TrimStart('/'));

                        string[] relatedFiles = Directory.GetFiles(filesDir, stem + "*");
                        if (relatedFiles.Length > alreadyPacked.Count)
                        {
                            using FileStream zipFs = new(outputPath, FileMode.Open, FileAccess.ReadWrite);
                            using ZipArchive zip = new(zipFs, ZipArchiveMode.Update);
                            foreach (string relatedFile in relatedFiles)
                            {
                                string name = Path.GetFileName(relatedFile);
                                if (alreadyPacked.Contains(name))
                                    continue;
                                if (zip.GetEntry(name) != null)
                                    continue;
                                zip.CreateEntryFromFile(relatedFile, name, CompressionLevel.Fastest);
                            }
                        }
                    }
                }

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = stage.Name,
                    index = stageIndex,
                    outputPath = outputPath
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = $"Failed to export stage: {ex.Message}",
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
