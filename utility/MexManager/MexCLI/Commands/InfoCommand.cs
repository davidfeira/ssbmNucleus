using System.Text.Json;
using mexLib;

namespace MexCLI.Commands
{
    public static class InfoCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli info <project.mexproj>");
                return 1;
            }

            string projectPath = args[1];

            MexWorkspace? workspace;
            string error;
            bool isoMissing;

            bool success = MexWorkspace.TryOpenWorkspace(projectPath, out workspace, out error, out isoMissing);

            if (!success || workspace == null)
            {
                var errorOutput = new
                {
                    success = false,
                    error = error
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }

            var output = new
            {
                success = true,
                build = new
                {
                    name = workspace.Project.Build.Name,
                    majorVersion = workspace.Project.Build.MajorVersion,
                    minorVersion = workspace.Project.Build.MinorVersion,
                    patchVersion = workspace.Project.Build.PatchVersion,
                    shortName = workspace.Project.Build.ShortName,
                    longName = workspace.Project.Build.LongName,
                    shortMaker = workspace.Project.Build.ShortMaker,
                    longMaker = workspace.Project.Build.LongMaker
                },
                counts = new
                {
                    fighters = workspace.Project.Fighters.Count,
                    stages = workspace.Project.Stages.Count,
                    music = workspace.Project.Music.Count,
                    soundGroups = workspace.Project.SoundGroups.Count,
                    series = workspace.Project.Series.Count
                }
            };

            Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
