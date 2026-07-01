using System;
using System.Collections.Generic;
using System.Linq;
using HSDRaw;
using HSDRaw.Common;
using HSDRaw.Common.Animation;
using HSDRawViewer.Extensions;
using OpenTK.Mathematics;

namespace HSDRawViewer.Rendering.Models
{
    /// <summary>
    /// Assembles a fully-featured costume onto a <see cref="RenderJObj"/> so the
    /// live viewers (skin/texture lab <c>StreamingServer</c>, in-app animation
    /// viewer <c>EmbeddedServer</c>) match what the batch CSP renderer already
    /// draws: m-ex costume accessories (caps / Navi / capes / nurse hat / Falco
    /// hair) and separate accessory/hat roots are rendered and, for the m-ex
    /// ones, tracked to their attach bone every frame; eye/blink matanim is wired
    /// in. This is the single source of truth the live servers share; the batch
    /// CSP path (Program.cs <c>RunCSPGeneration</c>) still keeps its own inline
    /// copy of this logic for now and is migrated onto this module in a later pass.
    ///
    /// IMPORTANT: splicing is done on the in-memory <see cref="LiveJObj"/> RENDER
    /// tree, NEVER on the <see cref="HSD_JOBJ"/> descriptors. The skin lab lets the
    /// user edit textures and export the modified DAT (<c>StreamingServer</c>'s
    /// <c>exportDat</c> saves the raw file), so the on-disk structure the game
    /// loads must stay untouched — otherwise the accessories would be duplicated
    /// into the body joint chain and shift its joint/DObj indices. The accessory
    /// TOBJs are the raw file's own accessors, so texture edits to accessories
    /// still land in the exported DAT even though the joint tree is only linked in
    /// memory.
    ///
    /// The splice/follow logic here is lifted from Program.cs
    /// <c>RunCSPGeneration</c> (accessory gather 826-899, attach-bone follow
    /// 1791-1855); see <c>csp-accessory-attach.md</c> for the
    /// coincident/at-origin/offset discrimination.
    /// </summary>
    public class MexCostumeScene
    {
        public delegate void LogFn(string msg);

        // m-ex Accessories[] : each RootJoint follows a body AttachBone.
        private readonly List<(HSD_JOBJ desc, int attachBone)> _attachAccessories = new();

        // Accessories shipped as their own JOBJ root (e.g. Jigglypuff alt-costume
        // *Hat_TopN_joint). Rendered, but head-follow needs a head bone the live
        // servers don't carry, so they sit at their (rest-correct) bind pose.
        private readonly List<HSD_JOBJ> _separateRoots = new();

        // Eye/blink material-animation banks (a separate *_matanim_joint root).
        private readonly List<HSD_MatAnimJoint> _matAnimRoots = new();

        // Live tree refs resolved in Attach and reused by every ApplyFollow.
        private readonly List<(LiveJObj acc, int attachBone)> _liveFollow = new();

        private readonly LogFn _log;

        public bool HasAccessories => _attachAccessories.Count > 0 || _separateRoots.Count > 0;

        private MexCostumeScene(LogFn log) { _log = log ?? (_ => { }); }

        /// <summary>
        /// Scan a loaded costume file for accessories + matanim, relative to the
        /// character body root the host passes to <c>new RenderJObj</c>. Read-only;
        /// mutates nothing.
        /// </summary>
        public static MexCostumeScene Build(HSDRawFile rawFile, HSD_JOBJ characterRoot, LogFn log = null)
        {
            var s = new MexCostumeScene(log);
            if (rawFile == null || characterRoot == null)
                return s;

            // (1) Separate JOBJ roots = an accessory shipped as its own root
            //     (anything that is neither the body nor a matanim bank).
            foreach (var r in rawFile.Roots)
            {
                if (r.Data is HSD_JOBJ rj
                    && !ReferenceEquals(r.Data, characterRoot)
                    && !(r.Name?.Contains("matanim") ?? false))
                {
                    s._separateRoots.Add(rj);
                }
            }

            // (2) m-ex costume accessories: caps / Navi / capes / nurse hat / Falco
            //     hair live inside the "mexCostume" root's Accessories[], each a
            //     standalone RootJoint authored relative to a body AttachBone.
            var mexRoot = rawFile.Roots.FirstOrDefault(r => r.Name == "mexCostume");
            if (mexRoot?.Data is HSDRaw.MEX.MEX_CostumeSymbol mexSym && mexSym.Accessories != null)
            {
                var accArr = mexSym.Accessories.Array;
                int accN = Math.Min(mexSym.AccessoryCount, accArr.Length);
                for (int i = 0; i < accN; i++)
                {
                    var rjt = accArr[i]?.RootJoint;
                    if (rjt == null)
                        continue;
                    s._attachAccessories.Add((rjt, accArr[i].AttachBone));
                }
            }

            // (3) Eye/blink matanim banks.
            foreach (var r in rawFile.Roots)
                if ((r.Name?.Contains("matanim") ?? false) && r.Data is HSD_MatAnimJoint mat)
                    s._matAnimRoots.Add(mat);

            s._log($"MexCostumeScene: {s._attachAccessories.Count} attach accessory(ies), " +
                   $"{s._separateRoots.Count} separate root(s), {s._matAnimRoots.Count} matanim root(s)");
            return s;
        }

