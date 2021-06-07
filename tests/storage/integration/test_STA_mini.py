import io
import json
import shutil
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock, call

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.common.custom_types import JSON
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.storage.main import build_storage

from antarest.storage.service import StorageService
from antarest.common.requests import (
    RequestParameters,
)
from tests.conftest import assert_study
from tests.storage.integration.data.de_details_hourly import de_details_hourly
from tests.storage.integration.data.de_fr_values_hourly import (
    de_fr_values_hourly,
)
from tests.storage.integration.data.simulation_log import simulation_log

ADMIN = JWTUser(
    id=1,
    impersonator=1,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)


def assert_url_content(
    storage_service: StorageService, url: str, expected_output: str
) -> None:
    app = FastAPI(title=__name__)
    build_storage(
        app,
        session=Mock(),
        user_service=Mock(),
        storage_service=storage_service,
        config=storage_service.study_service.config,
    )
    client = TestClient(app)
    res = client.get(url)
    assert_study(res.json(), expected_output)


def assert_with_errors(
    storage_service: StorageService, url: str, expected_output: dict
) -> None:
    url = url[len("/v1/studies/") :]
    params = RequestParameters(user=ADMIN)
    assert_study(
        storage_service.get(route=url, depth=3, params=params), expected_output
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        ("/v1/studies/STA-mini/settings/generaldata/general/horizon", 2030),
        ("/v1/studies/STA-mini/settings/simulations", {}),
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
            "/v1/studies/STA-mini/layers/layers/activeLayer/showAllLayer",
            True,
        ),
        (
            "/v1/studies/STA-mini/layers/layers/layers/0",
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
            "/v1/studies/STA-mini/Desktop/.shellclassinfo/iconfile",
            "settings/resources/study.ico",
        ),
        (
            "/v1/studies/STA-mini/Desktop/.shellclassinfo/infotip",
            "Antares Study7.0: STA-mini",
        ),
        ("/v1/studies/STA-mini/Desktop/.shellclassinfo/iconindex", 0),
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
            "/v1/studies/STA-mini/study/antares/created",
            1480683452,
        ),
        (
            "/v1/studies/STA-mini/study/antares/author",
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
            "/v1/studies/STA-mini/input/bindingconstraints/bindingconstraints",
            {},
        ),
        (
            "/v1/studies/STA-mini/input/hydro/series/de/mod",
            {},
        ),
        (
            "/v1/studies/STA-mini/input/areas/list",
            ["de", "es", "fr", "it"],
        ),
        ("/v1/studies/STA-mini/input/areas/sets/all areas/output", False),
        (
            "/v1/studies/STA-mini/input/areas/de/optimization/nodal optimization/spread-spilled-energy-cost",
            0,
        ),
        ("/v1/studies/STA-mini/input/areas/de/ui/layerX/0", 1),
        ("/v1/studies/STA-mini/input/hydro/allocation/de/[allocation/de", 1),
        (
            "/v1/studies/STA-mini/input/hydro/common/capacity/reservoir_fr",
            {
                "columns": [0, 1, 2],
                "index": list(range(365)),
                "data": [[0, 0.5, 1]] * 365,
            },
        ),
        (
            "/v1/studies/STA-mini/input/thermal/series/fr/05_nuclear/series",
            {
                "columns": [0],
                "index": list(range(8760)),
                "data": [[2000]] * 8760,
            },
        ),
        (
            "/v1/studies/STA-mini/input/hydro/prepro/correlation/general/mode",
            "annual",
        ),
        (
            "/v1/studies/STA-mini/input/hydro/prepro/fr/prepro/prepro/intermonthly-correlation",
            0.5,
        ),
        (
            "/v1/studies/STA-mini/input/hydro/prepro/fr/energy",
            "",
        ),
        (
            "/v1/studies/STA-mini/input/hydro/hydro/inter-monthly-breakdown/fr",
            1,
        ),
        (
            "/v1/studies/STA-mini/input/thermal/areas/unserverdenergycost/de",
            3000.0,
        ),
        (
            "/v1/studies/STA-mini/input/thermal/clusters/fr/list/05_nuclear/marginal-cost",
            50,
        ),
        (
            "/v1/studies/STA-mini/input/links/fr/properties/it/hurdles-cost",
            True,
        ),
        (
            "/v1/studies/STA-mini/input/links/fr/it",
            {
                "columns": list(range(8)),
                "index": list(range(8760)),
                "data": [[100000, 100000, 0.01, 0.01, 0, 0, 0, 0]] * 8760,
            },
        ),
        (
            "/v1/studies/STA-mini/input/load/prepro/fr/k",
            "",
        ),
        (
            "/v1/studies/STA-mini/input/load/series",
            {
                "load_de": "file:///...../input/load/series/load_de.txt",
                "load_es": "file:///...../input/load/series/load_es.txt",
                "load_fr": "file:///...../input/load/series/load_fr.txt",
                "load_it": "file:///...../input/load/series/load_it.txt",
            },
        ),
        (
            "/v1/studies/STA-mini/input/load/series/load_fr",
            {
                "columns": [0],
                "index": list(range(8760)),
                "data": [[i % 168 * 100] for i in range(8760)],
            },
        ),
        (
            "/v1/studies/STA-mini/input/misc-gen/miscgen-fr",
            "",
        ),
        (
            "/v1/studies/STA-mini/input/reserves/fr",
            "",
        ),
        (
            "/v1/studies/STA-mini/input/solar/prepro/fr/k",
            "",
        ),
        (
            "/v1/studies/STA-mini/input/solar/series/solar_fr",
            {},
        ),
        (
            "/v1/studies/STA-mini/input/wind/prepro/fr/k",
            "",
        ),
        (
            "/v1/studies/STA-mini/input/wind/series/wind_fr",
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
            "/v1/studies/STA-mini/output/3/annualSystemCost",
            "EXP : 185808000\nSTD : 0\nMIN : 185808000\nMAX : 185808000\n",
        ),
        (
            "/v1/studies/STA-mini/output/1/checkIntegrity",
            """1.85808475215665e+08
0.00000000000000e+00
1.85808475215665e+08
1.85808475215665e+08
1.85808475215665e+08
0.00000000000000e+00
1.85808475215665e+08
1.85808475215665e+08
""",
        ),
        (
            "/v1/studies/STA-mini/output/4/simulation-comments",
            "",
        ),
        (
            "/v1/studies/STA-mini/output/2/simulation",
            simulation_log,
        ),
        (
            "/v1/studies/STA-mini/output/1/about-the-study/areas",
            "DE\nES\nFR\nIT\n",
        ),
        (
            "/v1/studies/STA-mini/output/2/about-the-study/comments",
            "",
        ),
        (
            "/v1/studies/STA-mini/output/3/about-the-study/links",
            "de\n\tfr\nes\n\tfr\nfr\n\tit\nit\n",
        ),
        (
            "/v1/studies/STA-mini/output/4/about-the-study/parameters/general/horizon",
            2030,
        ),
        (
            "/v1/studies/STA-mini/output/1/about-the-study/study/antares/author",
            "Andrea SGATTONI",
        ),
        (
            "/v1/studies/STA-mini/output/1/economy/mc-all/grid/areas",
            "id\tname\nde\tDE\nes\tES\nfr\tFR\nit\tIT\n",
        ),
        ("/v1/studies/STA-mini/output/1/economy/mc-all/links/de/fr", {}),
        (
            "/v1/studies/STA-mini/output/1/economy/mc-ind/00001/links/de/fr",
            {
                "values-hourly": "file://...../economy/mc-inde/0001/links/de - fr/values-hourly.txt"
            },
        ),
        (
            "/v1/studies/STA-mini/output/1/economy/mc-ind/00001/links/de/fr/values-hourly",
            de_fr_values_hourly,
        ),
        (
            "/v1/studies/STA-mini/output/1/economy/mc-ind/00001/areas/de/details-annual",
            de_details_hourly,
        ),
        (
            "/v1/studies/STA-mini/output/1/ts-numbers/hydro/de",
            "size:1x1\n1\n",
        ),
        (
            "/v1/studies/STA-mini/output/1/ts-numbers/load/de",
            "size:1x1\n1\n",
        ),
        (
            "/v1/studies/STA-mini/output/1/ts-numbers/solar/de",
            "size:1x1\n1\n",
        ),
        (
            "/v1/studies/STA-mini/output/1/ts-numbers/wind/de",
            "size:1x1\n1\n",
        ),
        (
            "/v1/studies/STA-mini/output/1/ts-numbers/thermal/de/07_gas",
            "size:1x1\n1\n",
        ),
        (
            "/v1/studies/STA-mini/output/1/info/general/version",
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
    input_link = "input/links/de/fr.txt"

    source_study_name = "STA-mini"
    destination_study_name = "copy-STA-mini"

    app = FastAPI(title=__name__)
    build_storage(
        app,
        session=Mock(),
        user_service=Mock(),
        storage_service=storage_service,
        config=storage_service.study_service.config,
    )
    client = TestClient(app)
    result = client.post(
        f"/v1/studies/{source_study_name}/copy?dest={destination_study_name}"
    )

    assert result.status_code == HTTPStatus.CREATED.value
    uuid = result.json()[len("/studies/") :]

    parameters = RequestParameters(user=ADMIN)
    data_source = storage_service.get(source_study_name, -1, parameters)
    data_destination = storage_service.get(uuid, -1, parameters)

    link_url_source = data_source["input"]["links"]["de"]["fr"]
    assert input_link in link_url_source

    link_url_destination = data_destination["input"]["links"]["de"]["fr"]
    assert input_link in link_url_destination

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

    assert_study(data_source, data_destination)


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
    url = "/v1/studies"
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

    url = "/v1/studies/STA-mini/Desktop/.shellclassinfo/infotip"
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

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=storage_service,
        session=Mock(),
        user_service=Mock(),
        config=storage_service.study_service.config,
    )
    client = TestClient(app)

    study_data = io.BytesIO(sta_mini_zip_path.read_bytes())
    result = client.post("/v1/studies", files={"study": study_data})

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

    app = FastAPI(title=__name__)
    build_storage(
        app,
        storage_service=storage_service,
        session=Mock(),
        user_service=Mock(),
        config=storage_service.study_service.config,
    )
    client = TestClient(app)

    study_output_data = io.BytesIO(sta_mini_output_zip_path.read_bytes())
    result = client.post(
        "/v1/studies/STA-mini/output",
        files={"output": study_output_data},
    )

    assert result.status_code == HTTPStatus.ACCEPTED.value


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            "/v1/studies/STA-mini/output/1/ts-numbers/hydro/de,fr/",
            {
                "de": "size:1x1\n1\n",
                "fr": "size:1x1\n1\n",
            },
        ),
        (
            "/v1/studies/STA-mini/output/1/ts-numbers/hydro/*/",
            {
                "de": "size:1x1\n1\n",
                "fr": "size:1x1\n1\n",
                "it": "size:1x1\n1\n",
                "es": "size:1x1\n1\n",
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
