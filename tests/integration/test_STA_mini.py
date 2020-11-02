import json
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


def assert_with_errors(
    request_handler: RequestHandler, url: str, expected_output: dict
) -> None:
    url = url[10:]
    print(url)
    assert (
        request_handler.get(route=url, parameters=RequestHandlerParameters())
        == expected_output
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        ("/metadata/STA-mini/settings/generaldata/general/horizon", 2030),
        ("/metadata/STA-mini/settings/simulations", {}),
    ],
)
def test_sta_mini_settings(
    request_handler: RequestHandler, url: str, expected_output: str
):
    assert_with_errors(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )
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
            "/metadata/STA-mini/layers/layers/activeLayer/showAllLayer",
            True,
        ),
        (
            "/metadata/STA-mini/layers/layers/layers/0",
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
            "/metadata/STA-mini/desktop/.shellclassinfo/iconfile",
            "settings/resources/study.ico",
        ),
        (
            "/metadata/STA-mini/desktop/.shellclassinfo/infotip",
            "Antares Study7.0: STA-mini",
        ),
        ("/metadata/STA-mini/desktop/.shellclassinfo/iconindex", 0),
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
            "/metadata/STA-mini/study/antares/created",
            1480683452,
        ),
        (
            "/metadata/STA-mini/study/antares/author",
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
            "/metadata/STA-mini/input/bindingconstraints/bindingconstraints",
            {},
        ),
        (
            "/metadata/STA-mini/input/hydro/series/de/mod.txt",
            str(Path("file/STA-mini/input/hydro/series/de/mod.txt")),
        ),
        (
            "/metadata/STA-mini/input/areas/list",
            str(Path("file/STA-mini/input/areas/list.txt")),
        ),
        (
            "/metadata/STA-mini/input/areas/de/optimization/nodal optimization/spread-spilled-energy-cost",
            0,
        ),
        ("/metadata/STA-mini/input/areas/de/ui/layerX/0", 1),
        ("/metadata/STA-mini/input/hydro/allocation/de/[allocation/de", 1),
        (
            "/metadata/STA-mini/input/hydro/common/capacity/reservoir_fr",
            str(
                Path(
                    "file/STA-mini/input/hydro/common/capacity/reservoir_fr.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/input/thermal/series/fr/05_nuclear/series",
            str(
                Path(
                    "file/STA-mini/input//thermal/series/fr/05_nuclear/series.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/input/hydro/prepro/correlation/general/mode",
            "annual",
        ),
        (
            "/metadata/STA-mini/input/hydro/prepro/fr/prepro/prepro/intermonthly-correlation",
            0.5,
        ),
        (
            "/metadata/STA-mini/input/hydro/prepro/fr/energy",
            str(Path("file/STA-mini/input/hydro/prepro/fr/energy.txt")),
        ),
        (
            "/metadata/STA-mini/input/hydro/hydro/inter-monthly-breakdown/fr",
            1,
        ),
        (
            "/metadata/STA-mini/input/thermal/prepro/fr/05_nuclear/modulation",
            str(
                Path(
                    "file/STA-mini/input/thermal/prepro/fr/05_nuclear/modulation.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/input/thermal/clusters/fr/list/05_nuclear/marginal-cost",
            50,
        ),
        (
            "/metadata/STA-mini/input/links/fr/properties/it/hurdles-cost",
            True,
        ),
        (
            "/metadata/STA-mini/input/links/fr/it",
            str(Path("file/STA-mini/input/links/fr/it.txt")),
        ),
        (
            "/metadata/STA-mini/input/load/prepro/fr/k",
            str(Path("file/STA-mini/input/load/prepro/fr/k.txt")),
        ),
        (
            "/metadata/STA-mini/input/load/series/load_fr",
            str(Path("file/STA-mini/input/load/series/load_fr.txt")),
        ),
        (
            "/metadata/STA-mini/input/misc-gen/miscgen-fr",
            str(Path("file/STA-mini/input/misc-gen/miscgen-fr.txt")),
        ),
        (
            "/metadata/STA-mini/input/reserves/fr",
            str(Path("file/STA-mini/input/reserves/fr.txt")),
        ),
        (
            "/metadata/STA-mini/input/solar/prepro/fr/k",
            str(Path("file/STA-mini/input/solar/prepro/fr/k.txt")),
        ),
        (
            "/metadata/STA-mini/input/solar/series/solar_fr",
            str(Path("file/STA-mini/input/solar/series/solar_fr.txt")),
        ),
        (
            "/metadata/STA-mini/input/wind/prepro/fr/k",
            str(Path("file/STA-mini/input/wind/prepro/fr/k.txt")),
        ),
        (
            "/metadata/STA-mini/input/wind/series/wind_fr",
            str(Path("file/STA-mini/input/wind/series/wind_fr.txt")),
        ),
    ],
)
def test_sta_mini_input(
    request_handler: RequestHandler, url: str, expected_output: str
):
    assert_with_errors(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/metadata/STA-mini/output/3/annualSystemCost",
            str(
                Path(
                    "file/STA-mini/output/20201014-1427eco/annualSystemCost.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/checkIntegrity",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/checkIntegrity.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/4/simulation-comments",
            str(
                Path(
                    "file/STA-mini/output/20201014-1430adq/simulation-comments.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/2/simulation",
            str(
                Path(
                    "file/STA-mini/output/20201014-1425eco-goodbye/simulation.log"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/about-the-study/areas",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/about-the-study/areas.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/2/about-the-study/comments",
            str(
                Path(
                    "file/STA-mini/output/20201014-1425eco-goodbye/about-the-study/comments.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/3/about-the-study/links",
            str(
                Path(
                    "file/STA-mini/output/20201014-1427eco/about-the-study/links.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/4/about-the-study/parameters/general/horizon",
            2030,
        ),
        (
            "/metadata/STA-mini/output/1/about-the-study/study/antares/author",
            "Andrea SGATTONI",
        ),
        (
            "/metadata/STA-mini/output/1/economy/mc-all/areas/de/id-daily",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/economy/mc-all/areas/de/id-daily.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/economy/mc-all/grid/areas",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/economy/mc-all/grid/areas.txt"
                )
            ),
        ),
        ("/metadata/STA-mini/output/1/economy/mc-all/links/de/fr", {}),
        (
            "/metadata/STA-mini/output/1/economy/mc-ind/00001/links/de/fr/values-hourly",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/economy/mc-ind/00001/links/de - fr/values-hourly.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/economy/mc-ind/00001/areas/de/details-annual",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/economy/mc-ind/00001/areas/de/details-annual.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/economy/mc-ind/00001/areas/de/details-annual",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/economy/mc-ind/00001/areas/de/details-annual.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/4/adequacy/mc-all/areas/de/id-daily",
            str(
                Path(
                    "file/STA-mini/output/20201014-1430adq/adequacy/mc-all/areas/de/id-daily.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/ts-numbers/hydro/de",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/hydro/de.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/ts-numbers/load/de",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/load/de.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/ts-numbers/solar/de",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/solar/de.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/ts-numbers/wind/de",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/wind/de.txt"
                )
            ),
        ),
        (
            "/metadata/STA-mini/output/1/ts-numbers/thermal/de/07_gas",
            str(
                Path(
                    "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/thermal/de/07_gas.txt"
                )
            ),
        ),
    ],
)
def test_sta_mini_output(
    request_handler: RequestHandler, url: str, expected_output: str
):
    assert_with_errors(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )
