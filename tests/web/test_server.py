from unittest.mock import Mock

import pytest

from api_iso_antares.engine.url_engine import UrlNotMatchJsonDataError
from api_iso_antares.web.server import create_server


@pytest.mark.unit_test
def test_server() -> None:
    mock_handler = Mock()
    mock_handler.get = Mock(return_value={})

    app = create_server(mock_handler)
    client = app.test_client()
    client.get("/api/studies/study1/settings/general/params")

    mock_handler.get.assert_called_once_with("study1/settings/general/params")


@pytest.mark.unit_test
def test_404() -> None:
    mock_handler = Mock()
    mock_handler.get.side_effect = UrlNotMatchJsonDataError("Test")

    app = create_server(mock_handler)
    client = app.test_client()
    result = client.get("/api/studies/study1/settings/general/params")
    assert result.status_code == 404

    result = client.get("/api/studies/WRONG_STUDY")
    assert result.status_code == 404
