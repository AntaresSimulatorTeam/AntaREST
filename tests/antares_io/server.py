from typing import Any, Dict

from _pytest.monkeypatch import MonkeyPatch

import api_iso_antares.antares_io.server as server

class MockEngine:
    def __init__(self):
        self.count = 0
        self.path = ''

    def apply(self, path: str) -> Dict[str, Any]:
        self.count += 1
        self.path = path
        return {}


def test_server(monkeypatch: MonkeyPatch):
    mock = MockEngine()
    monkeypatch.setattr(server, "engine", mock)

    app = server.application.test_client()
    app.get('/api/settings/general/params')

    assert mock.count == 1
    assert mock.path == 'settings/general/params'
