using System.Text.Json;
using mexLib;

namespace MexCLI.Commands
{
    public static class OpenCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli open <project.mexproj>");
                return 1;
            }

            string projectPath = args[1];

            if (!File.Exists(projectPath))
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Project file not found: {projectPath}"
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }

            MexWorkspace? workspace;
            string error;
            bool isoMissing;

            bool success = MexWorkspace.TryOpenWorkspace(projectPath, out workspace, out error, out isoMissing);

            if (!success || workspace == null)
            {
                var errorOutput = new
                {
                    success = false,
                    error = error,
                    isoMissing = isoMissing
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }

            var output = new
            {
                success = true,
                projectPath = projectPath,
                projectName = workspace.Project.Build.Name,
                version = $"{workspace.Project.Build.MajorVersion}.{workspace.Project.Build.MinorVersion}.{workspace.Project.Build.PatchVersion}",
                fighterCount = workspace.Project.Fighters.Count,
                stageCount = workspace.Project.Stages.Count
            };

            Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
