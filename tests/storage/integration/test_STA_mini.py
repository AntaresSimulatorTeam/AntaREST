import io
import json
import shutil
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock, call

import pytest
from flask import Flask

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.storage.main import build_storage
from antarest.storage.model import Study
from antarest.storage.service import StorageService
from antarest.common.requests import (
    RequestParameters,
)
from tests.storage.integration.data.de_details_hourly import de_details_hourly
from tests.storage.integration.data.de_fr_values_hourly import (
    de_fr_values_hourly,
)

ADMIN = JWTUser(
    id=1,
    impersonator=1,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)


def assert_url_content(
    storage_service: StorageService, url: str, expected_output: str
) -> None:
    app = Flask(__name__)
    build_storage(
        app,
        session=Mock(),
        user_service=Mock(),
        storage_service=storage_service,
        config=storage_service.study_service.config,
    )
    client = app.test_client()
    res = client.get(url)
    assert json.loads(res.data) == expected_output


def assert_with_errors(
    storage_service: StorageService, url: str, expected_output: dict
) -> None:
    url = url[len("/studies/") :]
    params = RequestParameters(user=ADMIN)
    assert (
        storage_service.get(route=url, depth=3, params=params)
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
def test_sta_mini_settings(storage_service, url: str, expected_output: str):
    assert_with_errors(
        storage_service=storage_service,
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
    storage_service, url: str, expected_output: str
):
    assert_url_content(
        storage_service=storage_service,
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
def test_sta_mini_desktop(storage_service, url: str, expected_output: str):
    assert_with_errors(
        storage_service=storage_service,
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
    storage_service, url: str, expected_output: str
):
    assert_url_content(
        storage_service=storage_service,
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
            {},
        ),
        (
            "/studies/STA-mini/input/areas/list",
            ["de", "es", "fr", "it"],
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
            {
                0: {i: 0 for i in range(365)},
                1: {i: 0.5 for i in range(365)},
                2: {i: 1 for i in range(365)},
            },
        ),
        (
            "/studies/STA-mini/input/thermal/series/fr/05_nuclear/series",
            {0: {i: 2000 for i in range(8760)}},
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
            {
                0: {i: 100000 for i in range(8760)},
                1: {i: 100000 for i in range(8760)},
                2: {i: 0.01 for i in range(8760)},
                3: {i: 0.01 for i in range(8760)},
                4: {i: 0 for i in range(8760)},
                5: {i: 0 for i in range(8760)},
                6: {i: 0 for i in range(8760)},
                7: {i: 0 for i in range(8760)},
            },
        ),
        (
            "/studies/STA-mini/input/load/prepro/fr/k",
            "file/STA-mini/input/load/prepro/fr/k.txt",
        ),
        (
            "/studies/STA-mini/input/load/series/load_fr",
            {0: {i: (i % 168) * 100 for i in range(8760)}},
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
            {},
        ),
        (
            "/studies/STA-mini/input/wind/prepro/fr/k",
            "file/STA-mini/input/wind/prepro/fr/k.txt",
        ),
        (
            "/studies/STA-mini/input/wind/series/wind_fr",
            {},
        ),
    ],
)
def test_sta_mini_input(storage_service, url: str, expected_output: str):
    assert_with_errors(
        storage_service=storage_service,
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
            "/studies/STA-mini/output/1/economy/mc-all/grid/areas",
            "file/STA-mini/output/20201014-1422eco-hello/economy/mc-all/grid/areas.txt",
        ),
        ("/studies/STA-mini/output/1/economy/mc-all/links/de/fr", {}),
        (
            "/studies/STA-mini/output/1/economy/mc-ind/00001/links/de/fr/values-hourly",
            de_fr_values_hourly,
        ),
        (
            "/studies/STA-mini/output/1/economy/mc-ind/00001/areas/de/details-annual",
            de_details_hourly,
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
def test_sta_mini_output(storage_service, url: str, expected_output: str):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
def test_sta_mini_copy(storage_service) -> None:

    source_study_name = "STA-mini"
    destination_study_name = "copy-STA-mini"

    app = Flask(__name__)
    build_storage(
        app,
        session=Mock(),
        user_service=Mock(),
        storage_service=storage_service,
        config=storage_service.study_service.config,
    )
    client = app.test_client()
    result = client.post(
        f"/studies/{source_study_name}/copy?dest={destination_study_name}"
    )

    assert result.status_code == HTTPStatus.CREATED.value
    uuid = result.data.decode("utf-8")

    parameters = RequestParameters(user=ADMIN)
    data_source = storage_service.get(source_study_name, -1, parameters)
    data_destination = storage_service.get(uuid, -1, parameters)

    link_url_source = data_source["input"]["links"]["de"]["fr"]
    assert link_url_source == "file/STA-mini/input/links/de/fr.txt"

    link_url_destination = data_destination["input"]["links"]["de"]["fr"]
    assert link_url_destination == f"file/{uuid}/input/links/de/fr.txt"

    result_source = client.get(link_url_source)
    matrix_source = result_source.data
    result_destination = client.get(link_url_destination)
    matrix_destination = result_destination.data

    assert matrix_source == matrix_destination

    def replace_study_name(data: JSON) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.startswith("file/"):
                    data[key] = value.replace(uuid, source_study_name)
                else:
                    replace_study_name(value)

    replace_study_name(data_destination)
    del data_source["output"]
    data_source["study"] = {}
    data_destination["study"] = {}

    assert data_source == data_destination


@pytest.mark.integration_test
def test_sta_mini_list_studies(storage_service) -> None:
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
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
def notest_sta_mini_with_wrong_output_folder(
    storage_service: StorageService, sta_mini_path: Path
) -> None:
    # TODO why a wrong test should success
    (sta_mini_path / "output" / "maps").mkdir()

    url = "/studies/STA-mini/Desktop/.shellclassinfo/infotip"
    expected_output = "Antares Study7.0: STA-mini"

    assert_with_errors(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
def test_sta_mini_import(tmp_path: Path, storage_service) -> None:

    params = RequestParameters(user=ADMIN)
    path_study = storage_service.get_study_path("STA-mini", params)
    sta_mini_zip_filepath = shutil.make_archive(tmp_path, "zip", path_study)
    sta_mini_zip_path = Path(sta_mini_zip_filepath)

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=storage_service,
        session=Mock(),
        user_service=Mock(),
        config=storage_service.study_service.config,
    )
    client = app.test_client()

    study_data = io.BytesIO(sta_mini_zip_path.read_bytes())
    result = client.post("/studies", data={"study": (study_data, "study.zip")})

    assert result.status_code == HTTPStatus.CREATED.value


@pytest.mark.integration_test
def test_sta_mini_import_compact(tmp_path: Path, storage_service) -> None:

    params = RequestParameters(user=ADMIN)
    zip_study_stream = storage_service.export_study(
        "STA-mini", compact=True, params=params
    )

    app = Flask(__name__)
    build_storage(
        app,
        session=Mock(),
        user_service=Mock(),
        storage_service=storage_service,
        config=storage_service.study_service.config,
    )
    client = app.test_client()
    result = client.post(
        "/studies", data={"study": (zip_study_stream, "study.zip")}
    )

    assert result.status_code == HTTPStatus.CREATED.value


@pytest.mark.integration_test
def test_sta_mini_import_output(tmp_path: Path, storage_service) -> None:
    params = RequestParameters(user=ADMIN)

    path_study_output = (
        storage_service.get_study_path("STA-mini", params)
        / "output"
        / "20201014-1422eco-hello"
    )
    sta_mini_output_zip_filepath = shutil.make_archive(
        tmp_path, "zip", path_study_output
    )

    shutil.rmtree(path_study_output)

    sta_mini_output_zip_path = Path(sta_mini_output_zip_filepath)

    app = Flask(__name__)
    build_storage(
        app,
        storage_service=storage_service,
        session=Mock(),
        user_service=Mock(),
        config=storage_service.study_service.config,
    )
    client = app.test_client()

    study_output_data = io.BytesIO(sta_mini_output_zip_path.read_bytes())
    result = client.post(
        "/studies/STA-mini/output",
        data={"output": (study_output_data, "output.zip")},
    )

    assert result.status_code == HTTPStatus.ACCEPTED.value


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/studies/STA-mini/output/1/ts-numbers/hydro/de,fr/",
            {
                "de": "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/hydro/de.txt",
                "fr": "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/hydro/fr.txt",
            },
        ),
        (
            "/studies/STA-mini/output/1/ts-numbers/hydro/*/",
            {
                "de": "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/hydro/de.txt",
                "fr": "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/hydro/fr.txt",
                "it": "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/hydro/it.txt",
                "es": "file/STA-mini/output/20201014-1422eco-hello/ts-numbers/hydro/es.txt",
            },
        ),
    ],
)
def test_sta_mini_filter(storage_service, url: str, expected_output: dict):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )
