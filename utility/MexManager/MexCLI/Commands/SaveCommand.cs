using System.Text.Json;
using mexLib;

namespace MexCLI.Commands
{
    public static class SaveCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli save <project.mexproj>");
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
                workspace.Save(null);

                var output = new
                {
                    success = true,
                    message = "Project saved successfully"
                };

                Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Failed to save project: {ex.Message}",
                    stackTrace = ex.StackTrace
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
