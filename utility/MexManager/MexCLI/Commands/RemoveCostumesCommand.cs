using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// BATCH costume removal. Opens the workspace ONCE, removes many costumes (across
    /// one or more fighters), then Saves ONCE -- amortizing the full recompile that
    /// remove-costume otherwise pays per costume.
    ///
    /// Indices are removed in DESCENDING order within each fighter so earlier removals
    /// never shift the indices of later ones (the GUI's batch remove sorts the same
    /// way), making the result identical to N sequential remove-costume calls.
    ///
    /// Usage: mexcli remove-costumes &lt;project.mexproj&gt; &lt;manifest.json&gt;
    ///   manifest.json: { "Fox": [5, 3], "Nana": [3] }
    ///   (keys are fighter name or internal-id; values are costume indices)
    /// </summary>
    public static class RemoveCostumesCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 3)
            {
                Console.Error.WriteLine("Usage: mexcli remove-costumes <project.mexproj> <manifest.json>");
                return 1;
            }
            string projectPath = args[1];
            string manifestPath = args[2];

            if (!File.Exists(manifestPath))
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = $"Manifest not found: {manifestPath}" }));
                return 1;
            }

            Dictionary<string, List<int>>? manifest;
            try
            {
                manifest = JsonSerializer.Deserialize<Dictionary<string, List<int>>>(File.ReadAllText(manifestPath));
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = $"Bad manifest: {ex.Message}" }));
                return 1;
            }
            if (manifest == null || manifest.Count == 0)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = "Empty manifest" }));
                return 1;
            }

            if (!MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out _) || workspace == null)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }));
                return 1;
            }

            var perFighter = new Dictionary<string, object>();
            int totalRemoved = 0, totalFailed = 0;

            foreach (var (key, indices) in manifest)
            {
                var (fighter, internalId) = RemoveCostumeCommand.FindFighter(workspace, key);
                if (fighter == null)
                {
                    perFighter[key] = new { error = "fighter not found", removed = 0 };
                    continue;
                }

                int removed = 0, failed = 0;
                // descending + distinct: later removals can't invalidate earlier indices
                foreach (int idx in indices.Distinct().OrderByDescending(i => i))
                {
                    if (idx < 0 || idx >= fighter.Costumes.Count)
                    {
                        failed++; totalFailed++;
                        continue;
                    }
                    RemoveCostumeCommand.RemoveCostumeCore(workspace, fighter, internalId, idx);
                    removed++; totalRemoved++;
                }
                perFighter[fighter.Name] = new { removed, failed, remainingCostumes = fighter.Costumes.Count };
            }

            // The single, amortized full recompile + write for the WHOLE batch.
            workspace.Save(null);

            Console.WriteLine(JsonSerializer.Serialize(new
            {
                success = true,
                totalRemoved,
                totalFailed,
                perFighter,
            }, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
