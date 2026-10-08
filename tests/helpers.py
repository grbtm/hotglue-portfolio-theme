"""Window sizes, the theme's layout numbers, and measuring objects in the browser."""

import re
from pathlib import Path

PHONE = {"width": 390, "height": 844}
NARROW = {"width": 800, "height": 1000}  # the widest window that gets the phone layout
LAPTOP = {"width": 1440, "height": 900}
LAPTOPS = [{"width": 1280, "height": 800}, LAPTOP, {"width": 1512, "height": 982}]
MONITOR = {"width": 2560, "height": 1440}
BIG_MONITOR = {"width": 2880, "height": 1600}

# where the free area beside the menu starts: the menu width (--side in head.html) + the gap
# beside it (MENU_GAP in body.html)
ROOT = Path(__file__).parent.parent
SIDE = int(re.search(r"--side:\s*(\d+)px", (ROOT / "head.html").read_text())[1])
MENU_GAP = int(re.search(r"MENU_GAP = (\d+)", (ROOT / "body.html").read_text())[1])
MIN_LEFT = SIDE + MENU_GAP


def size_id(size):
    return f"{size['width']}x{size['height']}"


def rect(browser_page, site, page, key):
    """An object's box on the page (scrolled position included), and whether it is shown."""
    return browser_page.evaluate(
        """(id) => {
        const el = document.getElementById(id), r = el.getBoundingClientRect();
        return { left: r.left + scrollX, top: r.top + scrollY, right: r.right + scrollX,
                 width: r.width, height: r.height, shown: getComputedStyle(el).display !== "none",
                 zoom: getComputedStyle(el).zoom };
    }""",
        site.object_id(page, key),
    )


def scrolls_sideways(browser_page):
    return browser_page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
