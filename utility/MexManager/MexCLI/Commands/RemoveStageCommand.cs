using System;
using System.IO;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class RemoveStageCommand
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
                        usage = "mexcli remove-stage <project.mexproj> <stage-name>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string stageName = args[2];

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                int internalId = -1;
                for (int i = 0; i < workspace.Project.Stages.Count; i++)
                {
                    if (string.Equals(workspace.Project.Stages[i].Name, stageName, StringComparison.OrdinalIgnoreCase))
                    {
                        internalId = i;
                        break;
                    }
                }

                if (internalId < 0)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Stage '{stageName}' not found"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                if (!workspace.Project.RemoveStage(workspace, internalId))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Cannot remove '{stageName}' — only custom stages (index > 70) can be removed"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = stageName,
                    removedIndex = internalId
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = $"Failed to remove stage: {ex.Message}",
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
