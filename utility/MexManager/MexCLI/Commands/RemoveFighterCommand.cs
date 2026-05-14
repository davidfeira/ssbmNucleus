using System;
using System.IO;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class RemoveFighterCommand
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
                        usage = "mexcli remove-fighter <project.mexproj> <fighter-name>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string fighterName = args[2];

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                int internalId = -1;
                for (int i = 0; i < workspace.Project.Fighters.Count; i++)
                {
                    if (string.Equals(workspace.Project.Fighters[i].Name, fighterName, StringComparison.OrdinalIgnoreCase))
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
                        error = $"Fighter '{fighterName}' not found"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                if (!workspace.Project.RemoveFighter(workspace, internalId))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Cannot remove '{fighterName}' — only custom (m-ex) fighters can be removed"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // Remove the CSS icon that pointed to this fighter
                int externalId = MexFighterIDConverter.ToExternalID(internalId, workspace.Project.Fighters.Count + 1);
                for (int i = workspace.Project.CharacterSelect.FighterIcons.Count - 1; i >= 0; i--)
                {
                    if (workspace.Project.CharacterSelect.FighterIcons[i].Fighter == 0)
                    {
                        workspace.Project.CharacterSelect.FighterIcons.RemoveAt(i);
                        break;
                    }
                }

                workspace.Project.CharacterSelect.Template.Apply(
                    workspace.Project.CharacterSelect.FighterIcons);

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = fighterName,
                    removedIndex = internalId
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = $"Failed to remove fighter: {ex.Message}",
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
