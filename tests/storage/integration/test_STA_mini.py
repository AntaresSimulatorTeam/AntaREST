# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import io
import shutil
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from typing import Union
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.application import create_app_ctxt
from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.model import JSON
from antarest.core.roles import RoleType
from antarest.matrixstore.service import MatrixService
from antarest.study.main import build_study_service
from antarest.study.service import StudyService
from antarest.study.storage.study_download_utils import BadOutputFormat
from tests.helpers import assert_study, with_admin_user
from tests.storage.integration.conftest import UUID
from tests.storage.integration.data.de_details_hourly import de_details_hourly
from tests.storage.integration.data.de_fr_values_hourly import de_fr_values_hourly
from tests.storage.integration.data.digest_file import digest_file
from tests.storage.integration.data.set_id_annual import set_id_annual
from tests.storage.integration.data.set_values_monthly import set_values_monthly

ADMIN = JWTUser(
    id=1,
    impersonator=1,
    type="users",
    groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
)


def create_test_client(service: StudyService) -> TestClient:
    build_ctxt = create_app_ctxt(FastAPI(title=__name__))
    build_study_service(
        build_ctxt,
        cache=Mock(),
        user_service=Mock(),
        task_service=Mock(),
        file_transfer_manager=Mock(),
        study_service=service,
        matrix_service=Mock(spec=MatrixService),
        config=service.storage_service.raw_study_service.config,
    )
    return TestClient(build_ctxt.build())


def assert_url_content(storage_service: StudyService, url: str, expected_output: dict) -> None:
    client = create_test_client(storage_service)
    res = client.get(url)
    assert_study(res.json(), expected_output)


def assert_with_errors(
    storage_service: StudyService,
    url: str,
    expected_output: Union[str, dict],
    formatted: bool = True,
) -> None:
    url = url[len("/v1/studies/") :]
    uuid, url = url.split("/raw?path=")
    output = storage_service.get(uuid=uuid, url=url, depth=3, formatted=formatted)
    assert_study(
        output,
        expected_output,
    )


@with_admin_user
@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            f"/v1/studies/{UUID}/raw?path=settings/generaldata/general/horizon",
            2030,
        ),
        (f"/v1/studies/{UUID}/raw?path=settings/simulations", {}),
    ],
)
def test_sta_mini_settings(storage_service, url: str, expected_output: str):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@with_admin_user
@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            f"/v1/studies/{UUID}/raw?path=layers/layers/activeLayer/showAllLayer",
            True,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=layers/layers/layers/0",
            "All",
        ),
    ],
)
def test_sta_mini_layers_layers(storage_service, url: str, expected_output: str):
    assert_url_content(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@with_admin_user
@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            f"/v1/studies/{UUID}/raw?path=Desktop/.shellclassinfo/iconfile",
            "settings/resources/study.ico",
        ),
        (
            f"/v1/studies/{UUID}/raw?path=Desktop/.shellclassinfo/infotip",
            "Antares Study7.0: STA-mini",
        ),
        (f"/v1/studies/{UUID}/raw?path=Desktop/.shellclassinfo/iconindex", 0),
    ],
)
def test_sta_mini_desktop(storage_service, url: str, expected_output: str):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@with_admin_user
@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            f"/v1/studies/{UUID}/raw?path=study/antares/created",
            1480683452,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=study/antares/author",
            "Andrea SGATTONI",
        ),
    ],
)
def test_sta_mini_study_antares(storage_service, url: str, expected_output: str):
    assert_url_content(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


buffer = io.StringIO()
df = pd.DataFrame(np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 8760))
df.to_csv(buffer, sep="\t", header=False, index=False, float_format="%.6f")
expected_min_gen_response = buffer.getvalue()


