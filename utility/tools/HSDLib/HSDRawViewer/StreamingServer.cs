using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using HSDRaw;
using HSDRaw.Common;
using HSDRaw.Common.Animation;
using HSDRaw.Melee.Pl;
using HSDRaw.Tools.Melee;
using HSDRawViewer.GUI;
using HSDRawViewer.GUI.Plugins.SubactionEditor;
using HSDRawViewer.Rendering;
using HSDRawViewer.Rendering.Models;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.PixelFormats;
using SixLabors.ImageSharp.Formats.Jpeg;
using HSDRawViewer.Converters.Animation;
using HSDRawViewer.Tools;
using HSDRawViewer.GUI.Controls.JObjEditor;

namespace HSDRawViewer
{
    /// <summary>
    /// WebSocket streaming server for 3D model viewing
    /// Handles headless rendering and frame streaming to web clients
    /// </summary>
    public class StreamingServer : IDisposable
    {
        private HttpListener _httpListener;
        private ViewportControl _viewport;
        private RenderJObj _renderJObj;
        private Form _hostForm;
        private CancellationTokenSource _cts;
        private int _port;
        private int _frameWidth = 1280;
        private int _frameHeight = 960;
        private int _targetFps = 60;
        private bool _isRunning = false;
        private WebSocket _currentClient = null;
        private StreamWriter _logWriter;
        private string _logPath;

        // Animation state
        private bool _animationPlaying = false;
        private float _animationFrame = 0;
        private float _animationFrameCount = 0;
        private float _animationSpeed = 1.0f;

        // Animation archive manager (for loading real Melee animations)
        private FighterAJManager _ajManager;

        // Per-animation model-part visibility (Bowser shell, Link's bow, ...).
        // Shared with EmbeddedServer via ModelPartVisibility. See
        // docs/ANIMATION_PART_VISIBILITY.md.
        private ModelPartVisibility _partVis;

        // Cached texture list (populated after first render to avoid Invoke deadlocks)
        private List<TextureInfo> _cachedTextureList = null;

        // Lock to serialize WebSocket sends (prevent concurrent sends from corrupting connection)
        private SemaphoreSlim _sendLock = new SemaphoreSlim(1, 1);

        // Store the raw file and path for exporting modified DAT
        private HSDRaw.HSDRawFile _rawFile = null;
        private string _datFilePath = null;

        public StreamingServer(int port, string logPath = null)
        {
            _port = port;
            _cts = new CancellationTokenSource();
            _logPath = logPath;
            InitializeLogging();
        }

        private void InitializeLogging()
        {
            try
            {
                if (string.IsNullOrEmpty(_logPath))
                {
                    // Default to a logs folder relative to the executable
                    var exeDir = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
                    _logPath = Path.Combine(exeDir, "..", "..", "..", "..", "..", "..", "..", "logs");
                }

                // Create logs directory if it doesn't exist
                Directory.CreateDirectory(_logPath);

                var logFile = Path.Combine(_logPath, $"viewer_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}.log");
                _logWriter = new StreamWriter(logFile, append: true) { AutoFlush = true };
                Log($"=== HSDRawViewer Streaming Server Started ===");
                Log($"Log file: {logFile}");
                HSDRawViewer.Rendering.Models.RenderJObj.UpdateLog = Log;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to initialize logging: {ex.Message}");
                // Continue without file logging
            }
        }

        private void Log(string message)
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
            var logLine = $"[{timestamp}] {message}";
            // Don't use Console.WriteLine - blocks when stdout buffer fills (backend doesn't read it)
            try
            {
                _logWriter?.WriteLine(logLine);
            }
            catch { /* Ignore logging errors */ }
        }

