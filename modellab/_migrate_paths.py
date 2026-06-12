"""One-shot: rewrite absolute path literals after moving modellab/ into the
repo (ssbmNucleus-master/modellab -> ssbmNucleus-master/ssbmNucleus/modellab).
Literal -> literal so raw strings and f-strings all keep working."""
from pathlib import Path

HERE = Path(__file__).parent
OLD = [
    (r"C:\Users\david\projects\ssbmNucleus-master\modellab",
     r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab"),
    ("C:\\\\Users\\\\david\\\\projects\\\\ssbmNucleus-master\\\\modellab",
     "C:\\\\Users\\\\david\\\\projects\\\\ssbmNucleus-master\\\\ssbmNucleus\\\\modellab"),
    ("C:/Users/david/projects/ssbmNucleus-master/modellab",
     "C:/Users/david/projects/ssbmNucleus-master/ssbmNucleus/modellab"),
]

changed = 0
for py in sorted(HERE.glob("*.py")):
    if py.name == "_migrate_paths.py":
        continue
    text = py.read_text(encoding="utf-8", errors="replace")
    new = text
    for old, repl in OLD:
        new = new.replace(old, repl)
    if new != text:
        py.write_text(new, encoding="utf-8")
        changed += 1
        print(f"rewrote {py.name}")
print(f"{changed} files updated")
