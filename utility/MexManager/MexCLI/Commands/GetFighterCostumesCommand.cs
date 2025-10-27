using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class GetFighterCostumesCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 3)
            {
                Console.Error.WriteLine("Usage: mexcli get-costumes <project.mexproj> <fighter_name_or_id>");
                return 1;
            }

            string projectPath = args[1];
            string fighterNameOrId = args[2];

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

            // Find fighter by name or ID
            MexFighter? fighter = null;
            int fighterInternalId = -1;

            // Try parsing as internal ID first
            if (int.TryParse(fighterNameOrId, out int parsedId))
            {
                if (parsedId >= 0 && parsedId < workspace.Project.Fighters.Count)
                {
                    fighter = workspace.Project.Fighters[parsedId];
                    fighterInternalId = parsedId;
                }
            }

            // If not found, search by name (case-insensitive)
            if (fighter == null)
            {
                for (int i = 0; i < workspace.Project.Fighters.Count; i++)
                {
                    if (workspace.Project.Fighters[i].Name.Equals(fighterNameOrId, StringComparison.OrdinalIgnoreCase))
                    {
                        fighter = workspace.Project.Fighters[i];
                        fighterInternalId = i;
                        break;
                    }
                }
            }

            if (fighter == null)
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Fighter not found: {fighterNameOrId}"
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }

            // Get costumes
            var costumes = new List<object>();
            for (int i = 0; i < fighter.Costumes.Count; i++)
            {
                var costume = fighter.Costumes[i];
                costumes.Add(new
                {
                    index = i,
                    name = costume.Name,
                    fileName = costume.File.FileName,
                    colorSmashGroup = costume.ColorSmashGroup,
                    hasCSP = !string.IsNullOrEmpty(costume.CSP),
                    hasIcon = !string.IsNullOrEmpty(costume.Icon),
                    csp = costume.CSP,
                    icon = costume.Icon
                });
            }

            var output = new
            {
                success = true,
                fighter = fighter.Name,
                fighterInternalId = fighterInternalId,
                costumeCount = fighter.Costumes.Count,
                costumes = costumes
            };

            Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
