using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using HSDRaw;
using HSDRaw.Melee.Pl;
using HSDRawViewer.GUI.Plugins.SubactionEditor;
using HSDRawViewer.Rendering.Models;
using HSDRawViewer.Tools;

namespace HSDRawViewer
{
    /// <summary>
    /// Per-animation model-part visibility (Bowser shell, Link's bow, Peach's
    /// f-smash weapon, ...). SHARED by StreamingServer (--stream) and
    /// EmbeddedServer (--embedded) so the two never diverge.
    ///
    /// Reads the fighter-data dat (Pl&lt;XX&gt;.dat) ftData: the model lookup
    /// table + each action's subaction. Subaction event code 31 "Change Model
    /// State" (= decomp set_dobj_flags) selects a slot's variant = the auto path;
    /// hardcoded C-code swaps with no event (Bowser up-B shell, Yoshi egg) come
    /// from the curated Scripts/part_variant_overrides.json. See
    /// docs/ANIMATION_PART_VISIBILITY.md.
    /// </summary>
    public class ModelPartVisibility
    {
        private readonly RenderJObj _renderJObj;
        private readonly Action<string> _log;
        private readonly Action<string, Exception> _logError;

        private SBM_PlayerModelLookupTables _lookupTable;
        private SBM_CostumeLookupTable _costume0;   // costume-0 lookups (added costumes reuse it)
        // animation symbol -> its subaction events (only actions that actually swap parts)
        private Dictionary<string, List<SubactionEvent>> _actionSubactions;
        // processor for the currently-loaded animation (null if it has no swaps)
        private SubactionProcessor _subactionProcessor;
        // curated overrides for C-code swaps (no code-31), keyed by this char's ftData root
        private List<(string match, int slot, int variant)> _partOverrides;
        // the current animation's curated overrides (applied statically each frame)
        private List<(int slot, int variant)> _staticOverrides;

        /// <summary>True once a fighter-data dat with a usable lookup table is loaded.</summary>
        public bool Active => _lookupTable != null;

        public ModelPartVisibility(RenderJObj renderJObj, Action<string> log,
                                   Action<string, Exception> logError = null)
        {
            _renderJObj = renderJObj;
            _log = log ?? (_ => { });
            _logError = logError ?? ((m, e) => _log($"ERROR: {m}: {e?.Message}"));
        }

