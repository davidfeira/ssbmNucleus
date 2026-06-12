"""One-shot probe: does the reference-image path through _openrouter_generate
produce a material that follows the reference palette? Builds a teal/orange
reference, asks for 'dragon scales', saves both for eyeballing."""
import base64
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image

from blueprints.skin_lab import _openrouter_generate

ref = Image.new('RGB', (256, 256))
for y in range(256):
    for x in range(256):
        # hard teal/orange split with a diagonal — distinctive, un-lava-like
        ref.putpixel((x, y), (235, 120, 20) if x + y < 256 else (10, 150, 160))
buf = io.BytesIO()
ref.save(buf, format='JPEG', quality=90)
uri = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

out = Path(__file__).parent / '_probe_out'
out.mkdir(exist_ok=True)
ref.save(out / 'reference.png')

path, info = _openrouter_generate({
    'prompt': 'dragon scale armor plates',
    'referenceImage': uri,
    'name': 'insp-probe',
})
print('generated:', path)
print('info:', info)
