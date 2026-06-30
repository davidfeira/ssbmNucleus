using System.IO.Compression;
using System.Text.Json;
using HSDRaw;
using HSDRaw.Common;
using HSDRaw.GX;

namespace MexCLI.Commands
{
    // Detect the "Animelee" inverted-hull outline effect by GEOMETRY (decoded
    // vertices), NOT by counting cull flags (that approach was refuted: normal
    // Melee meshes cull too). The effect: for each base mesh, a 2nd POBJ is
    // appended to the SAME DObj that duplicates the mesh's vertex cloud — either
    // byte-identical with a flipped cull bit, or pushed OUT along vertex normals
    // — rendering a dark back-face hull that reads as the black contour.
    //
    // A "shell pair" = two POBJs in one DObj with EQUAL decoded vertex count whose
    // clouds are (a) identical positions + cull asymmetry, or (b) a thin, mostly-
    // along-normal outward offset. shellCoverage = dobjsWithShell / dobjs is the
    // discriminator: true Animelee outlines nearly every mesh.
    //
    //   mexcli detect-outline <path.dat|path.zip> [--debug]
    //   mexcli detect-outline --batch <manifest.json>   (one process, many costumes)
    public static class DetectOutlineCommand
    {
        const int MIN_VERTS = 6;

        sealed class PobjGeom
        {
            public GXVector3[] Pos = Array.Empty<GXVector3>();
            public GXVector3[] Nrm = Array.Empty<GXVector3>();
            public POBJ_FLAG Flags;
            public bool Culled => Flags.HasFlag(POBJ_FLAG.CULLFRONT) || Flags.HasFlag(POBJ_FLAG.CULLBACK);

            // distinct quantized positions (built once), centroid + mean radius
            public HashSet<long> Quant = new();
            public List<GXVector3> DistinctPos = new();
            public List<GXVector3> DistinctNrm = new();
            public double Cx, Cy, Cz, Radius;
            public int MatDif = -1, MatAmb = -1;   // material diffuse/ambient brightness (max rgb, 0-255)
            public int Distinct => Quant.Count;
        }

        // For a confirmed asym pair (outline=culled, base=non-culled), measure how
        // cleanly the outline is the base displaced ALONG its surface normals. A true
        // inverted hull: every outline vert ≈ nearest base vert + t·normal → the
        // displacement is parallel to the normal (perpRatio→0) and outward (push>0).
        // Vanilla intrinsic duplicates (LowPoly/two-sided/shell) lack this clean
        // per-vertex normal relationship → higher perpRatio.
        static (double perpRatio, double pushPct, int n) NormalOffsetQuality(
            PobjGeom outline, PobjGeom baseG, double bbox)
        {
            int stride = Math.Max(1, outline.DistinctPos.Count / 200);
            double sumProj = 0, sumPerp = 0, sumAbs = 0; int n = 0;
            for (int i = 0; i < outline.DistinctPos.Count; i += stride)
            {
                GXVector3 p = outline.DistinctPos[i];
                double best = double.MaxValue; int bj = -1;
                for (int j = 0; j < baseG.DistinctPos.Count; j++)
                {
                    GXVector3 q = baseG.DistinctPos[j];
                    double ex = p.X - q.X, ey = p.Y - q.Y, ez = p.Z - q.Z;
                    double d2 = ex * ex + ey * ey + ez * ez;
                    if (d2 < best) { best = d2; bj = j; }
                }
                if (bj < 0) continue;
                GXVector3 b = baseG.DistinctPos[bj], nb = baseG.DistinctNrm[bj];
                double dx = p.X - b.X, dy = p.Y - b.Y, dz = p.Z - b.Z;
                double dmag = Math.Sqrt(best);
                double nl = Math.Sqrt(nb.X * nb.X + nb.Y * nb.Y + nb.Z * nb.Z);
                double proj = nl > 1e-6 ? (dx * nb.X + dy * nb.Y + dz * nb.Z) / nl : 0;
                double perp2 = dmag * dmag - proj * proj;
                sumProj += proj;
                sumPerp += perp2 > 0 ? Math.Sqrt(perp2) : 0;
                sumAbs += dmag;
                n++;
            }
            double perpRatio = sumAbs > 1e-9 ? sumPerp / sumAbs : 1;
            double pushPct = n > 0 ? 100.0 * (sumProj / n) / bbox : 0;
            return (perpRatio, pushPct, n);
        }

