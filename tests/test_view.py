"""The published page in desktop windows: menu, shrink to fit, captions hidden."""

import pytest
from helpers import BIG_MONITOR, LAPTOP, LAPTOPS, MIN_LEFT, MONITOR, rect, scrolls_sideways, size_id
from hotglue.pages import PAGE


def photos(page_name):
    """The page's photos that are shown as placed (not linked, not tiled patterns)."""
    return [o for o in PAGE[page_name].objects if o.kind == "image" and not o.link and not o.tiled]


def test_menu(site, page, errors):
    page.goto(site.view("painting"))
    side = page.locator("header.hpt-side")
    assert side.locator(".hpt-name").inner_text() == "Test Artist"
    links = side.locator("li a")
    # "This line has no equals sign" and the javascript: line are left out
    assert links.all_inner_texts() == [
        "About",
        "Exhibitions",
        "Painting",
        "Sculpture",
        "Contact",
        "Instagram",
        "Pasted",
        "Encoded",
        "No https",  # kept, but reported in the red box (test_editor.py)
    ]
    hrefs = dict(zip(links.all_inner_texts(), (link.get_attribute("href") for link in links.all())))
    assert hrefs["Instagram"] == "https://www.instagram.com/example"
    assert hrefs["Pasted"] == "/?painting"  # a copied address of a page of this site
    assert hrefs["Encoded"] == "/?%C3%BCber"  # decoded once, encoded once
    assert side.locator('a[aria-current="page"]').all_inner_texts() == ["Painting", "Pasted"]
    assert not errors


def test_page_under_a_menu_page_highlights_it(site, page):
    page.goto(site.view("exhibitions-2025-example-show"))
    assert page.locator('header.hpt-side a[aria-current="page"]').inner_text() == "Exhibitions"


@pytest.mark.parametrize("size", LAPTOPS, ids=size_id)
def test_wide_page_shrinks_to_fit_laptop(site, page, errors, size):
    """A page laid out on a big monitor fits a laptop window: no sideways scrolling, nothing
    under the menu, and every object shrunk by the same factor, measured from the menu's edge."""
    page.set_viewport_size(size)
    page.goto(site.view("start"))
    assert not scrolls_sideways(page)
    tall = site.obj("start", "tall")
    scale = rect(page, site, "start", "tall")["width"] / tall.width
    assert 0.3 < scale < 1
    for o in photos("start"):
        r = rect(page, site, "start", o.key)
        assert r["left"] == pytest.approx(MIN_LEFT + (o.left - MIN_LEFT) * scale, abs=2), o.key
        assert r["top"] == pytest.approx(o.top * scale, abs=2), o.key
        assert (r["width"], r["height"]) == pytest.approx((o.width * scale, o.height * scale), abs=2), o.key
        assert r["right"] <= size["width"], o.key
    assert not errors


@pytest.mark.parametrize(
    ("page_name", "size"),
    [("painting", s) for s in LAPTOPS] + [("painting", MONITOR), ("start", BIG_MONITOR)],
    ids=lambda v: v if isinstance(v, str) else size_id(v),
)
def test_page_that_fits_is_left_as_placed(site, page, page_name, size):
    """Never moved or enlarged when the window is wide enough."""
    page.set_viewport_size(size)
    page.goto(site.view(page_name))
    for o in photos(page_name):
        r = rect(page, site, page_name, o.key)
        assert (r["left"], r["top"], r["width"], r["height"]) == pytest.approx(
            (o.left, o.top, o.width, o.height), abs=1
        ), o.key


def test_resizing_the_window_refits(site, page):
    page.set_viewport_size(BIG_MONITOR)
    page.goto(site.view("start"))
    page.set_viewport_size(LAPTOPS[0])
    page.wait_for_function("document.documentElement.scrollWidth <= document.documentElement.clientWidth")


def test_captions_hidden_others_shown(site, page):
    page.set_viewport_size(LAPTOP)
    page.goto(site.view("painting"))
    assert not rect(page, site, "painting", "p1-cap")["shown"]  # a caption: shown in the overlay only
    assert rect(page, site, "painting", "linked-cap")["shown"]  # under a linked photo: stays
    far = site.locator(page, "painting", "p2-far")  # too far below its photo: stays,
    assert far.is_visible() and far.inner_text().startswith("~")  # ~ included
