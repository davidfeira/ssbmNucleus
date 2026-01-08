using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Pipes;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using HSDRaw;
using HSDRaw.Common;
using HSDRaw.Common.Animation;
using HSDRaw.Tools.Melee;
using HSDRawViewer.GUI;
using HSDRawViewer.Rendering;
using HSDRawViewer.Rendering.Models;
using HSDRawViewer.Converters.Animation;
using HSDRawViewer.Tools;
using HSDRawViewer.GUI.Controls.JObjEditor;

namespace HSDRawViewer
{
    /// <summary>
    /// Embedded server for 3D model viewing in Electron app.
    /// Uses Named Pipes for IPC and creates a borderless window for embedding via SetParent.
    /// </summary>
    public class EmbeddedServer : IDisposable
    {
        // Win32 API imports for window embedding
        [DllImport("user32.dll", SetLastError = true)]
        private static extern IntPtr SetParent(IntPtr hWndChild, IntPtr hWndNewParent);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern int SetWindowLong(IntPtr hWnd, int nIndex, int dwNewLong);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern int GetWindowLong(IntPtr hWnd, int nIndex);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

        private const int GWL_STYLE = -16;
        private const int GWL_EXSTYLE = -20;
        private const int GWLP_HWNDPARENT = -8;
        private const int WS_CHILD = 0x40000000;
        private const int WS_POPUP = unchecked((int)0x80000000);
        private const int WS_EX_TOOLWINDOW = 0x00000080;

        private static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
        private static readonly IntPtr HWND_NOTOPMOST = new IntPtr(-2);
        private static readonly IntPtr HWND_TOP = IntPtr.Zero;

        private IntPtr _parentHwnd = IntPtr.Zero;
        private const uint SWP_NOMOVE = 0x0002;
        private const uint SWP_NOSIZE = 0x0001;
        private const uint SWP_SHOWWINDOW = 0x0040;

        private ViewportControl _viewport;
        private RenderJObj _renderJObj;
        private Form _hostForm;
        private CancellationTokenSource _cts;
        private string _pipeName;
        private bool _isRunning = false;
        private StreamWriter _logWriter;
        private string _logPath;

        // Animation state
        private bool _animationPlaying = false;
        private float _animationFrame = 0;
        private float _animationFrameCount = 0;
        private float _animationSpeed = 1.0f;

        // Animation archive manager
        private FighterAJManager _ajManager;

        // Cached texture list
        private List<TextureInfo> _cachedTextureList = null;

        // DAT file reference for export
        private HSDRawFile _rawFile = null;
        private string _datFilePath = null;

        // Named pipe streams
        private NamedPipeServerStream _pipeServer;
        private StreamReader _pipeReader;
        private StreamWriter _pipeWriter;

        public EmbeddedServer(string pipeName, string logPath = null)
        {
            _pipeName = pipeName;
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
                    var exeDir = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
                    _logPath = Path.Combine(exeDir, "..", "..", "..", "..", "..", "..", "..", "logs");
                }