@with_admin_user
@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output, formatted",
    [
        (f"/v1/studies/{UUID}/raw?path=input/bindingconstraints/bindingconstraints", {}, True),
        (
            f"/v1/studies/{UUID}/raw?path=input/hydro/series/de/mod",
            {
                "columns": [0, 1, 2],
                "index": list(range(365)),
                "data": [[0.0]] * 365,
            },
            True,
        ),
        (f"/v1/studies/{UUID}/raw?path=input/areas/list", ["DE", "ES", "FR", "IT"], True),
        (f"/v1/studies/{UUID}/raw?path=input/areas/sets/all areas/output", False, True),
        (
            f"/v1/studies/{UUID}/raw?path=input/areas/de/optimization/nodal optimization/spread-spilled-energy-cost",
            0,
            True,
        ),
        (f"/v1/studies/{UUID}/raw?path=input/areas/de/ui/layerX/0", 1, True),
        (f"/v1/studies/{UUID}/raw?path=input/hydro/allocation/de/[allocation]/de", 1, True),
        (
            f"/v1/studies/{UUID}/raw?path=input/hydro/common/capacity/reservoir_fr",
            {
                "columns": [0, 1, 2],
                "index": list(range(365)),
                "data": [[0, 0.5, 1]] * 365,
            },
            True,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/thermal/series/fr/05_nuclear/series",
            {
                "columns": [0],
                "index": list(range(8760)),
                "data": [[2000]] * 8760,
            },
            True,
        ),
        (f"/v1/studies/{UUID}/raw?path=input/hydro/prepro/correlation/general/mode", "annual", True),
        (f"/v1/studies/{UUID}/raw?path=input/hydro/prepro/fr/prepro/prepro/intermonthly-correlation", 0.5, True),
        (
            f"/v1/studies/{UUID}/raw?path=input/hydro/prepro/fr/energy",
            {"data": [[]], "index": [0], "columns": []},
            True,
        ),
        (f"/v1/studies/{UUID}/raw?path=input/hydro/hydro/inter-monthly-breakdown/fr", 1, True),
        (f"/v1/studies/{UUID}/raw?path=input/thermal/areas/unserverdenergycost/de", 3000.0, True),
        (f"/v1/studies/{UUID}/raw?path=input/thermal/clusters/fr/list/05_nuclear/marginal-cost", 50, True),
        (f"/v1/studies/{UUID}/raw?path=input/links/fr/properties/it/hurdles-cost", True, True),
        (
            f"/v1/studies/{UUID}/raw?path=input/links/fr/it",
            {
                "columns": list(range(8)),
                "index": list(range(8760)),
                "data": [[100000, 100000, 0.01, 0.01, 0, 0, 0, 0]] * 8760,
            },
            True,
        ),
        (f"/v1/studies/{UUID}/raw?path=input/load/prepro/fr/k", {"data": [[]], "index": [0], "columns": []}, True),
        (
            f"/v1/studies/{UUID}/raw?path=input/load/series",
            {
                "load_de": "matrixfile://load_de.txt",
                "load_es": "matrixfile://load_es.txt",
                "load_fr": "matrixfile://load_fr.txt",
                "load_it": "matrixfile://load_it.txt",
            },
            True,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/load/series/load_fr",
            {
                "columns": [0],
                "index": list(range(8760)),
                "data": [[i % 168 * 100] for i in range(8760)],
            },
            True,
        ),
        pytest.param(
            f"/v1/studies/{UUID}/raw?path=input/misc-gen/miscgen-fr",
            {
                "columns": [0, 1, 2, 3, 4, 5, 6, 7],
                "index": list(range(8760)),
                "data": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 8760,
            },
            True,
            id="empty_matrix_formatted",
        ),
        pytest.param(
            f"/v1/studies/{UUID}/raw?path=input/misc-gen/miscgen-fr",
            expected_min_gen_response,
            False,
            id="empty_matrix_unformatted",
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/reserves/fr",
            {
                "columns": [0],
                "index": list(range(8760)),
                "data": [[0.0]] * 8760,
            },
            True,
        ),
        (f"/v1/studies/{UUID}/raw?path=input/solar/prepro/fr/k", {"data": [[]], "index": [0], "columns": []}, True),
        (
            f"/v1/studies/{UUID}/raw?path=input/solar/series/solar_fr",
            {
                "columns": [0],
                "index": list(range(8760)),
                "data": [[0.0]] * 8760,
            },
            True,
        ),
        (f"/v1/studies/{UUID}/raw?path=input/wind/prepro/fr/k", {"data": [[]], "index": [0], "columns": []}, True),
        (
            f"/v1/studies/{UUID}/raw?path=input/wind/series/wind_fr",
            {
                "columns": [0],
                "index": list(range(8760)),
                "data": [[0.0]] * 8760,
            },
            True,
        ),
    ],
)
def test_sta_mini_input(storage_service, url: str, expected_output: dict, formatted: bool):
    assert_with_errors(storage_service=storage_service, url=url, expected_output=expected_output, formatted=formatted)