        static long QuantKey(GXVector3 p, double cell)
        {
            // pack 3 × 21-bit quantized coords (offset to stay non-negative)
            long qx = (long)Math.Round(p.X / cell) + 0x100000;
            long qy = (long)Math.Round(p.Y / cell) + 0x100000;
            long qz = (long)Math.Round(p.Z / cell) + 0x100000;
            qx &= 0x1FFFFF; qy &= 0x1FFFFF; qz &= 0x1FFFFF;
            return (qx << 42) | (qy << 21) | qz;
        }

        public sealed class ModelResult
        {
            public bool success { get; set; } = true;
            public string? error { get; set; }
            public string? path { get; set; }
            public int roots { get; set; }
            public int dobjs { get; set; }
            public int pobjs { get; set; }
            public int dupEqualCount { get; set; }   // POBJ pairs in same DObj w/ equal vertex count
            public int shellPairs { get; set; }      // of those, geometrically an outline shell
            public int shellIdentical { get; set; }  // identical positions + cull asymmetry
            public int shellPushed { get; set; }     // thin outward along-normal offset
            public int dobjsWithShell { get; set; }
            public int cullFront { get; set; }
            public int cullBack { get; set; }
            public int envelope { get; set; }
            public double shellCoverage { get; set; }      // dobjsWithShell / dobjs
            public double meanShellOffsetPct { get; set; } // avg outward push, % of bbox diagonal
            public int maxDupDistinct { get; set; }         // distinct-vtx count of largest duplicated part
            public int dupCullAsym { get; set; }            // confirmed dup pairs where exactly one is culled
            public int asymDupMax { get; set; }             // largest cull-asym duplicated part (distinct verts)
            public int asymDupSum { get; set; }             // total cull-asym duplicated distinct verts
            public int baseDistinct { get; set; }           // total distinct verts over non-culled major POBJs
            public double asymPerpRatio { get; set; }       // 0=clean normal offset (inverted hull), 1=random
            public double asymPushPct { get; set; }         // mean outward push of asym shells, % bbox diag
            public string geomHash { get; set; } = "";      // fingerprint of NON-culled body geometry (recolors match)
            public double bboxDiag { get; set; }
            public bool isAnimelee { get; set; }
            public List<object>? samples { get; set; }     // debug only
            public List<object>? pobjDump { get; set; }     // --dump only
        }

        public static int Execute(string[] args)
        {
            bool debug = args.Contains("--debug");
            bool dump = args.Contains("--dump");

            int bi = Array.IndexOf(args, "--batch");
            if (bi >= 0)
            {
                if (bi + 1 >= args.Length)
                {
                    Console.Error.WriteLine("Usage: mexcli detect-outline --batch <manifest.json>");
                    return 1;
                }
                return RunBatch(args[bi + 1]);
            }

            if (args.Length < 2)
            {
                Console.Error.WriteLine("Usage: mexcli detect-outline <path.dat|path.zip> [--debug] [--dump]");
                return 1;
            }

            // HSDRaw's vertex decoder writes "To be implemented: ..." to stdout for a
            // few unhandled attributes — mute stdout during analysis so JSON is clean.
            TextWriter real = Console.Out;
            ModelResult r;
            Console.SetOut(TextWriter.Null);
            try { r = AnalyzePath(args[1], debug, dump); }
            finally { Console.SetOut(real); }
            real.WriteLine(JsonSerializer.Serialize(r, new JsonSerializerOptions { WriteIndented = true }));
            return r.success ? 0 : 1;
        }

