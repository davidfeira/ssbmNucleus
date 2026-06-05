using HSDRaw.GX;
using mexLib;
using mexLib.Utilties;

namespace MexCLI.Commands
{
    // Dumps the exact CI8 image bytes + RGB5A3 TLUT bytes that the CSP texture
    // pipeline produces for a given PNG (the same ImageConverter.FromPNG path
    // MexTextureAsset.SetFromImageFile uses for CSPs: GXTexFmt.CI8 /
    // GXTlutFmt.RGB5A3). Used to validate the offline "compute Dolphin's texture
    // filename from the placeholder pixels" route against harvested ground truth.
    //
    //   mexcli placeholder-bytes <png>
    //
    // Prints one JSON line: { w, h, imgLen, palLen, usedMin, usedMax, img, pal }
    // where img/pal are uppercase hex of the in-.tex ImageData / PaletteData.
    public static class PlaceholderBytesCommand
    {
        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Error.WriteLine("usage: placeholder-bytes <png>");
                return 1;
            }
            string pngPath = args[1];
            using FileStream fs = File.OpenRead(pngPath);
            MexImage tex = ImageConverter.FromPNG(fs, 16, 16, GXTexFmt.CI8, GXTlutFmt.RGB5A3);

            byte[] img = tex.ImageData;
            byte[] pal = tex.PaletteData;

            int usedMin = 255, usedMax = 0;
            foreach (byte b in img)
            {
                if (b < usedMin) usedMin = b;
                if (b > usedMax) usedMax = b;
            }

            string imgHex = Convert.ToHexString(img);
            string palHex = Convert.ToHexString(pal);
            Console.WriteLine(
                $"{{\"w\":{tex.Width},\"h\":{tex.Height},\"imgLen\":{img.Length}," +
                $"\"palLen\":{pal.Length},\"usedMin\":{usedMin},\"usedMax\":{usedMax}," +
                $"\"img\":\"{imgHex}\",\"pal\":\"{palHex}\"}}");
            return 0;
        }
    }
}
