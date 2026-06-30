using System.Text.Json;
using HSDRaw;
using HSDRaw.Common;
using HSDRaw.GX;
using HSDRaw.Tools;

namespace MexCLI.Commands
{
    // Convert a costume .dat TO or FROM the "Animelee" inverted-hull outline.
    //
    // The outline (mechanism proven in DetectOutlineCommand) is a near-complete
    // duplicate of each body mesh, living in SEPARATE front-culled DObjs, pushed
    // OUT along vertex normals a few percent, painted with a black material.
    // Rendering the back-faces of that pushed-out hull draws the black contour.
    //
    //   mexcli convert-outline --mode generate --in <a.dat> --out <b.dat> [--offset 1.2]
    //   mexcli convert-outline --mode remove   --in <a.dat> --out <b.dat>
    //
    // generate : append a fresh front-culled, normal-offset, black duplicate of
    //            every non-culled body DObj. Skinning is preserved for free — the
    //            generated shell reuses the base POBJ's own envelope weights, which
    //            already reference this file's joints, so it deforms with the body.
    // remove   : delete every DObj that is a confirmed culled concentric duplicate
    //            of a non-culled base mesh (leaves vanilla's tiny intrinsic culled
    //            bits, which stay under the size gate, untouched).
    //
    // Output is written to --out; the caller keeps the original (this is a copy).
    public static class ConvertOutlineCommand
    {
        const int MAJOR_MIN = 40;          // distinct verts for a DObj to count as a real body part
        // Outward push as % of model bbox diagonal. 0.6 ≈ the median push of real
        // Animelee skins (266 measured: median 0.64, p25-p75 0.48-0.92); a uniform
        // push much larger than this balloons small parts (the head swells over the
        // face), so keep it near the real-world median.
        const double DEFAULT_OFFSET_PCT = 0.6;

        public static int Execute(string[] args)
        {
            string? mode = GetOpt(args, "--mode");
            string? inPath = GetOpt(args, "--in");
            string? outPath = GetOpt(args, "--out");
            double offsetPct = ParseDouble(GetOpt(args, "--offset"), DEFAULT_OFFSET_PCT);

            if (mode == null || inPath == null || outPath == null)
            {
                Console.Error.WriteLine("Usage: mexcli convert-outline --mode generate|remove --in <a.dat> --out <b.dat> [--offset 1.2]");
                return 1;
            }

            // HSDRaw's vertex decoder prints "To be implemented: ..." to stdout for a
            // few attributes — mute stdout during the work so our JSON line stays clean.
            TextWriter real = Console.Out;
            Console.SetOut(TextWriter.Null);
            object payload;
            try
            {
                var file = new HSDRawFile(File.ReadAllBytes(inPath));
                int changed;
                switch (mode)
                {
                    case "generate":
                        changed = GenerateOutline(file, offsetPct);
                        payload = new { success = true, mode, dobjsAdded = changed };
                        break;
                    case "remove":
                        changed = RemoveOutline(file);
                        payload = new { success = true, mode, dobjsRemoved = changed };
                        break;
                    default:
                        Console.SetOut(real);
                        Console.Error.WriteLine($"unknown mode: {mode} (expected generate or remove)");
                        return 1;
                }
                file.Save(outPath);
            }
            catch (Exception ex)
            {
                Console.SetOut(real);
                real.WriteLine(JsonSerializer.Serialize(new { success = false, error = ex.Message }));
                return 1;
            }
            Console.SetOut(real);
            real.WriteLine(JsonSerializer.Serialize(payload));
            return 0;
        }

        // ---- generate -------------------------------------------------------

