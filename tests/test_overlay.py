"""Clicking a photo: the overlay with its caption, keys, Back button and shareable #links."""

import re

import pytest
from helpers import LAPTOP, PHONE, size_id
from hotglue.pages import PAGE
from playwright.sync_api import expect


def photo(page, site, page_name, key):
    return site.locator(page, page_name, key).locator("img")


CAPTIONS = {"tall": "cap-tall", "wide": "cap-wide", "middle": "cap-middle"}  # start page; "right" has none


def caption_of(site, page_name, photo_key):
    return site.obj(page_name, CAPTIONS[photo_key]).caption if photo_key in CAPTIONS else ""


def test_click_opens_photo_with_caption(site, page, errors):
    page.set_viewport_size(LAPTOP)
    page.goto(site.view("start"))
    photo(page, site, "start", "middle").click()
    dialog = page.locator("dialog.hpt-lightbox")
    expect(dialog).to_be_visible()
    caption = dialog.locator(".hpt-caption")
    expect(caption).to_have_text(caption_of(site, "start", "middle"))  # without the ~
    expect(caption.locator("b")).to_have_text("Lorem")  # formatting kept
    assert page.url.endswith("#" + site.number("start", "middle"))
    assert not errors


def test_arrow_keys_follow_reading_order(site, page):
    page.goto(site.view("start"))
    first, second, *_, last = PAGE["start"].reading_order
    photo(page, site, "start", first).click()
    caption = page.locator("dialog.hpt-lightbox .hpt-caption")
    expect(caption).to_have_text(caption_of(site, "start", first))
    page.keyboard.press("ArrowRight")
    expect(caption).to_have_text(caption_of(site, "start", second))
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowLeft")  # wraps around to the last photo
    expect(caption).to_have_text(caption_of(site, "start", last))


@pytest.mark.parametrize("close", ["Escape", "Back"])
def test_closing_goes_back_to_the_page(site, page, close):
    page.goto(site.view("start"))
    photo(page, site, "start", "tall").click()
    if close == "Escape":
        page.keyboard.press("Escape")
    else:
        page.go_back()
    expect(page.locator("dialog.hpt-lightbox")).to_be_hidden()
    expect(page).to_have_url(site.view("start"))


@pytest.mark.parametrize("size", [LAPTOP, PHONE], ids=size_id)
def test_shared_link_opens_that_photo(site, page, size):
    page.set_viewport_size(size)
    link = site.view("start") + "#" + site.number("start", "wide")
    page.goto(link)
    expect(page.locator("dialog.hpt-lightbox .hpt-caption")).to_have_text(caption_of(site, "start", "wide"))
    expect(page).to_have_url(link)
    page.keyboard.press("Escape")
    expect(page).to_have_url(site.view("start"))


def test_linked_photo_stays_a_link(site, page):
    page.goto(site.view("painting"))
    img = photo(page, site, "painting", "linked")
    assert img.get_attribute("role") is None
    img.click()
    page.wait_for_url(re.compile(r"\?sculpture$"))
