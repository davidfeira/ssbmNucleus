using System.ComponentModel;
using System.Text.Json;
using mexLib;

namespace MexCLI.Commands
{
    public static class ExportCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 3)
            {
                Console.Error.WriteLine("Usage: mexcli export <project.mexproj> <output.iso> [csp-compression] [use-color-smash] [skip-compression]");
                return 1;
            }

            string projectPath = args[1];
            string outputPath = args[2];

            // Optional CSP compression parameter (default 1.0 = no compression)
            float cspCompression = 1.0f;
            if (args.Length >= 4 && float.TryParse(args[3], out float parsedCompression))
            {
                // Validate range: 0.1 to 1.0
                if (parsedCompression >= 0.1f && parsedCompression <= 1.0f)
                {
                    cspCompression = parsedCompression;
                }
            }

            // Optional use-color-smash parameter (default false)
            bool useColorSmash = false;
            if (args.Length >= 5)
            {
                if (bool.TryParse(args[4], out bool parsedColorSmash))
                {
                    useColorSmash = parsedColorSmash;
                }
                else
                {
                    Console.Error.WriteLine("Invalid use-color-smash value. Expected true or false.");
                    return 1;
                }
            }

            // Optional skip-compression parameter (default false)
            // When true, skips ApplyCompression entirely (useful for texture pack mode with fixed-size placeholders)
            bool skipCompression = false;
            if (args.Length >= 6 && bool.TryParse(args[5], out bool parsedSkipCompression))
            {
                skipCompression = parsedSkipCompression;
            }

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

            // Set CSP compression before export
            workspace.Project.CharacterSelect.CSPCompression = cspCompression;
            workspace.Project.CharacterSelect.UseColorSmash = useColorSmash;

            // Calculate target dimensions
            int targetWidth = (int)(136 * cspCompression);
            int targetHeight = (int)(188 * cspCompression);

            try
            {
                // Output start message with compression details
                var startOutput = new
                {
                    status = "started",
                    message = $"Beginning ISO export with CSP compression: {cspCompression:F2}x ({targetWidth}x{targetHeight})"
                };
                Console.WriteLine(JsonSerializer.Serialize(startOutput));
                Console.Error.WriteLine($"[DEBUG] CSP Compression Level: {cspCompression}");
                Console.Error.WriteLine($"[DEBUG] Target CSP Dimensions: {targetWidth}x{targetHeight}");
                Console.Error.WriteLine($"[DEBUG] Will apply compression: {cspCompression < 1.0f}");
                Console.Error.WriteLine($"[DEBUG] UseColorSmash setting: {useColorSmash}");
                Console.Error.WriteLine($"[DEBUG] SkipCompression setting: {skipCompression}");

                // Apply compression to CSPs (force=true to ensure it processes even if already at target size)
                // OR if color smash is disabled (need to assign unique ColorSmashGroups)
                // Skip entirely if skipCompression is true (texture pack mode with fixed-size placeholders)
                if (!skipCompression && (cspCompression < 1.0f || !useColorSmash))
                {
                    var compressionStart = new
                    {
                        status = "progress",
                        percentage = 0,
                        message = $"Preparing CSP compression ({targetWidth}x{targetHeight})..."
                    };
                    Console.WriteLine(JsonSerializer.Serialize(compressionStart));
                    Console.Error.WriteLine($"[DEBUG] Calling ApplyCompression with force=true");

                    var compressionProcessing = new
                    {
                        status = "progress",
                        percentage = 5,
                        message = $"Processing character portraits (this may take 30-60 seconds)..."
                    };
                    Console.WriteLine(JsonSerializer.Serialize(compressionProcessing));

                    workspace.Project.CharacterSelect.ApplyCompression(workspace, force: true);

                    Console.Error.WriteLine($"[DEBUG] ApplyCompression completed, now saving workspace...");

                    var savingWorkspace = new
                    {
                        status = "progress",
                        percentage = 8,
                        message = "Saving compressed textures to disk..."
                    };
                    Console.WriteLine(JsonSerializer.Serialize(savingWorkspace));

                    // IMPORTANT: Save workspace to persist compressed CSPs to disk
                    workspace.Save(null);

                    Console.Error.WriteLine($"[DEBUG] Workspace saved with compressed CSPs");

                    var compressionComplete = new
                    {
                        status = "progress",
                        percentage = 10,
                        message = "CSP compression complete"
                    };
                    Console.WriteLine(JsonSerializer.Serialize(compressionComplete));
                }
                else
                {
                    Console.Error.WriteLine($"[DEBUG] Skipping compression (skipCompression={skipCompression})");

                    // Even when skipping compression, we MUST call Save() to rebuild MnSlChr.usd
                    // with the current CSP textures. Without this, the ISO will have stale data.
                    Console.Error.WriteLine($"[DEBUG] Calling Save() to rebuild asset files...");
                    workspace.Save(null);
                    Console.Error.WriteLine($"[DEBUG] Save() complete");
                }

                // Set up progress reporting
                int lastProgress = -1;
                ProgressChangedEventHandler progressHandler = (sender, e) =>
                {
                    int currentProgress = e.ProgressPercentage;
                    if (currentProgress != lastProgress)
                    {
                        var progressOutput = new
                        {
                            status = "progress",
                            percentage = currentProgress,
                            message = e.UserState?.ToString() ?? ""
                        };
                        Console.WriteLine(JsonSerializer.Serialize(progressOutput));
                        lastProgress = currentProgress;
                    }
                };

                // Export ISO
                workspace.ExportISO(outputPath, progressHandler);

                // Output completion message
                var completeOutput = new
                {
                    success = true,
                    status = "completed",
                    message = "ISO exported successfully",
                    outputPath = outputPath
                };
                Console.WriteLine(JsonSerializer.Serialize(completeOutput));
                return 0;
            }
            catch (Exception ex)
            {
                var errorOutput = new
                {
                    success = false,
                    status = "error",
                    error = $"Failed to export ISO: {ex.Message}",
                    stackTrace = ex.StackTrace
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
