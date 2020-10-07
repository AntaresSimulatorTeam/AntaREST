from pathlib import Path
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch

from api_iso_antares.web.server import create_server


@pytest.mark.unit_test
def test_server() -> None:
    mock_handler = Mock()
    mock_handler.get = Mock(return_value={})

    app = create_server(mock_handler)
    client = app.test_client()
    client.get("/api/studies/settings/general/params")

    mock_handler.get.assert_called_once_with("settings/general/params")


@pytest.mark.unit_test
def test_404() -> None:
    mock_handler = Mock()
    mock_handler.get.return_value = None

    app = create_server(mock_handler)
    client = app.test_client()
    result = client.get("/api/studies/settings/general/params")

    assert result.status_code == 404