                Directory.CreateDirectory(_logPath);
                var logFile = Path.Combine(_logPath, $"embedded_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}.log");
                _logWriter = new StreamWriter(logFile, append: true) { AutoFlush = true };
                Log($"=== HSDRawViewer Embedded Server Started ===");
                Log($"Pipe name: {_pipeName}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to initialize logging: {ex.Message}");
            }
        }

        private void Log(string message)
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
            var logLine = $"[{timestamp}] {message}";
            try
            {
                _logWriter?.WriteLine(logLine);
            }
            catch { }
        }

        private void LogError(string message, Exception ex = null)
        {
            var timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
            var logLine = $"[{timestamp}] ERROR: {message}";
            if (ex != null)
            {
                logLine += $"\n  Exception: {ex.GetType().Name}: {ex.Message}\n  Stack: {ex.StackTrace}";
            }
            try
            {
                _logWriter?.WriteLine(logLine);
            }
            catch { }
        }

        public async Task StartAsync(string datFilePath, string sceneFilePath = null, string ajFilePath = null)
        {
            Log($"Starting embedded server with pipe: {_pipeName}");
            Log($"Loading DAT file: {datFilePath}");

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

            // Initialize MainForm for proper model loading
            Log("Initializing MainForm...");
            MainForm.Init();
            MainForm.Instance.OpenFile(datFilePath);
            Thread.Sleep(500);

            // Load the DAT file
            Log("Opening DAT file...");
            _rawFile = new HSDRawFile();
            _rawFile.Open(datFilePath);
            _datFilePath = datFilePath;

            // Find character JOBJ
            DataNode characterJobjNode = null;
            foreach (var root in _rawFile.Roots)
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
                foreach (var root in _rawFile.Roots)
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

            // Select and open editor
            MainForm.SelectedDataNode = characterJobjNode;
            MainForm.Instance.OpenEditor();
            Thread.Sleep(1000);

            // Create viewport
            Log("Creating ViewportControl...");
            _viewport = new ViewportControl();

            if (characterJobjNode.Accessor is HSD_JOBJ jobj)
            {
                Log("Creating RenderJObj...");
                _renderJObj = new RenderJObj(jobj);
                _renderJObj._settings.RenderBones = false;
                _renderJObj._settings.RenderObjects = ObjectRenderMode.Visible;

                var drawable = new SimpleJObjDrawable(_renderJObj);
                _viewport.AddRenderer(drawable);
                Log($"RenderJObj created. DOBJs: {_renderJObj.DObjCount}");
            }

            // Create borderless embeddable form
            Log("Creating borderless host form...");
            _hostForm = new Form();
            _hostForm.FormBorderStyle = FormBorderStyle.None;
            _hostForm.StartPosition = FormStartPosition.Manual;
            _hostForm.Location = new System.Drawing.Point(0, 0);
            _hostForm.Size = new System.Drawing.Size(800, 600);
            _hostForm.Text = "HSD Viewer (Embedded)";
            _hostForm.ShowInTaskbar = false;

            _viewport.Dock = DockStyle.Fill;
            _hostForm.Controls.Add(_viewport);
            _hostForm.Show();

            // Initialize OpenGL
            Log("Waiting for OpenGL initialization...");
            for (int i = 0; i < 100; i++)
            {
                Application.DoEvents();
                Thread.Sleep(10);
            }

            // Set up viewport
            _viewport.EnableBack = true;
            _viewport.DisplayGrid = true;

            // Load scene settings if provided
            SceneSettings sceneSettings = null;
            if (!string.IsNullOrEmpty(sceneFilePath) && File.Exists(sceneFilePath))
            {
                try
                {
                    Log($"Loading scene settings from: {sceneFilePath}");
                    sceneSettings = SceneSettings.Deserialize(sceneFilePath);

                    if (sceneSettings.Camera != null)
                    {
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

                    if (sceneSettings.Animation != null && _renderJObj != null)
                    {
                        _renderJObj.LoadAnimation(sceneSettings.Animation, null, null);
                        _animationFrameCount = sceneSettings.Animation.FrameCount;
                        _animationFrame = Math.Max(0, sceneSettings.Frame);
                        _renderJObj.RequestAnimationUpdate(FrameFlags.All, _animationFrame);
                    }

                    // Grid and background always on for skin creator
                    // _viewport.DisplayGrid = sceneSettings.ShowGrid;
                    // _viewport.EnableBack = sceneSettings.ShowBackdrop;
                }
                catch (Exception ex)
                {
                    LogError("Failed to load scene settings", ex);
                }
            }

            // Initial render
            Log("Performing initial render...");
            Application.DoEvents();
            _viewport.Render();
            Application.DoEvents();

            // Apply hidden nodes after render
            if (_renderJObj != null)
            {
                if (sceneSettings?.HiddenNodes != null && sceneSettings.HiddenNodes.Length > 0)
                {
                    foreach (int dobjIndex in sceneSettings.HiddenNodes)
                    {
                        if (dobjIndex >= 0 && dobjIndex < _renderJObj.DObjCount)
                            _renderJObj.SetDObjVisible(dobjIndex, false);
                    }
                    Application.DoEvents();
                    _viewport.Render();
                    Application.DoEvents();
                }

                _cachedTextureList = _renderJObj.GetTextureList();
                Log($"Cached {_cachedTextureList.Count} textures");
            }

            // Load animation archive if provided
            if (!string.IsNullOrEmpty(ajFilePath) && File.Exists(ajFilePath))
            {
                try
                {
                    Log($"Loading AJ file: {ajFilePath}");
                    _ajManager = new FighterAJManager(File.ReadAllBytes(ajFilePath));
                    Log($"Loaded {_ajManager.GetAnimationSymbols().Count()} animations");
                }
                catch (Exception ex)
                {
                    LogError("Failed to load AJ file", ex);
                }
            }

            // Start named pipe server
            Log($"Starting named pipe server: {_pipeName}");
            _pipeServer = new NamedPipeServerStream(
                _pipeName,
                PipeDirection.InOut,
                1,
                PipeTransmissionMode.Byte,
                PipeOptions.Asynchronous
            );

            _isRunning = true;
            Log("Waiting for pipe connection...");

            // Wait for connection in background
            _ = Task.Run(async () =>
            {
                try
                {
                    await _pipeServer.WaitForConnectionAsync(_cts.Token);
                    Log("Pipe client connected!");

                    // Use UTF8 without BOM - BOM breaks JSON parsing in Node.js
                    var utf8NoBom = new UTF8Encoding(false);
                    _pipeReader = new StreamReader(_pipeServer, utf8NoBom);
                    _pipeWriter = new StreamWriter(_pipeServer, utf8NoBom) { AutoFlush = true };

                    // Send ready message with HWND
                    var hwnd = _hostForm.Handle.ToInt64();
                    Log($"Sending ready message with HWND: {hwnd}");
                    await SendJsonAsync(new
                    {
                        type = "ready",
                        hwnd = hwnd,
                        dobjCount = _renderJObj?.DObjCount ?? 0,
                        animationFrameCount = _animationFrameCount
                    });

                    // Start receiving messages
                    await ReceiveMessagesAsync();
                }
                catch (Exception ex)
                {
                    LogError("Pipe error", ex);
                }
            });

            // Run animation/render loop on main thread
            Log("Starting render loop...");
            var frameInterval = TimeSpan.FromMilliseconds(1000.0 / 60.0);
            var lastFrameTime = DateTime.UtcNow;

            while (_isRunning && !_cts.Token.IsCancellationRequested)
            {
                var now = DateTime.UtcNow;
                var elapsed = now - lastFrameTime;

                if (elapsed >= frameInterval)
                {
                    lastFrameTime = now;

                    // Update animation if playing
                    if (_animationPlaying && _animationFrameCount > 0 && _renderJObj != null)
                    {
                        _animationFrame += _animationSpeed;
                        if (_animationFrame >= _animationFrameCount)
                            _animationFrame = 0;
                        else if (_animationFrame < 0)
                            _animationFrame = _animationFrameCount - 1;

                        _renderJObj.RequestAnimationUpdate(FrameFlags.All, _animationFrame);
                    }

                    // Render (OpenGL handles display directly - no frame encoding)
                    _viewport.Render();
                }

                Application.DoEvents();
                Thread.Sleep(1);
            }
        }

        private async Task ReceiveMessagesAsync()
        {
            try
            {
                while (_isRunning && _pipeServer.IsConnected && !_cts.Token.IsCancellationRequested)
                {
                    var line = await _pipeReader.ReadLineAsync();
                    if (line == null) break;

                    await ProcessCommandAsync(line);
                }
            }
            catch (Exception ex)
            {
                LogError("Receive error", ex);
            }
            finally
            {
                Log("Pipe disconnected");
            }
        }

        private async Task ProcessCommandAsync(string json)
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
                        if (root.TryGetProperty("deltaRotX", out var deltaRotX))
                            _viewport.Camera.RotationXRadians += (float)(deltaRotX.GetDouble() * Math.PI / 180.0);
                        if (root.TryGetProperty("deltaRotY", out var deltaRotY))
                            _viewport.Camera.RotationYRadians += (float)(deltaRotY.GetDouble() * Math.PI / 180.0);
                        if (root.TryGetProperty("deltaZoom", out var deltaZoom))
                        {
                            _viewport.Camera.Scale *= (float)(1.0 + deltaZoom.GetDouble());
                            _viewport.Camera.Scale = Math.Max(0.1f, Math.Min(1000f, _viewport.Camera.Scale));
                        }
                        if (root.TryGetProperty("deltaX", out var deltaX))
                            _viewport.Camera.X += (float)deltaX.GetDouble();
                        if (root.TryGetProperty("deltaY", out var deltaY))
                            _viewport.Camera.Y += (float)deltaY.GetDouble();
                        break;

                    case "resize":
                        // Update window position and size
                        int x = 0, y = 0, width = 800, height = 600;
                        if (root.TryGetProperty("x", out var xProp)) x = xProp.GetInt32();
                        if (root.TryGetProperty("y", out var yProp)) y = yProp.GetInt32();
                        if (root.TryGetProperty("width", out var wProp)) width = wProp.GetInt32();
                        if (root.TryGetProperty("height", out var hProp)) height = hProp.GetInt32();

                        _hostForm.Invoke((Action)(() =>
                        {
                            _hostForm.Location = new System.Drawing.Point(x, y);
                            _hostForm.ClientSize = new System.Drawing.Size(width, height);
                            _hostForm.PerformLayout();
                            _viewport.RefreshSize();
                            _viewport.Invalidate();
                            // Keep window on top - use TOPMOST since owned windows don't stay on top reliably
                            SetWindowPos(_hostForm.Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW);
                        }));
                        Log($"Resized to {x},{y} {width}x{height}");
                        break;

                    case "setParent":
                        // Make this window owned by (not child of) the Electron window
                        // This keeps it on top of Electron while avoiding Chromium compositor issues
                        if (root.TryGetProperty("hwnd", out var parentHwndProp))
                        {
                            _parentHwnd = new IntPtr(long.Parse(parentHwndProp.GetString()));
                            _hostForm.Invoke((Action)(() =>
                            {
                                var hwnd = _hostForm.Handle;
                                // Set owner (not parent) - window stays on top of owner
                                SetWindowLong(hwnd, GWLP_HWNDPARENT, (int)_parentHwnd);
                                // Make it a tool window so it doesn't show in taskbar
                                int exStyle = GetWindowLong(hwnd, GWL_EXSTYLE);
                                SetWindowLong(hwnd, GWL_EXSTYLE, exStyle | WS_EX_TOOLWINDOW);
                                // Bring to front
                                SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW);
                                _hostForm.Show();
                                Log($"Set owner to HWND: {_parentHwnd}");
                            }));
                        }
                        break;

                    case "show":
                        _hostForm.Invoke((Action)(() =>
                        {
                            _hostForm.Show();
                            SetWindowPos(_hostForm.Handle, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW);
                            _hostForm.Invalidate();
                        }));
                        break;

                    case "hide":
                        _hostForm.Invoke((Action)(() => _hostForm.Hide()));
                        break;

                    case "animPlay":
                        _animationPlaying = true;
                        break;

                    case "animPause":
                        _animationPlaying = false;
                        break;

                    case "animToggle":
                        _animationPlaying = !_animationPlaying;
                        break;

                    case "animSetFrame":
                        if (root.TryGetProperty("frame", out var frameVal))
                        {
                            _animationFrame = (float)frameVal.GetDouble();
                            _animationFrame = Math.Clamp(_animationFrame, 0, Math.Max(0, _animationFrameCount - 1));
                            if (_renderJObj != null)
                                _renderJObj.RequestAnimationUpdate(FrameFlags.All, _animationFrame);
                        }
                        break;

                    case "animSetSpeed":
                        if (root.TryGetProperty("speed", out var speedVal))
                            _animationSpeed = (float)speedVal.GetDouble();
                        break;

                    case "getAnimList":
                        if (_ajManager != null)
                        {
                            var symbols = _ajManager.GetAnimationSymbols().ToArray();
                            await SendJsonAsync(new { type = "animList", symbols });
                        }
                        else
                        {
                            await SendJsonAsync(new { type = "animList", symbols = Array.Empty<string>() });
                        }
                        break;

                    case "loadAnim":
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

                                        _hostForm.Invoke((Action)(() =>
                                        {
                                            _renderJObj.ClearAnimation(FrameFlags.Joint);
                                            _renderJObj.LoadAnimation(jointAnim, null, null);
                                            _animationFrameCount = newFrameCount;
                                            _animationFrame = 0;
                                            _animationPlaying = true;
                                            _renderJObj.RequestAnimationUpdate(FrameFlags.All, 0);
                                        }));

                                        await SendJsonAsync(new
                                        {
                                            type = "animLoaded",
                                            symbol,
                                            frameCount = newFrameCount
                                        });
                                    }
                                }
                                catch (Exception ex)
                                {
                                    LogError($"Failed to load animation: {symbol}", ex);
                                }
                            }
                        }
                        break;

                    case "getTextures":
                        if (_cachedTextureList != null)
                        {
                            var textureList = _cachedTextureList.Select(t => new
                            {
                                index = t.Index,
                                width = t.Width,
                                height = t.Height,
                                name = t.Name,
                                thumbnail = t.ThumbnailBase64
                            }).ToList();
                            await SendJsonAsync(new { type = "textureList", textures = textureList });
                        }
                        else
                        {
                            await SendJsonAsync(new { type = "textureList", textures = Array.Empty<object>() });
                        }
                        break;

                    case "updateTexture":
                        if (root.TryGetProperty("index", out var indexProp) &&
                            root.TryGetProperty("data", out var dataProp))
                        {
                            int texIndex = indexProp.GetInt32();
                            string base64Data = dataProp.GetString();
                            byte[] pngData = Convert.FromBase64String(base64Data);

                            _hostForm.BeginInvoke((Action)(() =>
                            {
                                try
                                {
                                    _renderJObj.UpdateTexture(texIndex, pngData);
                                }
                                catch (Exception ex)
                                {
                                    LogError($"Error updating texture {texIndex}", ex);
                                }
                            }));

                            await SendJsonAsync(new { type = "textureUpdated", index = texIndex, success = true });
                        }
                        break;

                    case "exportDat":
                        try
                        {
                            if (_rawFile == null)
                            {
                                await SendJsonAsync(new { type = "exportDat", success = false, error = "No DAT file loaded" });
                                break;
                            }

                            string tempPath = Path.Combine(Path.GetTempPath(), $"export_{Guid.NewGuid()}.dat");
                            byte[] datBytes = await Task.Run(() =>
                            {
                                _rawFile.Save(tempPath);
                                var data = File.ReadAllBytes(tempPath);
                                File.Delete(tempPath);
                                return data;
                            });

                            string base64 = Convert.ToBase64String(datBytes);
                            await SendJsonAsync(new { type = "exportDat", success = true, data = base64 });
                            Log($"DAT exported: {datBytes.Length} bytes");
                        }
                        catch (Exception ex)
                        {
                            LogError("Export error", ex);
                            await SendJsonAsync(new { type = "exportDat", success = false, error = ex.Message });
                        }
                        break;

                    case "ping":
                        await SendJsonAsync(new { type = "pong" });
                        break;

                    case "close":
                        Log("Received close command");
                        _isRunning = false;
                        break;

                    default:
                        Log($"Unknown command: {type}");
                        break;
                }
            }
            catch (Exception ex)
            {
                LogError("Command error", ex);
            }
        }

        private async Task SendJsonAsync(object data)
        {
            try
            {
                if (_pipeWriter != null && _pipeServer.IsConnected)
                {
                    var json = JsonSerializer.Serialize(data);
                    await _pipeWriter.WriteLineAsync(json);
                }
            }
            catch (Exception ex)
            {
                LogError("Send error", ex);
            }
        }

        public void Stop()
        {
            Log("Stopping embedded server...");
            _isRunning = false;
            _cts.Cancel();
            _hostForm?.Close();
            Log("Embedded server stopped");
        }

        public void Dispose()
        {
            Stop();
            _cts?.Dispose();
            _pipeReader?.Dispose();
            _pipeWriter?.Dispose();
            _pipeServer?.Dispose();
            _hostForm?.Dispose();
            _viewport?.Dispose();

            Log("=== HSDRawViewer Embedded Server Disposed ===");
            _logWriter?.Dispose();
        }
    }
}
