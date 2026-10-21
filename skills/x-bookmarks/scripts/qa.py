# Final check: looks for missing fields, topics outside the dictionary, broken wikilinks, missing images,
# HTML entities, has_images / images-section mismatch and duplicate tweet_ids in written notes; prints counts.
# Usage: python -I -X utf8 qa.py [HOURS]   (default 6: notes changed in the last 6 hours are reported)
import os, re, glob, sys, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import VAULT, ASSETS, ARTICLES, H, FIELDS, topics, note_names

hours = float(sys.argv[1]) if len(sys.argv) > 1 else 6
since = time.time() - hours * 3600
names = note_names()
topics_ok = topics()
ENTITIES = ['&quot;', '&#39;', '&amp;', '&#x27;', '&`#', '&#34;']

ids = collections.Counter(); vals = collections.Counter(); langs = collections.Counter()
new = 0; tr = 0; gv = 0; bad = []
for p in glob.glob(os.path.join(VAULT, "*.md")):
    f = os.path.basename(p)
    if f.startswith("_"): continue
    t = open(p, encoding="utf-8").read()
    m = re.search(r'^tweet_id: "(\d+)"', t, re.M)
    if m: ids[m.group(1)] += 1
    if os.path.getmtime(p) < since: continue
    new += 1
    for k in FIELDS:
        if not re.search(r'^' + k + ':', t, re.M): bad.append((f, 'missing field', k))
    v = re.search(r'^value: (\w+)', t, re.M); vals[v.group(1) if v else '?'] += 1
    l = re.search(r'^lang: (\w+)', t, re.M); langs[l.group(1) if l else '?'] += 1
    tr += 'translated: true' in t; gv += 'has_images: true' in t
    tp = re.search(r'^topics: \[(.*)\]', t, re.M)
    for x in [y.strip() for y in (tp.group(1) if tp else '').split(',') if y.strip()]:
        if x not in topics_ok: bad.append((f, 'topic not in dictionary', x))
    if f"## {H['for_you']}" not in t: bad.append((f, f"no '{H['for_you']}' section"))
    if ('has_images: true' in t) != (f"## {H['images']}" in t): bad.append((f, 'has_images / images section mismatch'))
    for w in re.findall(r'\[\[([^\]|#]+)', t):
        if re.search(r'\.(jpg|jpeg|png|webp|gif|pdf)$', w, re.I):
            if not os.path.exists(os.path.join(ASSETS, w)): bad.append((f, 'image missing', w))
        elif w not in names: bad.append((f, 'broken wikilink', w))
    for e in ENTITIES:
        if e in t: bad.append((f, 'html entity', e))

arts = [p for p in glob.glob(os.path.join(ARTICLES, "*.md")) if os.path.getmtime(p) >= since]
for p in arts:
    t = open(p, encoding="utf-8").read(); f = "Articles/" + os.path.basename(p)
    for w in re.findall(r'\[\[([^\]|#]+)', t):
        if w not in names: bad.append((f, 'broken wikilink', w[:60]))
    for e in ENTITIES[:3]:
        if e in t: bad.append((f, 'html entity', e))

print(f"notes in the last {hours:g} hours: {new}, articles: {len(arts)}")
print("value:", dict(vals), "| lang:", dict(langs), "| translated:", tr, "| has_images:", gv)
print("duplicate tweet_id:", [i for i, c in ids.items() if c > 1] or "none")
print("problems:", len(bad))
for b in bad: print("  ", b)
