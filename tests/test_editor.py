"""hotglue's editor: faded menu, the red box with warnings, and none of the published-page
changes (no shrinking, no phone column, no overlay)."""

import re

import pytest
from helpers import LAPTOP, LAPTOPS, MIN_LEFT, PHONE, size_id
from playwright.sync_api import expect

WARNED = re.compile(r"\bhpt-warn\b")


def notes(page):
    return page.locator(".hpt-notes")


def test_warnings_for_a_page_breaking_the_rules(site, page, errors):
    page.set_viewport_size(LAPTOP)
    page.goto(site.edit("loose-page"))
    expect(notes(page)).to_contain_text(f"closer than {MIN_LEFT} pixels")
    expect(notes(page)).to_contain_text('This page ("loose-page") is not in the menu')
    expect(notes(page)).to_contain_text('Menu line ignored: "This line has no equals sign"')
    expect(notes(page)).to_contain_text('Menu line ignored: "Script = javascript:alert(1)"')
    expect(notes(page)).to_contain_text('Menu line "No https = www.example.com/portfolio": for another website')
    # the red box stays in the menu's column, where it can't cover an object
    box = notes(page).bounding_box()
    assert box["x"] + box["width"] <= MIN_LEFT - 20
    expect(site.locator(page, "loose-page", "too-close")).to_have_class(WARNED)
    expect(page.locator("header.hpt-side")).to_have_class(re.compile(r"\bhpt-editing\b"))
    assert not errors


def test_loose_caption_outlined_attached_caption_not(site, page):
    page.goto(site.edit("painting"))
    expect(site.locator(page, "painting", "p2-far")).to_have_class(WARNED)
    expect(site.locator(page, "painting", "p1-cap")).not_to_have_class(WARNED)
    expect(notes(page)).to_contain_text("1 text starting with ~ not counted as a caption")


@pytest.mark.parametrize("size", [LAPTOPS[0], PHONE], ids=size_id)
def test_editor_shows_page_as_placed(site, page, size):
    """No shrinking, no overlay, no phone column: the artist places objects on the real canvas."""
    page.set_viewport_size(size)
    page.goto(site.edit("start"))
    expect(page.locator("header.hpt-side")).to_be_attached()
    assert not page.evaluate("document.body.classList.contains('hpt-view')")
    assert page.locator("dialog.hpt-lightbox").count() == 0
    box = site.locator(page, "start", "right").bounding_box()
    obj = site.obj("start", "right")
    assert (box["x"] + page.evaluate("scrollX"), box["width"]) == (obj.left, obj.width)


def test_warnings_follow_edits(site, page):
    """When an object moves (hotglue changes its inline style), the red box updates."""
    page.goto(site.edit("painting"))
    expect(notes(page)).to_contain_text("1 text starting with ~")
    far = site.locator(page, "painting", "p2-far")
    far.evaluate("(el) => { el.style.top = '470px'; }")  # now 10px under its photo
    expect(far).not_to_have_class(WARNED)