        static int RunBatch(string manifestPath)
        {
            if (!File.Exists(manifestPath))
            {
                Console.Error.WriteLine($"manifest not found: {manifestPath}");
                return 1;
            }

            using FileStream fs = File.OpenRead(manifestPath);
            using JsonDocument doc = JsonDocument.Parse(fs);
            JsonElement items = doc.RootElement.GetProperty("items");

            // mute stdout during analysis (see note in Execute)
            TextWriter real = Console.Out;
            Console.SetOut(TextWriter.Null);

            var results = new List<object>();
            foreach (JsonElement it in items.EnumerateArray())
            {
                string key = it.TryGetProperty("key", out var k) ? (k.GetString() ?? "") : "";
                string path = it.TryGetProperty("path", out var p) ? (p.GetString() ?? "") : "";
                ModelResult r;
                try { r = AnalyzePath(path, false); }
                catch (Exception ex) { r = new ModelResult { success = false, error = ex.Message, path = path }; }

                results.Add(new
                {
                    key,
                    r.success,
                    r.error,
                    r.dobjs,
                    r.pobjs,
                    r.shellPairs,
                    r.shellIdentical,
                    r.shellPushed,
                    r.maxDupDistinct,
                    r.dupCullAsym,
                    r.asymDupMax,
                    r.asymDupSum,
                    r.baseDistinct,
                    r.asymPerpRatio,
                    r.asymPushPct,
                    r.geomHash,
                    r.dobjsWithShell,
                    r.cullFront,
                    r.cullBack,
                    r.isAnimelee,
                });
            }
            Console.SetOut(real);
            real.WriteLine(JsonSerializer.Serialize(new { success = true, count = results.Count, results }));
            return 0;
        }

        public static ModelResult AnalyzePath(string path, bool debug, bool dump = false)
        {
            try
            {
                byte[] datBytes = ReadDatBytes(path);
                ModelResult res = Analyze(new HSDRawFile(datBytes), debug, dump);
                res.path = path;
                return res;
            }
            catch (Exception ex)
            {
                return new ModelResult { success = false, error = ex.Message, path = path };
            }
        }

        // Accept a raw .dat/.usd, or a costume .zip (pick the primary Pl*.dat).
        static byte[] ReadDatBytes(string path)
        {
            if (path.EndsWith(".zip", StringComparison.OrdinalIgnoreCase))
            {
                using ZipArchive za = ZipFile.OpenRead(path);
                ZipArchiveEntry? pick = null;
                foreach (ZipArchiveEntry e in za.Entries)
                {
                    string name = Path.GetFileName(e.FullName);
                    bool isDat = name.EndsWith(".dat", StringComparison.OrdinalIgnoreCase)
                              || name.EndsWith(".usd", StringComparison.OrdinalIgnoreCase);
                    if (!isDat) continue;
                    if (name.StartsWith("Pl", StringComparison.OrdinalIgnoreCase)) { pick = e; break; }
                    pick ??= e;
                }
                if (pick == null) throw new Exception("no .dat/.usd in zip");
                using Stream s = pick.Open();
                using var ms = new MemoryStream();
                s.CopyTo(ms);
                return ms.ToArray();
            }
            return File.ReadAllBytes(path);
        }

