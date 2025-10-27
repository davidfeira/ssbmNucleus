using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class ListFightersCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli list-fighters <project.mexproj>");
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

            var fighters = new List<object>();
            for (int internalId = 0; internalId < workspace.Project.Fighters.Count; internalId++)
            {
                MexFighter fighter = workspace.Project.Fighters[internalId];
                int externalId = MexFighterIDConverter.ToExternalID(internalId, workspace.Project.Fighters.Count);

                fighters.Add(new
                {
                    internalId = internalId,
                    externalId = externalId,
                    name = fighter.Name,
                    costumeCount = fighter.Costumes.Count,
                    isMexFighter = MexFighterIDConverter.IsMexFighter(internalId, workspace.Project.Fighters.Count)
                });
            }

            var output = new
            {
                success = true,
                fighters = fighters
            };

            Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
