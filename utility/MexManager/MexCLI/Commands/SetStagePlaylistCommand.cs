using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// Replaces a stage's music playlist. Entries are read from stdin as
    /// JSON: [{"musicId": 98, "chance": 50}, ...]. MexStage.FromPackage
    /// resets the playlist on import, so installs that port stage music
    /// set it explicitly afterwards.
    /// </summary>
    public static class SetStagePlaylistCommand
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
                        usage = "mexcli set-stage-playlist <project.mexproj> <stage_name_or_id>  (entries JSON on stdin)"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string stageNameOrId = args[2];

                string stdin = Console.In.ReadToEnd();
                JsonDocument doc = JsonDocument.Parse(stdin);
                var entries = new ObservableCollection<MexPlaylistEntry>();
                foreach (JsonElement e in doc.RootElement.EnumerateArray())
                {
                    entries.Add(new MexPlaylistEntry
                    {
                        MusicID = e.GetProperty("musicId").GetInt32(),
                        ChanceToPlay = (byte)(e.TryGetProperty("chance", out JsonElement c) ? c.GetInt32() : 50),
                    });
                }
                // an empty array is valid: it clears the playlist, restoring
                // the stage's vanilla default music (vanilla stage playlists
                // are empty in project data)

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // find the stage — by index, or LAST name match (a freshly
                // added stage sits at the end)
                MexStage? stage = null;
                if (int.TryParse(stageNameOrId, out int parsedId) &&
                    parsedId >= 0 && parsedId < workspace.Project.Stages.Count)
                {
                    stage = workspace.Project.Stages[parsedId];
                }
                if (stage == null)
                {
                    stage = workspace.Project.Stages
                        .LastOrDefault(s => s.Name.Equals(stageNameOrId, StringComparison.OrdinalIgnoreCase));
                }
                if (stage == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Stage not found: {stageNameOrId}"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                int maxMusic = workspace.Project.Music.Count;
                if (entries.Any(e => e.MusicID < 0 || e.MusicID >= maxMusic))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"musicId out of range (project has {maxMusic} tracks)"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                stage.Playlist.Entries = entries;
                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    stage = stage.Name,
                    entries = entries.Select(e => new { musicId = e.MusicID, chance = (int)e.ChanceToPlay }).ToArray(),
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
