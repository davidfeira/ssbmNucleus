using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class SetCSSIconCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 4)
            {
                Console.Error.WriteLine("Usage: mexcli set-css-icon <project.mexproj> <fighter_name_or_id> <icon.png>");
                return 1;
            }

            string projectPath = args[1];
            string fighterNameOrId = args[2];
            string iconPath = args[3];

            if (!File.Exists(iconPath))
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = $"Icon file not found: {iconPath}" }));
                return 1;
            }

            MexWorkspace? workspace;
            string error;
            bool isoMissing;

            bool success = MexWorkspace.TryOpenWorkspace(projectPath, out workspace, out error, out isoMissing);

            if (!success || workspace == null)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }));
                return 1;
            }

            // Find fighter by name or internal ID
            MexFighter? fighter = null;
            int fighterInternalId = -1;

            if (int.TryParse(fighterNameOrId, out int parsedId))
            {
                if (parsedId >= 0 && parsedId < workspace.Project.Fighters.Count)
                {
                    fighter = workspace.Project.Fighters[parsedId];
                    fighterInternalId = parsedId;
                }
            }

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
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = $"Fighter not found: {fighterNameOrId}" }));
                return 1;
            }

            try
            {
                using FileStream stream = File.OpenRead(iconPath);
                fighter.Assets.CSSIconAsset.SetFromImageFile(workspace, stream);

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    fighter = fighter.Name,
                    internalId = fighterInternalId,
                    message = $"Set CSS icon for {fighter.Name}"
                }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = ex.Message }));
                return 1;
            }
        }
    }
}