        static ModelResult Analyze(HSDRawFile file, bool debug, bool dump = false)
        {
            var res = new ModelResult();
            double minx = 1e30, miny = 1e30, minz = 1e30;
            double maxx = -1e30, maxy = -1e30, maxz = -1e30;
            var groups = new List<List<PobjGeom>>();

            foreach (HSDRootNode root in file.Roots)
            {
                if (root.Data is not HSD_JOBJ rootJ) continue;   // skips matanim/shapeanim/non-model roots
                res.roots++;

                foreach (HSD_JOBJ j in rootJ.TreeList)
                {
                    HSD_DOBJ? dobj = j.Dobj;
                    if (dobj == null) continue;

                    foreach (HSD_DOBJ d in dobj.List)
                    {
                        res.dobjs++;
                        var group = new List<PobjGeom>();

                        // material brightness for this DObj (all its POBJs share it)
                        int matDif = -1, matAmb = -1;
                        var mat = d.Mobj?.Material;
                        if (mat != null)
                        {
                            matDif = Math.Max(mat.DIF_R, Math.Max(mat.DIF_G, mat.DIF_B));
                            matAmb = Math.Max(mat.AMB_R, Math.Max(mat.AMB_G, mat.AMB_B));
                        }

                        HSD_POBJ? pobj = d.Pobj;
                        if (pobj != null)
                        {
                            foreach (HSD_POBJ p in pobj.List)
                            {
                                res.pobjs++;
                                if (p.Flags.HasFlag(POBJ_FLAG.CULLFRONT)) res.cullFront++;
                                if (p.Flags.HasFlag(POBJ_FLAG.CULLBACK)) res.cullBack++;
                                if (p.Flags.HasFlag(POBJ_FLAG.ENVELOPE)) res.envelope++;

                                try
                                {
                                    var verts = p.ToDisplayList().Vertices;
                                    var pg = new PobjGeom
                                    {
                                        Flags = p.Flags,
                                        MatDif = matDif,
                                        MatAmb = matAmb,
                                        Pos = new GXVector3[verts.Count],
                                        Nrm = new GXVector3[verts.Count],
                                    };
                                    double sx = 0, sy = 0, sz = 0;
                                    for (int k = 0; k < verts.Count; k++)
                                    {
                                        GXVector3 P = verts[k].POS;
                                        pg.Pos[k] = P;
                                        pg.Nrm[k] = verts[k].NRM;
                                        sx += P.X; sy += P.Y; sz += P.Z;
                                        if (P.X < minx) minx = P.X;
                                        if (P.Y < miny) miny = P.Y;
                                        if (P.Z < minz) minz = P.Z;
                                        if (P.X > maxx) maxx = P.X;
                                        if (P.Y > maxy) maxy = P.Y;
                                        if (P.Z > maxz) maxz = P.Z;
                                    }
                                    if (verts.Count > 0)
                                    {
                                        pg.Cx = sx / verts.Count; pg.Cy = sy / verts.Count; pg.Cz = sz / verts.Count;
                                        double sr = 0;
                                        foreach (var P in pg.Pos)
                                        {
                                            double rx = P.X - pg.Cx, ry = P.Y - pg.Cy, rz = P.Z - pg.Cz;
                                            sr += Math.Sqrt(rx * rx + ry * ry + rz * rz);
                                        }
                                        pg.Radius = sr / verts.Count;
                                    }
                                    group.Add(pg);
                                }
                                catch { /* undecodable POBJ — skip */ }
                            }
                        }
                        groups.Add(group);
                    }
                }
            }

            if (maxx > -1e29)
            {
                double dx = maxx - minx, dy = maxy - miny, dz = maxz - minz;
                res.bboxDiag = Math.Sqrt(dx * dx + dy * dy + dz * dz);
            }
            double bbox = res.bboxDiag <= 1e-9 ? 1.0 : res.bboxDiag;
            double cell = bbox * 1e-4;

            // build distinct quantized position sets (+ keep distinct coords/normals for NN)
            foreach (var g in groups)
                foreach (var pg in g)
                    for (int k = 0; k < pg.Pos.Length; k++)
                        if (pg.Quant.Add(QuantKey(pg.Pos[k], cell)))
                        {
                            pg.DistinctPos.Add(pg.Pos[k]);
                            pg.DistinctNrm.Add(pg.Nrm[k]);
                        }

            if (dump)
            {
                var dlist = new List<object>();
                for (int di = 0; di < groups.Count; di++)
                    for (int pi = 0; pi < groups[di].Count; pi++)
                    {
                        var pg = groups[di][pi];
                        dlist.Add(new
                        {
                            dobj = di,
                            pi,
                            vtx = pg.Pos.Length,
                            distinct = pg.Distinct,
                            cx = Math.Round(pg.Cx / bbox, 4),
                            cy = Math.Round(pg.Cy / bbox, 4),
                            cz = Math.Round(pg.Cz / bbox, 4),
                            r = Math.Round(pg.Radius / bbox, 4),
                            flags = "0x" + ((ushort)pg.Flags).ToString("X"),
                            culled = pg.Culled,
                        });
                    }
                res.pobjDump = dlist;
            }

            var samples = new List<object>();
            double offSum = 0; int offN = 0;
            double perpW = 0, pushW = 0; int qW = 0;   // vertex-weighted normal-offset quality

            // The outline is a near-complete duplicate of the base surface, living
            // in SEPARATE DObjs (usually flagged cull), pushed out a few %. So search
            // MODEL-WIDE for a "major" POBJ that is a concentric near-copy of another
            // major POBJ. Pre-filter by centroid/radius, then CONFIRM by nearest-
            // neighbour: every vertex of the smaller copy must have a twin a few %
            // away in the larger — this is what separates a real pushed-out surface
            // copy from two distinct meshes that merely share a centroid.
            const int MAJOR_MIN = 40;     // distinct verts to count as a real part
            double nnTol = 0.06 * bbox;   // a twin within 6% of bbox diagonal
            double nnTol2 = nnTol * nnTol;

            var majors = new List<(PobjGeom pg, int grp)>();
            for (int gi = 0; gi < groups.Count; gi++)
                foreach (var pg in groups[gi])
                    if (pg.Distinct >= MAJOR_MIN)
                    {
                        majors.Add((pg, gi));
                        if (!pg.Culled) res.baseDistinct += pg.Distinct;
                    }

            // body geometry fingerprint: FNV-1a over the distinct quantized positions
            // of all NON-culled major POBJs. Identical geometry (vanilla + its recolors,
            // which only swap textures) → identical hash; custom models → different.
            var bodyKeys = new List<long>();
            foreach (var (pg, _) in majors)
                if (!pg.Culled) bodyKeys.AddRange(pg.Quant);
            bodyKeys.Sort();
            ulong fnv = 14695981039346656037UL;
            long prevK = long.MinValue;
            foreach (long k in bodyKeys)
            {
                if (k == prevK) continue;   // distinct positions only
                prevK = k;
                fnv = (fnv ^ (ulong)k) * 1099511628211UL;
            }
            res.geomHash = fnv.ToString("x16");

            var shellGroups = new HashSet<int>();
            for (int a = 0; a < majors.Count; a++)
            {
                for (int b = a + 1; b < majors.Count; b++)
                {
                    PobjGeom A = majors[a].pg, B = majors[b].pg;

                    double cdx = A.Cx - B.Cx, cdy = A.Cy - B.Cy, cdz = A.Cz - B.Cz;
                    double centDist = Math.Sqrt(cdx * cdx + cdy * cdy + cdz * cdz) / bbox;
                    if (centDist > 0.05) continue;
                    double rHi = Math.Max(A.Radius, B.Radius), rLo = Math.Min(A.Radius, B.Radius);
                    double radRatio = rLo > 1e-9 ? rHi / rLo : 99;
                    if (radRatio > 1.25) continue;
                    int dlo = Math.Min(A.Distinct, B.Distinct), dhi = Math.Max(A.Distinct, B.Distinct);
                    if ((double)dlo / dhi < 0.5) continue;

                    // nearest-neighbour confirmation (sample the smaller copy)
                    var (S, L) = A.Distinct <= B.Distinct ? (A, B) : (B, A);
                    int stride = Math.Max(1, S.DistinctPos.Count / 300);
                    int sampled = 0, within = 0;
                    for (int i = 0; i < S.DistinctPos.Count; i += stride)
                    {
                        GXVector3 p = S.DistinctPos[i];
                        double best = double.MaxValue;
                        foreach (GXVector3 q in L.DistinctPos)
                        {
                            double ex = p.X - q.X, ey = p.Y - q.Y, ez = p.Z - q.Z;
                            double d2 = ex * ex + ey * ey + ez * ez;
                            if (d2 < best) { best = d2; if (best <= nnTol2) break; }
                        }
                        sampled++;
                        if (best <= nnTol2) within++;
                    }
                    double frac = sampled > 0 ? (double)within / sampled : 0;
                    if (frac < 0.80) continue;

                    // confirmed duplicate surface = outline shell
                    res.shellPairs++;
                    if (radRatio >= 1.03) res.shellPushed++; else res.shellIdentical++;
                    double perpRatio = -1, pushPct = 0;
                    if (A.Culled != B.Culled)
                    {
                        res.dupCullAsym++;
                        res.asymDupSum += dlo;
                        if (dlo > res.asymDupMax) res.asymDupMax = dlo;
                        // normal-offset cleanliness: is the culled copy the base pushed
                        // along its normals? (clean inverted hull) or a messy duplicate?
                        PobjGeom outline = A.Culled ? A : B, baseG = A.Culled ? B : A;
                        var (pr, pp, qn) = NormalOffsetQuality(outline, baseG, bbox);
                        if (qn > 0) { perpRatio = pr; pushPct = pp; perpW += pr * qn; pushW += pp * qn; qW += qn; }
                    }
                    if (dlo > res.maxDupDistinct) res.maxDupDistinct = dlo;
                    shellGroups.Add(majors[a].grp);
                    shellGroups.Add(majors[b].grp);
                    offSum += (radRatio - 1.0); offN++;

                    if (debug && samples.Count < 24)
                    {
                        PobjGeom outl = A.Culled ? A : B, bas = A.Culled ? B : A;
                        samples.Add(new
                        {
                            distinctS = S.Distinct,
                            distinctL = L.Distinct,
                            radRatio = Math.Round(radRatio, 3),
                            nnFrac = Math.Round(frac, 3),
                            cullAsym = A.Culled != B.Culled,
                            perpRatio = Math.Round(perpRatio, 3),
                            matDifBase = bas.MatDif,
                            matDifOutline = outl.MatDif,
                            matAmbBase = bas.MatAmb,
                            matAmbOutline = outl.MatAmb,
                            flagsS = "0x" + ((ushort)S.Flags).ToString("X"),
                            flagsL = "0x" + ((ushort)L.Flags).ToString("X"),
                        });
                    }
                }
            }

            res.dobjsWithShell = shellGroups.Count;
            res.shellCoverage = res.dobjs > 0 ? (double)res.dobjsWithShell / res.dobjs : 0;
            res.meanShellOffsetPct = offN > 0 ? 100.0 * offSum / offN : 0;  // avg outward push %
            res.asymPerpRatio = qW > 0 ? perpW / qW : -1;
            res.asymPushPct = qW > 0 ? pushW / qW : 0;
            // verdict: the model carries a SUBSTANTIAL back-face-culled concentric
            // duplicate of a non-culled base mesh = the inverted-hull outline.
            // Threshold 120 sits above the retail-vanilla ceiling (max asymDupMax
            // across all 273 vanilla costume DATs = 112) and below genuine Animelee
            // (Breloom-Yoshi = 137). Vanilla character models DO contain small
            // intrinsic black culled outlines, but they stay under this bar; callers
            // can additionally exclude exact vanilla geometry via geomHash.
            res.isAnimelee = res.dupCullAsym >= 2 && res.asymDupMax >= 120;
            if (debug) res.samples = samples;
            return res;
        }
    }
}