        static int GenerateOutline(HSDRawFile file, double offsetPct)
        {
            var dobjs = CollectDObjs(file, out double bbox);
            double offset = bbox * (offsetPct / 100.0);

            var gen = new POBJ_Generator { CullMode = GenCullMode.Front, UseTriangleStrips = true };

            // Build all outline POBJ chains first (the generator pools shared vertex
            // buffers across every part — finalize once with SaveChanges()). Decide
            // PER POBJ, not per DObj: a vanilla body DObj often already holds a small
            // intrinsic culled POBJ, so we outline only the non-culled body POBJs and
            // gather each DObj's results into one shell DObj.
            var work = new List<(HSD_DOBJ baseDobj, HSD_POBJ outlinePobj)>();
            foreach (var dg in dobjs)
            {
                if (dg.Dobj.Pobj == null) continue;

                HSD_POBJ? chainRoot = null, chainTail = null;
                foreach (var p in dg.Dobj.Pobj.List)
                {
                    // Outline every major body mesh. A normal Melee body POBJ is itself
                    // front-culled (e.g. 0xA001) — that is NOT an outline, it is the body,
                    // so we don't skip on cull flags; the backend only runs generate on a
                    // skin that isn't already Animelee.
                    var tris = DecodeOffsetTris(p, offset, out int distinct);
                    if (tris == null || distinct < MAJOR_MIN) continue;   // skip tiny non-body parts

                    var envelopes = p.EnvelopeWeights != null
                        ? new List<HSD_Envelope>(p.EnvelopeWeights)
                        : new List<HSD_Envelope>();

                    HSD_POBJ gp = gen.CreatePOBJsFromTriangleList(tris, AttrNames(p), envelopes);

                    // a rigid single-bound base has no envelopes — keep the same bind joint
                    if (p.EnvelopeWeights == null && p.SingleBoundJOBJ != null)
                        foreach (var q in gp.List)
                            q.SingleBoundJOBJ = p.SingleBoundJOBJ;

                    // Make the base two-sided (0x2000) by clearing both cull bits. The new
                    // shell is front-culled (0xA000), so the pair is now cull-asymmetric —
                    // exactly the authentic Animelee structure (base 0x2000 + outline
                    // 0xA000), which renders the black contour and lets 'remove' undo it.
                    p.Flags &= ~(POBJ_FLAG.CULLFRONT | POBJ_FLAG.CULLBACK);

                    if (chainRoot == null) chainRoot = gp;
                    else chainTail!.Next = gp;
                    chainTail = gp;
                    while (chainTail.Next != null) chainTail = chainTail.Next;
                }

                if (chainRoot != null) work.Add((dg.Dobj, chainRoot));
            }

            gen.SaveChanges();   // fills the pooled attribute buffers + display lists

            int added = 0;
            foreach (var (baseDobj, outlinePobj) in work)
            {
                var od = new HSD_DOBJ { Mobj = MakeBlackMobj(baseDobj.Mobj), Pobj = outlinePobj };
                od.Next = baseDobj.Next;   // splice the shell in right after its base
                baseDobj.Next = od;
                added++;
            }
            return added;
        }

        // decode a POBJ to a flat triangle list and push each vertex out along its
        // normal; reports the distinct-position count (for the body-part size gate)
        static List<GX_Vertex>? DecodeOffsetTris(HSD_POBJ p, double offset, out int distinct)
        {
            distinct = 0;
            GX_DisplayList dl = p.ToDisplayList();
            var tris = new List<GX_Vertex>();
            int off = 0;
            foreach (GX_PrimitiveGroup prim in dl.Primitives)
            {
                List<GX_Vertex> verts = dl.Vertices.GetRange(off, prim.Count);
                off += prim.Count;
                List<GX_Vertex> tl;
                switch (prim.PrimitiveType)
                {
                    case GXPrimitiveType.Triangles: tl = verts; break;
                    case GXPrimitiveType.TriangleStrip: tl = StripToList(verts); break;
                    case GXPrimitiveType.TriangleFan: tl = FanToList(verts); break;
                    case GXPrimitiveType.Quads: tl = QuadToList(verts); break;
                    default: continue;   // lines/points — not body geometry
                }
                tris.AddRange(tl);
            }

            var uniq = new HashSet<(float, float, float)>();
            for (int i = 0; i < tris.Count; i++)
            {
                GX_Vertex v = tris[i];
                uniq.Add((v.POS.X, v.POS.Y, v.POS.Z));
                double nx = v.NRM.X, ny = v.NRM.Y, nz = v.NRM.Z;
                double nl = Math.Sqrt(nx * nx + ny * ny + nz * nz);
                if (nl > 1e-6)
                {
                    v.POS.X += (float)(nx / nl * offset);
                    v.POS.Y += (float)(ny / nl * offset);
                    v.POS.Z += (float)(nz / nl * offset);
                    tris[i] = v;
                }
            }
            distinct = uniq.Count;
            return tris;
        }

        // a flat unlit black material — clone the base material so render/blend state
        // stays valid, then zero diffuse/ambient/specular (the proven "DIF 255→0").
        static HSD_MOBJ MakeBlackMobj(HSD_MOBJ? baseMobj)
        {
            HSD_MOBJ m = baseMobj != null
                ? new HSD_MOBJ { _s = baseMobj._s.DeepClone() }
                : new HSD_MOBJ { RenderFlags = RENDER_MODE.CONSTANT };

            HSD_Material mat = m.Material ?? new HSD_Material();
            if (m.Material == null) m.Material = mat;

            mat.AMB_R = 0; mat.AMB_G = 0; mat.AMB_B = 0; mat.AMB_A = 255;
            mat.DIF_R = 0; mat.DIF_G = 0; mat.DIF_B = 0; mat.DIF_A = 255;
            mat.SPC_R = 0; mat.SPC_G = 0; mat.SPC_B = 0; mat.SPC_A = 255;
            return m;
        }

