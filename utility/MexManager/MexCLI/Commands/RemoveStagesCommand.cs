using System.Text.Json;
using mexLib;

namespace MexCLI.Commands
{
    /// <summary>
    /// BATCH stage removal. Opens the workspace ONCE, removes many custom stages
    /// (by name), then Saves ONCE -- amortizing the full recompile that remove-stage
    /// otherwise pays per stage.
    ///
    /// Stages are resolved by name on each iteration (so the index re-resolution
    /// survives the re-indexing RemoveStage does), making the result identical to N
    /// sequential remove-stage calls when given the same name order.
    ///
    /// Usage: mexcli remove-stages &lt;project.mexproj&gt; &lt;manifest.json&gt;
    ///   manifest.json: { "stages": ["My Stage", "Another Stage"] }
    /// </summary>
    public static class RemoveStagesCommand
    {
        private sealed class StagesManifest
        {
            public List<string>? stages { get; set; }
        }

        public static int Execute(string[] args)
        {
            if (args.Length < 3)
            {
                Console.Error.WriteLine("Usage: mexcli remove-stages <project.mexproj> <manifest.json>");
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
            int totalRemoved = 0, totalFailed = 0;

            foreach (string stageName in manifest.stages)
            {
                int internalId = -1;
                for (int i = 0; i < workspace.Project.Stages.Count; i++)
                {
                    if (string.Equals(workspace.Project.Stages[i].Name, stageName, StringComparison.OrdinalIgnoreCase))
                    {
                        internalId = i;
                        break;
                    }
                }
                if (internalId < 0)
                {
                    totalFailed++;
                    results.Add(new { success = false, name = stageName, error = "not found" });
                    continue;
                }
                if (!workspace.Project.RemoveStage(workspace, internalId))
                {
                    totalFailed++;
                    results.Add(new { success = false, name = stageName, error = "only custom stages (index > 70) can be removed" });
                    continue;
                }
                totalRemoved++;
                results.Add(new { success = true, name = stageName, removedIndex = internalId });
            }

            // The single, amortized full recompile + write for the WHOLE batch.
            workspace.Save(null);

            Console.WriteLine(JsonSerializer.Serialize(new
            {
                success = true,
                totalRemoved,
                totalFailed,
                stages = results,
            }, new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
