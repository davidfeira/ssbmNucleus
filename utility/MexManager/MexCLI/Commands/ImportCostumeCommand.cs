using System.Text;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class ImportCostumeCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 4)
            {
                Console.Error.WriteLine("Usage: mexcli import-costume <project.mexproj> <fighter_name_or_id> <costume.zip>");
                return 1;
            }

            string projectPath = args[1];
            string fighterNameOrId = args[2];
            string zipPath = args[3];

            // Validate ZIP file exists
            if (!File.Exists(zipPath))
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"ZIP file not found: {zipPath}"
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

            // Import costume from ZIP
            try
            {
                using FileStream zipStream = new FileStream(zipPath, FileMode.Open, FileAccess.Read);
                StringBuilder log = new StringBuilder();

                var costumes = MexCostume.FromZip(workspace, zipStream, log).ToList();

                if (costumes.Count == 0)
                {
                    var errorOutput = new
                    {
                        success = false,
                        error = "No costumes found in ZIP file",
                        log = log.ToString()
                    };
                    Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // Add costumes to fighter
                foreach (var costume in costumes)
                {
                    fighter.Costumes.Add(costume);
                }

                // Save the workspace
                workspace.Save(null);

                var output = new
                {
                    success = true,
                    fighter = fighter.Name,
                    fighterInternalId = fighterInternalId,
                    costumesImported = costumes.Count,
                    totalCostumes = fighter.Costumes.Count,
                    importLog = log.ToString()
                };

                Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Failed to import costume: {ex.Message}",
                    stackTrace = ex.StackTrace
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
