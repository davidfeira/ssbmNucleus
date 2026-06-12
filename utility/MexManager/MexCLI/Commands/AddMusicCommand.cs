using System;
using System.IO;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    /// <summary>
    /// Adds a music track (.hps) to a project, reusing an existing entry
    /// with the same name when present. Outputs the music index so callers
    /// can point fighters (victory theme) at it.
    /// </summary>
    public static class AddMusicCommand
    {
        public static int Execute(string[] args)
        {
            try
            {
                if (args.Length < 4)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = "Invalid arguments",
                        usage = "mexcli add-music <project.mexproj> <file.hps> <name>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string hpsPath = args[2];
                string name = args[3];

                if (!File.Exists(hpsPath))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"HPS not found: {hpsPath}"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                // reuse an existing track only when BOTH the name and the
                // audio content match — different songs that happen to share
                // a name (e.g. two stages with a "Battle Theme") must not
                // collide into one entry
                byte[] newBytes = File.ReadAllBytes(hpsPath);
                for (int i = 0; i < workspace.Project.Music.Count; i++)
                {
                    if (!string.Equals(workspace.Project.Music[i].Name?.Trim(), name.Trim(), StringComparison.OrdinalIgnoreCase))
                        continue;

                    string existingPath = workspace.GetFilePath("audio/" + workspace.Project.Music[i].FileName);
                    if (!File.Exists(existingPath))
                        continue;
                    FileInfo info = new(existingPath);
                    if (info.Length != newBytes.Length)
                        continue;
                    if (!File.ReadAllBytes(existingPath).AsSpan().SequenceEqual(newBytes))
                        continue;

                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = true,
                        musicId = i,
                        name = workspace.Project.Music[i].Name,
                        existed = true,
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 0;
                }

                // unique file name within audio/
                string fileName = Path.GetFileName(hpsPath);
                string targetPath = workspace.GetFilePath($"audio/{fileName}");
                if (File.Exists(targetPath))
                {
                    string stem = Path.GetFileNameWithoutExtension(fileName);
                    string ext = Path.GetExtension(fileName);
                    int n = 2;
                    while (File.Exists(workspace.GetFilePath($"audio/{stem}_{n}{ext}")))
                        n++;
                    fileName = $"{stem}_{n}{ext}";
                    targetPath = workspace.GetFilePath($"audio/{fileName}");
                }

                workspace.FileManager.Set(targetPath, File.ReadAllBytes(hpsPath));
                workspace.Project.AddMusic(new MexMusic { Name = name, FileName = fileName });
                int musicId = workspace.Project.Music.Count - 1;

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    musicId,
                    name,
                    fileName,
                    existed = false,
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
