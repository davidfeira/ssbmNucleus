using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Windows.Forms;
using SixLabors.ImageSharp.Processing;
using SixLabors.ImageSharp.Formats.Png;
using HSDRawViewer.Rendering;
using HSDRawViewer.Rendering.Models;
using HSDRawViewer.Tools.Animation;
using HSDRawViewer.Converters.Animation;
using HSDRawViewer.GUI.Controls.JObjEditor;
using HSDRaw.Tools.Melee;
using HSDRaw.Common.Animation;
using HSDRawViewer.Converters;
using IONET;
using IONET.Core;
using IONET.Core.Model;
using HSDRaw;
using HSDRaw.Common;
using HSDRawViewer.Sound;
using System.Text.Json;
namespace HSDRawViewer
{
    static class Program
    {
        private static System.IO.StreamWriter logFile;

        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main(string[] args)
        {
            // CLI modes may be launched by the app with redirected output.
            // Forcing a console allocation creates a visible popup window.
            if (args.Length >= 2 && args[0] == "--csp")
            {
                // Redirect Console output to both console and file
                logFile = new System.IO.StreamWriter("csp_debug.log", false);
                logFile.AutoFlush = true;
                var multiWriter = new MultiTextWriter(Console.Out, logFile);
                Console.SetOut(multiWriter);
            }

            Console.WriteLine($"Main called with {args.Length} arguments");
            for (int i = 0; i < args.Length; i++)
            {
                Console.WriteLine($"Arg[{i}]: {args[i]}");
            }

            // Check for CLI CSP generation mode
            if (args.Length >= 2 && args[0] == "--csp")
            {
                Console.WriteLine("CSP mode detected, calling RunCSPGeneration");
                RunCSPGeneration(args);
                Console.WriteLine("RunCSPGeneration returned");
                logFile?.Close();
                return;
            }

            // Check for streaming mode
            if (args.Length >= 3 && args[0] == "--stream")
            {
                Console.WriteLine("Streaming mode detected");
                RunStreamingServer(args);
                return;
            }

            // Check for embedded mode (for Electron integration)
            if (args.Length >= 3 && args[0] == "--embedded")
            {
                Console.WriteLine("Embedded mode detected");
                RunEmbeddedServer(args);
                return;
            }

            // Check for model export/import mode
            if (args.Length >= 4 && args[0] == "--model")
            {
                Console.WriteLine("Model operation mode detected");
                RunModelOperation(args);
                return;
            }

            // Check for texture export/import mode
            if (args.Length >= 4 && args[0] == "--texture")
            {
                Console.WriteLine("Texture operation mode detected");
                RunTextureOperation(args);
                return;
            }

            // Check for sound extraction mode
            if (args.Length >= 1 && args[0] == "--sound")
            {
                Console.WriteLine("Sound operation mode detected");
                RunSoundOperation(args);
                return;
            }

            // Check for PNG → MEX .tex conversion mode
            if (args.Length >= 1 && args[0] == "--convert-tex")
            {
                Console.WriteLine("Convert TEX mode detected");
                RunConvertTex(args);
                return;
            }

            // Check for CSS icons dump mode
            if (args.Length >= 1 && args[0] == "--css-icons")
            {
                Console.WriteLine("CSS icons dump mode detected");
                RunCssIconsDump(args);
                return;
            }

            // Check for CSS background export/import mode
            if (args.Length >= 1 && args[0] == "--css-bg")
            {
                Console.WriteLine("CSS background mode detected");
                RunCssBgOperation(args);
                return;
            }

            // Check for SSS background export/import mode
            if (args.Length >= 1 && args[0] == "--sss-bg")
            {
                Console.WriteLine("SSS background mode detected");
                RunSssBgOperation(args);
                return;
            }

            // Check for CSS doors export/import mode
            if (args.Length >= 1 && args[0] == "--css-doors")
            {
                Console.WriteLine("CSS doors mode detected");
                RunCssDoorsOperation(args);
                return;
            }

            // Check for pause screen export/import mode
            if (args.Length >= 1 && args[0] == "--pause-screen")
            {
                Console.WriteLine("Pause screen mode detected");
                RunPauseScreenOperation(args);
                return;
            }

            // Check for stage texture export/import mode (Gr*.dat map_head models)
            if (args.Length >= 1 && args[0] == "--stage-textures")
            {
                Console.WriteLine("Stage textures mode detected");
                RunStageTexturesOperation(args);
                return;
            }

            // Check for MEX CSS info mode (reads MxDt.dat icon -> fighter mapping)
            if (args.Length >= 1 && args[0] == "--mex-css-info")
            {
                Console.WriteLine("MEX CSS info mode detected");
                RunMexCssInfo(args);
                return;
            }

            // Dump per-bone world transforms for an animation frame (the
            // character's true in-game rest pose lives in Wait1 frame 0, NOT
            // the bind pose — the model-lab rigger needs the difference)
            if (args.Length >= 1 && args[0] == "--dump-pose")
            {
                RunDumpPose(args);
                return;
            }

            // Attach a mexCostume physics accessory (cape/cloth with its own
            // dynamic joint chains) to a costume dat
            if (args.Length >= 1 && args[0] == "--accessory")
            {
                RunAddAccessory(args);
                return;
            }

            Console.WriteLine("Starting normal GUI mode");
            // Normal GUI mode
            Application.EnableVisualStyles();
            Application.SetHighDpiMode(HighDpiMode.SystemAware);
            Application.SetCompatibleTextRenderingDefault(false);
            Thread.CurrentThread.CurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
            PluginManager.Init();
            Rendering.OpenTKResources.Init();
            MainForm.Init();
            ApplicationSettings.Init();
            if (args.Length > 0)
                MainForm.Instance.OpenFile(args[0]);
            Application.Run(MainForm.Instance);
        }

