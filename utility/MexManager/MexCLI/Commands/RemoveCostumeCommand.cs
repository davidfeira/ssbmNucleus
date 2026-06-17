using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class RemoveCostumeCommand
    {
        /// <summary>Resolve a fighter by internal id or name. Returns (null, -1) if missing.</summary>
        internal static (MexFighter?, int) FindFighter(MexWorkspace workspace, string nameOrId)
        {
            if (int.TryParse(nameOrId, out int id) && id >= 0 && id < workspace.Project.Fighters.Count)
                return (workspace.Project.Fighters[id], id);
            for (int i = 0; i < workspace.Project.Fighters.Count; i++)
                if (workspace.Project.Fighters[i].Name.Equals(nameOrId, StringComparison.OrdinalIgnoreCase))
                    return (workspace.Project.Fighters[i], i);
            return (null, -1);
        }

        /// <summary>
        /// Remove ONE costume at an already-validated index, WITHOUT Save(). Both the
        /// standalone remove-costume command and the batch remove-costumes command call
        /// this; the caller validates the index and Saves. Keeps Kirby's per-fighter
        /// cap-costume tables aligned (internal id 4), same as the GUI.
        /// </summary>
        internal static (string name, string fileName) RemoveCostumeCore(
            MexWorkspace workspace, MexFighter fighter, int fighterInternalId, int costumeIndex)
        {
            MexCostume removed = fighter.Costumes[costumeIndex];
            string name = removed.Name;
            string file = removed.File.FileName;

            fighter.Costumes.RemoveAt(costumeIndex);

            if (fighterInternalId == 4)
            {
                foreach (MexFighter f in workspace.Project.Fighters)
                {
                    if (f.HasKirbyCostumes && costumeIndex < f.KirbyCostumes.Count)
                        f.KirbyCostumes.RemoveAt(costumeIndex);
                }
            }

            return (name, file);
        }

        public static int Execute(string[] args)
        {
            if (args.Length < 4)
            {
                Console.Error.WriteLine("Usage: mexcli remove-costume <project.mexproj> <fighter_name_or_id> <costume_index>");
                return 1;
            }

            string projectPath = args[1];
            string fighterNameOrId = args[2];
            string costumeIndexStr = args[3];

            // Parse costume index
            if (!int.TryParse(costumeIndexStr, out int costumeIndex))
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Invalid costume index: {costumeIndexStr}"
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }

            // Open workspace
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

            // Validate costume index
            if (costumeIndex < 0 || costumeIndex >= fighter.Costumes.Count)
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Costume index out of range: {costumeIndex} (fighter has {fighter.Costumes.Count} costumes)"
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }

            // Remove costume
            try
            {
                var (removedCostumeName, removedCostumeFile) =
                    RemoveCostumeCore(workspace, fighter, fighterInternalId, costumeIndex);

                // Save the workspace
                workspace.Save(null);

                var output = new
                {
                    success = true,
                    fighter = fighter.Name,
                    fighterInternalId = fighterInternalId,
                    removedCostume = new
                    {
                        index = costumeIndex,
                        name = removedCostumeName,
                        fileName = removedCostumeFile
                    },
                    remainingCostumes = fighter.Costumes.Count
                };

                Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Failed to remove costume: {ex.Message}",
                    stackTrace = ex.StackTrace
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
