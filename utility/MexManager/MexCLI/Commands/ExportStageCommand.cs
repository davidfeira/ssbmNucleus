using System;
using System.IO;
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

                using FileStream fs = new(outputPath, FileMode.Create);
                MexStage.ToPackage(fs, workspace, stage, options);

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
