using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class GetSssLayoutCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli get-sss-layout <project.mexproj>");
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
                var pages = new List<object>();

                foreach (MexStageSelect page in workspace.Project.StageSelects)
                {
                    var icons = new List<object>();

                    for (int i = 0; i < page.StageIcons.Count; i++)
                    {
                        MexStageSelectIcon icon = page.StageIcons[i];

                        string? iconPath = null;
                        string? stageName = null;

                        try
                        {
                            switch (icon.Status)
                            {
                                case MexStageSelectIcon.StageIconStatus.Unlocked:
                                {
                                    int internalId = MexStageIDConverter.ToInternalID(icon.StageID);
                                    if (internalId >= 0 && internalId < workspace.Project.Stages.Count)
                                    {
                                        MexStage stage = workspace.Project.Stages[internalId];
                                        stageName = stage.Name;
                                        string basePath = stage.Assets.IconAsset.GetFullPath(workspace);
                                        string pngPath = basePath + ".png";
                                        if (File.Exists(pngPath))
                                            iconPath = pngPath;
                                    }
                                    break;
                                }
                                case MexStageSelectIcon.StageIconStatus.Random:
                                {
                                    string basePath = workspace.Project.ReservedAssets.SSSNullAsset.GetFullPath(workspace);
                                    string pngPath = basePath + ".png";
                                    if (File.Exists(pngPath))
                                        iconPath = pngPath;
                                    stageName = "Random";
                                    break;
                                }
                                case MexStageSelectIcon.StageIconStatus.Locked:
                                {
                                    string basePath = workspace.Project.ReservedAssets.SSSLockedNullAsset.GetFullPath(workspace);
                                    string pngPath = basePath + ".png";
                                    if (File.Exists(pngPath))
                                        iconPath = pngPath;
                                    stageName = "Locked";
                                    break;
                                }
                                case MexStageSelectIcon.StageIconStatus.Decoration:
                                {
                                    if (icon.IconAsset.AssetFileName != null)
                                    {
                                        string basePath = icon.IconAsset.GetFullPath(workspace);
                                        string pngPath = basePath + ".png";
                                        if (File.Exists(pngPath))
                                            iconPath = pngPath;
                                    }
                                    stageName = "Decoration";
                                    break;
                                }
                                case MexStageSelectIcon.StageIconStatus.Hidden:
                                    stageName = "Hidden";
                                    break;
                            }
                        }
                        catch
                        {
                            // icon image resolution failed, leave iconPath null
                        }

                        icons.Add(new
                        {
                            index = i,
                            x = icon.X,
                            y = icon.Y,
                            z = icon.Z,
                            scaleX = icon.ScaleX,
                            scaleY = icon.ScaleY,
                            status = (int)icon.Status,
                            stageID = icon.StageID,
                            stageName = stageName,
                            group = icon.Group,
                            width = icon.Width,
                            height = icon.Height,
                            previewID = (int)icon.PreviewID,
                            randomSelectID = (int)icon.RandomSelectID,
                            iconPath = iconPath?.Replace('\\', '/'),
                            icon = icon.Icon
                        });
                    }

                    var placements = new List<object>();
                    foreach (var p in page.Template.IconPlacements)
                    {
                        placements.Add(new
                        {
                            group = p.Group,
                            width = p.Width,
                            height = p.Height,
                            x = p.X,
                            y = p.Y,
                            z = p.Z,
                            scaleX = p.ScaleX,
                            scaleY = p.ScaleY
                        });
                    }

                    pages.Add(new
                    {
                        name = page.Name,
                        template = new
                        {
                            appearTime = page.Template.AppearTime,
                            appearSpacing = page.Template.AppearSpacing,
                            startX = page.Template.StartX,
                            iconPlacements = placements
                        },
                        icons = icons
                    });
                }

                var stages = new List<object>();
                for (int i = 0; i < workspace.Project.Stages.Count; i++)
                {
                    MexStage stage = workspace.Project.Stages[i];
                    int externalId = MexStageIDConverter.ToExternalID(i);
                    stages.Add(new
                    {
                        externalId = externalId,
                        internalId = i,
                        name = stage.Name
                    });
                }

                var output = new
                {
                    success = true,
                    pages = pages,
                    stages = stages
                };

                Console.WriteLine(JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
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
