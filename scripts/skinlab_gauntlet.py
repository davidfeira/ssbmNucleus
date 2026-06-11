"""
skinlab_gauntlet.py -- benchmark OpenRouter vision models on the two LLM roles
of the skin lab, to find out how cheap a model the shipped feature can use.

Phase A (classify): the model sees a labeled contact sheet of every texture in
the open costume and assigns each index a role (fur/cloth/armor/eyes/mouth/
other). Scored against the shipped region map (ground truth).

Phase B (plan): the model gets the region map + a theme and must emit a plan
as JSON (composite / hue-shift steps with material prompts). The plan is
validated, then EXECUTED against the live skin lab; the rendered frame is
saved per model for side-by-side judging.

Usage:
  set OPENROUTER_API_KEY=...
  python scripts/skinlab_gauntlet.py --port <backend port> [--phase a|b|all]
                                     [--models id1,id2,...] [--theme "..."]
  Results land in --out (default: ../gauntlet_out relative to the repo).
"""

import argparse
import base64
import hashlib
import io
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parent.parent
REGION_MAP_PATH = REPO / 'backend' / 'assets' / 'texture_regions' / 'Fox.json'

DEFAULT_MODELS = [
    'openai/gpt-5-nano',
    'google/gemini-2.5-flash-lite',
    'qwen/qwen3-vl-30b-a3b-instruct',
    'openai/gpt-5-mini',
    'google/gemini-3-flash-preview',
    'anthropic/claude-haiku-4.5',
]

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Material generation route (set from CLI args in main()).
IMAGE_PROVIDER = 'openrouter'
IMAGE_MODEL = 'google/gemini-2.5-flash-image'

CLASSIFY_ROLES = ['fur', 'cloth', 'armor', 'eyes', 'mouth', 'other']


