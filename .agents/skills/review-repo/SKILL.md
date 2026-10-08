---
name: review-repo
description: Adversarial review of this repository (or of a change to it) in four areas - bugs and security, first-look clarity, clean code, simplicity - then verify each finding and fix the real ones. Use when asked to review the repo, a branch or a pull request, or before a release.
---

# Reviewing this repository

Four separate reviews, each by a reviewer who only reports, then one person (or agent) who
checks every finding and fixes the real ones. Separate reviewers find more than one reviewer
doing everything, and reviewers who don't edit can't hide a finding by "fixing" it in passing.

## 1. Run the four reviews

If you can run sub-agents, run one per area in parallel, each with the area's text below plus
the shared instructions. Otherwise do the areas one after another, starting fresh each time.

Shared instructions for every reviewer:

- Read README.md and AGENTS.md first, then every file in scope (all files for a full review;
  the diff plus whatever it touches for a change). Skip `.venv/`.
- Do not change files in the repository. Scratch files and probes go in a temporary
  directory outside it.
- Be concrete: `file:line`, what is wrong, a failure scenario (input -> wrong result), and the
  smallest fix. Say whether you verified it (how) or reasoned it.
- Verify where you can: `uv run pytest` runs the suite against real hotglue in Docker
  (AGENTS.md, "Tests"); `tests/hotglue/server.py` starts a hotglue for a probe script. Remove
  any Docker containers you start.
- Report only your area, most important first, and list what you checked and found fine.

### Bugs and security

Try to break it. In `body.html`: the artist's menu lines (any text, pasted addresses, other
schemes such as `javascript:`), captions copied into the overlay, the address and history
handling (the `guided=0` switch for hotglue-ng, the overlay's history entry, `#<number>`
links), pages without photos, objects left of the menu or without sizes, window widths at the
800px boundary (also fractional widths from browser zoom), browsers without CSS `zoom`, and the
editor's MutationObserver. In `head.html`: anything that breaks hotglue's editor or page. In
`tests/`: assertions that pass for the wrong reason, timing, cleanup after failures. In
`.github/workflows/`: permissions, injection through `github` context values, the
version-date check.

### First-look clarity

Read as an experienced engineer who has never heard of the project. Find: references to how
the repository came about (conversations, earlier repositories, private sites, people);
statements that are stale or will go stale without anything keeping them fresh; terms used
before or without being explained; contradictions between README.md, AGENTS.md, the manual and
developer notes in `body.html`, and the code; claims nothing in the repo backs. For any fact,
name or path mentioned more than once (a CI job's name or trigger, a version number, a file
path, a test count), grep for every occurrence and confirm they still agree: a changed detail
tends to get fixed where it was changed and left stale everywhere else it was repeated.
Check that the README's opening is right and understandable for a non-technical artist, and
that the manual in `body.html` stays in plain language.

### Clean code

Naming, function size, duplication (and which duplication the paste-in rule makes
unavoidable), magic numbers, comments that say what instead of why or are wrong, dead code,
consistency within each language, test structure. Respect the constraints in AGENTS.md: no
build step, single paste-ready files, plain JS and CSS.

### Simplicity

Is each piece of code, CSS rule, test, workflow step and doc section needed, and as simple
as it can be? Propose removals and simpler versions; check them on a copy of the repository
with the tests, and say honestly what each would lose. Also list what looks complex but is
justified.

## 2. Check, fix, prove

- Check every finding yourself before acting on it; reviewers can be wrong. Note which you
  reject and why.
- Fix bugs with a test first (AGENTS.md: add the case to `tests/hotglue/pages.py`, at the
  window sizes where it shows).
- Prove each new test can fail: break the fix on purpose, see the test fail, restore it.
- Run the tests in all three browsers, and `HOTGLUE_LIVE=1` and `HOTGLUE_LATEST=1` runs if
  hotglue-facing code changed.
- Changed `head.html` or `body.html`: new version (AGENTS.md).
- Report what was fixed, what was rejected and why, and what is left open.
