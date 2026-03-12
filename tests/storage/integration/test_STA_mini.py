# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from typing import Any, Union
from unittest.mock import Mock

import numpy as np
import pandas as pd
import polars as pl
import pytest
from fastapi import FastAPI
from sqlalchemy import Engine
from starlette.testclient import TestClient

from antarest.core.application import create_app_ctxt
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.core.utils.polars import create_polars_dataframe
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory, NormalizedMatrixUriMapper
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.output.model import OutputVariablesInformation
from antarest.output.routes import create_output_routes
from antarest.output.storage.file.repository import DbOutputVariables
from antarest.study.main import add_study_routes
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.common.prepro import default_k
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.prepro.area.area import default_energy
from antarest.study.storage.variantstudy.business.matrix_constants.common import fixed_4_columns
from tests.helpers import assert_study, with_admin_user, with_db_context
from tests.storage.integration.conftest import UUID
from tests.storage.integration.data.de_details_hourly import de_details_hourly
from tests.storage.integration.data.de_fr_values_hourly import de_fr_values_hourly
from tests.storage.integration.data.digest_file import digest_file
from tests.storage.integration.data.set_id_annual import set_id_annual
from tests.storage.integration.data.set_values_monthly import set_values_monthly


@pytest.fixture
def client(services, db_engine: Engine) -> TestClient:
    app = FastAPI(title=__name__)
    app.add_middleware(
        DBSessionMiddleware,
        custom_engine=db_engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    build_ctxt = create_app_ctxt(app)
    study_service, output_service, config = services
    add_study_routes(build_ctxt, study_service, Mock(), config)
    build_ctxt.api_root.include_router(
        create_output_routes(output_service, study_service.file_transfer_manager, config)
    )

    return TestClient(build_ctxt.build())


def assert_url_content(client: TestClient, url: str, expected_output: dict[str, Any] | str) -> None:
    res = client.get(url)
    assert_study(res.json(), expected_output)


def assert_with_errors(storage_service: StudyService, url: str, expected_output: Union[str, dict[str, Any]]) -> None:
    url = url[len("/v1/studies/") :]
    uuid, url = url.split("/raw?path=")
    # We use the `get_raw_content` method as it's the one called by the GET /raw endpoint.
    output = storage_service.get_raw_content(uuid=uuid, path=url, depth=3, formatted=True)
    assert_study(
        output,
        expected_output,
    )


@with_admin_user
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
def test_sta_mini_settings(storage_service: StudyService, url: str, expected_output: str) -> None:
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@with_admin_user
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
def test_sta_mini_layers_layers(client: TestClient, url: str, expected_output: str) -> None:
    assert_url_content(
        client=client,
        url=url,
        expected_output=expected_output,
    )


@with_admin_user
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
def test_sta_mini_desktop(storage_service: StudyService, url: str, expected_output: str) -> None:
    assert_with_errors(
        storage_service=storage_service,
        url=url,
        expected_output=expected_output,
    )


@with_admin_user
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
def test_sta_mini_study_antares(client: TestClient, url: str, expected_output: str) -> None:
    assert_url_content(
        client=client,
        url=url,
        expected_output=expected_output,
    )


@with_admin_user
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (f"/v1/studies/{UUID}/raw?path=input/bindingconstraints/bindingconstraints", {}),
        (
            f"/v1/studies/{UUID}/raw?path=input/hydro/series/de/mod",
            pl.DataFrame(data=[[0.0]] * 365, schema=["0"]),
        ),
        (f"/v1/studies/{UUID}/raw?path=input/areas/list", ["DE", "ES", "FR", "IT"]),
        (f"/v1/studies/{UUID}/raw?path=input/areas/sets/all areas/output", False),
        (f"/v1/studies/{UUID}/raw?path=input/areas/de/optimization/nodal optimization/spread-spilled-energy-cost", 0),
        (f"/v1/studies/{UUID}/raw?path=input/areas/de/ui/layerX/0", 1),
        (f"/v1/studies/{UUID}/raw?path=input/hydro/allocation/de/[allocation]/de", 1),
        (
            f"/v1/studies/{UUID}/raw?path=input/hydro/common/capacity/reservoir_fr",
            pl.DataFrame(data=[[0, 0.5, 1]] * 365, schema=["0", "1", "2"]),
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/thermal/series/fr/05_nuclear/series",
            pl.DataFrame(data=[[2000]] * 8760, schema=["0"]),
        ),
        (f"/v1/studies/{UUID}/raw?path=input/hydro/prepro/correlation/general/mode", "annual"),
        (f"/v1/studies/{UUID}/raw?path=input/hydro/prepro/fr/prepro/prepro/intermonthly-correlation", 0.5),
        (f"/v1/studies/{UUID}/raw?path=input/hydro/prepro/fr/energy", create_polars_dataframe(default_energy())),
        (f"/v1/studies/{UUID}/raw?path=input/hydro/hydro/inter-monthly-breakdown/fr", 1),
        (f"/v1/studies/{UUID}/raw?path=input/thermal/areas/unserverdenergycost/de", 3000.0),
        (f"/v1/studies/{UUID}/raw?path=input/thermal/clusters/fr/list/05_nuclear/marginal-cost", 50),
        (f"/v1/studies/{UUID}/raw?path=input/links/fr/properties/it/hurdles-cost", True),
        (
            f"/v1/studies/{UUID}/raw?path=input/links/fr/it",
            create_polars_dataframe([[100000, 100000, 0.01, 0.01, 0, 0, 0, 0]] * 8760),
        ),
        (f"/v1/studies/{UUID}/raw?path=input/load/prepro/fr/k", create_polars_dataframe(default_k())),
        (
            f"/v1/studies/{UUID}/raw?path=input/load/series",
            {
                "load_de": "matrix://load_de.txt",
                "load_es": "matrix://load_es.txt",
                "load_fr": "matrix://load_fr.txt",
                "load_it": "matrix://load_it.txt",
            },
        ),
        (
            f"/v1/studies/{UUID}/raw?path=input/load/series/load_fr",
            pl.DataFrame(data=[[i % 168 * 100] for i in range(8760)], schema=["0"]),
        ),
        pytest.param(
            f"/v1/studies/{UUID}/raw?path=input/misc-gen/miscgen-fr",
            create_polars_dataframe([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 8760),
        ),
        (f"/v1/studies/{UUID}/raw?path=input/reserves/fr", fixed_4_columns()),
        (f"/v1/studies/{UUID}/raw?path=input/solar/prepro/fr/k", create_polars_dataframe(default_k())),
        (f"/v1/studies/{UUID}/raw?path=input/solar/series/solar_fr", pl.DataFrame(data=[[0.0]] * 8760, schema=["0"])),
        (f"/v1/studies/{UUID}/raw?path=input/wind/prepro/fr/k", create_polars_dataframe(default_k())),
        (f"/v1/studies/{UUID}/raw?path=input/wind/series/wind_fr", pl.DataFrame(data=[[0.0]] * 8760, schema=["0"])),
    ],
)
def test_sta_mini_input(storage_service: StudyService, url: str, expected_output: Any) -> None:
    assert_with_errors(storage_service=storage_service, url=url, expected_output=expected_output)


