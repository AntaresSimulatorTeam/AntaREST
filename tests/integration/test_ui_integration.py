from multiprocessing import Process
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

front_path = Path(__file__).parent.parent.parent / "resources/webapp"


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
        browser.close()
