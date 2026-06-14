using System;
using System.Linq;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// Points a fighter at an existing SEM announcer script.
    /// This is used when a vault fighter has no announcer WAV to port, but
    /// its original announcerCall already resolves in the target project.
    /// </summary>
    public static class SetFighterAnnouncerIdCommand
    {
        private static int Fail(string error)
        {
            Console.WriteLine(JsonSerializer.Serialize(new { success = false, error },
                new JsonSerializerOptions { WriteIndented = true }));
            return 1;
        }

        public static int Execute(string[] args)
        {
            try
            {
                if (args.Length < 4)
                    return Fail("Usage: mexcli set-fighter-announcer-id <project.mexproj> <fighter_name_or_id> <announcerCall>");

                string projectPath = args[1];
                string fighterNameOrId = args[2];
                if (!int.TryParse(args[3], out int announcerCall))
                    return Fail($"Invalid announcerCall: {args[3]}");

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                    return Fail(error);

                MexFighter? fighter = null;
                if (int.TryParse(fighterNameOrId, out int parsedId) &&
                    parsedId >= 0 && parsedId < workspace.Project.Fighters.Count)
                {
                    fighter = workspace.Project.Fighters[parsedId];
                }
                fighter ??= workspace.Project.Fighters.FirstOrDefault(
                    f => f.Name.Equals(fighterNameOrId, StringComparison.OrdinalIgnoreCase));
                if (fighter == null)
                    return Fail($"Fighter not found: {fighterNameOrId}");

                fighter.AnnouncerCall = announcerCall;
                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    fighter = fighter.Name,
                    announcerCall,
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                return Fail($"{ex.Message}\n{ex.StackTrace}");
            }
        }
    }
}