        // ---- remove ---------------------------------------------------------

        static int RemoveOutline(HSDRawFile file)
        {
            var dobjs = CollectDObjs(file, out double bbox);
            // an outline shell is a DObj whose POBJs are ALL culled; a base mesh keeps
            // at least one non-culled POBJ. Match shells only against real bases.
            var bases = dobjs.FindAll(d => !d.AllCulled && d.Distinct >= MAJOR_MIN);
            double nnTol2 = (0.06 * bbox) * (0.06 * bbox);

            var remove = new List<DGeom>();
            foreach (var dg in dobjs)
            {
                if (!dg.AllCulled) continue;            // only fully-culled DObjs are outline shells
                if (dg.Distinct < MAJOR_MIN) continue;  // leave tiny intrinsic culled bits

                foreach (var b in bases)
                {
                    double cdx = dg.Cx - b.Cx, cdy = dg.Cy - b.Cy, cdz = dg.Cz - b.Cz;
                    if (Math.Sqrt(cdx * cdx + cdy * cdy + cdz * cdz) / bbox > 0.05) continue;
                    double rHi = Math.Max(dg.Radius, b.Radius), rLo = Math.Min(dg.Radius, b.Radius);
                    if (rLo <= 1e-9 || rHi / rLo > 1.25) continue;
                    if (NNFrac(dg, b, nnTol2) >= 0.80) { remove.Add(dg); break; }
                }
            }

            foreach (var dg in remove) UnlinkDObj(dg.Joint, dg.Dobj);
            return remove.Count;
        }

        // fraction of a's distinct positions that have a twin within tol in b
        static double NNFrac(DGeom a, DGeom b, double tol2)
        {
            int stride = Math.Max(1, a.DistinctPos.Count / 300);
            int sampled = 0, within = 0;
            for (int i = 0; i < a.DistinctPos.Count; i += stride)
            {
                GXVector3 p = a.DistinctPos[i];
                double best = double.MaxValue;
                foreach (GXVector3 q in b.DistinctPos)
                {
                    double ex = p.X - q.X, ey = p.Y - q.Y, ez = p.Z - q.Z;
                    double d2 = ex * ex + ey * ey + ez * ez;
                    if (d2 < best) { best = d2; if (best <= tol2) break; }
                }
                sampled++;
                if (best <= tol2) within++;
            }
            return sampled > 0 ? (double)within / sampled : 0;
        }

        static void UnlinkDObj(HSD_JOBJ j, HSD_DOBJ target)
        {
            HSD_DOBJ? head = j.Dobj;
            if (head == null) return;
            if (head._s == target._s) { j.Dobj = target.Next; return; }
            HSD_DOBJ cur = head;
            while (cur.Next != null)
            {
                if (cur.Next._s == target._s) { cur.Next = target.Next; return; }
                cur = cur.Next;
            }
        }

        // ---- shared geometry pass ------------------------------------------

        sealed class DGeom
        {
            public HSD_JOBJ Joint = null!;
            public HSD_DOBJ Dobj = null!;
            public bool AnyCulled;
            public bool AllCulled;   // every POBJ culled — i.e. a pure outline shell
            public readonly List<GXVector3> Raw = new();
            public readonly List<GXVector3> DistinctPos = new();
            public readonly HashSet<long> Quant = new();
            public double Cx, Cy, Cz, Radius;
            public int Distinct => Quant.Count;
        }