@with_admin_user
@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            f"/v1/studies/{UUID}/raw?path=output/20241807-1540eco-extra-outputs/economy/mc-all/binding_constraints/binding-constraints-annual",
            {
                "columns": [
                    ("contrainte (<)", " ", "EXP"),
                    ("contrainte (<)", " ", "std"),
                    ("contrainte (<)", " ", "min"),
                    ("contrainte (<)", " ", "max"),
                ],
                "index": ["Annual"],
                "data": [[0.0, 0.0, 0.0, 0.0]],
            },
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20241807-1540eco-extra-outputs/economy/mc-all/areas/@ all areas/values-monthly",
            set_values_monthly,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20241807-1540eco-extra-outputs/economy/mc-all/areas/@ all areas/id-annual",
            set_id_annual,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20241807-1540eco-extra-outputs/ts-numbers/bindingconstraints/default",
            [1],
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/annualSystemCost",
            b"EXP : 185808000\nSTD : 0\nMIN : 185808000\nMAX : 185808000\n",
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/checkIntegrity",
            b"""1.85808475215665e+08
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
            f"/v1/studies/{UUID}/raw?path=output/20201014-1425eco-goodbye/simulation-comments",
            b"",
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/about-the-study/areas",
            b"DE\r\nES\r\nFR\r\nIT\r\n",
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1425eco-goodbye/about-the-study/comments",
            b"",
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1427eco/about-the-study/links",
            b"de\n\tfr\nes\n\tfr\nfr\n\tit\nit\n",
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1430adq/about-the-study/parameters/general/horizon",
            2030,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/about-the-study/study/antares/author",
            "Andrea SGATTONI",
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/economy/mc-all/grid/areas",
            {"columns": ["id", "name"], "data": [["de", "DE"], ["es", "ES"], ["fr", "FR"], ["it", "IT"]]},
        ),
        (f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/economy/mc-all/grid/digest", digest_file),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/economy/mc-all/grid/links",
            {"columns": ["upstream", "downstream"], "data": [["de", "fr"], ["es", "fr"], ["fr", "it"]]},
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/economy/mc-all/links/de/fr",
            {},
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/economy/mc-ind/00001/links/de/fr",
            {"values-hourly": "matrixfile://values-hourly.txt"},
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/economy/mc-ind/00001/links/de/fr/values-hourly",
            de_fr_values_hourly,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/economy/mc-ind/00001/areas/de/details-annual",
            de_details_hourly,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/ts-numbers/hydro/de",
            [1],
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/ts-numbers/load/de",
            [1],
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/ts-numbers/solar/de",
            [1],
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/ts-numbers/wind/de",
            [1],
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/ts-numbers/thermal/de/07_gas",
            [1],
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/info/general/version",
            700,
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1430adq-2/about-the-study/areas",
            b"DE\r\nES\r\nFR\r\nIT\r\n",
        ),
    ],
)
def test_sta_mini_output(storage_service, url: str, expected_output: dict):
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
            f"/v1/studies/{UUID}/raw?path=user/expansion/settings",
            {
                "optimality_gap": 1,
                "max_iteration": "+Inf",
                "uc_type": '"expansion_fast"',
                "master": '"integer"',
                "yearly-weights": "None",
                "additional-constraints": "None",
                "relaxed_optimality_gap": 0.00001,
                # legacy attributes from version < 800
                "cut-type": '"average"',
                "ampl.solver": '"cbc"',
                "ampl.presolve": 0,
                "ampl.solve_bounds_frequency": 1000000,
            },
        ),
        (
            f"/v1/studies/{UUID}/raw?path=user/expansion/candidates",
            {},
        ),
        (
            f"/v1/studies/{UUID}/raw?path=user/expansion/capa",
            {},
        ),
    ],
)
def test_sta_mini_expansion(storage_service, url: str, expected_output: dict):
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
def test_sta_mini_copy(storage_service) -> None:
    source_study_name = UUID
    destination_study_name = "copy-STA-mini"

    client = create_test_client(storage_service)
    result = client.post(f"/v1/studies/{source_study_name}/copy?dest={destination_study_name}&use_task=false")

    assert result.status_code == HTTPStatus.CREATED.value
    uuid = result.json()

    data_source = storage_service.get(source_study_name, "/", -1, True)
    data_destination = storage_service.get(uuid, "/", -1, True)

    link_url_source = data_source["input"]["links"]["de"]["fr"]
    assert "matrixfile://fr.txt" == link_url_source

    link_url_destination = data_destination["input"]["links"]["de"]["fr"]
    assert "matrixfile://fr.txt" == link_url_destination

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
        UUID: {
            "id": UUID,
            "name": "STA-mini",
            "version": 700,
            "created": str(datetime.fromtimestamp(1480683452)),
            "updated": str(datetime.fromtimestamp(1602678639)),
            "type": "rawstudy",
            "owner": {"id": None, "name": "Andrea SGATTONI"},
            "groups": [],
            "public_mode": "NONE",
            "workspace": "default",
            "managed": True,
            "archived": False,
            "horizon": "2030",
            "folder": None,
            "tags": [],
        }
    }
    url = "/v1/studies"
    assert_url_content(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
def notest_sta_mini_with_wrong_output_folder(storage_service: StudyService, sta_mini_path: Path) -> None:
    # TODO why a wrong test should success
    (sta_mini_path / "output" / "maps").mkdir()

    url = f"/v1/studies/{UUID}/raw?path=Desktop/.shellclassinfo/infotip"
    expected_output = "Antares Study7.0: STA-mini"

    assert_with_errors(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@pytest.mark.integration_test
def test_sta_mini_import(tmp_path: Path, storage_service) -> None:
    path_study = storage_service.get_study_path(UUID)
    sta_mini_zip_filepath = shutil.make_archive(tmp_path, "zip", path_study)
    sta_mini_zip_path = Path(sta_mini_zip_filepath)

    client = create_test_client(storage_service)

    study_data = io.BytesIO(sta_mini_zip_path.read_bytes())
    result = client.post("/v1/studies/_import", files={"study": study_data})

    assert result.status_code == HTTPStatus.CREATED.value


@pytest.mark.integration_test
def test_sta_mini_import_output(tmp_path: Path, storage_service) -> None:
    path_study_output = storage_service.get_study_path(UUID) / "output" / "20201014-1422eco-hello"
    sta_mini_output_zip_filepath = shutil.make_archive(tmp_path, "zip", path_study_output)

    shutil.rmtree(path_study_output)

    sta_mini_output_zip_path = Path(sta_mini_output_zip_filepath)

    client = create_test_client(storage_service)

    study_output_data = io.BytesIO(sta_mini_output_zip_path.read_bytes())
    result = client.post(
        f"/v1/studies/{UUID}/output",
        files={"output": study_output_data},
    )

    assert result.status_code == HTTPStatus.ACCEPTED.value


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/ts-numbers/hydro/de,fr/",
            {
                "de": [1],
                "fr": [1],
            },
        ),
        (
            f"/v1/studies/{UUID}/raw?path=output/20201014-1422eco-hello/ts-numbers/hydro/*/",
            {
                "de": [1],
                "fr": [1],
                "it": [1],
                "es": [1],
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


def test_sta_mini_output_variables_nominal_case(output_service):
    variables = output_service.output_variables_information(UUID, "20201014-1422eco-hello")
    assert variables["area"] == [
        "OV. COST",
        "OP. COST",
        "MRG. PRICE",
        "CO2 EMIS.",
        "BALANCE",
        "ROW BAL.",
        "PSP",
        "MISC. NDG",
        "LOAD",
        "H. ROR",
        "WIND",
        "SOLAR",
        "NUCLEAR",
        "LIGNITE",
        "COAL",
        "GAS",
        "OIL",
        "MIX. FUEL",
        "MISC. DTG",
        "H. STOR",
        "H. PUMP",
        "H. LEV",
        "H. INFL",
        "H. OVFL",
        "H. VAL",
        "H. COST",
        "UNSP. ENRG",
        "SPIL. ENRG",
        "LOLD",
        "LOLP",
        "AVL DTG",
        "DTG MRG",
        "MAX MRG",
        "NP COST",
        "NODU",
    ]
    assert variables["link"] == [
        "FLOW LIN.",
        "UCAP LIN.",
        "LOOP FLOW",
        "FLOW QUAD.",
        "CONG. FEE (ALG.)",
        "CONG. FEE (ABS.)",
        "MARG. COST",
        "CONG. PROB +",
        "CONG. PROB -",
        "HURDLE COST",
    ]


def test_sta_mini_output_variables_no_mc_ind(output_service):
    with pytest.raises(BadOutputFormat, match=r"Not a year by year simulation"):
        output_service.output_variables_information(UUID, "20201014-1427eco")


def test_sta_mini_output_variables_no_links(output_service):
    study_path = Path(output_service._study_service.get_study(UUID).path)
    links_folder = study_path / "output" / "20201014-1422eco-hello" / "economy" / "mc-ind" / "00001" / "links"
    shutil.rmtree(links_folder)
    variables = output_service.output_variables_information(UUID, "20201014-1422eco-hello")
    # When there's no links folder, asserts the endpoint doesn't fail and simply return an empty list
    assert variables["link"] == []


def test_sta_mini_output_variables_no_areas(output_service):
    study_path = Path(output_service._study_service.get_study(UUID).path)
    areas_mc_ind_folder = study_path / "output" / "20201014-1422eco-hello" / "economy" / "mc-ind" / "00001" / "areas"
    areas_mc_all_folder = study_path / "output" / "20201014-1422eco-hello" / "economy" / "mc-all" / "areas"
    shutil.rmtree(areas_mc_ind_folder)
    shutil.rmtree(areas_mc_all_folder)
    variables = output_service.output_variables_information(UUID, "20201014-1422eco-hello")
    # When there's no areas folder, asserts the endpoint doesn't fail and simply return an empty list
    assert variables["area"] == []
