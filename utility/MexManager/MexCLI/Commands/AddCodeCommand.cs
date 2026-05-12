using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class AddCodeCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 4)
            {
                Console.Error.WriteLine("Usage: mexcli add-code <project.mexproj> <name> <hex_source>");
                Console.Error.WriteLine("  hex_source example: \"04263384 48000010\"");
                return 1;
            }

            string projectPath = args[1];
            string codeName = args[2];
            string hexSource = args[3];

            MexWorkspace? workspace;
            string error;
            bool isoMissing;

            bool success = MexWorkspace.TryOpenWorkspace(projectPath, out workspace, out error, out isoMissing);

            if (!success || workspace == null)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }));
                return 1;
            }

            // Check if a code with the same name already exists
            foreach (var existing in workspace.Project.Codes)
            {
                if (existing.Name.Equals(codeName, StringComparison.OrdinalIgnoreCase))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = true,
                        skipped = true,
                        message = $"Code '{codeName}' already exists, skipping"
                    }));
                    return 0;
                }
            }

            try
            {
                var code = new MexCode
                {
                    Name = codeName,
                    Source = hexSource,
                    Enabled = true
                };

                if (code.CompileError != null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Code compilation error: {code.CompileError}"
                    }));
                    return 1;
                }

                workspace.Project.Codes.Add(code);
                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = codeName,
                    message = $"Added code '{codeName}' to project"
                }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = ex.Message }));
                return 1;
            }
        }
    }
}
