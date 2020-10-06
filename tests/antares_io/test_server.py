from pathlib import Path
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch

import api_iso_antares.antares_io.server as server


@pytest.mark.unit_test
def test_server(monkeypatch: MonkeyPatch) -> None:
    path = Path('my-path')

    mock_app = Mock()
    mock_app.get = Mock(return_value={})

    monkeypatch.setattr(server, "app", mock_app)

    app = server.application.test_client()
    app.get("/api/simulations/settings/general/params")

    mock_app.get.assert_called_once_with("settings/general/params")


@pytest.mark.unit_test
def test_404(monkeypatch: MonkeyPatch) -> None:
    mock_app = Mock()
    mock_app.get = Mock(return_value=None)

    monkeypatch.setattr(server, "app", mock_app)

    app = server.application.test_client()
    result = app.get("/api/simulations/ettings/general/params")

    assert result.status_code == 404