# --------------------------------------------------------------------------- #
# OpenRouter plumbing                                                          #
# --------------------------------------------------------------------------- #
def call_model(model, text, image_b64=None, max_tokens=4000, mime='image/png'):
    content = [{'type': 'text', 'text': text}]
    if image_b64:
        content.append({'type': 'image_url',
                        'image_url': {'url': f'data:{mime};base64,{image_b64}'}})
    t0 = time.time()
    res = requests.post(OPENROUTER_URL, timeout=180, json={
        'model': model,
        'messages': [{'role': 'user', 'content': content}],
        'max_tokens': max_tokens,
    }, headers={'Authorization': f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
    elapsed = time.time() - t0
    body = res.json()
    if 'error' in body:
        raise RuntimeError(f"{model}: {body['error']}")
    msg = body['choices'][0]['message']['content'] or ''
    usage = body.get('usage') or {}
    return msg, {'elapsed_s': round(elapsed, 1),
                 'prompt_tokens': usage.get('prompt_tokens'),
                 'completion_tokens': usage.get('completion_tokens')}


def extract_json(text):
    """Lenient: first balanced {...} block in the reply (handles ```json fences)."""
    text = re.sub(r'```(?:json)?', '', text)
    start = text.find('{')
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


# --------------------------------------------------------------------------- #
# skin-lab plumbing                                                            #
# --------------------------------------------------------------------------- #
class Lab:
    def __init__(self, port):
        self.base = f'http://127.0.0.1:{port}/api/mex/skin-lab'

    def open(self, character='Fox', costume_code='PlFxNr'):
        r = requests.post(f'{self.base}/open', timeout=120,
                          json={'character': character,
                                'costumeCode': costume_code}).json()
        if not r.get('success'):
            raise RuntimeError(f"open failed: {r.get('error')}")
        return r['session']

    def regions(self):
        return requests.get(f'{self.base}/regions', timeout=120).json()

    def close(self):
        requests.post(f'{self.base}/close', timeout=30)

    def texture(self, index):
        r = requests.get(f'{self.base}/texture/{index}', timeout=30)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert('RGBA')

    def frame(self, fresh=4):
        r = requests.get(f'{self.base}/frame?fresh={fresh}', timeout=30)
        r.raise_for_status()
        return r.content

    def camera(self, **kw):
        requests.post(f'{self.base}/camera', json=kw, timeout=15)

    def composite(self, **kw):
        return requests.post(f'{self.base}/composite', json=kw, timeout=900).json()

    def hue_shift(self, **kw):
        return requests.post(f'{self.base}/hue-shift', json=kw, timeout=120).json()

    def tint(self, **kw):
        return requests.post(f'{self.base}/tint', json=kw, timeout=120).json()


def capture_review_sheet(lab):
    """One image, full information: front + back at a whole-body framing,
    plus the CSP-camera shot (the vault-facing view users actually see).
    Returns (jpeg_bytes, PIL.Image)."""
    csp_cam = (lab.session.get('camera') or {})  # the scene's CSP framing
    panels = []
    for label, cam in (
            ('front', {'rotX': 0, 'rotY': 0, 'scale': 0.75, 'x': 0, 'y': 10}),
            ('back', {'rotX': 0, 'rotY': 180, 'scale': 0.75, 'x': 0, 'y': 10}),
            ('CSP view', {k: csp_cam.get(k) for k in ('rotX', 'rotY', 'scale', 'x', 'y')
                          if csp_cam.get(k) is not None})):
        lab.camera(**cam)
        img = Image.open(io.BytesIO(lab.frame())).convert('RGB')
        # crop the model area (center 60% horizontally) so panels read larger
        w, h = img.size
        img = img.crop((int(w * 0.2), 0, int(w * 0.8), h))
        img = img.resize((420, int(420 * img.height / img.width)))
        draw = ImageDraw.Draw(img)
        draw.text((8, 6), label, fill=(255, 255, 120))
        panels.append(img)
    sheet = Image.new('RGB', (sum(p.width for p in panels), max(p.height for p in panels)), (0, 0, 0))
    x = 0
    for p in panels:
        sheet.paste(p, (x, 0))
        x += p.width
    buf = io.BytesIO()
    sheet.save(buf, format='JPEG', quality=88)
    return buf.getvalue(), sheet


def contact_sheet(lab, indexes, cell=112, cols=6):
    """A labeled grid of texture thumbnails for the classification prompt."""
    rows = (len(indexes) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell, rows * (cell + 16)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for n, idx in enumerate(indexes):
        img = lab.texture(idx).convert('RGB')
        img.thumbnail((cell - 8, cell - 8), Image.NEAREST)
        x = (n % cols) * cell
        y = (n // cols) * (cell + 16)
        sheet.paste(img, (x + 4, y + 16))
        draw.text((x + 4, y + 2), f'#{idx}', fill=(255, 255, 80))
    buf = io.BytesIO()
    sheet.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii'), sheet


# --------------------------------------------------------------------------- #
# Phase A: classification                                                      #
# --------------------------------------------------------------------------- #
def ground_truth():
    rm = json.loads(REGION_MAP_PATH.read_text(encoding='utf-8'))
    regions = rm['regions']
    truth = {}
    for i in range(rm['basis']['textureCount']):
        roles = set()
        for region, idxs in regions.items():
            if i in idxs:
                roles.add({'face_detail': 'mouth'}.get(region, region))
        # nose counts as mouth-area face detail; anything unclassified = other
        truth[i] = roles or {'other'}
    return truth


CLASSIFY_PROMPT = """You are looking at a contact sheet of every texture inside a
Super Smash Bros. Melee character costume file (the character is Fox McCloud:
an anthropomorphic fox with golden-orange fur wearing a jacket, pants, boots,
gloves and a headset). Each thumbnail is labeled with its texture index (#N).

Classify EVERY index into exactly one role:
- fur: the character's fur/hair (any color of pelt)
- cloth: fabric clothing (jacket, pants, sleeves, belt)
- armor: hard surfaces - boots, gloves, helmet, metal panels, buckles
- eyes: an eye/iris
- mouth: mouth, teeth, tongue, or nose
- other: anything else / unidentifiable

Reply with ONLY a JSON object mapping every index to a role, e.g.
{"0": "cloth", "1": "fur", ...}. Every index on the sheet must appear."""


def phase_a(models, lab, out_dir, results):
    indexes = [t['index'] for t in lab.session['textures']]
    sheet_b64, sheet = contact_sheet(lab, indexes)
    sheet.save(out_dir / 'contact_sheet.png')
    truth = ground_truth()

    for model in models:
        entry = results.setdefault(model, {})
        try:
            reply, usage = call_model(model, CLASSIFY_PROMPT, image_b64=sheet_b64)
            parsed = extract_json(reply) or {}
            answers = {int(k): str(v).strip().lower() for k, v in parsed.items()
                       if str(k).strip().lstrip('#').isdigit()}
            correct = sum(1 for i in indexes if answers.get(i) in truth.get(i, set()))
            entry['classify'] = {
                'accuracy': round(correct / len(indexes), 3),
                'correct': correct, 'total': len(indexes),
                'missing': len([i for i in indexes if i not in answers]),
                'usage': usage,
                'answers': {str(i): answers.get(i) for i in indexes},
            }
            print(f"[A] {model}: {correct}/{len(indexes)} "
                  f"({entry['classify']['accuracy']:.0%})  {usage}")
        except Exception as e:
            entry['classify'] = {'error': str(e)[:500]}
            print(f"[A] {model}: ERROR {e}")


# --------------------------------------------------------------------------- #
# Phase B: plan + execute                                                      #
# --------------------------------------------------------------------------- #
PLAN_PROMPT = """You are designing a Super Smash Bros. Melee costume transformation
for {character} using a texture-compositing API. The theme is:

  "{theme}"

The costume's textures are grouped into named regions:
{region_summary}

The CURRENT costume colors (measured from its pixels):
{color_facts}
A great themed skin usually transforms ALL of it -- anything you don't touch
stays stock and looks out of place.

You can emit three kinds of steps:
1. {{"op": "composite", "region": "<name>", "material_prompt": "<a text-to-image
   prompt for a seamless material/fabric tile>", "modulate": {{"lo": 0.3-0.5,
   "hi": 1.4-1.9}}}}
   -- generates the material and lays it over that region's pixels, shaded by
   the original lighting. Use vivid, specific material prompts. NOTE: on
   "cloth" this replaces only the COLORED fabric; on "armor" only the
   WHITE/GRAY surfaces.
2. {{"op": "hue-shift", "region": "<name>", "hueShift": -180..180,
   "saturationShift": -100..100}}
   -- rotates the existing colors (starting points above), keeps the pattern.
   Does NOTHING on white/gray pixels (no hue to rotate).
3. {{"op": "tint", "region": "<name>", "hue": 0-360, "saturation": 0-100}}
   -- paints the region's pixels to one hue, keeping the shading. This is the
   tool for white/gray armor (e.g. hue 120 sat 50 = mossy green armor) or for
   flat recolors without a generated pattern.

Rules:
- 3 to 6 steps total. At most 3 composite steps.
- Cover the whole costume: EVERY region listed above should get a step unless
  the theme truly calls for leaving it stock (small detail regions like
  "jewels" or "face_detail" are fine to skip or just tint).
- The "eyes" region may be hue-shifted or tinted but NEVER composited.

Reply with ONLY JSON: {{"skin_name": "<short name>", "steps": [...]}}"""


REVIEW_PROMPT = """You previously designed a Melee costume for the theme
"{theme}" and your plan was executed. The attached image is the ACTUAL result
rendered on the 3D model.

Critique it against the theme. Look specifically for: parts that still look
STOCK/untouched (original colors: {color_facts}), regions whose color clashes
with the theme, and anything too subtle to read. The image shows front, back,
and the character-select framing -- check ALL three.

If it needs work, reply with up to 3 fix-up steps. Each step must be an OBJECT
in exactly the same format as the planning ops, e.g.:
  {{"op": "tint", "region": "armor", "hue": 120, "saturation": 55}}
  {{"op": "hue-shift", "region": "fur", "hueShift": 80, "saturationShift": 10}}
  {{"op": "composite", "region": "cloth", "material_prompt": "..."}}
At most 1 new composite. If it genuinely looks complete and on-theme, reply
with an empty steps list.

Reply with ONLY JSON: {{"assessment": "<one sentence>", "steps": [...]}}"""


def validate_plan(plan, regions, max_steps=6, max_composites=3, allow_empty=False,
                  lenient=False):
    """lenient=True (review mode): SKIP malformed entries instead of rejecting
    the whole list -- models get loose with the fix-step format."""
    if not isinstance(plan, dict) or not isinstance(plan.get('steps'), list):
        return None, 'no steps list'
    steps, composites = [], 0
    for s in plan['steps'][:max_steps]:
        if not isinstance(s, dict):
            if lenient:
                continue
            return None, 'step is not an object'
        op = (s.get('op') or '').strip()
        region = (s.get('region') or '').strip()
        if lenient and (op not in ('composite', 'hue-shift', 'tint') or region not in regions):
            continue
        if region not in regions:
            return None, f'unknown region {region!r}'
        if op == 'composite':
            if region == 'eyes':
                return None, 'tried to composite eyes'
            prompt = (s.get('material_prompt') or '').strip()
            if not prompt:
                return None, 'composite without material_prompt'
            composites += 1
            if composites > max_composites:
                return None, 'too many composites'
            steps.append(s)
        elif op == 'hue-shift':
            try:
                float(s.get('hueShift', 0) or 0)
                float(s.get('saturationShift', 0) or 0)
            except (TypeError, ValueError):
                return None, 'non-numeric shift'
            steps.append(s)
        elif op == 'tint':
            try:
                float(s.get('hue'))
                float(s.get('saturation', 60) or 60)
            except (TypeError, ValueError):
                return None, 'tint without numeric hue'
            steps.append(s)
        else:
            return None, f'unknown op {op!r}'
    if not steps and not allow_empty:
        return None, 'empty plan'
    return steps, None


def execute_steps(lab, steps):
    """Run validated steps against the open session; raises on failure.
    Composites run FIRST regardless of plan order: their masks select the
    ORIGINAL colors, and a tint on the same region beforehand re-saturates the
    pixels so the composite mask matches nothing (observed self-sabotage).
    Logs each step's changed/skipped so silent partial-coverage shows up."""
    steps = sorted(steps, key=lambda s: 0 if s['op'] == 'composite' else 1)
    for s in steps:
        if s['op'] == 'composite':
            key = re.sub(r'\s+', ' ', s['material_prompt'].strip().lower())
            material = {'generate': {
                'prompt': s['material_prompt'],
                'provider': IMAGE_PROVIDER,
                'model': IMAGE_MODEL,
                'name': hashlib.sha1(key.encode()).hexdigest()[:10]}}
            r = lab.composite(region=s['region'], material=material,
                              modulate=s.get('modulate') or {})
            if not r.get('success'):
                raise RuntimeError(f"composite failed: {r.get('error')}")
        elif s['op'] == 'tint':
            r = lab.tint(region=s['region'], hue=s.get('hue'),
                         saturation=s.get('saturation', 60) or 60)
            if not r.get('success'):
                raise RuntimeError(f"tint failed: {r.get('error')}")
        else:
            r = lab.hue_shift(region=s['region'],
                              hueShift=s.get('hueShift', 0) or 0,
                              saturationShift=s.get('saturationShift', 0) or 0)
            if not r.get('success'):
                raise RuntimeError(f"hue-shift failed: {r.get('error')}")
        skipped = r.get('skipped') or []
        print(f"    {s['op']}:{s['region']} changed={r.get('changed')}"
              + (f" skipped={[(k['index'], k['reason']) for k in skipped]}" if skipped else ''))


HUE_NAMES = [(15, 'red'), (40, 'orange'), (65, 'yellow'), (95, 'olive'),
             (150, 'green'), (185, 'teal'), (250, 'blue'), (290, 'purple'),
             (330, 'magenta'), (360, 'red')]


def hue_name(h):
    for limit, name in HUE_NAMES:
        if h <= limit:
            return name
    return 'red'


def color_facts_from_hints(hints):
    facts = []
    for region, hint in (hints or {}).items():
        if hint.get('hueMin') is not None and hint.get('hueMax') is not None:
            mid = (hint['hueMin'] + hint['hueMax']) / 2 if hint['hueMin'] <= hint['hueMax'] \
                else ((hint['hueMin'] + hint['hueMax'] + 360) / 2) % 360
            facts.append(f"- {region}: {hue_name(mid)} (hue ~{hint['hueMin']}-{hint['hueMax']})")
        elif hint.get('satMax') is not None:
            facts.append(f'- {region}: white/gray surfaces')
    return '\n'.join(facts) or '- (no color data)'


def phase_b(models, lab_port, theme, out_dir, results, character='Fox',
            costume_code='PlFxNr'):
    map_path = REGION_MAP_PATH.parent / f'{character}.json'
    rm = json.loads(map_path.read_text(encoding='utf-8'))
    region_summary = '\n'.join(
        f'- {name}: texture indexes {idxs}'
        for name, idxs in rm['regions'].items())

    # probe session: measure the open costume's actual colors for the prompt
    probe = Lab(lab_port)
    probe.session = probe.open(character, costume_code)
    try:
        live = (probe.regions().get('regionMap') or {}).get('liveMaskHints') or {}
    finally:
        probe.close()
    color_facts = color_facts_from_hints(live)
    print(f'[B] costume colors:\n{color_facts}')

    prompt = PLAN_PROMPT.format(theme=theme, region_summary=region_summary,
                                character=character, color_facts=color_facts)

    for model in models:
        entry = results.setdefault(model, {})
        plan_info = {}
        entry['plan'] = plan_info
        try:
            reply, usage = call_model(model, prompt)
            plan_info['usage'] = usage
            plan = extract_json(reply)
            steps, err = validate_plan(plan or {}, set(rm['regions']))
            if err:
                plan_info.update(valid=False, error=err, raw=reply[:1200])
                print(f"[B] {model}: INVALID PLAN ({err})")
                continue
            plan_info.update(valid=True, skin_name=(plan.get('skin_name') or '')[:60],
                             steps=steps)
            print(f"[B] {model}: plan ok -- "
                  + '; '.join(f"{s['op']}:{s['region']}" for s in steps))

            # execute on a FRESH session
            lab = Lab(lab_port)
            lab.session = lab.open(character, costume_code)
            try:
                execute_steps(lab, steps)
                shot, _ = capture_review_sheet(lab)
                safe = re.sub(r'[^\w.-]', '_', model)
                (out_dir / f'{safe}_v1.jpg').write_bytes(shot)
                plan_info['executed'] = True
                print(f"[B] {model}: executed (v1 rendered)")

                # REVIEW ITERATION: show the model its own result, apply fixes.
                try:
                    review_reply, review_usage = call_model(
                        model,
                        REVIEW_PROMPT.format(theme=theme, color_facts=color_facts),
                        image_b64=base64.b64encode(shot).decode('ascii'),
                        mime='image/jpeg')
                    plan_info['review_usage'] = review_usage
                    review = extract_json(review_reply) or {}
                    fixes, ferr = validate_plan(review, set(rm['regions']),
                                                max_steps=3, max_composites=1,
                                                allow_empty=True, lenient=True)
                    plan_info['assessment'] = (review.get('assessment') or '')[:300]
                    if ferr:
                        plan_info['review_error'] = ferr
                        print(f"[B] {model}: review invalid ({ferr})")
                    elif fixes:
                        plan_info['fixes'] = fixes
                        execute_steps(lab, fixes)
                        shot, _ = capture_review_sheet(lab)
                        print(f"[B] {model}: review applied "
                              + '; '.join(f"{s['op']}:{s['region']}" for s in fixes))
                    else:
                        plan_info['fixes'] = []
                        print(f"[B] {model}: review says done")
                except Exception as re_err:  # vision unsupported, etc.
                    plan_info['review_error'] = str(re_err)[:300]
                    print(f"[B] {model}: review skipped ({str(re_err)[:120]})")

                (out_dir / f'{safe}.jpg').write_bytes(shot)
                plan_info['render'] = f'{safe}.jpg'
                print(f"[B] {model}: final rendered")
            finally:
                lab.close()
        except Exception as e:
            plan_info.setdefault('valid', False)
            plan_info['error'] = str(e)[:500]
            print(f"[B] {model}: ERROR {e}")


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--phase', default='all', choices=['a', 'b', 'all'])
    ap.add_argument('--models', default=','.join(DEFAULT_MODELS))
    ap.add_argument('--theme', default='toxic swamp fox: corroded hazmat gear, '
                                       'glowing radioactive green slime')
    ap.add_argument('--out', default=str(REPO.parent / 'gauntlet_out'))
    ap.add_argument('--image-provider', default='openrouter',
                    choices=['openrouter', 'assetfarm'])
    ap.add_argument('--image-model', default='google/gemini-2.5-flash-image')
    ap.add_argument('--character', default='Fox')
    ap.add_argument('--costume', default='PlFxNr')
    args = ap.parse_args()

    global IMAGE_PROVIDER, IMAGE_MODEL
    IMAGE_PROVIDER = args.image_provider
    IMAGE_MODEL = args.image_model if args.image_provider == 'openrouter' else None

    if not os.environ.get('OPENROUTER_API_KEY'):
        sys.exit('set OPENROUTER_API_KEY first')

    models = [m.strip() for m in args.models.split(',') if m.strip()]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    if args.phase in ('a', 'all'):
        lab = Lab(args.port)
        lab.session = lab.open()
        try:
            phase_a(models, lab, out_dir, results)
        finally:
            lab.close()

    if args.phase in ('b', 'all'):
        phase_b(models, args.port, args.theme, out_dir, results,
                character=args.character, costume_code=args.costume)

    (out_dir / 'results.json').write_text(json.dumps(results, indent=2),
                                          encoding='utf-8')
    print(f'\nresults -> {out_dir / "results.json"}')


if __name__ == '__main__':
    main()
