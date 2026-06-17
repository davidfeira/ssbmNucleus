using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// BATCH custom-stage import. Opens the workspace ONCE, adds many stages (each
    /// with an optional music playlist), then Saves ONCE.
    ///
    /// A single stage install fires add-stage + one add-music PER playlist track +
    /// set-stage-playlist, and every one of those runs the full
    /// <see cref="MexWorkspace.Save"/>. So N stages with ~T tracks each pay ~N*(2+T)
    /// full recompiles. This composes the SAME save-free cores those commands use
    /// (<see cref="AddStageCommand.AddStageCore"/>, <see cref="AddMusicCommand.AddMusicCore"/>)
    /// and Saves once.
    ///
    /// Usage: mexcli add-stages &lt;project.mexproj&gt; &lt;manifest.json&gt;
    ///   manifest.json: { "stages": [
    ///       { "zip": "a.zip", "playlist": [ { "hps": "m0.hps", "name": "Track",
    ///                                         "chance": 50 } ] },
    ///       { "zip": "b.zip" }
    ///   ] }
    /// </summary>
    public static class AddStagesCommand
    {
        private sealed class Track
        {
            public string? hps { get; set; }
            public string? name { get; set; }
            public int? chance { get; set; }
        }

        private sealed class StageEntry
        {
            public string? zip { get; set; }
            public List<Track>? playlist { get; set; }
        }

        private sealed class StagesManifest
        {
            public List<StageEntry>? stages { get; set; }
        }

        public static int Execute(string[] args)
        {
            if (args.Length < 3)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = "Usage: mexcli add-stages <project.mexproj> <manifest.json>"
                }));
                return 1;
            }

            string projectPath = args[1];
            string manifestPath = args[2];

            if (!File.Exists(manifestPath))
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = $"Manifest not found: {manifestPath}" }));
                return 1;
            }

            StagesManifest? manifest;
            try
            {
                manifest = JsonSerializer.Deserialize<StagesManifest>(
                    File.ReadAllText(manifestPath),
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = $"Bad manifest: {ex.Message}" }));
                return 1;
            }
            if (manifest?.stages == null || manifest.stages.Count == 0)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = "Empty manifest" }));
                return 1;
            }

            if (!MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out _) || workspace == null)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }));
                return 1;
            }

            var results = new List<object>();
            int totalAdded = 0, totalFailed = 0, totalTracks = 0;

            foreach (StageEntry entry in manifest.stages)
            {
                if (string.IsNullOrEmpty(entry.zip) || !File.Exists(entry.zip))
                {
                    totalFailed++;
                    results.Add(new { success = false, zip = entry.zip, error = "zip not found" });
                    continue;
                }

                var warnings = new List<string>();

                // 1) The stage itself (save-free core shared with add-stage).
                string? addErr = AddStageCommand.AddStageCore(workspace, entry.zip!,
                    out MexStage? stage, out int internalId, out int externalId);
                if (addErr != null || stage == null)
                {
                    totalFailed++;
                    results.Add(new { success = false, zip = entry.zip, error = addErr ?? "add-stage failed" });
                    continue;
                }

                // 2) Playlist: add each track's music (reuse dedupe via AddMusicCore),
                //    then point the stage at the resulting ids. add-stage resets the
                //    playlist on import, so an empty/absent playlist leaves the stage's
                //    vanilla default music (matches set-stage-playlist with no entries).
                int tracksPorted = 0;
                if (entry.playlist != null && entry.playlist.Count > 0)
                {
                    var pl = new ObservableCollection<MexPlaylistEntry>();
                    foreach (Track t in entry.playlist)
                    {
                        if (string.IsNullOrEmpty(t.hps) || !File.Exists(t.hps) || string.IsNullOrEmpty(t.name))
                        {
                            warnings.Add($"track '{t.name}' file missing, skipped");
                            continue;
                        }
                        try
                        {
                            int musicId = AddMusicCommand.AddMusicCore(workspace, t.hps!, t.name!, out _, out _);
                            pl.Add(new MexPlaylistEntry
                            {
                                MusicID = musicId,
                                ChanceToPlay = (byte)(t.chance ?? 50),
                            });
                            tracksPorted++;
                        }
                        catch (Exception ex)
                        {
                            warnings.Add($"track '{t.name}' failed: {ex.Message}");
                        }
                    }
                    if (pl.Count > 0)
                        stage.Playlist.Entries = pl;
                }

                totalAdded++;
                totalTracks += tracksPorted;
                results.Add(new
                {
                    success = true,
                    name = stage.Name,
                    internalId,
                    externalId,
                    tracksPorted,
                    warnings,
                });
            }

            // The single, amortized full recompile + write for the WHOLE batch.
            workspace.Save(null);

            Console.WriteLine(JsonSerializer.Serialize(new
            {
                success = true,
                totalAdded,
                totalFailed,
                totalTracks,
                stages = results,
            }, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
