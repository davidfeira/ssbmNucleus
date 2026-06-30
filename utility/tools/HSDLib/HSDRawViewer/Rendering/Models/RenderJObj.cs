using HSDRaw.Common;
using HSDRaw.Common.Animation;
using HSDRaw.GX;
using HSDRaw.Tools;
using HSDRawViewer.Extensions;
using HSDRawViewer.Rendering.GX;
using HSDRawViewer.Rendering.Shaders;
using OpenTK.Graphics.OpenGL;
using OpenTK.Mathematics;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using SixLabors.ImageSharp.Processing;

namespace HSDRawViewer.Rendering.Models
{
    [Flags]
    public enum FrameFlags
    {
        None = 0,
        Joint = 1,
        Material = 2,
        Shape = 4,
        All = Joint | Material | Shape,
    }

    public class TextureInfo
    {
        public int Index { get; set; }
        public int Width { get; set; }
        public int Height { get; set; }
        public string Name { get; set; }
        public byte[] RgbaData { get; set; }
        public string ThumbnailBase64 { get; set; }
        public int GlTextureId { get; set; }
        public HSDRaw.Common.HSD_TOBJ Tobj { get; set; } // Reference for updating HSD data
        public bool IsMatAnim { get; set; }     // a MatAnim swap frame (blink etc.), not a material texture
        public int AnimatesIndex { get; set; } = -1;  // texture index this swap frame animates, or -1
        public bool IsExtraRoot { get; set; }   // from a non-rendered extra JOBJ root (e.g. Jigglypuff hats)
    }

    public class RenderJObj
    {
        private static int MAX_TEX { get; } = 4;
        private static int MAX_LIGHTS { get; } = 4;

        private GXShader _shader;

        public LiveJObj RootJObj { get; internal set; }

        private bool Initialized = false;

        public RenderMode RenderMode { get; set; }

        private RenderLObj[] _lights { get; } = new RenderLObj[MAX_LIGHTS];
        private RenderLObj[] _cameraLights { get; } = new RenderLObj[]
        {
            new()
            {
                Enabled = true,
                Type = LObjType.AMBIENT,
                _color = new Vector4(179, 179, 179, 255) / 255f,
            },
            new()
            {
                Enabled = true,
                Type = LObjType.INFINITE,

            },
        };

        public GXFogParam _fogParam { get; internal set; } = new GXFogParam();

        public JobjDisplaySettings _settings { get; internal set; } = new JobjDisplaySettings();

        public float ModelScale { get; set; } = 1;

        public Vector3 OverlayColor { get; set; } = Vector3.One;


        // Keyed on (image data, TLUT data). Palettized textures frequently SHARE
        // one image-data blob -- e.g. an exporter dedupes identical all-zero "color
        // swatch" pixels -- while each carries a DIFFERENT TLUT holding its real
        // color. Keying on image data alone collapsed them to a single decode, so
        // every part drew the first palette's color (Vader's per-part swatches all
        // rendered dark -> a black silhouette). The TLUT must be part of the key.
        private readonly Dictionary<(byte[] img, byte[] tlut), int> imageBufferTextureIndex = new();

        private static (byte[], byte[]) TexCacheKey(HSD_TOBJ t)
            => (t?.ImageData?.ImageData, t?.TlutData?.TlutData);

        /// <summary>
        /// collection of renderable dobjs
        /// </summary>
        private List<RenderDObj> RenderDobjs = new();

        /// <summary>
        /// MatAnim texture-swap banks (blink frames etc.) from the DAT's
        /// matanim_joint roots. Each entry pairs a TexAnim with synthetic
        /// TOBJs wrapping its image/palette buffers IN PLACE -- injecting
        /// into these TOBJs mutates the raw file's buffers directly, so
        /// edits survive export. Set by hosts via SetMatAnims().
        /// </summary>
        private readonly List<(HSD_TexAnim anim, HSD_TOBJ[] frames)> _matAnimBanks = new();

        /// <summary>
        /// Extra JOBJ roots that are NOT part of the rendered model -- e.g.
        /// Jigglypuff's alt-costume hats live in a second *Hat_TopN_joint
        /// root. Their material textures must still appear in the texture
        /// list and be reachable by updates. Set by hosts via SetExtraRoots().
        /// </summary>
        private readonly List<HSD_JOBJ> _extraRoots = new();

        /// <summary>
        /// For managing opengl buffers
        /// </summary>
        private readonly VertexBufferManager BufferManager = new();

        /// <summary>
        /// For managing opengl textures
        /// </summary>
        private readonly TextureManager TextureManager = new();

        /// <summary>
        /// 
        /// </summary>
        public HSD_JOBJ SelectedJObj;

        /// <summary>
        /// 
        /// </summary>
        public JointAnimManager JointAnim { get; internal set; }

        /// <summary>
        /// 
        /// </summary>

        public MatAnimManager MatAnim { get; internal set; }

        private bool UpdateMaterialFrame = false;

        /// <summary>
        /// 
        /// </summary>
        public HSD_ShapeAnimJoint ShapeAnim { get; internal set; }


        public delegate void OnIntialize();
        public OnIntialize Initialize;


