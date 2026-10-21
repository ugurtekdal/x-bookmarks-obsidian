# Writes vault notes (and article notes, if any) for the bookmarks in a data file.
# Usage:
#   python -I -X utf8 build_notes.py DATA.py dry    -> check only, writes nothing
#   python -I -X utf8 build_notes.py DATA.py show   -> check + print the generated notes
#   python -I -X utf8 build_notes.py DATA.py        -> write notes, copy images, move pending\ -> processed\
# Data file format: example_data.py
# Mechanical work done here: builds the frontmatter in schema order, copies the Original text from the raw
# file verbatim (without image lines, HTML entities cleaned), adds the translation callout, skips duplicate
# tweet_ids, warns about topics outside the dictionary and [[wikilinks]] missing from the vault.
# Never writes to the raw bookmarks\ folder.
import os, re, shutil, sys, importlib.util, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BASE, VAULT, ASSETS, ARTICLES, RAW, PENDING, PROCESSED, KEEP_LANGS, H, VALUES, TYPES, topics, note_names

TOPICS = topics()
NOTE_NAMES = note_names()

def clean(s):
    for a, b in [("&`#x27`;", "'"), ("&`#39`;", "'"), ("&#x27;", "'"), ("&#39;", "'"), ("&#34;", '"'),
                 ("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">"), ("&#38;", "&"), ("&amp;", "&")]:
        s = s.replace(a, b)
    return s

def q(s): return '"' + clean(s).replace('"', '').replace('\n', ' ').strip() + '"'
def flow(l, quote=False): return "[" + ", ".join((f'"{x}"' if quote else x) for x in l) + "]"
def quote_block(t): return "\n".join(("> " + l if l.strip() else ">") for l in t.split("\n"))

def existing_ids():
    ids = set()
    for p in glob.glob(os.path.join(VAULT, "*.md")):
        m = re.search(r'^tweet_id:\s*"?(\d+)', open(p, encoding="utf-8").read(), re.M)
        if m: ids.add(m.group(1))
    return ids

def orig_parts(raw):
    """Returns (header lines, body) from the raw file; image lines dropped, entities cleaned."""
    b = raw.split("# Thread", 1)[-1].strip("\n")
    lines = [l for l in b.split("\n") if not re.match(r'^[>\s]*!\[[^\]]*\]\(assets[^)]*\)\s*$', l)]
    b = clean(re.sub(r'\n{3,}', '\n\n', "\n".join(lines)).strip())
    b = re.sub(r'\[\[([^\]\n]*)\]\]', r'[\\[\1\\]]', b)  # [[X]] in tweet text must not become a fake wikilink
    b = b.replace("[[", "[\\[")  # also unclosed patterns like [[Title](url)]
    m = re.search(r'^\[View on Twitter\]\([^)]*\)\s*$', b, re.M)
    if m: return b[:m.end()].strip(), b[m.end():].strip()
    return "", b

def rawfm(raw):
    d = {}
    for l in raw.split("---", 2)[1].splitlines():
        m = re.match(r'^(\w+):\s*"?(.*?)"?\s*$', l)
        if m: d[m.group(1)] = m.group(2)
    return d

def build(name, dd, write=True, ids=None):
    src = os.path.join(PENDING, name)
    raw = open(src, encoding="utf-8").read()
    r = rawfm(raw)
    if ids is not None and r['id'] in ids:
        print("== DUPLICATE", name)
        if write: shutil.move(src, os.path.join(PROCESSED, name))
        return None
    lang = dd.get('lang', 'en'); trans = lang not in KEEP_LANGS
    val = dd['value']; tps = dd['topics'][:3]
    if val not in VALUES: print("!! UNKNOWN value", name, val, "->", VALUES)
    if dd['type'] not in TYPES: print("!! UNKNOWN type", name, dd['type'], "->", TYPES)
    bad = [t for t in tps if t not in TOPICS]
    if bad: print("!! TOPIC NOT IN DICTIONARY", name, bad, "-> add it to _topics.md or change it")
    # low notes get no images section, so has_images is false for them too.
    has_img = bool(dd.get('images')) and val != 'low'
    source = r['url'].replace("https://twitter.com", "https://x.com")
    fname = dd['file'] if dd['file'].endswith(".md") else dd['file'] + ".md"
    links = dd.get('links', [])
    fm = ["---", f"title: {q(dd['title'])}", f"source: {source}", f"author: {r['author']}", f"date: {r['date']}",
          f'tweet_id: "{r["id"]}"', f'x_folder: "{r.get("folder", "")}"', f"type: {dd['type']}",
          f"topics: {flow(tps)}", f"tags: {flow(dd.get('tags', [])[:5])}", f"related: {flow(dd.get('related', []), True)}",
          f"lang: {lang}", f"translated: {'true' if trans else 'false'}", f"has_images: {'true' if has_img else 'false'}",
          f"value: {val}", "status: inbox", f"summary: {q(dd['summary'])}"]
    fm += (["links:"] + [f'  - "{x}"' for x in links]) if links else ["links: []"]
    fm.append("---\n")
    out = ["\n".join(fm)]
    art = dd.get('article')
    ov = dd['overview'].strip()
    if art: ov += f"\n\n{H['full_article']} [[{art['name']}]]"
    out.append(f"## {H['summary']}\n" + ov + "\n")
    if val != 'low': out.append(f"## {H['why']}\n" + dd['why'].strip() + "\n")
    out.append(f"## {H['for_you']}\n" + dd['for_you'].strip() + "\n")
    if val != 'low':
        if dd.get('key_points'): out.append(f"## {H['key_points']}\n" + dd['key_points'].strip() + "\n")
        if has_img:
            emb = "\n".join(f"![[{x}]]" for x in dd.get('copy', []))
            out.append(f"## {H['images']}\n" + dd['images'].strip() + "\n\n" + emb + "\n")
        if dd.get('links_section'): out.append(f"## {H['links']}\n" + dd['links_section'].strip() + "\n")
    head, rest = orig_parts(raw)
    if art: rest = re.sub(r'\[([^\]]*)\]\(articles[/\\][^)]*\)', lambda m: f"[[{art['name']}|{m.group(1)}]]", rest)
    if trans:
        if 'trans' in dd:
            tr = dd['trans'].strip()
        else:
            tr = rest
            for old, new in dd['tmap']:
                if old not in tr: print("!! TMAP NOT FOUND", name, old[:60])
                tr = tr.replace(old, new)
        body = f"## {H['original']}\n" + quote_block((head + "\n\n" + tr).strip()) + \
               f"\n\n> [!quote]- {H['source_lang']} ({lang})\n" + quote_block(rest) + "\n"
    else:
        body = f"## {H['original']}\n" + quote_block((head + "\n\n" + rest).strip() if head else rest) + "\n"
    out.append(body)
    text = "\n".join(out)
    for w in re.findall(r'\[\[([^\]|#]+)', text):
        if re.search(r'\.(jpg|jpeg|png|webp|gif|pdf)$', w, re.I):
            if not os.path.exists(os.path.join(RAW, "assets", w)): print("!! IMAGE MISSING", name, w)
        elif w not in NOTE_NAMES and not (art and w == art['name']):
            print("!! WIKILINK MISSING", name, w)
    if not write: return text
    if art:
        a = open(os.path.join(RAW, "articles", art['src']), encoding="utf-8").read()
        a = re.sub(r'^---.*?---\s*', '', a, count=1, flags=re.S)
        a = a.split("\n", 1)[1] if a.startswith("# ") else a
        a = "\n".join(l for l in a.split("\n") if not re.match(r'^\s*!\[[^\]]*\]\([^)]*\)\s*$', l))
        a = re.sub(r'\n{3,}', '\n\n', clean(a)).strip()
        a = re.sub(r'\[\[([^\]]*)\]\]', r'[ [\1] ]', a)  # [[...]] in the article must not become a fake wikilink
        alang = art.get('lang', 'en'); atrans = alang not in KEEP_LANGS
        if atrans:
            a = art['trans'].strip() + f"\n\n> [!quote]- {H['source_lang']} ({alang})\n" + quote_block(a)
        afm = ["---", f"title: {q(art['title'])}", f"source: {art.get('source', source)}",
               f"author: {art.get('author', r['author'])}", f"date: {art.get('date', r['date'])}", f"lang: {alang}",
               f"translated: {'true' if atrans else 'false'}", f'bookmark: "[[{fname[:-3]}]]"', "---\n"]
        dest = os.path.join(ARTICLES, art['name'] + ".md")
        if os.path.exists(dest): print("-- article already exists, skipped:", art['name'])
        else: open(dest, "w", encoding="utf-8", newline="\n").write("\n".join(afm) + "\n" + a + "\n")
    dest = os.path.join(VAULT, fname)
    if os.path.exists(dest):
        print("!! A NOTE WITH THIS NAME EXISTS, not written:", fname); return None
    open(dest, "w", encoding="utf-8", newline="\n").write(text)
    if has_img:
        for c in dd.get('copy', []):
            s = os.path.join(RAW, "assets", c)
            if os.path.exists(s): shutil.copy2(s, os.path.join(ASSETS, c))
            else: print("!! IMAGE MISSING", c)
    shutil.move(src, os.path.join(PROCESSED, name))
    if ids is not None: ids.add(r['id'])
    return text

if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("data", sys.argv[1])
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mode = sys.argv[2] if len(sys.argv) > 2 else "write"
    for d in (ASSETS, ARTICLES, PROCESSED): os.makedirs(d, exist_ok=True)
    ids = existing_ids()
    for n, dd in mod.D.items():
        t = build(n, dd, write=(mode == "write"), ids=ids)
        print("ok", n, "->", dd['file'])
        if mode == "show" and t: print(t)
