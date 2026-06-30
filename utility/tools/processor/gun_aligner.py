"""
Interactive Fox-blaster CSP aligner (dev tool).

Spawns ONE persistent HSDRawViewer in --gun-align-loop mode (the DAT/scene/GL
context load once), then each slider change just re-poses the 3D gun and
re-screenshots -- near-instant. Drag the gun to line it up under the vanilla CSP
(or the gun-only layer), then copy the printed `--gun-*` params into
generate_csp.py's FOX_GUN to update the baked-in placement.

Run:  python gun_aligner.py        (open the printed http://localhost:PORT)
      ALIGN_PORT=9000 python gun_aligner.py   (custom port)

The orientation/offset that ship in the CSP pipeline live in
generate_csp.py -> FOX_GUN; START_* below mirror them so the tool opens at the
current placement. Calibration is tied to Fox's CSP scene (cspfinal.anim +
csp1.yml); re-run this if that pose/camera ever changes.
"""
import http.server, socketserver, urllib.parse, subprocess, os, threading, time, tempfile
from pathlib import Path

ROOT    = Path(__file__).resolve().parents[3]          # ssbmNucleus/
PROC    = ROOT / "utility" / "tools" / "processor"
FOXDIR  = PROC / "csp_data" / "Fox"
EXE     = ROOT / "utility" / "tools" / "HSDLib" / "HSDRawViewer" / "bin" / "Release" / "net6.0-windows" / "HSDRawViewer.exe"
DAT     = ROOT / "storage" / "test-base" / "files" / "PlFxNr.dat"
PLFX    = ROOT / "storage" / "test-base" / "files" / "PlFx.dat"
ANIM    = FOXDIR / "cspfinal.anim"
CAM     = FOXDIR / "csp1.yml"
GUNLAYER= FOXDIR / "gunlayer.png"                       # legacy gun-only 2D layer
VANILLA = FOXDIR / "MnSlChr.usd_0x14BA40_9.png"         # real vanilla Fox CSP (the target)
WORK    = Path(tempfile.gettempdir()) / "fox_gun_aligner"
WORK.mkdir(exist_ok=True)
LIVE    = WORK / "_aligner_live.png"
SCALE, BONE = 4, 68
NO_WIN  = 0x08000000 if os.name == "nt" else 0

# starting placement = the values baked into generate_csp.py FOX_GUN
START = dict(screen=47, roll=-47, pitch=-114, ox=-0.15, oy=-0.8, oz=0.05, gscale=0.85, mirror=0)

