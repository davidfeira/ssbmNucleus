using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// Recompiles CSP assets from their source PNG files.
    /// This regenerates .tex files without resizing, useful when PNG files have been
    /// modified externally (e.g., replaced with texture pack placeholders).
    /// </summary>
    public static class RecompileCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli recompile-csps <project.mexproj>");
                return 1;
            }

            string projectPath = args[1];

            MexWorkspace? workspace;
            string error;
            bool isoMissing;

            bool success = MexWorkspace.TryOpenWorkspace(projectPath, out workspace, out error, out isoMissing);

            if (!success || workspace == null)
            {
                var errorOutput = new
                {
                    success = false,
                    error = error
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }

            try
            {
                int recompiledCount = 0;
                int errorCount = 0;

                // Iterate through all fighters and their costumes
                foreach (MexFighter fighter in workspace.Project.Fighters)
                {
                    foreach (MexCostume costume in fighter.Costumes)
                    {
                        try
                        {
                            // Recompile CSP from source PNG using the asset's own method
                            if (costume.CSPAsset.AssetFileName != null)
                            {
                                var sourceImage = costume.CSPAsset.GetSourceImage(workspace);
                                if (sourceImage != null)
                                {
                                    costume.CSPAsset.SetFromMexImage(workspace, sourceImage, false);
                                    recompiledCount++;
                                }
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.Error.WriteLine($"[ERROR] Failed to recompile {fighter.Name}/{costume.Name}: {ex.Message}");
                            errorCount++;
                        }
                    }
                }

                // Save the file manager changes to disk
                workspace.FileManager.Save();

                var output = new
                {
                    success = true,
                    recompiledCount = recompiledCount,
                    errorCount = errorCount,
                    message = $"Recompiled {recompiledCount} CSP textures"
                };
                Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Failed to recompile CSPs: {ex.Message}",
                    stackTrace = ex.StackTrace
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
