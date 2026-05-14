using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class GetCssLayoutCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli get-css-layout <project.mexproj>");
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
                MexCharacterSelect css = workspace.Project.CharacterSelect;
                var icons = new List<object>();

                for (int i = 0; i < css.FighterIcons.Count; i++)
                {
                    MexCharacterSelectIcon icon = css.FighterIcons[i];
                    string? iconPath = null;
                    string? fighterName = null;

                    try
                    {
                        int internalId = MexFighterIDConverter.ToInternalID(icon.Fighter, workspace.Project.Fighters.Count);
                        if (internalId >= 0 && internalId < workspace.Project.Fighters.Count)
                        {
                            MexFighter fighter = workspace.Project.Fighters[internalId];
                            fighterName = fighter.Name;
                            string basePath = fighter.Assets.CSSIconAsset.GetFullPath(workspace);
                            string pngPath = basePath + ".png";
                            if (File.Exists(pngPath))
                                iconPath = pngPath;
                        }
                    }
                    catch { }

                    icons.Add(new
                    {
                        index = i,
                        x = icon.X,
                        y = icon.Y,
                        z = icon.Z,
                        scaleX = icon.ScaleX,
                        scaleY = icon.ScaleY,
                        fighter = icon.Fighter,
                        fighterName = fighterName,
                        sfxID = icon.SFXID,
                        collisionOffsetX = icon.CollisionOffsetX,
                        collisionOffsetY = icon.CollisionOffsetY,
                        collisionSizeX = icon.CollisionSizeX,
                        collisionSizeY = icon.CollisionSizeY,
                        iconPath = iconPath?.Replace('\\', '/')
                    });
                }

                var template = new
                {
                    iconsPerRow = css.Template.IconsPerRow,
                    scaleX = css.Template.ScaleX,
                    scaleY = css.Template.ScaleY,
                    centerX = css.Template.CenterX,
                    centerY = css.Template.CenterY,
                    iconWidth = css.Template.IconWidth,
                    iconHeight = css.Template.IconHeight,
                    iconSideDropX = css.Template.IconSideDropX,
                    iconSideDropY = css.Template.IconSideDropY,
                    iconSideDropZ = css.Template.IconSideDropZ
                };

                var fighters = new List<object>();
                for (int i = 0; i < workspace.Project.Fighters.Count; i++)
                {
                    MexFighter fighter = workspace.Project.Fighters[i];
                    int externalId = MexFighterIDConverter.ToExternalID(i, workspace.Project.Fighters.Count);
                    fighters.Add(new
                    {
                        externalId,
                        internalId = i,
                        name = fighter.Name
                    });
                }

                var output = new
                {
                    success = true,
                    characterSelectHandScale = css.CharacterSelectHandScale,
                    cspCompression = css.CSPCompression,
                    useColorSmash = css.UseColorSmash,
                    template,
                    icons,
                    fighters
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
