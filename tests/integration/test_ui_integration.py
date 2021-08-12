import time
from multiprocessing import Process
from pathlib import Path
from typing import Callable

import pytest
from playwright.sync_api import sync_playwright, WebSocket, Page

front_path = Path(__file__).parent.parent.parent / "resources/webapp"

console_log = []


def retry(
    assertion: Callable[[], bool], delay: float = 0.2, max_try: int = 10
):
    if assertion():
        return True
    elif max_try > 0:
        time.sleep(delay)
        return retry(assertion, delay, max_try - 1)
    return False


def log_console(msg):
    console_log.append(msg)


def check_studylist(page: Page, expected_nb: int):
    els = page.query_selector_all(".studylistitem")
    return len(els) == expected_nb


@pytest.mark.skipif(
    not front_path.exists(),
    reason="Requires webapp to be built for distribution",
)
def test_ui(running_app_with_ui: Process):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080")
        assert page.title() == "Antares Web"

        # login
        page.fill("#login", "admin")
        page.fill("#password", "admin")
        page.press("button", "Enter")

        page.on("console", log_console)

        with page.expect_websocket() as ws:
            page.wait_for_selector(".studylistingcontainer")
            els = page.query_selector_all(".studylistitem")
            assert len(els) == 1

            page.fill("#studyname", "foo")
            page.click("#createstudysubmit")
            ws.value.expect_event("framereceived")

            assert retry(lambda: check_studylist(page, 2))

        browser.close()