@pytest.mark.parametrize(
    "url, expected_output",
    [
        pytest.param(
            f"/v1/studies/{UUID}/raw?path=input/misc-gen/miscgen-fr",
            pd.DataFrame(np.array([[0, 0, 0, 0, 0, 0, 0, 0]] * 8760)),
            id="miscgen-fr",
        )
    ],
)
def test_sta_mini_input_for_R_scripts(client: TestClient, url: str, expected_output: pd.DataFrame) -> None:
    res = client.get(f"{url}&formatted=False")
    actual_output = pd.read_csv(io.BytesIO(res.content), sep="\t", header=None)
    pd.testing.assert_frame_equal(actual_output, expected_output, check_dtype=False)


@with_admin_user
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
            {"values-hourly": "matrix://values-hourly.txt"},
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
    ],
)
def test_sta_mini_output(storage_service: StudyService, url: str, expected_output: Any) -> None:
    assert_with_errors(storage_service=storage_service, url=url, expected_output=expected_output)


@with_admin_user
@pytest.mark.parametrize(
    "url, expected_output",
    [
        (
            f"/v1/studies/{UUID}/raw?path=user/expansion/settings",
            {
                "master": "relaxed",
                "uc_type": "expansion_fast",
                "optimality_gap": 1000000,
                "relative_gap": 1e-06,
                "relaxed_optimality_gap": 1e-05,
                "max_iteration": 200,
                "solver": "Xpress",
                "log_level": 1,
                "separation_parameter": 0.5,
                "batch_size": 96,
                "timelimit": 10000,
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
def test_sta_mini_expansion(storage_service: StudyService, url: str, expected_output: Any) -> None:
    assert_with_errors(storage_service=storage_service, url=url, expected_output=expected_output)


@with_admin_user
def test_sta_mini_copy(
    storage_service: StudyService, tmp_path: Path, matrix_service: ISimpleMatrixService, client: TestClient
) -> None:
    source_study_name = UUID
    destination_study_name = "copy-STA-mini"

    storage_service.job_result_repository.find_by_study_and_output_ids.return_value = []

    result = client.post(f"/v1/studies/{source_study_name}/copy?study_name={destination_study_name}&use_task=false")

    assert result.status_code == HTTPStatus.CREATED.value
    uuid = result.json()

    data_source = storage_service.get(source_study_name, "/", -1, True)
    data_destination = storage_service.get(uuid, "/", -1, True)

    link_url_source = data_source["input"]["links"]["de"]["fr"]
    assert "matrix://fr.txt" == link_url_source

    link_url_destination = data_destination["input"]["links"]["de"]["fr"]
    # The study is copied; therefore, it was normalized
    assert link_url_destination == "matrix://ef73d0226d966d7c085e03bf37f26986fb7bfaba0977f8f60acfa9109ded8c1f"

    # We should first denormalize the copied study to ensure it's the same exact study.
    denormalized_path = tmp_path / "denormalized_study"
    storage_service.export_study_flat(uuid, denormalized_path)

    config = build(denormalized_path, "")
    mapper_factory = MatrixUriMapperFactory(matrix_service=matrix_service)
    matrix_mapper = mapper_factory.create(NormalizedMatrixUriMapper.NORMALIZED)
    tree = FileStudyTree(matrix_mapper=matrix_mapper, config=config)
    data_destination = tree.get()

    del data_source["output"]

    assert_study(data_source, data_destination)


@with_admin_user
def test_sta_mini_list_studies(client: TestClient) -> None:
    expected_output = {
        UUID: {
            "id": UUID,
            "name": "STA-mini",
            "version": 700,
            "author": "Andrea SGATTONI",
            "editor": None,
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
            "directory_id": None,
            "parent_id": None,
        }
    }
    url = "/v1/studies"
    assert_url_content(client=client, url=url, expected_output=expected_output)


@with_admin_user
def test_sta_mini_import(tmp_path: Path, storage_service: StudyService, client: TestClient) -> None:
    path_study = storage_service.get_study_path(UUID)
    sta_mini_zip_filepath = shutil.make_archive(str(tmp_path), "zip", path_study)
    sta_mini_zip_path = Path(sta_mini_zip_filepath)

    study_data = io.BytesIO(sta_mini_zip_path.read_bytes())
    result = client.post("/v1/studies/_import", files={"study": study_data})

    assert result.status_code == HTTPStatus.CREATED.value


@with_admin_user
def test_sta_mini_import_output(tmp_path: Path, storage_service: StudyService, client: TestClient) -> None:
    path_study_output = storage_service.get_study_path(UUID) / "output" / "20201014-1422eco-hello"
    sta_mini_output_zip_filepath = shutil.make_archive(str(tmp_path), "zip", path_study_output)

    sta_mini_output_zip_path = Path(sta_mini_output_zip_filepath)

    study_output_data = io.BytesIO(sta_mini_output_zip_path.read_bytes())

    result = client.post(
        "/v1/studies",
        params={"name": "test"},
    )
    assert result.status_code == 201

    result = client.post(
        f"/v1/studies/{result.json()}/output",
        files={"output": study_output_data},
    )

    assert result.status_code == HTTPStatus.ACCEPTED.value


def _clean_db() -> None:
    """Cleans the OutputVariables table for other tests"""
    with db():
        db.session.query(DbOutputVariables).delete()
        db.session.commit()


@with_admin_user
@with_db_context
def test_sta_mini_output_variables(services) -> None:
    study_service, output_service, _ = services
    # Adds the study UUID inside the DB to avoid ForeignKey issues
    with db():
        study = study_service.get_study(UUID)
        db.session.add(study)
        db.session.commit()

    # Nominal case
    variables = output_service.get_output_variables_information(UUID, "20201014-1422eco-hello")
    assert variables.model_dump() == {
        "area": [
            "AVL DTG",
            "BALANCE",
            "CO2 EMIS.",
            "COAL",
            "DTG MRG",
            "GAS",
            "H. COST",
            "H. INFL",
            "H. LEV",
            "H. OVFL",
            "H. PUMP",
            "H. ROR",
            "H. STOR",
            "H. VAL",
            "LIGNITE",
            "LOAD",
            "LOLD",
            "LOLP",
            "MAX MRG",
            "MISC. DTG",
            "MISC. NDG",
            "MIX. FUEL",
            "MRG. PRICE",
            "NODU",
            "NP COST",
            "NUCLEAR",
            "OIL",
            "OP. COST",
            "OV. COST",
            "PSP",
            "ROW BAL.",
            "SOLAR",
            "SPIL. ENRG",
            "UNSP. ENRG",
            "WIND",
        ],
        "link": [
            "CONG. FEE (ABS.)",
            "CONG. FEE (ALG.)",
            "CONG. PROB +",
            "CONG. PROB -",
            "FLOW LIN.",
            "FLOW QUAD.",
            "HURDLE COST",
            "LOOP FLOW",
            "MARG. COST",
            "UCAP LIN.",
        ],
    }

    # No links (clean DB first)
    _clean_db()
    study_path = Path(study_service.get_study(UUID).path)
    links_folder = study_path / "output" / "20201014-1422eco-hello" / "economy" / "mc-ind" / "00001" / "links"
    shutil.rmtree(links_folder)
    variables = output_service.get_output_variables_information(UUID, "20201014-1422eco-hello")
    # When there's no links folder, asserts the endpoint doesn't fail and simply return an empty list
    assert variables.link == []

    # No areas (clean DB first)
    _clean_db()
    areas_mc_ind_folder = study_path / "output" / "20201014-1422eco-hello" / "economy" / "mc-ind" / "00001" / "areas"
    areas_mc_all_folder = study_path / "output" / "20201014-1422eco-hello" / "economy" / "mc-all" / "areas"
    shutil.rmtree(areas_mc_ind_folder)
    shutil.rmtree(areas_mc_all_folder)
    variables = output_service.get_output_variables_information(UUID, "20201014-1422eco-hello")
    # When there's no areas folder, asserts the endpoint doesn't fail and simply return an empty list
    assert variables.area == []

    # No mc-ind
    res = output_service.get_output_variables_information(UUID, "20201014-1427eco")
    assert res == OutputVariablesInformation(area=[], link=[])