        static void RunStreamingServer(string[] args)
        {
            try
            {
                if (args.Length < 3)
                {
                    Console.WriteLine("Usage: HSDRawViewer.exe --stream <port> <dat_file> [logs_path] [scene_file] [aj_file]");
                    Console.WriteLine("Example: HSDRawViewer.exe --stream 8765 PlFxNr.dat C:\\projects\\logs scene.yml PlFxAJ.dat");
                    return;
                }

                int port = int.Parse(args[1]);
                string datFile = args[2];
                string logsPath = args.Length >= 4 ? args[3] : null;
                string sceneFile = args.Length >= 5 ? args[4] : null;
                string ajFile = args.Length >= 6 ? args[5] : null;

                Console.WriteLine($"Starting streaming server on port {port}...");
                Console.WriteLine($"DAT file: {datFile}");
                if (logsPath != null)
                    Console.WriteLine($"Logs path: {logsPath}");
                if (sceneFile != null)
                    Console.WriteLine($"Scene file: {sceneFile}");
                if (ajFile != null)
                    Console.WriteLine($"AJ file: {ajFile}");

                using var server = new StreamingServer(port, logsPath);

                // Handle Ctrl+C
                Console.CancelKeyPress += (sender, e) =>
                {
                    e.Cancel = true;
                    Console.WriteLine("Shutdown requested...");
                    server.Stop();
                };

                // Run server (blocking)
                server.StartAsync(datFile, sceneFile, ajFile).GetAwaiter().GetResult();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Streaming server error: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        static void RunEmbeddedServer(string[] args)
        {
            try
            {
                if (args.Length < 3)
                {
                    Console.WriteLine("Usage: HSDRawViewer.exe --embedded <pipe_name> <dat_file> [logs_path] [scene_file] [aj_file]");
                    Console.WriteLine("Example: HSDRawViewer.exe --embedded HSDViewer_12345 PlFxNr.dat C:\\logs scene.yml PlFxAJ.dat");
                    return;
                }

                string pipeName = args[1];
                string datFile = args[2];
                string logsPath = args.Length >= 4 ? args[3] : null;
                string sceneFile = args.Length >= 5 ? args[4] : null;
                string ajFile = args.Length >= 6 ? args[5] : null;

                Console.WriteLine($"Starting embedded server with pipe: {pipeName}");
                Console.WriteLine($"DAT file: {datFile}");
                if (logsPath != null)
                    Console.WriteLine($"Logs path: {logsPath}");
                if (sceneFile != null)
                    Console.WriteLine($"Scene file: {sceneFile}");
                if (ajFile != null)
                    Console.WriteLine($"AJ file: {ajFile}");

                using var server = new EmbeddedServer(pipeName, logsPath);

                // Handle Ctrl+C
                Console.CancelKeyPress += (sender, e) =>
                {
                    e.Cancel = true;
                    Console.WriteLine("Shutdown requested...");
                    server.Stop();
                };

                // Run server (blocking)
                server.StartAsync(datFile, sceneFile, ajFile).GetAwaiter().GetResult();
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Embedded server error: {ex.Message}");
                Console.Error.WriteLine($"Stack trace: {ex.StackTrace}");
                Console.Error.Flush();
                Environment.Exit(1);
            }
        }

        static void RunCSPGeneration(string[] args)
        {
            try
            {
                Console.WriteLine("Starting CSP generation...");

                if (args.Length < 3)
                {
                    Console.WriteLine("Usage: HSDRawViewer.exe --csp <dat_file> <output_file> [--scale N] [anim_file] [camera_yml]");
                    Console.WriteLine("Example: HSDRawViewer.exe --csp PlKpNr.dat bowser_csp.png --scale 4 cspfinal.anim cspfinal.yml");
                    return;
                }

                // Parse --scale argument if present
                int cspScale = 1;
                var argsList = new List<string>(args);
                int scaleIndex = argsList.IndexOf("--scale");
                if (scaleIndex >= 0 && scaleIndex + 1 < argsList.Count)
                {
                    if (int.TryParse(argsList[scaleIndex + 1], out int parsedScale))
                    {
                        cspScale = parsedScale;
                        Console.WriteLine($"Scale factor: {cspScale}x");
                    }
                    // Remove --scale and its value from args
                    argsList.RemoveAt(scaleIndex + 1);
                    argsList.RemoveAt(scaleIndex);
                    args = argsList.ToArray();
                }

                // Parse --head-bone argument if present: project this JOBJ's
                // posed position into CSP pixel coordinates and write a
                // <output>.head.json sidecar (used by stock icon generation
                // to crop the head of arbitrary imported models).
                int headBoneIndex = -1;
                int headBoneArg = argsList.IndexOf("--head-bone");
                if (headBoneArg >= 0 && headBoneArg + 1 < argsList.Count)
                {
                    if (int.TryParse(argsList[headBoneArg + 1], out int parsedHead))
                    {
                        headBoneIndex = parsedHead;
                        Console.WriteLine($"Head bone index: {headBoneIndex}");
                    }
                    argsList.RemoveAt(headBoneArg + 1);
                    argsList.RemoveAt(headBoneArg);
                    args = argsList.ToArray();
                }

                // --head-shot: render the BIND POSE with an auto-framed camera
                // (no animation/scene args should be passed). Gives stock-icon
                // generation a consistent front-facing render where the head
                // can never be posed out of frame.
                bool headShot = false;
                int headShotArg = argsList.IndexOf("--head-shot");
                if (headShotArg >= 0)
                {
                    headShot = true;
                    argsList.RemoveAt(headShotArg);
                    args = argsList.ToArray();
                    // raw silhouette: the CSPMaker post-process stamps a fake
                    // drop shadow that pollutes the crop's alpha mask
                    GUI.ViewportControl.SkipCSPPostProcess = true;
                    Console.WriteLine("Head-shot mode: bind pose + auto-framed camera, raw silhouette");
                }

                // strip the legacy --no-shadow flag (the shadow was never a
                // scene object -- it is CSPMaker post-processing, handled
                // above) so it can't be mistaken for a positional argument
                int noShadowArg = argsList.IndexOf("--no-shadow");
                if (noShadowArg >= 0)
                {
                    argsList.RemoveAt(noShadowArg);
                    args = argsList.ToArray();
                }

                // --head-shot-yaw N: 3/4-view angle in degrees for head shots
                float headShotYaw = 30f;
                int yawArg = argsList.IndexOf("--head-shot-yaw");
                if (yawArg >= 0 && yawArg + 1 < argsList.Count)
                {
                    if (float.TryParse(argsList[yawArg + 1],
                            System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out float parsedYaw))
                        headShotYaw = parsedYaw;
                    argsList.RemoveAt(yawArg + 1);
                    argsList.RemoveAt(yawArg);
                    args = argsList.ToArray();
                }

                // --collapse-bones a,b: zero-scale these JOBJ subtrees before
                // rendering (head shots collapse the ARMS so a T-pose can't
                // overlap or widen the head silhouette; works for one-piece
                // skinned custom models where DOBJ hiding cannot)
                var collapseBones = new List<int>();
                int collapseArg = argsList.IndexOf("--collapse-bones");
                if (collapseArg >= 0 && collapseArg + 1 < argsList.Count)
                {
                    foreach (var part in argsList[collapseArg + 1].Split(','))
                        if (int.TryParse(part.Trim(), out int b))
                            collapseBones.Add(b);
                    argsList.RemoveAt(collapseArg + 1);
                    argsList.RemoveAt(collapseArg);
                    args = argsList.ToArray();
                    Console.WriteLine($"Collapsing bone subtrees: {string.Join(",", collapseBones)}");
                }

                // Apply scale to CSP dimensions
                if (cspScale > 1)
                {
                    GUI.ViewportControl.CSPWidth = 136 * 2 * cspScale;
                    GUI.ViewportControl.CSPHeight = 188 * 2 * cspScale;
                    Console.WriteLine($"CSP dimensions set to: {GUI.ViewportControl.CSPWidth / 2}x{GUI.ViewportControl.CSPHeight / 2}");
                }

                string datFile = args[1];
                string outputFile = args[2];
                string animFile = args.Length > 3 ? args[3] : null;
                string cameraFile = args.Length > 4 ? args[4] : null;

                // Detect if we're using a scene file by filename
                // If the yml file is named "scene.yml", use scene mode
                bool useSceneFile = false;
                string sceneFileToCheck = cameraFile ?? animFile;

                if (!string.IsNullOrEmpty(sceneFileToCheck) && System.IO.File.Exists(sceneFileToCheck))
                {
                    string filename = System.IO.Path.GetFileName(sceneFileToCheck).ToLower();
                    if (filename == "scene.yml")
                    {
                        useSceneFile = true;
                        // If scene file was passed as animFile (arg[3]), move it to cameraFile
                        if (cameraFile == null && animFile != null)
                        {
                            cameraFile = animFile;
                            animFile = null;  // Clear animFile since it's actually a scene file
                        }
                        Console.WriteLine("*** SCENE FILE DETECTED (scene.yml) ***");
                    }
                }

                Console.WriteLine($"Generating CSP for: {datFile}");
                Console.WriteLine($"Output: {outputFile}");
                Console.WriteLine($"Scene file mode: {useSceneFile}");

                // Initialize core systems (no GUI)
                Thread.CurrentThread.CurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
                PluginManager.Init();
                ApplicationSettings.Init();

                // Load DAT file
                Console.WriteLine($"Loading DAT file: {datFile}");
                if (!System.IO.File.Exists(datFile))
                {
                    throw new System.IO.FileNotFoundException($"DAT file not found: {datFile}");
                }

                var rawFile = new HSDRaw.HSDRawFile();
                rawFile.Open(datFile);

                // Initialize headless OpenGL context using GLControl approach
                Console.WriteLine("Setting up headless OpenGL context...");

                // Use the EXACT same approach as the working GUI - create actual ViewportControl
                Console.WriteLine("Creating ViewportControl with loaded DAT...");

                // Initialize MainForm like normal GUI mode (this sets up all the renderers properly)
                MainForm.Init();
                MainForm.Instance.OpenFile(datFile);

                // Wait for file to load
                System.Threading.Thread.Sleep(500);

                // Find and select the character JOBJ node (like PlyPichu5K_Share_joint)
                Console.WriteLine("Looking for character JOBJ to render...");
                DataNode characterJobjNode = null;

                // Search through all roots for character JOBJ nodes
                foreach (var root in rawFile.Roots)
                {
                    Console.WriteLine($"Checking root: {root.Name} (Type: {root.Data?.GetType().Name})");

                    // Look for JOBJ nodes with character-like names
                    if (root.Data is HSDRaw.Common.HSD_JOBJ &&
                        (root.Name.Contains("Share_joint") || root.Name.Contains("_joint") || root.Name.Contains("Ply")))
                    {
                        Console.WriteLine($"Found character JOBJ: {root.Name}");
                        characterJobjNode = new DataNode(root.Name, root.Data, root: root);
                        break;
                    }
                }

                if (characterJobjNode != null)
                {
                    Console.WriteLine($"Selecting character JOBJ: {characterJobjNode.Text}");
                    MainForm.SelectedDataNode = characterJobjNode;
                    MainForm.Instance.OpenEditor(); // This triggers the viewport rendering
                }
                else
                {
                    Console.WriteLine("No character JOBJ found - trying first JOBJ as fallback");
                    // Fallback to first JOBJ found
                    foreach (var root in rawFile.Roots)
                    {
                        if (root.Data is HSDRaw.Common.HSD_JOBJ)
                        {
                            Console.WriteLine($"Using fallback JOBJ: {root.Name}");
                            characterJobjNode = new DataNode(root.Name, root.Data, root: root);
                            MainForm.SelectedDataNode = characterJobjNode;
                            MainForm.Instance.OpenEditor();
                            break;
                        }
                    }
                }

                // Wait for editor to open
                System.Threading.Thread.Sleep(1000);

                // Create a ViewportControl directly
                var viewport = new HSDRawViewer.GUI.ViewportControl();

                // Manually create the RenderJObj like JObjEditorNew does
                HSDRawViewer.Rendering.Models.RenderJObj renderJObj = null;
                if (characterJobjNode != null && characterJobjNode.Accessor is HSDRaw.Common.HSD_JOBJ jobj)
                {
                    Console.WriteLine("Creating RenderJObj...");
                    renderJObj = new HSDRawViewer.Rendering.Models.RenderJObj(jobj);
                    Console.WriteLine($"RenderJObj created. DOBJs loaded: {renderJObj.DObjCount}");

                    // Note: We'll hide bones and nodes after loading YAML settings

                    // Load scene file OR separate animation file
                    if (useSceneFile && !string.IsNullOrEmpty(cameraFile))
                    {
                        Console.WriteLine($"=== LOADING SCENE FILE: {cameraFile} ===");
                        try
                        {
                            // Use SceneSettings deserializer (same as GUI)
                            var sceneSettings = SceneSettings.Deserialize(cameraFile);
                            Console.WriteLine("Scene file deserialized successfully");

                            // Apply animation from scene
                            if (sceneSettings.Animation != null)
                            {
                                Console.WriteLine($"Loading animation from scene file (FrameCount: {sceneSettings.Animation.FrameCount})");
                                renderJObj.LoadAnimation(sceneSettings.Animation, null, null);
                                Console.WriteLine("Animation loaded from scene");
                            }
                            else
                            {
                                Console.WriteLine("WARNING: Scene file has no animation data");
                            }

                            Console.WriteLine("=== SCENE FILE LOADED ===");
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"FAILED to load scene file: {ex.Message}");
                            Console.WriteLine($"Stack trace: {ex.StackTrace}");
                            throw; // Re-throw since this is required for Ganondorf
                        }
                    }
                    else if (!string.IsNullOrEmpty(animFile) && System.IO.File.Exists(animFile))
                    {
                        // Check if this is a YML file with animSymbol + AJ file path in cameraFile
                        string animSymbol = null;
                        bool isYmlWithSymbol = animFile.EndsWith(".yml", StringComparison.OrdinalIgnoreCase);

                        if (isYmlWithSymbol)
                        {
                            // Parse YML to look for animSymbol
                            try
                            {
                                var ymlLines = System.IO.File.ReadAllLines(animFile);
                                foreach (var line in ymlLines)
                                {
                                    var trimmed = line.Trim();
                                    if (trimmed.StartsWith("animSymbol:"))
                                    {
                                        animSymbol = trimmed.Substring(11).Trim();
                                        Console.WriteLine($"Found animSymbol in YML: {animSymbol}");
                                        break;
                                    }
                                }
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine($"Error parsing YML for animSymbol: {ex.Message}");
                            }
                        }

                        // NEW PATH: Load animation from AJ file using symbol
                        if (!string.IsNullOrEmpty(animSymbol) &&
                            !string.IsNullOrEmpty(cameraFile) &&
                            cameraFile.EndsWith(".dat", StringComparison.OrdinalIgnoreCase) &&
                            System.IO.File.Exists(cameraFile))
                        {
                            Console.WriteLine($"=== LOADING ANIMATION FROM AJ FILE BY SYMBOL ===");
                            Console.WriteLine($"AJ File: {cameraFile}");
                            Console.WriteLine($"Symbol: {animSymbol}");
                            try
                            {
                                var ajManager = new FighterAJManager(System.IO.File.ReadAllBytes(cameraFile));
                                var animData = ajManager.GetAnimationData(animSymbol);

                                if (animData != null)
                                {
                                    Console.WriteLine($"Found animation data for symbol, length: {animData.Length} bytes");
                                    var animRawFile = new HSDRaw.HSDRawFile(animData);

                                    if (animRawFile.Roots.Count > 0 && animRawFile.Roots[0].Data is HSD_FigaTree tree)
                                    {
                                        var jointAnim = new JointAnimManager(tree);
                                        renderJObj.LoadAnimation(jointAnim, null, null);
                                        Console.WriteLine($"Animation loaded from AJ file (FrameCount: {jointAnim.FrameCount})");
                                    }
                                    else
                                    {
                                        Console.WriteLine("Animation data did not contain HSD_FigaTree");
                                    }
                                }
                                else
                                {
                                    Console.WriteLine($"Symbol '{animSymbol}' not found in AJ file");
                                }
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine($"Failed to load animation from AJ: {ex.Message}");
                                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                            }
                        }
                        else if (!isYmlWithSymbol)
                        {
                            // OLD PATH: Load animation from separate .anim file
                            Console.WriteLine($"Loading animation file: {animFile}");
                            try
                            {
                                // Use the same animation loader as the GUI
                                var jointMap = new JointMap(); // Use empty joint map for basic animation loading
                                var animManager = JointAnimationLoader.LoadJointAnimFromFile(jointMap, animFile);

                                if (animManager != null)
                                {
                                    Console.WriteLine("Animation loaded successfully");
                                    renderJObj.LoadAnimation(animManager, null, null);
                                }
                                else
                                {
                                    Console.WriteLine("Failed to load animation - loader returned null");
                                }
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine($"Failed to load animation: {ex.Message}");
                            }
                        }
                    }

                    // Create a simple drawable wrapper that calls RenderJObj.Render
                    var drawable = new SimpleJObjDrawable(renderJObj);

                    // Add the drawable to the viewport
                    Console.WriteLine("Adding drawable to viewport...");
                    viewport.AddRenderer(drawable);
                }

                // Create a form to host the viewport (hidden, never activates -
                // batch CSP generation must not steal focus from the user).
                // Parked offscreen rather than minimized: a minimized window with
                // ShowInTaskbar=false is drawn by Windows as a small caption box
                // at the bottom-left of the desktop (the "lil popup" users saw).
                using (var form = new NoActivateForm())
                {
                    form.FormBorderStyle = FormBorderStyle.None;
                    form.StartPosition = FormStartPosition.Manual;
                    form.Location = new System.Drawing.Point(-32000, -32000);
                    form.ShowInTaskbar = false;
                    viewport.Dock = DockStyle.Fill;
                    form.Controls.Add(viewport);
                    form.Show();

                    // Wait for everything to initialize
                    System.Threading.Thread.Sleep(1000);

                    // Enable CSP mode exactly like the GUI
                    Console.WriteLine("Enabling CSP mode...");
                    viewport.CSPMode = true;

                    // Disable background for transparent CSP
                    Console.WriteLine("Disabling background for transparency...");
                    viewport.EnableBack = false;

                    Console.WriteLine("*** TESTING: NEW CODE IS RUNNING ***");

                    // Load camera settings if provided
                    Console.WriteLine($"Checking camera file: '{cameraFile}'");
                    Console.WriteLine($"File exists: {System.IO.File.Exists(cameraFile)}");
                    var hiddenNodes = new List<int>();

                    // Lighting settings variables (declared here for proper scope)
                    float lightX = 30, lightY = 30, lightZ = 80;
                    float ambientPower = 0.35f, ambientR = 255, ambientG = 255, ambientB = 255;
                    float diffusePower = 1.2f, diffuseR = 255, diffuseG = 255, diffuseB = 255;
                    bool hasLightingSettings = false;
                    // When the YML sets `useCameraLight: true`, leave the default camera light
                    // alone — don't slam in a custom hard-lit setup that washes out the model.
                    // Mirrors the meleeWebsite repo's CSP fix; YMLs in csp_data/<Char>/ rely on
                    // this so vanilla skins render with the canonical Melee CSS lighting.
                    bool useCameraLight = false;
                    bool useCameraLightFound = false;
                    float animFrame = -1; // -1 means not set

                    // Load settings from scene file if using scene mode
                    if (useSceneFile && !string.IsNullOrEmpty(cameraFile) && System.IO.File.Exists(cameraFile))
                    {
                        Console.WriteLine("=== LOADING CAMERA/SETTINGS FROM SCENE FILE ===");
                        try
                        {
                            var sceneSettings = SceneSettings.Deserialize(cameraFile);

                            // Apply camera settings
                            if (sceneSettings.Camera != null)
                            {
                                viewport.Camera = sceneSettings.Camera;
                                Console.WriteLine("Camera loaded from scene file");
                            }

                            // Apply display settings
                            if (sceneSettings.Settings != null)
                            {
                                renderJObj._settings = sceneSettings.Settings;
                                Console.WriteLine("Render settings loaded from scene file");
                            }

                            // Apply frame
                            animFrame = sceneSettings.Frame;
                            Console.WriteLine($"Frame from scene: {animFrame}");

                            // Apply hidden nodes
                            if (sceneSettings.HiddenNodes != null && sceneSettings.HiddenNodes.Length > 0)
                            {
                                hiddenNodes.AddRange(sceneSettings.HiddenNodes);
                                Console.WriteLine($"Hidden nodes from scene: {hiddenNodes.Count}");
                            }

                            Console.WriteLine("=== SCENE CAMERA/SETTINGS LOADED ===");
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"FAILED to load camera/settings from scene: {ex.Message}");
                            Console.WriteLine($"Stack trace: {ex.StackTrace}");
                            throw; // Re-throw since this is required for Ganondorf
                        }
                    }
                    else if (!useSceneFile && !string.IsNullOrEmpty(cameraFile) && System.IO.File.Exists(cameraFile) &&
                             !cameraFile.EndsWith(".dat", StringComparison.OrdinalIgnoreCase))
                    {
                        Console.WriteLine($"Loading camera settings from: {cameraFile}");
                        try
                        {
                            Console.WriteLine("*** DEBUG: Starting YAML parsing with hiddenNodes support ***");
                            var lines = System.IO.File.ReadAllLines(cameraFile);
                            bool parsingHiddenNodes = false;

                            Console.WriteLine($"Parsing YAML file with {lines.Length} lines...");
                            foreach (var line in lines)
                            {
                                var trimmedLine = line.Trim();
                                Console.WriteLine($"Processing line: '{trimmedLine}'");
                                if (trimmedLine.StartsWith("frame:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(6).Trim(), out float frame))
                                    {
                                        animFrame = frame;
                                        Console.WriteLine($"Found animation frame setting: {animFrame}");
                                    }
                                }
                                else if (trimmedLine.StartsWith("x:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(2).Trim(), out float x))
                                        viewport.Camera.X = x;
                                }
                                else if (trimmedLine.StartsWith("y:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(2).Trim(), out float y))
                                        viewport.Camera.Y = y;
                                }
                                else if (trimmedLine.StartsWith("z:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(2).Trim(), out float z))
                                        viewport.Camera.Z = z;
                                }
                                else if (trimmedLine.StartsWith("scale:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(6).Trim(), out float scale))
                                        viewport.Camera.Scale = scale;
                                }
                                else if (trimmedLine.StartsWith("fovRadians:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(11).Trim(), out float fov))
                                        viewport.Camera.FovRadians = fov;
                                }
                                else if (trimmedLine.StartsWith("rotationXRadians:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(17).Trim(), out float rotX))
                                        viewport.Camera.RotationXRadians = rotX;
                                }
                                else if (trimmedLine.StartsWith("rotationYRadians:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(17).Trim(), out float rotY))
                                        viewport.Camera.RotationYRadians = rotY;
                                }
                                else if (trimmedLine.StartsWith("farClipPlane:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(13).Trim(), out float farClip))
                                        viewport.Camera.FarClipPlane = farClip;
                                }
                                else if (trimmedLine.StartsWith("nearClipPlane:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(14).Trim(), out float nearClip))
                                        viewport.Camera.NearClipPlane = nearClip;
                                }
                                else if (trimmedLine.StartsWith("hiddenNodes:"))
                                {
                                    parsingHiddenNodes = true;
                                    Console.WriteLine("Found hiddenNodes section in YAML");
                                }
                                else if (parsingHiddenNodes && trimmedLine.StartsWith("- "))
                                {
                                    if (int.TryParse(trimmedLine.Substring(2).Trim(), out int nodeIndex))
                                    {
                                        hiddenNodes.Add(nodeIndex);
                                        Console.WriteLine($"Added node {nodeIndex} to hidden list");
                                    }
                                }
                                else if (parsingHiddenNodes && !string.IsNullOrWhiteSpace(trimmedLine) && !trimmedLine.StartsWith(" "))
                                {
                                    parsingHiddenNodes = false;
                                }
                                // Parse lighting settings
                                else if (trimmedLine.StartsWith("useCameraLight:"))
                                {
                                    var val = trimmedLine.Substring(15).Trim().ToLower();
                                    useCameraLight = val == "true";
                                    useCameraLightFound = true;
                                    Console.WriteLine($"Found useCameraLight: {useCameraLight}");
                                }
                                else if (trimmedLine.StartsWith("lightX:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(7).Trim(), out float val))
                                    {
                                        lightX = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("lightY:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(7).Trim(), out float val))
                                    {
                                        lightY = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("lightZ:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(7).Trim(), out float val))
                                    {
                                        lightZ = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("ambientPower:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(13).Trim(), out float val))
                                    {
                                        ambientPower = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("ambientR:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(9).Trim(), out float val))
                                    {
                                        ambientR = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("ambientG:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(9).Trim(), out float val))
                                    {
                                        ambientG = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("ambientB:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(9).Trim(), out float val))
                                    {
                                        ambientB = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("diffusePower:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(13).Trim(), out float val))
                                    {
                                        diffusePower = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("diffuseR:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(9).Trim(), out float val))
                                    {
                                        diffuseR = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("diffuseG:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(9).Trim(), out float val))
                                    {
                                        diffuseG = val;
                                        hasLightingSettings = true;
                                    }
                                }
                                else if (trimmedLine.StartsWith("diffuseB:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(9).Trim(), out float val))
                                    {
                                        diffuseB = val;
                                        hasLightingSettings = true;
                                    }
                                }
                            }
                            Console.WriteLine("Camera settings loaded successfully");
                            Console.WriteLine($"Found {hiddenNodes.Count} nodes to hide: [{string.Join(", ", hiddenNodes)}]");

                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"Failed to load camera settings: {ex.Message}");
                            Console.WriteLine($"Stack trace: {ex.StackTrace}");
                        }

                        // Now hide bones and apply settings after YAML is loaded
                        Console.WriteLine("Applying YAML settings...");
                        if (renderJObj != null)
                        {
                            renderJObj._settings.RenderBones = false;
                            // Ensure we're using Visible render mode so hidden objects are respected
                            renderJObj._settings.RenderObjects = HSDRawViewer.Rendering.Models.ObjectRenderMode.Visible;
                            Console.WriteLine($"Set render mode to: {renderJObj._settings.RenderObjects}");

                            // Apply animation frame if found in YAML
                            if (animFrame >= 0)
                            {
                                Console.WriteLine($"Setting animation to frame: {animFrame}");
                                renderJObj.RequestAnimationUpdate(HSDRawViewer.Rendering.Models.FrameFlags.All, animFrame);
                            }

                            // Apply lighting settings if found in YAML — but only when the YML
                            // hasn't explicitly opted into camera light. `useCameraLight: true`
                            // means "leave the default lighting alone".
                            if (useCameraLightFound && useCameraLight)
                            {
                                Console.WriteLine("useCameraLight=true — skipping custom lighting override");
                            }
                            else if (hasLightingSettings)
                            {
                                Console.WriteLine("Applying custom lighting settings...");
                                ApplyLightingSettings(renderJObj, lightX, lightY, lightZ, ambientPower, ambientR, ambientG, ambientB, diffusePower, diffuseR, diffuseG, diffuseB);
                            }
                        }

                        // Note: Hidden nodes will be applied after first render when DOBJs are loaded
                    }
                    // NEW: Load camera settings from animFile when it's a pose YML and cameraFile is AJ DAT
                    else if (!useSceneFile &&
                             !string.IsNullOrEmpty(animFile) &&
                             animFile.EndsWith(".yml", StringComparison.OrdinalIgnoreCase) &&
                             System.IO.File.Exists(animFile) &&
                             (string.IsNullOrEmpty(cameraFile) || cameraFile.EndsWith(".dat", StringComparison.OrdinalIgnoreCase)))
                    {
                        Console.WriteLine($"=== LOADING CAMERA SETTINGS FROM POSE YML: {animFile} ===");
                        try
                        {
                            var lines = System.IO.File.ReadAllLines(animFile);
                            bool parsingCamera = false;
                            bool parsingHiddenNodes = false;

                            foreach (var line in lines)
                            {
                                var trimmedLine = line.Trim();

                                // Track when we enter camera section
                                if (trimmedLine == "camera:")
                                {
                                    parsingCamera = true;
                                    continue;
                                }
                                // Exit camera section when we hit another top-level key
                                if (parsingCamera && !line.StartsWith(" ") && !line.StartsWith("\t") && trimmedLine.EndsWith(":"))
                                {
                                    parsingCamera = false;
                                }

                                if (trimmedLine.StartsWith("frame:"))
                                {
                                    if (float.TryParse(trimmedLine.Substring(6).Trim(), out float frame))
                                    {
                                        animFrame = frame;
                                        Console.WriteLine($"Found animation frame: {animFrame}");
                                    }
                                }
                                else if (parsingCamera || trimmedLine.StartsWith("x:"))
                                {
                                    if (trimmedLine.StartsWith("x:"))
                                    {
                                        if (float.TryParse(trimmedLine.Substring(2).Trim(), out float x))
                                            viewport.Camera.X = x;
                                    }
                                    else if (trimmedLine.StartsWith("y:"))
                                    {
                                        if (float.TryParse(trimmedLine.Substring(2).Trim(), out float y))
                                            viewport.Camera.Y = y;
                                    }
                                    else if (trimmedLine.StartsWith("z:"))
                                    {
                                        if (float.TryParse(trimmedLine.Substring(2).Trim(), out float z))
                                            viewport.Camera.Z = z;
                                    }
                                    else if (trimmedLine.StartsWith("scale:"))
                                    {
                                        if (float.TryParse(trimmedLine.Substring(6).Trim(), out float scale))
                                            viewport.Camera.Scale = scale;
                                    }
                                    else if (trimmedLine.StartsWith("fovRadians:"))
                                    {
                                        if (float.TryParse(trimmedLine.Substring(11).Trim(), out float fov))
                                            viewport.Camera.FovRadians = fov;
                                    }
                                    else if (trimmedLine.StartsWith("rotationXRadians:"))
                                    {
                                        if (float.TryParse(trimmedLine.Substring(17).Trim(), out float rotX))
                                            viewport.Camera.RotationXRadians = rotX;
                                    }
                                    else if (trimmedLine.StartsWith("rotationYRadians:"))
                                    {
                                        if (float.TryParse(trimmedLine.Substring(17).Trim(), out float rotY))
                                            viewport.Camera.RotationYRadians = rotY;
                                    }
                                }
                                else if (trimmedLine.StartsWith("hiddenNodes:"))
                                {
                                    parsingHiddenNodes = true;
                                }
                                else if (parsingHiddenNodes && trimmedLine.StartsWith("- "))
                                {
                                    if (int.TryParse(trimmedLine.Substring(2).Trim(), out int nodeIndex))
                                        hiddenNodes.Add(nodeIndex);
                                }
                                else if (parsingHiddenNodes && !string.IsNullOrWhiteSpace(trimmedLine) && !trimmedLine.StartsWith(" "))
                                {
                                    parsingHiddenNodes = false;
                                }
                            }
                            Console.WriteLine("Camera settings loaded from pose YML");
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"Failed to load camera settings from pose YML: {ex.Message}");
                        }

                        // Apply settings
                        if (renderJObj != null)
                        {
                            renderJObj._settings.RenderBones = false;
                            renderJObj._settings.RenderObjects = HSDRawViewer.Rendering.Models.ObjectRenderMode.Visible;

                            if (animFrame >= 0)
                            {
                                Console.WriteLine($"Setting animation to frame: {animFrame}");
                                renderJObj.RequestAnimationUpdate(HSDRawViewer.Rendering.Models.FrameFlags.All, animFrame);
                            }
                        }
                    }

                    // Check if the viewport has any drawables loaded
                    Console.WriteLine("Checking viewport drawable count...");

                    // Force a render to make sure everything is loaded
                    Console.WriteLine("Forcing viewport render...");
                    viewport.Render();

                    // Now check if DOBJs are loaded and apply hiding after first render
                    if (renderJObj != null)
                    {
                        Console.WriteLine($"After first render - DOBJs loaded: {renderJObj.DObjCount}");

                        // Apply animation frame AFTER DOBJs are loaded (needed for pose thumbnails)
                        if (animFrame >= 0)
                        {
                            Console.WriteLine($"Applying animation frame after DOBJs loaded: {animFrame}");
                            renderJObj.RequestAnimationUpdate(HSDRawViewer.Rendering.Models.FrameFlags.All, animFrame);
                            viewport.Render();
                        }

                        // Apply hidden nodes if any were specified (moved here after render)
                        if (hiddenNodes.Count > 0)
                        {
                            Console.WriteLine($"Applying hidden nodes after render to {hiddenNodes.Count} JOBJ indices...");
                            ApplyHiddenNodes(characterJobjNode, hiddenNodes, renderJObj);

                            // Force another render to apply the visibility changes
                            Console.WriteLine("Forcing second render to apply visibility changes...");
                            viewport.Render();
                        }
                    }

                    // Head-shot mode: frame the bind-pose model from its bone
                    // positions so the whole character (and therefore the
                    // head) is inside the CSP crop region regardless of the
                    // model's proportions. The visible CSP area is the center
                    // half of the canvas, hence the x2 on the radius.
                    if (headShot && renderJObj != null && renderJObj.RootJObj != null)
                    {
                        try
                        {
                            // no scene yml in head-shot mode, so disable the
                            // debug skeleton overlay explicitly
                            renderJObj._settings.RenderBones = false;
                            renderJObj._settings.RenderObjects = HSDRawViewer.Rendering.Models.ObjectRenderMode.Visible;

                            // collapse requested subtrees (arms) to a point;
                            // tiny non-zero scale avoids divide-by-zero in
                            // scale-compensated children
                            foreach (int boneIdx in collapseBones)
                            {
                                var bone = renderJObj.RootJObj.GetJObjAtIndex(boneIdx);
                                if (bone != null)
                                    bone.Scale = new OpenTK.Mathematics.Vector3(0.0001f);
                                else
                                    Console.WriteLine($"Collapse bone {boneIdx} not found");
                            }
                            if (collapseBones.Count > 0)
                            {
                                renderJObj.RootJObj.RecalculateTransforms(null, true);
                                viewport.Render();
                            }

                            var positions = new List<OpenTK.Mathematics.Vector3>();
                            foreach (var j in renderJObj.RootJObj.Enumerate)
                                positions.Add(j.WorldTransform.ExtractTranslation());
                            if (positions.Count > 0)
                            {
                                OpenTK.Mathematics.Vector3 min = positions[0], max = positions[0];
                                foreach (var p in positions)
                                {
                                    min = OpenTK.Mathematics.Vector3.ComponentMin(min, p);
                                    max = OpenTK.Mathematics.Vector3.ComponentMax(max, p);
                                }
                                var center = (min + max) / 2f;
                                // robust radius: some imports carry far-flung
                                // helper bones that balloon the max distance
                                // and shrink the model to a speck (sm4sh
                                // models) -- use a high percentile instead
                                var dists = new List<float>();
                                foreach (var p in positions)
                                    dists.Add((p - center).Length);
                                dists.Sort();
                                float radius = dists[Math.Min(dists.Count - 1, (int)(dists.Count * 0.92f))];
                                // pad: meshes extend beyond bones (big-head swaps)
                                radius = Math.Max(radius * 1.45f, 8f);
                                viewport.Camera.FrameBoundingSphere(center, radius * 2f, 0);
                                // 3/4 view like the vanilla stock art -- a
                                // dead-on front view flattens snouts/faces
                                viewport.Camera.RotationYRadians = headShotYaw * (float)Math.PI / 180f;
                                viewport.Render();
                                Console.WriteLine($"Head-shot framing: center={center}, radius={radius:F1}, yaw={headShotYaw}, bones={positions.Count}");
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"Head-shot framing failed: {ex.Message}");
                        }
                    }

                    // Project the head bone into CSP pixel coordinates and write
                    // the sidecar. Mirrors TakeGLScreenShot's mapping exactly:
                    // framebuffer -> half-size resize -> center crop of
                    // CSPWidth/2 x CSPHeight/2 (with optional horizontal mirror
                    // applied before the crop).
                    if (headBoneIndex >= 0 && renderJObj != null)
                    {
                        try
                        {
                            var headJobj = renderJObj.RootJObj?.GetJObjAtIndex(headBoneIndex);
                            if (headJobj == null && renderJObj.RootJObj != null)
                            {
                                // swapped skeletons can be truncated; the
                                // topmost bone is a fair head approximation
                                float bestY = float.MinValue;
                                foreach (var j in renderJObj.RootJObj.Enumerate)
                                {
                                    var p = j.WorldTransform.ExtractTranslation();
                                    if (p.Y > bestY)
                                    {
                                        bestY = p.Y;
                                        headJobj = j;
                                    }
                                }
                                Console.WriteLine($"Head bone {headBoneIndex} not found; using topmost bone (y={bestY:F1})");
                            }
                            if (headJobj == null)
                            {
                                Console.WriteLine($"Head bone {headBoneIndex} not found in JOBJ tree");
                            }
                            else
                            {
                                OpenTK.Mathematics.Vector3 world = headJobj.WorldTransform.ExtractTranslation();
                                OpenTK.Mathematics.Matrix4 m = viewport.Camera.MvpMatrix;
                                // row-vector convention (matches GL.LoadMatrix usage)
                                float cx = world.X * m.M11 + world.Y * m.M21 + world.Z * m.M31 + m.M41;
                                float cy = world.X * m.M12 + world.Y * m.M22 + world.Z * m.M32 + m.M42;
                                float cw = world.X * m.M14 + world.Y * m.M24 + world.Z * m.M34 + m.M44;
                                float renderW = viewport.Camera.RenderWidth;
                                float renderH = viewport.Camera.RenderHeight;
                                float ndcX = cx / cw;
                                float ndcY = cy / cw;
                                float fbX = (ndcX * 0.5f + 0.5f) * renderW;
                                float fbYImg = (1f - (ndcY * 0.5f + 0.5f)) * renderH;
                                float hx = fbX / 2f;
                                float hy = fbYImg / 2f;
                                if (viewport.Camera.MirrorScreenshot)
                                    hx = renderW / 2f - hx;
                                float cspX = hx - (renderW - GUI.ViewportControl.CSPWidth) / 4f;
                                float cspY = hy - (renderH - GUI.ViewportControl.CSPHeight) / 4f;
                                int outW = GUI.ViewportControl.CSPWidth / 2;
                                int outH = GUI.ViewportControl.CSPHeight / 2;
                                string headJson = string.Format(
                                    System.Globalization.CultureInfo.InvariantCulture,
                                    "{{\"x\": {0:F2}, \"y\": {1:F2}, \"width\": {2}, \"height\": {3}, \"behindCamera\": {4}}}",
                                    cspX, cspY, outW, outH, cw <= 0 ? "true" : "false");
                                string headJsonPath = System.IO.Path.GetFullPath(outputFile) + ".head.json";
                                System.IO.File.WriteAllText(headJsonPath, headJson);
                                Console.WriteLine($"Head bone projected to CSP ({cspX:F1}, {cspY:F1}) -> {headJsonPath}");
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"Head bone projection failed: {ex.Message}");
                        }
                    }

                    // Set up the screenshot callback to capture the output
                    string actualOutputFile = System.IO.Path.GetFullPath(outputFile);
                    bool screenshotTaken = false;

                    viewport.ScreenshotTaken += (control) => {
                        Console.WriteLine("Screenshot callback triggered!");
                        screenshotTaken = true;
                    };

                    // Take screenshot using the EXACT same method as GUI
                    Console.WriteLine("Taking screenshot using native method...");
                    viewport.Screenshot();

                    // Wait for screenshot to complete
                    int attempts = 0;
                    while (!screenshotTaken && attempts < 10)
                    {
                        System.Threading.Thread.Sleep(500);
                        System.Windows.Forms.Application.DoEvents(); // Process events
                        attempts++;
                    }

                    if (screenshotTaken)
                    {
                        // The screenshot should be saved in the default location
                        string datDir = System.IO.Path.GetDirectoryName(System.IO.Path.GetFullPath(datFile));
                        string defaultPath = System.IO.Path.Combine(datDir, "csp_" + System.IO.Path.GetFileNameWithoutExtension(datFile) + ".png");

                        if (System.IO.File.Exists(defaultPath))
                        {
                            if (System.IO.File.Exists(actualOutputFile))
                                System.IO.File.Delete(actualOutputFile);
                            System.IO.File.Move(defaultPath, actualOutputFile);
                            Console.WriteLine($"CSP saved to: {actualOutputFile}");
                        }
                        else
                        {
                            Console.WriteLine($"Default CSP file not found at: {defaultPath}");
                        }
                    }
                    else
                    {
                        Console.WriteLine("Screenshot was not taken successfully");
                    }
                }

                Console.WriteLine("CSP generation completed successfully!");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"EXCEPTION CAUGHT: Error generating CSP: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Console.WriteLine($"Inner exception: {ex.InnerException?.Message}");
                Environment.Exit(1);
            }
            finally
            {
                Console.WriteLine("RunCSPGeneration finally block reached");
            }
        }

        /// <summary>
        /// Dump per-bone world transforms (and positions) for an animation
        /// frame as JSON. Usage:
        ///   --dump-pose <costume.dat> <PlXxAJ.dat> <animSubstring> <out.json> [frame]
        /// </summary>
        // --accessory <costume.dat> <accessory.smd> <attachBone> <dynamics.json> <out.dat>
        // Adds a mexCostume physics accessory (akaneia m-ex wiki): the model
        // gets its own joint chains, attaches to AttachBone at runtime, and
        // the game runs real cloth dynamics over the chains in dynamics.json
        // (accessory-LOCAL bone indices; params copied from a vanilla cape).
        static void RunAddAccessory(string[] args)
        {
            Thread.CurrentThread.CurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
            if (args.Length < 6)
            {
                Console.WriteLine("Usage: --accessory <costume.dat> <accessory.smd> <attachBone> <dynamics.json> <out.dat>");
                return;
            }
            try
            {
                string datFile = args[1], modelFile = args[2];
                int attachBone = int.Parse(args[3], System.Globalization.CultureInfo.InvariantCulture);
                string dynJson = args[4], outFile = args[5];

                var file = new HSDRawFile(datFile);

                HSD_JOBJ accRoot = ImportModelHeadless(modelFile, null);
                if (accRoot == null)
                {
                    Console.WriteLine("FAILED: accessory model import returned null");
                    return;
                }

                int nDobj = 0;
                foreach (var j in accRoot.TreeList)
                {
                    var dobj = j.Dobj;
                    while (dobj != null) { nDobj++; dobj = dobj.Next; }
                }
                Console.WriteLine($"Accessory: {accRoot.TreeList.Count} joints, {nDobj} dobjs");
                byte[] allIdx = new byte[nDobj];
                for (int i = 0; i < nDobj; i++) allIdx[i] = (byte)i;

                HSDRaw.Melee.Pl.SBM_LookupTable MakeTable(byte[] entries)
                {
                    var e = new HSDRaw.Melee.Pl.SBM_LookupEntry { Entries = entries };
                    var t = new HSDRaw.Melee.Pl.SBM_LookupTable();
                    t.LookupEntries = new HSDArrayAccessor<HSDRaw.Melee.Pl.SBM_LookupEntry> { Array = new[] { e } };
                    return t;
                }
                var lookup = new HSDRaw.Melee.Pl.SBM_CostumeLookupTable
                {
                    // no separate low poly: the wiki says use the high poly
                    // indices in the low poly table
                    HighPoly = new HSDArrayAccessor<HSDRaw.Melee.Pl.SBM_LookupTable> { Array = new[] { MakeTable(allIdx) } },
                    LowPoly = new HSDArrayAccessor<HSDRaw.Melee.Pl.SBM_LookupTable> { Array = new[] { MakeTable(allIdx) } },
                    MetalPoly = new HSDArrayAccessor<HSDRaw.Melee.Pl.SBM_LookupTable> { Array = new[] { MakeTable(allIdx) } },
                };

                var descs = new List<HSDRaw.Melee.Pl.SBM_DynamicDesc>();
                using (var doc = System.Text.Json.JsonDocument.Parse(System.IO.File.ReadAllText(dynJson)))
                {
                    foreach (var chain in doc.RootElement.EnumerateArray())
                    {
                        var desc = new HSDRaw.Melee.Pl.SBM_DynamicDesc
                        {
                            BoneIndex = chain.GetProperty("bone").GetInt32(),
                            PARAM1 = chain.GetProperty("PARAM1").GetSingle(),
                            PARAM2 = chain.GetProperty("PARAM2").GetSingle(),
                            PARAM3 = chain.GetProperty("PARAM3").GetSingle(),
                        };
                        var plist = new List<HSDRaw.Melee.Pl.SBM_DynamicParams>();
                        foreach (var joint in chain.GetProperty("joints").EnumerateArray())
                        {
                            float[] v = joint.EnumerateArray().Select(x => x.GetSingle()).ToArray();
                            plist.Add(new HSDRaw.Melee.Pl.SBM_DynamicParams
                            {
                                PARAM1 = v[0], PARAM2 = v[1],
                                RotX = v[2], RotY = v[3], RotZ = v[4], RotW = v[5],
                                RotLimit = v[6], PARAM8 = v[7], PARAM9 = v[8],
                                PARAM10 = v[9], PARAM11 = v[10], PARAM12 = v[11],
                                PARAM13 = v[12], RotMomentumSpeed = v[13],
                                MaxAngleChange = v[14],
                            });
                        }
                        desc.Parameters = plist.ToArray();
                        descs.Add(desc);
                    }
                }
                Console.WriteLine($"Dynamics: {descs.Count} chains");

                var acc = new HSDRaw.MEX.MEX_CostumeAccessory
                {
                    RootJoint = accRoot,
                    AttachBone = attachBone,
                    DynamicCount = descs.Count,
                    LookupCount = 1,
                    LookupTable = lookup,
                    DynamicHitCount = 0,
                };
                acc.DynamicDef = new HSDFixedLengthPointerArrayAccessor<HSDRaw.Melee.Pl.SBM_DynamicDesc> { Array = descs.ToArray() };

                // do NOT call New(): it creates EMPTY CostumeVisLookup /
                // CostumeMatLookup overrides for the MAIN model (count 0,
                // null table) - a runtime that null-checks the outer pointer
                // then derefs the table crashes at costume load. Leave both
                // null so the loader skips the override path entirely.
                var sym = new HSDRaw.MEX.MEX_CostumeSymbol();
                // the accessor base ctor invokes New() which creates EMPTY main-model
                // lookup overrides (count 0 / null table) - the runtime derefs the
                // null table at costume load. Null them out explicitly.
                sym.CostumeVisLookup = null;
                sym.CostumeMatLookup = null;
                sym.AccessoryCount = 1;
                sym.Accessories = new HSDFixedLengthPointerArrayAccessor<HSDRaw.MEX.MEX_CostumeAccessory> { Array = new[] { acc } };

                // replace an existing mexCostume root if present
                for (int i = file.Roots.Count - 1; i >= 0; i--)
                    if (file.Roots[i].Name == "mexCostume")
                        file.Roots.RemoveAt(i);
                file.Roots.Add(new HSDRootNode { Name = "mexCostume", Data = sym });
                file.Save(outFile);
                Console.WriteLine($"SUCCESS: wrote {outFile} (attach bone {attachBone}, {descs.Count} dynamic chains, {nDobj} dobjs)");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"FAILED: {ex.Message}");
                Console.WriteLine(ex.StackTrace);
            }
        }

        static void RunDumpPose(string[] args)
        {
            if (args.Length < 5)
            {
                Console.WriteLine("Usage: --dump-pose <costume.dat> <aj.dat> <animSubstring> <out.json> [frame]");
                Environment.Exit(1);
                return;
            }

            Thread.CurrentThread.CurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
            string datFile = args[1];
            string ajFile = args[2];
            string animSub = args[3];
            string outFile = args[4];
            float frame = args.Length > 5 ? float.Parse(args[5]) : 0f;

            var rawFile = new HSDRawFile(datFile);
            HSD_JOBJ jobj = null;
            foreach (var r in rawFile.Roots)
            {
                if (r.Name != null && r.Name.EndsWith("_joint") &&
                    !r.Name.Contains("matanim") && r.Data is HSD_JOBJ j)
                {
                    jobj = j;
                    break;
                }
            }
            if (jobj == null)
            {
                Console.WriteLine("ERROR: no joint root found");
                Environment.Exit(1);
                return;
            }

            var root = new HSDRawViewer.Rendering.Models.LiveJObj(jobj);
            string symbol = "(bind pose)";

            // animSubstring "bind" = dump the bind pose itself (no animation).
            // LiveJObj world transforms include bone scale + classical-scaling
            // semantics that text formats (SMD) cannot carry.
            if (animSub != "bind")
            {
                var aj = new HSDRaw.Tools.Melee.FighterAJManager(System.IO.File.ReadAllBytes(ajFile));
                symbol = null;
                foreach (var s in aj.GetAnimationSymbols())
                {
                    if (s != null && s.Contains(animSub))
                    {
                        symbol = s;
                        break;
                    }
                }
                if (symbol == null)
                {
                    Console.WriteLine($"ERROR: no animation symbol containing '{animSub}'");
                    Environment.Exit(1);
                    return;
                }
                Console.WriteLine($"Using animation: {symbol}");

                var animFile = new HSDRawFile(aj.GetAnimationData(symbol));
                var tree = animFile.Roots[0].Data as HSDRaw.Common.Animation.HSD_FigaTree;
                if (tree == null)
                {
                    Console.WriteLine("ERROR: animation is not a FigaTree");
                    Environment.Exit(1);
                    return;
                }

                var jam = new HSDRawViewer.Rendering.JointAnimManager(tree);
                jam.ApplyAnimation(root, frame);
            }
            root.RecalculateTransforms(null, true);

            var sb = new System.Text.StringBuilder();
            sb.Append("{\"symbol\":\"" + symbol + "\",\"frame\":" + frame + ",\"bones\":[");
            bool first = true;
            for (int i = 0; i < root.JointCount; i++)
            {
                var j = root.GetJObjAtIndex(i);
                var m = j.WorldTransform;
                if (!first) sb.Append(',');
                first = false;
                sb.Append($"{{\"index\":{i},\"pos\":[{m.M41},{m.M42},{m.M43}],");
                sb.Append($"\"matrix\":[{m.M11},{m.M12},{m.M13},{m.M14},");
                sb.Append($"{m.M21},{m.M22},{m.M23},{m.M24},");
                sb.Append($"{m.M31},{m.M32},{m.M33},{m.M34},");
                sb.Append($"{m.M41},{m.M42},{m.M43},{m.M44}]}}");
            }
            sb.Append("]}");
            System.IO.File.WriteAllText(outFile, sb.ToString());
            Console.WriteLine($"SUCCESS: wrote {root.JointCount} bone transforms to {outFile}");
        }

        /// <summary>
        /// Run model export/import operations in headless mode.
        /// Usage:
        ///   Export: HSDRawViewer.exe --model export [dat_file] [jobj_path] [output.dae]
        ///   Import: HSDRawViewer.exe --model import [dat_file] [jobj_path] [model.dae] [output.dat]
        /// </summary>
        static void RunModelOperation(string[] args)
        {
            try
            {
                if (args.Length < 5)
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --model export <dat_file> <jobj_path> <output.dae>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --model import <dat_file> <jobj_path> <model.dae> <output.dat>");
                    Console.WriteLine();
                    Console.WriteLine("Example paths:");
                    Console.WriteLine("  ftDataFalco/Articles/Articles_1/Model_/RootModelJoint");
                    return;
                }

                string operation = args[1]; // "export" or "import"

                if (operation == "export")
                {
                    // HSDRawViewer.exe --model export <dat_file> <jobj_path> <output.dae>
                    if (args.Length < 5)
                    {
                        Console.WriteLine("Export requires: <dat_file> <jobj_path> <output.dae>");
                        return;
                    }

                    string datFile = args[2];
                    string jobjPath = args[3];
                    string outputFile = args[4];

                    Console.WriteLine($"Exporting model from: {datFile}");
                    Console.WriteLine($"JOBJ path: {jobjPath}");
                    Console.WriteLine($"Output file: {outputFile}");

                    // Load DAT
                    var rawFile = new HSDRawFile(datFile);

                    // Navigate to JOBJ
                    HSD_JOBJ jobj = NavigateToJOBJ(rawFile, jobjPath);
                    if (jobj == null)
                    {
                        Console.WriteLine($"ERROR: Could not find JOBJ at path: {jobjPath}");
                        Environment.Exit(1);
                        return;
                    }

                    Console.WriteLine("JOBJ found, exporting...");

                    // Export using existing ModelExporter
                    var settings = new ModelExportSettings();
                    var jointMap = new HSDRawViewer.Tools.Animation.JointMap();
                    ModelExporter.ExportFile(outputFile, jobj, settings, jointMap);

                    Console.WriteLine($"SUCCESS: Exported model to: {outputFile}");
                }
                else if (operation == "import")
                {
                    // HSDRawViewer.exe --model import <dat_file> <jobj_path> <model.dae> <output.dat>
                    if (args.Length < 6)
                    {
                        Console.WriteLine("Import requires: <dat_file> <jobj_path> <model.dae> <output.dat>");
                        return;
                    }

                    string datFile = args[2];
                    string jobjPath = args[3];
                    string modelFile = args[4];
                    string outputDat = args[5];

                    Console.WriteLine($"Importing model into: {datFile}");
                    Console.WriteLine($"JOBJ path: {jobjPath}");
                    Console.WriteLine($"Model file: {modelFile}");
                    Console.WriteLine($"Output DAT: {outputDat}");

                    // Load DAT
                    var rawFile = new HSDRawFile(datFile);

                    // Get the parent and property info for replacement
                    var navResult = NavigateToJOBJWithParent(rawFile, jobjPath);
                    if (navResult.jobj == null)
                    {
                        Console.WriteLine($"ERROR: Could not find JOBJ at path: {jobjPath}");
                        Environment.Exit(1);
                        return;
                    }

                    Console.WriteLine("JOBJ found, importing model...");

                    // Import model headlessly
                    HSD_JOBJ newJobj = ImportModelHeadless(modelFile, navResult.jobj);
                    if (newJobj == null)
                    {
                        Console.WriteLine("ERROR: Failed to import model");
                        Environment.Exit(1);
                        return;
                    }

                    Console.WriteLine("Model imported, replacing structure...");

                    // Replace the JOBJ structure
                    navResult.jobj._s.SetFromStruct(newJobj._s);

                    // Optional: neutralize the matanim root. The vanilla matanim
                    // tree binds texture-swap anims against the vanilla DObj
                    // layout; bound against a generated model's layout it crashes
                    // the game at match load. The rename must mutate the PREFIX
                    // while KEEPING the "_matanim_joint" suffix: m-ex's costume
                    // table needs a symbol ending in the suffix (empty -> frame-1
                    // hang) but the game's own lookup derives the name from the
                    // joint symbol's prefix (miss -> no matanim -> healthy).
                    // Removing the root entirely also hangs. All verified in-game.
                    if (args.Length > 6 && args[6] == "--strip-matanim")
                    {
                        const string suffix = "_matanim_joint";
                        foreach (var r in rawFile.Roots)
                        {
                            if (r.Name != null && r.Name.EndsWith(suffix) &&
                                r.Name.Length > suffix.Length)
                            {
                                char[] chars = r.Name.ToCharArray();
                                int i = r.Name.Length - suffix.Length - 1;
                                chars[i] = chars[i] == 'X' ? 'Y' : 'X';
                                r.Name = new string(chars);
                                Console.WriteLine($"Neutralized matanim root -> {r.Name}");
                            }
                        }
                    }

                    // Save modified DAT
                    rawFile.Save(outputDat);

                    Console.WriteLine($"SUCCESS: Imported model and saved to: {outputDat}");
                }
                else
                {
                    Console.WriteLine($"Unknown operation: {operation}");
                    Console.WriteLine("Use 'export' or 'import'");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Model operation failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Run texture export/import operations in headless mode.
        /// Usage:
        ///   Export: HSDRawViewer.exe --texture export [dat_file] [node_path] [tex_index] [output.png]
        ///   Import: HSDRawViewer.exe --texture import [dat_file] [node_path] [tex_index] [input.png] [output.dat]
        /// </summary>
        static void RunTextureOperation(string[] args)
        {
            try
            {
                if (args.Length < 6)
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --texture export <dat_file> <node_path> <tex_index> <output.png>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --texture import <dat_file> <node_path> <tex_index> <input.png> <output.dat>");
                    Console.WriteLine();
                    Console.WriteLine("Example path: effFoxDataTable/Models_4_/RootJoint");
                    return;
                }

                string operation = args[1]; // "export" or "import"

                if (operation == "export")
                {
                    // HSDRawViewer.exe --texture export <dat_file> <node_path> <tex_index> <output.png>
                    if (args.Length < 6)
                    {
                        Console.WriteLine("Export requires: <dat_file> <node_path> <tex_index> <output.png>");
                        return;
                    }

                    string datFile = args[2];
                    string nodePath = args[3];
                    int texIndex = int.Parse(args[4]);
                    string outputFile = args[5];

                    Console.WriteLine($"Exporting texture from: {datFile}");
                    Console.WriteLine($"Node path: {nodePath}");
                    Console.WriteLine($"Texture index: {texIndex}");
                    Console.WriteLine($"Output file: {outputFile}");

                    // Load DAT
                    var rawFile = new HSDRawFile(datFile);

                    // Navigate to the node and get texture
                    var tobj = NavigateToTexture(rawFile, nodePath, texIndex);
                    if (tobj == null)
                    {
                        Console.WriteLine($"ERROR: Could not find texture at path: {nodePath}, index: {texIndex}");
                        Environment.Exit(1);
                        return;
                    }

                    Console.WriteLine("Texture found, exporting...");

                    // Export texture to PNG
                    using (var image = tobj.ToImage())
                    using (var fs = new System.IO.FileStream(outputFile, System.IO.FileMode.Create))
                    {
                        image.Save(fs, new PngEncoder());
                    }

                    Console.WriteLine($"SUCCESS: Exported texture to: {outputFile}");
                }
                else if (operation == "import")
                {
                    // HSDRawViewer.exe --texture import <dat_file> <node_path> <tex_index> <input.png> <output.dat>
                    if (args.Length < 7)
                    {
                        Console.WriteLine("Import requires: <dat_file> <node_path> <tex_index> <input.png> <output.dat>");
                        return;
                    }

                    string datFile = args[2];
                    string nodePath = args[3];
                    int texIndex = int.Parse(args[4]);
                    string inputPng = args[5];
                    string outputDat = args[6];

                    Console.WriteLine($"Importing texture into: {datFile}");
                    Console.WriteLine($"Node path: {nodePath}");
                    Console.WriteLine($"Texture index: {texIndex}");
                    Console.WriteLine($"Input PNG: {inputPng}");
                    Console.WriteLine($"Output DAT: {outputDat}");

                    // Load DAT
                    var rawFile = new HSDRawFile(datFile);

                    // Navigate to the node and get texture
                    var tobj = NavigateToTexture(rawFile, nodePath, texIndex);
                    if (tobj == null)
                    {
                        Console.WriteLine($"ERROR: Could not find texture at path: {nodePath}, index: {texIndex}");
                        Environment.Exit(1);
                        return;
                    }

                    Console.WriteLine("Texture found, importing...");

                    // Load the PNG image
                    using (var image = SixLabors.ImageSharp.Image.Load<SixLabors.ImageSharp.PixelFormats.Bgra32>(inputPng))
                    {
                        // Inject the bitmap into the texture object
                        // Use the original texture's format and palette format
                        var imgFormat = tobj.ImageData.Format;
                        var palFormat = tobj.TlutData?.Format ?? HSDRaw.GX.GXTlutFmt.IA8;
                        tobj.InjectBitmap(image, imgFormat, palFormat);
                    }

                    // Save modified DAT
                    rawFile.Save(outputDat);

                    Console.WriteLine($"SUCCESS: Imported texture and saved to: {outputDat}");
                }
                else
                {
                    Console.WriteLine($"Unknown operation: {operation}");
                    Console.WriteLine("Use 'export' or 'import'");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Texture operation failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Dump every TOBJ found on the given JOBJ subtree, recursively, into outDir.
        /// Returns a flat list of manifest entries (one per dumped texture).
        /// </summary>
        static List<Dictionary<string, object>> DumpJobjTextures(HSDRaw.Common.HSD_JOBJ root, string outDir, string prefix)
        {
            var entries = new List<Dictionary<string, object>>();
            if (root == null) return entries;

            int jointIndex = 0;
            // Walk every joint in the tree (depth-first via Children flattened by enumerator below)
            void Walk(HSDRaw.Common.HSD_JOBJ jobj, List<int> path)
            {
                int dobjIdx = 0;
                var dobj = jobj.Dobj;
                while (dobj != null)
                {
                    var mobj = dobj.Mobj;
                    var tobj = mobj?.Textures;
                    int tobjIdx = 0;
                    while (tobj != null)
                    {
                        string filename = $"{prefix}_j{string.Join("-", path)}_d{dobjIdx}_t{tobjIdx}.png";
                        try
                        {
                            using var img = tobj.ToImage();
                            using var fs = new System.IO.FileStream(System.IO.Path.Combine(outDir, filename), System.IO.FileMode.Create);
                            img.Save(fs, new PngEncoder());

                            entries.Add(new Dictionary<string, object>
                            {
                                ["filename"] = filename,
                                ["joint_path"] = string.Join("-", path),
                                ["dobj_index"] = dobjIdx,
                                ["tobj_index"] = tobjIdx,
                            });
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"  Skipped texture {filename}: {ex.Message}");
                        }
                        tobj = tobj.Next;
                        tobjIdx++;
                    }
                    dobj = dobj.Next;
                    dobjIdx++;
                }

                int childIdx = 0;
                var child = jobj.Child;
                while (child != null)
                {
                    var nextPath = new List<int>(path) { childIdx };
                    Walk(child, nextPath);
                    child = child.Next;
                    childIdx++;
                }
            }

            Walk(root, new List<int> { jointIndex });
            return entries;
        }

        /// <summary>
        /// Dump CSS icon textures from a CSS data file (MnSlChr.dat / .usd / mexSelectChr.dat).
        /// Usage:
        ///   HSDRawViewer.exe --css-icons export <dat_file> <output_dir>
        ///
        /// Output:
        ///   - PNG files for each icon TOBJ
        ///   - manifest.json describing format detected and per-file metadata
        /// </summary>
        /// <summary>
        /// Export or import CSS background model/animation from MnSlChr.dat/.usd.
        /// Export: HSDRawViewer.exe --css-bg export <mnslchr.dat> <output_dir>
        /// Import: HSDRawViewer.exe --css-bg import <project_mnslchr.usd> <background.dat> <output.usd>
        /// </summary>
        static void RunCssBgOperation(string[] args)
        {
            try
            {
                if (args.Length < 2)
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --css-bg export <mnslchr.dat> <output_dir>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --css-bg import <project.usd> <background.dat> <output.usd>");
                    return;
                }

                string subCommand = args[1].ToLower();

                if (subCommand == "export")
                {
                    if (args.Length < 4)
                    {
                        Console.WriteLine("Usage: HSDRawViewer.exe --css-bg export <mnslchr.dat> <output_dir>");
                        return;
                    }

                    string datFile = args[2];
                    string outDir = args[3];
                    System.IO.Directory.CreateDirectory(outDir);

                    Console.WriteLine($"Loading: {datFile}");
                    var rawFile = new HSDRawFile(datFile);

                    Console.WriteLine($"Roots in file: {rawFile.Roots.Count}");
                    foreach (var r in rawFile.Roots)
                        Console.WriteLine($"  - {r.Name} ({r.Data?.GetType().Name})");

                    var vanillaRoot = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Mn.SBM_SelectChrDataTable);
                    if (vanillaRoot == null)
                    {
                        Console.WriteLine("ERROR: No SBM_SelectChrDataTable root found in DAT");
                        Environment.Exit(1);
                        return;
                    }

                    var tb = (HSDRaw.Melee.Mn.SBM_SelectChrDataTable)vanillaRoot.Data;

                    if (tb.BackgroundModel == null)
                    {
                        Console.WriteLine("ERROR: SBM_SelectChrDataTable has no BackgroundModel (offset 0x10)");
                        Environment.Exit(1);
                        return;
                    }

                    var bgFile = new HSDRawFile();
                    bgFile.Roots.Add(new HSDRootNode() { Name = "bg_model", Data = tb.BackgroundModel });
                    if (tb.BackgroundAnimation != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_anim", Data = tb.BackgroundAnimation });
                    if (tb.BackgroundMaterialAnimation != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_matanim", Data = tb.BackgroundMaterialAnimation });
                    if (tb.Camera != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_camera", Data = tb.Camera });
                    if (tb.Light1 != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_light1", Data = tb.Light1 });
                    if (tb.Light2 != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_light2", Data = tb.Light2 });
                    if (tb.Fog != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_fog", Data = tb.Fog });

                    string bgDatPath = System.IO.Path.Combine(outDir, "background.dat");
                    bgFile.Save(bgDatPath);
                    Console.WriteLine($"Saved background.dat with {bgFile.Roots.Count} roots");

                    var manifest = new Dictionary<string, object>
                    {
                        ["format"] = "css_background",
                        ["source_file"] = System.IO.Path.GetFileName(datFile),
                        ["roots"] = bgFile.Roots.Count,
                        ["has_model"] = true,
                        ["has_anim"] = tb.BackgroundAnimation != null,
                        ["has_matanim"] = tb.BackgroundMaterialAnimation != null,
                        ["has_scene"] = tb.Camera != null,
                    };
                    System.IO.File.WriteAllText(
                        System.IO.Path.Combine(outDir, "manifest.json"),
                        JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true })
                    );

                    Console.WriteLine($"SUCCESS: Exported CSS background to {outDir}");
                }
                else if (subCommand == "import")
                {
                    if (args.Length < 5)
                    {
                        Console.WriteLine("Usage: HSDRawViewer.exe --css-bg import <project.usd> <background.dat> <output.usd>");
                        return;
                    }

                    string projectUsd = args[2];
                    string bgDatPath = args[3];
                    string outputUsd = args[4];

                    Console.WriteLine($"Loading project: {projectUsd}");
                    var rawFile = new HSDRawFile(projectUsd);

                    var vanillaRoot = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Mn.SBM_SelectChrDataTable);
                    if (vanillaRoot == null)
                    {
                        Console.WriteLine("ERROR: No SBM_SelectChrDataTable root found in project USD");
                        Environment.Exit(1);
                        return;
                    }

                    var tb = (HSDRaw.Melee.Mn.SBM_SelectChrDataTable)vanillaRoot.Data;

                    Console.WriteLine($"Loading background: {bgDatPath}");
                    var bgFile = new HSDRawFile(bgDatPath);

                    Console.WriteLine($"Background file roots: {bgFile.Roots.Count}");
                    foreach (var r in bgFile.Roots)
                        Console.WriteLine($"  - {r.Name} ({r.Data?.GetType().Name})");

                    var modelRoot = bgFile.Roots.Find(r => r.Name == "bg_model");
                    var animRoot = bgFile.Roots.Find(r => r.Name == "bg_anim");
                    var matAnimRoot = bgFile.Roots.Find(r => r.Name == "bg_matanim");

                    if (modelRoot == null)
                    {
                        Console.WriteLine("ERROR: background.dat missing 'bg_model' root");
                        Environment.Exit(1);
                        return;
                    }

                    tb.BackgroundModel = new HSD_JOBJ() { _s = modelRoot.Data._s };
                    tb.BackgroundAnimation = animRoot != null
                        ? new HSDRaw.Common.Animation.HSD_AnimJoint() { _s = animRoot.Data._s }
                        : null;
                    tb.BackgroundMaterialAnimation = matAnimRoot != null
                        ? new HSDRaw.Common.Animation.HSD_MatAnimJoint() { _s = matAnimRoot.Data._s }
                        : null;

                    bool includeScene = args.Any(a => a == "--include-scene");
                    if (includeScene)
                    {
                        var cameraRoot = bgFile.Roots.Find(r => r.Name == "bg_camera");
                        var light1Root = bgFile.Roots.Find(r => r.Name == "bg_light1");
                        var light2Root = bgFile.Roots.Find(r => r.Name == "bg_light2");
                        var fogRoot = bgFile.Roots.Find(r => r.Name == "bg_fog");

                        if (cameraRoot != null)
                            tb.Camera = new HSD_Camera() { _s = cameraRoot.Data._s };
                        if (light1Root != null)
                            tb.Light1 = new HSD_LOBJ() { _s = light1Root.Data._s };
                        if (light2Root != null)
                            tb.Light2 = new HSD_LOBJ() { _s = light2Root.Data._s };
                        if (fogRoot != null)
                            tb.Fog = new HSD_FogDesc() { _s = fogRoot.Data._s };
                        Console.WriteLine("Applied scene settings (camera, lights, fog)");
                    }

                    Console.WriteLine($"Saving to: {outputUsd}");
                    rawFile.Save(outputUsd);

                    Console.WriteLine($"SUCCESS: Imported CSS background into {outputUsd}");
                }
                else
                {
                    Console.WriteLine($"Unknown css-bg sub-command: {subCommand}");
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --css-bg export <mnslchr.dat> <output_dir>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --css-bg import <project.usd> <background.dat> <output.usd>");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: CSS background operation failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// CSS doors texture export/import.
        ///   Export: HSDRawViewer.exe --css-doors export mnslchr.usd output_dir
        ///   Import: HSDRawViewer.exe --css-doors import mnslchr.usd door.png output.usd
        /// </summary>
        /// <summary>
        /// Collect all TOBJs from a JOBJ tree, returning (jointIndex, tobj) pairs
        /// </summary>
        static List<(int jointIdx, HSD_TOBJ tobj)> CollectAllTextures(HSD_JOBJ root)
        {
            var result = new List<(int, HSD_TOBJ)>();
            var joints = root.TreeList;
            for (int ji = 0; ji < joints.Count; ji++)
            {
                var jobj = joints[ji];
                if (jobj.Dobj == null) continue;
                foreach (var dobj in jobj.Dobj.List)
                {
                    if (dobj.Mobj?.Textures == null) continue;
                    foreach (var tobj in dobj.Mobj.Textures.List)
                    {
                        if (tobj.ImageData != null)
                            result.Add((ji, tobj));
                    }
                }
            }
            return result;
        }

        static void RunCssDoorsOperation(string[] args)
        {
            try
            {
                if (args.Length < 2)
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --css-doors export <mnslchr.usd> <output_dir>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --css-doors import <mnslchr.usd> <door.png> <output.usd>");
                    return;
                }

                string subCommand = args[1].ToLower();

                if (subCommand == "export")
                {
                    if (args.Length < 4)
                    {
                        Console.WriteLine("Usage: HSDRawViewer.exe --css-doors export <mnslchr.usd> <output_dir>");
                        return;
                    }

                    string datFile = args[2];
                    string outDir = args[3];
                    System.IO.Directory.CreateDirectory(outDir);

                    Console.WriteLine($"Loading: {datFile}");
                    var rawFile = new HSDRawFile(datFile);

                    var root = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Mn.SBM_SelectChrDataTable);
                    if (root == null)
                    {
                        Console.WriteLine("ERROR: No SBM_SelectChrDataTable root found");
                        Environment.Exit(1);
                        return;
                    }

                    var tb = (HSDRaw.Melee.Mn.SBM_SelectChrDataTable)root.Data;

                    // Dump ALL textures from MenuModel so we can identify doors
                    var allTex = CollectAllTextures(tb.MenuModel);
                    Console.WriteLine($"Found {allTex.Count} textures in MenuModel:");
                    int exported = 0;
                    foreach (var (ji, tobj) in allTex)
                    {
                        string fmt = tobj.ImageData.Format.ToString();
                        int w = tobj.ImageData.Width;
                        int h = tobj.ImageData.Height;
                        string outPath = System.IO.Path.Combine(outDir, $"menu_j{ji}_{w}x{h}_{fmt}_{exported}.png");
                        using (var image = tobj.ToImage())
                        using (var fs = new System.IO.FileStream(outPath, System.IO.FileMode.Create))
                        {
                            image.Save(fs, new PngEncoder());
                        }
                        Console.WriteLine($"  Joint {ji}: {w}x{h} {fmt} -> {System.IO.Path.GetFileName(outPath)}");
                        exported++;
                    }
                    Console.WriteLine($"SUCCESS: Exported {exported} textures");
                }
                else if (subCommand == "import")
                {
                    if (args.Length < 5)
                    {
                        Console.WriteLine("Usage: HSDRawViewer.exe --css-doors import <mnslchr.usd> <door.png> <output.usd>");
                        return;
                    }

                    string datFile = args[2];
                    string doorPng = args[3];
                    string outputDat = args[4];

                    Console.WriteLine($"Loading: {datFile}");
                    var rawFile = new HSDRawFile(datFile);

                    var root = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Mn.SBM_SelectChrDataTable);
                    if (root == null)
                    {
                        Console.WriteLine("ERROR: No SBM_SelectChrDataTable root found");
                        Environment.Exit(1);
                        return;
                    }

                    var tb = (HSDRaw.Melee.Mn.SBM_SelectChrDataTable)root.Data;

                    // Load the user's door image
                    using var userImage = SixLabors.ImageSharp.Image.Load<SixLabors.ImageSharp.PixelFormats.Bgra32>(doorPng);

                    // Find door textures: look for the characteristic diagonal-alpha texture
                    // Door textures have partial transparency (alpha < 255 in some pixels, > 0 in others)
                    // and are the same size repeated across ports.
                    // Strategy: find all unique-sized textures that have mixed alpha values
                    var allTex = CollectAllTextures(tb.MenuModel);
                    Console.WriteLine($"Found {allTex.Count} textures in MenuModel, searching for door textures...");

                    // Group textures by size+format (shared textures have same dimensions and format)
                    var byKey = new Dictionary<string, List<(int ji, HSD_TOBJ tobj)>>();
                    foreach (var entry in allTex)
                    {
                        var key = $"{entry.tobj.ImageData.Width}x{entry.tobj.ImageData.Height}_{entry.tobj.ImageData.Format}";
                        if (!byKey.ContainsKey(key))
                            byKey[key] = new List<(int, HSD_TOBJ)>();
                        byKey[key].Add(entry);
                    }

                    // Door textures are 128x200 IA8 at joints 138/139, 146/147, 154/155, 162/163
                    List<HSD_TOBJ> doorTobjs = new();
                    HSD_TOBJ doorTobj = null;

                    foreach (var (ji, tobj) in allTex)
                    {
                        if (tobj.ImageData.Width == 128 && tobj.ImageData.Height == 200)
                        {
                            doorTobjs.Add(tobj);
                            doorTobj ??= tobj;
                            Console.WriteLine($"  Door texture found at joint {ji}: {tobj.ImageData.Format}");
                        }
                    }

                    if (doorTobj == null)
                    {
                        Console.WriteLine("ERROR: No 128x200 door textures found. Try 'export' to inspect textures manually.");
                        Environment.Exit(1);
                        return;
                    }

                    Console.WriteLine($"Found {doorTobjs.Count} door textures to replace");

                    // Extract alpha mask from original
                    using var originalImage = doorTobj.ToImage();
                    using var resizedUser = userImage.Clone(ctx => ctx.Resize(originalImage.Width, originalImage.Height));

                    // Apply original alpha mask to user's image
                    resizedUser.ProcessPixelRows(originalImage, (userAccessor, origAccessor) =>
                    {
                        for (int y = 0; y < userAccessor.Height; y++)
                        {
                            var userRow = userAccessor.GetRowSpan(y);
                            var origRow = origAccessor.GetRowSpan(y);
                            for (int x = 0; x < userRow.Length; x++)
                            {
                                userRow[x] = new SixLabors.ImageSharp.PixelFormats.Bgra32(
                                    userRow[x].R, userRow[x].G, userRow[x].B, origRow[x].A);
                            }
                        }
                    });

                    // RGB5A3: same 2 bytes/pixel as IA8, but with color support
                    var imgFormat = HSDRaw.GX.GXTexFmt.RGB5A3;
                    var palFormat = HSDRaw.GX.GXTlutFmt.IA8;
                    Console.WriteLine($"Encoding as RGB5A3 (2 bytes/pixel, color)");

                    foreach (var tobj in doorTobjs)
                    {
                        tobj.InjectBitmap(resizedUser, imgFormat, palFormat);
                    }

                    rawFile.Save(outputDat);
                    Console.WriteLine($"SUCCESS: Replaced {doorTobjs.Count} door textures as RGB5A3, saved to: {outputDat}");
                }
                else
                {
                    Console.WriteLine($"Unknown css-doors sub-command: {subCommand}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: CSS doors operation failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Collect all textures from every model group under a stage DAT's
        /// map_head root. Returns a flat list in stable traversal order with
        /// the owning group index.
        /// </summary>
        static List<(int group, HSD_TOBJ tobj)> CollectStageTextures(HSDRawFile rawFile)
        {
            var root = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Gr.SBM_Map_Head);
            if (root == null)
                return null;

            var head = (HSDRaw.Melee.Gr.SBM_Map_Head)root.Data;
            var result = new List<(int, HSD_TOBJ)>();
            var groups = head.ModelGroups?.Array;
            if (groups == null)
                return result;

            for (int g = 0; g < groups.Length; g++)
            {
                var rootNode = groups[g]?.RootNode;
                if (rootNode == null)
                    continue;
                foreach (var (_, tobj) in CollectAllTextures(rootNode))
                    result.Add((g, tobj));
            }
            return result;
        }

        /// <summary>
        /// Rotate an RGB color's hue by `deg` and scale its saturation (HSL space).
        /// </summary>
        static (byte, byte, byte) RotateHue(byte r, byte g, byte b, float deg, float satScale)
        {
            float rf = r / 255f, gf = g / 255f, bf = b / 255f;
            float max = Math.Max(rf, Math.Max(gf, bf)), min = Math.Min(rf, Math.Min(gf, bf));
            float l = (max + min) / 2f, d = max - min;
            float s = d == 0 ? 0 : d / (1f - Math.Abs(2f * l - 1f) + 1e-6f);
            float h = 0;
            if (d > 0)
            {
                if (max == rf) h = ((gf - bf) / d % 6f + 6f) % 6f;
                else if (max == gf) h = (bf - rf) / d + 2f;
                else h = (rf - gf) / d + 4f;
                h *= 60f;
            }
            h = ((h + deg) % 360f + 360f) % 360f;
            s = Math.Clamp(s * satScale, 0f, 1f);
            float c = (1f - Math.Abs(2f * l - 1f)) * s;
            float x = c * (1f - Math.Abs(h / 60f % 2f - 1f));
            float m = l - c / 2f;
            (float r2, float g2, float b2) = h switch
            {
                < 60f => (c, x, 0f),
                < 120f => (x, c, 0f),
                < 180f => (0f, c, x),
                < 240f => (0f, x, c),
                < 300f => (x, 0f, c),
                _ => (c, 0f, x),
            };
            return ((byte)Math.Clamp((r2 + m) * 255f, 0, 255),
                    (byte)Math.Clamp((g2 + m) * 255f, 0, 255),
                    (byte)Math.Clamp((b2 + m) * 255f, 0, 255));
        }

        /// <summary>
        /// Standalone *_image roots that do NOT alias any map_head TOBJ
        /// buffer -- e.g. Pokémon Stadium's GrdPSNormalBase* field surfaces,
        /// which the game's transformation engine uploads by symbol name
        /// (replacing a map_head texture does nothing for those). Format
        /// parses from the root name; dimensions are inferred from the data
        /// length (square power-of-two first, then 2:1). Returns detached
        /// TOBJ wrappers so the normal codecs apply.
        /// </summary>
        static List<(HSDRootNode root, HSD_TOBJ tobj)> CollectRootImages(HSDRawFile rawFile)
        {
            var fmtTokens = new (string token, HSDRaw.GX.GXTexFmt fmt, int bpp)[]
            {
                ("_CMPR_", HSDRaw.GX.GXTexFmt.CMP, 4),
                ("_RGBA8_", HSDRaw.GX.GXTexFmt.RGBA8, 32),
                ("_RGB5A3_", HSDRaw.GX.GXTexFmt.RGB5A3, 16),
                ("_RGB565_", HSDRaw.GX.GXTexFmt.RGB565, 16),
                ("_IA8_", HSDRaw.GX.GXTexFmt.IA8, 16),
                ("_IA4_", HSDRaw.GX.GXTexFmt.IA4, 8),
                ("_I8_", HSDRaw.GX.GXTexFmt.I8, 8),
                ("_I4_", HSDRaw.GX.GXTexFmt.I4, 4),
            };
            var result = new List<(HSDRootNode, HSD_TOBJ)>();

            var aliased = new HashSet<string>();
            var mapTex = CollectStageTextures(rawFile);
            if (mapTex != null)
                foreach (var (_, t) in mapTex)
                    if (t?.ImageData?.ImageData != null)
                        aliased.Add(Convert.ToHexString(System.Security.Cryptography.MD5.HashData(t.ImageData.ImageData)));

            foreach (var r in rawFile.Roots)
            {
                if (r.Name == null || !r.Name.EndsWith("_image"))
                    continue;
                var data = r.Data?._s?.GetData();
                if (data == null || data.Length == 0)
                    continue;
                if (aliased.Contains(Convert.ToHexString(System.Security.Cryptography.MD5.HashData(data))))
                    continue;
                var ft = fmtTokens.FirstOrDefault(t => r.Name.Contains(t.token));
                if (ft.token == null)
                    continue;   // C4/C8 roots would need their tlut root; none unaliased so far
                long pixels = (long)data.Length * 8 / ft.bpp;
                int w = 0, h = 0;
                for (int side = 1; side <= 1024; side *= 2)
                {
                    if ((long)side * side == pixels) { w = side; h = side; break; }
                    if ((long)side * side * 2 == pixels) { w = side * 2; h = side; break; }
                }
                if (w == 0)
                    continue;
                var tobj = new HSD_TOBJ();
                tobj.ImageData = new HSD_Image
                {
                    Width = (short)w,
                    Height = (short)h,
                    Format = ft.fmt,
                    ImageData = data,
                };
                result.Add((r, tobj));
            }
            return result;
        }

        /// <summary>
        /// Texture-SWAP animation frames (MatAnim TexAnim ImageBuffers) --
        /// e.g. Pokémon Stadium's blinking deck light strips. The anim player
        /// uploads these per frame; they are neither map_head TOBJs nor named
        /// roots, so they form a third texture store. Buffers sharing an
        /// HSD_Image accessor with a map_head TOBJ are skipped (those update
        /// through the TOBJ entry). Wrappers reference the LIVE accessors, so
        /// InjectBitmap writes the bank in place.
        /// </summary>
        static List<HSD_TOBJ> CollectTexAnimImages(HSDRawFile rawFile)
        {
            var result = new List<HSD_TOBJ>();
            var root = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Gr.SBM_Map_Head);
            if (root == null)
                return result;
            var head = (HSDRaw.Melee.Gr.SBM_Map_Head)root.Data;
            var groups = head.ModelGroups?.Array;
            if (groups == null)
                return result;

            var mapImages = new HashSet<HSD_Image>();
            var mapTex = CollectStageTextures(rawFile);
            if (mapTex != null)
                foreach (var (_, t) in mapTex)
                    if (t?.ImageData != null)
                        mapImages.Add(t.ImageData);

            var seen = new HashSet<HSD_Image>();
            for (int g = 0; g < groups.Length; g++)
            {
                var majArr = groups[g]?.MaterialAnimations?.Array;
                if (majArr == null) continue;
                foreach (var majRoot in majArr)
                {
                    if (majRoot == null) continue;
                    foreach (var maj in majRoot.TreeList)
                    {
                        if (maj.MaterialAnimation == null) continue;
                        foreach (var ma in maj.MaterialAnimation.List)
                        {
                            if (ma.TextureAnimation == null) continue;
                            foreach (var ta in ma.TextureAnimation.List)
                            {
                                var bufs = ta.ImageBuffers?.Array;
                                if (bufs == null) continue;
                                var tluts = ta.TlutBuffers?.Array;
                                for (int i = 0; i < bufs.Length; i++)
                                {
                                    var img = bufs[i]?.Data;
                                    if (img?.ImageData == null) continue;
                                    if (mapImages.Contains(img) || !seen.Add(img)) continue;
                                    var tobj = new HSD_TOBJ { ImageData = img };
                                    if (tluts != null && i < tluts.Length && tluts[i]?.Data != null)
                                        tobj.TlutData = tluts[i].Data;
                                    result.Add(tobj);
                                }
                            }
                        }
                    }
                }
            }
            return result;
        }

        /// <summary>
        /// Rotate an RGB color's hue (0..1 floats) by `deg` and scale its
        /// saturation (HSL space). Float twin of <see cref="RotateHue"/> for
        /// animation color tracks.
        /// </summary>
        static (float, float, float) RotateHueF(float rf, float gf, float bf, float deg, float satScale)
        {
            float max = Math.Max(rf, Math.Max(gf, bf)), min = Math.Min(rf, Math.Min(gf, bf));
            float l = (max + min) / 2f, d = max - min;
            float s = d == 0 ? 0 : d / (1f - Math.Abs(2f * l - 1f) + 1e-6f);
            float h = 0;
            if (d > 0)
            {
                if (max == rf) h = ((gf - bf) / d % 6f + 6f) % 6f;
                else if (max == gf) h = (bf - rf) / d + 2f;
                else h = (rf - gf) / d + 4f;
                h *= 60f;
            }
            h = ((h + deg) % 360f + 360f) % 360f;
            s = Math.Clamp(s * satScale, 0f, 1f);
            float c = (1f - Math.Abs(2f * l - 1f)) * s;
            float x = c * (1f - Math.Abs(h / 60f % 2f - 1f));
            float m = l - c / 2f;
            (float r2, float g2, float b2) = h switch
            {
                < 60f => (c, x, 0f),
                < 120f => (x, c, 0f),
                < 180f => (0f, c, x),
                < 240f => (0f, x, c),
                < 300f => (x, 0f, c),
                _ => (c, 0f, x),
            };
            return (Math.Clamp(r2 + m, 0f, 1f), Math.Clamp(g2 + m, 0f, 1f), Math.Clamp(b2 + m, 0f, 1f));
        }

        /// <summary>
        /// Rotate one packed GX color entry (GXCompTypeClr layouts) in place
        /// inside a big-endian buffer. Returns 1 if an entry was rewritten.
        /// </summary>
        static int RotateClrBytes(byte[] buf, int off, int compType, float deg, float satScale)
        {
            switch (compType)
            {
                case 0:
                {   // RGB565
                    int v = (buf[off] << 8) | buf[off + 1];
                    var (r, g, b) = RotateHue((byte)(((v >> 11) & 0x1F) << 3), (byte)(((v >> 5) & 0x3F) << 2), (byte)((v & 0x1F) << 3), deg, satScale);
                    int nv = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
                    buf[off] = (byte)(nv >> 8); buf[off + 1] = (byte)nv;
                    return 1;
                }
                case 1: case 2: case 5:
                {   // RGB8 / RGBX8 / RGBA8 -- first three bytes are RGB
                    var (r, g, b) = RotateHue(buf[off], buf[off + 1], buf[off + 2], deg, satScale);
                    buf[off] = r; buf[off + 1] = g; buf[off + 2] = b;
                    return 1;
                }
                case 3:
                {   // RGBA4
                    int v = (buf[off] << 8) | buf[off + 1];
                    var (r, g, b) = RotateHue((byte)(((v >> 12) & 0xF) * 17), (byte)(((v >> 8) & 0xF) * 17), (byte)(((v >> 4) & 0xF) * 17), deg, satScale);
                    int nv = ((r >> 4) << 12) | ((g >> 4) << 8) | ((b >> 4) << 4) | (v & 0xF);
                    buf[off] = (byte)(nv >> 8); buf[off + 1] = (byte)nv;
                    return 1;
                }
                case 4:
                {   // RGBA6
                    int v = (buf[off] << 16) | (buf[off + 1] << 8) | buf[off + 2];
                    var (r, g, b) = RotateHue((byte)(((v >> 18) & 0x3F) << 2), (byte)(((v >> 12) & 0x3F) << 2), (byte)(((v >> 6) & 0x3F) << 2), deg, satScale);
                    int nv = ((r >> 2) << 18) | ((g >> 2) << 12) | ((b >> 2) << 6) | (v & 0x3F);
                    buf[off] = (byte)(nv >> 16); buf[off + 1] = (byte)(nv >> 8); buf[off + 2] = (byte)nv;
                    return 1;
                }
            }
            return 0;
        }

        /// <summary>
        /// Rotate a POBJ's vertex colors (CLR0/CLR1). Stage geometry often
        /// gets its color ENTIRELY from vertex colors over grayscale textures
        /// (e.g. Pokémon Stadium's green deck light strips) -- no texture,
        /// material, TEV, or matanim edit can touch those. Handles indexed
        /// color arrays in place and DIRECT colors via a display-list
        /// round-trip (indexes preserved, attributes untouched). Gray verts
        /// (baked lighting) are hue-rotation no-ops, so this is safe to run
        /// across whole groups. Returns the number of colors rewritten.
        /// </summary>
        static int RotateVertexColors(HSDRaw.Common.HSD_POBJ pobj, float deg, float satScale)
        {
            int changed = 0;
            var attrs = pobj.ToGXAttributes();
            bool hasDirectClr = false;
            foreach (var att in attrs)
            {
                if (att.AttributeName != HSDRaw.GX.GXAttribName.GX_VA_CLR0
                    && att.AttributeName != HSDRaw.GX.GXAttribName.GX_VA_CLR1)
                    continue;
                if (att.AttributeType == HSDRaw.GX.GXAttribType.GX_DIRECT)
                {
                    hasDirectClr = true;
                    continue;
                }
                var buf = att.Buffer?._s?.GetData();
                if (buf == null || att.Stride <= 0)
                    continue;
                int n = buf.Length / att.Stride;
                for (int i = 0; i < n; i++)
                    changed += RotateClrBytes(buf, i * att.Stride, (int)att.CompType, deg, satScale);
                att.Buffer._s.SetData(buf);
            }
            if (hasDirectClr)
            {
                var dl = pobj.ToDisplayList(attrs);
                foreach (var prim in dl.Primitives)
                    foreach (var ig in prim.Indices)
                    {
                        if (ig.Clr0 != null)
                        {
                            (ig.Clr0[0], ig.Clr0[1], ig.Clr0[2]) = RotateHue(ig.Clr0[0], ig.Clr0[1], ig.Clr0[2], deg, satScale);
                            changed++;
                        }
                        if (ig.Clr1 != null)
                        {
                            (ig.Clr1[0], ig.Clr1[1], ig.Clr1[2]) = RotateHue(ig.Clr1[0], ig.Clr1[1], ig.Clr1[2], deg, satScale);
                            changed++;
                        }
                    }
                pobj.DisplayListBuffer = dl.ToBuffer();
            }
            return changed;
        }

        /// <summary>
        /// Rotate the hue of R/G/B keyframe-track triples on an AOBJ. Each
        /// entry in `firstChannels` names the R track of a triple (G and B
        /// are the next two track ids). Stage matanims re-assert these colors
        /// every frame in-game, overriding any static MOBJ color edit -- this
        /// is what makes e.g. Pokémon Stadium's turf immune to materialTints.
        /// Tracks are resampled at the union of the triple's keyframes and
        /// re-encoded linearly. Only complete triples are rotated (a partial
        /// triple's missing channels live in the static material, which the
        /// MOBJ pass already handles). Returns the number of triples changed.
        /// </summary>
        static int RotateAobjColorTriples(HSDRaw.Common.Animation.HSD_AOBJ aobj,
                                          float deg, float satScale, params byte[] firstChannels)
        {
            if (aobj?.FObjDesc == null)
                return 0;
            var tracks = aobj.FObjDesc.List;
            int changed = 0;
            foreach (var first in firstChannels)
            {
                var rT = tracks.Find(t => t.TrackType == first);
                var gT = tracks.Find(t => t.TrackType == first + 1);
                var bT = tracks.Find(t => t.TrackType == first + 2);
                if (rT == null || gT == null || bT == null)
                    continue;

                var rp = new HSDRaw.Tools.FOBJ_Player(rT.TrackType, rT.GetDecodedKeys());
                var gp = new HSDRaw.Tools.FOBJ_Player(gT.TrackType, gT.GetDecodedKeys());
                var bp = new HSDRaw.Tools.FOBJ_Player(bT.TrackType, bT.GetDecodedKeys());

                var frames = new SortedSet<float>();
                foreach (var k in rp.Keys) frames.Add(k.Frame);
                foreach (var k in gp.Keys) frames.Add(k.Frame);
                foreach (var k in bp.Keys) frames.Add(k.Frame);
                if (frames.Count == 0)
                    continue;

                var rk = new List<HSDRaw.Tools.FOBJKey>();
                var gk = new List<HSDRaw.Tools.FOBJKey>();
                var bk = new List<HSDRaw.Tools.FOBJKey>();
                foreach (var f in frames)
                {
                    var (nr, ng, nb) = RotateHueF(
                        Math.Clamp(rp.GetValue(f), 0f, 1f),
                        Math.Clamp(gp.GetValue(f), 0f, 1f),
                        Math.Clamp(bp.GetValue(f), 0f, 1f), deg, satScale);
                    rk.Add(new HSDRaw.Tools.FOBJKey { Frame = f, Value = nr, InterpolationType = HSDRaw.Common.Animation.GXInterpolationType.HSD_A_OP_LIN });
                    gk.Add(new HSDRaw.Tools.FOBJKey { Frame = f, Value = ng, InterpolationType = HSDRaw.Common.Animation.GXInterpolationType.HSD_A_OP_LIN });
                    bk.Add(new HSDRaw.Tools.FOBJKey { Frame = f, Value = nb, InterpolationType = HSDRaw.Common.Animation.GXInterpolationType.HSD_A_OP_LIN });
                }
                rT.SetKeys(rk, rT.TrackType);
                gT.SetKeys(gk, gT.TrackType);
                bT.SetKeys(bk, bT.TrackType);
                // decoded keys are rebased to frame 0
                rT.StartFrame = 0; gT.StartFrame = 0; bT.StartFrame = 0;
                changed++;
            }
            return changed;
        }

        /// <summary>
        /// Stage (Gr*.dat) texture export/import over the map_head model groups.
        ///   Export: HSDRawViewer.exe --stage-textures export <stage.dat> <output_dir>
        ///   Import: HSDRawViewer.exe --stage-textures import <stage.dat> <spec.json> <output.dat>
        /// spec.json: {"replacements": [{"index": 4, "png": "..."}]} -- always
        /// re-encodes in the texture's ORIGINAL format.
        /// </summary>
        static void RunStageTexturesOperation(string[] args)
        {
            try
            {
                string subCommand = args.Length >= 2 ? args[1].ToLower() : "";

                if (subCommand == "dump" && args.Length >= 3)
                {
                    // Diagnostic: where do a stage's colors live? Lists every
                    // root, and per map_head group the material colors, matanim
                    // color tracks, and vertex-color usage.
                    var rawFile = new HSDRawFile(args[2]);
                    foreach (var r in rawFile.Roots)
                        Console.WriteLine($"ROOT: {r.Name} ({r.Data?.GetType().Name}) len={r.Data?._s?.Length ?? -1}");

                    // Do standalone *_image roots alias map_head TOBJ buffers,
                    // or are they separate copies the game swaps in (e.g.
                    // Stadium's transformation field bases)?
                    {
                        var tobjHashes = new Dictionary<string, List<int>>();
                        var allTex2 = CollectStageTextures(rawFile);
                        if (allTex2 != null)
                            for (int i = 0; i < allTex2.Count; i++)
                            {
                                var data = allTex2[i].tobj?.ImageData?.ImageData;
                                if (data == null) continue;
                                var h = Convert.ToHexString(System.Security.Cryptography.MD5.HashData(data));
                                if (!tobjHashes.TryGetValue(h, out var lst))
                                    tobjHashes[h] = lst = new List<int>();
                                lst.Add(i);
                            }
                        foreach (var r in rawFile.Roots)
                        {
                            if (r.Name == null || !r.Name.EndsWith("_image"))
                                continue;
                            var data = r.Data?._s?.GetData();
                            if (data == null) continue;
                            var h = Convert.ToHexString(System.Security.Cryptography.MD5.HashData(data));
                            var match = tobjHashes.TryGetValue(h, out var idxs)
                                ? $"ALIASES map_head tex [{string.Join(",", idxs)}]"
                                : "no map_head match";
                            Console.WriteLine($"IMGROOT: {r.Name} len={data.Length} md5={h.Substring(0, 8)} {match}");
                        }
                    }
                    foreach (var r in rawFile.Roots)
                    {
                        if (!(r.Data is HSDRaw.Melee.Gr.SBM_Map_Head head))
                            continue;
                        var groups = head.ModelGroups?.Array;
                        if (groups == null) continue;
                        for (int g = 0; g < groups.Length; g++)
                        {
                            var rootNode = groups[g]?.RootNode;
                            int dobjs = 0, colored = 0, vtxColor = 0;
                            if (rootNode != null)
                                foreach (var jobj in rootNode.TreeList)
                                {
                                    if (jobj.Dobj == null) continue;
                                    foreach (var dobj in jobj.Dobj.List)
                                    {
                                        dobjs++;
                                        var mat = dobj.Mobj?.Material;
                                        if (mat != null && (mat.DIF_R != mat.DIF_G || mat.DIF_G != mat.DIF_B))
                                        {
                                            colored++;
                                            Console.WriteLine($"  g{g} dobj{dobjs - 1} MOBJ DIF=({mat.DIF_R},{mat.DIF_G},{mat.DIF_B}) AMB=({mat.AMB_R},{mat.AMB_G},{mat.AMB_B})");
                                        }
                                        if (dobj.Mobj?.Textures != null)
                                            foreach (var tobjT in dobj.Mobj.Textures.List)
                                            {
                                                var tev = tobjT?.TEV;
                                                if (tev == null) continue;
                                                var k = tev.constant; var t0 = tev.tev0; var t1 = tev.tev1;
                                                Console.WriteLine($"  g{g} dobj{dobjs - 1} TEV konst=({k.R},{k.G},{k.B}) tev0=({t0.R},{t0.G},{t0.B}) tev1=({t1.R},{t1.G},{t1.B}) active={tev.active}");
                                            }
                                        if (dobj.Pobj != null)
                                            foreach (var pobj in dobj.Pobj.List)
                                                if (pobj.ToGXAttributes().Any(a => a.AttributeName == HSDRaw.GX.GXAttribName.GX_VA_CLR0))
                                                    vtxColor++;
                                    }
                                }
                            Console.WriteLine($"GROUP {g}: {dobjs} dobjs, {colored} colored materials, {vtxColor} pobjs with vertex colors");
                            var majArr = groups[g]?.MaterialAnimations?.Array;
                            if (majArr == null) continue;
                            for (int m = 0; m < majArr.Length; m++)
                            {
                                if (majArr[m] == null) continue;
                                int jIdx = 0;
                                foreach (var maj in majArr[m].TreeList)
                                {
                                    int aIdx = 0;
                                    if (maj.MaterialAnimation != null)
                                        foreach (var ma in maj.MaterialAnimation.List)
                                        {
                                            void DumpAobj(HSDRaw.Common.Animation.HSD_AOBJ ao, string tag)
                                            {
                                                if (ao?.FObjDesc == null) return;
                                                foreach (var t in ao.FObjDesc.List)
                                                {
                                                    var keys = t.GetDecodedKeys();
                                                    var first = keys.Count > 0 ? keys[0].Value : float.NaN;
                                                    var last = keys.Count > 0 ? keys[keys.Count - 1].Value : float.NaN;
                                                    Console.WriteLine($"  g{g} maj{m}/{jIdx} anim{aIdx} {tag} track {(HSDRaw.Common.Animation.MatTrackType)t.TrackType}({t.TrackType}) keys={keys.Count} first={first:0.###} last={last:0.###}");
                                                }
                                            }
                                            DumpAobj(ma.AnimationObject, "mat");
                                            if (ma.TextureAnimation != null)
                                                foreach (var ta in ma.TextureAnimation.List)
                                                    DumpAobj(ta.AnimationObject, $"tex({ta.GXTexMapID})");
                                            aIdx++;
                                        }
                                    jIdx++;
                                }
                            }
                        }
                    }
                    return;
                }

                if (subCommand == "export" && args.Length >= 4)
                {
                    string datFile = args[2];
                    string outDir = args[3];
                    System.IO.Directory.CreateDirectory(outDir);

                    Console.WriteLine($"Loading: {datFile}");
                    var rawFile = new HSDRawFile(datFile);
                    var allTex = CollectStageTextures(rawFile);
                    if (allTex == null)
                    {
                        Console.WriteLine("ERROR: No map_head root found (not a stage file?)");
                        Environment.Exit(1);
                        return;
                    }

                    Console.WriteLine($"Found {allTex.Count} textures:");
                    var manifest = new List<Dictionary<string, object>>();
                    int index = 0;
                    foreach (var (grp, tobj) in allTex)
                    {
                        string fmt = tobj.ImageData.Format.ToString();
                        int w = tobj.ImageData.Width;
                        int h = tobj.ImageData.Height;
                        string fileName = $"stage_t{index}_g{grp}_{w}x{h}_{fmt}.png";
                        using (var image = tobj.ToImage())
                        using (var fs = new System.IO.FileStream(System.IO.Path.Combine(outDir, fileName), System.IO.FileMode.Create))
                        {
                            image.Save(fs, new PngEncoder());
                        }
                        manifest.Add(new Dictionary<string, object>
                        {
                            ["index"] = index,
                            ["group"] = grp,
                            ["width"] = w,
                            ["height"] = h,
                            ["format"] = fmt,
                            ["filename"] = fileName,
                        });
                        Console.WriteLine($"  t{index} group {grp}: {w}x{h} {fmt}");
                        index++;
                    }
                    // Standalone root images (e.g. Stadium's NormalBase field
                    // surfaces) continue the index space after map_head.
                    foreach (var (root, tobj) in CollectRootImages(rawFile))
                    {
                        string fmt = tobj.ImageData.Format.ToString();
                        int w = tobj.ImageData.Width;
                        int h = tobj.ImageData.Height;
                        string fileName = $"stage_t{index}_root_{w}x{h}_{fmt}.png";
                        using (var image = tobj.ToImage())
                        using (var fs = new System.IO.FileStream(System.IO.Path.Combine(outDir, fileName), System.IO.FileMode.Create))
                        {
                            image.Save(fs, new PngEncoder());
                        }
                        manifest.Add(new Dictionary<string, object>
                        {
                            ["index"] = index,
                            ["root"] = root.Name,
                            ["width"] = w,
                            ["height"] = h,
                            ["format"] = fmt,
                            ["filename"] = fileName,
                        });
                        Console.WriteLine($"  t{index} root {root.Name}: {w}x{h} {fmt}");
                        index++;
                    }
                    // Texture-swap animation frames (blinking light strips
                    // etc.) continue the index space after the roots.
                    foreach (var tobj in CollectTexAnimImages(rawFile))
                    {
                        string fmt = tobj.ImageData.Format.ToString();
                        int w = tobj.ImageData.Width;
                        int h = tobj.ImageData.Height;
                        string fileName = $"stage_t{index}_anim_{w}x{h}_{fmt}.png";
                        using (var image = tobj.ToImage())
                        using (var fs = new System.IO.FileStream(System.IO.Path.Combine(outDir, fileName), System.IO.FileMode.Create))
                        {
                            image.Save(fs, new PngEncoder());
                        }
                        manifest.Add(new Dictionary<string, object>
                        {
                            ["index"] = index,
                            ["anim"] = true,
                            ["width"] = w,
                            ["height"] = h,
                            ["format"] = fmt,
                            ["filename"] = fileName,
                        });
                        Console.WriteLine($"  t{index} anim-frame: {w}x{h} {fmt}");
                        index++;
                    }
                    System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "manifest.json"),
                        JsonSerializer.Serialize(new Dictionary<string, object> { ["textures"] = manifest },
                                                 new JsonSerializerOptions { WriteIndented = true }));
                    Console.WriteLine($"SUCCESS: Exported {index} textures");
                }
                else if (subCommand == "import" && args.Length >= 5)
                {
                    string datFile = args[2];
                    string specFile = args[3];
                    string outputDat = args[4];

                    Console.WriteLine($"Loading: {datFile}");
                    var rawFile = new HSDRawFile(datFile);
                    var allTex = CollectStageTextures(rawFile);
                    if (allTex == null || allTex.Count == 0)
                    {
                        Console.WriteLine("ERROR: No map_head textures found (not a stage file?)");
                        Environment.Exit(1);
                        return;
                    }

                    // Roots, then texture-swap anim frames, continue the
                    // index space after map_head.
                    var rootImages = CollectRootImages(rawFile);
                    var animImages = CollectTexAnimImages(rawFile);

                    using var specDoc = JsonDocument.Parse(System.IO.File.ReadAllText(specFile));
                    int replaced = 0;
                    foreach (var entry in specDoc.RootElement.GetProperty("replacements").EnumerateArray())
                    {
                        int idx = entry.GetProperty("index").GetInt32();
                        string pngPath = entry.GetProperty("png").GetString();
                        if (idx < 0 || idx >= allTex.Count + rootImages.Count + animImages.Count)
                        {
                            Console.WriteLine($"WARNING: texture index {idx} out of range (file has {allTex.Count}+{rootImages.Count}+{animImages.Count}); skipping");
                            continue;
                        }
                        if (!System.IO.File.Exists(pngPath))
                        {
                            Console.WriteLine($"WARNING: png not found: {pngPath}; skipping");
                            continue;
                        }
                        var isRoot = idx >= allTex.Count && idx < allTex.Count + rootImages.Count;
                        var isAnim = idx >= allTex.Count + rootImages.Count;
                        var tobj = isAnim ? animImages[idx - allTex.Count - rootImages.Count]
                                 : isRoot ? rootImages[idx - allTex.Count].tobj
                                 : allTex[idx].tobj;
                        using var userImage = SixLabors.ImageSharp.Image.Load<SixLabors.ImageSharp.PixelFormats.Bgra32>(pngPath);
                        int w = tobj.ImageData.Width;
                        int h = tobj.ImageData.Height;
                        using var resized = userImage.Clone(ctx => ctx.Resize(w, h));
                        var imgFormat = tobj.ImageData.Format;
                        var palFormat = tobj.TlutData != null ? tobj.TlutData.Format : HSDRaw.GX.GXTlutFmt.RGB565;
                        tobj.InjectBitmap(resized, imgFormat, palFormat);
                        if (isRoot)
                        {
                            // Detached wrapper: copy the re-encoded bytes back
                            // into the root's own data block (same dims+format
                            // keeps the length identical -- the game uploads
                            // this buffer by symbol name).
                            var root = rootImages[idx - allTex.Count].root;
                            var newBytes = tobj.ImageData.ImageData;
                            var oldLen = root.Data._s.Length;
                            if (newBytes.Length != oldLen)
                                Console.WriteLine($"WARNING: root {root.Name} re-encode length {newBytes.Length} != original {oldLen}");
                            root.Data._s.SetData(newBytes);
                            Console.WriteLine($"  t{idx}: replaced ROOT {root.Name} ({w}x{h} {imgFormat})");
                        }
                        else
                        {
                            // Anim-frame wrappers reference the bank's LIVE
                            // HSD_Image/HSD_Tlut, so the inject above already
                            // wrote them in place.
                            Console.WriteLine($"  t{idx}: replaced{(isAnim ? " ANIM-FRAME" : "")} ({w}x{h} {imgFormat})");
                        }
                        replaced++;
                    }
                    // Optional material-color pass: {"materialTints": [{"hueShift": deg,
                    // "saturationScale": 1.0, "groups": [..] (omit = all groups)}]}
                    // Rotates the hue of every MOBJ DIFFUSE+AMBIENT color in the
                    // targeted map_head model groups (stage glow/rim colors often
                    // live in materials, not textures).
                    int matCount = 0;
                    int matAnimCount = 0;
                    int vtxCount = 0;
                    if (specDoc.RootElement.TryGetProperty("materialTints", out var tintsEl))
                    {
                        var headRoot = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Gr.SBM_Map_Head);
                        var head = headRoot != null ? (HSDRaw.Melee.Gr.SBM_Map_Head)headRoot.Data : null;
                        var modelGroups = head?.ModelGroups?.Array;
                        if (modelGroups != null)
                        {
                            foreach (var tint in tintsEl.EnumerateArray())
                            {
                                float hueShift = tint.TryGetProperty("hueShift", out var hs) ? hs.GetSingle() : 0f;
                                float satScale = tint.TryGetProperty("saturationScale", out var ss) ? ss.GetSingle() : 1f;
                                HashSet<int> groupFilter = null;
                                if (tint.TryGetProperty("groups", out var groupsEl))
                                {
                                    groupFilter = new HashSet<int>();
                                    foreach (var g in groupsEl.EnumerateArray())
                                        groupFilter.Add(g.GetInt32());
                                }
                                for (int g = 0; g < modelGroups.Length; g++)
                                {
                                    if (groupFilter != null && !groupFilter.Contains(g))
                                        continue;
                                    var rootNode = modelGroups[g]?.RootNode;
                                    if (rootNode == null)
                                        continue;
                                    foreach (var jobj in rootNode.TreeList)
                                    {
                                        if (jobj.Dobj == null) continue;
                                        foreach (var dobj in jobj.Dobj.List)
                                        {
                                            var mat = dobj.Mobj?.Material;
                                            if (mat != null)
                                            {
                                                (mat.DIF_R, mat.DIF_G, mat.DIF_B) =
                                                    RotateHue(mat.DIF_R, mat.DIF_G, mat.DIF_B, hueShift, satScale);
                                                (mat.AMB_R, mat.AMB_G, mat.AMB_B) =
                                                    RotateHue(mat.AMB_R, mat.AMB_G, mat.AMB_B, hueShift, satScale);
                                                matCount++;
                                            }
                                            // Static TOBJ TEV constants (glow/accent
                                            // colors mixed over grayscale masks).
                                            if (dobj.Mobj?.Textures != null)
                                                foreach (var tobjT in dobj.Mobj.Textures.List)
                                                {
                                                    var tev = tobjT?.TEV;
                                                    if (tev == null) continue;
                                                    var (kr, kg, kb) = RotateHue(tev.constant.R, tev.constant.G, tev.constant.B, hueShift, satScale);
                                                    tev.constant = System.Drawing.Color.FromArgb(kr, kg, kb);
                                                    var (r0, g0, b0) = RotateHue(tev.tev0.R, tev.tev0.G, tev.tev0.B, hueShift, satScale);
                                                    tev.tev0 = System.Drawing.Color.FromArgb(r0, g0, b0);
                                                    var (r1, g1, b1) = RotateHue(tev.tev1.R, tev.tev1.G, tev.tev1.B, hueShift, satScale);
                                                    tev.tev1 = System.Drawing.Color.FromArgb(r1, g1, b1);
                                                    matCount++;
                                                }
                                            // Vertex colors: often the ONLY color
                                            // source for stage geometry (gray verts
                                            // are rotation no-ops, so this is safe).
                                            if (dobj.Pobj != null)
                                                foreach (var pobj in dobj.Pobj.List)
                                                    vtxCount += RotateVertexColors(pobj, hueShift, satScale);
                                        }
                                    }

                                    // Matanims re-assert material colors every frame
                                    // in-game (Pokémon Stadium's turf), overriding the
                                    // static MOBJ pass above -- rotate their color
                                    // keyframe tracks too (ambient/diffuse + TEV consts).
                                    var matAnimJoints = modelGroups[g]?.MaterialAnimations?.Array;
                                    if (matAnimJoints != null)
                                    {
                                        foreach (var majRoot in matAnimJoints)
                                        {
                                            if (majRoot == null) continue;
                                            foreach (var maj in majRoot.TreeList)
                                            {
                                                var matAnim = maj.MaterialAnimation;
                                                if (matAnim == null) continue;
                                                foreach (var ma in matAnim.List)
                                                {
                                                    matAnimCount += RotateAobjColorTriples(
                                                        ma.AnimationObject, hueShift, satScale,
                                                        (byte)HSDRaw.Common.Animation.MatTrackType.HSD_A_M_AMBIENT_R,
                                                        (byte)HSDRaw.Common.Animation.MatTrackType.HSD_A_M_DIFFUSE_R);
                                                    if (ma.TextureAnimation != null)
                                                        foreach (var ta in ma.TextureAnimation.List)
                                                            matAnimCount += RotateAobjColorTriples(
                                                                ta.AnimationObject, hueShift, satScale,
                                                                (byte)HSDRaw.Common.Animation.TexTrackType.HSD_A_T_KONST_R,
                                                                (byte)HSDRaw.Common.Animation.TexTrackType.HSD_A_T_TEV0_R,
                                                                (byte)HSDRaw.Common.Animation.TexTrackType.HSD_A_T_TEV1_R);
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            Console.WriteLine($"Material tints applied to {matCount} materials, {matAnimCount} matanim color triples, {vtxCount} vertex colors");
                        }
                    }

                    rawFile.Save(outputDat);
                    Console.WriteLine($"SUCCESS: Replaced {replaced} textures (+{matCount} material tints, +{matAnimCount} matanim triples, +{vtxCount} vertex colors), saved to: {outputDat}");
                }
                else
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --stage-textures export <stage.dat> <output_dir>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --stage-textures import <stage.dat> <spec.json> <output.dat>");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: stage textures operation failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Collect all textures from every JOBJDesc model in a scene_data file
        /// (e.g. GmPause.usd's ScGamPause_scene_data root). Returns a flat list
        /// in stable traversal order.
        /// </summary>
        static List<(int jointIdx, HSD_TOBJ tobj)> CollectSceneTextures(HSDRawFile rawFile)
        {
            var root = rawFile.Roots.Find(r => r.Data is HSD_SOBJ);
            if (root == null)
                return null;

            var sobj = (HSD_SOBJ)root.Data;
            var result = new List<(int, HSD_TOBJ)>();
            var descs = sobj.JOBJDescs?.Array;
            if (descs == null)
                return result;

            foreach (var desc in descs)
            {
                if (desc?.RootJoint == null)
                    continue;
                result.AddRange(CollectAllTextures(desc.RootJoint));
            }
            return result;
        }

        /// <summary>
        /// Pause screen (GmPause.dat/.usd) texture export/import.
        ///   Export: HSDRawViewer.exe --pause-screen export <gmpause.usd> <output_dir>
        ///   Import: HSDRawViewer.exe --pause-screen import <gmpause.usd> <spec.json> <output.usd>
        /// spec.json: {"replacements": [{"index": 4, "png": "...", "format": "original"},
        ///                              {"target": "main", "png": "...", "format": "rgb5a3"}]}
        /// </summary>
        static void RunPauseScreenOperation(string[] args)
        {
            try
            {
                if (args.Length < 2)
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --pause-screen export <gmpause.usd> <output_dir>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --pause-screen import <gmpause.usd> <spec.json> <output.usd>");
                    return;
                }

                string subCommand = args[1].ToLower();

                if (subCommand == "export")
                {
                    if (args.Length < 4)
                    {
                        Console.WriteLine("Usage: HSDRawViewer.exe --pause-screen export <gmpause.usd> <output_dir>");
                        return;
                    }

                    string datFile = args[2];
                    string outDir = args[3];
                    System.IO.Directory.CreateDirectory(outDir);

                    Console.WriteLine($"Loading: {datFile}");
                    var rawFile = new HSDRawFile(datFile);

                    var allTex = CollectSceneTextures(rawFile);
                    if (allTex == null)
                    {
                        Console.WriteLine("ERROR: No scene_data root found (not a GmPause file?)");
                        Environment.Exit(1);
                        return;
                    }

                    Console.WriteLine($"Found {allTex.Count} textures:");
                    var manifest = new List<Dictionary<string, object>>();
                    int index = 0;
                    foreach (var (ji, tobj) in allTex)
                    {
                        string fmt = tobj.ImageData.Format.ToString();
                        int w = tobj.ImageData.Width;
                        int h = tobj.ImageData.Height;
                        string fileName = $"pause_t{index}_j{ji}_{w}x{h}_{fmt}.png";
                        string outPath = System.IO.Path.Combine(outDir, fileName);
                        using (var image = tobj.ToImage())
                        using (var fs = new System.IO.FileStream(outPath, System.IO.FileMode.Create))
                        {
                            image.Save(fs, new PngEncoder());
                        }
                        manifest.Add(new Dictionary<string, object>
                        {
                            ["index"] = index,
                            ["joint"] = ji,
                            ["width"] = w,
                            ["height"] = h,
                            ["format"] = fmt,
                            ["filename"] = fileName,
                        });
                        Console.WriteLine($"  t{index} joint {ji}: {w}x{h} {fmt} -> {fileName}");
                        index++;
                    }

                    string manifestPath = System.IO.Path.Combine(outDir, "manifest.json");
                    System.IO.File.WriteAllText(manifestPath, JsonSerializer.Serialize(
                        new Dictionary<string, object> { ["textures"] = manifest },
                        new JsonSerializerOptions { WriteIndented = true }));
                    Console.WriteLine($"SUCCESS: Exported {index} textures");
                }
                else if (subCommand == "import")
                {
                    if (args.Length < 5)
                    {
                        Console.WriteLine("Usage: HSDRawViewer.exe --pause-screen import <gmpause.usd> <spec.json> <output.usd>");
                        return;
                    }

                    string datFile = args[2];
                    string specFile = args[3];
                    string outputDat = args[4];

                    Console.WriteLine($"Loading: {datFile}");
                    var rawFile = new HSDRawFile(datFile);

                    var allTex = CollectSceneTextures(rawFile);
                    if (allTex == null || allTex.Count == 0)
                    {
                        Console.WriteLine("ERROR: No scene_data textures found (not a GmPause file?)");
                        Environment.Exit(1);
                        return;
                    }

                    using var specDoc = JsonDocument.Parse(System.IO.File.ReadAllText(specFile));
                    int replaced = 0;
                    foreach (var entry in specDoc.RootElement.GetProperty("replacements").EnumerateArray())
                    {
                        string pngPath = entry.GetProperty("png").GetString();
                        string formatMode = entry.TryGetProperty("format", out var fmtEl)
                            ? fmtEl.GetString() : "original";

                        // Resolve target textures: explicit index, or "main"
                        // (every 88x72 texture — the central pause graphic,
                        // vanilla t4 + t10).
                        var targets = new List<HSD_TOBJ>();
                        if (entry.TryGetProperty("index", out var idxEl))
                        {
                            int idx = idxEl.GetInt32();
                            if (idx < 0 || idx >= allTex.Count)
                            {
                                Console.WriteLine($"WARNING: texture index {idx} out of range (file has {allTex.Count}); skipping");
                                continue;
                            }
                            targets.Add(allTex[idx].tobj);
                        }
                        else if (entry.TryGetProperty("target", out var tgtEl) && tgtEl.GetString() == "main")
                        {
                            foreach (var (ji, tobj) in allTex)
                                if (tobj.ImageData.Width == 88 && tobj.ImageData.Height == 72)
                                    targets.Add(tobj);
                            if (targets.Count == 0)
                            {
                                Console.WriteLine("WARNING: no 88x72 main pause textures found; skipping");
                                continue;
                            }
                        }
                        else
                        {
                            Console.WriteLine("WARNING: replacement entry has neither 'index' nor 'target'; skipping");
                            continue;
                        }

                        if (!System.IO.File.Exists(pngPath))
                        {
                            Console.WriteLine($"WARNING: png not found: {pngPath}; skipping");
                            continue;
                        }

                        using var userImage = SixLabors.ImageSharp.Image.Load<SixLabors.ImageSharp.PixelFormats.Bgra32>(pngPath);
                        foreach (var tobj in targets)
                        {
                            int w = tobj.ImageData.Width;
                            int h = tobj.ImageData.Height;
                            using var resized = userImage.Clone(ctx => ctx.Resize(w, h));

                            HSDRaw.GX.GXTexFmt imgFormat;
                            HSDRaw.GX.GXTlutFmt palFormat;
                            if (formatMode == "rgb5a3")
                            {
                                // Color support for user-uploaded pictures (the
                                // vanilla pause textures are grayscale I4/IA4).
                                imgFormat = HSDRaw.GX.GXTexFmt.RGB5A3;
                                palFormat = HSDRaw.GX.GXTlutFmt.IA8;
                            }
                            else
                            {
                                imgFormat = tobj.ImageData.Format;
                                palFormat = tobj.TlutData?.Format ?? HSDRaw.GX.GXTlutFmt.IA8;
                            }

                            // Vanilla GmPause aliases identical textures (the two
                            // 88x72 main graphics) to a single pixel buffer, so an
                            // in-place inject would silently rewrite the sibling
                            // slot too. Give this TOBJ its own image struct first.
                            var oldImage = tobj.ImageData;
                            tobj.ImageData = new HSDRaw.Common.HSD_Image()
                            {
                                Width = oldImage.Width,
                                Height = oldImage.Height,
                                Format = oldImage.Format,
                                MipMap = oldImage.MipMap,
                                MinLOD = oldImage.MinLOD,
                                MaxLOD = oldImage.MaxLOD,
                            };

                            tobj.InjectBitmap(resized, imgFormat, palFormat);
                            Console.WriteLine($"  Replaced {w}x{h} texture as {imgFormat}");
                            replaced++;
                        }
                    }

                    if (replaced == 0)
                    {
                        Console.WriteLine("ERROR: No textures were replaced");
                        Environment.Exit(1);
                        return;
                    }

                    rawFile.Save(outputDat);
                    Console.WriteLine($"SUCCESS: Replaced {replaced} textures, saved to: {outputDat}");
                }
                else
                {
                    Console.WriteLine($"Unknown pause-screen sub-command: {subCommand}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Pause screen operation failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Export or import SSS background model/animation from MnSlMap.dat/.usd.
        /// Export: HSDRawViewer.exe --sss-bg export <mnslmap.dat> <output_dir>
        /// Import: HSDRawViewer.exe --sss-bg import <project_mnslmap.usd> <background.dat> <output.usd>
        /// </summary>
        static void RunSssBgOperation(string[] args)
        {
            try
            {
                if (args.Length < 2)
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --sss-bg export <mnslmap.dat> <output_dir>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --sss-bg import <project.usd> <background.dat> <output.usd>");
                    return;
                }

                string subCommand = args[1].ToLower();

                if (subCommand == "export")
                {
                    if (args.Length < 4)
                    {
                        Console.WriteLine("Usage: HSDRawViewer.exe --sss-bg export <mnslmap.dat> <output_dir>");
                        return;
                    }

                    string datFile = args[2];
                    string outDir = args[3];
                    System.IO.Directory.CreateDirectory(outDir);

                    Console.WriteLine($"Loading: {datFile}");
                    var rawFile = new HSDRawFile(datFile);

                    Console.WriteLine($"Roots in file: {rawFile.Roots.Count}");
                    foreach (var r in rawFile.Roots)
                        Console.WriteLine($"  - {r.Name} ({r.Data?.GetType().Name})");

                    var vanillaRoot = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Mn.SBM_MnSelectStageDataTable);
                    if (vanillaRoot == null)
                    {
                        Console.WriteLine("ERROR: No SBM_MnSelectStageDataTable root found in DAT");
                        Environment.Exit(1);
                        return;
                    }

                    var tb = (HSDRaw.Melee.Mn.SBM_MnSelectStageDataTable)vanillaRoot.Data;

                    if (tb.BackgroundModel == null)
                    {
                        Console.WriteLine("ERROR: SBM_MnSelectStageDataTable has no BackgroundModel (offset 0xB0)");
                        Environment.Exit(1);
                        return;
                    }

                    var bgFile = new HSDRawFile();
                    bgFile.Roots.Add(new HSDRootNode() { Name = "bg_model", Data = tb.BackgroundModel });
                    if (tb.BackgroundAnimation != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_anim", Data = tb.BackgroundAnimation });
                    if (tb.BackgroundMaterialAnimation != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_matanim", Data = tb.BackgroundMaterialAnimation });
                    if (tb.BackgroundShapeAnimation != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_shapeanim", Data = tb.BackgroundShapeAnimation });
                    if (tb.Camera != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_camera", Data = tb.Camera });
                    if (tb.Light1 != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_light1", Data = tb.Light1 });
                    if (tb.Light2 != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_light2", Data = tb.Light2 });
                    if (tb.Fog != null)
                        bgFile.Roots.Add(new HSDRootNode() { Name = "bg_fog", Data = tb.Fog });

                    string bgDatPath = System.IO.Path.Combine(outDir, "background.dat");
                    bgFile.Save(bgDatPath);
                    Console.WriteLine($"Saved background.dat with {bgFile.Roots.Count} roots");

                    var manifest = new Dictionary<string, object>
                    {
                        ["format"] = "sss_background",
                        ["source_file"] = System.IO.Path.GetFileName(datFile),
                        ["roots"] = bgFile.Roots.Count,
                        ["has_model"] = true,
                        ["has_anim"] = tb.BackgroundAnimation != null,
                        ["has_matanim"] = tb.BackgroundMaterialAnimation != null,
                        ["has_shapeanim"] = tb.BackgroundShapeAnimation != null,
                        ["has_scene"] = tb.Camera != null,
                    };
                    System.IO.File.WriteAllText(
                        System.IO.Path.Combine(outDir, "manifest.json"),
                        JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true })
                    );

                    Console.WriteLine($"SUCCESS: Exported SSS background to {outDir}");
                }
                else if (subCommand == "import")
                {
                    if (args.Length < 5)
                    {
                        Console.WriteLine("Usage: HSDRawViewer.exe --sss-bg import <project.usd> <background.dat> <output.usd>");
                        return;
                    }

                    string projectUsd = args[2];
                    string bgDatPath = args[3];
                    string outputUsd = args[4];

                    Console.WriteLine($"Loading project: {projectUsd}");
                    var rawFile = new HSDRawFile(projectUsd);

                    var vanillaRoot = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Mn.SBM_MnSelectStageDataTable);
                    if (vanillaRoot == null)
                    {
                        Console.WriteLine("ERROR: No SBM_MnSelectStageDataTable root found in project USD");
                        Environment.Exit(1);
                        return;
                    }

                    var tb = (HSDRaw.Melee.Mn.SBM_MnSelectStageDataTable)vanillaRoot.Data;

                    Console.WriteLine($"Loading background: {bgDatPath}");
                    var bgFile = new HSDRawFile(bgDatPath);

                    Console.WriteLine($"Background file roots: {bgFile.Roots.Count}");
                    foreach (var r in bgFile.Roots)
                        Console.WriteLine($"  - {r.Name} ({r.Data?.GetType().Name})");

                    var modelRoot = bgFile.Roots.Find(r => r.Name == "bg_model");
                    var animRoot = bgFile.Roots.Find(r => r.Name == "bg_anim");
                    var matAnimRoot = bgFile.Roots.Find(r => r.Name == "bg_matanim");
                    var shapeAnimRoot = bgFile.Roots.Find(r => r.Name == "bg_shapeanim");

                    if (modelRoot == null)
                    {
                        Console.WriteLine("ERROR: background.dat missing 'bg_model' root");
                        Environment.Exit(1);
                        return;
                    }

                    tb.BackgroundModel = new HSD_JOBJ() { _s = modelRoot.Data._s };
                    tb.BackgroundAnimation = animRoot != null
                        ? new HSDRaw.Common.Animation.HSD_AnimJoint() { _s = animRoot.Data._s }
                        : null;
                    tb.BackgroundMaterialAnimation = matAnimRoot != null
                        ? new HSDRaw.Common.Animation.HSD_MatAnimJoint() { _s = matAnimRoot.Data._s }
                        : null;
                    tb.BackgroundShapeAnimation = shapeAnimRoot != null
                        ? new HSDRaw.Common.Animation.HSD_ShapeAnimJoint() { _s = shapeAnimRoot.Data._s }
                        : null;

                    bool includeScene = args.Any(a => a == "--include-scene");
                    if (includeScene)
                    {
                        var cameraRoot = bgFile.Roots.Find(r => r.Name == "bg_camera");
                        var light1Root = bgFile.Roots.Find(r => r.Name == "bg_light1");
                        var light2Root = bgFile.Roots.Find(r => r.Name == "bg_light2");
                        var fogRoot = bgFile.Roots.Find(r => r.Name == "bg_fog");

                        if (cameraRoot != null)
                            tb.Camera = new HSD_Camera() { _s = cameraRoot.Data._s };
                        if (light1Root != null)
                            tb.Light1 = new HSD_LOBJ() { _s = light1Root.Data._s };
                        if (light2Root != null)
                            tb.Light2 = new HSD_LOBJ() { _s = light2Root.Data._s };
                        if (fogRoot != null)
                            tb.Fog = new HSD_FogDesc() { _s = fogRoot.Data._s };
                        Console.WriteLine("Applied scene settings (camera, lights, fog)");
                    }

                    Console.WriteLine($"Saving to: {outputUsd}");
                    rawFile.Save(outputUsd);

                    Console.WriteLine($"SUCCESS: Imported SSS background into {outputUsd}");
                }
                else
                {
                    Console.WriteLine($"Unknown sss-bg sub-command: {subCommand}");
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --sss-bg export <mnslmap.dat> <output_dir>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --sss-bg import <project.usd> <background.dat> <output.usd>");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: SSS background operation failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        static void RunCssIconsDump(string[] args)
        {
            try
            {
                if (args.Length >= 2 && args[1] == "import")
                {
                    RunCssIconsImport(args);
                    return;
                }

                if (args.Length < 4 || args[1] != "export")
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  Export: HSDRawViewer.exe --css-icons export <dat_file> <output_dir>");
                    Console.WriteLine("  Import: HSDRawViewer.exe --css-icons import <mexSelectChr.dat> <icons_dir> <output.dat>");
                    return;
                }

                string datFile = args[2];
                string outDir = args[3];
                System.IO.Directory.CreateDirectory(outDir);

                Console.WriteLine($"Loading: {datFile}");
                var rawFile = new HSDRawFile(datFile);

                Console.WriteLine($"Roots in file: {rawFile.Roots.Count}");
                foreach (var r in rawFile.Roots)
                    Console.WriteLine($"  - {r.Name} ({r.Data?.GetType().Name})");

                string format = null;
                var manifestIcons = new List<Dictionary<string, object>>();
                var manifestOther = new List<Dictionary<string, object>>();

                // PHASE 1: try MEX format (mexSelectChr root)
                var mexRoot = rawFile.Roots.Find(r => r.Data is HSDRaw.MEX.Menus.MEX_mexSelectChr);
                if (mexRoot != null)
                {
                    format = "mex";
                    Console.WriteLine("Detected MEX format (mexSelectChr root)");

                    var mex = (HSDRaw.MEX.Menus.MEX_mexSelectChr)mexRoot.Data;
                    var iconModel = mex.IconModel;
                    if (iconModel != null)
                    {
                        // Each child JOBJ of IconModel is one CSS icon slot.
                        // Per GenerateMexSelectChr.cs: first DOBJ = background, second DOBJ = foreground icon.
                        var children = iconModel.Children;
                        Console.WriteLine($"Found {children.Length} icon slots in IconModel");

                        for (int i = 0; i < children.Length; i++)
                        {
                            var child = children[i];
                            int dobjIdx = 0;
                            var dobj = child.Dobj;
                            string fgFile = null;
                            string bgFile = null;
                            while (dobj != null)
                            {
                                var tobj = dobj.Mobj?.Textures;
                                if (tobj != null)
                                {
                                    string role = dobjIdx == 0 ? "bg" : (dobjIdx == 1 ? "fg" : $"d{dobjIdx}");
                                    string filename = $"icon_{i:D2}_{role}.png";
                                    try
                                    {
                                        using var img = tobj.ToImage();
                                        using var fs = new System.IO.FileStream(System.IO.Path.Combine(outDir, filename), System.IO.FileMode.Create);
                                        img.Save(fs, new PngEncoder());
                                        if (role == "fg") fgFile = filename;
                                        else if (role == "bg") bgFile = filename;
                                    }
                                    catch (Exception ex)
                                    {
                                        Console.WriteLine($"  Slot {i} {role}: skipped ({ex.Message})");
                                    }
                                }
                                dobj = dobj.Next;
                                dobjIdx++;
                            }

                            manifestIcons.Add(new Dictionary<string, object>
                            {
                                ["index"] = i,
                                ["foreground"] = fgFile,
                                ["background"] = bgFile,
                            });
                        }
                    }
                    else
                    {
                        Console.WriteLine("WARNING: mexSelectChr has no IconModel");
                    }
                }

                // PHASE 2: vanilla format (MnSelectChrDataTable)
                // Always run, even if MEX was detected — vanilla CSS still contains the
                // base icon strip in MenuMaterialAnimation that some tools rely on.
                var vanillaRoot = rawFile.Roots.Find(r => r.Data is HSDRaw.Melee.Mn.SBM_SelectChrDataTable);
                if (vanillaRoot != null)
                {
                    if (format == null) format = "vanilla";
                    Console.WriteLine($"Detected vanilla CSS data ({vanillaRoot.Name})");
                    var tb = (HSDRaw.Melee.Mn.SBM_SelectChrDataTable)vanillaRoot.Data;

                    // Dump static JOBJ textures from each model tree.
                    // The small icon-grid tiles live on the MenuModel JOBJ tree as
                    // static DOBJ textures, separate from the CSP tex-anims.
                    void DumpJobjStaticTextures(HSDRaw.Common.HSD_JOBJ root, string prefix, List<Dictionary<string, object>> bucket)
                    {
                        if (root == null) return;
                        int jointIdx = 0;
                        void Walk(HSDRaw.Common.HSD_JOBJ jobj)
                        {
                            int ji = jointIdx++;
                            var dobj = jobj.Dobj;
                            int dobjIdx = 0;
                            while (dobj != null)
                            {
                                var tobj = dobj.Mobj?.Textures;
                                int tobjIdx = 0;
                                while (tobj != null)
                                {
                                    string filename = $"{prefix}_static_j{ji:D3}_d{dobjIdx}_t{tobjIdx}.png";
                                    try
                                    {
                                        using var img = tobj.ToImage();
                                        int w = img.Width, h = img.Height;
                                        using var fs = new System.IO.FileStream(System.IO.Path.Combine(outDir, filename), System.IO.FileMode.Create);
                                        img.Save(fs, new PngEncoder());
                                        bucket.Add(new Dictionary<string, object>
                                        {
                                            ["filename"] = filename,
                                            ["joint_index"] = ji,
                                            ["dobj_index"] = dobjIdx,
                                            ["tobj_index"] = tobjIdx,
                                            ["section"] = prefix + "_static",
                                            ["width"] = w,
                                            ["height"] = h,
                                        });
                                    }
                                    catch { }
                                    tobj = tobj.Next;
                                    tobjIdx++;
                                }
                                dobj = dobj.Next;
                                dobjIdx++;
                            }
                            var child = jobj.Child;
                            while (child != null)
                            {
                                Walk(child);
                                child = child.Next;
                            }
                        }
                        Walk(root);
                    }

                    // For vanilla CSS icon grids, the actual small icons (64x56) are
                    // static DOBJ textures on the MenuModel's JOBJ tree. Each icon
                    // joint has 2 DOBJs: [0]=background, [1]=foreground icon.
                    // We extract DOBJ 1 for joints that have a 64x56 texture.
                    if (format == "vanilla" && tb.MenuModel != null)
                    {
                        int ji = 0;
                        void WalkIcons(HSDRaw.Common.HSD_JOBJ jobj)
                        {
                            int myJoint = ji++;
                            var dobj = jobj.Dobj;
                            // Skip to DOBJ 1 (foreground)
                            if (dobj != null && dobj.Next != null)
                            {
                                var fg = dobj.Next;
                                var tobj = fg.Mobj?.Textures;
                                if (tobj != null)
                                {
                                    try
                                    {
                                        using var img = tobj.ToImage();
                                        if (img.Width == 64 && img.Height == 56)
                                        {
                                            string filename = $"icon_j{myJoint:D3}.png";
                                            using var fs = new System.IO.FileStream(
                                                System.IO.Path.Combine(outDir, filename),
                                                System.IO.FileMode.Create);
                                            img.Save(fs, new PngEncoder());
                                            manifestIcons.Add(new Dictionary<string, object>
                                            {
                                                ["filename"] = filename,
                                                ["joint_index"] = myJoint,
                                                ["width"] = 64,
                                                ["height"] = 56,
                                            });
                                        }
                                    }
                                    catch { }
                                }
                            }
                            var child = jobj.Child;
                            while (child != null)
                            {
                                WalkIcons(child);
                                child = child.Next;
                            }
                        }
                        WalkIcons(tb.MenuModel);
                        Console.WriteLine($"Extracted {manifestIcons.Count} vanilla icon grid tiles (64x56)");
                    }

                    void DumpAnimJointTOBJs(HSDRaw.Common.Animation.HSD_MatAnimJoint root, string prefix, List<Dictionary<string, object>> bucket)
                    {
                        if (root == null) return;
                        var tree = root.TreeList;
                        for (int j = 0; j < tree.Count; j++)
                        {
                            var node = tree[j];
                            var texAnim = node.MaterialAnimation?.TextureAnimation;
                            if (texAnim == null) continue;
                            HSDRaw.Common.HSD_TOBJ[] tobjs;
                            try { tobjs = texAnim.ToTOBJs(); }
                            catch { continue; }

                            // Pull keyframes (frame -> tobj_index) for this animation when present.
                            // For vanilla CSS the texture animation cycles icons by frame number, where
                            // frame ~= fighter ExternalCharID + stride * costume_index.
                            List<Dictionary<string, object>> keyframes = null;
                            try
                            {
                                var fobj = texAnim.AnimationObject?.FObjDesc;
                                if (fobj != null)
                                {
                                    var keys = fobj.GetDecodedKeys();
                                    if (keys != null && keys.Count > 0)
                                    {
                                        keyframes = new List<Dictionary<string, object>>();
                                        foreach (var key in keys)
                                        {
                                            keyframes.Add(new Dictionary<string, object>
                                            {
                                                ["frame"] = key.Frame,
                                                ["tobj_index"] = (int)key.Value,
                                            });
                                        }
                                    }
                                }
                            }
                            catch { /* keyframes are best-effort */ }

                            for (int k = 0; k < tobjs.Length; k++)
                            {
                                string filename = $"{prefix}_j{j:D2}_{k:D2}.png";
                                try
                                {
                                    using var img = tobjs[k].ToImage();
                                    using var fs = new System.IO.FileStream(System.IO.Path.Combine(outDir, filename), System.IO.FileMode.Create);
                                    img.Save(fs, new PngEncoder());
                                    var entry = new Dictionary<string, object>
                                    {
                                        ["filename"] = filename,
                                        ["joint_index"] = j,
                                        ["tobj_index"] = k,
                                        ["section"] = prefix,
                                    };
                                    if (keyframes != null && k == 0)
                                    {
                                        // Attach the joint's keyframe schedule once (on the first tobj entry)
                                        entry["keyframes"] = keyframes;
                                    }
                                    bucket.Add(entry);
                                }
                                catch (Exception ex)
                                {
                                    Console.WriteLine($"  {filename}: skipped ({ex.Message})");
                                }
                            }
                        }
                    }

                    // MenuMaterialAnimation joints 51-54 = CSP portraits (NOT icon grid tiles).
                    // Store in 'other' bucket regardless of format.
                    DumpAnimJointTOBJs(tb.MenuMaterialAnimation, "menu", manifestOther);
                    // single-player menu icon (joint 45)
                    DumpAnimJointTOBJs(tb.SingleMenuMaterialAnimation, "single", manifestOther);
                    // big portrait (joint 6)
                    DumpAnimJointTOBJs(tb.PortraitMaterialAnimation, "portrait", manifestOther);
                }

                if (format == null)
                {
                    Console.WriteLine("ERROR: No recognized CSS data found in DAT");
                    Environment.Exit(1);
                    return;
                }

                var manifest = new Dictionary<string, object>
                {
                    ["format"] = format,
                    ["source_file"] = System.IO.Path.GetFileName(datFile),
                    ["icons"] = manifestIcons,
                    ["other"] = manifestOther,
                };
                System.IO.File.WriteAllText(
                    System.IO.Path.Combine(outDir, "manifest.json"),
                    JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true })
                );

                Console.WriteLine($"SUCCESS: Dumped {manifestIcons.Count} icons + {manifestOther.Count} other textures ({format} format)");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: CSS icons dump failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Read MEX_CSSIcon[] from MxDt.dat and write JSON describing each icon.
        /// Usage:
        ///   HSDRawViewer.exe --mex-css-info export <mxdt_file> <output.json>
        /// </summary>
        /// <summary>
        /// Convert a PNG image to MEX's .tex format.
        /// Usage:
        ///   HSDRawViewer.exe --convert-tex <input.png> <output.tex> <width> <height> <gx_format> <tlut_format>
        /// For CSS icons: --convert-tex icon.png icon.tex 64 56 8 2
        ///   (format 8 = CI8, tlut 2 = RGB5A3)
        /// </summary>
        static void RunConvertTex(string[] args)
        {
            try
            {
                if (args.Length < 7)
                {
                    Console.WriteLine("Usage: HSDRawViewer.exe --convert-tex <input.png> <output.tex> <width> <height> <gx_format> <tlut_format>");
                    Console.WriteLine("  CSS icon example: --convert-tex icon.png icon.tex 64 56 8 2");
                    return;
                }

                string inputPng = args[1];
                string outputTex = args[2];
                int width = int.Parse(args[3]);
                int height = int.Parse(args[4]);
                var format = (HSDRaw.GX.GXTexFmt)int.Parse(args[5]);
                var tlutFormat = (HSDRaw.GX.GXTlutFmt)int.Parse(args[6]);

                // Load PNG, resize to target dimensions, get BGRA pixels
                using var rawImg = SixLabors.ImageSharp.Image.Load<SixLabors.ImageSharp.PixelFormats.Bgra32>(inputPng);
                rawImg.Mutate(x => x.Resize(width, height));
                byte[] bgra = new byte[width * height * 4];
                rawImg.CopyPixelDataTo(bgra);

                // Convert BGRA → RGBA for GXImageConverter
                byte[] rgba = new byte[bgra.Length];
                for (int i = 0; i < bgra.Length; i += 4)
                {
                    rgba[i]     = bgra[i + 2]; // R
                    rgba[i + 1] = bgra[i + 1]; // G
                    rgba[i + 2] = bgra[i];     // B
                    rgba[i + 3] = bgra[i + 3]; // A
                }

                // Encode to GX format
                byte[] imageData = HSDRaw.Tools.GXImageConverter.EncodeImage(
                    rgba, width, height, format, tlutFormat, out byte[] palData);

                // Write MEX .tex format: header + image data + palette data
                using var outStream = System.IO.File.Create(outputTex);
                outStream.WriteByte((byte)'T');
                outStream.WriteByte((byte)'E');
                outStream.WriteByte((byte)'X');
                outStream.WriteByte(0); // no compression
                outStream.WriteByte((byte)format);
                outStream.WriteByte((byte)tlutFormat);
                outStream.WriteByte(0); outStream.WriteByte(0); // padding
                outStream.Write(BitConverter.GetBytes(width));
                outStream.Write(BitConverter.GetBytes(height));
                outStream.Write(BitConverter.GetBytes(0x20)); // image offset
                outStream.Write(BitConverter.GetBytes(imageData.Length));
                outStream.Write(BitConverter.GetBytes(0x20 + imageData.Length)); // palette offset
                outStream.Write(BitConverter.GetBytes(palData?.Length ?? 0));
                outStream.Write(imageData);
                if (palData != null) outStream.Write(palData);

                Console.WriteLine($"SUCCESS: {inputPng} → {outputTex} ({width}x{height}, fmt={format}, tlut={tlutFormat})");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Convert TEX failed: {ex.Message}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Import icon PNGs into a mexSelectChr.dat file.
        /// Usage:
        ///   HSDRawViewer.exe --css-icons import <mexSelectChr.dat> <icons_dir> <output.dat>
        ///
        /// icons_dir contains files named like "Mario.png", "Fox.png" etc.
        /// Each is injected into the corresponding IconModel child's foreground TOBJ,
        /// matched by slot index (icon_dir file order doesn't matter — the manifest.json
        /// from a prior export maps slot → character, and the Python caller renames
        /// files to slot indices before calling this).
        ///
        /// Actually simpler: files are named by slot index: "00.png", "01.png", ...
        /// The Python caller handles character→slot mapping.
        /// </summary>
        static void RunCssIconsImport(string[] args)
        {
            try
            {
                if (args.Length < 5)
                {
                    Console.WriteLine("Usage: HSDRawViewer.exe --css-icons import <mexSelectChr.dat> <icons_dir> <output.dat>");
                    return;
                }

                string datFile = args[2];
                string iconsDir = args[3];
                string outputDat = args[4];

                Console.WriteLine($"Loading: {datFile}");
                var rawFile = new HSDRawFile(datFile);

                var mexRoot = rawFile.Roots.Find(r => r.Data is HSDRaw.MEX.Menus.MEX_mexSelectChr);
                if (mexRoot == null)
                {
                    Console.WriteLine("ERROR: No mexSelectChr root found — only MEX format supported for import");
                    Environment.Exit(1);
                    return;
                }

                var mex = (HSDRaw.MEX.Menus.MEX_mexSelectChr)mexRoot.Data;
                var iconModel = mex.IconModel;
                if (iconModel == null)
                {
                    Console.WriteLine("ERROR: mexSelectChr has no IconModel");
                    Environment.Exit(1);
                    return;
                }

                var children = iconModel.Children;
                Console.WriteLine($"IconModel has {children.Length} slots");

                int replaced = 0;
                for (int i = 0; i < children.Length; i++)
                {
                    // Look for a PNG named by slot index: "00.png", "01.png", etc.
                    string pngPath = System.IO.Path.Combine(iconsDir, $"{i:D2}.png");
                    if (!System.IO.File.Exists(pngPath))
                        continue;

                    var child = children[i];
                    // Foreground DOBJ is the second one (index 1)
                    var dobj = child.Dobj;
                    if (dobj?.Next == null)
                    {
                        Console.WriteLine($"  Slot {i}: no foreground DOBJ, skipping");
                        continue;
                    }

                    var fgDobj = dobj.Next;
                    var tobj = fgDobj.Mobj?.Textures;
                    if (tobj == null)
                    {
                        Console.WriteLine($"  Slot {i}: no foreground TOBJ, skipping");
                        continue;
                    }

                    try
                    {
                        using var image = SixLabors.ImageSharp.Image.Load<SixLabors.ImageSharp.PixelFormats.Bgra32>(pngPath);
                        var imgFormat = tobj.ImageData.Format;
                        var palFormat = tobj.TlutData?.Format ?? HSDRaw.GX.GXTlutFmt.IA8;
                        tobj.InjectBitmap(image, imgFormat, palFormat);
                        replaced++;
                        Console.WriteLine($"  Slot {i}: replaced ({image.Width}x{image.Height})");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"  Slot {i}: failed ({ex.Message})");
                    }
                }

                rawFile.Save(outputDat);
                Console.WriteLine($"SUCCESS: Replaced {replaced}/{children.Length} icon slots → {outputDat}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: CSS icons import failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        static void RunMexCssInfo(string[] args)
        {
            try
            {
                if (args.Length < 4 || args[1] != "export")
                {
                    Console.WriteLine("Usage: HSDRawViewer.exe --mex-css-info export <mxdt_file> <output.json>");
                    return;
                }

                string mxdtFile = args[2];
                string outFile = args[3];

                Console.WriteLine($"Loading: {mxdtFile}");
                var rawFile = new HSDRawFile(mxdtFile);

                var mexRoot = rawFile.Roots.Find(r => r.Data is HSDRaw.MEX.MEX_Data);
                if (mexRoot == null)
                {
                    Console.WriteLine("ERROR: No mexData root found in file");
                    Environment.Exit(1);
                    return;
                }

                var mexData = (HSDRaw.MEX.MEX_Data)mexRoot.Data;
                var menuTable = mexData.MenuTable;
                var cssIconData = menuTable?.CSSIconData;
                if (cssIconData == null)
                {
                    Console.WriteLine("ERROR: No CSSIconData in mexData.MenuTable");
                    Environment.Exit(1);
                    return;
                }

                var icons = cssIconData.Icons ?? new HSDRaw.MEX.Menus.MEX_CSSIcon[0];
                Console.WriteLine($"Found {icons.Length} MEX CSS icons");

                var icon_entries = new List<Dictionary<string, object>>();
                foreach (var icon in icons)
                {
                    icon_entries.Add(new Dictionary<string, object>
                    {
                        ["joint_id"] = icon.JointID,
                        ["external_char_id"] = icon.ExternalCharID,
                        ["csp_lookup_index"] = icon.CSPLookupIndex,
                        ["sfx_id"] = icon.SFXID,
                        ["x1"] = icon.X1,
                        ["y1"] = icon.Y1,
                        ["x2"] = icon.X2,
                        ["y2"] = icon.Y2,
                    });
                }

                // Pull the fighter table (display names + char file symbols) when present.
                var fighter_entries = new List<Dictionary<string, object>>();
                var fighterData = mexData.FighterData;
                if (fighterData != null)
                {
                    var nameArr = fighterData.NameText?.Array ?? new HSDRaw.Common.HSD_String[0];
                    var charArr = fighterData.CharFiles?.Array ?? new HSDRaw.MEX.MEX_CharFileStrings[0];
                    int fighterCount = System.Math.Max(nameArr.Length, charArr.Length);
                    Console.WriteLine($"Fighter table: {nameArr.Length} names, {charArr.Length} char files");
                    for (int i = 0; i < fighterCount; i++)
                    {
                        string name = i < nameArr.Length ? (nameArr[i]?.Value ?? string.Empty) : string.Empty;
                        string symbol = i < charArr.Length ? (charArr[i]?.Symbol ?? string.Empty) : string.Empty;
                        string fileName = i < charArr.Length ? (charArr[i]?.FileName ?? string.Empty) : string.Empty;
                        fighter_entries.Add(new Dictionary<string, object>
                        {
                            ["internal_id"] = i,
                            ["name"] = name,
                            ["symbol"] = symbol,
                            ["file_name"] = fileName,
                        });
                    }
                }

                var output = new Dictionary<string, object>
                {
                    ["source_file"] = System.IO.Path.GetFileName(mxdtFile),
                    ["icon_count"] = icons.Length,
                    ["icons"] = icon_entries,
                    ["fighter_count"] = fighter_entries.Count,
                    ["fighters"] = fighter_entries,
                };

                System.IO.File.WriteAllText(outFile, JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
                Console.WriteLine($"SUCCESS: wrote {outFile}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: MEX CSS info failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Run sound extraction operations in headless mode.
        /// Usage:
        ///   Extract: HSDRawViewer.exe --sound extract [ssm_file] [output_dir] [--names json_file]
        /// </summary>
        static void RunSoundOperation(string[] args)
        {
            try
            {
                if (args.Length < 4)
                {
                    Console.WriteLine("Usage:");
                    Console.WriteLine("  HSDRawViewer.exe --sound extract <ssm_file> <output_dir> [--names <json_file>]");
                    Console.WriteLine();
                    Console.WriteLine("Options:");
                    Console.WriteLine("  --names <json_file>  JSON file mapping sound indices to names");
                    Console.WriteLine("                       Format: { \"0\": \"sound_name\", \"1\": \"another_sound\" }");
                    Console.WriteLine();
                    Console.WriteLine("Example:");
                    Console.WriteLine("  HSDRawViewer.exe --sound extract main.ssm ./output --names sounds.json");
                    return;
                }

                string operation = args[1]; // "extract"

                if (operation == "extract")
                {
                    string ssmFile = args[2];
                    string outputDir = args[3];

                    // Parse optional --names argument
                    string namesFile = null;
                    for (int i = 4; i < args.Length - 1; i++)
                    {
                        if (args[i] == "--names")
                        {
                            namesFile = args[i + 1];
                            break;
                        }
                    }

                    Console.WriteLine($"Extracting sounds from: {ssmFile}");
                    Console.WriteLine($"Output directory: {outputDir}");
                    if (namesFile != null)
                        Console.WriteLine($"Names file: {namesFile}");

                    // Verify SSM file exists
                    if (!System.IO.File.Exists(ssmFile))
                    {
                        Console.WriteLine($"ERROR: SSM file not found: {ssmFile}");
                        Environment.Exit(1);
                        return;
                    }

                    // Create output directory if it doesn't exist
                    if (!System.IO.Directory.Exists(outputDir))
                    {
                        System.IO.Directory.CreateDirectory(outputDir);
                        Console.WriteLine($"Created output directory: {outputDir}");
                    }

                    // Load sound name mappings if provided
                    Dictionary<int, string> soundNames = new Dictionary<int, string>();
                    if (namesFile != null && System.IO.File.Exists(namesFile))
                    {
                        try
                        {
                            string jsonContent = System.IO.File.ReadAllText(namesFile);
                            var nameDict = JsonSerializer.Deserialize<Dictionary<string, string>>(jsonContent);
                            if (nameDict != null)
                            {
                                foreach (var kvp in nameDict)
                                {
                                    if (int.TryParse(kvp.Key, out int index))
                                    {
                                        soundNames[index] = kvp.Value;
                                    }
                                }
                                Console.WriteLine($"Loaded {soundNames.Count} sound name mappings");
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"Warning: Failed to load names file: {ex.Message}");
                        }
                    }

                    // Parse SSM file
                    Console.WriteLine("Parsing SSM file...");
                    SSM ssm = new SSM();
                    ssm.Open(ssmFile);

                    Console.WriteLine($"Found {ssm.Sounds.Length} sounds (starting index: {ssm.StartIndex})");

                    // Extract each sound
                    int extractedCount = 0;
                    for (int i = 0; i < ssm.Sounds.Length; i++)
                    {
                        DSP sound = ssm.Sounds[i];
                        int soundIndex = ssm.StartIndex + i;

                        // Determine output filename
                        string fileName;
                        if (soundNames.TryGetValue(soundIndex, out string name))
                        {
                            fileName = $"{name}.wav";
                        }
                        else if (soundNames.TryGetValue(i, out string nameByArrayIndex))
                        {
                            // Also try array index (0-based)
                            fileName = $"{nameByArrayIndex}.wav";
                        }
                        else
                        {
                            fileName = $"sound_{soundIndex:D4}.wav";
                        }

                        string outputPath = System.IO.Path.Combine(outputDir, fileName);

                        try
                        {
                            sound.ExportFormat(outputPath);
                            Console.WriteLine($"  [{i + 1}/{ssm.Sounds.Length}] Exported: {fileName} ({sound.ChannelType}, {sound.Frequency}Hz, {sound.Length})");
                            extractedCount++;
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"  [{i + 1}/{ssm.Sounds.Length}] FAILED: {fileName} - {ex.Message}");
                        }
                    }

                    Console.WriteLine($"SUCCESS: Extracted {extractedCount}/{ssm.Sounds.Length} sounds to: {outputDir}");
                }
                else
                {
                    Console.WriteLine($"Unknown operation: {operation}");
                    Console.WriteLine("Use 'extract'");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR: Sound operation failed: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                Environment.Exit(1);
            }
        }

        /// <summary>
        /// Navigate to a texture (HSD_TOBJ) within a DAT file using a path and texture index.
        /// Path format: "effFoxDataTable/Models_4_/RootJoint"
        /// The texture is accessed via RootJoint -> DOBJs -> MOBJs -> TOBJs
        /// </summary>
        static HSD_TOBJ NavigateToTexture(HSDRawFile rawFile, string path, int texIndex)
        {
            try
            {
                string[] parts = path.Split('/');
                if (parts.Length == 0)
                    return null;

                // Find root by name
                var root = rawFile.Roots.Find(r => r.Name == parts[0]);
                if (root == null)
                {
                    Console.WriteLine($"Root '{parts[0]}' not found. Available roots:");
                    foreach (var r in rawFile.Roots)
                        Console.WriteLine($"  - {r.Name}");
                    return null;
                }

                HSDAccessor current = root.Data;

                // Navigate through properties
                for (int i = 1; i < parts.Length; i++)
                {
                    string part = parts[i];

                    // Handle array indexing like "Models_4_"
                    if (part.Contains("_") && char.IsDigit(part[part.LastIndexOf('_') - 1]))
                    {
                        // Find the last underscore that precedes a digit
                        int lastUnderscoreIdx = part.LastIndexOf('_');
                        // Look for pattern like "Name_N_" where N is a number
                        int secondLastUnderscore = part.LastIndexOf('_', lastUnderscoreIdx - 1);
                        if (secondLastUnderscore >= 0)
                        {
                            string propName = part.Substring(0, secondLastUnderscore);
                            string indexStr = part.Substring(secondLastUnderscore + 1, lastUnderscoreIdx - secondLastUnderscore - 1);

                            if (int.TryParse(indexStr, out int index))
                            {
                                var prop = current.GetType().GetProperty(propName);
                                if (prop == null)
                                {
                                    Console.WriteLine($"Property '{propName}' not found on type {current.GetType().Name}");
                                    return null;
                                }

                                var arr = prop.GetValue(current);
                                if (arr is Array array)
                                {
                                    current = array.GetValue(index) as HSDAccessor;
                                }
                                else
                                {
                                    Console.WriteLine($"Property '{propName}' is not an array");
                                    return null;
                                }
                                continue;
                            }
                        }
                    }

                    // Normal property access
                    var normalProp = current.GetType().GetProperty(part);
                    if (normalProp == null)
                    {
                        // Try removing trailing underscore
                        string altPart = part.TrimEnd('_');
                        normalProp = current.GetType().GetProperty(altPart);
                        if (normalProp == null)
                        {
                            Console.WriteLine($"Property '{part}' not found on type {current.GetType().Name}");
                            Console.WriteLine($"Available properties:");
                            foreach (var p in current.GetType().GetProperties())
                                Console.WriteLine($"  - {p.Name}");
                            return null;
                        }
                    }
                    current = normalProp.GetValue(current) as HSDAccessor;

                    if (current == null)
                    {
                        Console.WriteLine($"Navigation returned null at '{part}'");
                        return null;
                    }
                }

                // Now we should be at a JOBJ - traverse to find textures
                if (current is HSD_JOBJ jobj)
                {
                    Console.WriteLine("Found JOBJ, searching for textures...");
                    return FindTextureInJOBJ(jobj, texIndex);
                }
                else
                {
                    Console.WriteLine($"Expected HSD_JOBJ at end of path, got {current.GetType().Name}");
                    return null;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Navigation error: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Find a texture at the specified index within a JOBJ hierarchy.
        /// Traverses: JOBJ -> DOBJs -> MOBJs -> TOBJs
        /// </summary>
        static HSD_TOBJ FindTextureInJOBJ(HSD_JOBJ jobj, int texIndex)
        {
            var textures = new List<HSD_TOBJ>();
            CollectTexturesFromJOBJ(jobj, textures);

            Console.WriteLine($"Found {textures.Count} textures in JOBJ hierarchy");

            if (texIndex >= 0 && texIndex < textures.Count)
            {
                var tex = textures[texIndex];
                Console.WriteLine($"Texture {texIndex}: {tex.ImageData?.Width}x{tex.ImageData?.Height}, Format: {tex.ImageData?.Format}");
                return tex;
            }

            Console.WriteLine($"Texture index {texIndex} out of range (0-{textures.Count - 1})");
            return null;
        }

        /// <summary>
        /// Recursively collect all textures from a JOBJ and its children.
        /// </summary>
        static void CollectTexturesFromJOBJ(HSD_JOBJ jobj, List<HSD_TOBJ> textures)
        {
            if (jobj == null) return;

            // Check this JOBJ's DOBJs
            if (jobj.Dobj != null)
            {
                foreach (var dobj in jobj.Dobj.List)
                {
                    if (dobj.Mobj?.Textures != null)
                    {
                        foreach (var tobj in dobj.Mobj.Textures.List)
                        {
                            if (tobj.ImageData != null)
                            {
                                textures.Add(tobj);
                            }
                        }
                    }
                }
            }

            // Recurse into children
            if (jobj.Child != null)
            {
                CollectTexturesFromJOBJ(jobj.Child, textures);
            }

            // Recurse into siblings
            if (jobj.Next != null)
            {
                CollectTexturesFromJOBJ(jobj.Next, textures);
            }
        }

        /// <summary>
        /// Navigate to a JOBJ within a DAT file using a path like:
        /// "ftDataFalco/Articles/Articles_1/Model_/RootModelJoint"
        /// </summary>
        static HSD_JOBJ NavigateToJOBJ(HSDRawFile rawFile, string path)
        {
            var result = NavigateToJOBJWithParent(rawFile, path);
            return result.jobj;
        }

        /// <summary>
        /// Navigate to a JOBJ and return it along with parent info for replacement.
        /// </summary>
        static (HSD_JOBJ jobj, HSDAccessor parent, string propertyName) NavigateToJOBJWithParent(HSDRawFile rawFile, string path)
        {
            try
            {
                string[] parts = path.Split('/');
                if (parts.Length == 0)
                    return (null, null, null);

                // Find root by name
                var root = rawFile.Roots.Find(r => r.Name == parts[0]);
                if (root == null)
                {
                    Console.WriteLine($"Root '{parts[0]}' not found. Available roots:");
                    foreach (var r in rawFile.Roots)
                        Console.WriteLine($"  - {r.Name}");
                    return (null, null, null);
                }

                HSDAccessor current = root.Data;
                HSDAccessor parent = null;
                string lastPropName = null;

                // Navigate through properties
                for (int i = 1; i < parts.Length; i++)
                {
                    string part = parts[i];

                    // Handle array indexing like "Articles_1"
                    if (part.Contains("_") && !part.EndsWith("_"))
                    {
                        int lastUnderscore = part.LastIndexOf('_');
                        string propName = part.Substring(0, lastUnderscore);
                        string indexStr = part.Substring(lastUnderscore + 1);

                        if (int.TryParse(indexStr, out int index))
                        {
                            var prop = current.GetType().GetProperty(propName);
                            if (prop == null)
                            {
                                Console.WriteLine($"Property '{propName}' not found on type {current.GetType().Name}");
                                return (null, null, null);
                            }

                            var arr = prop.GetValue(current);
                            if (arr is Array array)
                            {
                                parent = current;
                                lastPropName = part;
                                current = array.GetValue(index) as HSDAccessor;
                            }
                            else
                            {
                                Console.WriteLine($"Property '{propName}' is not an array");
                                return (null, null, null);
                            }
                        }
                        else
                        {
                            // Not an array index, treat as normal property
                            var prop = current.GetType().GetProperty(part);
                            if (prop == null)
                            {
                                Console.WriteLine($"Property '{part}' not found on type {current.GetType().Name}");
                                return (null, null, null);
                            }
                            parent = current;
                            lastPropName = part;
                            current = prop.GetValue(current) as HSDAccessor;
                        }
                    }
                    else
                    {
                        var prop = current.GetType().GetProperty(part);
                        if (prop == null)
                        {
                            // Try removing trailing underscore
                            string altPart = part.TrimEnd('_');
                            prop = current.GetType().GetProperty(altPart);
                            if (prop == null)
                            {
                                Console.WriteLine($"Property '{part}' not found on type {current.GetType().Name}");
                                Console.WriteLine($"Available properties:");
                                foreach (var p in current.GetType().GetProperties())
                                    Console.WriteLine($"  - {p.Name}");
                                return (null, null, null);
                            }
                        }
                        parent = current;
                        lastPropName = part;
                        current = prop.GetValue(current) as HSDAccessor;
                    }

                    if (current == null)
                    {
                        Console.WriteLine($"Navigation returned null at '{part}'");
                        return (null, null, null);
                    }
                }

                return (current as HSD_JOBJ, parent, lastPropName);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Navigation error: {ex.Message}");
                return (null, null, null);
            }
        }

        /// <summary>
        /// Import a model file (.dae, .obj, etc.) headlessly and return the resulting JOBJ.
        /// </summary>
        static HSD_JOBJ ImportModelHeadless(string modelFile, HSD_JOBJ original)
        {
            try
            {
                // Load model using IONET
                IOScene scene = IOManager.LoadScene(modelFile, new ImportSettings { Triangulate = true });
                if (scene.Models.Count == 0)
                {
                    Console.WriteLine("No models found in file");
                    return null;
                }

                IOModel model = scene.Models[0];
                Console.WriteLine($"Loaded model with {model.Meshes.Count} meshes");

                // SMD carries no material->texture links. Resolve textures from a
                // sidecar map ("<model>.textures.json": material name -> image file,
                // relative to the model's folder) or fall back to "<material>.png".
                string modelFolder = System.IO.Path.GetDirectoryName(System.IO.Path.GetFullPath(modelFile));
                var texMap = new Dictionary<string, string>();
                string sidecar = modelFile + ".textures.json";
                if (System.IO.File.Exists(sidecar))
                {
                    using (var texDoc = System.Text.Json.JsonDocument.Parse(System.IO.File.ReadAllText(sidecar)))
                        foreach (var prop in texDoc.RootElement.EnumerateObject())
                            texMap[prop.Name] = prop.Value.GetString();
                    Console.WriteLine($"Loaded texture map with {texMap.Count} entries");
                }
                int texturesResolved = 0;
                foreach (var mat in scene.Materials)
                {
                    if (mat.DiffuseMap != null && !string.IsNullOrEmpty(mat.DiffuseMap.FilePath))
                        continue;
                    string texFile = null;
                    if (texMap.TryGetValue(mat.Name, out string mapped))
                        texFile = mapped;
                    else if (System.IO.File.Exists(System.IO.Path.Combine(modelFolder, mat.Name + ".png")))
                        texFile = mat.Name + ".png";
                    if (texFile != null)
                    {
                        mat.DiffuseMap = new IONET.Core.Model.IOTexture()
                        {
                            Name = System.IO.Path.GetFileNameWithoutExtension(texFile),
                            FilePath = texFile,
                        };
                        texturesResolved++;
                    }
                }
                Console.WriteLine($"Resolved textures for {texturesResolved}/{scene.Materials.Count} materials");

                // Remove Blender's armature root if present
                for (int i = 0; i < model.Skeleton.RootBones.Count; i++)
                {
                    if (model.Skeleton.RootBones[i].Name.Equals("Armature"))
                    {
                        model.Skeleton.RootBones[i] = model.Skeleton.RootBones[i].Child;
                        if (model.Skeleton.RootBones[i] != null)
                            model.Skeleton.RootBones[i].Parent = null;
                    }
                }

                // Preserve the original skeleton when the incoming joint tree matches its
                // structure (required for animations and netplay-legal costumes). Mirrors
                // the GUI flow in ModelImporter.ImportModelFromFile, minus the prompt.
                bool preserveSkeleton = false;
                if (original != null && model.Skeleton.RootBones.Count > 0 &&
                    ModelImporter.JointTreeIsSimilar(original, model.Skeleton))
                {
                    Console.WriteLine("Skeleton structure matches original - preserving original bones");
                    ModelImporter.ReplaceWithBonesFromFile(original, model.Skeleton.RootBones[0]);
                    preserveSkeleton = true;
                }
                else
                {
                    Console.WriteLine("WARNING: skeleton structure does not match original - bones will come from the model file");
                }

                // Create default settings
                var settings = new ModelImportSettings
                {
                    UseStrips = true,
                    ImportSkinning = true,
                    ClassicalScaling = true
                };

                // Create mesh settings for each mesh
                var meshSettings = model.Meshes.Select(m => new MeshImportSettings(m)
                {
                    FlipUVs = true,
                    ImportNormals = ImportNormalSettings.Yes
                });

                // Create material settings for each material
                var materialSettings = scene.Materials.Select(m => new MaterialImportSettings(m)
                {
                    ImportTexture = true,
                    EnableDiffuse = true
                });

                // Create importer - use absolute path for folder
                string absModelPath = System.IO.Path.GetFullPath(modelFile);
                string folderPath = System.IO.Path.GetDirectoryName(absModelPath);
                Console.WriteLine($"Model folder: {folderPath}");

                var importer = new ModelImporter(
                    folderPath,
                    scene, model, settings,
                    meshSettings, materialSettings);

                // Run import synchronously using a dummy worker
                Console.WriteLine("Running import...");
                var worker = new System.ComponentModel.BackgroundWorker();
                worker.WorkerReportsProgress = true;
                worker.ProgressChanged += (s, e) => Console.WriteLine($"Progress: {e.ProgressPercentage}%");

                // Call Work directly on current thread
                importer.Work(worker);
                Console.WriteLine("Import completed");

                // Get the result using reflection (NewModel is private)
                var newModelField = typeof(ModelImporter).GetField("NewModel",
                    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                if (newModelField != null)
                {
                    var result = newModelField.GetValue(importer) as HSD_JOBJ;
                    Console.WriteLine($"NewModel found: {result != null}");

                    // snap bone transforms back to the original's exact values
                    // (text formats lose float precision), and restore the
                    // original per-joint flags (CLASSICAL_SCALING, SKELETON,
                    // TEXGEN...) which the importer derives instead of copying
                    if (preserveSkeleton && result != null)
                    {
                        ModelImporter.ReplaceWithBonesFromFile(original, result);

                        var origJoints = original.TreeList;
                        var newJoints = result.TreeList;
                        if (origJoints.Count == newJoints.Count)
                        {
                            for (int i = 0; i < origJoints.Count; i++)
                                newJoints[i].Flags = origJoints[i].Flags;
                            Console.WriteLine($"Restored original flags on {origJoints.Count} joints");
                        }
                    }

                    return result;
                }

                Console.WriteLine("Could not access NewModel field");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Import error: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                return null;
            }
        }

        // Helper method to find JOBJ nodes in the DAT file tree
        static DataNode FindJOBJNode(DataNode node)
        {
            if (node.Accessor is HSDRaw.Common.HSD_JOBJ)
                return node;

            foreach (DataNode child in node.Nodes)
            {
                var found = FindJOBJNode(child);
                if (found != null)
                    return found;
            }
            return null;
        }

        // Helper method to find the viewport control in the form
        static HSDRawViewer.GUI.ViewportControl FindViewportControl(Control parent)
        {
            foreach (Control control in parent.Controls)
            {
                if (control is HSDRawViewer.GUI.ViewportControl viewport)
                    return viewport;

                if (control is HSDRawViewer.GUI.Controls.DockableViewport dockableViewport)
                    return dockableViewport.glViewport;

                var found = FindViewportControl(control);
                if (found != null)
                    return found;
            }
            return null;
        }

        // Helper method to hide DOBJs by direct DOBJ indices
        static void ApplyHiddenNodes(DataNode jobjRootNode, List<int> hiddenNodeIndices, HSDRawViewer.Rendering.Models.RenderJObj renderJObj = null)
        {
            if (renderJObj != null && hiddenNodeIndices.Count > 0)
            {
                Console.WriteLine($"Hiding {hiddenNodeIndices.Count} DOBJs...");

                int hiddenCount = 0;
                foreach (int dobjIndex in hiddenNodeIndices)
                {
                    if (dobjIndex >= 0 && dobjIndex < renderJObj.DObjCount)
                    {
                        renderJObj.SetDObjVisible(dobjIndex, false);
                        hiddenCount++;
                    }
                }
                Console.WriteLine($"Successfully hid {hiddenCount} DOBJs");
            }
        }

        // Helper method to apply lighting settings from YAML
        static void ApplyLightingSettings(HSDRawViewer.Rendering.Models.RenderJObj renderJObj,
            float lightX, float lightY, float lightZ,
            float ambientPower, float ambientR, float ambientG, float ambientB,
            float diffusePower, float diffuseR, float diffuseG, float diffuseB)
        {
            try
            {
                // Set to use custom lighting
                renderJObj._settings.LightSource = HSDRawViewer.Rendering.Models.LightRenderMode.Custom;

                // Configure the primary light (Light0)
                if (renderJObj._settings._lights != null && renderJObj._settings._lights.Length > 0)
                {
                    var light0 = renderJObj._settings._lights[0];
                    light0.Enabled = true;
                    light0.Type = HSDRaw.Common.LObjType.INFINITE;
                    light0._position = new OpenTK.Mathematics.Vector3(lightX, lightY, lightZ);

                    // Set diffuse light color (convert from 0-255 range to 0-1 range)
                    light0._color = new OpenTK.Mathematics.Vector4(
                        (diffuseR / 255f) * diffusePower,
                        (diffuseG / 255f) * diffusePower,
                        (diffuseB / 255f) * diffusePower,
                        1.0f
                    );

                    Console.WriteLine($"Applied lighting: Position({lightX}, {lightY}, {lightZ}), " +
                                    $"Diffuse({diffuseR}, {diffuseG}, {diffuseB}) * {diffusePower}, " +
                                    $"Ambient({ambientR}, {ambientG}, {ambientB}) * {ambientPower}");
                }

                // Configure ambient lighting if there's a second light slot
                if (renderJObj._settings._lights.Length > 1)
                {
                    var ambientLight = renderJObj._settings._lights[1];
                    ambientLight.Enabled = true;
                    ambientLight.Type = HSDRaw.Common.LObjType.AMBIENT;

                    // Set ambient light color
                    ambientLight._color = new OpenTK.Mathematics.Vector4(
                        (ambientR / 255f) * ambientPower,
                        (ambientG / 255f) * ambientPower,
                        (ambientB / 255f) * ambientPower,
                        1.0f
                    );
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error applying lighting settings: {ex.Message}");
            }
        }

    }

    // Simple drawable wrapper for RenderJObj
    public class SimpleJObjDrawable : IDrawable
    {
        public DrawOrder DrawOrder => DrawOrder.First;
        private readonly RenderJObj _renderJObj;

        public SimpleJObjDrawable(RenderJObj renderJObj)
        {
            _renderJObj = renderJObj;
        }

        public void GLInit()
        {
            // RenderJObj handles its own OpenGL initialization
        }

        public void GLFree()
        {
            // RenderJObj handles its own OpenGL cleanup
        }

        public void Draw(Camera cam, int windowWidth, int windowHeight)
        {
            _renderJObj.Render(cam);
        }
    }

    // Helper class to write to multiple TextWriters simultaneously
    public class MultiTextWriter : System.IO.TextWriter
    {
        private System.IO.TextWriter[] writers;

        public MultiTextWriter(params System.IO.TextWriter[] writers)
        {
            this.writers = writers;
        }

        public override void Write(char value)
        {
            foreach (var writer in writers)
                writer.Write(value);
        }

        public override void WriteLine(string value)
        {
            foreach (var writer in writers)
                writer.WriteLine(value);
        }

        public override System.Text.Encoding Encoding
        {
            get { return System.Text.Encoding.UTF8; }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                foreach (var writer in writers)
                    writer.Dispose();
            }
            base.Dispose(disposing);
        }
    }
}
