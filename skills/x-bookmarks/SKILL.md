---
name: x-bookmarks
description: Downloads your X (Twitter) bookmarks and turns them into organized, searchable Obsidian notes, each with a summary, key points, what the images actually show, and a personal "For you" section on how to use it in your own work. Use when the user says "/x-bookmarks", "process my bookmarks", "add new bookmarks to the vault", "update my X bookmarks", or "/x-bookmarks setup".
---

# X Bookmarks → Obsidian

Bookmarks you save on X are usually never opened again. This skill fixes that: it downloads the new ones,
reads each tweet (thread, linked X article and images included), and writes an Obsidian note that answers
"what is this and what can I do with it?". Claude does the interpretive work (reading, looking at images,
summarizing, translating, the "For you" section); bundled scripts do the mechanical work (frontmatter,
copying the original text verbatim, copying images, moving files, duplicate and broken-link checks), so
nothing gets lost or shortened.

Modes:
- **Setup** (`/x-bookmarks setup`): first-time configuration.
- **Normal** (`/x-bookmarks`): download new bookmarks, filter, convert, write to the vault.
  "without downloading" / "skip download" → only process what is already pending.

## Paths

All paths come from the config file: `$X_BOOKMARKS_CONFIG`, otherwise `~/.x-bookmarks/config.json`.
Read it first. If it does not exist, run **Setup**.

| Key | Meaning |
|---|---|
| `tool_dir` | Folder holding birdmarks and its working folders (below) |
| `birdmarks_exe` | Optional; default `tool_dir/birdmarks-win-x64.exe` |
| `vault` | Obsidian vault root |
| `target` | Bookmark notes folder, relative to the vault (e.g. `Resources/X Bookmarks`) |
| `note_language` | Language the notes are written in (`en`, `tr`, ... ; headings exist for `en` and `tr`) |
| `keep_languages` | Content in these languages is kept as is; anything else is translated to English. Default: `[note_language, "en"]` |
| `x_folders` | Only bookmarks in these X bookmark folders are processed; `[]` = all |
| `cookie_source` | Browser birdmarks reads your X login from: `firefox`, `chrome`, `safari` |

