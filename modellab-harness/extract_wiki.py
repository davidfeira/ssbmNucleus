"""Strip HTML from a saved wiki page and print the article text."""
import re
import sys

path = sys.argv[1]
html = open(path, encoding="utf-8", errors="replace").read()
html = re.sub(r"<script[\s\S]*?</script>", "", html)
html = re.sub(r"<style[\s\S]*?</style>", "", html)
text = re.sub(r"<[^>]+>", " ", html)
text = (text.replace("&#39;", "'").replace("&quot;", '"')
            .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))
text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r"\n\s*\n+", "\n", text)

start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 9000
# skip the github chrome: find the wiki body marker
m = re.search(r"(Clone this wiki locally|mexCostume)", text)
if m and start == 0:
    start = m.start()
sys.stdout.buffer.write(text[start:start + limit].encode("utf-8", "replace"))
