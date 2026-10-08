"""What only hotglue-ng (hotglue2's ng-dev branch) has: its own phone view, which must stay
off, and "centered" pages."""

import pytest
from helpers import MIN_LEFT, PHONE, rect, scrolls_sideways
from hotglue.pages import PAGE
from playwright.sync_api import expect


@pytest.fixture
def ng(site):
    if not site.hotglue.is_ng:
        pytest.skip("hotglue-ng only")
    return site


def test_its_phone_view_stays_off(ng, page, errors):
    page.set_viewport_size(PHONE)
    page.goto(ng.view("start"))
    expect(page).to_have_url(ng.view("start"))  # the switch is taken out of the address again
    assert page.locator("#hg-mg-canvas").count() == 0
    assert page.locator("header.hpt-side").bounding_box()["y"] == 0
    assert not errors


def test_centered_page_in_wide_window(ng, page):
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.goto(ng.view("sculpture"))
    offset = (1920 - PAGE["sculpture"].centered_width) / 2
    s1 = ng.obj("sculpture", "s1")
    r = rect(page, ng, "sculpture", "s1")
    assert (r["left"], r["width"]) == pytest.approx((offset + s1.left, s1.width), abs=1)


def test_centered_page_in_laptop_window(ng, page):
    """Narrower than the box: it fills the window and its objects shrink to fit."""
    size = {"width": 1024, "height": 768}
    page.set_viewport_size(size)
    page.goto(ng.view("sculpture"))
    assert not scrolls_sideways(page)
    for key in PAGE["sculpture"].reading_order:
        r = rect(page, ng, "sculpture", key)
        assert r["left"] >= MIN_LEFT - 1, key
        assert r["right"] <= size["width"], key


def test_centered_page_on_phone(ng, page):
    page.set_viewport_size(PHONE)
    page.goto(ng.view("sculpture"))
    assert not scrolls_sideways(page)
    tops = [rect(page, ng, "sculpture", key)["top"] for key in PAGE["sculpture"].reading_order]
    assert tops == sorted(tops)