        private void LogError(string message, Exception ex = null)
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
            var logLine = $"[{timestamp}] ERROR: {message}";
            if (ex != null)
            {
                logLine += $"\n  Exception: {ex.GetType().Name}: {ex.Message}\n  Stack: {ex.StackTrace}";
            }
            // Don't use Console.WriteLine - blocks when stdout buffer fills
            try
            {
                _logWriter?.WriteLine(logLine);
            }
            catch { /* Ignore logging errors */ }
        }

        public async Task StartAsync(string datFilePath, string sceneFilePath = null, string ajFilePath = null, string dataFilePath = null)
        {
            Log($"Starting streaming server on port {_port}...");
            Log($"Loading DAT file: {datFilePath}");
            if (!string.IsNullOrEmpty(sceneFilePath))
                Log($"Scene file: {sceneFilePath}");
            if (!string.IsNullOrEmpty(ajFilePath))
                Log($"AJ file: {ajFilePath}");

            // Initialize core systems
            Thread.CurrentThread.CurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
            PluginManager.Init();
            ApplicationSettings.Init();

            // Load DAT file
            if (!File.Exists(datFilePath))
            {
                LogError($"DAT file not found: {datFilePath}");
                throw new FileNotFoundException($"DAT file not found: {datFilePath}");
            }

            // Use MainForm like CSP mode does - this properly loads all model data
            Log("Initializing MainForm...");
            MainForm.Init();
            MainForm.Instance.OpenFile(datFilePath);

            // Wait for file to load
            Log("Waiting for file to load...");
            Thread.Sleep(500);

            // Load the DAT file to find JOBJ nodes
            Log("Opening DAT file...");
            _rawFile = new HSDRaw.HSDRawFile();
            _rawFile.Open(datFilePath);
            _datFilePath = datFilePath;
            var rawFile = _rawFile; // Keep local var for rest of method
            Log($"DAT file opened. Root count: {rawFile.Roots.Count}");

            // Find character JOBJ
            DataNode characterJobjNode = null;
            foreach (var root in rawFile.Roots)
            {
                Log($"  Root: {root.Name} -> {root.Data?.GetType().Name ?? "null"}");
                if (root.Data is HSD_JOBJ &&
                    (root.Name.Contains("Share_joint") || root.Name.Contains("_joint") || root.Name.Contains("Ply")))
                {
                    Log($"Found character JOBJ: {root.Name}");
                    characterJobjNode = new DataNode(root.Name, root.Data, root: root);
                    break;
                }
            }

            if (characterJobjNode == null)
            {
                // Fallback to first JOBJ
                foreach (var root in rawFile.Roots)
                {
                    if (root.Data is HSD_JOBJ)
                    {
                        Log($"Using fallback JOBJ: {root.Name}");
                        characterJobjNode = new DataNode(root.Name, root.Data, root: root);
                        break;
                    }
                }
            }

            if (characterJobjNode == null)
            {
                LogError("No JOBJ found in DAT file");
                throw new Exception("No JOBJ found in DAT file");
            }

            // Select the node and open editor like CSP mode does
            Log($"Selecting character JOBJ: {characterJobjNode.Text}");
            MainForm.SelectedDataNode = characterJobjNode;
            MainForm.Instance.OpenEditor();

            // Wait for editor to open
            Thread.Sleep(1000);

            // Create viewport and render object
            Log("Creating ViewportControl...");
            _viewport = new ViewportControl();

            if (characterJobjNode.Accessor is HSD_JOBJ jobj)
            {
                Log("Creating RenderJObj...");
                _renderJObj = new RenderJObj(jobj);
                _renderJObj._settings.RenderBones = false;
                _renderJObj._settings.RenderObjects = ObjectRenderMode.Visible;

                // MatAnim swap frames (blink textures etc.) hide in
                // matanim_joint roots -- register them so the texture list
                // and texture updates cover them.
                var matAnimRoots = rawFile.Roots
                    .Where(r => r.Data is HSDRaw.Common.Animation.HSD_MatAnimJoint)
                    .Select(r => (HSDRaw.Common.Animation.HSD_MatAnimJoint)r.Data)
                    .ToList();
                if (matAnimRoots.Count > 0)
                {
                    _renderJObj.SetMatAnims(matAnimRoots);
                    Log($"Registered {matAnimRoots.Count} matanim root(s)");
                }

                // Costume accessories can ship as EXTRA JOBJ roots (e.g.
                // Jigglypuff's alt-costume hats: Ply*Hat_TopN_joint) -- the
                // render model only walks the character root, so register
                // the rest for texture-list/update coverage.
                var extraJobjRoots = rawFile.Roots
                    .Where(r => r.Data is HSD_JOBJ && !ReferenceEquals(r.Data, jobj))
                    .Select(r => (HSD_JOBJ)r.Data)
                    .ToList();
                if (extraJobjRoots.Count > 0)
                {
                    _renderJObj.SetExtraRoots(extraJobjRoots);
                    Log($"Registered {extraJobjRoots.Count} extra JOBJ root(s)");
                }

                var drawable = new SimpleJObjDrawable(_renderJObj);
                _viewport.AddRenderer(drawable);
                Log($"RenderJObj created. DOBJs: {_renderJObj.DObjCount}");
            }

            // Create host form. The window must exist and be "visible" for the
            // OpenGL context (minimizing breaks it), but nobody needs to SEE it:
            // frames are read back via GenerateBitmap. Park it far offscreen so
            // headless/streaming sessions don't pop windows over the user's work.
            Log("Creating host form...");
            _hostForm = new Form();
            _hostForm.StartPosition = FormStartPosition.Manual;
            _hostForm.Location = new System.Drawing.Point(-32000, 100);
            _hostForm.ShowInTaskbar = false;
            _hostForm.Size = new System.Drawing.Size(_frameWidth + 50, _frameHeight + 50);
            _hostForm.Text = "HSD Viewer (Streaming)";
            // Don't minimize - keep visible to ensure OpenGL works
            _viewport.Dock = DockStyle.Fill;
            _hostForm.Controls.Add(_viewport);
            _hostForm.Show();

            // Pump messages to let OpenGL initialize properly
            Log("Waiting for OpenGL initialization...");
            for (int i = 0; i < 100; i++)  // Pump messages for ~1s
            {
                Application.DoEvents();
                Thread.Sleep(10);
            }

            // Set up viewport
            Log("Setting up viewport...");
            _viewport.EnableBack = true;
            _viewport.DisplayGrid = false;  // Hide grid for cleaner CSP-style view

            // Load scene settings if provided
            SceneSettings sceneSettings = null;
            if (!string.IsNullOrEmpty(sceneFilePath) && File.Exists(sceneFilePath))
            {
                try
                {
                    Log($"Loading scene settings from: {sceneFilePath}");
                    sceneSettings = SceneSettings.Deserialize(sceneFilePath);

                    // Apply camera settings
                    if (sceneSettings.Camera != null)
                    {
                        Log($"Applying camera: X={sceneSettings.Camera.X}, Y={sceneSettings.Camera.Y}, Scale={sceneSettings.Camera.Scale}");
                        _viewport.Camera.X = sceneSettings.Camera.X;
                        _viewport.Camera.Y = sceneSettings.Camera.Y;
                        _viewport.Camera.Z = sceneSettings.Camera.Z;
                        _viewport.Camera.Scale = sceneSettings.Camera.Scale;
                        _viewport.Camera.FovRadians = sceneSettings.Camera.FovRadians;
                        _viewport.Camera.RotationXRadians = sceneSettings.Camera.RotationXRadians;
                        _viewport.Camera.RotationYRadians = sceneSettings.Camera.RotationYRadians;
                        _viewport.Camera.FarClipPlane = sceneSettings.Camera.FarClipPlane;
                        _viewport.Camera.NearClipPlane = sceneSettings.Camera.NearClipPlane;
                    }

                    // Load animation
                    if (sceneSettings.Animation != null && _renderJObj != null)
                    {
                        Log($"Loading animation (FrameCount: {sceneSettings.Animation.FrameCount})");
                        _renderJObj.LoadAnimation(sceneSettings.Animation, null, null);
                        _animationFrameCount = sceneSettings.Animation.FrameCount;

                        // Set to the specified frame
                        _animationFrame = Math.Max(0, sceneSettings.Frame);
                        Log($"Setting animation frame: {_animationFrame}");
                        _renderJObj.RequestAnimationUpdate(FrameFlags.All, _animationFrame);
                    }

                    // Apply other scene settings
                    _viewport.DisplayGrid = sceneSettings.ShowGrid;
                    _viewport.EnableBack = sceneSettings.ShowBackdrop;

                    Log("Scene settings applied successfully");
                }
                catch (Exception ex)
                {
                    LogError("Failed to load scene settings", ex);
                }
            }

            Log($"Current camera: Scale={_viewport.Camera.Scale}");

            // Force a render
            Log("Performing initial render...");
            Application.DoEvents();
            _viewport.Render();
            Application.DoEvents();

            // Check DOBJs again after render (they may be loaded lazily)
            if (_renderJObj != null)
            {
                Log($"After first render - DOBJs: {_renderJObj.DObjCount}");

                // Per-animation model-part visibility (shared with EmbeddedServer).
                // Apply the default state immediately so the first frame starts
                // with low-poly/alternate parts hidden.
                _partVis = new ModelPartVisibility(_renderJObj, Log, LogError);
                _partVis.LoadFighterData(dataFilePath);
                _partVis.ApplyDefaultState();
                Application.DoEvents();
                _viewport.Render();
                Application.DoEvents();

                // Apply hidden nodes now that DOBJs are loaded
                if (sceneSettings?.HiddenNodes != null && sceneSettings.HiddenNodes.Length > 0)
                {
                    Log($"Hiding {sceneSettings.HiddenNodes.Length} DOBJs...");
                    int hiddenCount = 0;
                    foreach (int dobjIndex in sceneSettings.HiddenNodes)
                    {
                        if (dobjIndex >= 0 && dobjIndex < _renderJObj.DObjCount)
                        {
                            _renderJObj.SetDObjVisible(dobjIndex, false);
                            hiddenCount++;
                        }
                    }
                    Log($"Successfully hid {hiddenCount} DOBJs");

                    // Re-render to apply visibility changes
                    Application.DoEvents();
                    _viewport.Render();
                    Application.DoEvents();
                }

                // Cache texture list after initial render
                _cachedTextureList = _renderJObj.GetTextureList();
                Log($"Cached {_cachedTextureList.Count} textures");
            }

            // Log viewport/control sizes for debugging
            Log($"Host form size: {_hostForm.Width}x{_hostForm.Height}");
            Log($"Viewport size: {_viewport.Width}x{_viewport.Height}");

            // Force the form to process layout
            _hostForm.PerformLayout();
            Application.DoEvents();

            Log($"After layout - Host form size: {_hostForm.Width}x{_hostForm.Height}");
            Log($"After layout - Viewport size: {_viewport.Width}x{_viewport.Height}");

            // Save a debug frame to check what's being rendered
            try
            {
                using var debugBitmap = _viewport.GenerateBitmap(_frameWidth, _frameHeight);
                var debugPath = Path.Combine(_logPath, "debug_frame.png");
                debugBitmap.SaveAsPng(debugPath);
                Log($"Debug frame saved to: {debugPath}");
            }
            catch (Exception ex)
            {
                LogError("Failed to save debug frame", ex);
            }

            Log($"Viewport ready. Starting HTTP listener...");

            // Load animation archive if provided
            if (!string.IsNullOrEmpty(ajFilePath) && File.Exists(ajFilePath))
            {
                try
                {
                    Log($"Loading AJ file: {ajFilePath}");
                    _ajManager = new FighterAJManager(File.ReadAllBytes(ajFilePath));
                    var animCount = _ajManager.GetAnimationSymbols().Count();
                    Log($"Loaded {animCount} animations from AJ file");
                }
                catch (Exception ex)
                {
                    LogError("Failed to load AJ file", ex);
                }
            }

            // Start HTTP/WebSocket listener
            _httpListener = new HttpListener();
            _httpListener.Prefixes.Add($"http://localhost:{_port}/");
            _httpListener.Start();

            _isRunning = true;
            Log($"Streaming server listening on ws://localhost:{_port}/");
            Log("Waiting for client connection...");

            // Start connection handler in background
            _ = Task.Run(() => AcceptConnectionsAsync());

            // Run message pump on main thread to keep UI responsive
            Log("Starting message pump...");
            while (_isRunning && !_cts.Token.IsCancellationRequested)
            {
                Application.DoEvents();
                Thread.Sleep(16);  // ~60fps message pump
            }
        }

        private async Task AcceptConnectionsAsync()
        {
            while (_isRunning && !_cts.Token.IsCancellationRequested)
            {
                try
                {
                    var context = await _httpListener.GetContextAsync();
                    Log($"Incoming request: {context.Request.HttpMethod} {context.Request.Url} IsWebSocket: {context.Request.IsWebSocketRequest}");

                    // Add CORS headers for all responses
                    context.Response.Headers.Add("Access-Control-Allow-Origin", "*");
                    context.Response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
                    context.Response.Headers.Add("Access-Control-Allow-Headers", "*");

                    if (context.Request.IsWebSocketRequest)
                    {
                        Log("Accepting WebSocket connection...");
                        var wsContext = await context.AcceptWebSocketAsync(null);
                        Log("Client connected!");
                        await HandleClientAsync(wsContext.WebSocket);
                    }
                    else
                    {
                        // Handle regular HTTP request (health check)
                        context.Response.StatusCode = 200;
                        context.Response.ContentType = "text/plain";
                        var buffer = Encoding.UTF8.GetBytes("Streaming server running");
                        context.Response.ContentLength64 = buffer.Length;
                        await context.Response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
                        context.Response.Close();
                    }
                }
                catch (Exception ex) when (!_cts.Token.IsCancellationRequested)
                {
                    LogError("Connection error", ex);
                }
            }
        }

        private async Task HandleClientAsync(WebSocket webSocket)
        {
            _currentClient = webSocket;
            var receiveBuffer = new byte[65536]; // 64KB for texture data
            var frameInterval = TimeSpan.FromMilliseconds(1000.0 / _targetFps);
            var lastFrameTime = DateTime.UtcNow;
            int frameCount = 0;
            var startTime = DateTime.UtcNow;

            try
            {
                // Send initial info with camera state and animation info
                var info = new
                {
                    type = "info",
                    width = _frameWidth,
                    height = _frameHeight,
                    fps = _targetFps,
                    dobjCount = _renderJObj?.DObjCount ?? 0,
                    camera = new
                    {
                        rotX = _viewport.Camera.RotationXRadians * 180.0 / Math.PI,
                        rotY = _viewport.Camera.RotationYRadians * 180.0 / Math.PI,
                        scale = _viewport.Camera.Scale,
                        x = _viewport.Camera.X,
                        y = _viewport.Camera.Y,
                        z = _viewport.Camera.Z
                    },
                    animation = new
                    {
                        frameCount = _animationFrameCount,
                        currentFrame = _animationFrame,
                        playing = _animationPlaying,
                        speed = _animationSpeed
                    }
                };
                await SendJsonAsync(webSocket, info);
                Log($"Sent initial info: {_frameWidth}x{_frameHeight} @ {_targetFps}fps, animation frames={_animationFrameCount}");

                // Create receive task
                var receiveTask = ReceiveMessagesAsync(webSocket, receiveBuffer);

                // Frame streaming loop
                while (webSocket.State == WebSocketState.Open && !_cts.Token.IsCancellationRequested)
                {
                    var now = DateTime.UtcNow;
                    var elapsed = now - lastFrameTime;

                    if (elapsed >= frameInterval)
                    {
                        lastFrameTime = now;

                        // Render and send frame on UI thread (OpenGL context is thread-bound)
                        try
                        {
                            Image<Rgba32> bitmap = null;

                            // Must render on the UI thread where OpenGL context was created
                            _hostForm.Invoke((Action)(() =>
                            {
                                Application.DoEvents();

                                // Update animation if playing
                                if (_animationPlaying && _animationFrameCount > 0 && _renderJObj != null)
                                {
                                    _animationFrame += _animationSpeed;
                                    if (_animationFrame >= _animationFrameCount)
                                        _animationFrame = 0;
                                    else if (_animationFrame < 0)
                                        _animationFrame = _animationFrameCount - 1;

                                    _renderJObj.RequestAnimationUpdate(FrameFlags.All, _animationFrame);
                                    _partVis?.ApplyFrame(_animationFrame);
                                }

                                bitmap = _viewport.GenerateBitmap(_frameWidth, _frameHeight);
                            }));

                            if (bitmap == null) continue;

                            byte[] frameData;
                            using (bitmap)
                            using (var ms = new MemoryStream())
                            {
                                // Encode as JPEG
                                var encoder = new JpegEncoder { Quality = 75 };
                                bitmap.Save(ms, encoder);
                                frameData = ms.ToArray();
                            }

                            await SendBinaryAsync(webSocket, frameData);

                            frameCount++;
                        }
                        catch (Exception ex)
                        {
                            LogError("Frame render/send error", ex);
                        }
                    }

                    // Small delay to prevent busy-waiting
                    await Task.Delay(5);
                }
            }
            catch (WebSocketException ex)
            {
                LogError("WebSocket error", ex);
            }
            finally
            {
                _currentClient = null;
                var totalElapsed = (DateTime.UtcNow - startTime).TotalSeconds;
                Log($"Client disconnected. Streamed {frameCount} frames in {totalElapsed:F1}s ({frameCount / totalElapsed:F1} fps avg)");

                if (webSocket.State == WebSocketState.Open)
                {
                    await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
                }
            }
        }

        private async Task ReceiveMessagesAsync(WebSocket webSocket, byte[] buffer)
        {
            try
            {
                // Use a MemoryStream to accumulate fragmented messages
                using var messageBuffer = new MemoryStream();

                while (webSocket.State == WebSocketState.Open && !_cts.Token.IsCancellationRequested)
                {
                    var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), _cts.Token);

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        Log("Received close message from client");
                        break;
                    }

                    if (result.MessageType == WebSocketMessageType.Text)
                    {
                        // Accumulate message fragments
                        messageBuffer.Write(buffer, 0, result.Count);

                        // Only process when we have the complete message
                        if (result.EndOfMessage)
                        {
                            var message = Encoding.UTF8.GetString(messageBuffer.ToArray());
                            messageBuffer.SetLength(0); // Clear for next message
                            await ProcessCommandAsync(webSocket, message);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                LogError("Receive error", ex);
            }
        }

        private async Task ProcessCommandAsync(WebSocket webSocket, string json)
        {
            try
            {
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;

                if (!root.TryGetProperty("type", out var typeElement))
                    return;

                var type = typeElement.GetString();

                switch (type)
                {
                    case "camera":
                        // Delta-based rotation (in degrees)
                        if (root.TryGetProperty("deltaRotX", out var deltaRotX))
                            _viewport.Camera.RotationXRadians += (float)(deltaRotX.GetDouble() * Math.PI / 180.0);
                        if (root.TryGetProperty("deltaRotY", out var deltaRotY))
                            _viewport.Camera.RotationYRadians += (float)(deltaRotY.GetDouble() * Math.PI / 180.0);

                        // Delta-based zoom (additive to scale)
                        if (root.TryGetProperty("deltaZoom", out var deltaZoom))
                        {
                            _viewport.Camera.Scale *= (float)(1.0 + deltaZoom.GetDouble());
                            _viewport.Camera.Scale = Math.Max(0.1f, Math.Min(1000f, _viewport.Camera.Scale));
                        }

                        // Delta-based pan
                        if (root.TryGetProperty("deltaX", out var deltaX))
                            _viewport.Camera.X += (float)deltaX.GetDouble();
                        if (root.TryGetProperty("deltaY", out var deltaY))
                            _viewport.Camera.Y += (float)deltaY.GetDouble();
                        break;

                    case "resize":
                        if (root.TryGetProperty("width", out var w))
                            _frameWidth = Math.Clamp(w.GetInt32(), 320, 1920);
                        if (root.TryGetProperty("height", out var h))
                            _frameHeight = Math.Clamp(h.GetInt32(), 240, 1080);
                        Log($"Resized to {_frameWidth}x{_frameHeight}");
                        break;

                    case "fps":
                        if (root.TryGetProperty("value", out var fps))
                        {
                            _targetFps = Math.Clamp(fps.GetInt32(), 1, 60);
                            Log($"FPS changed to {_targetFps}");
                        }
                        break;

                    case "animPlay":
                        _animationPlaying = true;
                        Log("Animation playing");
                        break;

                    case "animPause":
                        _animationPlaying = false;
                        Log("Animation paused");
                        break;

                    case "animToggle":
                        _animationPlaying = !_animationPlaying;
                        Log($"Animation {(_animationPlaying ? "playing" : "paused")}");
                        break;

                    case "animSetFrame":
                        if (root.TryGetProperty("frame", out var frameVal))
                        {
                            _animationFrame = (float)frameVal.GetDouble();
                            _animationFrame = Math.Clamp(_animationFrame, 0, Math.Max(0, _animationFrameCount - 1));
                            if (_renderJObj != null)
                            {
                                _renderJObj.RequestAnimationUpdate(FrameFlags.All, _animationFrame);
                                _partVis?.ApplyFrame(_animationFrame);
                            }
                        }
                        break;

                    case "animSetSpeed":
                        if (root.TryGetProperty("speed", out var speedVal))
                        {
                            _animationSpeed = (float)speedVal.GetDouble();
                            Log($"Animation speed: {_animationSpeed}");
                        }
                        break;

                    case "getAnimList":
                        // Return list of available animations from AJ file
                        Log($"Processing getAnimList, _ajManager is {(_ajManager != null ? "set" : "null")}");
                        try
                        {
                            if (_ajManager != null)
                            {
                                var symbols = _ajManager.GetAnimationSymbols().ToArray();
                                Log($"Sending animation list: {symbols.Length} animations");
                                await SendJsonAsync(webSocket, new { type = "animList", symbols });
                            }
                            else
                            {
                                Log("No AJ file loaded, sending empty animation list");
                                await SendJsonAsync(webSocket, new { type = "animList", symbols = Array.Empty<string>() });
                            }
                        }
                        catch (Exception ex)
                        {
                            LogError("Error in getAnimList", ex);
                            await SendJsonAsync(webSocket, new { type = "animList", symbols = Array.Empty<string>() });
                        }
                        break;

                    case "getTextures":
                        // Return cached texture list (thumbnails for sidebar)
                        try
                        {
                            if (_cachedTextureList != null)
                            {
                                var textureList = _cachedTextureList.Select(t => new
                                {
                                    index = t.Index,
                                    width = t.Width,
                                    height = t.Height,
                                    name = t.Name,
                                    thumbnail = t.ThumbnailBase64,
                                    matAnim = t.IsMatAnim,
                                    animates = t.AnimatesIndex,
                                    extra = t.IsExtraRoot
                                }).ToList();
                                await SendJsonAsync(webSocket, new { type = "textureList", textures = textureList });
                            }
                            else
                            {
                                await SendJsonAsync(webSocket, new { type = "textureList", textures = Array.Empty<object>() });
                            }
                        }
                        catch (Exception ex)
                        {
                            LogError("Error in getTextures", ex);
                            await SendJsonAsync(webSocket, new { type = "textureList", textures = Array.Empty<object>() });
                        }
                        break;

                    case "getFullTexture":
                        // Return full resolution texture for editor
                        try
                        {
                            if (root.TryGetProperty("index", out var texIdxProp) && _cachedTextureList != null)
                            {
                                int texIndex = texIdxProp.GetInt32();
                                if (texIndex >= 0 && texIndex < _cachedTextureList.Count)
                                {
                                    var tex = _cachedTextureList[texIndex];
                                    // Convert BGRA to RGBA and encode as PNG
                                    byte[] rgbaData = new byte[tex.RgbaData.Length];
                                    for (int i = 0; i < tex.RgbaData.Length; i += 4)
                                    {
                                        rgbaData[i + 0] = tex.RgbaData[i + 2]; // R
                                        rgbaData[i + 1] = tex.RgbaData[i + 1]; // G
                                        rgbaData[i + 2] = tex.RgbaData[i + 0]; // B
                                        rgbaData[i + 3] = tex.RgbaData[i + 3]; // A
                                    }
                                    using var image = SixLabors.ImageSharp.Image.LoadPixelData<Rgba32>(rgbaData, tex.Width, tex.Height);
                                    using var ms = new MemoryStream();
                                    image.Save(ms, new SixLabors.ImageSharp.Formats.Png.PngEncoder());
                                    string base64Data = Convert.ToBase64String(ms.ToArray());
                                    await SendJsonAsync(webSocket, new { type = "fullTexture", index = texIndex, width = tex.Width, height = tex.Height, data = base64Data });
                                }
                                else
                                {
                                    await SendJsonAsync(webSocket, new { type = "fullTexture", error = "Invalid texture index" });
                                }
                            }
                        }
                        catch (Exception ex)
                        {
                            LogError("Error in getFullTexture", ex);
                            await SendJsonAsync(webSocket, new { type = "fullTexture", error = ex.Message });
                        }
                        break;

                    case "getUVLayout":
                        // Per-texture UV triangles + posed world positions, for
                        // UV-aware (projection) compositing in the skin lab.
                        try
                        {
                            if (_renderJObj == null || _cachedTextureList == null)
                            {
                                await SendJsonAsync(webSocket, new { type = "uvLayout", error = "no model loaded" });
                                break;
                            }
                            List<object> layout = null;
                            Exception layoutError = null;
                            var done = new TaskCompletionSource<object>();
                            // run on the UI thread: reads LiveJObj transforms the
                            // render loop owns
                            _hostForm.BeginInvoke((Action)(() =>
                            {
                                try
                                {
                                    layout = _renderJObj.GetUVLayout(_cachedTextureList);
                                }
                                catch (Exception ex)
                                {
                                    layoutError = ex;
                                }
                                finally
                                {
                                    done.TrySetResult(null);
                                }
                            }));
                            await done.Task;
                            if (layoutError != null)
                            {
                                LogError("Error in getUVLayout", layoutError);
                                await SendJsonAsync(webSocket, new { type = "uvLayout", error = layoutError.Message });
                            }
                            else
                            {
                                Log($"getUVLayout: {layout.Count} textures with geometry");
                                await SendJsonAsync(webSocket, new { type = "uvLayout", textures = layout });
                            }
                        }
                        catch (Exception ex)
                        {
                            LogError("Error in getUVLayout", ex);
                            await SendJsonAsync(webSocket, new { type = "uvLayout", error = ex.Message });
                        }
                        break;

                    case "updateTexture":
                        // Update a texture with new image data
                        try
                        {
                            if (root.TryGetProperty("index", out var indexProp) &&
                                root.TryGetProperty("data", out var dataProp))
                            {
                                int texIndex = indexProp.GetInt32();
                                string base64Data = dataProp.GetString();
                                byte[] pngData = Convert.FromBase64String(base64Data);

                                // Use BeginInvoke to avoid deadlock (the UI thread must
                                // never wait on this socket). Update via the CACHED
                                // TextureInfo -- the client's indexes refer to
                                // _cachedTextureList, and a fresh enumeration inside
                                // UpdateTexture(int) can drift from it.
                                // The ack must only go out AFTER the UI thread applied
                                // the update: clients treat it as "applied", and acking
                                // early let frame grabs race a backlog of pending
                                // updates (stale review-sheet panels).
                                var applied = new TaskCompletionSource<object>();
                                _hostForm.BeginInvoke((Action)(() =>
                                {
                                    try
                                    {
                                        if (_cachedTextureList != null
                                            && texIndex >= 0 && texIndex < _cachedTextureList.Count)
                                        {
                                            _renderJObj.UpdateTexture(_cachedTextureList[texIndex], pngData);
                                        }
                                        else
                                        {
                                            _renderJObj.UpdateTexture(texIndex, pngData);
                                        }
                                    }
                                    catch (Exception ex)
                                    {
                                        LogError($"Error updating texture {texIndex}", ex);
                                    }
                                    finally
                                    {
                                        applied.TrySetResult(null);
                                    }
                                }));
                                await applied.Task;

                                await SendJsonAsync(webSocket, new { type = "textureUpdated", index = texIndex, success = true });
                            }
                        }
                        catch (Exception ex)
                        {
                            LogError("Error in updateTexture", ex);
                            await SendJsonAsync(webSocket, new { type = "textureUpdated", success = false, error = ex.Message });
                        }
                        break;

                    case "exportDat":
                        // Export the modified DAT file with updated textures
                        try
                        {
                            Log("Received exportDat command");

                            if (_rawFile == null)
                            {
                                await SendJsonAsync(webSocket, new { type = "exportDat", success = false, error = "No DAT file loaded" });
                                break;
                            }

                            string tempPath = Path.Combine(Path.GetTempPath(), $"export_{Guid.NewGuid()}.dat");

                            // Run on background thread - no UI thread needed for file I/O
                            byte[] datBytes = await Task.Run(() =>
                            {
                                _rawFile.Save(tempPath);
                                var data = File.ReadAllBytes(tempPath);
                                File.Delete(tempPath);
                                return data;
                            });

                            string base64Data = Convert.ToBase64String(datBytes);
                            await SendJsonAsync(webSocket, new { type = "exportDat", success = true, data = base64Data });
                            Log($"DAT exported successfully, size: {datBytes.Length} bytes");
                        }
                        catch (Exception ex)
                        {
                            LogError("Error in exportDat", ex);
                            await SendJsonAsync(webSocket, new { type = "exportDat", success = false, error = ex.Message });
                        }
                        break;

                    case "loadAnim":
                        // Load a specific animation by symbol name
                        if (_ajManager != null && root.TryGetProperty("symbol", out var symbolProp))
                        {
                            var symbol = symbolProp.GetString();
                            var animData = _ajManager.GetAnimationData(symbol);
                            if (animData != null)
                            {
                                try
                                {
                                    var animFile = new HSDRawFile(animData);
                                    if (animFile.Roots.Count > 0 && animFile.Roots[0].Data is HSD_FigaTree tree)
                                    {
                                        var jointAnim = new JointAnimManager(tree);
                                        float newFrameCount = jointAnim.FrameCount;

                                        // Must run on UI thread for thread safety
                                        _hostForm.Invoke((Action)(() =>
                                        {
                                            _renderJObj.ClearAnimation(FrameFlags.Joint);
                                            _renderJObj.LoadAnimation(jointAnim, null, null);
                                            _animationFrameCount = newFrameCount;
                                            _animationFrame = 0;
                                            _animationPlaying = true;
                                            _renderJObj.RequestAnimationUpdate(FrameFlags.All, 0);
                                            // arm/clear per-animation model-part visibility for this symbol
                                            _partVis?.OnAnimationLoaded(symbol);
                                        }));

                                        Console.Error.WriteLine($"[ANIM] Loaded: {symbol}, {newFrameCount} frames");

                                        await SendJsonAsync(webSocket, new
                                        {
                                            type = "animLoaded",
                                            symbol,
                                            frameCount = newFrameCount
                                        });
                                    }
                                }
                                catch (Exception ex)
                                {
                                    Console.Error.WriteLine($"[ANIM ERR] {symbol}: {ex.Message}");
                                }
                            }
                            else
                            {
                                Log($"Animation not found: {symbol}");
                            }
                        }
                        break;

                    default:
                        Log($"Unknown command type: {type}");
                        break;
                }
            }
            catch (Exception ex)
            {
                LogError("Command parse error", ex);
            }
        }

        private async Task SendJsonAsync(WebSocket webSocket, object data)
        {
            await _sendLock.WaitAsync();
            try
            {
                if (webSocket.State == WebSocketState.Open)
                {
                    var json = JsonSerializer.Serialize(data);
                    var bytes = Encoding.UTF8.GetBytes(json);
                    await webSocket.SendAsync(
                        new ArraySegment<byte>(bytes),
                        WebSocketMessageType.Text,
                        true,
                        _cts.Token
                    );
                }
            }
            finally
            {
                _sendLock.Release();
            }
        }

        private async Task SendBinaryAsync(WebSocket webSocket, byte[] data)
        {
            await _sendLock.WaitAsync();
            try
            {
                if (webSocket.State == WebSocketState.Open)
                {
                    await webSocket.SendAsync(
                        new ArraySegment<byte>(data),
                        WebSocketMessageType.Binary,
                        true,
                        _cts.Token
                    );
                }
            }
            finally
            {
                _sendLock.Release();
            }
        }

        public void Stop()
        {
            Log("Stopping streaming server...");
            _isRunning = false;
            _cts.Cancel();

            _currentClient?.CloseAsync(WebSocketCloseStatus.NormalClosure, "Server shutdown", CancellationToken.None).Wait(1000);
            _httpListener?.Stop();
            _hostForm?.Close();
            Log("Streaming server stopped");
        }

        public void Dispose()
        {
            Stop();
            _cts?.Dispose();
            _httpListener?.Close();
            _hostForm?.Dispose();
            _viewport?.Dispose();

            Log("=== HSDRawViewer Streaming Server Disposed ===");
            _logWriter?.Dispose();
        }
    }
}
