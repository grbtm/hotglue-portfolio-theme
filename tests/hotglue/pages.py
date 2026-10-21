"""The test site: pages and objects as an artist would place them in hotglue's editor.

Positions and sizes are in px, as hotglue stores them. Each page covers cases that matter for
body.html; keep the comments saying which.
"""

from dataclasses import dataclass


@dataclass
class Obj:
    key: str  # our name for it in tests (hotglue names objects <page>.head.<number>)
    kind: str  # "image" or "text"
    left: int
    top: int
    width: int
    height: int
    text: str = ""  # text objects: their HTML content
    colour: tuple = (120, 140, 120)  # images: a solid colour
    tiled: bool = False  # images: a tiled background pattern instead of a photo (hotglue.me)
    link: str = ""  # "make the object a link": the page it links to

    @property
    def caption(self):
        """A caption's text as the overlay shows it: without the ~ and the HTML tags."""
        return self.text.lstrip("~").replace("<b>", "").replace("</b>", "").strip()


@dataclass
class Page:
    name: str
    objects: list
    centered_width: int = 0  # hotglue-ng only: a "centered" page, its box this many px wide
    reading_order: tuple = ()  # photo keys, top to bottom: the phone column and the arrow keys


def image(key, left, top, width, height, **kw):
    return Obj(key, "image", left, top, width, height, **kw)


def text(key, left, top, width, height, content):
    return Obj(key, "text", left, top, width, height, text=content)


PAGES = [
    # Laid out on a big monitor: reaches 2654px, far wider than a 1280-1512px laptop window.
    # Created in a different order than they are read, as artists do.
    Page(
        "start",
        [
            image("tall", 653, 232, 791, 1154, colour=(200, 120, 90)),
            image("wide", 1516, 402, 972, 429, colour=(90, 120, 200)),
            image("right", 2127, 952, 527, 332, colour=(90, 180, 120)),
            image("middle", 1479, 866, 534, 696, colour=(180, 170, 80)),
            # captions 9px under "wide", 4px under "tall", 11px under "middle"
            text("cap-wide", 1863, 840, 100, 100, "~Irregularities #001, 2026. Canvas on sunlight"),
            text("cap-tall", 942, 1390, 100, 100, "~Shades of white #001. 2026, photography."),
            text("cap-middle", 1686, 1573, 100, 100, "~Irregularities 002, 2026. <b>Lorem</b> ipsum."),
        ],
        reading_order=("tall", "wide", "middle", "right"),
    ),
    # Fits a laptop window: must not be shrunk. Also a linked photo (no overlay, its ~ text
    # stays visible), a tiled background pattern, a ~ text too far below to count, and a
    # text with a link in it.
    Page(
        "painting",
        [
            image("p1", 300, 60, 400, 300, colour=(200, 60, 60)),
            text("p1-cap", 300, 370, 400, 40, "~Red, 2024, oil on canvas"),
            image("p2", 760, 60, 300, 400, colour=(60, 60, 200)),
            text("p2-far", 760, 600, 300, 40, "~Too far below to count"),
            image("linked", 300, 500, 300, 200, colour=(60, 160, 60), link="sculpture"),
            text("linked-cap", 300, 710, 300, 40, "~Under a linked photo"),
            image("pattern", 1100, 60, 100, 600, colour=(230, 230, 200), tiled=True),
            text("words", 760, 700, 300, 60, 'Some text with <a href="?contact">a link</a>.'),
        ],
    ),
    # A page under a menu page (rule 3): highlights "Exhibitions" in the menu.
    Page(
        "exhibitions-2025-example-show",
        [
            text("title", 300, 60, 400, 40, "Example show, 2025"),
            image("show", 300, 120, 500, 300, colour=(150, 100, 150)),
        ],
    ),
    # A year under a menu page, listed in the menu (an indented line under "Painting")
    Page(
        "painting-2026",
        [
            image("y1", 300, 60, 400, 300, colour=(200, 160, 60)),
            text("y1-cap", 300, 370, 400, 40, "~Yellow, 2026, oil on canvas"),
        ],
    ),
    # A menu page
    Page(
        "exhibitions",
        [
            text("intro", 300, 60, 400, 40, "Exhibitions"),
        ],
    ),
    # hotglue-ng's "centered" mode: objects inside a 1200px box in the middle of the window.
    # (On hotglue.me, which has no such mode, an ordinary page.)
    Page(
        "sculpture",
        [
            image("s1", 300, 60, 500, 400, colour=(120, 120, 120)),
            image("s2", 850, 60, 300, 500, colour=(80, 80, 80)),
            text("s1-cap", 300, 470, 500, 40, "~Stone, 2023"),
        ],
        centered_width=1200,
        reading_order=("s1", "s2"),
    ),
    # Not in the menu and not under a menu page: reported in the editor. Also one object too
    # close to the menu (rule 1).
    Page(
        "loose-page",
        [
            text("too-close", 100, 60, 300, 40, "Under the menu"),
        ],
    ),
]

PAGE = {page.name: page for page in PAGES}

# The menu block used in the tests (what the artist edits at the top of body.html). {site} is
# the test site's address: the last lines are pasted addresses, as artists copy them.
# Indented lines are years under a menu page (one with a tab); "Reels" is indented under
# another website, so it never shows and is reported.
MENU = """Test Artist
About = about
Exhibitions = exhibitions
Painting = painting
  2026 = painting-2026
	2025 = painting-2025
Sculpture = sculpture
Contact = contact
Instagram = https://www.instagram.com/example
  Reels = reels
This line has no equals sign
Pasted = {site}?painting&guided=0
Encoded = {site}?%C3%BCber/edit
Script = javascript:alert(1)
No https = www.example.com/portfolio
"""
