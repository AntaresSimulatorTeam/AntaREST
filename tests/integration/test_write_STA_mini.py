import json

import pytest

from api_iso_antares.custom_types import SUB_JSON
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.request_handler import RequestHandlerParameters
from api_iso_antares.web.server import create_server


def assert_url_content(
    request_handler: RequestHandler, url: str, new: SUB_JSON
) -> None:
    app = create_server(request_handler)
    client = app.test_client()
    res = client.post(url, data=json.dumps(url))
    assert json.loads(res.data) == new

    res = client.get(url)
    assert json.loads(res.data) == new


def assert_with_errors(
    request_handler: RequestHandler, url: str, new: SUB_JSON
) -> None:
    url = url[len("/studies/") :]
    print(url)
    res = request_handler.edit_study(route=url, new=new)
    assert res == new

    res = request_handler.get(
        route=url, parameters=RequestHandlerParameters(depth=-1)
    )
    assert res == new


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, new",
    [
        ("/studies/STA-mini/settings/generaldata/general/horizon", 3000),
    ],
)
def test_sta_mini_settings(
    request_handler: RequestHandler, url: str, new: SUB_JSON
):
    assert_with_errors(
        request_handler=request_handler,
        url=url,
        new=new,
    )
