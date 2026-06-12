"""
session.py -- a programmatic client for HSDRawViewer's --stream WebSocket
protocol, so an agent (or any script) can drive the same machinery the Skin
Creator UI uses: list/fetch/replace textures, reposition the camera, pose
animations, grab rendered frames, and export the edited DAT.

One ViewerSession = one HSDRawViewer process + one WebSocket connection.
The server pushes binary JPEG frames continuously (we keep only the latest)
and answers JSON commands with typed JSON replies; requests here are
serialized (one in flight) which matches how the UI uses it.

Camera note: the stream protocol is DELTA-based (deltaRotX/deltaRotY are
added, deltaZoom multiplies scale, deltaX/deltaY pan). Deltas apply exactly
and in order over TCP, so we mirror the math locally -- seeded from the
server's initial `info` message -- which gives callers absolute positioning
(`set_camera(rot_y=90)`) without a server-side protocol change.
"""

import json
import math
import subprocess
import threading
import time
import urllib.request
from base64 import b64decode, b64encode

try:
    import websocket  # websocket-client -- optional: only the skin lab needs it
except ImportError:
    websocket = None

REQUEST_TIMEOUT = 30.0


class ViewerSessionError(RuntimeError):
    pass


class ViewerSession:
    def __init__(self, exe, port, dat_file, logs_path=None, scene_file=None,
                 aj_file=None, subprocess_kwargs=None, frame_fps=10,
                 startup_timeout=40.0):
        if websocket is None:
            raise ViewerSessionError(
                "The 'websocket-client' package is not installed in the backend's "
                "Python environment (pip install websocket-client).")
        self.port = port
        self.closed = False
        self._send_lock = threading.Lock()      # websocket-client send isn't thread-safe
        self._request_lock = threading.Lock()   # one command in flight at a time
        self._replies = {}                      # msg type -> (threading.Event, payload)
        self._replies_lock = threading.Lock()
        self._frame = None                      # latest binary JPEG frame
        self._frame_seq = 0
        self._frame_cond = threading.Condition()
        self.info = None
        self.camera = None                      # tracked absolute state (degrees for rot)
        self.textures = []                      # cached list (no thumbnails)

        cmd = [str(exe), '--stream', str(port), str(dat_file)]
        # positional args: logs path must be present to pass scene/aj after it
        cmd.append(str(logs_path) if logs_path else '')
        cmd.append(str(scene_file) if scene_file else '')
        if aj_file:
            cmd.append(str(aj_file))
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            **(subprocess_kwargs or {}))

        try:
            self._wait_http_ready(startup_timeout)
            self.ws = websocket.create_connection(
                f'ws://localhost:{port}/', timeout=10)
            self.ws.settimeout(5)
            self._reader = threading.Thread(target=self._read_loop, daemon=True)
            self._reader.start()
            self._wait_info(timeout=15.0)
            # throttle the frame stream; we only ever read the latest frame
            self._send({'type': 'fps', 'value': int(frame_fps)})
            self._load_texture_list()
        except Exception:
            self.close()
            raise

    # ------------------------------------------------------------------ #
    # process / connection plumbing                                       #
    # ------------------------------------------------------------------ #
    def _wait_http_ready(self, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise ViewerSessionError(
                    f'viewer process exited during startup (code {self.process.returncode})')
            try:
                req = urllib.request.urlopen(f'http://localhost:{self.port}/', timeout=1)
                if req.status == 200:
                    return
            except Exception:
                pass
            time.sleep(0.4)
        raise ViewerSessionError('viewer did not become ready in time')

    def _read_loop(self):
        while not self.closed:
            try:
                opcode, data = self.ws.recv_data()
            except websocket.WebSocketTimeoutException:
                continue
            except Exception:
                break
            if opcode == websocket.ABNF.OPCODE_BINARY:
                with self._frame_cond:
                    self._frame = data
                    self._frame_seq += 1
                    self._frame_cond.notify_all()
            elif opcode == websocket.ABNF.OPCODE_TEXT:
                try:
                    msg = json.loads(data)
                except Exception:
                    continue
                mtype = msg.get('type')
                if not mtype:
                    continue
                with self._replies_lock:
                    waiter = self._replies.get(mtype)
                if waiter:
                    waiter[1] = msg
                    waiter[0].set()
                elif mtype == 'info':
                    self.info = msg
            elif opcode == websocket.ABNF.OPCODE_CLOSE:
                break

    def _wait_info(self, timeout):
        # `info` arrives unsolicited right after connect
        deadline = time.time() + timeout
        while self.info is None and time.time() < deadline:
            time.sleep(0.05)
        if self.info is None:
            raise ViewerSessionError('no info message from viewer')
        cam = self.info.get('camera') or {}
        self.camera = {
            'rotX': float(cam.get('rotX', 0.0)),
            'rotY': float(cam.get('rotY', 0.0)),
            'scale': float(cam.get('scale', 1.0)),
            'x': float(cam.get('x', 0.0)),
            'y': float(cam.get('y', 0.0)),
        }

    def _send(self, msg):
        with self._send_lock:
            self.ws.send(json.dumps(msg))

    def _request(self, msg, reply_type, timeout=REQUEST_TIMEOUT):
        """Send a command and wait for its typed reply."""
        with self._request_lock:
            event = threading.Event()
            waiter = [event, None]
            with self._replies_lock:
                self._replies[reply_type] = waiter
            try:
                self._send(msg)
                if not event.wait(timeout):
                    raise ViewerSessionError(f'timed out waiting for {reply_type}')
                return waiter[1]
            finally:
                with self._replies_lock:
                    self._replies.pop(reply_type, None)

    def alive(self):
        return not self.closed and self.process.poll() is None

    def close(self):
        self.closed = True
        try:
            if getattr(self, 'ws', None):
                self.ws.close()
        except Exception:
            pass
        try:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # textures                                                            #
    # ------------------------------------------------------------------ #
    def _load_texture_list(self):
        reply = self._request({'type': 'getTextures'}, 'textureList')
        # matAnim/animates: MatAnim swap frames (blink textures etc.) the
        # viewer appends after the material textures; `animates` is the
        # material texture index the swap bank animates (-1 if unlinked).
        # extra: textures from non-rendered extra JOBJ roots (e.g.
        # Jigglypuff's alt-costume hats), appended after the matanim entries.
        self.textures = [
            {'index': t.get('index'), 'name': t.get('name'),
             'width': t.get('width'), 'height': t.get('height'),
             'matAnim': bool(t.get('matAnim')),
             'animates': t.get('animates', -1),
             'extra': bool(t.get('extra'))}
            for t in (reply.get('textures') or [])
        ]

    def get_full_texture(self, index):
        """Full-resolution texture as PNG bytes."""
        reply = self._request({'type': 'getFullTexture', 'index': int(index)},
                              'fullTexture')
        if reply.get('error') or not reply.get('data'):
            raise ViewerSessionError(reply.get('error') or 'no texture data')
        return b64decode(reply['data'])

    def get_uv_layout(self):
        """Per-texture UV layout: for every texture that geometry samples,
        the triangles as [u0,v0,u1,v1,u2,v2, x0,y0,z0, x1,y1,z1, x2,y2,z2]
        (UVs in wrap units, positions posed world space) plus wrapS/wrapT.
        Used by projection-mode composites (compose.composite_project)."""
        reply = self._request({'type': 'getUVLayout'}, 'uvLayout', timeout=60.0)
        if reply.get('error'):
            raise ViewerSessionError(reply['error'])
        return reply.get('textures') or []

    def update_texture(self, index, png_bytes):
        """Replace a texture (PNG bytes; caller is responsible for sizing)."""
        reply = self._request(
            {'type': 'updateTexture', 'index': int(index),
             'data': b64encode(png_bytes).decode('ascii')},
            'textureUpdated')
        if not reply.get('success'):
            raise ViewerSessionError(reply.get('error') or 'texture update failed')

    # ------------------------------------------------------------------ #
    # camera (absolute via tracked deltas)                                #
    # ------------------------------------------------------------------ #
    def set_camera(self, rot_x=None, rot_y=None, scale=None, x=None, y=None):
        """Absolute camera positioning. Rotations in degrees, scale ~ zoom
        (bigger = closer), x/y pan in world units."""
        msg = {'type': 'camera'}
        if rot_x is not None:
            msg['deltaRotX'] = float(rot_x) - self.camera['rotX']
            self.camera['rotX'] = float(rot_x)
        if rot_y is not None:
            msg['deltaRotY'] = float(rot_y) - self.camera['rotY']
            self.camera['rotY'] = float(rot_y)
        if scale is not None:
            target = max(0.1, min(1000.0, float(scale)))
            if self.camera['scale'] > 0:
                msg['deltaZoom'] = target / self.camera['scale'] - 1.0
            self.camera['scale'] = target
        if x is not None:
            msg['deltaX'] = float(x) - self.camera['x']
            self.camera['x'] = float(x)
        if y is not None:
            msg['deltaY'] = float(y) - self.camera['y']
            self.camera['y'] = float(y)
        if len(msg) > 1:
            self._send(msg)
        return dict(self.camera)

    def nudge_camera(self, delta_rot_x=0.0, delta_rot_y=0.0, delta_zoom=0.0,
                     delta_x=0.0, delta_y=0.0):
        """Relative camera move (mirrors the protocol directly)."""
        msg = {'type': 'camera'}
        if delta_rot_x:
            msg['deltaRotX'] = float(delta_rot_x)
            self.camera['rotX'] += float(delta_rot_x)
        if delta_rot_y:
            msg['deltaRotY'] = float(delta_rot_y)
            self.camera['rotY'] += float(delta_rot_y)
        if delta_zoom:
            msg['deltaZoom'] = float(delta_zoom)
            self.camera['scale'] = max(0.1, min(1000.0, self.camera['scale'] * (1.0 + float(delta_zoom))))
        if delta_x:
            msg['deltaX'] = float(delta_x)
            self.camera['x'] += float(delta_x)
        if delta_y:
            msg['deltaY'] = float(delta_y)
            self.camera['y'] += float(delta_y)
        if len(msg) > 1:
            self._send(msg)
        return dict(self.camera)

    # ------------------------------------------------------------------ #
    # frames                                                              #
    # ------------------------------------------------------------------ #
    def grab_frame(self, fresh=2, timeout=5.0):
        """The current rendered view as JPEG bytes. Waits for `fresh` NEW
        frames so recent camera/texture changes are actually in the shot."""
        with self._frame_cond:
            target = self._frame_seq + max(0, int(fresh))
            deadline = time.time() + timeout
            while self._frame_seq < target:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._frame_cond.wait(remaining)
            if self._frame is None:
                raise ViewerSessionError('no frame received from viewer yet')
            return self._frame

    def resize(self, width, height):
        self._send({'type': 'resize',
                    'width': int(width), 'height': int(height)})

    # ------------------------------------------------------------------ #
    # animation                                                           #
    # ------------------------------------------------------------------ #
    def get_anim_list(self):
        reply = self._request({'type': 'getAnimList'}, 'animList')
        return reply.get('symbols') or []

    def load_anim(self, symbol):
        reply = self._request({'type': 'loadAnim', 'symbol': symbol},
                              'animLoaded', timeout=15.0)
        return reply

    def set_anim_frame(self, frame):
        self._send({'type': 'animSetFrame', 'frame': float(frame)})

    def set_anim_playing(self, playing):
        self._send({'type': 'animPlay' if playing else 'animPause'})

    # ------------------------------------------------------------------ #
    # export                                                              #
    # ------------------------------------------------------------------ #
    def export_dat(self):
        """The current DAT -- including every updateTexture applied -- as bytes."""
        reply = self._request({'type': 'exportDat'}, 'exportDat', timeout=60.0)
        if not reply.get('success') or not reply.get('data'):
            raise ViewerSessionError(reply.get('error') or 'export failed')
        return b64decode(reply['data'])
