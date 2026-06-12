"""Verify the model-lab save path live: zip the v8 DAT exactly like
model_lab.save() does and POST it to the running backend's unified intake.
Then report what the intake created (CSP / stock icon)."""
import io
import json
import zipfile
from pathlib import Path
from urllib import request

DAT = Path(r"C:\Users\david\projects\ssbmNucleus-master\modellab\out\falco_on_fox\PlFxFalcoV8.dat")
NAME = "Falco (AI Model Lab)"

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("PlFxNr.dat", DAT.read_bytes())
zip_bytes = buf.getvalue()
print(f"zip: {len(zip_bytes)} bytes (dat {DAT.stat().st_size})")

boundary = "----modellabsave"
parts = []
parts.append(
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"custom_title\"\r\n\r\n{NAME}\r\n".encode())
parts.append(
    (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
     f"filename=\"{NAME}.zip\"\r\nContent-Type: application/zip\r\n\r\n").encode()
    + zip_bytes + b"\r\n")
parts.append(f"--{boundary}--\r\n".encode())
body = b"".join(parts)

req = request.Request(
    "http://127.0.0.1:5000/api/mex/import/file", data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
try:
    with request.urlopen(req, timeout=600) as r:
        print("status:", r.status)
        print(json.dumps(json.loads(r.read()), indent=2)[:3000])
except request.HTTPError as e:
    print("status:", e.code)
    print(e.read().decode("utf-8", "replace")[:2000])
