using HSDRaw.GX;
using mexLib.Utilties;
using System.Collections.Concurrent;
using System.IO.Compression;
using System.Security.Cryptography;

namespace mexLib.AssetTypes
{
    public class MexTextureAsset
    {
        /// <summary>
        /// Optional process-wide decode cache used ONLY by the batch importer.
        /// When non-null, <see cref="SetFromImageFile"/> returns pre-decoded
        /// (png, tex) bytes for an image-content key instead of running the
        /// expensive ImageSharp quantization inline. The batch importer decodes
        /// every CSP/icon PNG in parallel up-front, fills this cache, then commits
        /// them serially -- so the FileManager path assignment stays byte-identical
        /// to N sequential imports while the heavy decode is parallelized.
        ///
        /// Null on the single-import / GUI path => zero overhead, original behavior.
        /// </summary>
        public static ConcurrentDictionary<string, (byte[] png, byte[] tex)>? DecodeCache;

        /// <summary>
        /// Stable content hash of raw image bytes, used as the decode-cache key.
        /// </summary>
        public static string HashImage(byte[] bytes)
        {
            return Convert.ToHexString(SHA256.HashData(bytes));
        }

        /// <summary>
        /// PURE decode (no workspace mutation, safe to call from any thread).
        /// Reproduces exactly the two FromPNG conversions inside
        /// <see cref="SetFromImageFile"/>: the native-size preview .png and the
        /// format-sized .tex. Returns the bytes the serial commit would have
        /// produced inline.
        /// </summary>
        public (byte[] png, byte[] tex) DecodeImageBytes(byte[] imageBytes)
        {
            using MemoryStream ms = new(imageBytes);

            ms.Position = 0;
            MexImage source_png = ImageConverter.FromPNG(ms, Format, TlutFormat);
            byte[] png = source_png.ToPNG();

            ms.Position = 0;
            MexImage tex = ImageConverter.FromPNG(ms,
                Width == -1 ? source_png.Width : Width,
                Height == -1 ? source_png.Height : Height,
                Format,
                TlutFormat);

            return (png, tex.ToByteArray());
        }

        /// <summary>
        /// Cache key incorporating the target format/dimensions so the same PNG
        /// decoded as (say) a CSP vs an icon never alias.
        /// </summary>
        public string DecodeKey(byte[] imageBytes)
        {
            return $"{Format}_{Width}_{Height}_{TlutFormat}_{HashImage(imageBytes)}";
        }
        public string? AssetFileName { get; set; }

        public string AssetPath { get; internal set; } = "";

        public int Width { get; internal set; }

        public int Height { get; internal set; }

        public GXTexFmt Format { get; internal set; }

        public GXTlutFmt TlutFormat { get; internal set; }

