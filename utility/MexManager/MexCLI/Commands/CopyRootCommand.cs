using System.Text.Json;
using HSDRaw;

namespace MexCLI.Commands
{
    // Graft a named root (e.g. Ploaj's "ftFunction" sword-trail code) from one
    // DAT into another. HSDRaw handles relocations/strings/shared structs.
    public static class CopyRootCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 5)
            {
                Console.Error.WriteLine("Usage: mexcli copy-root <src.dat> <rootName> <dst.dat> <out.dat>");
                return 1;
            }
            string srcPath = args[1], rootName = args[2], dstPath = args[3], outPath = args[4];
            if (!File.Exists(srcPath)) { Console.WriteLine(Err($"src not found: {srcPath}")); return 1; }
            if (!File.Exists(dstPath)) { Console.WriteLine(Err($"dst not found: {dstPath}")); return 1; }

            try
            {
                HSDRawFile src = new(srcPath);
                HSDRawFile dst = new(dstPath);

                HSDRootNode? node = src[rootName];
                if (node == null || node.Data == null)
                {
                    Console.WriteLine(Err($"root \"{rootName}\" not found in {srcPath}. roots: "
                        + string.Join(",", src.Roots.ConvertAll(r => r.Name))));
                    return 1;
                }

                // remove any existing root of the same name on dst, then add
                dst.Roots.RemoveAll(r => r.Name == rootName);
                dst.Roots.Add(new HSDRootNode { Name = rootName, Data = node.Data });
                dst.Save(outPath);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    copied = rootName,
                    dstRoots = dst.Roots.ConvertAll(r => r.Name),
                    outPath
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(Err($"copy-root failed: {ex.Message}"));
                return 1;
            }
        }

        private static string Err(string m) =>
            JsonSerializer.Serialize(new { success = false, error = m });
    }
}