        /// <summary>
        /// After <c>new RenderJObj(characterRoot)</c>: wire eye/blink matanim and
        /// link each accessory's LiveJObj subtree into the render tree (appended
        /// AFTER the whole body so existing joint/DObj indices are preserved — the
        /// low-poly hide list and part-visibility use those). Invalidates so the
        /// renderer rebuilds its DObj cache to include the new geometry.
        /// </summary>
        public void Attach(RenderJObj render)
        {
            if (render == null)
                return;

            // Eyes / blink swap frames. The base texture at frame 0 == the neutral
            // open eye, so this is safe for the live viewers' default frame too.
            if (_matAnimRoots.Count > 0)
                render.SetMatAnims(_matAnimRoots);

            var root = render.RootJObj;
            if (root == null || !HasAccessories)
                return;

            _liveFollow.Clear();

            foreach (var (desc, attachBone) in _attachAccessories)
            {
                var live = LinkAccessory(root, desc);
                if (live != null)
                    _liveFollow.Add((live, attachBone));
            }
            foreach (var desc in _separateRoots)
                LinkAccessory(root, desc); // rendered; no attach-bone follow

            // Force the DObj cache to rebuild (with the accessories) on next render.
            render.Invalidate();
            _log($"MexCostumeScene: linked {_liveFollow.Count} follow accessory(ies) + " +
                 $"{_separateRoots.Count} separate root(s) into the render tree");
        }

        /// <summary>
        /// Build a LiveJObj for an accessory descriptor and link it as the last
        /// child-sibling of <paramref name="root"/> WITHOUT touching any
        /// <see cref="HSD_JOBJ"/> descriptor (unlike <c>LiveJObj.AddChild</c>,
        /// which rewrites <c>Desc.Child/Next</c>). Indices continue past the body
        /// so accessory nodes never collide with a body bone index in
        /// <c>GetJObjAtIndex</c>.
        /// </summary>
        private LiveJObj LinkAccessory(LiveJObj root, HSD_JOBJ desc)
        {
            try
            {
                if (desc == null)
                    return null;

                int idx = root.JointCount; // next free render index
                var live = new LiveJObj(desc, root, ref idx);
                live.Sibling = null; // drop any spurious desc.Next sibling subtree

                if (root.Child == null)
                {
                    root.Child = live;
                }
                else
                {
                    var tail = root.Child;
                    while (tail.Sibling != null)
                        tail = tail.Sibling;
                    tail.Sibling = live;
                }
                return live;
            }
            catch (Exception ex)
            {
                _log($"MexCostumeScene: failed to link accessory: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Re-pin each attach-bone accessory to its bone's POSED world. Call after
        /// every <c>RequestAnimationUpdate</c>, before grabbing the frame, so the
        /// accessory tracks the head/hand throughout an animation. Idempotent: it
        /// reads only FIXED bind data (<c>LiveJObj.InvertedTransform</c>, set once
        /// at construction) times the CURRENT posed bone world, and bakes a fresh
        /// local SRT each call — so it neither drifts nor accumulates across frames.
        /// (Program.cs:1791-1855.)
        /// </summary>
        public void ApplyFollow(RenderJObj render, Camera camera)
        {
            var root = render?.RootJObj;
            if (root == null || _liveFollow.Count == 0)
                return;

            try
            {
                var rootInv = root.WorldTransform.Inverted();
                int applied = 0;
                foreach (var (acc, attachBone) in _liveFollow)
                {
                    var bone = root.GetJObjAtIndex(attachBone);
                    if (acc == null || bone == null)
                        continue;

                    // bind -> posed delta of the attach bone this frame
                    var boneDelta = bone.InvertedTransform * bone.WorldTransform;
                    var accBind = acc.InvertedTransform.Inverted();
                    var boneBindW = bone.InvertedTransform.Inverted();
                    var accBindT = accBind.ExtractTranslation();

                    // Bone-RELATIVE authoring (mesh sits "on" the bone) shows up two
                    // ways: accBind coincident with the bone's bind (nurse hat), or
                    // accBind at the model origin (Falco hair). Both want the bone's
                    // full POSED world. A genuine model-space OFFSET accessory
                    // (Link's cap) keeps the bind->posed delta so its offset holds.
                    bool coincident = (accBindT - boneBindW.ExtractTranslation()).Length < 0.5f;
                    bool atOrigin = accBindT.Length < 0.5f;
                    bool boneRelative = coincident || atOrigin;

                    Matrix4 local = boneRelative
                        ? bone.WorldTransform * rootInv          // (B) inherit bone posed world
                        : (accBind * boneDelta) * rootInv;       // (A) model-space bind->posed delta

                    acc.Scale = local.ExtractScale();
                    var rot = local.ExtractRotationEuler();
                    acc.Rotation = new Vector4(rot.X, rot.Y, rot.Z, 0);
                    acc.Translation = local.ExtractTranslation();
                    applied++;
                }

                if (applied > 0)
                    root.RecalculateTransforms(camera, true);
            }
            catch (Exception ex)
            {
                _log($"MexCostumeScene: accessory follow failed: {ex.Message}");
            }
        }
    }
}
