using System.IO.Compression;

namespace mexLib.Utilties
{
    public static class ZipExtensions
    {
        /// <summary>
        /// Reads file from zip and adds it to workspace and returns the new filename if it changed
        /// </summary>
        /// <param name="zip"></param>
        /// <param name="workspace"></param>
        /// <param name="filename"></param>
        /// <returns></returns>
        public static string TryReadFile(this ZipArchive zip, MexWorkspace workspace, string filename)
        {
            ZipArchiveEntry? e = zip.GetEntry(filename);
            if (e == null)
                return "";

            byte[] data = e.Extract();
            string path = workspace.GetFilePath(filename);

            // If a file with this exact name already exists and is byte-identical,
            // reuse it instead of writing a renamed _00n copy. Identical effect
            // files (Ef*Data.dat shared across clones) would otherwise each consume
            // one of m-ex's 64 effect slots and overflow the table — late fighters
            // then crash in-game with "does not have effBehaviorTable".
            if (workspace.FileManager.Exists(path))
            {
                byte[] existing = workspace.FileManager.Get(path);
                if (existing.Length == data.Length && existing.AsSpan().SequenceEqual(data))
                    return Path.GetFileName(path);
            }

            path = workspace.FileManager.GetUniqueFilePath(path);
            workspace.FileManager.Set(path, data);

            return Path.GetFileName(path);
        }
    }
}
