using System;
using System.IO;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class AddFighterCommand
    {
        public static int Execute(string[] args)
        {
            try
            {
                if (args.Length < 3)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = "Invalid arguments",
                        usage = "mexcli add-fighter <project.mexproj> <fighter.zip>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string fighterZipPath = args[2];

                if (!File.Exists(fighterZipPath))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Fighter ZIP not found: {fighterZipPath}"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // Import fighter from ZIP
                MexFighter? fighter;
                {
                    using FileStream stream = new(fighterZipPath, FileMode.Open);
                    var importError = MexFighter.FromPackage(workspace, stream, out fighter);

                    if (importError != null || fighter == null)
                    {
                        Console.WriteLine(JsonSerializer.Serialize(new
                        {
                            success = false,
                            error = importError?.Message ?? "Failed to parse fighter package"
                        }, new JsonSerializerOptions { WriteIndented = true }));
                        return 1;
                    }
                }

                // FromPackage doesn't extract fighter data files — do it manually
                {
                    using FileStream stream2 = new(fighterZipPath, FileMode.Open);
                    using System.IO.Compression.ZipArchive zip = new(stream2);
                    fighter.Files.FromPackage(workspace, zip);
                }

                // Internal index 34 is a broken slot in m-ex — insert a NONE placeholder
                // if this addition would land there, then add the real fighter after it.
                int insertIndex = workspace.Project.Fighters.Count - 6;
                if (insertIndex == 34)
                {
                    MexFighter noneFighter = new() { Name = "NONE" };
                    workspace.Project.AddNewFighter(noneFighter);
                }

                // Compute the external ID before adding (same as AddNewFighter does internally)
                int internalId = workspace.Project.Fighters.Count - 6;
                int externalId = MexFighterIDConverter.ToExternalID(internalId, workspace.Project.Fighters.Count);

                // Add fighter to project (shifts existing CSS icon references)
                workspace.Project.AddNewFighter(fighter);

                // Add a CSS icon for the new fighter (not for NONE)
                workspace.Project.CharacterSelect.FighterIcons.Add(new MexCharacterSelectIcon
                {
                    Fighter = externalId,
                });

                // Auto-layout the CSS grid
                workspace.Project.CharacterSelect.Template.Apply(
                    workspace.Project.CharacterSelect.FighterIcons);

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = fighter.Name,
                    internalId = internalId,
                    externalId = externalId,
                    costumeCount = fighter.Costumes.Count
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = $"Failed to add fighter: {ex.Message}",
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
