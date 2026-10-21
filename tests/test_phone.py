"""Phones and narrow windows: menu on top, objects in one column in reading order."""

import pytest
from helpers import NARROW, PHONE, rect, scrolls_sideways, size_id
from hotglue.pages import PAGE


@pytest.mark.parametrize("size", [PHONE, NARROW], ids=size_id)
def test_one_column_in_reading_order(site, page, errors, size):
    page.set_viewport_size(size)
    page.goto(site.view("start"))
    boxes = {o.key: rect(page, site, "start", o.key) for o in PAGE["start"].objects}
    shown = sorted((key for key, b in boxes.items() if b["shown"]), key=lambda key: boxes[key]["top"])
    assert shown == list(PAGE["start"].reading_order)  # captions are hidden
    for key in shown:
        assert boxes[key]["left"] >= 0, key
        assert boxes[key]["right"] <= size["width"], key
        assert boxes[key]["zoom"] in ("1", "normal"), key  # shrink to fit is for wide windows only
    assert not scrolls_sideways(page)
    assert not errors


def test_photos_never_larger_than_placed(site, page):
    page.set_viewport_size(NARROW)
    page.goto(site.view("painting"))
    for o in PAGE["painting"].objects:
        r = rect(page, site, "painting", o.key)
        if o.kind == "image" and r["shown"]:
            assert r["width"] <= o.width + 1, o.key


def test_menu_on_top(site, page):
    page.set_viewport_size(PHONE)
    page.goto(site.view("painting"))
    side = page.locator("header.hpt-side").bounding_box()
    first = site.locator(page, "painting", "p1").bounding_box()
    assert side["y"] + side["height"] <= first["y"]


def test_years_in_the_menu_on_phones(site, page):
    """The years under a menu page share a row with it, below the other menu items before it."""
    page.set_viewport_size(PHONE)
    page.goto(site.view("painting-2026"))
    side = page.locator("header.hpt-side")
    painting = side.get_by_role("link", name="Painting", exact=True).bounding_box()
    year = side.get_by_role("link", name="2026").bounding_box()
    about = side.get_by_role("link", name="About").bounding_box()
    assert year["y"] == pytest.approx(painting["y"], abs=2)  # same row
    assert year["x"] >= painting["x"] + painting["width"] + 10  # with a gap
    assert painting["y"] > about["y"]  # a row of its own
    assert not scrolls_sideways(page)
