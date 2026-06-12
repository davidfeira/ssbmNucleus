"""Generate the shared inspiration image for the planner gauntlet: a monarch
butterfly wing — orange/black/white palette + a strong motif, neither of
which appears anywhere in the theme text the planners will get."""
import base64
import sys
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / 'backend'))

from aiengine import keystore

key = keystore.get_openrouter_key()
res = requests.post('https://openrouter.ai/api/v1/chat/completions', timeout=180, json={
    'model': 'google/gemini-2.5-flash-image',
    'messages': [{'role': 'user', 'content':
                  'A close-up photograph of a monarch butterfly wing: vivid '
                  'orange panels, bold black veins, white spots along the '
                  'dark edge. Fills the frame.'}],
    'modalities': ['image', 'text'],
}, headers={'Authorization': f'Bearer {key}'})
body = res.json()
url = body['choices'][0]['message']['images'][0]['image_url']['url']
out = REPO.parent / 'gauntlet_out' / 'inspiration' / 'inspiration.png'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(base64.b64decode(url.split('base64,', 1)[1]))
print('saved:', out)
