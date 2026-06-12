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
        /// audio-to-hps &lt;in&gt; &lt;out.hps&gt;
        /// Converts an audio file (wav/mp3/aiff/wma/m4a/dsp) to Melee's HPS
        /// music format — the same DSP.FromFile + WriteDSPAsHPS path
        /// MexManager's music import uses.
        /// </summary>
        public static int AudioToHps(string[] args)
        {
            if (args.Length < 3)
                return Fail("Usage: mexcli audio-to-hps <in> <out.hps>");

            string inPath = args[1];
            string outPath = args[2];
            if (!File.Exists(inPath))
                return Fail($"File not found: {inPath}");

            try
            {
                DSP dsp = new();
                if (!dsp.FromFile(inPath))
                    return Fail($"Unsupported or unreadable audio file: {inPath}");

                // HPS music must be stereo — mirror a mono source
                if (dsp.Channels.Count == 1)
                {
                    DSPChannel c = dsp.Channels[0];
                    dsp.Channels.Add(new DSPChannel()
                    {
                        Format = c.Format,
                        COEF = c.COEF,
                        Data = (byte[])c.Data.Clone(),
                        LoopFlag = c.LoopFlag,
                        Gain = c.Gain,
                        InitialPredictorScale = c.InitialPredictorScale,
                        InitialSampleHistory1 = c.InitialSampleHistory1,
                        InitialSampleHistory2 = c.InitialSampleHistory2,
                        LoopPredictorScale = c.LoopPredictorScale,
                        LoopSampleHistory1 = c.LoopSampleHistory1,
                        LoopSampleHistory2 = c.LoopSampleHistory2,
                        LoopStart = c.LoopStart,
                        NibbleCount = c.NibbleCount,
                    });
                }
                else if (dsp.Channels.Count != 2)
                    return Fail($"HPS music must be mono or stereo (file has {dsp.Channels.Count} channels)");

                using (MemoryStream ms = new())
                {
                    HPS.WriteDSPAsHPS(dsp, ms);
                    File.WriteAllBytes(outPath, ms.ToArray());
                }

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
                return Fail($"HPS encode failed: {ex.Message}");
            }
        }

        /// <summary>
        /// ssm-replace &lt;in.ssm&gt; &lt;soundIndex&gt; &lt;audioFile&gt; &lt;out.ssm&gt;
        /// Replaces one sound in a bank with an audio file (wav/mp3/dsp/hps...)
        /// and writes the rebuilt bank.
        /// </summary>
        public static int SsmReplace(string[] args)
        {
            if (args.Length < 5)
                return Fail("Usage: mexcli ssm-replace <in.ssm> <soundIndex> <audioFile> <out.ssm>");

            string inPath = args[1];
            string audioPath = args[3];
            string outPath = args[4];
            if (!File.Exists(inPath))
                return Fail($"File not found: {inPath}");
            if (!File.Exists(audioPath))
                return Fail($"File not found: {audioPath}");
            if (!int.TryParse(args[2], out int index))
                return Fail($"Invalid sound index: {args[2]}");

            try
            {
                SSM ssm = new();
                using (FileStream fs = new(inPath, FileMode.Open, FileAccess.Read))
                    ssm.Open(Path.GetFileName(inPath), fs);

                if (index < 0 || index >= ssm.Sounds.Length)
                    return Fail($"Sound index {index} out of range (0..{ssm.Sounds.Length - 1})");

                DSP dsp = new();
                if (!dsp.FromFile(audioPath))
                    return Fail($"Unsupported or unreadable audio file: {audioPath}");

                ssm.Sounds[index] = dsp;

                using (MemoryStream ms = new())
                {
                    ssm.WriteToStream(ms, out int _);
                    File.WriteAllBytes(outPath, ms.ToArray());
                }

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
                return Fail($"SSM replace failed: {ex.Message}");
            }
        }

        /// <summary>
        /// ssm-copy &lt;src.ssm&gt; &lt;srcIndex&gt; &lt;dst.ssm&gt; &lt;dstIndex&gt; &lt;out.ssm&gt;
        /// Copies a sound between banks without re-encoding (lossless revert).
        /// </summary>
        public static int SsmCopy(string[] args)
        {
            if (args.Length < 6)
                return Fail("Usage: mexcli ssm-copy <src.ssm> <srcIndex> <dst.ssm> <dstIndex> <out.ssm>");

            string srcPath = args[1];
            string dstPath = args[3];
            string outPath = args[5];
            if (!File.Exists(srcPath))
                return Fail($"File not found: {srcPath}");
            if (!File.Exists(dstPath))
                return Fail($"File not found: {dstPath}");
            if (!int.TryParse(args[2], out int srcIndex))
                return Fail($"Invalid sound index: {args[2]}");
            if (!int.TryParse(args[4], out int dstIndex))
                return Fail($"Invalid sound index: {args[4]}");

            try
            {
                SSM src = new();
                using (FileStream fs = new(srcPath, FileMode.Open, FileAccess.Read))
                    src.Open(Path.GetFileName(srcPath), fs);
                SSM dst = new();
                using (FileStream fs = new(dstPath, FileMode.Open, FileAccess.Read))
                    dst.Open(Path.GetFileName(dstPath), fs);

                if (srcIndex < 0 || srcIndex >= src.Sounds.Length)
                    return Fail($"Source index {srcIndex} out of range (0..{src.Sounds.Length - 1})");
                if (dstIndex < 0 || dstIndex >= dst.Sounds.Length)
                    return Fail($"Dest index {dstIndex} out of range (0..{dst.Sounds.Length - 1})");

                dst.Sounds[dstIndex] = src.Sounds[srcIndex];

                using (MemoryStream ms = new())
                {
                    dst.WriteToStream(ms, out int _);
                    File.WriteAllBytes(outPath, ms.ToArray());
                }

                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    success = true,
                    index = dstIndex,
                    durationMs = dst.Sounds[dstIndex].TotalMilliseconds,
                    frequency = dst.Sounds[dstIndex].Frequency,
                }, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            catch (Exception ex)
            {
                return Fail($"SSM copy failed: {ex.Message}");
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