        /// <summary>
        /// Load the fighter-data dat and cache the model-part lookup table + the
        /// subaction of every action that swaps a part (event code 31/32/33) + the
        /// curated overrides for this character.
        /// </summary>
        public void LoadFighterData(string path)
        {
            try
            {
                if (string.IsNullOrEmpty(path) || !File.Exists(path))
                {
                    _log($"Model-part vis: no fighter-data dat ({path})");
                    return;
                }
                _log($"Loading fighter data for model-part visibility: {path}");
                var f = new HSDRawFile();
                f.Open(path);

                SBM_FighterData fd = null;
                string ftRootName = null;
                foreach (var root in f.Roots)
                {
                    if (root.Data == null || !root.Name.StartsWith("ftData"))
                        continue;
                    fd = root.Data as SBM_FighterData
                         ?? new SBM_FighterData() { _s = root.Data._s };
                    ftRootName = root.Name;
                    break;
                }
                if (fd == null) { _log("  no ftData root in fighter-data dat"); return; }

                _lookupTable = fd.ModelLookupTables;
                if (_lookupTable == null) { _log("  no ModelLookupTables"); return; }
                var cl = _lookupTable.CostumeVisibilityLookups;
                if (cl == null || cl.Length == 0)
                {
                    _log("  empty CostumeVisibilityLookups -- disabling model-part vis");
                    _lookupTable = null;
                    return;
                }
                _costume0 = cl[0];

                _actionSubactions = new Dictionary<string, List<SubactionEvent>>();
                var table = fd.FighterActionTable;
                if (table != null)
                {
                    // The subaction processor follows subroutine/goto pointers via
                    // SubactionEvent.GetPointer, which resolves against this global
                    // list. The editor fills it from its action list; headless we
                    // build it from every subaction's (nested) references so frame
                    // timing across subroutines is correct.
                    var ptrValues = new List<CustomPointerValue>();
                    var seenStructs = new HashSet<HSDStruct>();
                    void CollectRefs(HSDStruct s)
                    {
                        if (s == null || !seenStructs.Add(s)) return;
                        foreach (var kv in s.References)
                        {
                            ptrValues.Add(new CustomPointerValue { Struct = kv.Value, Value = $"0x{kv.Key:X}" });
                            CollectRefs(kv.Value);
                        }
                    }
                    foreach (var act in table.Commands)
                        if (act.SubAction?._s != null)
                            CollectRefs(act.SubAction._s);
                    CustomPointerValue.Values = ptrValues;

                    foreach (var act in table.Commands)
                    {
                        var name = act.Name;
                        if (string.IsNullOrEmpty(name) || act.SubAction == null)
                            continue;
                        List<SubactionEvent> events;
                        try
                        {
                            events = SubactionEvent
                                .GetEvents(SubactionGroup.Fighter, act.SubAction._s)
                                .ToList();
                        }
                        catch { continue; }
                        // keep only actions that actually change model parts:
                        // 31 = Change Model State, 32 = Revert, 33 = Remove
                        bool hasVis = events.Any(e => e.Code == (31 << 2)
                                                   || e.Code == (32 << 2)
                                                   || e.Code == (33 << 2));
                        if (hasVis)
                            _actionSubactions[name] = events;   // last entry wins (duplicates are identical)
                    }
                }
                _log($"  lookup table loaded; {_actionSubactions.Count} action(s) carry model-part swaps");
                LoadPartOverrides(ftRootName);
            }
            catch (Exception ex)
            {
                _logError("LoadFighterData failed", ex);
                _lookupTable = null;
                _actionSubactions = null;
            }
        }

        /// <summary>
        /// Curated overrides for swaps driven by hardcoded C code with no code-31
        /// event (Bowser/Giga up-B shell, Yoshi egg roll/shield). Keyed by ftData
        /// root name in part_variant_overrides.json.
        /// </summary>
        private void LoadPartOverrides(string ftRootName)
        {
            try
            {
                if (string.IsNullOrEmpty(ftRootName)) return;
                var path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory,
                                        "Scripts", "part_variant_overrides.json");
                if (!File.Exists(path)) return;
                using var doc = JsonDocument.Parse(File.ReadAllText(path));
                if (!doc.RootElement.TryGetProperty(ftRootName, out var arr)
                    || arr.ValueKind != JsonValueKind.Array)
                    return;
                var list = new List<(string, int, int)>();
                foreach (var e in arr.EnumerateArray())
                {
                    if (!e.TryGetProperty("match", out var m) || m.ValueKind != JsonValueKind.String)
                        continue;
                    int slot = e.TryGetProperty("slot", out var s) ? s.GetInt32() : 0;
                    int variant = e.TryGetProperty("variant", out var v) ? v.GetInt32() : 0;
                    list.Add((m.GetString(), slot, variant));
                }
                if (list.Count > 0)
                {
                    _partOverrides = list;
                    _log($"  loaded {list.Count} curated part-override(s) for {ftRootName}");
                }
            }
            catch (Exception ex)
            {
                _logError("LoadPartOverrides failed", ex);
            }
        }

        /// <summary>
        /// Show one option (variant) of a model slot and hide the slot's other
        /// options -- the in-game ftParts_80074B6C apply loop. objectid -1 hides
        /// every option of the slot.
        /// </summary>
        private void SetModelVis(SBM_LookupTable lookuptable, int objectid)
        {
            if (lookuptable?.LookupEntries == null || _renderJObj == null)
                return;
            var structs = lookuptable.LookupEntries.Array;
            for (int i = 0; i < structs.Length; i++)
                foreach (byte v in structs[i].Entries)
                    if (v < _renderJObj.DObjCount)
                        _renderJObj.SetDObjVisible(v, i == objectid);
        }

