using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class SetSssLayoutCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli set-sss-layout <project.mexproj> (reads JSON from stdin)");
                return 1;
            }

            string projectPath = args[1];

            bool success = MexWorkspace.TryOpenWorkspace(projectPath, out MexWorkspace? workspace, out string error, out bool isoMissing);

            if (!success || workspace == null)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = false,
                    error = error
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }

            try
            {
                string stdinJson = Console.In.ReadToEnd();
                using JsonDocument doc = JsonDocument.Parse(stdinJson);
                JsonElement root = doc.RootElement;

                if (!root.TryGetProperty("pages", out JsonElement pagesElement))
                {
                    Console.WriteLine(JsonSerializer.Serialize(new
                    {
                        success = false,
                        error = "Missing 'pages' property in input JSON"
                    }, new JsonSerializerOptions { WriteIndented = true }));
                    return 1;
                }

                workspace.Project.StageSelects.Clear();

                foreach (JsonElement pageEl in pagesElement.EnumerateArray())
                {
                    MexStageSelect page = new()
                    {
                        Name = pageEl.GetProperty("name").GetString() ?? "New Page"
                    };

                    if (pageEl.TryGetProperty("template", out JsonElement templateEl))
                    {
                        page.Template = new MexStageSelectTemplate();

                        if (templateEl.TryGetProperty("appearTime", out JsonElement at))
                            page.Template.AppearTime = at.GetSingle();
                        if (templateEl.TryGetProperty("appearSpacing", out JsonElement asp))
                            page.Template.AppearSpacing = asp.GetSingle();
                        if (templateEl.TryGetProperty("startX", out JsonElement sx))
                            page.Template.StartX = sx.GetSingle();

                        if (templateEl.TryGetProperty("iconPlacements", out JsonElement placementsEl))
                        {
                            page.Template.IconPlacements.Clear();
                            foreach (JsonElement pEl in placementsEl.EnumerateArray())
                            {
                                page.Template.IconPlacements.Add(new MexStageSelectTemplate.MexStageSelectIconPlacementTemplate
                                {
                                    Group = pEl.TryGetProperty("group", out JsonElement g) ? g.GetInt32() : 0,
                                    Width = pEl.TryGetProperty("width", out JsonElement w) ? w.GetSingle() : 3.1f,
                                    Height = pEl.TryGetProperty("height", out JsonElement h) ? h.GetSingle() : 2.7f,
                                    X = pEl.TryGetProperty("x", out JsonElement x) ? x.GetSingle() : 0,
                                    Y = pEl.TryGetProperty("y", out JsonElement y) ? y.GetSingle() : 0,
                                    Z = pEl.TryGetProperty("z", out JsonElement z) ? z.GetSingle() : 0,
                                    ScaleX = pEl.TryGetProperty("scaleX", out JsonElement scx) ? scx.GetSingle() : 1f,
                                    ScaleY = pEl.TryGetProperty("scaleY", out JsonElement scy) ? scy.GetSingle() : 1f,
                                });
                            }
                        }
                    }

                    if (pageEl.TryGetProperty("icons", out JsonElement iconsEl))
                    {
                        foreach (JsonElement iconEl in iconsEl.EnumerateArray())
                        {
                            MexStageSelectIcon icon = new();

                            if (iconEl.TryGetProperty("status", out JsonElement statusEl))
                                icon.Status = (MexStageSelectIcon.StageIconStatus)statusEl.GetInt32();

                            if (iconEl.TryGetProperty("stageID", out JsonElement sidEl))
                                icon.StageID = sidEl.GetInt32();

                            if (iconEl.TryGetProperty("x", out JsonElement ixEl))
                                icon.X = ixEl.GetSingle();
                            if (iconEl.TryGetProperty("y", out JsonElement iyEl))
                                icon.Y = iyEl.GetSingle();
                            if (iconEl.TryGetProperty("z", out JsonElement izEl))
                                icon.Z = izEl.GetSingle();

                            if (iconEl.TryGetProperty("scaleX", out JsonElement isxEl))
                                icon.ScaleX = isxEl.GetSingle();
                            if (iconEl.TryGetProperty("scaleY", out JsonElement isyEl))
                                icon.ScaleY = isyEl.GetSingle();

                            if (iconEl.TryGetProperty("group", out JsonElement grpEl))
                                icon.Group = grpEl.GetInt32();

                            if (iconEl.TryGetProperty("width", out JsonElement iwEl))
                                icon.Width = iwEl.GetSingle();
                            if (iconEl.TryGetProperty("height", out JsonElement ihEl))
                                icon.Height = ihEl.GetSingle();

                            if (iconEl.TryGetProperty("previewID", out JsonElement pidEl))
                                icon.PreviewID = (byte)pidEl.GetInt32();
                            if (iconEl.TryGetProperty("randomSelectID", out JsonElement rsidEl))
                                icon.RandomSelectID = (byte)rsidEl.GetInt32();

                            if (iconEl.TryGetProperty("icon", out JsonElement icoEl))
                            {
                                string? iconAssetName = icoEl.GetString();
                                if (iconAssetName != null)
                                    icon.IconAsset.AssetFileName = iconAssetName;
                            }

                            page.StageIcons.Add(icon);
                        }
                    }

                    workspace.Project.StageSelects.Add(page);
                }

                workspace.Save(null);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true
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
