using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    public static class SetCssLayoutCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli set-css-layout <project.mexproj> (reads JSON from stdin)");
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

                MexCharacterSelect css = workspace.Project.CharacterSelect;

                if (root.TryGetProperty("template", out JsonElement tmpl))
                {
                    if (tmpl.TryGetProperty("iconsPerRow", out JsonElement v)) css.Template.IconsPerRow = v.GetInt32();
                    if (tmpl.TryGetProperty("scaleX", out v)) css.Template.ScaleX = v.GetSingle();
                    if (tmpl.TryGetProperty("scaleY", out v)) css.Template.ScaleY = v.GetSingle();
                    if (tmpl.TryGetProperty("centerX", out v)) css.Template.CenterX = v.GetSingle();
                    if (tmpl.TryGetProperty("centerY", out v)) css.Template.CenterY = v.GetSingle();
                    if (tmpl.TryGetProperty("iconWidth", out v)) css.Template.IconWidth = v.GetSingle();
                    if (tmpl.TryGetProperty("iconHeight", out v)) css.Template.IconHeight = v.GetSingle();
                    if (tmpl.TryGetProperty("iconSideDropX", out v)) css.Template.IconSideDropX = v.GetSingle();
                    if (tmpl.TryGetProperty("iconSideDropY", out v)) css.Template.IconSideDropY = v.GetSingle();
                    if (tmpl.TryGetProperty("iconSideDropZ", out v)) css.Template.IconSideDropZ = v.GetSingle();
                }

                if (root.TryGetProperty("icons", out JsonElement iconsEl))
                {
                    css.FighterIcons.Clear();
                    foreach (JsonElement el in iconsEl.EnumerateArray())
                    {
                        MexCharacterSelectIcon icon = new();
                        if (el.TryGetProperty("x", out JsonElement v)) icon.X = v.GetSingle();
                        if (el.TryGetProperty("y", out v)) icon.Y = v.GetSingle();
                        if (el.TryGetProperty("z", out v)) icon.Z = v.GetSingle();
                        if (el.TryGetProperty("scaleX", out v)) icon.ScaleX = v.GetSingle();
                        if (el.TryGetProperty("scaleY", out v)) icon.ScaleY = v.GetSingle();
                        if (el.TryGetProperty("fighter", out v)) icon.Fighter = v.GetInt32();
                        if (el.TryGetProperty("sfxID", out v)) icon.SFXID = v.GetInt32();
                        if (el.TryGetProperty("collisionOffsetX", out v)) icon.CollisionOffsetX = v.GetSingle();
                        if (el.TryGetProperty("collisionOffsetY", out v)) icon.CollisionOffsetY = v.GetSingle();
                        if (el.TryGetProperty("collisionSizeX", out v)) icon.CollisionSizeX = v.GetSingle();
                        if (el.TryGetProperty("collisionSizeY", out v)) icon.CollisionSizeY = v.GetSingle();
                        css.FighterIcons.Add(icon);
                    }
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
    }
}
