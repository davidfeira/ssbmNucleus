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

            // Check for MEX CSS info mode (reads MxDt.dat icon -> fighter mapping)
            if (args.Length >= 1 && args[0] == "--mex-css-info")
            {
                Console.WriteLine("MEX CSS info mode detected");
                RunMexCssInfo(args);
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

                // Create a form to host the viewport (hidden)
                using (var form = new Form())
                {
                    form.WindowState = FormWindowState.Minimized;
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
