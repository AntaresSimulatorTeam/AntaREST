import json
import os

import pytest

from api_iso_antares.web import RequestHandler
from api_iso_antares.web.request_handler import RequestHandlerParameters
from api_iso_antares.web.server import create_server


def assert_url_content(
    request_handler: RequestHandler, url: str, expected_output: str
) -> None:
    app = create_server(request_handler)
    client = app.test_client()
    res = client.get(url)
    assert json.loads(res.data) == expected_output


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url,expected_output",
    [
        (
            "/metadata/STA-mini/Desktop.ini/.shellclassinfo/infotip",
            "Antares Study7.0: STA-mini",
        ),
        ("/metadata/STA-mini/settings/generaldata.ini/general/horizon", 2030),
        (
            "/metadata/STA-mini/settings/comments.txt",
            f"file{os.sep}STA-mini{os.sep}settings{os.sep}comments.txt",
        ),
    ],
)
def test_sta_mini(
    request_handler: RequestHandler, url: str, expected_output: str
) -> None:

    # url = url[10:]
    # print(url)
    # assert (
    #     request_handler.get(route=url, parameters=RequestHandlerParameters())
    #     == expected_output
    # )

    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        ("/metadata/STA-mini/settings/generaldata.ini/general/horizon", 2030),
        (
            "/metadata/STA-mini/settings/comments.txt",
            f"file{os.sep}STA-mini{os.sep}settings{os.sep}comments.txt",
        ),
        (
            "/metadata/STA-mini/settings/scenariobuilder.dat",
            f"file{os.sep}STA-mini{os.sep}settings{os.sep}scenariobuilder.dat",
        ),
        ("/metadata/STA-mini/settings/simulations", {}),
        (
            "/metadata/STA-mini/settings/resources/study.ico",
            f"file{os.sep}STA-mini{os.sep}settings{os.sep}resources{os.sep}study.ico",
        ),
    ],
)
def test_sta_mini_settings(
    request_handler: RequestHandler, url: str, expected_output: str
):
    # url = url[10:]
    # print(url)
    # assert (
    #     request_handler.get(route=url, parameters=RequestHandlerParameters())
    #     == expected_output
    # )
    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )
