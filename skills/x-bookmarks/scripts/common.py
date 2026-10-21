# Shared settings for the x-bookmarks scripts: config loading, paths and localized note headings.
# Config location: the X_BOOKMARKS_CONFIG environment variable, otherwise ~/.x-bookmarks/config.json
# (see config.example.json in the repository root).
import os, re, sys, json, glob

CONFIG_PATH = os.environ.get("X_BOOKMARKS_CONFIG") or os.path.join(os.path.expanduser("~"), ".x-bookmarks", "config.json")

if not os.path.exists(CONFIG_PATH):
    sys.exit(f"!! config not found: {CONFIG_PATH}\n   Run '/x-bookmarks setup' or copy config.example.json there.")
CFG = json.load(open(CONFIG_PATH, encoding="utf-8"))

BASE = os.path.expanduser(CFG["tool_dir"])             # birdmarks output and working folders
ROOT = os.path.expanduser(CFG["vault"])                # Obsidian vault root
VAULT = os.path.join(ROOT, CFG.get("target", "X Bookmarks"))  # where bookmark notes are written
ASSETS = os.path.join(VAULT, "assets")
ARTICLES = os.path.join(VAULT, "Articles")
RAW = os.path.join(BASE, "bookmarks")                  # birdmarks output: READ ONLY
PENDING = os.path.join(BASE, "pending")
PROCESSED = os.path.join(BASE, "processed")
WORK = os.path.join(BASE, "work")
TOPICS_FILE = os.path.join(VAULT, "_topics.md")
LANG = CFG.get("note_language", "en")
KEEP_LANGS = set(CFG.get("keep_languages", [LANG, "en"]))  # other languages are translated to English

HEADINGS = {
    "en": dict(summary="Summary", why="Why it matters", for_you="For you", key_points="Key points",
               images="From the images", links="Links", original="Original text",
               source_lang="Source language", full_article="Full article note:"),
    "tr": dict(summary="Özet", why="Neden değerli", for_you="Senin için", key_points="Önemli noktalar",
               images="Görsellerden", links="Linkler", original="Orijinal metin",
               source_lang="Kaynak dil", full_article="Tam makale notu:"),
}
H = HEADINGS.get(LANG, HEADINGS["en"])

FIELDS = ['title', 'source', 'author', 'date', 'tweet_id', 'x_folder', 'type', 'topics', 'tags', 'related',
          'lang', 'translated', 'has_images', 'value', 'status', 'summary', 'links']
VALUES = ('high', 'medium', 'low')
TYPES = ('tool', 'article', 'idea', 'news', 'tutorial', 'resource-list', 'other')

def topics():
    if not os.path.exists(TOPICS_FILE): return set()
    return set(re.findall(r'^- (\S+)', open(TOPICS_FILE, encoding="utf-8").read(), re.M))

def note_names():
    return {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)}
