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
                Console.Error.WriteLine("Usage: mexcli export <project.mexproj> <output.iso> [csp-compression]");
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

                // Apply compression to CSPs (force=true to ensure it processes even if already at target size)
                if (cspCompression < 1.0f)
                {
                    var compressionProgress = new
                    {
                        status = "progress",
                        percentage = 0,
                        message = $"Applying CSP compression to {targetWidth}x{targetHeight}..."
                    };
                    Console.WriteLine(JsonSerializer.Serialize(compressionProgress));
                    Console.Error.WriteLine($"[DEBUG] Calling ApplyCompression with force=true");

                    workspace.Project.CharacterSelect.ApplyCompression(workspace, force: true);

                    Console.Error.WriteLine($"[DEBUG] ApplyCompression completed, now saving workspace...");

                    // IMPORTANT: Save workspace to persist compressed CSPs to disk
                    workspace.Save(null);

                    Console.Error.WriteLine($"[DEBUG] Workspace saved with compressed CSPs");

                    var compressionComplete = new
                    {
                        status = "progress",
                        percentage = 10,
                        message = "CSP compression complete, workspace saved"
                    };
                    Console.WriteLine(JsonSerializer.Serialize(compressionComplete));
                }
                else
                {
                    Console.Error.WriteLine($"[DEBUG] Skipping compression (value is 1.0)");
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