        /// <summary>
        /// 
        /// </summary>
        public MexTextureAsset()
        {
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="basePath"></param>
        /// <param name="subPath"></param>
        /// <returns></returns>
        private static string GetRelativePath(string basePath, string subPath)
        {
            Uri baseUri = new(basePath);
            Uri subUri = new(subPath);
            Uri relativeUri = baseUri.MakeRelativeUri(subUri);

            // Get the relative path string
            string relativePath = Uri.UnescapeDataString(relativeUri.ToString().Replace('/', Path.DirectorySeparatorChar));

            // Remove the file extension, if present
            string relativePathWithoutExtension = Path.Combine(Path.GetDirectoryName(relativePath) ?? string.Empty,
                                                               Path.GetFileNameWithoutExtension(relativePath));

            return relativePathWithoutExtension;
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="workspace"></param>
        /// <returns></returns>
        private string GetUniqueAssetPath(MexWorkspace workspace)
        {
            string assetPath = workspace.GetAssetPath("");
            string sourcePath = workspace.FileManager.GetUniqueFilePath(workspace.GetAssetPath(AssetPath) + ".png");
            return GetRelativePath(assetPath, sourcePath);
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="workspace"></param>
        /// <returns></returns>
        public string GetFullPath(MexWorkspace workspace)
        {
            AssetFileName ??= GetUniqueAssetPath(workspace);
            return workspace.GetAssetPath(AssetFileName);
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="workspace"></param>
        /// <param name="image"></param>
        public void SetFromMexImage(MexWorkspace workspace, MexImage image, bool updateSource = true)
        {
            string path = GetFullPath(workspace);

            // set png
            workspace.FileManager.Set(path + ".tex", image.ToByteArray());

            // compile and set tex
            if (updateSource)
                workspace.FileManager.Set(path + ".png", image.ToPNG());
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="workspace"></param>
        /// <param name="filePath"></param>
        public void SetFromImageFile(MexWorkspace workspace, Stream imageStream)
        {
            byte[] png, tex;

            ConcurrentDictionary<string, (byte[] png, byte[] tex)>? cache = DecodeCache;
            if (cache != null)
            {
                // Batch path: reuse the parallel-decoded result (or decode now on a
                // miss). Byte-identical to the inline path below -- same FromPNG on
                // the same bytes -- just memoized.
                imageStream.Position = 0;
                using MemoryStream raw = new();
                imageStream.CopyTo(raw);
                byte[] bytes = raw.ToArray();
                (png, tex) = cache.GetOrAdd(DecodeKey(bytes), _ => DecodeImageBytes(bytes));
            }
            else
            {
                // Single-import / GUI path: decode inline (original behavior).
                // i perform an encoding before saving to apply limitations of the texture format for more accurate preview
                imageStream.Position = 0;
                MexImage source_png = ImageConverter.FromPNG(imageStream, Format, TlutFormat);
                png = source_png.ToPNG();

                imageStream.Position = 0;
                MexImage texImg = ImageConverter.FromPNG(imageStream,
                    Width == -1 ? source_png.Width : Width,
                    Height == -1 ? source_png.Height : Height,
                    Format,
                    TlutFormat);
                tex = texImg.ToByteArray();
            }

            // path assignment + commit stay strictly serial (GetUniqueFilePath is
            // order-dependent); decode above is the only thing parallelized.
            string path = GetFullPath(workspace);
            workspace.FileManager.Set(path + ".png", png);
            workspace.FileManager.Set(path + ".tex", tex);
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="workspace"></param>
        /// <returns></returns>
        private Stream? GetSourceImageStream(MexWorkspace workspace)
        {
            if (AssetFileName == null)
                return null;

            string path = GetFullPath(workspace);

            return workspace.FileManager.GetStream(path + ".png");
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="workspace"></param>
        /// <returns></returns>
        public MexImage? GetSourceImage(MexWorkspace workspace)
        {
            using Stream? stream = GetSourceImageStream(workspace);

            if (stream == null)
                return null;

            MexImage tex = ImageConverter.FromPNG(stream, Format, TlutFormat);

            return tex;
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="workspace"></param>
        /// <returns></returns>
        public MexImage? GetTexFile(MexWorkspace workspace)
        {
            if (AssetFileName == null)
                return null;

            string texPath = GetFullPath(workspace) + ".tex";

            if (!workspace.FileManager.Exists(texPath))
                return null;

            byte[] stream = workspace.FileManager.Get(texPath);
            return MexImage.FromByteArray(stream);
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="workspace"></param>
        public void Delete(MexWorkspace workspace)
        {
            if (AssetFileName == null)
                return;

            string path = GetFullPath(workspace);

            workspace.FileManager.Remove(path + ".png");
            workspace.FileManager.Remove(path + ".tex");
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="csp_width"></param>
        /// <param name="csp_height"></param>
        /// <exception cref="NotImplementedException"></exception>
        internal MexImage? Resize(MexWorkspace workspace, int csp_width, int csp_height)
        {
            MexImage? source = GetSourceImage(workspace);

            if (source != null)
            {
                MexImage resized = ImageConverter.Resize(source, csp_width, csp_height);

                string path = GetFullPath(workspace);
                workspace.FileManager.Set(path + ".tex", resized.ToByteArray());

                return resized;
            }

            return null;
        }
        /// <summary>
        /// 
        /// </summary>
        /// <param name="workspace"></param>
        /// <param name="zip"></param>
        /// <param name="filename"></param>
        /// <returns></returns>
        public bool SetFromPackage(MexWorkspace workspace, ZipArchive zip, string filename)
        {
            ZipArchiveEntry? entry = zip.GetEntry(filename);

            if (entry == null)
                return false;

            AssetFileName = null;

            using MemoryStream img = new(entry.Extract());
            SetFromImageFile(workspace, img);

            return true;
        }
    }
}
