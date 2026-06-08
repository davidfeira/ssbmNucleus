using System.Text.Json;
using mexLib;

namespace MexCLI.Commands
{
    // Reads the GameCube disc-banner metadata (the title/creator/description shown
    // in Dolphin's game list and on the boot screen) plus a raw RGBA preview of the
    // 96x32 banner image. Companion to set-build. See MexBuildInfo / BannerEditor.
    //
    //   mexcli get-build <project.mexproj>
    public static class GetBuildCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli get-build <project.mexproj>");
                return 1;
            }

            string projectPath = args[1];

            bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);

            if (!success || workspace == null)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }

            try
            {
                var build = workspace.Project.Build;

                // Materialize the banner asset from opening.bnr if it hasn't been yet
                // (LoadBanner is a no-op when the asset already exists).
                if (build.BannerAsset.GetTexFile(workspace) == null)
                    build.LoadBanner(workspace);

                string bannerRgbaBase64 = "";
                int bannerWidth = 0;
                int bannerHeight = 0;

                var img = build.BannerAsset.GetTexFile(workspace);
                if (img != null)
                {
                    bannerWidth = img.Width;
                    bannerHeight = img.Height;
                    // GetRgba already yields display-order RGBA (matches BannerEditor's preview).
                    bannerRgbaBase64 = Convert.ToBase64String(img.GetRgba());
                }

                var output = new
                {
                    success = true,
                    shortName = build.ShortName,
                    longName = build.LongName,
                    shortMaker = build.ShortMaker,
                    longMaker = build.LongMaker,
                    description = build.Description,
                    bannerWidth,
                    bannerHeight,
                    bannerRgbaBase64,
                };

                Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = ex.Message, stackTrace = ex.StackTrace }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }
    }
}