Inside `tool_dir`:
- `bookmarks\`, `bookmarks\assets\`, `bookmarks\articles\`: raw birdmarks output. **READ ONLY: never change, delete or move anything here.**
- `pending\`: to be processed · `processed\`: done · `work\`: per-run data files · `seen.txt`: sync state

Inside the target folder: notes at the root, `Articles\`, `assets\`, the topic dictionary `_topics.md`,
the user profile `_profile.md`.

Helper scripts are in the `scripts\` folder next to this SKILL.md (see "Tools"). Always run Python as
`python -I -X utf8` (without `-X utf8` non-ASCII output fails on Windows).

## Setup

1. Ask the user (one short question at a time, offer sensible defaults): vault path, target folder inside
   the vault, note language, which X bookmark folders to process (or all), which browser they are logged
   into X with, and where birdmarks lives (`tool_dir`). If they don't have birdmarks yet, point them to
   the README's install section.
2. Write `~/.x-bookmarks/config.json` (format: `templates\config.example.json` next to this SKILL.md).
3. Create the target folder with `Articles\` and `assets\`.
4. **Profile:** If `_profile.md` doesn't exist, copy `templates\_profile.md` (next to this SKILL.md)
   into the target folder and offer to fill it in together:
   who they are, what they work on, their projects and tools. The "For you" sections are only as good as
   this file.
5. **Backlog:** Ask whether existing bookmarks should be processed (can be many, each costs tokens) or
   skipped. To skip, run the sync script once with `-FirstRun`.
6. Run `bookmarks-sync.ps1 -SkipDownload` once as a smoke test and report the result.

## Tools

| Script | What it does |
|---|---|
| `bookmarks-sync.ps1 [-SkipDownload] [-FirstRun]` | Downloads new bookmarks with birdmarks, copies new ones (from the selected X folders) to `pending\`. |
| `view_pending.py START COUNT` | Prints `pending\` files in order; linked articles on `[ARTICLE]` lines, images on `[IMAGE]` lines. Output can be long: redirect to `work\show.txt` and read that. |
| `build_notes.py DATA.py [dry\|show]` | Writes the note (and article note) for each bookmark in the data file, copies images, moves the source to `processed\`. `dry`/`show` write nothing, they only check. Always fix the warnings (`!!`). |
| `example_data.py` | Data file format with every key (commented). |
| `comment_cues.py pending\|vault` | Lists bookmarks whose text says the real content is in the comments ("prompt in the replies", "link in first comment"). Downloads nothing. |
| `qa.py [HOURS]` | Checks notes written in the last N hours: missing fields, topics outside the dictionary, broken wikilinks, missing images, HTML entities, duplicate `tweet_id`; prints the counts for the report. |

## Preparation (once, at the start)

1. **Profile:** Read `_profile.md`. If it's missing, tell the user and keep "For you" sections general.
2. **The user's work:** List note names in the vault's project/area folders. In "For you" you may link
   them with `[[wikilinks]]`.
3. **Topic dictionary:** Read `_topics.md` if it exists. Otherwise collect `tags` and `topics` values from
   frontmatter across the vault (Grep), build a starting list of 10-20 frequent ones and write it as
   `_topics.md` (one per line: `- topic-name`). Use this list for `topics` first; if nothing fits you may
   open a new topic, but add it to the file and list it separately in the report.

## Normal mode

### 1. Download and filter
Unless the user said "without downloading":
```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<skill dir>\scripts\bookmarks-sync.ps1"
```
Otherwise add `-SkipDownload`. If there's a rate-limit warning, mention it briefly and continue with what
arrived. If `pending\` is empty, say "No new bookmarks" and stop.

Downloading can take long (with folder filtering ~90 bookmarks take 15-25 min because the folder map is
rebuilt each run): run it **in the background** and do the preparation steps meanwhile. When done, put
the `New / Other folder / No folder info yet` lines and any `Error downloading media` warnings in the
report. `Found article from tweet <id>: <title>` lines matter too: for bookmarks whose raw file only has an
`x.com/i/article/...` link, the article is saved under `bookmarks\articles\` with that title; match them
using these lines.

### 2. Processing loop
0. Run `comment_cues.py pending`. birdmarks usually brings the author's own reply under the tweet as part
   of the thread; while reading, check whether the content really arrived. If not, end the Summary with
   a note that the author says the content is in the comments and it is missing, and list these
   bookmarks with links in the report (the user can check them in the browser).
1. Show 5-7 bookmarks with `view_pending.py` and read them; open every `[IMAGE]` with Read and actually
   look at it, read `[ARTICLE]` articles (if long, the beginning and section headings).
2. Write `work\data_NN.py` for this group (format: `example_data.py`). All rules below apply.
3. Check with `build_notes.py data_NN.py dry`, fix warnings, then run it without an argument to write.
4. Go to the next group; give a short status every ~20 notes. With more than 20 files, keep going
   without stopping.
5. When all are done, run `qa.py`; fix until problems are 0, and write the report from `qa.py` numbers.

If the scripts don't work, apply the rules below by hand.

### 3. Rules for each pending file
1. **Duplicates:** If the target already has the same `tweet_id`, don't write; move the file to
   `processed\` and count it as a duplicate (`build_notes.py` does this).
2. **Read:** Read the file. If it links `articles\...`, read the article in `bookmarks\articles\` too.
3. **Images:** Open every image referenced as `assets\...` from `bookmarks\assets\` with Read and really
   look at it. Copy images that carry information (text, table, diagram, code, screenshot, sample
   image/video frame) via `copy`. Don't copy decorative images or memes.
4. **Language:** Determine the language of the main content → `lang`.
   - In `keep_languages`: stays as is.
   - Any other language: translate the content to **English, understanding the context** (by meaning, not
     word for word; technical terms, product names, code, URLs, @handles and hashtags stay unchanged).
     The script sets `translated: true` and keeps the source text in a collapsed callout.
5. **Article:** If there's an article, it becomes a separate note under `Articles\` (same language rule)
   linked from the bookmark note.
   - If the article comes from a quoted tweet, `author` and `source` must be the article's **own** author
     and tweet, not the person who shared the bookmark.
   - Several bookmarks can quote the same article: write the article note once, link the others to it.

## Note schema

File name: `YYYY-MM-DD-short-title.md` (tweet date; lowercase, hyphens, ASCII only, at most 6 words).
If the name exists, add `-2`.

```markdown
---
title: "..."
source: https://x.com/...
author: handle
date: YYYY-MM-DD
tweet_id: "..."
x_folder: "..."
type: tool | article | idea | news | tutorial | resource-list | other
topics: [at most 3, from the dictionary]
tags: [at most 5, lowercase, hyphenated, no #]
related: [related projects from the profile or vault, otherwise empty]
lang: en | tr | es | ...
translated: false
has_images: false
value: high | medium | low
status: inbox
summary: "..."
links: []
---
```

Field rules:
- `title` and `summary` always in double quotes; remove double quotes inside them.
- `x_folder`: copied verbatim from the raw file's `folder:` value.
- `links`: every external link in the tweet and in quoted (nested) tweets, plus quoted tweet URLs. The
  expanded URL, never t.co.
- `has_images`: `true` if the note has at least one information-carrying image.
- `value`: `high` = concrete information, method, tool, resource; `medium` = useful but general;
  `low` = motivation, opinion, pointer, one-line news.

### Body (high / medium)
Section headings are written in `note_language` by the script; the texts you write go in the same language.
```markdown
## Summary
2-3 sentences.

## Why it matters
One sentence.

## For you
(Rules below.)

## Key points
- ...

## From the images
(Only if there is an information-carrying image) What is really visible in the image, briefly. Then:
![[file-name.jpg]]

## Links
- [Title](url) — one-line description
(Skip this section if there are no external links.)

## Original text
> verbatim tweet / thread text (English translation if translated)

> [!quote]- Source language (xx)
> (Only if translated) the original text verbatim
```

### Body (low)
`Summary` (1-2 sentences), `For you` (short version) and `Original text` (with the source-language
callout if translated).

## The "For you" section

Goal: when the user opens this note, the answer to "what do I do with this?" is already there. Write in
`note_language`, friendly but clear, addressing the user directly ("you could try..."). Base it on
`_profile.md` and the user's work in the vault.

**high / medium notes** (about 120-250 words in total):
1. A short intro paragraph: which of the user's work does this touch, and why?
2. `**What you can do:**` 2-4 items. Concrete, actionable steps, with which tool where possible. If useful,
   show how the prompt or method in the bookmark adapts to the user's own work.
3. `**Where it helps:**` Related projects/skills; with `[[wikilink]]` if the vault has a note. Put the same
   names in `related`.
4. `**First step:**` One thing that can be done in 15-30 minutes.

**low notes:** 1-3 sentences. If there's a useful side, say it; otherwise say plainly that there's no
direct use.

Rules:
- **Don't force connections.** If the content isn't really related to the user's work, say so honestly;
  don't try to tie every note to a project. Mention general value if there is any.
- Don't invent projects or tools that aren't in the profile or vault.
- Don't present the bookmark's claims as verified here either; be cautious with paid or risky suggestions
  (e.g. financial "opportunities").

## Hard rules

- No making things up. Only write what is really in the file and the images. If unsure, leave it empty.
- Don't state claims as facts; attribute them ("according to the post", "the author says").
- If tweet and image contradict, trust the image. Viral tweets often attribute things to someone famous
  ("Karpathy's prompt", "Apple's motion lead's formula"); if a footnote in the image ("Not written or
  endorsed by...") or a correction in the thread refutes it, correct it in the Summary.
- Mark revenue, view and star counts as "the author's claim"; if the tweet's number differs from repo data
  in the raw file, say so.
- If the text mentions a video, article or tool without a link, end the Summary with a note that the
  mentioned resource's link is not in the text.
- Never shorten or change the original text. Keep backticks around hashtags. Don't put image lines
  (`![](assets\...)`) in the Original text.
- Only use `[[wikilinks]]` for notes that REALLY exist in the vault (and article notes you created).
- Never write to `bookmarks\`; never delete or move anything from there.
- Don't write notes outside the target folder in the vault (except `_topics.md` and `_profile.md` inside it).

## Report

At the end give a short summary: how many notes were written, how many translated (from which
languages), how many are `low` value, duplicates, bookmarks whose content is said to be in the comments,
new topics opened, errors.
