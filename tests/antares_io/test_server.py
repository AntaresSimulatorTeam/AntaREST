from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch

import api_iso_antares.antares_io.server as server


@pytest.mark.unit_test
def test_server(monkeypatch: MonkeyPatch) -> None:
    mock_engine: Mock = Mock()
    mock_engine.apply = Mock(return_value={})
    monkeypatch.setattr(server, "engine", mock_engine)

    app = server.application.test_client()
    app.get("/api/settings/general/params")

    mock_engine.apply.assert_called_once_with("settings/general/params")


@pytest.mark.unit_test
def test_404(monkeypatch: MonkeyPatch) -> None:
    mock_engine: Mock = Mock()
    mock_engine.apply = Mock(return_value=None)
    monkeypatch.setattr(server, "engine", mock_engine)

    app = server.application.test_client()
    result = app.get("/api/settings/general/params")

    assert result.status_code == 404
