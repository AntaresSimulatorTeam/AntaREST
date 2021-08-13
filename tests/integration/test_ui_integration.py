import time
from multiprocessing import Process
from pathlib import Path
from typing import Callable

import pytest
from playwright.sync_api import sync_playwright, WebSocket, Page

front_path = Path(__file__).parent.parent.parent / "resources/webapp"

console_log = []


def retry(
    page: Page,
    assertion: Callable[[], bool],
    delay: float = 500,
    max_try: int = 10,
):
    if assertion():
        return True
    elif max_try > 0:
        page.wait_for_timeout(delay)
        return retry(page, assertion, delay, max_try - 1)
    return False


def log_console(msg):
    console_log.append(msg)


def check_studylist(page: Page, expected_nb: int):
    els = page.query_selector_all(".studylistitem")
    print(len(els))
    return len(els) == expected_nb


@pytest.mark.skipif(
    not front_path.exists(),
    reason="Requires webapp to be built for distribution",
)
def test_ui(running_app_with_ui: Process):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        context.set_default_timeout(10000)
        page = context.new_page()
        page.goto("http://localhost:8080")
        assert page.title() == "Antares Web"

        # login
        page.fill("#login", "admin")
        page.fill("#password", "admin")
        page.press("button", "Enter")

        page.on("console", log_console)

        with page.expect_websocket() as ws:
            page.wait_for_selector(".studylistingcontainer")
            assert retry(page, lambda: check_studylist(page, 1))

            page.fill("#studyname", "foo")
            page.click("#createstudysubmit")
            ws.value.expect_event("framereceived")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector(".studylistingcontainer")
            assert retry(page, lambda: check_studylist(page, 2))

        browser.close()
