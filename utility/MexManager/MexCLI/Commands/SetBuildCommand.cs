using System.Text.Json;
using HSDRaw.GX;
using mexLib;
using mexLib.Utilties;

namespace MexCLI.Commands
{
    // Writes the GameCube disc-banner metadata (title/creator/description) and,
    // optionally, a new 96x32 banner image. Reads a JSON object from stdin:
    //
    //   { "shortName", "longName", "shortMaker", "longMaker", "description",
    //     "bannerPngBase64" }   // all keys optional
    //
    // workspace.Save() runs MexProject.Save -> MexBuildInfo.SaveBanner, which writes
    // files/opening.bnr. Modeled on SetCssLayoutCommand; image path mirrors
    // BannerEditor's ImportButton (decode PNG -> exact 96x32 RGB5A3).
    //
    //   mexcli set-build <project.mexproj>   (reads JSON from stdin)
    public static class SetBuildCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli set-build <project.mexproj> (reads JSON from stdin)");
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
                string stdinJson = Console.In.ReadToEnd();
                using JsonDocument doc = JsonDocument.Parse(stdinJson);
                JsonElement root = doc.RootElement;

                var build = workspace.Project.Build;

                // Apply text fields. Truncate to the GameCube banner field limits
                // (mirrors BannerEditor.BannerProxy StringLength attributes; the -1
                // leaves room for the null terminator in the fixed-size bnr fields).
                if (root.TryGetProperty("shortName", out JsonElement v))
                    build.ShortName = Truncate(v.GetString(), 31);
                if (root.TryGetProperty("longName", out v))
                    build.LongName = Truncate(v.GetString(), 63);
                if (root.TryGetProperty("shortMaker", out v))
                    build.ShortMaker = Truncate(v.GetString(), 31);
                if (root.TryGetProperty("longMaker", out v))
                    build.LongMaker = Truncate(v.GetString(), 63);
                if (root.TryGetProperty("description", out v))
                    build.Description = Truncate(v.GetString(), 127);

                // Optional banner image (base64 PNG, any size -> exact 96x32).
                if (root.TryGetProperty("bannerPngBase64", out JsonElement pngEl)
                    && pngEl.ValueKind == JsonValueKind.String
                    && !string.IsNullOrEmpty(pngEl.GetString()))
                {
                    byte[] pngBytes = Convert.FromBase64String(pngEl.GetString()!);
                    using MemoryStream ms = new(pngBytes);
                    MexImage img = ImageConverter.FromPNG(ms, GXTexFmt.RGB5A3, GXTlutFmt.IA8);
                    img = ImageConverter.Resize(img, 96, 32);
                    build.BannerAsset.SetFromMexImage(workspace, img);
                }
                else if (build.BannerAsset.GetTexFile(workspace) == null)
                {
                    // No new image and the existing banner asset is missing: reload it
                    // from opening.bnr so SaveBanner has pixels to write (SaveBanner
                    // early-returns on a null asset, which would drop the text edits).
                    build.BannerAsset.AssetFileName = null;
                    build.LoadBanner(workspace);
                }

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new { success = true }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error = ex.Message, stackTrace = ex.StackTrace }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }

        private static string Truncate(string? s, int maxLength)
        {
            s ??= "";
            return s.Length <= maxLength ? s : s[..maxLength];
        }
    }
}