        /// <summary>
        /// 
        /// </summary>
        public RenderJObj()
        {
            for (int i = 0; i < MAX_LIGHTS; i++)
                _lights[i] = new RenderLObj();

            _lights[0].Enabled = true;
            _lights[0].Type = LObjType.AMBIENT;
            _lights[0]._color = new Vector4(255, 255, 255, 255) / 255f;

            _lights[1].Enabled = true;
            _lights[1].Type = LObjType.INFINITE;
            _lights[1]._position = new Vector3(0, 12, 9);
            _lights[1]._color = new Vector4(200, 200, 200, 255) / 255f;
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="desc"></param>
        public RenderJObj(HSD_JOBJ desc) : base()
        {
            LoadJObj(desc);
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="index"></param>
        /// <param name="state"></param>
        public void SetMaterialAnimation(int dobj_index, float frame, List<FOBJ_Player> tracks, IEnumerable<List<FOBJ_Player>> textureStates, List<List<HSD_TOBJ>> textures)
        {
            if (dobj_index >= 0 && dobj_index < RenderDobjs.Count)
            {
                RenderDobjs[dobj_index].MaterialState.ApplyAnim(tracks, frame);

                int ti = 0;
                foreach (List<FOBJ_Player> t in textureStates)
                {
                    if (ti >= RenderDobjs[dobj_index].TextureStates.Length)
                        break;

                    RenderDobjs[dobj_index].TextureStates[ti].ApplyAnim(textures[ti], t, frame);
                    ti++;
                }
            }
        }

        /// <summary>
        /// 
        /// </summary>
        public void RequestAnimationUpdate(FrameFlags flags, float frame)
        {
            if (flags.HasFlag(FrameFlags.Joint) && RootJObj != null && JointAnim != null)
            {
                JointAnim.ApplyAnimation(RootJObj, frame);
            }

            if (flags.HasFlag(FrameFlags.Material) && MatAnim != null)
            {
                // if frame is -1 don't actually update the frame values
                if (frame != -1)
                    MatAnim.SetAllFrames(frame);
                UpdateMaterialFrame = true;
            }

            // TODO: shape animation
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name=""></param>
        public void ClearAnimation(FrameFlags flags)
        {
            if (flags.HasFlag(FrameFlags.Joint))
            {
                JointAnim = null;
                ResetDefaultStateJoints();
            }

            if (flags.HasFlag(FrameFlags.Material))
            {
                MatAnim = null;
                ResetDefaultStateMaterial();
            }

            // TODO: shape animation
        }

        /// <summary>
        /// 
        /// </summary>
        public void LoadAnimation(JointAnimManager joint, HSD_MatAnimJoint material, HSD_ShapeAnimJoint shape)
        {
            FrameFlags flags = FrameFlags.None;

            if (joint != null)
            {
                flags |= FrameFlags.Joint;
                JointAnim = joint;
            }

            if (material != null)
            {
                flags |= FrameFlags.Material;
                MatAnim = new MatAnimManager(material);
            }

            if (shape != null)
            {
                ShapeAnim = shape;
                flags |= FrameFlags.Shape;
            }

            // request anim update
            RequestAnimationUpdate(flags, 0);
        }

        /// <summary>
        /// 
        /// </summary>
        public void ResetDefaultStateAll()
        {
            ResetDefaultStateJoints();
            ResetDefaultStateMaterial();
        }

        /// <summary>
        /// 
        /// </summary>
        public void ResetDefaultStateJoints()
        {
            // reset skeleton
            RootJObj?.ResetTransforms();
        }


        /// <summary>
        /// 
        /// </summary>
        public void ResetDefaultStateMaterial()
        {
            // reset materials
            foreach (RenderDObj d in RenderDobjs)
                d.ResetMaterialState();
        }

        /// <summary>
        /// 
        /// </summary>
        public void LoadJObj(HSD_JOBJ desc)
        {
            ClearAnimation(FrameFlags.Material | FrameFlags.Shape);
            RootJObj = new LiveJObj(desc);
            Initialized = false;
        }

        /// <summary>
        /// This will free all opengl resources used for rendering
        /// </summary>
        public void FreeResources()
        {
            // initialize shader
            if (_shader != null)
            {
                _shader.Dispose();
                _shader = null;
            }

            // clear previous caches
            BufferManager.ClearRenderingCache();
            TextureManager.ClearTextures();
            imageBufferTextureIndex.Clear();
            RenderDobjs.Clear();
        }

        /// <summary>
        /// 
        /// </summary>
        public void InvalidateDObjOrder()
        {
            // determine new order
            Dictionary<HSD_DOBJ, int> newOrder = new(RenderDobjs.Count);
            int i = 0;
            foreach (LiveJObj j in RootJObj?.Enumerate)
            {
                if (j.Desc.Dobj == null)
                    continue;
                foreach (HSD_DOBJ d in j.Desc.Dobj.List)
                    newOrder.Add(d, i++);
            }

            // order render dobjs
            RenderDobjs = RenderDobjs.OrderBy(e => newOrder[e._dobj]).ToList();

            // update display index
            foreach (RenderDObj d in RenderDobjs)
                d.DisplayIndex = d.Parent.Desc.Dobj.List.IndexOf(d._dobj);
        }

        /// <summary>
        /// 
        /// </summary>
        private void InitializeRendering()
        {
            Initialized = true;

            // free old resources
            FreeResources();

            // initialize shader
            _shader = new GXShader();

            // initial dobj cache
            foreach (LiveJObj j in RootJObj?.Enumerate)
            {
                if (j.Desc.Dobj == null)
                    continue;

                // initialize all dobjs
                foreach (HSD_DOBJ d in j.Desc.Dobj.List)
                {
                    RenderDObj dob = new(j, d);
                    dob.InitializeBufferData(BufferManager);
                    RenderDobjs.Add(dob);

                    // preload textures
                    if (d.Mobj != null && d.Mobj.Textures != null)
                    {
                        foreach (HSD_TOBJ t in d.Mobj.Textures.List)
                        {
                            PreLoadTexture(t);
                        }
                    }
                }
            }

            // re apply animation after invalidating
            RequestAnimationUpdate(FrameFlags.All, 0);

            // print diagnostic info
            System.Diagnostics.Debug.WriteLine($"Buffer Count: {BufferManager.BufferCount}");
            System.Diagnostics.Debug.WriteLine($"Texture Count: {TextureManager.TextureCount}");

            // callback done initializing
            Initialize?.Invoke();
        }

        /// <summary>
        /// Signals jobj to reload data during next render update
        /// This operation is very slow!
        /// </summary>
        public void Invalidate()
        {
            Initialized = false;
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="cam"></param>
        /// <param name="update"></param>
        public void Render(Camera camera, bool update = true)
        {
            // nothing to render if jobj is nul
            if (RootJObj == null)
                return;

            // initial rendering if not already
            if (!Initialized)
                InitializeRendering();

            //push attrib for cleanup
            GL.PushAttrib(AttribMask.AllAttribBits);

            // recalculate transforms
            if (update)
            {
                Vector3 temp = RootJObj.Scale;
                RootJObj.Scale *= ModelScale;
                RootJObj.RecalculateTransforms(camera, true);
                RootJObj.Scale = temp;
            }

            // apply material animation update during render only
            DrawUpdateMaterialAnimation();

            // enable depth test
            GL.Enable(EnableCap.DepthTest);
            GL.DepthFunc(DepthFunction.Lequal);

            // prepare shader
            SetupShader();

            // render with shader
            _shader.Bind(camera, _fogParam);

            // lighting
            _shader.SetFloat("saturate", 1);
            _shader.SetBoolToInt("perPixelLighting", true);
            switch (_settings.LightSource)
            {
                case LightRenderMode.Camera:
                    {
                        _cameraLights[1]._position = camera.TransformedPosition;
                        for (int i = 0; i < MAX_LIGHTS; i++)
                        {
                            if (i < _cameraLights.Length)
                                _cameraLights[i].Bind(_shader, i);
                            else
                                _shader.SetBoolToInt($"light[{i}].enabled", false);
                        }
                    }
                    break;
                case LightRenderMode.Default:
                    {
                        for (int i = 0; i < MAX_LIGHTS; i++)
                            _lights[i].Bind(_shader, i);
                    }
                    break;
                case LightRenderMode.Custom:
                    {
                        for (int i = 0; i < MAX_LIGHTS; i++)
                        {
                            if (i < _settings._lights.Length)
                                _settings._lights[i].Bind(_shader, i);
                            else
                                _shader.SetBoolToInt($"light[{i}].enabled", false);
                        }
                    }
                    break;
            }

            // Render DOBJS
            RenderJObjDisplay(camera);

            // unbind shader
            _shader.Unbind();

            // pop attribute for cleanup
            GL.PopAttrib();

            // render splines
            if (_settings.RenderSplines)
                DrawSplines(camera);

            // draw lights
            if (_settings.RenderCustomLightPositions && _settings.LightSource == LightRenderMode.Custom)
            {
                foreach (RenderLObj l in _settings._lights)
                {
                    if (l.Enabled && l.Type != LObjType.AMBIENT)
                        DrawShape.DrawSphere(Matrix4.CreateTranslation(l._position), 1, 10, 10, l._color.Xyz, 1);
                }
            }

            // bone overlay
            RenderBoneOverlay();
        }

        /// <summary>
        /// 
        /// </summary>
        private void DrawUpdateMaterialAnimation()
        {
            if (UpdateMaterialFrame)
            {
                // apply animation to all render dobjs
                foreach (RenderDObj v in RenderDobjs)
                {
                    // get material state
                    LiveMaterial state = v.MaterialState;
                    MatAnim.GetMaterialState(v._dobj.Mobj, v.JointIndex, v.DisplayIndex, ref state);
                    v.MaterialState = state;

                    // get texture states
                    if (v._dobj.Mobj.Textures != null)
                    {
                        int ti = 0;
                        foreach (HSD_TOBJ i in v._dobj.Mobj.Textures.List)
                        {
                            if (ti < v.TextureStates.Length)
                            {
                                LiveTObj ts = v.TextureStates[ti];

                                MatAnim.GetTextureAnimState(i.TexMapID, v.JointIndex, v.DisplayIndex, ref ts);

                                v.TextureStates[ti] = ts;
                            }
                            ti++;
                        }
                    }
                }

                UpdateMaterialFrame = false;
            }
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="visible"></param>
        /// <param name="selected"></param>
        /// <returns></returns>
        private bool DisplayObject(bool visible, bool selected)
        {
            switch (_settings.RenderObjects)
            {
                case ObjectRenderMode.All:
                    return true;
                case ObjectRenderMode.None:
                    return false;
                case ObjectRenderMode.Selected:
                    return selected;
                case ObjectRenderMode.Visible:
                    return visible;
            }

            return true;
        }

        /// <summary>
        /// 
        /// </summary>
        private void RenderJObjDisplay(Camera camera)
        {
            if (Environment.GetEnvironmentVariable("CSP_DOBJ_DEBUG") == "1")
            {
                int tot = RenderDobjs.Count, noP = 0, hid = 0, br = 0, op = 0, xl = 0, ne = 0;
                foreach (var e in RenderDobjs)
                {
                    if (e.PObjs.Count == 0) noP++;
                    if (!DisplayObject(e.Visible, e.Selected)) hid++;
                    if (!e.Parent.BranchVisible) br++;
                    bool mx = e._dobj.Mobj.RenderFlags.HasFlag(RENDER_MODE.XLU);
                    bool inOpa = !mx && e.Parent.Desc.Flags.HasFlag(JOBJ_FLAG.OPA);
                    bool inXlu = mx && (e.Parent.Desc.Flags.HasFlag(JOBJ_FLAG.XLU) || e.Parent.Desc.Flags.HasFlag(JOBJ_FLAG.TEXEDGE));
                    if (inOpa) op++; else if (inXlu) xl++; else ne++;
                }
                Console.WriteLine($"[cspdbg] dobjs={tot} noPobj={noP} hidden={hid} branchHidden={br} opaPass={op} xluPass={xl} neither={ne}");
            }

            // render opaque dobjs first
            foreach (RenderDObj opa in RenderDobjs.Where(e => !e._dobj.Mobj.RenderFlags.HasFlag(RENDER_MODE.XLU) && e.Parent.Desc.Flags.HasFlag(JOBJ_FLAG.OPA)))
            {
                if (DisplayObject(opa.Visible, opa.Selected) && opa.Parent.BranchVisible)
                    RenderDOBJShader(opa);
            }

            // render sorted xlu objects last
            foreach (RenderDObj xlu in RenderDobjs.Where(e =>
                e._dobj.Mobj.RenderFlags.HasFlag(RENDER_MODE.XLU) &&
                (e.Parent.Desc.Flags.HasFlag(JOBJ_FLAG.XLU) || e.Parent.Desc.Flags.HasFlag(JOBJ_FLAG.TEXEDGE))
                ))
            {
                if (DisplayObject(xlu.Visible, xlu.Selected) && xlu.Parent.BranchVisible)
                    RenderDOBJShader(xlu);
            }

            // render selection outline
            GL.DepthFunc(DepthFunction.Always);
            if (_settings.OutlineSelected)
                foreach (RenderDObj i in RenderDobjs.Where(e => e.Selected))
                {
                    RenderDOBJShader(i, true);
                }
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="dobj"></param>
        /// <param name="selected"></param>
        private void RenderDOBJShader(RenderDObj dobj, bool selected = false)
        {
            // check if dobj has polygons to render
            if (dobj.PObjs.Count == 0)
                return;

            // get parent jobj
            JOBJ_FLAG jointFlags = dobj.Parent.Desc.Flags;

            // setup skeleton flag
            _shader.SetBoolToInt("isSkeleton", jointFlags.HasFlag(JOBJ_FLAG.SKELETON_ROOT));// || jointFlags.HasFlag(JOBJ_FLAG.SKELETON));

            // setup single bind
            Matrix4 single = dobj.Parent.WorldTransform;
            GL.UniformMatrix4(_shader.GetVertexAttributeUniformLocation("singleBind"), false, ref single);

            // overlay params
            _shader.SetVector3("overlayColor", OverlayColor);
            _shader.SetBoolToInt("colorOverride", selected);

            // bind material
            if (!selected)
                SetupMObj(dobj);

            // get shape blending
            float shapeBlend = dobj.ShapeBlend;

            // bind buffer
            if (BufferManager.EnableBuffers(_shader, dobj._dobj, (int)shapeBlend, (int)shapeBlend + 1, shapeBlend - (int)shapeBlend))
            {
                // render pobjs
                foreach (RenderPObj p in dobj.PObjs)
                {
                    if (Environment.GetEnvironmentVariable("CSP_DOBJ_DEBUG") == "1" && p.DisplayLists.Count == 0)
                        Console.WriteLine($"[cspdbg] pobj has 0 display lists");
                    // get flags
                    POBJ_FLAG pobjflags = p.pobj.Flags;

                    // load envelopes
                    GL.Uniform1(_shader.GetVertexAttributeUniformLocation("envelopeIndex"), p.Envelopes.Length, ref p.Envelopes[0]);

                    // load weights
                    GL.Uniform1(_shader.GetVertexAttributeUniformLocation("weights"), p.Weights.Length, ref p.Weights[0]);

                    // set uniform flag information
                    _shader.SetBoolToInt("hasEnvelopes", p.HasWeighting);
                    _shader.SetBoolToInt("enableParentTransform", !pobjflags.HasFlag(POBJ_FLAG.SHAPESET_AVERAGE));

                    // enable parent transform
                    if (p.pobj.Flags.HasFlag(POBJ_FLAG.UNKNOWN2))
                        _shader.SetInt("enableParentTransform", 2);

                    // set culling
                    GL.Enable(EnableCap.CullFace);
                    if (selected)
                    {
                        GL.CullFace(CullFaceMode.Front);
                        GL.PolygonMode(MaterialFace.Back, PolygonMode.Line);
                    }
                    else
                    if (pobjflags.HasFlag(POBJ_FLAG.CULLFRONT))
                    {
                        GL.CullFace(CullFaceMode.Front);
                        GL.PolygonMode(MaterialFace.Front, PolygonMode.Fill);
                    }
                    else
                    if (pobjflags.HasFlag(POBJ_FLAG.CULLBACK))
                    {
                        GL.CullFace(CullFaceMode.Back);
                        GL.PolygonMode(MaterialFace.Back, PolygonMode.Fill);
                    }
                    else
                    {
                        GL.Disable(EnableCap.CullFace);
                    }

                    // draw display lists
                    foreach (CachedDL dl in p.DisplayLists)
                        GL.DrawArrays(dl.PrimType, dl.Offset, dl.Count);
                }
            }
            else if (Environment.GetEnvironmentVariable("CSP_DOBJ_DEBUG") == "1")
            {
                Console.WriteLine($"[cspdbg] EnableBuffers FAILED (pobjs={dobj.PObjs.Count})");
            }
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="mobj"></param>
        private void SetupMObj(RenderDObj dobj)
        {
            if (dobj == null && dobj._dobj != null && dobj._dobj.Mobj != null)
                return;

            HSD_MOBJ mobj = dobj._dobj.Mobj;
            LiveMaterial MaterialState = dobj.MaterialState;
            LiveTObj[] textureStates = dobj.TextureStates;
            HSD_JOBJ parentJOBJ = dobj.Parent.Desc;

            // init GL state
            GL.Enable(EnableCap.Texture2D);

            GL.Enable(EnableCap.Blend);
            GL.BlendFunc(BlendingFactor.SrcAlpha, BlendingFactor.OneMinusSrcAlpha);

            GL.Enable(EnableCap.AlphaTest);
            GL.AlphaFunc(AlphaFunction.Greater, 0f);

            GL.DepthMask(!mobj.RenderFlags.HasFlag(RENDER_MODE.NO_ZUPDATE));
            GL.DepthFunc(DepthFunction.Lequal);

            // Pixel Processing
            _shader.SetInt("alphaOp", -1); // none
            _shader.SetInt("alphaComp0", 7); // always
            _shader.SetInt("alphaComp1", 7);

            // Materials
            _shader.SetVector4("ambientColor", MaterialState.Ambient);
            _shader.SetVector4("diffuseColor", MaterialState.Diffuse);
            _shader.SetVector4("specularColor", MaterialState.Specular);
            _shader.SetFloat("shinniness", MaterialState.Shininess);
            _shader.SetFloat("alpha", MaterialState.Alpha);

            // pixel processing
            HSD_PEDesc pp = mobj.PEDesc;
            if (pp != null)
            {
                GL.BlendFunc(GXTranslator.toBlendingFactor(pp.SrcFactor), GXTranslator.toBlendingFactor(pp.DstFactor));
                GL.DepthFunc(GXTranslator.toDepthFunction(pp.DepthFunction));

                _shader.SetInt("alphaOp", (int)pp.AlphaOp);
                _shader.SetInt("alphaComp0", (int)pp.AlphaComp0);
                _shader.SetInt("alphaComp1", (int)pp.AlphaComp1);
                _shader.SetFloat("alphaRef0", MaterialState.Ref0);
                _shader.SetFloat("alphaRef1", MaterialState.Ref1);
            }

            // all flag
            bool enableAll = mobj.RenderFlags.HasFlag(RENDER_MODE.DF_ALL);
            // # of TObjs actually in this material's chain. DF_ALL (RenderMode bit 28)
            // -- and even a stray RenderMode TEX bit -- must NOT enable a texture UNIT
            // that has no TObj: the shader would then sample an unbound (black) unit
            // and the TEV combine multiplies the whole surface to black. (Seen on a
            // Sonic-over-Mario costume whose body MObj sets DF_ALL but ships a single
            // texture -> body rendered pure black.) Gate hasTEX by the texture count;
            // the bind loop below additionally turns on every TObj it actually loads,
            // covering chains whose real skin sits past the RenderMode TEX bits.
            int texCount = mobj.Textures?.List?.Count ?? 0;

            _shader.SetBoolToInt("no_zupdate", mobj.RenderFlags.HasFlag(RENDER_MODE.NO_ZUPDATE));
            _shader.SetBoolToInt("enableSpecular", parentJOBJ.Flags.HasFlag(JOBJ_FLAG.SPECULAR) && mobj.RenderFlags.HasFlag(RENDER_MODE.SPECULAR));
            _shader.SetBoolToInt("enableDiffuse", parentJOBJ.Flags.HasFlag(JOBJ_FLAG.LIGHTING) && mobj.RenderFlags.HasFlag(RENDER_MODE.DIFFUSE));
            _shader.SetBoolToInt("useConstant", mobj.RenderFlags.HasFlag(RENDER_MODE.CONSTANT));
            _shader.SetBoolToInt("useVertexColor", mobj.RenderFlags.HasFlag(RENDER_MODE.VERTEX));
            _shader.SetBoolToInt("useToonShading", mobj.RenderFlags.HasFlag(RENDER_MODE.TOON));

            // Textures
            for (int i = 0; i < MAX_TEX; i++)
            {
                _shader.SetBoolToInt($"hasTEX[{i}]", i < texCount && (enableAll || mobj.RenderFlags.HasFlag((RENDER_MODE)(1 << (i + 4)))));
            }

            // initialize bump texture to unused
            _shader.SetInt("BumpTexture", -1);

            // Bind Textures
            if (mobj.Textures != null)
            {
                List<HSD_TOBJ> textures = mobj.Textures.List;
                for (int i = 0; i < textures.Count; i++)
                {
                    // make sure texture is not out of supported range
                    if (i > MAX_TEX)
                        break;

                    // get texture
                    HSD_TOBJ tex = textures[i];
                    HSD_TOBJ_TEV tev = tex.TEV;

                    // texture state info
                    HSD_TOBJ displayTex;
                    float blending;
                    Matrix4 transform;
                    Vector4 konst = Vector4.Zero;
                    Vector4 tev0 = Vector4.Zero;
                    Vector4 tev1 = Vector4.Zero;

                    // get texture state data if it exists
                    if (textureStates != null && i < textureStates.Length && textureStates[i] != null)
                    {
                        LiveTObj texState = textureStates[i];
                        displayTex = texState.TOBJ;
                        blending = texState.Blending;
                        transform = texState.Transform;
                        if (tev != null)
                        {
                            konst = texState.Konst;
                            tev0 = texState.Tev0;
                            tev1 = texState.Tev1;
                        }
                    }
                    else
                    {
                        displayTex = tex;
                        blending = tex.Blending;
                        transform = Matrix4.Identity;

                        if (tev != null)
                        {
                            konst = new Vector4(tev.constant.R / 255f, tev.constant.B / 255f, tev.constant.G / 255f, tev.constantAlpha / 255f);
                            tev0 = new Vector4(tev.tev0.R / 255f, tev.tev0.B / 255f, tev.tev0.G / 255f, tev.tev0Alpha / 255f);
                            tev1 = new Vector4(tev.tev1.R / 255f, tev.tev1.B / 255f, tev.tev1.G / 255f, tev.tev1Alpha / 255f);
                        }
                    }

                    // if texture image data is null skip setup?
                    if (tex.ImageData == null)
                        continue;

                    // make sure texture is loaded
                    if (!PreLoadTexture(displayTex))
                        continue;

                    // grab texture id
                    int texid = TextureManager.GetGLID(imageBufferTextureIndex[TexCacheKey(displayTex)]);

                    // set texture
                    GL.ActiveTexture(TextureUnit.Texture0 + i);
                    GL.BindTexture(TextureTarget.Texture2D, texid);
                    GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapS, (int)GXTranslator.toWrapMode(tex.WrapS));
                    GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapT, (int)GXTranslator.toWrapMode(tex.WrapT));
                    GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMagFilter, (int)GXTranslator.toMagFilter(tex.MagFilter));
                    GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureLodBias, 0); //640×548

                    // optional texture mipmap coords
                    if (tex.LOD != null)
                    {
                        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureLodBias, tex.LOD.Bias); //640×548
                    }

                    // A texture actually present (and loaded) in the material's TObj
                    // chain is sampled by the game regardless of the MOBJ RenderMode
                    // TEX0..7 bits: Melee's HSD_TObjSetup walks the whole chain and the
                    // TEV stages combine every TObj. Some re-exported/"scrambled"
                    // costumes carry MORE TObjs than RenderMode TEX flags -- e.g. a
                    // body material flagged RM=TEX0 but whose real skin is a shared
                    // atlas at TObj index 3. Gating hasTEX by RenderMode alone then
                    // samples only TEX0 (a tiny stub) and renders the body flat white
                    // (cause G). Enabling each present slot here makes its TEV stage
                    // run, matching the game. (No effect on normal models: their
                    // RenderMode TEX bits already match the TObjs that load here.)
                    _shader.SetBoolToInt($"hasTEX[{i}]", true);

                    TOBJ_FLAGS flags = tex.Flags;

                    int coordType = (int)flags & 0xF;
                    int colorOP = ((int)flags >> 16) & 0xF;
                    int alphaOP = ((int)flags >> 20) & 0xF;

                    if (flags.HasFlag(TOBJ_FLAGS.BUMP))
                    {
                        colorOP = 4;
                    }

                    _shader.SetInt($"sampler{i}", i);
                    _shader.SetInt($"TEX[{i}].gensrc", (int)tex.GXTexGenSrc);
                    _shader.SetBoolToInt($"TEX[{i}].is_ambient", flags.HasFlag(TOBJ_FLAGS.LIGHTMAP_AMBIENT));
                    _shader.SetBoolToInt($"TEX[{i}].is_diffuse", flags.HasFlag(TOBJ_FLAGS.LIGHTMAP_DIFFUSE));
                    _shader.SetBoolToInt($"TEX[{i}].is_specular", flags.HasFlag(TOBJ_FLAGS.LIGHTMAP_SPECULAR));
                    _shader.SetBoolToInt($"TEX[{i}].is_ext", flags.HasFlag(TOBJ_FLAGS.LIGHTMAP_EXT));
                    _shader.SetBoolToInt($"TEX[{i}].is_bump", flags.HasFlag(TOBJ_FLAGS.BUMP));
                    _shader.SetInt($"TEX[{i}].color_operation", colorOP);
                    _shader.SetInt($"TEX[{i}].alpha_operation", alphaOP);
                    _shader.SetInt($"TEX[{i}].coord_type", coordType);
                    _shader.SetFloat($"TEX[{i}].blend", blending);
                    _shader.SetMatrix4x4($"TEX[{i}].transform", ref transform);

                    bool colorTev = tev != null && tev.active.HasFlag(TOBJ_TEVREG_ACTIVE.COLOR_TEV);
                    bool alphaTev = tev != null && tev.active.HasFlag(TOBJ_TEVREG_ACTIVE.ALPHA_TEV);
                    _shader.SetBoolToInt($"hasColorTev[{i}]", colorTev);
                    _shader.SetBoolToInt($"hasAlphaTev[{i}]", alphaTev);
                    if (colorTev)
                    {
                        _shader.SetInt($"Tev[{i}].color_op", (int)tev.color_op);
                        _shader.SetInt($"Tev[{i}].color_bias", (int)tev.color_bias);
                        _shader.SetInt($"Tev[{i}].color_scale", (int)tev.color_scale);
                        _shader.SetBoolToInt($"Tev[{i}].color_clamp", tev.color_clamp);
                        _shader.SetInt($"Tev[{i}].color_a", (int)tev.color_a_in);
                        _shader.SetInt($"Tev[{i}].color_b", (int)tev.color_b_in);
                        _shader.SetInt($"Tev[{i}].color_c", (int)tev.color_c_in);
                        _shader.SetInt($"Tev[{i}].color_d", (int)tev.color_d_in);
                    }
                    if (alphaTev)
                    {
                        _shader.SetInt($"Tev[{i}].alpha_op", (int)tev.alpha_op);
                        _shader.SetInt($"Tev[{i}].alpha_bias", (int)tev.alpha_bias);
                        _shader.SetInt($"Tev[{i}].alpha_scale", (int)tev.alpha_scale);
                        _shader.SetBoolToInt($"Tev[{i}].alpha_clamp", tev.alpha_clamp);
                        _shader.SetInt($"Tev[{i}].alpha_a", (int)tev.alpha_a_in);
                        _shader.SetInt($"Tev[{i}].alpha_b", (int)tev.alpha_b_in);
                        _shader.SetInt($"Tev[{i}].alpha_c", (int)tev.alpha_c_in);
                        _shader.SetInt($"Tev[{i}].alpha_d", (int)tev.alpha_d_in);
                    }

                    _shader.SetVector4($"Tev[{i}].konst", konst);
                    _shader.SetVector4($"Tev[{i}].tev0", tev0);
                    _shader.SetVector4($"Tev[{i}].tev1", tev1);
                }
            }
        }

        /// <summary>
        /// 
        /// </summary>
        public bool PreLoadTexture(HSD_TOBJ tobj)
        {
            if (tobj?.ImageData?.ImageData == null)
                return false;

            if (!imageBufferTextureIndex.ContainsKey(TexCacheKey(tobj)))
            {
                byte[] rawImageData = tobj.ImageData.ImageData;
                short width = tobj.ImageData.Width;
                short height = tobj.ImageData.Height;

                List<byte[]> mips = new();

                try
                {
                    if (tobj.LOD != null && tobj.ImageData.MaxLOD != 0)
                    {
                        for (int i = 0; i < tobj.ImageData.MaxLOD - 1; i++)
                            mips.Add(tobj.GetDecodedImageData(i));
                    }
                    else
                    {
                        mips.Add(tobj.GetDecodedImageData());
                    }
                }
                catch (Exception ex)
                {
                    if (Environment.GetEnvironmentVariable("CSP_DOBJ_DEBUG") == "1")
                        Console.WriteLine($"[texfail] {width}x{height} fmt={tobj.ImageData.Format} tlut={tobj.TlutData?.ColorCount}: {ex.Message}");
                    System.Diagnostics.Debug.WriteLine($"PreLoadTexture: skipped undecodable texture: {ex.Message}");
                    return false;
                }

                if (Environment.GetEnvironmentVariable("CSP_DOBJ_DEBUG") == "1" && mips.Count > 0 && mips[0].Length >= 4)
                {
                    var _p = mips[0];
                    Console.WriteLine($"[texdbg] {width}x{height} fmt={tobj.ImageData.Format} tlut={tobj.TlutData?.ColorCount} px0=({_p[0]},{_p[1]},{_p[2]},{_p[3]})");
                }

                int index = TextureManager.Add(mips, width, height);

                imageBufferTextureIndex.Add((rawImageData, tobj.TlutData?.TlutData), index);
                UpdateLog?.Invoke($"PreLoadTexture: NEW GL texture tmi={index} glId={TextureManager.GetGLID(index)} "
                    + $"{width}x{height} dataLen={rawImageData.Length} "
                    + $"tobj={System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(tobj):x8} "
                    + $"arr={System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(rawImageData):x8}");
            }
            return true;
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="shader"></param>
        public void SetupShader()
        {
            // nothing to render
            if (RootJObj == null)
                return;

            if (_shader == null)
                return;

            // update selected bone
            _shader.SelectedBone = RootJObj.GetIndexOfDesc(SelectedJObj);

            // set render mode
            _shader.RenderMode = RenderMode;

            // update shader bone transforms
            int i = 0;
            foreach (LiveJObj v in RootJObj.Enumerate)
            {
                if (i < Shader.MAX_BONES)
                {
                    _shader.WorldTransforms[i] = v.WorldTransform;
                    _shader.WorldTransforms[i + Shader.MAX_BONES] = v.BindTransform;
                    i++;
                }
                else
                {
                    break;
                }
            }
        }

        /// <summary>
        /// 
        /// </summary>
        private void RenderBoneOverlay()
        {
            if (!_settings.RenderBones)
                return;

            GL.PushAttrib(AttribMask.AllAttribBits);

            GL.Disable(EnableCap.Texture2D);
            GL.Disable(EnableCap.DepthTest);

            float mag = 0;

            if (_settings.RenderOrientation)
                mag = 2; //Vector3.TransformPosition(new Vector3(1, 0, 0), camera.MvpMatrix.Inverted()).Length / 30;

            foreach (LiveJObj b in RootJObj.Enumerate)
                RenderBone(mag, b, b.Desc.Equals(SelectedJObj));

            GL.PopAttrib();
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="transform"></param>
        /// <param name="parentTransform"></param>
        private void RenderBone(float mag, LiveJObj jobj, bool selected)
        {
            Matrix4 transform = jobj.WorldTransform;

            if (jobj.Parent != null)
            {
                Matrix4 parentTransform = jobj.Parent.WorldTransform;

                Vector3 bonePosition = transform.ExtractTranslation();
                Vector3 parentPosition = parentTransform.ExtractTranslation();

                GL.LineWidth(1f);
                GL.Begin(PrimitiveType.Lines);
                GL.Color3(0f, 1f, 0f);
                GL.Vertex3(parentPosition);
                GL.Color3(0f, 0f, 1f);
                GL.Vertex3(bonePosition);
                GL.End();
            }

            if (selected)
            {
                GL.Color3(1f, 1f, 0f);
                GL.PointSize(7f);
            }
            else
            {
                GL.Color3(1f, 0f, 0f);
                GL.PointSize(5f);
            }

            GL.PushMatrix();
            GL.MultMatrix(ref transform);

            GL.Begin(PrimitiveType.Points);
            GL.Vertex3(0, 0, 0);
            GL.End();

            if (_settings.RenderOrientation)
            {
                GL.LineWidth(1.5f);

                GL.Begin(PrimitiveType.Lines);
                GL.Color3(1f, 0f, 0f);
                GL.Vertex3(0, 0, 0);
                GL.Vertex3(mag, 0, 0);
                GL.Color3(0f, 1f, 0f);
                GL.Vertex3(0, 0, 0);
                GL.Vertex3(0, mag, 0);
                GL.Color3(0f, 0f, 1f);
                GL.Vertex3(0, 0, 0);
                GL.Vertex3(0, 0, mag);
                GL.End();
            }

            GL.PopMatrix();
        }

        /// <summary>
        /// 
        /// </summary>
        private void DrawSplines(Camera camera)
        {
            if (RootJObj == null)
                return;

            foreach (LiveJObj j in RootJObj.Enumerate)
                if (j.Desc.Spline != null)
                    DrawShape.RenderSpline(j.WorldTransform, j.Desc.Spline, Color.Yellow, Color.Blue);
        }

        /// <summary>
        /// 
        /// </summary>
        public void ClearDObjSelection()
        {
            foreach (RenderDObj d in RenderDobjs)
                d.Selected = false;
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="index"></param>
        /// <param name="selected"></param>
        public void SetDObjSelected(int index, bool selected)
        {
            if (index >= 0 && index < RenderDobjs.Count)
                RenderDobjs[index].Selected = selected;
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="index"></param>
        /// <param name="selected"></param>
        public void SetDObjVisible(int index, bool visible)
        {
            if (index >= 0 && index < RenderDobjs.Count)
                RenderDobjs[index].Visible = visible;
        }

        /// <summary>
        /// Gets the total number of DOBJs
        /// </summary>
        public int DObjCount => RenderDobjs.Count;

        /// <summary>
        /// Gets a list of all hidden DObj indices
        /// </summary>
        /// <returns>Array of indices for DOBJs that are not visible</returns>
        public int[] GetHiddenDObjIndices()
        {
            var hidden = new List<int>();
            for (int i = 0; i < RenderDobjs.Count; i++)
            {
                if (!RenderDobjs[i].Visible)
                    hidden.Add(i);
            }
            return hidden.ToArray();
        }

        /// <summary>
        /// Hides all DOBJs that belong to the specified JOBJ indices
        /// </summary>
        /// <param name="jobjIndices">List of JOBJ indices to hide</param>
        public void HideDObjsByJObjIndex(IEnumerable<int> jobjIndices)
        {
            var hiddenJobjSet = new HashSet<int>(jobjIndices);
            int hiddenCount = 0;

            for (int i = 0; i < RenderDobjs.Count; i++)
            {
                var dobj = RenderDobjs[i];
                if (hiddenJobjSet.Contains(dobj.JointIndex))
                {
                    dobj.Visible = false;
                    hiddenCount++;
                }
            }

            Console.WriteLine($"Successfully hid {hiddenCount} DOBJs out of {RenderDobjs.Count} total");
        }

        /// <summary>
        /// Registers the DAT's matanim_joint roots so MatAnim texture-swap
        /// frames (blink/half-closed eyes etc.) are exposed in the texture
        /// list and covered by content-matched updates. The synthetic TOBJs
        /// share the buffers' HSD_Image/HSD_Tlut accessors, so injections
        /// land in the raw file in place.
        /// </summary>
        public void SetMatAnims(IEnumerable<HSD_MatAnimJoint> matAnimRoots)
        {
            _matAnimBanks.Clear();
            if (matAnimRoots == null)
                return;
            foreach (var root in matAnimRoots)
            {
                if (root == null)
                    continue;
                foreach (var joint in root.TreeList)
                {
                    if (joint.MaterialAnimation == null)
                        continue;
                    foreach (var matAnim in joint.MaterialAnimation.List)
                    {
                        if (matAnim.TextureAnimation == null)
                            continue;
                        foreach (var texAnim in matAnim.TextureAnimation.List)
                        {
                            if (texAnim.ImageCount > 0 && texAnim.ImageBuffers != null)
                                _matAnimBanks.Add((texAnim, texAnim.ToTOBJs()));
                        }
                    }
                }
            }
        }

        /// <summary>
        /// Registers JOBJ roots beyond the rendered one (costume accessories
        /// like Jigglypuff's hats ship as their own *_TopN_joint root) so
        /// their material textures appear in the texture list and are
        /// covered by content-matched updates. The TOBJs are the raw file's
        /// own accessors, so injections land in the file in place.
        /// </summary>
        public void SetExtraRoots(IEnumerable<HSD_JOBJ> roots)
        {
            _extraRoots.Clear();
            if (roots == null)
                return;
            foreach (var root in roots)
                if (root != null)
                    _extraRoots.Add(root);
        }

        private IEnumerable<HSD_TOBJ> ExtraRootTobjs()
        {
            foreach (var root in _extraRoots)
                foreach (var jobj in root.TreeList)
                {
                    if (jobj.Dobj == null)
                        continue;
                    foreach (var dobj in jobj.Dobj.List)
                    {
                        if (dobj?.Mobj?.Textures == null)
                            continue;
                        foreach (var tobj in dobj.Mobj.Textures.List)
                            yield return tobj;
                    }
                }
        }

        private static bool TexDataEquals(byte[] a, byte[] b)
            => ReferenceEquals(a, b)
               || (a != null && b != null && a.Length == b.Length
                   && System.MemoryExtensions.SequenceEqual<byte>(a, b));

        /// <summary>
        /// Gets a list of all textures used by this model -- the material
        /// (DOBJ) textures first, then any MatAnim swap frames whose content
        /// isn't already listed (a TexAnim's frame 0 usually duplicates the
        /// material texture it animates; those are skipped and instead used
        /// to link the bank to its base texture via AnimatesIndex).
        /// </summary>
        public List<TextureInfo> GetTextureList()
        {
            var textures = new List<TextureInfo>();
            var seenTextures = new HashSet<byte[]>();
            int textureIndex = 0;

            TextureInfo MakeInfo(HSD_TOBJ tobj, int glTextureId)
            {
                int width = tobj.ImageData.Width;
                int height = tobj.ImageData.Height;
                byte[] rgbaData = tobj.GetDecodedImageData();

                // Generate thumbnail (64x64)
                string thumbnailBase64 = "";
                try
                {
                    using var image = SixLabors.ImageSharp.Image.LoadPixelData<SixLabors.ImageSharp.PixelFormats.Bgra32>(rgbaData, width, height);
                    image.Mutate(x => x.Resize(64, 64));
                    using var ms = new System.IO.MemoryStream();
                    image.Save(ms, new SixLabors.ImageSharp.Formats.Png.PngEncoder());
                    thumbnailBase64 = Convert.ToBase64String(ms.ToArray());
                }
                catch { }

                return new TextureInfo
                {
                    Index = textureIndex,
                    Width = width,
                    Height = height,
                    Name = $"Texture_{textureIndex}",
                    RgbaData = rgbaData,
                    ThumbnailBase64 = thumbnailBase64,
                    GlTextureId = glTextureId,
                    Tobj = tobj
                };
            }

            foreach (var dobj in RenderDobjs)
            {
                if (dobj._dobj?.Mobj?.Textures == null)
                    continue;

                foreach (var tobj in dobj._dobj.Mobj.Textures.List)
                {
                    if (tobj?.ImageData?.ImageData == null)
                        continue;

                    // Skip if we've already seen this texture data
                    if (seenTextures.Contains(tobj.ImageData.ImageData))
                        continue;

                    seenTextures.Add(tobj.ImageData.ImageData);

                    // Get OpenGL texture ID
                    int glTextureId = -1;
                    if (imageBufferTextureIndex.TryGetValue(TexCacheKey(tobj), out int texIndex))
                    {
                        glTextureId = TextureManager.GetGLID(texIndex);
                    }

                    textures.Add(MakeInfo(tobj, glTextureId));
                    textureIndex++;
                }
            }

            // MatAnim swap frames (blink etc.) -- textures the DOBJ walk
            // can't see. Content-duplicates of listed textures are skipped
            // (updates reach them via content matching); the rest are
            // appended after the material textures so existing indexes are
            // stable.
            int matAnimCount = 0;
            foreach (var (anim, frames) in _matAnimBanks)
            {
                // the bank's base texture: the listed texture some frame of
                // this bank duplicates (frame 0 is the default/open state)
                int animates = -1;
                foreach (var frame in frames)
                {
                    if (frame?.ImageData?.ImageData == null)
                        continue;
                    var match = textures.FirstOrDefault(t => !t.IsMatAnim
                        && TexDataEquals(t.Tobj?.ImageData?.ImageData, frame.ImageData.ImageData));
                    if (match != null)
                    {
                        animates = match.Index;
                        break;
                    }
                }

                foreach (var frame in frames)
                {
                    if (frame?.ImageData?.ImageData == null)
                        continue;
                    if (textures.Any(t => TexDataEquals(t.Tobj?.ImageData?.ImageData, frame.ImageData.ImageData)))
                        continue;

                    var info = MakeInfo(frame, -1);
                    info.IsMatAnim = true;
                    info.AnimatesIndex = animates;
                    info.Name = $"MatAnim_{matAnimCount}";
                    textures.Add(info);
                    textureIndex++;
                    matAnimCount++;
                }
            }

            // Extra (non-rendered) JOBJ roots -- e.g. Jigglypuff's alt-costume
            // hats. Appended last so the material/matanim indexes existing
            // callers cached stay stable.
            int extraCount = 0;
            foreach (var tobj in ExtraRootTobjs())
            {
                if (tobj?.ImageData?.ImageData == null)
                    continue;
                if (textures.Any(t => TexDataEquals(t.Tobj?.ImageData?.ImageData, tobj.ImageData.ImageData)))
                    continue;

                var info = MakeInfo(tobj, -1);
                info.IsExtraRoot = true;
                info.Name = $"Extra_{extraCount}";
                textures.Add(info);
                textureIndex++;
                extraCount++;
            }

            return textures;
        }

        /// <summary>
        /// Exports the UV layout of every texture in a previously captured
        /// texture list: per texture, the triangles that sample it, as
        /// (transformed UV, posed world-space position) per corner. UVs have
        /// the TOBJ's texture matrix applied (repeat/mirror scaling included),
        /// i.e. they are in WRAP units where [0,1] is one tile; positions
        /// mirror gx.vert's skinning exactly at the CURRENT pose. Geometry of
        /// hidden DOBJs is emitted first so overlapping bakes resolve in
        /// favor of the visible mesh. Reflection/toon-mapped TOBJs have no
        /// stable UV layout and are skipped.
        /// </summary>
        public List<object> GetUVLayout(List<TextureInfo> cachedTextureList)
        {
            const int W_MAX = 6;       // RenderPObj.MAX_WEIGHTS
            const int W_STRIDE = 10;   // RenderPObj.WEIGHT_STRIDE

            // bone matrices in shader order (RootJObj.Enumerate)
            var worlds = new List<Matrix4>();
            var binds = new List<Matrix4>();
            if (RootJObj != null)
            {
                foreach (LiveJObj v in RootJObj.Enumerate)
                {
                    worlds.Add(v.WorldTransform);
                    binds.Add(v.BindTransform);
                }
            }

            // row-vector transforms (matches LiveJObj composition + how the
            // shader sees the uploaded matrices)
            Vector3 XformPos(Vector3 p, Matrix4 m) => Vector3.TransformPosition(p, m);
            Vector2 XformUV(float u, float v, Matrix4 m)
            {
                float x = u * m.M11 + v * m.M21 + m.M41;
                float y = u * m.M12 + v * m.M22 + m.M42;
                float w = u * m.M14 + v * m.M24 + m.M44;
                if (Math.Abs(w) < 1e-9f)
                    w = 1;
                return new Vector2(x / w, y / w);
            }

            var triangles = new Dictionary<int, List<float[]>>();

            foreach (var dobj in RenderDobjs.OrderBy(d => d.Visible ? 1 : 0))
            {
                var texList = dobj._dobj?.Mobj?.Textures?.List;
                if (texList == null || dobj.Parent == null)
                    continue;

                // which cached textures this dobj samples, via which vertex
                // UV channel and texture matrix
                var bindings = new List<(int cacheIdx, int channel, Matrix4 xform)>();
                for (int ti = 0; ti < texList.Count; ti++)
                {
                    var tobj = texList[ti];
                    if (tobj?.ImageData?.ImageData == null)
                        continue;
                    if (tobj.CoordType != HSDRaw.Common.COORD_TYPE.UV)
                        continue;
                    int gensrc = (int)tobj.GXTexGenSrc;
                    int channel;
                    if (gensrc >= (int)GXTexGenSrc.GX_TG_TEX0 && gensrc <= (int)GXTexGenSrc.GX_TG_TEX7)
                        channel = Math.Min(gensrc - (int)GXTexGenSrc.GX_TG_TEX0, 3);
                    else if (gensrc >= (int)GXTexGenSrc.GX_TG_TEXCOORD0 && gensrc <= (int)GXTexGenSrc.GX_TG_TEXCOORD6)
                        channel = Math.Min(gensrc - (int)GXTexGenSrc.GX_TG_TEXCOORD0, 3);
                    else
                        continue;
                    int ci = cachedTextureList.FindIndex(t => !t.IsMatAnim
                        && TexDataEquals(t.Tobj?.ImageData?.ImageData, tobj.ImageData.ImageData));
                    if (ci < 0)
                        continue;
                    Matrix4 xf;
                    if (ti < dobj.TextureStates.Length && dobj.TextureStates[ti].TOBJ != null)
                        xf = dobj.TextureStates[ti].Transform;
                    else
                    {
                        var lt = new LiveTObj();
                        lt.Reset(tobj);
                        xf = lt.Transform;
                    }
                    bindings.Add((ci, channel, xf));
                }
                if (bindings.Count == 0)
                    continue;

                bool isSkeleton = dobj.Parent.Desc.Flags.HasFlag(JOBJ_FLAG.SKELETON_ROOT);
                Matrix4 single = dobj.Parent.WorldTransform;

                foreach (var p in dobj.PObjs)
                {
                    GX_Attribute[] attrs;
                    try
                    {
                        attrs = p.pobj.ToGXAttributes();
                        if (attrs.Length == 0 || attrs[attrs.Length - 1].AttributeName != GXAttribName.GX_VA_NULL)
                            continue;
                    }
                    catch
                    {
                        continue;
                    }
                    var dl = p.pobj.ToDisplayList(attrs);
                    bool envelopes = p.HasWeighting;
                    bool parent2 = p.pobj.Flags.HasFlag(POBJ_FLAG.UNKNOWN2);
                    bool parent1 = !p.pobj.Flags.HasFlag(POBJ_FLAG.SHAPESET_AVERAGE);

                    Vector3 PosedPosition(GX_Vertex v)
                    {
                        var pos = new Vector3(v.POS.X, v.POS.Y, v.POS.Z);
                        int mi = Math.Clamp(v.PNMTXIDX / 3, 0, W_STRIDE - 1);
                        if (envelopes)
                        {
                            // mirrors gx.vert: non-skeleton roots apply the
                            // parent transform BEFORE skinning
                            float w0 = p.Weights[mi * W_MAX];
                            if (!isSkeleton)
                                pos = XformPos(pos, single);
                            if (isSkeleton && w0 == 1f)
                            {
                                int b0 = p.Envelopes[mi * W_MAX];
                                if (b0 >= 0 && b0 < worlds.Count)
                                    pos = XformPos(pos, worlds[b0]);
                            }
                            else
                            {
                                var skinned = Vector3.Zero;
                                for (int wi = 0; wi < W_MAX; wi++)
                                {
                                    float w = p.Weights[mi * W_MAX + wi];
                                    if (w <= 0)
                                        continue;
                                    int b = p.Envelopes[mi * W_MAX + wi];
                                    if (b >= 0 && b < binds.Count)
                                        skinned += XformPos(pos, binds[b]) * w;
                                }
                                pos = skinned;
                            }
                        }
                        else if (parent2)
                        {
                            int b0 = p.Envelopes[mi * W_MAX];
                            if (b0 >= 0 && b0 < worlds.Count)
                                pos = XformPos(pos, worlds[b0]);
                        }
                        else if (parent1)
                        {
                            pos = XformPos(pos, single);
                        }
                        return pos;
                    }

                    int off = 0;
                    foreach (var prim in dl.Primitives)
                    {
                        var verts = dl.Vertices.GetRange(off, prim.Count);
                        off += prim.Count;
                        switch (prim.PrimitiveType)
                        {
                            case GXPrimitiveType.Quads:
                                verts = HSDRawViewer.Tools.TriangleConverter.QuadToList(verts);
                                break;
                            case GXPrimitiveType.TriangleStrip:
                                verts = HSDRawViewer.Tools.TriangleConverter.StripToList(verts);
                                break;
                            case GXPrimitiveType.TriangleFan:
                                {
                                    // fan (c, v1, v2, v3...) -> (c,v1,v2), (c,v2,v3), ...
                                    var fan = new List<GX_Vertex>();
                                    for (int f = 1; f + 1 < verts.Count; f++)
                                    {
                                        fan.Add(verts[0]);
                                        fan.Add(verts[f]);
                                        fan.Add(verts[f + 1]);
                                    }
                                    verts = fan;
                                }
                                break;
                            case GXPrimitiveType.Triangles:
                                break;
                            default:
                                continue;   // points/lines paint nothing useful
                        }
                        for (int t = 0; t + 2 < verts.Count; t += 3)
                        {
                            Vector3 p0 = PosedPosition(verts[t]);
                            Vector3 p1 = PosedPosition(verts[t + 1]);
                            Vector3 p2 = PosedPosition(verts[t + 2]);

                            foreach (var (ci, channel, xf) in bindings)
                            {
                                Vector2 RawUV(GX_Vertex v) => channel switch
                                {
                                    0 => new Vector2(v.TEX0.X, v.TEX0.Y),
                                    1 => new Vector2(v.TEX1.X, v.TEX1.Y),
                                    2 => new Vector2(v.TEX2.X, v.TEX2.Y),
                                    _ => new Vector2(v.TEX3.X, v.TEX3.Y),
                                };
                                Vector2 uv0 = XformUV(RawUV(verts[t]).X, RawUV(verts[t]).Y, xf);
                                Vector2 uv1 = XformUV(RawUV(verts[t + 1]).X, RawUV(verts[t + 1]).Y, xf);
                                Vector2 uv2 = XformUV(RawUV(verts[t + 2]).X, RawUV(verts[t + 2]).Y, xf);

                                // strips emit degenerate triangles; they paint nothing
                                float area = Math.Abs((uv1.X - uv0.X) * (uv2.Y - uv0.Y)
                                                    - (uv2.X - uv0.X) * (uv1.Y - uv0.Y));
                                if (area < 1e-10f)
                                    continue;

                                if (!triangles.TryGetValue(ci, out var list))
                                    triangles[ci] = list = new List<float[]>();
                                list.Add(new[]
                                {
                                    uv0.X, uv0.Y, uv1.X, uv1.Y, uv2.X, uv2.Y,
                                    p0.X, p0.Y, p0.Z,
                                    p1.X, p1.Y, p1.Z,
                                    p2.X, p2.Y, p2.Z,
                                });
                            }
                        }
                    }
                }
            }

            var result = new List<object>();
            foreach (var tex in cachedTextureList)
            {
                if (!triangles.TryGetValue(tex.Index, out var list))
                    continue;
                result.Add(new
                {
                    index = tex.Index,
                    width = tex.Width,
                    height = tex.Height,
                    wrapS = (int)(tex.Tobj?.WrapS ?? GXWrapMode.REPEAT),
                    wrapT = (int)(tex.Tobj?.WrapT ?? GXWrapMode.REPEAT),
                    triangles = list,
                });
            }
            return result;
        }

        // GL texture indexes for content-duplicate instances that were merged by
        // an update (one array can only key one entry in imageBufferTextureIndex,
        // but the duplicates' GL textures still need refreshing on later updates).
        private readonly Dictionary<byte[], List<int>> _mergedGlIndexes = new Dictionary<byte[], List<int>>();

        /// <summary>
        /// Optional diagnostics sink for texture updates (set by streaming hosts).
        /// </summary>
        public static Action<string> UpdateLog;

        /// <summary>
        /// Updates a texture with new image data.
        ///
        /// Melee models frequently contain the SAME texture as multiple array
        /// instances (visible + hidden duplicates across DOBJs/LODs), so TOBJs
        /// are matched by CONTENT, not reference -- updating only a
        /// reference-shared group can land entirely on a hidden duplicate and
        /// leave the on-screen instance stale (silent no-op).
        /// </summary>
        public void UpdateTexture(int textureIndex, byte[] pngData)
        {
            // Legacy index-based entry: indexes into a FRESH enumeration, which
            // can diverge from a list the caller cached earlier. Callers holding
            // a cached list should use the TextureInfo overload instead.
            var textures = GetTextureList();

            if (textureIndex < 0 || textureIndex >= textures.Count)
            {
                return;
            }

            UpdateTexture(textures[textureIndex], pngData);
        }

        /// <summary>
        /// Updates the texture referenced by a TextureInfo from a PREVIOUSLY
        /// CAPTURED texture list -- immune to enumeration drift between the
        /// caller's cache and the live DOBJ set.
        /// </summary>
        public void UpdateTexture(TextureInfo texInfo, byte[] pngData)
        {
            if (texInfo?.Tobj?.ImageData?.ImageData == null)
            {
                return;
            }

            byte[] oldImageData = texInfo.Tobj.ImageData.ImageData;

            // Find ALL TOBJs whose texture content matches, and every distinct
            // backing array among them. MatAnim swap-frame TOBJs are included:
            // a TexAnim's default frame often duplicates the material texture,
            // and edits must land on BOTH or the character flashes the stock
            // texture whenever the animation swaps frames (the blink bug).
            var tobjsToUpdate = new List<HSD_TOBJ>();
            var oldArrays = new List<byte[]>();
            var seenImages = new HashSet<HSD_Image>();
            void Collect(HSD_TOBJ tobj)
            {
                var data = tobj?.ImageData?.ImageData;
                if (data == null)
                    return;
                if (!TexDataEquals(data, oldImageData))
                    return;
                // distinct TOBJs can share one HSD_Image accessor -- encode once
                if (!seenImages.Add(tobj.ImageData))
                    return;
                tobjsToUpdate.Add(tobj);
                if (!oldArrays.Any(a => ReferenceEquals(a, data)))
                    oldArrays.Add(data);
            }
            foreach (var dobj in RenderDobjs)
            {
                if (dobj._dobj?.Mobj?.Textures == null)
                    continue;
                foreach (var tobj in dobj._dobj.Mobj.Textures.List)
                    Collect(tobj);
            }
            foreach (var (_, frames) in _matAnimBanks)
                foreach (var frame in frames)
                    Collect(frame);
            foreach (var tobj in ExtraRootTobjs())
                Collect(tobj);
            if (tobjsToUpdate.Count == 0)
            {
                UpdateLog?.Invoke($"UpdateTexture: NO content match (oldData len={oldImageData.Length})");
                return;
            }

            // Decode PNG to BGRA (matching original texture format)
            using var image = SixLabors.ImageSharp.Image.Load<SixLabors.ImageSharp.PixelFormats.Bgra32>(pngData);
            byte[] bgraData = new byte[image.Width * image.Height * 4];
            image.CopyPixelDataTo(bgraData);

            UpdateLog?.Invoke($"UpdateTexture: tobjs={tobjsToUpdate.Count} arrays={oldArrays.Count} "
                + $"{image.Width}x{image.Height}");

            // Update HSD TOBJ data for export - update ALL matching TOBJs
            var imgFormat = texInfo.Tobj.ImageData?.Format ?? GXTexFmt.RGBA8;
            var palFormat = texInfo.Tobj.TlutData?.Format ?? GXTlutFmt.RGB565;

            // Size-increasing pushes carry MORE detail than the original slot
            // (the tiny-texture upscale for composites) -- a 16-color CI4
            // palette would posterize it, so step those up to CI8.
            if (imgFormat == GXTexFmt.CI4
                && (image.Width > texInfo.Width || image.Height > texInfo.Height))
            {
                imgFormat = GXTexFmt.CI8;
            }

            byte[] newImageData = null;
            foreach (var tobj in tobjsToUpdate)
            {
                tobj.InjectBitmap(image, imgFormat, palFormat);
                if (newImageData == null)
                {
                    newImageData = tobj.ImageData.ImageData;
                }
                else
                {
                    // Make all TOBJs share the same byte[] reference
                    tobj.ImageData.ImageData = newImageData;
                }
                UpdateLog?.Invoke($"UpdateTexture: injected tobj={System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(tobj):x8} "
                    + $"arr={System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(tobj.ImageData.ImageData):x8}");
            }

            // Deliberately NO GL writes and NO re-keying of imageBufferTextureIndex:
            // MULTIPLE RenderJObj instances can render these shared HSD structs,
            // each with its own GL bookkeeping. Mapping the new array onto this
            // instance's old GL id pins OTHER instances (and later edits) to a
            // stale texture. Instead, drop this instance's old keys and let every
            // renderer's lazy PreLoadTexture rebuild from the new data on its
            // next frame -- the one refresh path that works for all instances.
            foreach (var arr in oldArrays)
            {
                // composite-keyed cache: drop every (image, tlut) entry that shares
                // this image array so each palette variant rebuilds on next frame.
                var staleKeys = new List<(byte[] img, byte[] tlut)>();
                foreach (var k in imageBufferTextureIndex.Keys)
                    if (ReferenceEquals(k.img, arr)) staleKeys.Add(k);
                foreach (var k in staleKeys)
                    imageBufferTextureIndex.Remove(k);
                _mergedGlIndexes.Remove(arr);
            }

            texInfo.RgbaData = bgraData; // Also cache for thumbnails
        }
    }
}
