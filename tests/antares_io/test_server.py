from unittest.mock import Mock

from _pytest.monkeypatch import MonkeyPatch

import api_iso_antares.antares_io.server as server


def test_server(monkeypatch: MonkeyPatch) -> None:
    mock_engine: Mock = Mock()
    mock_engine.apply = Mock(return_value={})
    monkeypatch.setattr(server, "engine", mock_engine)

    app = server.application.test_client()
    app.get("/api/settings/general/params")

    mock_engine.apply.assert_called_once_with("settings/general/params")


def test_404(monkeypatch: MonkeyPatch) -> None:
    mock_engine: Mock = Mock()
    mock_engine.apply = Mock(return_value=None)
    monkeypatch.setattr(server, "engine", mock_engine)

    app = server.application.test_client()
    result = app.get("/api/settings/general/params")

    assert result.status_code == 404
