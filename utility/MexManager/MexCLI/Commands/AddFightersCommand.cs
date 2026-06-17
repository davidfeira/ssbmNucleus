using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// BATCH custom-character import. Opens the workspace ONCE, adds many fighters
    /// (each with optional victory theme + announcer name-call), then Saves ONCE.
    ///
    /// Why this is much faster than calling add-fighter/add-music/set-fighter-music/
    /// set-fighter-announcer per character: every one of those commands runs the full
    /// <see cref="MexWorkspace.Save"/> (MxDt, MnSlChr CSPs, codes.gct, sound banks ...)
    /// -- a typical install fires ~4 of them, so N chars pay ~4N full recompiles.
    /// This composes the SAME save-free cores those commands use and Saves once,
    /// collapsing ~4N recompiles to 1. Byte-identical to the sequential path
    /// (validated via backend/charadd_diff_build.py + multi-char in-game boot).
    ///
    /// Series creation stays a separate (pre-batch) add-series call in the backend
    /// -- it's rare (custom franchises only) and the fighter zips carry the resolved
    /// seriesID, so it never needs folding here.
    ///
    /// Usage: mexcli add-fighters &lt;project.mexproj&gt; &lt;manifest.json&gt;
    ///   manifest.json: { "fighters": [
    ///       { "zip": "a.zip", "victoryHps": "a.hps", "victoryName": "A Victory",
    ///         "announcerWav": "a.wav" },
    ///       { "zip": "b.zip" }            // no theme / announcer
    ///   ] }
    /// </summary>
    public static class AddFightersCommand
    {
        private sealed class BatchEntry
        {
            public string? zip { get; set; }
            public string? victoryHps { get; set; }
            public string? victoryName { get; set; }
            public string? announcerWav { get; set; }
            public int? announcerCallReuse { get; set; }
        }

        private sealed class BatchManifest
        {
            public List<BatchEntry>? fighters { get; set; }
        }

        public static int Execute(string[] args)
        {
            if (args.Length < 3)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = "Usage: mexcli add-fighters <project.mexproj> <manifest.json>"
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

            BatchManifest? manifest;
            try
            {
                manifest = JsonSerializer.Deserialize<BatchManifest>(
                    File.ReadAllText(manifestPath),
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = $"Bad manifest: {ex.Message}" }));
                return 1;
            }
            if (manifest?.fighters == null || manifest.fighters.Count == 0)
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
            var addedFighters = new List<MexFighter>();
            int totalAdded = 0, totalFailed = 0;

            foreach (BatchEntry entry in manifest.fighters)
            {
                if (string.IsNullOrEmpty(entry.zip) || !File.Exists(entry.zip))
                {
                    totalFailed++;
                    results.Add(new { success = false, zip = entry.zip, error = "zip not found" });
                    continue;
                }

                var warnings = new List<string>();

                // 1) The fighter itself (save-free core shared with add-fighter).
                string? addErr = AddFighterCommand.AddFighterCore(workspace, entry.zip!,
                    out MexFighter? fighter, out int internalId, out int externalId,
                    out int cssSfxId, out int packCodesMerged, out int packPatchesMerged);
                if (addErr != null || fighter == null)
                {
                    totalFailed++;
                    results.Add(new { success = false, zip = entry.zip, error = addErr ?? "add-fighter failed" });
                    continue;
                }

                // 2) Victory theme (add-music core -> point the fighter at it).
                int victoryThemeId = -1;
                if (!string.IsNullOrEmpty(entry.victoryHps))
                {
                    if (File.Exists(entry.victoryHps))
                    {
                        try
                        {
                            string vname = string.IsNullOrEmpty(entry.victoryName)
                                ? $"{fighter.Name} Victory" : entry.victoryName!;
                            victoryThemeId = AddMusicCommand.AddMusicCore(workspace, entry.victoryHps!, vname, out _, out _);
                            fighter.VictoryTheme = victoryThemeId;
                        }
                        catch (Exception ex)
                        {
                            warnings.Add($"victory theme failed: {ex.Message}");
                        }
                    }
                    else
                    {
                        warnings.Add($"victory hps not found: {entry.victoryHps}");
                    }
                }

                // 3) Announcer name-call: prefer the WAV port (the common case); fall
                //    back to reusing an existing announcerCall id if one was supplied.
                int announcerCall = -1;
                if (!string.IsNullOrEmpty(entry.announcerWav) && File.Exists(entry.announcerWav))
                {
                    string? annErr = SetFighterAnnouncerCommand.SetFighterAnnouncerCore(
                        workspace, fighter, entry.announcerWav!,
                        out announcerCall, out int annCss, out _, out _, out _);
                    if (annErr != null)
                    {
                        warnings.Add($"announcer port failed: {annErr}");
                        announcerCall = -1;
                    }
                    else
                    {
                        cssSfxId = annCss;
                    }
                }
                if (announcerCall < 0 && entry.announcerCallReuse is int reuse)
                {
                    fighter.AnnouncerCall = reuse;
                    cssSfxId = FighterAudioHelpers.ApplyAnnouncerCallToCssIcons(workspace, fighter);
                    announcerCall = reuse;
                }

                addedFighters.Add(fighter);
                totalAdded++;
                results.Add(new
                {
                    success = true,
                    name = fighter.Name,
                    internalId,
                    externalId,
                    costumeCount = fighter.Costumes.Count,
                    victoryThemeId,
                    announcerCall,
                    cssSfxId,
                    packCodesMerged,
                    packPatchesMerged,
                    warnings,
                });
            }

            // The single, amortized full recompile + write for the WHOLE batch.
            workspace.Save(null);

            // RetargetCloneSoundCalls reads each fighter's data file from disk, so it
            // must run AFTER the save (same as the standalone add-fighter command).
            foreach (MexFighter f in addedFighters)
                AddFighterCommand.RetargetCloneSoundCalls(workspace, f);

            Console.WriteLine(JsonSerializer.Serialize(new
            {
                success = true,
                totalAdded,
                totalFailed,
                fighters = results,
            }, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
