import io
import json
import shutil
from http import HTTPStatus
from pathlib import Path

import pytest

from api_iso_antares.custom_types import JSON
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
    url = url[len("/studies/") :]
    print(url)
    assert (
        request_handler.get(route=url, parameters=RequestHandlerParameters())
        == expected_output
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        ("/studies/STA-mini/settings/generaldata/general/horizon", 2030),
        ("/studies/STA-mini/settings/simulations", {}),
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


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/studies/STA-mini/layers/layers/activeLayer/showAllLayer",
            True,
        ),
        (
            "/studies/STA-mini/layers/layers/layers/0",
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
            "/studies/STA-mini/Desktop/.shellclassinfo/iconfile",
            "settings/resources/study.ico",
        ),
        (
            "/studies/STA-mini/Desktop/.shellclassinfo/infotip",
            "Antares Study7.0: STA-mini",
        ),
        ("/studies/STA-mini/Desktop/.shellclassinfo/iconindex", 0),
    ],
)
def test_sta_mini_desktop(
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
            "/studies/STA-mini/study/antares/created",
            1480683452,
        ),
        (
            "/studies/STA-mini/study/antares/author",
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
            "/studies/STA-mini/input/bindingconstraints/bindingconstraints",
            {},
        ),
        (
            "/studies/STA-mini/input/hydro/series/de/mod",
            "file/STA-mini/input/hydro/series/de/mod.txt",
        ),
        (
            "/studies/STA-mini/input/areas/list",
            "file/STA-mini/input/areas/list.txt",
        ),
        ("/studies/STA-mini/input/areas/sets/all areas/output", False),
        (
            "/studies/STA-mini/input/areas/de/optimization/nodal optimization/spread-spilled-energy-cost",
            0,
        ),
        ("/studies/STA-mini/input/areas/de/ui/layerX/0", 1),
        ("/studies/STA-mini/input/hydro/allocation/de/[allocation/de", 1),
        (
            "/studies/STA-mini/input/hydro/common/capacity/reservoir_fr",
            "file/STA-mini/input/hydro/common/capacity/reservoir_fr.txt",
        ),
        (
            "/studies/STA-mini/input/thermal/series/fr/05_nuclear/series",
            "file/STA-mini/input/thermal/series/fr/05_nuclear/series.txt",
        ),
        (
            "/studies/STA-mini/input/hydro/prepro/correlation/general/mode",
            "annual",
        ),
        (
            "/studies/STA-mini/input/hydro/prepro/fr/prepro/prepro/intermonthly-correlation",
            0.5,
        ),
        (
            "/studies/STA-mini/input/hydro/prepro/fr/energy",
            "file/STA-mini/input/hydro/prepro/fr/energy.txt",
        ),
        (
            "/studies/STA-mini/input/hydro/hydro/inter-monthly-breakdown/fr",
            1,
        ),
        (
            "/studies/STA-mini/input/thermal/prepro/fr/05_nuclear/modulation",
            "file/STA-mini/input/thermal/prepro/fr/05_nuclear/modulation.txt",
        ),
        (
            "/studies/STA-mini/input/thermal/areas/unserverdenergycost/de",
            3000.0,
        ),
        (
            "/studies/STA-mini/input/thermal/clusters/fr/list/05_nuclear/marginal-cost",
            50,
        ),
        (
            "/studies/STA-mini/input/links/fr/properties/it/hurdles-cost",
            True,
        ),
        (
            "/studies/STA-mini/input/links/fr/it",
            "file/STA-mini/input/links/fr/it.txt",
        ),
        (
            "/studies/STA-mini/input/load/prepro/fr/k",
            "file/STA-mini/input/load/prepro/fr/k.txt",
        ),
        (
            "/studies/STA-mini/input/load/series/load_fr",
            "file/STA-mini/input/load/series/load_fr.txt",
        ),
        (
            "/studies/STA-mini/input/misc-gen/miscgen-fr",
            "file/STA-mini/input/misc-gen/miscgen-fr.txt",
        ),
        (
            "/studies/STA-mini/input/reserves/fr",
            "file/STA-mini/input/reserves/fr.txt",
        ),
        (
            "/studies/STA-mini/input/solar/prepro/fr/k",
            "file/STA-mini/input/solar/prepro/fr/k.txt",
        ),
        (
            "/studies/STA-mini/input/solar/series/solar_fr",
            "file/STA-mini/input/solar/series/solar_fr.txt",
        ),
        (
            "/studies/STA-mini/input/wind/prepro/fr/k",
            "file/STA-mini/input/wind/prepro/fr/k.txt",
        ),
        (
            "/studies/STA-mini/input/wind/series/wind_fr",
            "file/STA-mini/input/wind/series/wind_fr.txt",
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
            "/studies/STA-mini/output/3/annualSystemCost",
            "file/STA-mini/output/20201014-1427eco/annualSystemCost.txt",
        ),
        (
            "/studies/STA-mini/output/1/checkIntegrity",
            "file/STA-mini/output/20201014-1422eco-hello/checkIntegrity.txt",
        ),
        (
            "/studies/STA-mini/output/4/simulation-comments",
            "file/STA-mini/output/20201014-1430adq/simulation-comments.txt",
        ),
        (
            "/studies/STA-mini/output/2/simulation",
            "file/STA-mini/output/20201014-1425eco-goodbye/simulation.log",
        ),
        (
            "/studies/STA-mini/output/1/about-the-study/areas",
            "file/STA-mini/output/20201014-1422eco-hello/about-the-study/areas.txt",
        ),
        (
            "/studies/STA-mini/output/2/about-the-study/comments",
            "file/STA-mini/output/20201014-1425eco-goodbye/about-the-study/comments.txt",
        ),
        (
            "/studies/STA-mini/output/3/about-the-study/links",
            "file/STA-mini/output/20201014-1427eco/about-the-study/links.txt",
        ),
        (
            "/studies/STA-mini/output/4/about-the-study/parameters/general/horizon",
            2030,
        ),
        (
            "/studies/STA-mini/output/1/about-the-study/study/antares/author",
            "Andrea SGATTONI",
        ),
        (
            "/studies/STA-mini/output/1/economy/mc-all/areas/de/id-daily",
            "file/STA-mini/output/20201014-1422eco-hello/economy/mc-all/areas/de/id-daily.txt",
        ),
        (
            "/studies/STA-mini/output/1/economy/mc-all/grid/areas",
            "file/STA-mini/output/20201014-1422eco-hello/economy/mc-all/grid/areas.txt",
        ),
        ("/studies/STA-mini/output/1/economy/mc-all/links/de/fr", {}),
        (
            "/studies/STA-mini/output/1/economy/mc-ind/00001/links/de/fr/values-hourly",
            "file/STA-mini/output/20201014-1422eco-hello/economy/mc-ind/00001/links/de - fr/values-hourly.txt",
        ),
        (
            "/studies/STA-mini/output/1/economy/mc-ind/00001/areas/de/details-annual",
            "file/STA-mini/output/20201014-1422eco-hello/economy/mc-ind/00001/areas/de/details-annual.txt",
        ),
        (
            "/studies/STA-mini/output/1/economy/mc-ind/00001/areas/de/details-annual",
            "file/STA-mini/output/20201014-1422eco-hello/economy/mc-ind/00001/areas/de/details-annual.txt",
        ),
        (
            "/studies/STA-mini/output/4/adequacy/mc-all/areas/de/id-daily",
            "file/STA-mini/output/20201014-1430adq/adequacy/mc-all/areas/de/id-daily.txt",
        ),
        (
            "/studies/STA-mini/output/1/ts-numbers/hydro/de",
            "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/hydro/de.txt",
        ),
        (
            "/studies/STA-mini/output/1/ts-numbers/load/de",
            "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/load/de.txt",
        ),
        (
            "/studies/STA-mini/output/1/ts-numbers/solar/de",
            "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/solar/de.txt",
        ),
        (
            "/studies/STA-mini/output/1/ts-numbers/wind/de",
            "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/wind/de.txt",
        ),
        (
            "/studies/STA-mini/output/1/ts-numbers/thermal/de/07_gas",
            "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/thermal/de/07_gas.txt",
        ),
        (
            "/studies/STA-mini/output/1/info/general/version",
            700,
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


@pytest.mark.integration_test
def test_sta_mini_copy(request_handler: RequestHandler) -> None:

    source_study_name = "STA-mini"
    destination_study_name = "copy-STA-mini"

    app = create_server(request_handler)
    client = app.test_client()
    result = client.post(
        f"/studies/{source_study_name}/copy?dest={destination_study_name}"
    )

    assert result.status_code == HTTPStatus.CREATED.value
    url_destination = result.data.decode("utf-8")

    destination_folder = url_destination.split("/")[2]

    parameters = RequestHandlerParameters(depth=None)
    data_source = request_handler.get(source_study_name, parameters)
    data_destination = request_handler.get(destination_folder, parameters)

    link_url_source = data_source["input"]["links"]["de"]["fr"]
    assert link_url_source == "file/STA-mini/input/links/de/fr.txt"

    link_url_destination = data_destination["input"]["links"]["de"]["fr"]
    assert (
        link_url_destination
        == f"file/{destination_folder}/input/links/de/fr.txt"
    )

    result_source = client.get(link_url_source)
    matrix_source = result_source.data
    result_destination = client.get(link_url_destination)
    matrix_destination = result_destination.data

    assert matrix_source == matrix_destination

    def replace_study_name(data: JSON) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.startswith("file/"):
                    data[key] = value.replace(
                        destination_folder, source_study_name
                    )
                else:
                    replace_study_name(value)

    replace_study_name(data_destination)
    data_source["output"] = {}
    data_source["study"] = {}
    data_destination["study"] = {}

    assert data_source == data_destination


@pytest.mark.integration_test
def test_sta_mini_list_studies(request_handler: RequestHandler) -> None:
    expected_output = {
        "STA-mini": {
            "antares": {
                "author": "Andrea SGATTONI",
                "caption": "STA-mini",
                "created": 1480683452,
                "lastsave": 1602678639,
                "version": 700,
            }
        }
    }
    url = "/studies"
    assert_url_content(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
def test_sta_mini_with_wrong_output_folder(
    request_handler: RequestHandler, sta_mini_path: Path
) -> None:

    (sta_mini_path / "output" / "maps").mkdir()

    url = "/studies/STA-mini/Desktop/.shellclassinfo/infotip"
    expected_output = "Antares Study7.0: STA-mini"

    assert_with_errors(
        request_handler=request_handler,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
def test_sta_mini_import(
    tmp_path: Path, request_handler: RequestHandler
) -> None:

    path_study = request_handler.get_study_path("STA-mini")
    sta_mini_zip_filepath = shutil.make_archive(tmp_path, "zip", path_study)
    sta_mini_zip_path = Path(sta_mini_zip_filepath)

    app = create_server(request_handler)
    client = app.test_client()

    study_data = io.BytesIO(sta_mini_zip_path.read_bytes())
    result = client.post("/studies", data=study_data)

    assert result.status_code == HTTPStatus.CREATED.value
