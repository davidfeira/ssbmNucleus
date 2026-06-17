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
        /// <summary>
        /// Add (or reuse) a music track WITHOUT Save(). Returns the music index.
        /// Existence/content checks go through FileManager so a track added by an
        /// earlier (not-yet-saved) entry in a batch is correctly deduped — for the
        /// standalone command the FileManager has no pending writes, so this is
        /// identical to the old File.* path. Caller must verify hpsPath exists.
        /// </summary>
        internal static int AddMusicCore(MexWorkspace workspace, string hpsPath, string name,
                                         out bool existed, out string? fileName)
        {
            existed = false;
            fileName = null;

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
                if (!workspace.FileManager.Exists(existingPath))
                    continue;
                byte[] existingBytes = workspace.FileManager.Get(existingPath);
                if (existingBytes.Length != newBytes.Length)
                    continue;
                if (!existingBytes.AsSpan().SequenceEqual(newBytes))
                    continue;

                existed = true;
                fileName = workspace.Project.Music[i].FileName;
                return i;
            }

            // unique file name within audio/
            string fn = Path.GetFileName(hpsPath);
            string targetPath = workspace.GetFilePath($"audio/{fn}");
            if (workspace.FileManager.Exists(targetPath))
            {
                string stem = Path.GetFileNameWithoutExtension(fn);
                string ext = Path.GetExtension(fn);
                int n = 2;
                while (workspace.FileManager.Exists(workspace.GetFilePath($"audio/{stem}_{n}{ext}")))
                    n++;
                fn = $"{stem}_{n}{ext}";
                targetPath = workspace.GetFilePath($"audio/{fn}");
            }

            workspace.FileManager.Set(targetPath, newBytes);
            workspace.Project.AddMusic(new MexMusic { Name = name, FileName = fn });
            fileName = fn;
            return workspace.Project.Music.Count - 1;
        }

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

                int musicId = AddMusicCore(workspace, hpsPath, name, out bool existed, out string? fileName);

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    musicId,
                    name = existed ? workspace.Project.Music[musicId].Name : name,
                    fileName,
                    existed,
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
