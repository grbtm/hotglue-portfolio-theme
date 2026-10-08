"""hotglue.me itself: do its sites and its demo of hotglue-ng still run the hotglue versions
the other tests use?

Runs only with HOTGLUE_LIVE=1 (the "hotglue-changed" CI job, run by hand): it depends on the
internet and on live sites.
A failure here means hotglue.me changed: see AGENTS.md, "When hotglue.me changes".
"""

import os
import re
import subprocess
import urllib.request

import pytest
from conftest import VERSIONS
from hotglue.server import checkout

# hotglue.me's own homepage is a hotglue page too (with photos), on the same code as its users' sites
SITE = "https://hotglue.me/"
NG_DEMO = "https://www.hotglue.me/ng/"  # hotglue-ng's demo

pytestmark = pytest.mark.skipif(not os.environ.get("HOTGLUE_LIVE"), reason="set HOTGLUE_LIVE=1")


def fetch(path, site=SITE):
    request = urllib.request.Request(site + path, headers={"User-Agent": "hotglue-portfolio-theme tests"})
    return urllib.request.urlopen(request, timeout=20).read()


@pytest.mark.parametrize(("live_site", "branch"), [(SITE, "master"), (NG_DEMO, "ng-dev")])
@pytest.mark.parametrize("path", ["js/edit.js", "css/edit.css", "css/main.css", "js/glue.js"])
def test_runs_the_tested_version(live_site, branch, path):
    live = fetch(path, live_site)
    clone, sha = checkout(VERSIONS[branch])
    if live == git_show(clone, sha, path):
        return
    # Which branch does it run now? The newest commit of each, for a start.
    matches = [b for b in VERSIONS if live == git_show(clone, checkout(b)[1], path)]
    pytest.fail(
        f"{live_site}{path} is no longer hotglue2 {branch} at {sha[:8]}; it matches the newest "
        f"commit of: {', '.join(matches) or 'no branch'}. See AGENTS.md, 'When hotglue.me changes'."
    )


def git_show(clone, sha, path):
    return subprocess.run(["git", "-C", str(clone), "show", f"{sha}:{path}"], check=True, capture_output=True).stdout


def test_published_markup_is_as_expected():
    """The assumptions listed in body.html's developer notes, on a live page."""
    html = fetch("").decode()
    assert re.search(r'<body id="[a-z0-9_-]+\.head"', html)
    objects = re.findall(r'<div id="[a-z0-9_-]+\.head\.\d+" class="([^"]*)" style="([^"]*)"', html)
    assert objects, "no objects found"
    for classes, style in objects:
        assert "object" in classes.split()
        for prop in ("left", "top", "width", "height"):
            assert re.search(rf"(^|; ){prop}: -?[\d.]+px", style), (prop, style)
    assert re.search(r'class="image[^"]*object"[^>]*>\s*<img ', html), "photos are no longer <img>"
