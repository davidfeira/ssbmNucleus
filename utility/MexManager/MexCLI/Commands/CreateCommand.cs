using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using mexLib;
using mexLib.Types;
using mexLib.Utilties;

namespace MexCLI.Commands
{
    public static class CreateCommand
    {
        public static int Execute(string[] args)
        {
            try
            {
                // Parse arguments
                if (args.Length < 4)
                {
                    var usageOutput = new
                    {
                        success = false,
                        error = "Invalid arguments",
                        usage = "mexcli create <vanilla-iso-path> <output-directory> <project-name>"
                    };
                    Console.WriteLine(JsonSerializer.Serialize(usageOutput, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string isoPath = args[1];
                string outputDir = args[2];
                string projectName = args[3];

                // Validate ISO exists
                if (!File.Exists(isoPath))
                {
                    var errorOutput = new
                    {
                        success = false,
                        error = $"ISO file not found: {isoPath}"
                    };
                    Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // Create output directory if it doesn't exist
                if (!Directory.Exists(outputDir))
                {
                    Directory.CreateDirectory(outputDir);
                }

                string projectFilePath = Path.Combine(outputDir, "project.mexproj");

                // Check if project already exists
                if (File.Exists(projectFilePath))
                {
                    var errorOutput = new
                    {
                        success = false,
                        error = $"Project file already exists: {projectFilePath}"
                    };
                    Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // Load MEX codes from files next to mexcli.exe
                string mexCodePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "codes.gct");
                string mexAddCodePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "codes.ini");

                if (!File.Exists(mexCodePath))
                {
                    var errorOutput = new
                    {
                        success = false,
                        error = $"MEX codes file not found: {mexCodePath}",
                        hint = "Make sure codes.gct is in the same directory as mexcli.exe"
                    };
                    Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // Output progress
                var progressOutput = new
                {
                    status = "started",
                    message = "Creating MEX project from vanilla Melee ISO...",
                    isoPath = isoPath,
                    outputPath = projectFilePath,
                    projectName = projectName
                };
                Console.WriteLine(JsonSerializer.Serialize(progressOutput, new JsonSerializerOptions { WriteIndented = true }));

                // Load codes
                MexCode? mainCode = CodeLoader.FromGCT(File.ReadAllBytes(mexCodePath));
                IEnumerable<MexCode> defaultCodes = File.Exists(mexAddCodePath)
                    ? CodeLoader.FromINI(File.ReadAllBytes(mexAddCodePath))
                    : Enumerable.Empty<MexCode>();

                if (mainCode == null)
                {
                    var errorOutput = new
                    {
                        success = false,
                        error = "Failed to load MEX main code from codes.gct"
                    };
                    Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                var extractingOutput = new
                {
                    status = "extracting",
                    message = "Extracting ISO... (this may take 1-2 minutes)"
                };
                Console.WriteLine(JsonSerializer.Serialize(extractingOutput, new JsonSerializerOptions { WriteIndented = true }));

                // Create workspace from vanilla ISO
                // This will:
                // 1. Extract entire ISO to files/ folder
                // 2. Extract system files to sys/ folder
                // 3. Run MexInstaller to patch DOL and extract vanilla game data
                // 4. Initialize project structure
                MexWorkspace workspace = MexWorkspace.NewWorkspace(
                    projectFilePath,
                    isoPath,
                    mainCode,
                    defaultCodes
                );

                var installingOutput = new
                {
                    status = "installing",
                    message = "Installing MEX framework..."
                };
                Console.WriteLine(JsonSerializer.Serialize(installingOutput, new JsonSerializerOptions { WriteIndented = true }));

                // Set project name
                workspace.Project.Build.Name = projectName;

                // Save the workspace
                var savingOutput = new
                {
                    status = "saving",
                    message = "Saving project..."
                };
                Console.WriteLine(JsonSerializer.Serialize(savingOutput, new JsonSerializerOptions { WriteIndented = true }));

                workspace.Save(null);

                // Output success with project details
                var successOutput = new
                {
                    success = true,
                    status = "complete",
                    message = "MEX project created successfully",
                    projectPath = projectFilePath,
                    projectName = workspace.Project.Build.Name,
                    version = $"{workspace.Project.Build.MajorVersion}.{workspace.Project.Build.MinorVersion}.{workspace.Project.Build.PatchVersion}",
                    fighterCount = workspace.Project.Fighters.Count,
                    stageCount = workspace.Project.Stages.Count,
                    musicCount = workspace.Project.Music.Count
                };

                Console.WriteLine(JsonSerializer.Serialize(successOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Failed to create project: {ex.Message}",
                    stackTrace = ex.StackTrace
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
