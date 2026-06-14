using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI
{
    class Program
    {
        static int Main(string[] args)
        {
            try
            {
                if (args.Length == 0)
                {
                    PrintUsage();
                    return 1;
                }

                string command = args[0].ToLower();

                switch (command)
                {
                    case "create":
                        return Commands.CreateCommand.Execute(args);
                    case "import-iso":
                        return Commands.ImportIsoCommand.Execute(args);
                    case "open":
                        return Commands.OpenCommand.Execute(args);
                    case "list-fighters":
                        return Commands.ListFightersCommand.Execute(args);
                    case "func-probe":
                        return Commands.FuncProbeCommand.Execute(args);
                    case "copy-root":
                        return Commands.CopyRootCommand.Execute(args);
                    case "get-costumes":
                        return Commands.GetFighterCostumesCommand.Execute(args);
                    case "import-costume":
                        return Commands.ImportCostumeCommand.Execute(args);
                    case "remove-costume":
                        return Commands.RemoveCostumeCommand.Execute(args);
                    case "reorder-costume":
                        return Commands.ReorderCostumeCommand.Execute(args);
                    case "save":
                        return Commands.SaveCommand.Execute(args);
                    case "export":
                        return Commands.ExportCommand.Execute(args);
                    case "recompile-csps":
                        return Commands.RecompileCommand.Execute(args);
                    case "info":
                        return Commands.InfoCommand.Execute(args);
                    case "get-build":
                        return Commands.GetBuildCommand.Execute(args);
                    case "set-build":
                        return Commands.SetBuildCommand.Execute(args);
                    case "set-css-icon":
                        return Commands.SetCSSIconCommand.Execute(args);
                    case "add-code":
                        return Commands.AddCodeCommand.Execute(args);
                    case "get-sss-layout":
                        return Commands.GetSssLayoutCommand.Execute(args);
                    case "set-sss-layout":
                        return Commands.SetSssLayoutCommand.Execute(args);
                    case "get-css-layout":
                        return Commands.GetCssLayoutCommand.Execute(args);
                    case "set-css-layout":
                        return Commands.SetCssLayoutCommand.Execute(args);
                    case "export-fighter":
                        return Commands.ExportFighterCommand.Execute(args);
                    case "export-stage":
                        return Commands.ExportStageCommand.Execute(args);
                    case "add-fighter":
                        return Commands.AddFighterCommand.Execute(args);
                    case "add-series":
                        return Commands.AddSeriesCommand.Execute(args);
                    case "add-music":
                        return Commands.AddMusicCommand.Execute(args);
                    case "set-fighter-music":
                        return Commands.SetFighterMusicCommand.Execute(args);
                    case "set-fighter-announcer":
                        return Commands.SetFighterAnnouncerCommand.Execute(args);
                    case "set-fighter-announcer-id":
                        return Commands.SetFighterAnnouncerIdCommand.Execute(args);
                    case "dedup-sound-banks":
                        return Commands.DedupSoundBanksCommand.Execute(args);
                    case "set-stage-playlist":
                        return Commands.SetStagePlaylistCommand.Execute(args);
                    case "hps-to-wav":
                        return Commands.AudioCommands.HpsToWav(args);
                    case "ssm-info":
                        return Commands.AudioCommands.SsmInfo(args);
                    case "ssm-to-wav":
                        return Commands.AudioCommands.SsmToWav(args);
                    case "ssm-replace":
                        return Commands.AudioCommands.SsmReplace(args);
                    case "ssm-copy":
                        return Commands.AudioCommands.SsmCopy(args);
                    case "audio-to-hps":
                        return Commands.AudioCommands.AudioToHps(args);
                    case "sem-resolve":
                        return Commands.AudioCommands.SemResolve(args);
                    case "import-ssm":
                        return Commands.ImportSsmCommand.Execute(args);
                    case "remove-fighter":
                        return Commands.RemoveFighterCommand.Execute(args);
                    case "add-stage":
                        return Commands.AddStageCommand.Execute(args);
                    case "placeholder-bytes":
                        return Commands.PlaceholderBytesCommand.Execute(args);
                    case "remove-stage":
                        return Commands.RemoveStageCommand.Execute(args);
                    case "help":
                    case "--help":
                    case "-h":
                        PrintUsage();
                        return 0;
                    default:
                        Console.Error.WriteLine($"Unknown command: {command}");
                        PrintUsage();
                        return 1;
                }
            }
            catch (Exception ex)
            {
                var errorOutput = new
                {
                    success = false,
                    error = ex.Message,
                    stackTrace = ex.StackTrace
                };
                Console.Error.WriteLine(JsonSerializer.Serialize(errorOutput, new JsonSerializerOptions { WriteIndented = true }));
                return 1;
            }
        }

        static void PrintUsage()
        {
            Console.WriteLine("MexCLI - Command-line interface for MexManager");
            Console.WriteLine();
            Console.WriteLine("Usage:");
            Console.WriteLine("  mexcli <command> [options]");
            Console.WriteLine();
            Console.WriteLine("Commands:");
            Console.WriteLine("  create <iso> <dir> <name>                  - Create project from vanilla ISO");
            Console.WriteLine("  import-iso <iso> <dir> <name>              - Import ISO (vanilla or modded)");
            Console.WriteLine("  open <project.mexproj>                     - Open and validate project");
            Console.WriteLine("  list-fighters <project.mexproj>            - List all fighters");
            Console.WriteLine("  get-costumes <project> <fighter>           - Get costumes for fighter");
            Console.WriteLine("  import-costume <project> <fighter> <zip>   - Import costume ZIP");
            Console.WriteLine("  remove-costume <project> <fighter> <index> - Remove costume by index");
            Console.WriteLine("  reorder-costume <project> <fighter> <from> <to> - Reorder costume");
            Console.WriteLine("  save <project.mexproj>                     - Save project changes");
            Console.WriteLine("  export <project.mexproj> <output.iso>      - Export ISO");
            Console.WriteLine("  recompile-csps <project.mexproj>           - Recompile CSPs from PNG sources");
            Console.WriteLine("  info <project.mexproj>                     - Get project information");
            Console.WriteLine("  get-build <project.mexproj>                - Get disc banner title/creator + image preview");
            Console.WriteLine("  set-build <project.mexproj>                - Set disc banner fields (reads JSON from stdin)");
            Console.WriteLine("  add-code <project> <name> <hex_source>     - Add a Gecko code to project");
            Console.WriteLine("  get-sss-layout <project.mexproj>           - Get SSS layout data as JSON");
            Console.WriteLine("  set-sss-layout <project.mexproj>           - Set SSS layout (reads JSON from stdin)");
            Console.WriteLine("  help                                       - Show this help message");
        }
    }
}
