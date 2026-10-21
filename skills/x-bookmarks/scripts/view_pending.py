# Prints the bookmarks in pending\ one after another (for reading).
# Usage: python -I -X utf8 view_pending.py START COUNT > work\show.txt
# Output can be long; write it to a file and read that. Linked articles are listed on [ARTICLE] lines,
# images on [IMAGE] lines.
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PENDING, RAW

files = sorted(f for f in os.listdir(PENDING) if f.endswith(".md"))
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
count = int(sys.argv[2]) if len(sys.argv) > 2 else 6
print(f"# pending total: {len(files)}")
for i, f in enumerate(files[start:start + count], start):
    t = open(os.path.join(PENDING, f), encoding="utf-8").read()
    print(f"\n######## [{i}] {f}")
    print(t)
    for a in re.findall(r'\]\((articles[/\\][^)]+)\)', t):
        p = os.path.join(RAW, *re.split(r'[/\\]', a))
        size = os.path.getsize(p) if os.path.exists(p) else 0
        print(f"   [ARTICLE] {a} exists={os.path.exists(p)} size={size}")
    for img in re.findall(r'\(assets[/\\]([^)]+\.(?:jpg|jpeg|png|webp|gif))\)', t, re.I):
        print(f"   [IMAGE] {os.path.join(RAW, 'assets', img)}")
