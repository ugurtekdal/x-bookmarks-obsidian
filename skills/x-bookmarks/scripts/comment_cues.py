# Finds bookmarks whose text says the real content is in the comments / replies
# ("prompt in the comments", "link in the first reply", "ilk yorumda" ...). Downloads nothing.
# Usage:
#   python -I -X utf8 comment_cues.py pending   -> candidates in pending\
#   python -I -X utf8 comment_cues.py vault     -> candidates among the notes already in the vault
# birdmarks usually brings the author's own reply under the tweet as part of the thread; check while reading
# whether the content actually arrived. (birdmarks --replies only fetches other users' replies, so it can't
# be used to get the author's missing reply.)
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PENDING, RAW, VAULT

# 👇 alone doesn't count, it usually points at a quote. To reduce false positives a content noun
# (prompt, link, repo...) is required near the "comment" word.
_NOUN_EN = r"(prompts?|links?|repos?|guides?|templates?|code|files?|workflows?|tutorials?|details|full (?:prompt|guide|list|setup))"
_NOUN_ES = r"(prompts?|enlaces?|links?|plantillas?|gu[ií]a)"
_NOUN_TR = r"(prompt(?:u|lar[ıi])?|link(?:i|ler[ıi])?|repo(?:yu)?|kaynak|kaynaklar|detaylar[ıi]?|dosya)"
CUES = re.compile(
    _NOUN_EN + r"\b[^.\n]{0,30}\b(in|below in|in the|at) (the )?(first )?(comments?|replies|reply|thread)\b"
    r"|\b(first|1st) (comment|reply)\b"
    r"|" + _NOUN_ES + r"[^.\n]{0,30}comentario|primer comentario"
    r"|" + _NOUN_TR + r"[^.\n]{0,30}\byorum|\bilk yorum"
    r"|(プロンプト|リンク)[^。\n]{0,20}(コメント|リプ)|(提示词|链接)[^。\n]{0,20}评论", re.I)

def raw_text(raw):
    return raw.split("# Thread", 1)[-1]

def fm(raw):
    d = {}
    for l in raw.split("---", 2)[1].splitlines():
        m = re.match(r'^(\w+):\s*"?(.*?)"?\s*$', l)
        if m: d[m.group(1)] = m.group(2)
    return d

def candidates(where):
    if where == "pending":
        files = glob.glob(os.path.join(PENDING, "*.md"))
    else:
        ids = set()
        for p in glob.glob(os.path.join(VAULT, "*.md")):
            m = re.search(r'^tweet_id: "(\d+)"', open(p, encoding="utf-8").read(), re.M)
            if m: ids.add(m.group(1))
        files = [f for f in glob.glob(os.path.join(RAW, "*.md"))
                 if re.search(r'-(\d+)\.md$', f) and re.search(r'-(\d+)\.md$', f).group(1) in ids]
    out = []
    for f in sorted(files):
        raw = open(f, encoding="utf-8").read()
        m = CUES.search(raw_text(raw))
        if m:
            d = fm(raw)
            out.append((d.get("id"), d.get("author"), os.path.basename(f), m.group(0)))
    return out

if __name__ == "__main__":
    cand = candidates(sys.argv[1] if len(sys.argv) > 1 else "pending")
    print(f"candidates: {len(cand)}")
    for c in cand: print(f"  {c[0]} @{c[1]}  [{c[3]}]  {c[2]}")
