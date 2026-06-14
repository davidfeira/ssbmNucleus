using System;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// Repoints fighters that sit on a DUPLICATE sound bank (an "X_001.ssm"
    /// copy the importer created from an existing "X.ssm") onto the original
    /// bank instead.
    ///
    /// Cloned/reskin fighters (Blood Falcon=Captain, Blastoise=Bowser, Lyn=
    /// emblem, ...) get a fresh copy of the donor's bank on import, but the
    /// clone's sound wiring doesn't resolve to that copy in-game, so they end
    /// up silent. The copy is byte-for-byte the same samples as the original
    /// vanilla bank, so pointing the fighter back at the original (which loads
    /// fine) restores the donor's voice. The orphaned copies are left in place
    /// (harmless — there is no hard bank-count limit).
    /// </summary>
    public static class DedupSoundBanksCommand
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
                if (args.Length < 2)
                    return Fail("Usage: mexcli dedup-sound-banks <project.mexproj>");

                string projectPath = args[1];
                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                    return Fail(error);

                var groups = workspace.Project.SoundGroups;
                var dupRe = new Regex(@"^(.*)_(\d+)\.ssm$", RegexOptions.IgnoreCase);

                int FindByName(string name) =>
                    groups.ToList().FindIndex(g => string.Equals(g.FileName, name, StringComparison.OrdinalIgnoreCase));

                var repoints = new System.Collections.Generic.List<object>();
                foreach (MexFighter f in workspace.Project.Fighters)
                {
                    int sb = f.SoundBank;
                    if (sb < 0 || sb >= groups.Count) continue;

                    Match m = dupRe.Match(groups[sb].FileName);
                    if (!m.Success) continue;

                    string baseName = m.Groups[1].Value + ".ssm";
                    int baseIdx = FindByName(baseName);
                    if (baseIdx >= 0 && baseIdx != sb)
                    {
                        repoints.Add(new
                        {
                            fighter = f.Name,
                            from = sb,
                            fromFile = groups[sb].FileName,
                            to = baseIdx,
                            toFile = baseName,
                        });
                        f.SoundBank = baseIdx;
                    }
                }

                // Make every fighter actually LOAD its own sound bank. Cloned
                // fighters inherit the donor's SSM load bitfield (e.g. CDI King,
                // a Ganondorf clone, loads ganon.ssm), so a fighter with its
                // own bank never gets that bank into audio memory → silent.
                // Vanilla fighters load exactly their own bank; match that.
                var bitfixes = new System.Collections.Generic.List<object>();
                foreach (MexFighter f in workspace.Project.Fighters)
                {
                    int sb = f.SoundBank;
                    if (sb < 0 || sb >= 64 || sb >= groups.Count) continue;
                    if (string.Equals(groups[sb].FileName, "null.ssm", StringComparison.OrdinalIgnoreCase))
                        continue; // intentionally silent (wireframes, sandbag, ...)

                    bool ownSet = sb < 32
                        ? (f.SSMBitfield2 & (1u << sb)) != 0
                        : (f.SSMBitfield1 & (1u << (sb - 32))) != 0;
                    if (ownSet) continue;

                    uint oldB1 = f.SSMBitfield1, oldB2 = f.SSMBitfield2;
                    if (sb < 32) { f.SSMBitfield1 = 0; f.SSMBitfield2 = 1u << sb; }
                    else { f.SSMBitfield1 = 1u << (sb - 32); f.SSMBitfield2 = 0; }

                    bitfixes.Add(new
                    {
                        fighter = f.Name,
                        soundBank = sb,
                        bankFile = groups[sb].FileName,
                        oldBitfield = $"{oldB1:X8}{oldB2:X8}",
                        newBitfield = $"{f.SSMBitfield1:X8}{f.SSMBitfield2:X8}",
                    });
                }

                if (repoints.Count > 0 || bitfixes.Count > 0)
                    workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    repointed = repoints.Count,
                    repoints,
                    bitfieldFixed = bitfixes.Count,
                    bitfixes,
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