class Renderer:
    def __init__(self):
        self.lock = threading.Lock(); self.proc = None; self.start()
    def start(self):
        cmd = [str(EXE), "--csp", str(DAT), str(LIVE), "--scale", str(SCALE),
               "--gun", str(PLFX), "--gun-bone", str(BONE),
               "--gun-view", f'{START["screen"]},{START["roll"]},{START["pitch"]}',
               "--gun-offset", f'{START["ox"]},{START["oy"]},{START["oz"]}',
               "--gun-scale", str(START["gscale"]), "--gun-align-loop", str(ANIM), str(CAM)]
        self.proc = subprocess.Popen(cmd, cwd=str(WORK), creationflags=NO_WIN,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        t0=time.time()
        for line in self.proc.stdout:
            if "GUNLOOP READY" in line: print(f"warm renderer ready in {time.time()-t0:.1f}s"); return
            if self.proc.poll() is not None: print("renderer exited during warmup"); return
    def render(self, p):
        with self.lock:
            if self.proc is None or self.proc.poll() is not None: self.start()
            msg = f'{p["screen"]},{p["roll"]},{p["pitch"]},{p["ox"]},{p["oy"]},{p["oz"]},{p["gscale"]},{int(p.get("mirror",0))}\n'
            try:
                self.proc.stdin.write(msg); self.proc.stdin.flush()
            except Exception:
                self.start(); return None
            for line in self.proc.stdout:
                if "RENDERED" in line: break
                if self.proc.poll() is not None: return None
            return str(LIVE) if LIVE.exists() else None

R = Renderer()

PAGE = """<!doctype html><html><head><meta charset=utf-8><title>Fox Gun Aligner</title>
<style>
 body{margin:0;background:#1e1e24;color:#ddd;font:13px system-ui;display:flex}
 #stage{position:relative;width:480px;height:664px;margin:16px;background:#2a2a33;border:1px solid #444;flex:none}
 #stage img{position:absolute;left:0;top:0;width:480px;height:664px}
 #target{pointer-events:none}
 #panel{padding:18px 20px;min-width:300px}
 .row{margin:9px 0}
 label{display:flex;justify-content:space-between;font-size:12px;color:#bbb}
 input[type=range]{width:100%}
 .val{color:#ffd84d;font-variant-numeric:tabular-nums}
 h3{margin:4px 0 10px;color:#fff}
 #params{white-space:pre-wrap;background:#111;padding:10px;border-radius:6px;font-family:ui-monospace,monospace;font-size:11px;color:#9fd;margin-top:12px;user-select:all}
 button{background:#3a6;border:0;color:#fff;padding:7px 12px;border-radius:6px;cursor:pointer;margin:0 6px 4px 0}
 #status{color:#6c9;height:16px;font-size:11px}
 .hint{color:#888;font-size:11px;line-height:1.5;margin-top:6px}
</style></head><body>
<div id=stage><img id=render src=""><img id=target src="/gunlayer"></div>
<div id=panel>
 <h3>Fox blaster aligner <span style=font-size:11px;color:#6c9>warm</span></h3>
 <div id=status></div>
 <div class=row><label>screen rotate <span class=val id=vscreen></span></label><input type=range id=screen min=-180 max=180 step=1></div>
 <div class=row><label>roll (tilt / face) <span class=val id=vroll></span></label><input type=range id=roll min=-180 max=180 step=1></div>
 <div class=row><label>pitch (in/out) <span class=val id=vpitch></span></label><input type=range id=pitch min=-180 max=180 step=1></div>
 <div class=row><label>pos X <span class=val id=vox></span></label><input type=range id=ox min=-8 max=8 step=0.05></div>
 <div class=row><label>pos Y <span class=val id=voy></span></label><input type=range id=oy min=-8 max=8 step=0.05></div>
 <div class=row><label>depth Z <span class=val id=voz></span></label><input type=range id=oz min=-8 max=8 step=0.05></div>
 <div class=row><label>gun scale <span class=val id=vgscale></span></label><input type=range id=gscale min=0.3 max=2 step=0.01></div>
 <div class=row><label>target opacity <span class=val id=vop></span></label><input type=range id=op min=0 max=1 step=0.05 value=0.5></div>
 <div class=row><button id=undoBtn onclick="undo()">⟲ undo</button><button onclick="reset()">reset</button></div>
 <div class=row>overlay: <button onclick="setOv('/vanilla')">vanilla CSP</button><button onclick="setOv('/gunlayer')">gun layer</button><button onclick="setOv('')">off</button></div>
 <div class=row>mirror: <button id=mx onclick="togM(1)">flip X</button><button id=my onclick="togM(2)">flip Y</button><button id=mz onclick="togM(4)">flip Z</button></div>
 <div class=hint><b>screen</b>=spin in plane, <b>roll</b>=gangster tilt, <b>pitch</b>=tip toward camera, <b>mirror</b>=other-handed side. Updates live while you drag. Copy the params line into generate_csp.py FOX_GUN.</div>
 <div id=params></div>
</div>
<script>
const START=__START__;
const ids=['screen','roll','pitch','ox','oy','oz','gscale'];
const el=Object.fromEntries([...ids,'op'].map(i=>[i,document.getElementById(i)]));
ids.forEach(i=>el[i].value=START[i]); el.op.value=0.5;
let mirror=START.mirror||0;
function vals(){const v={};ids.forEach(i=>v[i]=+el[i].value);v.mirror=mirror;return v;}
function setOv(src){const t=document.getElementById('target'); if(src){t.src=src;t.style.display='block';}else{t.style.display='none';}}
function labels(){
  vscreen.textContent=el.screen.value+'°'; vroll.textContent=el.roll.value+'°'; vpitch.textContent=el.pitch.value+'°';
  vox.textContent=(+el.ox.value).toFixed(2); voy.textContent=(+el.oy.value).toFixed(2); voz.textContent=(+el.oz.value).toFixed(2);
  vgscale.textContent=(+el.gscale.value).toFixed(2); vop.textContent=(+el.op.value).toFixed(2);
  document.getElementById('target').style.opacity=el.op.value;
  const p=vals();
  params.textContent='--gun-bone 68 --gun-view "'+p.screen+','+p.roll+','+p.pitch+'" --gun-offset "'+p.ox+','+p.oy+','+p.oz+'" --gun-scale '+p.gscale+(mirror?' --gun-mirror '+mirror:'');
}
function snap(){const s=vals();s.op=+el.op.value;return s;}
function applyState(s){for(const k in s){if(el[k])el[k].value=s[k];} mirror=s.mirror||0; updateMirrorBtns(); labels();}
function updateMirrorBtns(){mx.style.background=(mirror&1)?'#c63':'';my.style.background=(mirror&2)?'#c63':'';mz.style.background=(mirror&4)?'#c63':'';}
let history=[], last=null;
function record(){ if(last) history.push(last); last=snap(); if(history.length>80)history.shift(); document.getElementById('undoBtn').disabled=history.length==0; }
function undo(){ if(!history.length)return; const s=history.pop(); applyState(s); last=snap(); document.getElementById('undoBtn').disabled=history.length==0; go(); }
function reset(){ record(); applyState(Object.assign({op:0.5},START)); last=snap(); go(); }
function togM(bit){ if(last) history.push(last); mirror^=bit; updateMirrorBtns(); last=snap(); document.getElementById('undoBtn').disabled=false; labels(); go(); }
let busy=false,pending=false;
async function go(){
  labels();
  if(busy){pending=true;return;}
  busy=true; status.textContent='rendering...';
  const t=performance.now(); const qs=new URLSearchParams(vals()).toString();
  const img=document.getElementById('render');
  await new Promise(r=>{img.onload=r;img.onerror=r;img.src='/render?'+qs+'&t='+Date.now();});
  busy=false; status.textContent=((performance.now()-t)|0)+' ms';
  if(pending){pending=false;go();}
}
ids.forEach(i=>{ el[i].addEventListener('input',()=>go()); el[i].addEventListener('change',()=>record()); });
el.op.addEventListener('input',labels);
document.addEventListener('keydown',e=>{ if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()=='z'){e.preventDefault();undo();} });
updateMirrorBtns(); last=snap(); document.getElementById('undoBtn').disabled=true; labels(); go();
</script></body></html>""".replace("__START__", str(START).replace("'", '"'))

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        u=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(u.query)
        if u.path=="/":
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers()
            self.wfile.write(PAGE.encode()); return
        if u.path=="/vanilla": self._png(VANILLA); return
        if u.path=="/gunlayer": self._png(GUNLAYER); return
        if u.path=="/render":
            try:
                p={k:float(q[k][0]) for k in ["screen","roll","pitch","ox","oy","oz","gscale"]}
                p["mirror"]=int(float(q.get("mirror",["0"])[0]))
            except Exception:
                self.send_response(400); self.end_headers(); return
            self._png(R.render(p)); return
        self.send_response(404); self.end_headers()
    def _png(self,path):
        path=str(path) if path else None
        if not path or not os.path.exists(path):
            self.send_response(503); self.end_headers(); return
        data=open(path,"rb").read()
        self.send_response(200); self.send_header("Content-Type","image/png")
        self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(data)))
        self.end_headers(); self.wfile.write(data)

class TS(socketserver.ThreadingMixIn, socketserver.TCPServer): daemon_threads=True; allow_reuse_address=True
if __name__ == "__main__":
    PORT=int(os.environ.get("ALIGN_PORT","8777"))
    print(f"FOX GUN ALIGNER -> http://localhost:{PORT}  (Ctrl+C to stop)")
    TS(("127.0.0.1",PORT),H).serve_forever()
