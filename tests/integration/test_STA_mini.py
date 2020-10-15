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
            "/metadata/STA-mini/layers/layers.ini/activeLayer/showAllLayer",
            True,
        ),
        (
            "/metadata/STA-mini/layers/layers.ini/layers/0",
            "All",
        ),
    ],
)
def test_sta_mini_layers_layers(
    request_handler: RequestHandler, url: str, expected_output: str
):

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
            "/metadata/STA-mini/Desktop.ini/.shellclassinfo/iconfile",
            "settings/resources/study.ico",
        ),
        (
            "/metadata/STA-mini/Desktop.ini/.shellclassinfo/infotip",
            "Antares Study7.0: STA-mini",
        ),
        ("/metadata/STA-mini/Desktop.ini/.shellclassinfo/iconindex", 0),
    ],
)
def test_sta_mini_desktop(
    request_handler: RequestHandler, url: str, expected_output: str
):
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
            "/metadata/STA-mini/study.antares/antares/created",
            1480683452,
        ),
        (
            "/metadata/STA-mini/study.antares/antares/author",
            "Andrea SGATTONI",
        ),
    ],
)
def test_sta_mini_study_antares(
    request_handler: RequestHandler, url: str, expected_output: str
):
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
            "/metadata/STA-mini/input/bindingconstraints/bindingconstraints.ini",
            {},
        ),
        (
            "/metadata/STA-mini/input/hydro/series/de/mod.txt",
            f"file{os.sep}STA-mini{os.sep}input{os.sep}hydro{os.sep}series{os.sep}de{os.sep}mod.txt",
        ),
    ],
)
def test_sta_mini_input(
    request_handler: RequestHandler, url: str, expected_output: str
):
    url = url[10:]
    assert (
        request_handler.get(url, RequestHandlerParameters()) == expected_output
    )
    # assert_url_content(
    #     request_handler=request_handler,
    #     url=url,
    #     expected_output=expected_output,
    # )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/metadata/STA-mini/output/20201014-1427eco/annualSystemCost.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1427eco{os.sep}annualSystemCost.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1422eco-hello/checkIntegrity.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1422eco-hello{os.sep}checkIntegrity.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1430adq/simulation-comments.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1430adq{os.sep}simulation-comments.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1425eco-goodbye/simulation.log",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1425eco-goodbye{os.sep}simulation.log",
        ),
        (
            "/metadata/STA-mini/output/20201014-1422eco-hello/about-the-study/areas.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1422eco-hello{os.sep}about-the-study{os.sep}areas.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1425eco-goodbye/about-the-study/comments.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1425eco-goodbye{os.sep}about-the-study{os.sep}comments.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1427eco/about-the-study/links.txt",
            f"file{os.sep}STA-mini{os.sep}output{os.sep}20201014-1427eco{os.sep}about-the-study{os.sep}links.txt",
        ),
        (
            "/metadata/STA-mini/output/20201014-1430adq/about-the-study/parameters.ini/general/horizon",
            2030,
        ),
        (
            "/metadata/STA-mini/output/20201014-1422eco-hello/about-the-study/study.ini/antares/author",
            "Andrea SGATTONI",
        ),
    ],
)
def test_sta_mini_output(
    request_handler: RequestHandler, url: str, expected_output: str
):
    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )
