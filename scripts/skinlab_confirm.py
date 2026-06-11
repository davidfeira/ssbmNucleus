"""Map-confirmation campaign: run a themed 2-model gauntlet for every mapped
character. Validates that each region map produces full-coverage skins.

Resumable: characters with an existing results.json are skipped.

Usage:
  python scripts/skinlab_confirm.py --port <p> --out gauntlet_out/confirm
  python scripts/skinlab_confirm.py --port <p> --out ... --only Marth,Samus
"""
import argparse
import json
import traceback
from pathlib import Path

from skinlab_collect import ROSTER, slugify
from skinlab_gauntlet import phase_b

MODELS = ['google/gemini-3-flash-preview', 'openai/gpt-5-mini']

THEMES = {
    'Bowser': 'obsidian volcano king: black volcanic rock hide, glowing lava shell',
    'C. Falcon': 'midnight stealth racer: black carbon-fiber suit, neon cyan trim',
    'DK': 'arctic yeti: snow-white fur, icy blue skin',
    'Dr. Mario': 'plague doctor: black leather coat, brass instruments',
    'Falco': 'phoenix: flame-red feathers, ember-gold jacket',
    'Fox': 'shadow ops: charcoal fatigues, night-vision green accents',
    'Ganondorf': 'holy paladin: radiant white-gold armor, ivory cape',
    'Ice Climbers': 'lava climber: magma-orange parka, obsidian trim',
    'Jigglypuff': 'void puff: deep space-black body, glowing teal eyes',
    'Kirby': 'shadow kirby: dark violet body, crimson feet',
    'Link': 'dark hero: black tunic, silver chainmail',
    'Luigi': 'ghost hunter: dark green coat, glowing ecto accents',
    'Mario': 'wildfire: flame-pattern shirt, ash-gray overalls',
    'Marth': 'black knight: onyx armor, blood-red cape',
    'Mewtwo': 'cosmic horror: void-black skin, glowing nebula tail',
    'Nana': 'sakura festival: cherry-blossom pink parka, white silk trim',
    'Ness': 'psychic storm: galaxy-print shirt, violet shorts',
    'Peach': 'wicked queen: black-rose gown, silver jewels',
    'Pichu': 'thunderstorm: storm-gray fur, electric-blue cheeks',
    'Pikachu': 'shiny gold: metallic gold fur, ruby cheeks',
    'Roy': 'emberlord: charred black armor, burning ember cape',
    'Samus': 'stealth suit: gunmetal-gray armor, blood-red visor',
    'Sheik': 'white assassin: ivory bodysuit, gold-trimmed wraps',
    'Yoshi': 'dragon: emerald scale hide, obsidian-spiked shell',
    'Young Link': 'forest spirit: mossy bark tunic, white birch shield',
    'Zelda': 'twilight princess: black-violet gown, silver hair',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--only', default='')
    args = ap.parse_args()

    only = {s.strip() for s in args.only.split(',') if s.strip()}
    failures = []
    for character, code in ROSTER:
        if only and character not in only:
            continue
        out_dir = Path(args.out) / slugify(character)
        if (out_dir / 'results.json').exists():
            print(f'{character}: already confirmed, skipping', flush=True)
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        theme = THEMES[character]
        print(f'=== {character}: "{theme}"', flush=True)
        results = {}
        try:
            phase_b(MODELS, args.port, theme, out_dir, results,
                    character=character, costume_code=code)
            (out_dir / 'results.json').write_text(
                json.dumps(results, indent=1), encoding='utf-8')
        except Exception:
            failures.append(character)
            print(f'FAILED {character}:', flush=True)
            traceback.print_exc()
    print('done. failures:', failures or 'none', flush=True)


if __name__ == '__main__':
    main()
