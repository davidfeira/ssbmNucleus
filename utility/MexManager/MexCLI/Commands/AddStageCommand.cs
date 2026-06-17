using System;
using System.IO;
using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class AddStageCommand
    {
        /// <summary>
        /// All workspace-mutating work of adding ONE stage, WITHOUT Save(). Both the
        /// standalone add-stage command and the batch add-stages command call this;
        /// the caller Saves. Returns an error message, or null on success.
        /// </summary>
        internal static string? AddStageCore(
            MexWorkspace workspace,
            string stageZipPath,
            out MexStage? stage,
            out int internalId,
            out int externalId)
        {
            stage = null;
            internalId = -1;
            externalId = -1;

            using (FileStream stream = new(stageZipPath, FileMode.Open))
            {
                var importError = MexStage.FromPackage(stream, workspace, out stage);
                if (importError != null || stage == null)
                    return importError?.Message ?? "Failed to parse stage package";
            }

            // Extract any extra related files from the ZIP that FromPackage didn't handle
            // (dynamically loaded files like GrAcDy.dat, GrAcNt.dat, etc.)
            {
                using FileStream stream2 = new(stageZipPath, FileMode.Open);
                using System.IO.Compression.ZipArchive zip = new(stream2);
                foreach (var entry in zip.Entries)
                {
                    if (!entry.Name.EndsWith(".dat", StringComparison.OrdinalIgnoreCase))
                        continue;
                    if (entry.Name.Equals("stage.json", StringComparison.OrdinalIgnoreCase))
                        continue;
                    string destPath = workspace.GetFilePath(entry.Name);
                    if (File.Exists(destPath))
                        continue;
                    string? destDir = Path.GetDirectoryName(destPath);
                    if (destDir != null && !Directory.Exists(destDir))
                        Directory.CreateDirectory(destDir);
                    using Stream entryStream = entry.Open();
                    using FileStream outFile = new(destPath, FileMode.CreateNew);
                    entryStream.CopyTo(outFile);
                }
            }

            internalId = workspace.Project.AddStage(stage);
            externalId = MexStageIDConverter.ToExternalID(internalId);

            // Auto-place the new stage's icon on a "Custom" SSS page. Page 0 is
            // the vanilla stage-select; custom stages live on pages 1+. A page can
            // only show as many icons as its layout template has positioned slots
            // (the default template = 30 vanilla placements), so once the current
            // custom page is full we spill onto a fresh page rather than stacking
            // the extra icons at the origin.
            MexStageSelect customPage = GetOrCreateCustomStagePage(workspace.Project);

            customPage.StageIcons.Add(new MexStageSelectIcon
            {
                StageID = externalId,
                Status = MexStageSelectIcon.StageIconStatus.Unlocked,
            });

            // Lay the page out from its template grid so the new icon (and any
            // others on the page) land in their slots instead of at (0, 0).
            customPage.Template.ApplyTemplate(customPage.StageIcons);

            return null;
        }

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
                        usage = "mexcli add-stage <project.mexproj> <stage.zip>"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string projectPath = args[1];
                string stageZipPath = args[2];

                if (!File.Exists(stageZipPath))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = $"Stage ZIP not found: {stageZipPath}"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);
                if (!success || workspace == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                string? coreError = AddStageCore(workspace, stageZipPath,
                    out MexStage? stage, out int internalId, out int externalId);
                if (coreError != null || stage == null)
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = coreError ?? "Failed to parse stage package"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = stage.Name,
                    internalId = internalId,
                    externalId = externalId,
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = $"Failed to add stage: {ex.Message}",
                    stackTrace = ex.StackTrace
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }

        /// <summary>
        /// Returns the custom SSS page that should receive the next stage icon,
        /// adding a new page when the current one is full. Page 0 is reserved for
        /// the vanilla stage-select; custom stages start on page 1 ("Custom") and
        /// overflow onto "Custom 2", "Custom 3", … as each page fills up. A page's
        /// capacity is the number of positioned slots in its layout template
        /// (30 for the default vanilla template).
        /// </summary>
        private static MexStageSelect GetOrCreateCustomStagePage(MexProject project)
        {
            // Reuse the most recent custom page while it still has a free slot. A
            // template with no placements is treated as unbounded so we never spin
            // up empty pages for it.
            if (project.StageSelects.Count >= 2)
            {
                MexStageSelect last = project.StageSelects[^1];
                int capacity = last.Template.IconPlacements.Count;
                if (capacity <= 0 || last.StageIcons.Count < capacity)
                    return last;
            }

            // Otherwise add a new page. The first custom page is "Custom"; later
            // ones are numbered to match their position after the vanilla page
            // ("Custom 2" is the 3rd page overall, "Custom 3" the 4th, and so on).
            int pageNumber = Math.Max(1, project.StageSelects.Count);
            MexStageSelect page = new()
            {
                Name = pageNumber == 1 ? "Custom" : $"Custom {pageNumber}",
            };
            project.StageSelects.Add(page);
            return page;
        }
    }
}
