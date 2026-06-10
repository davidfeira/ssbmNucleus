using System;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// Points a fighter's victory theme at a project music index
    /// (MexFighter.FromPackage resets it to 10 on import, so installs
    /// that port a custom theme set it explicitly afterwards).
    /// </summary>
    public static class SetFighterMusicCommand
    {
        public static int Execute(string[] args)
        {
            try
            {
                if (args.Length < 4)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = "Invalid arguments",
                        usage = "mexcli set-fighter-music <project.mexproj> <fighter_name_or_id> <victoryThemeId>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string fighterNameOrId = args[2];
                if (!int.TryParse(args[3], out int victoryThemeId))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Invalid victoryThemeId: {args[3]}"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                if (victoryThemeId < 0 || victoryThemeId >= workspace.Project.Music.Count)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"victoryThemeId {victoryThemeId} out of range (project has {workspace.Project.Music.Count} tracks)"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                MexFighter? fighter = null;
                if (int.TryParse(fighterNameOrId, out int parsedId) &&
                    parsedId >= 0 && parsedId < workspace.Project.Fighters.Count)
                {
                    fighter = workspace.Project.Fighters[parsedId];
                }
                if (fighter == null)
                {
                    foreach (MexFighter f in workspace.Project.Fighters)
                    {
                        if (f.Name.Equals(fighterNameOrId, StringComparison.OrdinalIgnoreCase))
                        {
                            fighter = f;
                            break;
                        }
                    }
                }
                if (fighter == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Fighter not found: {fighterNameOrId}"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                fighter.VictoryTheme = victoryThemeId;
                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    fighter = fighter.Name,
                    victoryTheme = victoryThemeId,
                    musicName = workspace.Project.Music[victoryThemeId].Name,
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = ex.Message,
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
