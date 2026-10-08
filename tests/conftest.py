"""Test setup: a real hotglue per version, filled with the test site, with our files installed.

Every test runs once per hotglue version (VERSIONS) and once per browser (pytest-playwright's
--browser option; CI runs chromium, firefox and webkit). Set HOTGLUE_LATEST=1 to test the
newest commit of each branch instead of the pinned one.
"""

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from hotglue.pages import MENU, PAGE, PAGES
from hotglue.server import PASSWORD, USER, Hotglue, build_image

ROOT = Path(__file__).parent.parent

# hotglue2 versions to test (branch: commit). hotglue.me runs master (checked by test_live.py,
# run by hand via the "hotglue-changed" CI job). Its server follows dev according to a note
# once in hotglue2's repository
# (REPOS-AND-BRANCHES.md, removed after commit bd17e0c), so dev is likely what it gets next.
# ng-dev is the rewrite in development ("hotglue-ng"). Pinned so a change in hotglue can't
# fail a test by surprise; bump a commit after checking that the tests pass with
# HOTGLUE_LATEST=1.
VERSIONS = {
    "master": "91ae6133fce93175cb21652bcc4996dfd271974b",  # 2026-05-30
    "dev": "5ab1c26749e4f19c521f3e4460e020704fd23ca5",  # 2026-08-30; its editor has a JS error
    "ng-dev": "3e734bbf689c14cc88376bbd394e0a87f4806e54",  # 2026-10-07
}


def with_menu(body, menu):
    """body.html with the artist's name and menu lines replaced by `menu`."""
    start = '<script type="text/plain" id="hpt-menu">\n'
    # a function as replacement, so backslashes in `menu` stay as they are
    return re.sub(re.escape(start) + r".*?(?=</script>)", lambda _: start + menu, body, count=1, flags=re.DOTALL)


class Site:
    """The running test site in one hotglue version."""

    def __init__(self, hotglue, names):
        self.hotglue = hotglue
        self.url = hotglue.url
        self.names = names  # {page name: {object key: hotglue object id}}

    def view(self, page):
        return self.url + "?" + page

    def edit(self, page):
        return self.url + "?" + page + "/edit"

    def object_id(self, page, key):
        return self.names[page][key]

    def number(self, page, key):
        """The object's number, which is also its photo's #link in the overlay."""
        return self.object_id(page, key).rsplit(".", 1)[1]

    def locator(self, browser_page, page, key):
        # hotglue's ids contain dots, so "#id" selectors don't work
        return browser_page.locator(f'[id="{self.object_id(page, key)}"]')

    def obj(self, page, key):
        return next(o for o in PAGE[page].objects if o.key == key)


def start_site(ref, workdir):
    """A running hotglue at `ref` with the test site and our files installed (stop it with
    site.hotglue.stop())."""
    build_image()
    hotglue = Hotglue(ref, workdir)
    try:
        hotglue.start()
        names = {page.name: hotglue.add_page(page) for page in PAGES}
        body = with_menu((ROOT / "body.html").read_text(), MENU.format(site=hotglue.url))
        hotglue.set_code((ROOT / "head.html").read_text(), body)
    except BaseException:
        hotglue.stop()
        raise
    return Site(hotglue, names)


@pytest.fixture(scope="session")
def sites(tmp_path_factory):
    """One running site per hotglue version, started when first needed and kept for the whole
    run (pytest may reorder parametrized tests, which would otherwise restart them)."""
    running = {}

    def get(version):
        if version not in running:
            ref = version if os.environ.get("HOTGLUE_LATEST") else VERSIONS[version]
            running[version] = start_site(ref, tmp_path_factory.mktemp(version))
        return running[version]

    yield get
    for site in running.values():
        site.hotglue.stop()


@pytest.fixture(params=list(VERSIONS))
def site(request, sites):
    return sites(request.param)


@pytest.fixture
def browser_context_args(browser_context_args):
    # the editor asks for hotglue's password
    return {**browser_context_args, "http_credentials": {"username": USER, "password": PASSWORD}}


@pytest.fixture
def errors(page):
    """Errors from our script: what its step() logs ("portfolio theme, <step>: ..."), and
    uncaught errors raised in the page's inline scripts (ours is one; their stack lines read
    "<site>/?<page>:<line>"). Errors in hotglue's own script files are not counted: hotglue2's
    dev branch has one in its editor even without our code."""
    found = []

    def on_console(message):
        if message.type == "error" and "portfolio theme" in message.text:
            found.append(message.text)

    def on_error(error):
        parts = urlsplit(page.url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if re.search(re.escape(origin) + r"/(\?[^\s:]*)?:\d+", error.stack or ""):
            found.append(f"{error}\n{error.stack}")

    page.on("console", on_console)
    page.on("pageerror", on_error)
    return found


@pytest.fixture(scope="session")
def connect_options():
    """PLAYWRIGHT_SERVER=ws://host:port/: use the browsers of a running Playwright server, for
    systems Playwright's browsers don't run on (see AGENTS.md)."""
    url = os.environ.get("PLAYWRIGHT_SERVER")
    return {"endpoint": url} if url else None
