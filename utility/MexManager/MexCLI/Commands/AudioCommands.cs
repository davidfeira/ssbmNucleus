using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using MeleeMedia.Audio;

namespace MexCLI.Commands
{
    /// <summary>
    /// File-based audio helpers (no project needed): decode Melee audio
    /// formats to WAV for previewing vault content.
    /// </summary>
    public static class AudioCommands
    {
        private static int Fail(string error)
        {
            Console.WriteLine(JsonSerializer.Serialize(new { success = false, error },
                new JsonSerializerOptions { WriteIndented = true }));
            return 1;
        }

        /// <summary>
        /// hps-to-wav &lt;in.hps&gt; &lt;out.wav&gt;
        /// </summary>
        public static int HpsToWav(string[] args)
        {
            if (args.Length < 3)
                return Fail("Usage: mexcli hps-to-wav <in.hps> <out.wav>");

            string inPath = args[1];
            string outPath = args[2];
            if (!File.Exists(inPath))
                return Fail($"File not found: {inPath}");

            try
            {
                DSP dsp = HPS.ToDSP(File.ReadAllBytes(inPath));
                File.WriteAllBytes(outPath, dsp.ToWAVE().ToFile());
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    durationMs = dsp.TotalMilliseconds,
                    frequency = dsp.Frequency,
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                return Fail($"HPS decode failed: {ex.Message}");
            }
        }

        /// <summary>
        /// ssm-info &lt;in.ssm&gt;
        /// </summary>
        public static int SsmInfo(string[] args)
        {
            if (args.Length < 2)
                return Fail("Usage: mexcli ssm-info <in.ssm>");

            string inPath = args[1];
            if (!File.Exists(inPath))
                return Fail($"File not found: {inPath}");

            try
            {
                SSM ssm = new();
                using (FileStream fs = new(inPath, FileMode.Open, FileAccess.Read))
                    ssm.Open(Path.GetFileName(inPath), fs);

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    name = ssm.Name,
                    startIndex = ssm.StartIndex,
                    count = ssm.Sounds.Length,
                    sounds = ssm.Sounds.Select((s, i) => new
                    {
                        index = i,
                        frequency = s.Frequency,
                        durationMs = s.TotalMilliseconds,
                    }).ToArray(),
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                return Fail($"SSM read failed: {ex.Message}");
            }
        }

        /// <summary>
        /// sem-resolve &lt;file.sem&gt; &lt;globalScriptId&gt;
        /// Resolves a SEM sound script id (bank*10000 + script, the form
        /// fighter announcerCall uses) to the script's SFX id.
        /// </summary>
        public static int SemResolve(string[] args)
        {
            if (args.Length < 3)
                return Fail("Usage: mexcli sem-resolve <file.sem> <globalScriptId>");

            string inPath = args[1];
            if (!File.Exists(inPath))
                return Fail($"File not found: {inPath}");
            if (!int.TryParse(args[2], out int globalId))
                return Fail($"Invalid script id: {args[2]}");

            try
            {
                var banks = SEM.ReadSEMFile(inPath);
                int bankIndex = globalId / 10000;
                int scriptIndex = globalId % 10000;
                if (bankIndex < 0 || bankIndex >= banks.Count)
                    return Fail($"Bank {bankIndex} out of range (0..{banks.Count - 1})");
                var scripts = banks[bankIndex].Scripts;
                if (scriptIndex < 0 || scriptIndex >= scripts.Length)
                    return Fail($"Script {scriptIndex} out of range (0..{scripts.Length - 1})");

                var script = scripts[scriptIndex];
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    bank = bankIndex,
                    script = scriptIndex,
                    sfxId = script.SFXID,
                    name = script.Name,
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                return Fail($"SEM read failed: {ex.Message}");
            }
        }

        /// <summary>
        /// ssm-to-wav &lt;in.ssm&gt; &lt;soundIndex&gt; &lt;out.wav&gt;
        /// </summary>
        public static int SsmToWav(string[] args)
        {
            if (args.Length < 4)
                return Fail("Usage: mexcli ssm-to-wav <in.ssm> <soundIndex> <out.wav>");

            string inPath = args[1];
            string outPath = args[3];
            if (!File.Exists(inPath))
                return Fail($"File not found: {inPath}");
            if (!int.TryParse(args[2], out int index))
                return Fail($"Invalid sound index: {args[2]}");

            try
            {
                SSM ssm = new();
                using (FileStream fs = new(inPath, FileMode.Open, FileAccess.Read))
                    ssm.Open(Path.GetFileName(inPath), fs);

                if (index < 0 || index >= ssm.Sounds.Length)
                    return Fail($"Sound index {index} out of range (0..{ssm.Sounds.Length - 1})");

                DSP dsp = ssm.Sounds[index];
                File.WriteAllBytes(outPath, dsp.ToWAVE().ToFile());
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    index,
                    durationMs = dsp.TotalMilliseconds,
                    frequency = dsp.Frequency,
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                return Fail($"SSM decode failed: {ex.Message}");
            }
        }
    }
}
