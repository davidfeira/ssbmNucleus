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
    public static class ImportIsoCommand
    {
        public static int Execute(string[] args)
        {
            try
            {
                if (args.Length < 4)
                {
                    var usageOutput = new
                    {
                        success = false,
                        error = "Invalid arguments",
                        usage = "mexcli import-iso <iso-path> <output-directory> <project-name>"
                    };
                    Console.WriteLine(JsonSerializer.Serialize(usageOutput, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string isoPath = args[1];
                string outputDir = args[2];
                string projectName = args[3];

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

                if (!Directory.Exists(outputDir))
                    Directory.CreateDirectory(outputDir);

                string projectFilePath = Path.Combine(outputDir, "project.mexproj");

                // Load MEX codes
                string mexCodePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "codes.gct");
                string mexAddCodePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "codes.ini");

                if (!File.Exists(mexCodePath))
                    throw new Exception($"MEX codes file not found: {mexCodePath}");

                MexCode? mainCode = CodeLoader.FromGCT(File.ReadAllBytes(mexCodePath));
                IEnumerable<MexCode> defaultCodes = File.Exists(mexAddCodePath)
                    ? CodeLoader.FromINI(File.ReadAllBytes(mexAddCodePath))
                    : Enumerable.Empty<MexCode>();

                if (mainCode == null)
                    throw new Exception("Failed to load MEX main code from codes.gct");

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    status = "extracting",
                    message = "Extracting ISO... (this may take 1-2 minutes)"
                }, new JsonSerializerOptions { WriteIndented = true }));

                MexWorkspace workspace;
                bool isModded = false;

                try
                {
                    // Try vanilla path first (NewWorkspace extracts + patches DOL)
                    workspace = MexWorkspace.NewWorkspace(
                        projectFilePath, isoPath, mainCode, defaultCodes);
                }
                catch (Exception vanillaEx)
                {
                    // NewWorkspace extracts the ISO before patching, so files/ and sys/
                    // should exist even after a DOL patch failure.
                    string mxdtPath = Path.Combine(outputDir, "files", "MxDt.dat");
                    if (!File.Exists(mxdtPath))
                        throw new Exception(
                            $"ISO is not vanilla (DOL patch failed) and has no MxDt.dat (not a m-ex build). " +
                            $"Original error: {vanillaEx.Message}");

                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        status = "importing",
                        message = "Detected m-ex build, importing from MxDt..."
                    }, new JsonSerializerOptions { WriteIndented = true }));

                    isModded = true;

                    // Clean up partial project file from failed attempt
                    if (File.Exists(projectFilePath))
                        File.Delete(projectFilePath);

                    // Use the MxDt import path — files are already extracted in-place
                    workspace = MexWorkspace.CreateFromMexFileSystem(
                        projectFilePath, outputDir, mainCode, defaultCodes);
                }

                workspace.Project.Build.Name = projectName;
                workspace.Save(null);

                var successOutput = new
                {
                    success = true,
                    status = "complete",
                    isModded = isModded,
                    projectPath = projectFilePath,
                    projectName = workspace.Project.Build.Name,
                    fighterCount = workspace.Project.Fighters.Count,
                    stageCount = workspace.Project.Stages.Count,
                };

                Console.WriteLine(JsonSerializer.Serialize(successOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                var errorOutput = new
                {
                    success = false,
                    error = $"Failed to import ISO: {ex.Message}",
                    stackTrace = ex.StackTrace
                };
                Console.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