        /// <summary>Select variant <paramref name="objectid"/> for HighPoly slot <paramref name="slot"/>.</summary>
        private void SetModelVis(int slot, int objectid)
        {
            if (_costume0?.HighPoly == null) return;
            var hp = _costume0.HighPoly;
            if (slot >= 0 && slot < hp.Length)
                SetModelVis(hp[slot], objectid);
        }

        /// <summary>
        /// Baseline model state for any motion (mirrors ScriptRenderer.ResetModelState):
        /// every HighPoly slot -&gt; option 0, all LowPoly hidden. Subaction swaps are
        /// then layered on top per frame.
        /// </summary>
        private void ResetModelVis()
        {
            if (_costume0 == null || _renderJObj == null) return;
            if (_costume0.HighPoly != null)
                for (int i = 0; i < _costume0.HighPoly.Length; i++)
                    SetModelVis(_costume0.HighPoly[i], 0);
            if (_costume0.LowPoly?.Array != null)
                foreach (var lut in _costume0.LowPoly.Array)
                    SetModelVis(lut, -1);
        }

        /// <summary>
        /// Apply the default in-game part visibility without requiring an
        /// animation to be selected. This is the initial pose/editor baseline.
        /// </summary>
        public void ApplyDefaultState()
        {
            if (_lookupTable == null)
                return;
            ResetModelVis();
        }

        /// <summary>
        /// Prepare model-part visibility for a newly-loaded animation. Reverts to
        /// the default model, then arms a SubactionProcessor (auto code-31) or a
        /// curated static override. Must run on the render/UI thread.
        /// </summary>
        public void OnAnimationLoaded(string symbol)
        {
            _subactionProcessor = null;
            _staticOverrides = null;
            if (_lookupTable == null)
                return;
            try
            {
                // always revert to default first so a previous animation's swap
                // (e.g. shell) doesn't linger into one that doesn't reset it
                ResetModelVis();
                if (_actionSubactions != null && symbol != null
                    && _actionSubactions.TryGetValue(symbol, out var events))
                {
                    // auto path: the animation's own subaction code-31 events
                    var proc = new SubactionProcessor { UpdateVISMethod = SetModelVis };
                    proc.SetStruct(events, SubactionGroup.Fighter);
                    _subactionProcessor = proc;
                    ApplyFrame(0);
                    _log($"Model-part swaps armed for {symbol}");
                }
                else if (_partOverrides != null && symbol != null)
                {
                    // curated path: C-code swaps (up-B shell, egg roll) with no event
                    var matched = _partOverrides
                        .Where(o => symbol.Contains(o.match))
                        .Select(o => (o.slot, o.variant))
                        .ToList();
                    if (matched.Count > 0)
                    {
                        _staticOverrides = matched;
                        ApplyFrame(0);
                        _log($"Curated model-part override for {symbol}: "
                            + string.Join(",", matched.Select(o => $"{o.slot}:{o.variant}")));
                    }
                }
            }
            catch (Exception ex)
            {
                // degrade gracefully: a swap failure must never break anim loading
                _subactionProcessor = null;
                _staticOverrides = null;
                _logError($"OnAnimationLoaded failed for {symbol}", ex);
            }
        }

        /// <summary>Apply the model-part state for <paramref name="frame"/> of the current animation.</summary>
        public void ApplyFrame(float frame)
        {
            if (_lookupTable == null)
                return;
            if (_subactionProcessor != null)
            {
                ResetModelVis();                // default, then layer this frame's swaps
                _subactionProcessor.SetFrame(frame);
            }
            else if (_staticOverrides != null)
            {
                ResetModelVis();                // default, then the curated swap (whole anim)
                foreach (var (slot, variant) in _staticOverrides)
                    SetModelVis(slot, variant);
            }
        }
    }
}
