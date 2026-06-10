using System;
using System.IO;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// Adds a new franchise/series to a project (name + optional icon texture
    /// + optional emblem OBJ model). Outputs the new series index so callers
    /// can point fighters at it.
    /// </summary>
    public static class AddSeriesCommand
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
                        usage = "mexcli add-series <project.mexproj> <name> [icon.png] [emblem.obj]"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string name = args[2];
                string? iconPath = args.Length > 3 ? args[3] : null;
                string? objPath = args.Length > 4 ? args[4] : null;

                if (iconPath != null && !File.Exists(iconPath))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Icon not found: {iconPath}"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                MexSeries series = new()
                {
                    Name = name,
                };

                if (iconPath != null)
                {
                    using FileStream iconStream = new(iconPath, FileMode.Open, FileAccess.Read);
                    series.IconAsset.SetFromImageFile(workspace, iconStream);
                }

                if (objPath != null && File.Exists(objPath))
                {
                    series.ModelAsset.SetFromData(workspace, File.ReadAllBytes(objPath));
                }

                workspace.Project.Series.Add(series);
                int seriesId = workspace.Project.Series.Count - 1;

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    seriesId,
                    name,
                    hasIcon = iconPath != null,
                    hasModel = objPath != null && File.Exists(objPath),
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = ex.Message,
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
