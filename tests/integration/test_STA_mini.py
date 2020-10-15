import json
import os
from pathlib import Path

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
    [],
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


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "layers/layers.ini/activeLayer/showAllLayer",
            True,
        ),
        (
            "layers/layers.ini/layers/0",
            "All",
        ),
    ],
)
def test_sta_mini_layers_layers(
    request_handler: RequestHandler, url: str, expected_output: str
):

    url_path = Path("/metadata/STA-mini") / url

    assert_url_content(
        request_handler=request_handler,
        url=str(url_path),
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "Desktop.ini/.shellclassinfo/iconfile",
            "settings/resources/study.ico",
        ),
        (
            "Desktop.ini/.shellclassinfo/infotip",
            "Antares Study7.0: STA-mini",
        ),
        ("Desktop.ini/.shellclassinfo/iconindex", 0),
    ],
)
def test_sta_mini_desktop(
    request_handler: RequestHandler, url: str, expected_output: str
):
    url_path = Path("/metadata/STA-mini") / url

    assert_url_content(
        request_handler=request_handler,
        url=str(url_path),
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "study.antares/antares/created",
            1480683452,
        ),
        (
            "study.antares/antares/author",
            "Andrea SGATTONI",
        ),
    ],
)
def test_sta_mini_study_antares(
    request_handler: RequestHandler, url: str, expected_output: str
):

    url_path = Path("/metadata/STA-mini") / url

    assert_url_content(
        request_handler=request_handler,
        url=str(url_path),
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        ("/metadata/STA-mini/input/bindingconstraints/bindingconstraints.ini", {}),
        ("/metadata/STA-mini/input/hydro/series/de/mod.txt", 'file/STA-mini/input/hydro/series/de/mod.txt')

    ],
)
def test_sta_mini_input(
    request_handler: RequestHandler, url: str, expected_output: str
):
    url = url[10:]
    assert request_handler.get(url, RequestHandlerParameters()) == expected_output
    # assert_url_content(
    #     request_handler=request_handler,
    #     url=url,
    #     expected_output=expected_output,
    # )
