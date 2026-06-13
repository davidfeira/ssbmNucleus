using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using MeleeMedia.Audio;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// Imports replacement sound bank(s) into a project through mexLib —
    /// the only safe path: a raw audio/us/*.ssm file drop would be
    /// regenerated from project data on the next workspace save, and the
    /// MxDt SSM table's recorded buffer size would go stale (the game
    /// allocates that many bytes to load the bank). Swapping the DSPs on
    /// the project's MexSoundGroup and saving recomputes both.
    ///
    /// The sound count must match the existing bank — SEM scripts address
    /// sounds by index within the bank.
    /// </summary>
    public static class ImportSsmCommand
    {
        public static int Execute(string[] args)
        {
            try
            {
                if (args.Length < 4 || (args.Length - 2) % 2 != 0)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = "Invalid arguments",
                        usage = "mexcli import-ssm <project.mexproj> <bankFileName> <new.ssm> [<bankFileName> <new.ssm> ...]"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                var updated = new List<object>();
                for (int a = 2; a + 1 < args.Length; a += 2)
                {
                    string bankName = args[a];
                    string ssmPath = args[a + 1];

                    if (!File.Exists(ssmPath))
                        return Fail($"File not found: {ssmPath}");

                    MexSoundGroup? group = workspace.Project.SoundGroups
                        .FirstOrDefault(g => string.Equals(g.FileName, bankName, StringComparison.OrdinalIgnoreCase));
                    if (group == null)
                        return Fail($"Sound bank not found in project: {bankName}");

                    SSM ssm = new();
                    using (FileStream fs = new(ssmPath, FileMode.Open, FileAccess.Read))
                        ssm.Open(Path.GetFileName(ssmPath), fs);

                    if (group.Sounds == null || group.Scripts == null)
                        return Fail($"Project sound data failed to load for bank: {bankName}");
                    if (ssm.Sounds.Length != group.Sounds.Count)
                        return Fail($"Sound count mismatch for {bankName}: bank has {group.Sounds.Count}, file has {ssm.Sounds.Length}");

                    // swap DSPs in place, preserving sound names/metadata
                    for (int i = 0; i < ssm.Sounds.Length; i++)
                        group.Sounds[i].DSP = ssm.Sounds[i];

                    updated.Add(new { bank = bankName, count = ssm.Sounds.Length });
                }

                // regenerates ssm/sem/smst and recompiles MxDt with fresh buffer sizes
                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    updated,
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

        private static int Fail(string error)
        {
            Console.WriteLine(JsonSerializer.Serialize(new { success = false, error },
                new JsonSerializerOptions { WriteIndented = true }));
            return 1;
        }
    }
}