        // walk every model root → joint tree → DObj, recording each DObj's vertex
        // cloud and cull state. Two passes: gather raw positions + global bbox, then
        // quantize to distinct positions and compute centroid/radius (bbox-relative).
        static List<DGeom> CollectDObjs(HSDRawFile file, out double bbox)
        {
            var list = new List<DGeom>();
            double minx = 1e30, miny = 1e30, minz = 1e30, maxx = -1e30, maxy = -1e30, maxz = -1e30;

            foreach (HSDRootNode root in file.Roots)
            {
                if (root.Data is not HSD_JOBJ rootJ) continue;
                foreach (HSD_JOBJ j in rootJ.TreeList)
                {
                    HSD_DOBJ? dobj = j.Dobj;
                    if (dobj == null) continue;
                    foreach (HSD_DOBJ d in dobj.List)
                    {
                        var dg = new DGeom { Joint = j, Dobj = d };
                        HSD_POBJ? pobj = d.Pobj;
                        bool sawPobj = false, allCulled = true;
                        if (pobj != null)
                            foreach (HSD_POBJ p in pobj.List)
                            {
                                sawPobj = true;
                                bool culled = p.Flags.HasFlag(POBJ_FLAG.CULLFRONT) || p.Flags.HasFlag(POBJ_FLAG.CULLBACK);
                                if (culled) dg.AnyCulled = true; else allCulled = false;
                                try
                                {
                                    foreach (GX_Vertex v in p.ToDisplayList().Vertices)
                                    {
                                        GXVector3 P = v.POS;
                                        dg.Raw.Add(P);
                                        if (P.X < minx) minx = P.X;
                                        if (P.Y < miny) miny = P.Y;
                                        if (P.Z < minz) minz = P.Z;
                                        if (P.X > maxx) maxx = P.X;
                                        if (P.Y > maxy) maxy = P.Y;
                                        if (P.Z > maxz) maxz = P.Z;
                                    }
                                }
                                catch { /* undecodable POBJ — skip */ }
                            }
                        dg.AllCulled = sawPobj && allCulled;
                        list.Add(dg);
                    }
                }
            }

            double dx = maxx - minx, dy = maxy - miny, dz = maxz - minz;
            bbox = maxx > -1e29 ? Math.Sqrt(dx * dx + dy * dy + dz * dz) : 1.0;
            if (bbox <= 1e-9) bbox = 1.0;
            double cell = bbox * 1e-4;

            foreach (DGeom dg in list)
            {
                foreach (GXVector3 P in dg.Raw)
                    if (dg.Quant.Add(QuantKey(P, cell)))
                        dg.DistinctPos.Add(P);

                int n = dg.DistinctPos.Count;
                if (n > 0)
                {
                    double sx = 0, sy = 0, sz = 0;
                    foreach (GXVector3 P in dg.DistinctPos) { sx += P.X; sy += P.Y; sz += P.Z; }
                    dg.Cx = sx / n; dg.Cy = sy / n; dg.Cz = sz / n;
                    double sr = 0;
                    foreach (GXVector3 P in dg.DistinctPos)
                    {
                        double rx = P.X - dg.Cx, ry = P.Y - dg.Cy, rz = P.Z - dg.Cz;
                        sr += Math.Sqrt(rx * rx + ry * ry + rz * rz);
                    }
                    dg.Radius = sr / n;
                }
            }
            return list;
        }

        static long QuantKey(GXVector3 p, double cell)
        {
            long qx = ((long)Math.Round(p.X / cell) + 0x100000) & 0x1FFFFF;
            long qy = ((long)Math.Round(p.Y / cell) + 0x100000) & 0x1FFFFF;
            long qz = ((long)Math.Round(p.Z / cell) + 0x100000) & 0x1FFFFF;
            return (qx << 42) | (qy << 21) | qz;
        }

        // ---- helpers --------------------------------------------------------

        // base POBJ's attribute names (without the trailing NULL terminator)
        static GXAttribName[] AttrNames(HSD_POBJ p)
        {
            var names = new List<GXAttribName>();
            foreach (GX_Attribute a in p.ToGXAttributes())
            {
                if (a.AttributeName == GXAttribName.GX_VA_NULL) break;
                names.Add(a.AttributeName);
            }
            return names.ToArray();
        }

        static List<GX_Vertex> StripToList(List<GX_Vertex> s)
        {
            var o = new List<GX_Vertex>();
            for (int i = 2; i < s.Count; i++)
            {
                if ((i & 1) == 0) { o.Add(s[i - 2]); o.Add(s[i - 1]); o.Add(s[i]); }
                else { o.Add(s[i - 1]); o.Add(s[i - 2]); o.Add(s[i]); }
            }
            return o;
        }

        static List<GX_Vertex> FanToList(List<GX_Vertex> f)
        {
            var o = new List<GX_Vertex>();
            for (int i = 2; i < f.Count; i++) { o.Add(f[0]); o.Add(f[i - 1]); o.Add(f[i]); }
            return o;
        }

        static List<GX_Vertex> QuadToList(List<GX_Vertex> q)
        {
            var o = new List<GX_Vertex>();
            for (int i = 0; i + 3 < q.Count; i += 4)
            {
                o.Add(q[i]); o.Add(q[i + 1]); o.Add(q[i + 2]);
                o.Add(q[i]); o.Add(q[i + 2]); o.Add(q[i + 3]);
            }
            return o;
        }

        static string? GetOpt(string[] args, string name)
        {
            int i = Array.IndexOf(args, name);
            return (i >= 0 && i + 1 < args.Length) ? args[i + 1] : null;
        }

        static double ParseDouble(string? s, double fallback)
            => double.TryParse(s, System.Globalization.NumberStyles.Float,
                               System.Globalization.CultureInfo.InvariantCulture, out double v) ? v : fallback;
    }
}
