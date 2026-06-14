using System;
using System.Linq;
using System.Text.Json;
using MeleeMedia.Audio;
using mexLib;
using mexLib.Types;
using mexLib.Utilties;

namespace MexCLI.Commands
{
    /// <summary>
    /// Ports a fighter's announcer name-call into the project's narrator
    /// name bank (nr_name) and points the fighter at it.
    ///
    /// Custom characters carry an announcerCall index (51xxxx) that only
    /// resolves against the narrator bank of the build they were ripped
    /// from. A different project's nr_name bank usually has fewer entries,
    /// so that index dangles and the game falls back to "se_call_bonus"
    /// (the fighter gets announced as a bonus character). This command
    /// appends the supplied name-call WAV as a brand-new narrator entry so
    /// the call always resolves, regardless of index ranges.
    /// </summary>
    public static class SetFighterAnnouncerCommand
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
                    return Fail("Usage: mexcli set-fighter-announcer <project.mexproj> <fighter_name_or_id> <announcer.wav>");

                string projectPath = args[1];
                string fighterNameOrId = args[2];
                string wavPath = args[3];

                if (!System.IO.File.Exists(wavPath))
                    return Fail($"WAV not found: {wavPath}");

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                    return Fail(error);

                // resolve fighter (id or name)
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

                // locate the narrator name bank (nr_name.ssm) by index
                int narratorIndex = -1;
                for (int i = 0; i < workspace.Project.SoundGroups.Count; i++)
                {
                    MexSoundGroup g = workspace.Project.SoundGroups[i];
                    if (string.Equals(g.FileName, "nr_name.ssm", StringComparison.OrdinalIgnoreCase))
                    {
                        narratorIndex = i;
                        break;
                    }
                }
                // fall back to the NarratorName-typed bank with the most entries
                if (narratorIndex == -1)
                {
                    int best = -1;
                    for (int i = 0; i < workspace.Project.SoundGroups.Count; i++)
                    {
                        MexSoundGroup g = workspace.Project.SoundGroups[i];
                        if (g.Group == MexSoundGroupGroup.NarratorName && g.Sounds.Count > best)
                        {
                            best = g.Sounds.Count;
                            narratorIndex = i;
                        }
                    }
                }
                if (narratorIndex == -1)
                    return Fail("Narrator name bank (nr_name) not found in project");

                MexSoundGroup narrator = workspace.Project.SoundGroups[narratorIndex];
                if (narrator.Scripts == null)
                    return Fail("Narrator bank has no script table loaded");

                // decode the name-call audio
                DSP dsp = new();
                if (!dsp.FromFile(wavPath))
                    return Fail($"Unsupported or unreadable audio file: {wavPath}");

                // append the sound to the bank; its bank-relative index is the
                // old count (scripts store sound ids relative to the bank)
                int soundRelIndex = narrator.Sounds.Count;
                narrator.Sounds.Add(new MexSound
                {
                    Name = $"nr_{fighter.Name}",
                    DSP = dsp,
                });

                // build the play script by cloning an existing narrator script
                // (preserves the priority/volume envelope) and retargeting its
                // sound command; fall back to a minimal script if none exist
                SemScript? template = narrator.Scripts.FirstOrDefault(s => s.GetFirstSoundID() >= 0);
                SemScript script;
                if (template != null)
                {
                    script = new SemScript(template);
                    foreach (SemCommand c in script.Script)
                        if (c.SemCode == SemCode.Sound)
                            c.Value = soundRelIndex;
                }
                else
                {
                    script = new SemScript();
                    script.Script.Add(new SemCommand(SemCode.Sound, soundRelIndex));
                    script.Script.Add(new SemCommand(SemCode.End, 0));
                }
                script.Name = $"nr_{fighter.Name}";

                int scriptIndex = narrator.Scripts.Count;
                narrator.Scripts.Add(script);

                int announcerCall = narratorIndex * 10000 + scriptIndex;
                fighter.AnnouncerCall = announcerCall;

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    fighter = fighter.Name,
                    announcerCall,
                    narratorBank = narratorIndex,
                    scriptIndex,
                    soundIndex = soundRelIndex,
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
