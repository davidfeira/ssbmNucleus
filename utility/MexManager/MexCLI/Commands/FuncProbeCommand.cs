using System.Text.Json;
using mexLib;
using mexLib.Types;

namespace MexCLI.Commands
{
    // Temporary diagnostic: dump fighter function pointers (esp. GetSwordTrail)
    // so we can read vanilla Marth/Roy's sword-trail function value.
    public static class FuncProbeCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli func-probe <project.mexproj>");
                return 1;
            }

            bool success = MexWorkspace.TryOpenWorkspace(args[1], out MexWorkspace? ws, out string error, out bool isoMissing);
            if (!success || ws == null)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { success = false, error }));
                return 1;
            }

            var rows = new List<object>();
            for (int id = 0; id < ws.Project.Fighters.Count; id++)
            {
                MexFighter f = ws.Project.Fighters[id];
                var fn = f.Functions;
                rows.Add(new
                {
                    internalId = id,
                    name = f.Name,
                    dataSymbol = f.Files?.FighterDataSymbol,
                    getSwordTrail = fn?.GetSwordTrail ?? 0,
                    getSwordTrailHex = "0x" + (fn?.GetSwordTrail ?? 0).ToString("X"),
                });
            }
            Console.WriteLine(JsonSerializer.Serialize(new { success = true, fighters = rows },
                new JsonSerializerOptions { WriteIndented = true }));
            return 0;
        }
    }
}
