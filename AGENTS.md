# Notes for developers and AI coding assistants

A theme for sites on [hotglue.me](https://hotglue.me): two files that a hotglue user pastes into
the `<head>` and `<body>` boxes at `https://<username>.hotglue.me/code`. Start with README.md,
which is written for the artists who use it. (CLAUDE.md only points Claude Code to this file.)

## Rules

- **Python only through uv**, never the system's `python` or `pip`: `uv run <command>` for
  everything in this project (it uses the project's `.venv` and the locked versions in
  uv.lock), `uv run --with <package> python ...` for a one-off extra package, `uv add --dev`
  to add one for good. CI does the same.
- **`head.html` and `body.html` are the product and the source.** No build step, no
  minifying, no splitting into other files: what is in the repo is exactly what gets pasted.
  Plain CSS and one vanilla JS script, no libraries.
- **Every change to either file is a release with a new version:** the date of the change
  on line 2 of `body.html` (`PORTFOLIO THEME FOR HOTGLUE.ME · version YYYY-MM-DD`; a second or
  third release on the same day adds `-2`, `-3`). CI checks it changed. A date tells artists
  at a glance whether theirs is older, and needs no release process.
- **Write for artists** in README.md, the manual (the comment at the top of
  `body.html`) and the settings comments in `head.html`: plain, short sentences, no developer
  terms. The manual travels with the files, so it must stay accurate and complete; change it
  in the same commit as the behaviour. Developer notes go at the top of the `<script>`.
- **Keep what artists carry from one version to the next stable:** the menu block's format
  (`<script type="text/plain" id="hpt-menu">`, first line the name, then `Label = page`) and
  the names of the settings at the top of head.html. Keep the default settings neutral.
- Our classes, ids and CSS variables start with `hpt-` / `--hpt-`, except those settings.
  hotglue's own CSS and JS share the page.
- The script must never stop the page from working: each part runs in `step()`, which logs
  `portfolio theme, <step>:` errors. Tests that take the `errors` fixture fail on them.
- In hotglue's editor, change nothing the artist could save by accident: hotglue saves each
  object's position, size and content, so only add classes/outlines/`title`, never move or
  resize objects there.

## Adding or changing a feature

1. Add the case to `tests/hotglue/pages.py` and a failing test (`tests/test_*.py`, by area).
2. Change `head.html` / `body.html`; keep the step list and the "relies on" list at the top of
   the script current.
3. Update the manual in `body.html` and, if artists notice, README.md.
4. New version (see Rules). Run the tests in all three browsers.

## Reviews

To review the repository, a branch or a pull request, follow
`.agents/skills/review-repo/SKILL.md`: four adversarial reviews (bugs and security, first-look
clarity, clean code, simplicity), then check and fix. It is an [Agent Skills](https://agentskills.io)
skill, so coding agents that support the standard find it on their own (`.claude/skills` links
to `.agents/skills` for Claude Code); others, and people, can read it as a checklist.

## hotglue versions

hotglue.me runs the open-source [hotglue2](https://github.com/k0a1a/hotglue2), branch
`master`. A rewrite, called hotglue-ng here, is in development on `ng-dev`; its demo at
[hotglue.me/ng](https://www.hotglue.me/ng/) runs that branch.
The `dev` branch sits in between: a note once in hotglue2's repository said hotglue.me's server
follows it, so it is likely what hotglue.me gets next. The theme must work on all three. The
script tells hotglue-ng apart by `<meta name="generator" content="hotglue-ng">` (`ng` in
body.html). hotglue-ng's own elements use the prefix `hg-`: never use it for ours.

What hotglue-ng changes, and how the theme handles it:

| hotglue-ng | Theme |
|---|---|
| Its own phone view ("guided" view, [`js/mobile-guided.js`](https://github.com/k0a1a/hotglue2/blob/ng-dev/js/mobile-guided.js)): zooms into a canvas holding all objects, the menu included | Switched off with `guided=0` in the address while the page loads (step 0), so the theme's phone layout shows. That file calls the switch testing tooling: if it goes away, the "hotglue-changed" run against the newest ng-dev commit fails. |
| "Centered" pages: objects in a fixed-width box (`#hg-centered-wrapper`) in the middle of the window | The box is centred in wide windows, shrinks with its objects in narrower ones, and joins the phone column. |
| Objects in reading order in the page, which the artist can change | Used as is for the phone column and the arrow keys (on hotglue.me the theme sorts by position). |
| Photos always `<img>`, also in the editor; tiled images removed | hotglue.me can tile an image as a pattern, which the theme hides on phones. hotglue-ng can tile a background on any object instead; those stay visible on phones. |
| The editor redraws objects (undo) and shows the selection as an outline | The red box re-checks on every change to the page, and its outline steps aside while an object is selected. |

Not looked at yet: hotglue-ng's custom code per object (its "code panel"), audio objects,
rotated objects, and page background videos.

Separately: hotglue2's `dev` branch, at the pinned commit, throws a JavaScript error in its
own editor when a page opens, with or without the theme (`Unexpected token '<'`); the tests
ignore errors from hotglue's own scripts.

The tests run every case on all three branches, pinned to commits in `tests/conftest.py`
(`VERSIONS`). What body.html relies on in hotglue's pages is listed at the top of its script;
if you add a reliance, add it there, to the table above if it's specific to hotglue-ng, and
to `tests/test_live.py` if a live page can show it.

### When hotglue.me changes

Run the "hotglue-changed" CI job by hand (Actions tab, "Run workflow") to check: it fails
when hotglue.me or its hotglue-ng demo no longer runs the pinned commit (the message says
which branch it matches now), or when the newest commit of a branch fails the tests. Then:

1. Run `HOTGLUE_LATEST=1 uv run pytest` and fix what fails (a new test case first).
2. Pin the new commits in `VERSIONS`, with their dates.
3. If hotglue.me now runs another branch, change the branch for the hotglue.me check in
   `tests/test_live.py`, and this section.
4. Code only for a branch nobody runs any more can go (the hotglue.me-only parts are
   commented as such in body.html).
5. New version if `head.html` or `body.html` changed.

## Tests

Needs Docker: `tests/hotglue/` runs the real hotglue2 PHP code in a container, creates the
test site (`tests/hotglue/pages.py`) through hotglue's own JSON API, then installs our two
files as the /code page does. Tests use real hotglue output, never hand-copied markup, so
they notice when hotglue renders differently. hotglue2 is cloned once into
`~/.cache/hotglue-portfolio-theme`.

```
uv run playwright install chromium          # once (also firefox, webkit)
uv run pytest                               # chromium; add --browser firefox --browser webkit
HOTGLUE_LATEST=1 uv run pytest              # against the newest commit of each hotglue branch
HOTGLUE_LIVE=1 uv run pytest tests/test_live.py   # do hotglue.me and its demo run the pinned commits?
uv run tests/serve.py [master|dev|ng-dev]   # the test site in a browser, to look around
uv run ruff check tests && uv run ruff format tests
```

The live tests read hotglue.me's homepage (itself a hotglue page) and its hotglue-ng demo.

If Playwright's browsers don't run on your system (WebKit needs Ubuntu 24.04's libraries),
use the official image as a browser server; its version must match `playwright` in uv.lock:

```
docker run -d --rm --name pw-server --network host --init mcr.microsoft.com/playwright/python:v1.63.0-noble \
  sh -c "pip install -q --break-system-packages playwright==1.63.0 && playwright run-server --port 3123 --host 127.0.0.1"
PLAYWRIGHT_SERVER=ws://127.0.0.1:3123/ uv run pytest --browser webkit
```

Layout bugs depend on the window size: test laptop widths (1280-1512), big monitors (2560+)
and phones (390, 800); the common sizes are in `tests/helpers.py`. The screenshots in
`docs/screenshots/` were taken from a local hotglue with placeholder pictures; retake them
when the look changes.
