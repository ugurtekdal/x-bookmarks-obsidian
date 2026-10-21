# Example data file for build_notes.py. On each run write work\data_01.py, data_02.py ... inside the
# tool folder (groups of 5-7 bookmarks). Key: the file name inside pending\.
#
# Required: file, title, summary, type, topics, value, overview, for_you   (high/medium notes also: why)
# Optional:
#   tags, related (projects from the profile / vault), links (frontmatter links: expanded external links
#     + quoted tweet URLs)
#   key_points, links_section (Links section), images (From the images text) + copy (image files to copy)
#   lang (default en). If lang is not in keep_languages, give either trans (the whole translated body)
#     or tmap [(source, translation), ...].
#   article=dict(src=file name inside bookmarks\articles\, name=note name under Articles\, title, date,
#                author=the ARTICLE's author, source=the article's tweet URL, lang, trans)
#     author/source fall back to the bookmark's author; always give them for quoted articles.
# Notes: low notes get no why/key_points/images/links_section (has_images becomes false).
#        Use \" for double quotes inside text. [[wikilinks]] in for_you must exist in the vault.
#        Section texts are written in note_language from the config.
D = {
"2026-10-17-exampleauthor-1234567890123456789.md": dict(
 file="2026-10-17-short-title-six-words-max",
 title="Note title",
 summary="One-sentence summary.",
 type="tutorial", topics=["video-generation", "prompt-engineering"], tags=["tag-1", "tag-2"],
 related=["My YouTube Channel"], lang="en", value="high",
 links=["https://github.com/example/repo", "https://x.com/example/status/111"],
 copy=["HUxxxxxxxxxxxx.jpg"],
 article=dict(src="Article-File-Name.md", name="2026-10-16-article-short-name", title="Article title",
              date="2026-10-16", author="articleauthor", source="https://x.com/articleauthor/status/111"),
 overview="2-3 sentences, attributed (according to the author...).",
 why="One sentence.",
 for_you="""Intro paragraph.

**What you can do:**
- ...

**Where it helps:** [[My YouTube Channel]].

**First step:** ... (15 min).""",
 key_points="""- ...""",
 images="What is actually visible in the image.",
 links_section="- [Title](https://github.com/example/repo) — one-line description",
),
}
