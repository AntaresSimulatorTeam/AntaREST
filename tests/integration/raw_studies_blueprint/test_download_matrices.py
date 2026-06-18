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

import datetime
import io
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from antares.study.version import StudyVersion
from pandas._testing import assert_frame_equal
from requests import Response
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.archives import archive_dir
from antarest.study.model import STUDY_VERSION_8_2, STUDY_VERSION_8_6, StorageMode
from tests.integration.utils import wait_task_completion
from tests.test_helpers.dates import utc_to_local


class Proxy:
    def __init__(self, client: TestClient, user_access_token: str):
        self.client = client
        self.user_access_token = user_access_token
        self.headers = {"Authorization": f"Bearer {user_access_token}"}


class PreparerProxy(Proxy):
    def create_minimal_study(self, target_version: StudyVersion, storage_mode: StorageMode) -> str:
        res = self.client.post(
            f"/v1/studies?name=NewStudy_{target_version}&storage_mode={storage_mode}&version={target_version}"
        )
        assert res.status_code == 201
        study_id = res.json()

        self.create_area(study_id, name="de", country="de")
        self.create_area(study_id, name="fr", country="fr")
        res = self.client.post(f"/v1/studies/{study_id}/links", json={"area1": "de", "area2": "fr"})
        res.raise_for_status()
        res = self.client.post(f"/v1/studies/{study_id}/areas/de/clusters/thermal", json={"name": "01_solar"})
        res.raise_for_status()

        return study_id

    def upload_matrix(self, study_id: str, matrix_path: str, df: pd.DataFrame) -> None:
        tsv = io.BytesIO()
        df.to_csv(tsv, sep="\t", index=False, header=False)
        tsv.seek(0)
        # noinspection SpellCheckingInspection
        res = self.client.put(f"/v1/studies/{study_id}/raw", params={"path": matrix_path}, files={"file": tsv})
        res.raise_for_status()

    def create_variant(self, parent_id: str, *, name: str) -> str:
        res = self.client.post(f"/v1/studies/{parent_id}/variants", params={"name": name})
        res.raise_for_status()
        variant_id = res.json()
        return variant_id

    def generate_snapshot(self, variant_id: str) -> None:
        # Generate a snapshot for the variant
        res = self.client.put(f"/v1/studies/{variant_id}/generate", params={"from_scratch": True})
        res.raise_for_status()
        task_id = res.json()
        assert task_id

        task = wait_task_completion(self.client, self.user_access_token, task_id, base_timeout=20)
        assert task.status == TaskStatus.COMPLETED

    def create_area(self, parent_id: str, *, name: str, country: str = "FR") -> str:
        res = self.client.post(
            f"/v1/studies/{parent_id}/areas", json={"name": name, "type": "AREA", "metadata": {"country": country}}
        )
        res.raise_for_status()
        area_id = res.json()["id"]
        return area_id

    def update_general_data(self, study_id: str, **data: Any) -> None:
        res = self.client.put(f"/v1/studies/{study_id}/config/general/form", json=data)
        res.raise_for_status()


class TestDownloadMatrices:
    """
    Checks the retrieval of matrices with the endpoint GET studies/uuid/raw/download
    """

    @pytest.mark.parametrize("storage_mode", [StorageMode.FILESYSTEM, StorageMode.DATABASE])
    def test_download_matrices(self, client: TestClient, user_access_token: str, storage_mode: StorageMode) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # =====================
        #  STUDIES PREPARATION
        # =====================

        preparer = PreparerProxy(client, user_access_token)

        study_820_id = preparer.create_minimal_study(target_version=STUDY_VERSION_8_2, storage_mode=storage_mode)

        # Create Variant
        variant_id = preparer.create_variant(study_820_id, name="New Variant")

        # Create a new area to implicitly create normalized matrices
        area_id = preparer.create_area(variant_id, name="Mayenne", country="France")

        # Change study start_date
        preparer.update_general_data(variant_id, firstMonth="July")

        # Really generates the snapshot
        preparer.generate_snapshot(variant_id)

        # Prepare a managed study to test specific matrices for version 8.6
        study_860_id = preparer.create_minimal_study(target_version=STUDY_VERSION_8_6, storage_mode=storage_mode)

        # Import a Min Gen. matrix: shape=(8760, 3), with random integers between 0 and 1000
        generator = np.random.default_rng(11)
        min_gen_df = pd.DataFrame(generator.integers(0, 10, size=(8760, 3)))
        preparer.upload_matrix(study_860_id, "input/hydro/series/de/mingen", min_gen_df)

        # =============================================
        #  TESTS NOMINAL CASE ON RAW AND VARIANT STUDY
        # =============================================

        raw_matrix_path = r"input/load/series/load_de"
        variant_matrix_path = f"input/load/series/load_{area_id}"

        raw_start_date = datetime.datetime(2018, 1, 1)
        variant_start_date = datetime.datetime(2028, 7, 1)

        for uuid, path, start_date in [
            (study_820_id, raw_matrix_path, raw_start_date),
            (variant_id, variant_matrix_path, variant_start_date),
        ]:
            # Export the matrix in CSV format (which is the default format)
            # and retrieve it as binary content (a ZIP-like file).
            res = client.get(f"/v1/studies/{uuid}/raw/download", params={"path": path})
            assert res.status_code == 200
            assert res.headers["content-type"] == "text/csv; charset=utf-8"

            # load into dataframe
            dataframe = pd.read_csv(io.BytesIO(res.content), index_col=0, header="infer", sep=",")

            # check time coherence
            actual_index = dataframe.index
            date_format = "%Y-%m-%d %H:%M:%S"
            first_date = datetime.datetime.strptime(str(actual_index[0]), date_format)
            second_date = datetime.datetime.strptime(str(actual_index[1]), date_format)
            first_month = 1 if uuid == study_820_id else 7  # July
            assert first_date.month == second_date.month == first_month
            assert first_date.day == second_date.day == 1
            assert first_date.hour == 0
            assert second_date.hour == 1

            # asserts that the result is the same as the one we get with the classic get /raw endpoint
            res = client.get(f"/v1/studies/{uuid}/raw", params={"path": path, "formatted": True})
            expected_matrix = res.json()
            expected_matrix["columns"] = [f"TS-{int(n) + 1}" for n in expected_matrix["columns"]]

            time_column = [
                (start_date + datetime.timedelta(hours=i)).strftime(date_format)
                for i in range(len(expected_matrix["data"]))
            ]

            expected_matrix["index"] = time_column
            expected = pd.DataFrame(**expected_matrix)
            assert_frame_equal(dataframe, expected, check_dtype=False)

        # =============================
        # TESTS INDEX AND HEADER PARAMETERS
        # =============================
        download_url = f"/v1/studies/{study_820_id}/raw/download"

        # test only few possibilities as each API call is quite long
        # (also check that the format is case-insensitive)
        for header in [True, False]:
            index = not header
            res = client.get(
                download_url,
                params={"path": raw_matrix_path, "format": "TSV", "header": header, "index": index},
            )
            assert res.status_code == 200
            assert res.headers["content-type"] == "text/tab-separated-values; charset=utf-8"

            content = io.BytesIO(res.content)
            dataframe = pd.read_csv(
                content, index_col=0 if index else None, header="infer" if header else None, sep="\t"
            )
            first_index = dataframe.index[0]
            assert first_index == "2018-01-01 00:00:00" if index else first_index == 0
            assert isinstance(dataframe.columns[0], str) if header else isinstance(dataframe.columns[0], np.int64)

        # =============================
        # TEST SPECIFIC MATRICES
        # =============================

        # tests links headers after v8.2
        res = client.get(download_url, params={"path": "input/links/de/fr_parameters", "format": "tsv"})
        assert res.status_code == 200
        content = io.BytesIO(res.content)
        dataframe = pd.read_csv(content, index_col=0, sep="\t")
        assert list(dataframe.columns) == [
            "Hurdle costs direct (de->fr_parameters)",
            "Hurdle costs indirect (fr_parameters->de)",
            "Impedances",
            "Loop flow",
            "P.Shift Min",
            "P.Shift Max",
        ]

        # modulation matrix
        res = client.get(
            download_url,
            params={"path": "input/thermal/prepro/de/01_solar/modulation", "format": "tsv"},
        )
        assert res.status_code == 200
        content = io.BytesIO(res.content)
        dataframe = pd.read_csv(content, index_col=0, sep="\t")
        assert dataframe.index[0] == "2018-01-01 00:00:00"
        dataframe.index = range(len(dataframe))
        transposed_matrix = list(zip(*[8760 * [1.0], 8760 * [1.0], 8760 * [1.0], 8760 * [0.0]]))
        expected_df = pd.DataFrame(
            columns=["Marginal cost modulation", "Market bid modulation", "Capacity modulation", "Min gen modulation"],
            index=range(8760),
            data=transposed_matrix,
        )
        assert dataframe.equals(expected_df)

        # test the Min Gen of the 8.6 study
        for export_format in ["tsv", "xlsx"]:
            res = client.get(
                f"/v1/studies/{study_860_id}/raw/download",
                params={"path": "input/hydro/series/de/mingen", "format": export_format},
            )
            assert res.status_code == 200
            content = io.BytesIO(res.content)
            if export_format == "tsv":
                dataframe = pd.read_csv(content, index_col=0, sep="\t")
            else:
                dataframe = pd.read_excel(content, index_col=0)
            assert dataframe.shape == (8760, 3)
            assert dataframe.columns.tolist() == ["TS-1", "TS-2", "TS-3"]
            assert str(dataframe.index[0]) == "2018-01-01 00:00:00"
            assert np.array_equal(dataframe.to_numpy(), min_gen_df.to_numpy())

        # =============================
        #  ERRORS
        # =============================

        fake_str = "fake_str"

        # fake study_id
        res = client.get(f"/v1/studies/{fake_str}/raw/download", params={"path": raw_matrix_path, "format": "tsv"})
        assert res.status_code == 422
        assert "should match pattern" in res.json()["description"]

        # fake path
        res = client.get(download_url, params={"path": f"input/links/de/{fake_str}", "format": "tsv"})
        assert res.status_code == 404
        assert res.json()["exception"] == "IncorrectPathError"

        # path that does not lead to a matrix
        res = client.get(download_url, params={"path": "settings/generaldata", "format": "tsv"})
        assert res.status_code == 404
        assert res.json()["exception"] == "IncorrectPathError"
        assert res.json()["description"] == "The provided path does not point to a valid matrix: 'settings/generaldata'"

        # wrong format
        res = client.get(download_url, params={"path": raw_matrix_path, "format": fake_str})
        assert res.status_code == 422
        assert res.json()["exception"] == "RequestValidationError"


def test_other_cases(client: TestClient, user_access_token: str, internal_study_id: str) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # tests links headers before v8.2
    res = client.get(
        f"/v1/studies/{internal_study_id}/raw/download",
        params={"path": "input/links/de/fr", "format": "tsv", "index": False},
    )
    assert res.status_code == 200
    content = io.BytesIO(res.content)
    dataframe = pd.read_csv(content, sep="\t")
    assert list(dataframe.columns) == [
        "Capacités de transmission directes",
        "Capacités de transmission indirectes",
        "Hurdle costs direct (de->fr)",
        "Hurdle costs indirect (fr->de)",
        "Impedances",
        "Loop flow",
        "P.Shift Min",
        "P.Shift Max",
    ]

    # checks default value for an empty water_values matrix
    res = client.get(
        f"/v1/studies/{internal_study_id}/raw/download",
        params={"path": "input/hydro/common/capacity/waterValues_de", "format": "tsv"},
    )
    assert res.status_code == 200
    content = io.BytesIO(res.content)
    dataframe = pd.read_csv(content, index_col=0, sep="\t")
    assert dataframe.to_numpy().tolist() == 365 * [101 * [0.0]]

    # checks default value for an empty energy matrix
    res = client.get(
        f"/v1/studies/{internal_study_id}/raw/download",
        params={"path": "input/hydro/prepro/de/energy", "format": "tsv"},
    )
    assert res.status_code == 200
    content = io.BytesIO(res.content)
    dataframe = pd.read_csv(content, index_col=0, sep="\t")
    assert dataframe.to_numpy().tolist() == 12 * [5 * [0.0]]


def test_download_output_matrices_for_both_storage_modes(
    client: TestClient, user_access_token: str, internal_study_id: str, tmp_path: Path
) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Create a study stored in Database mode
    res = client.post("/v1/studies?name=MyStudy&storage_mode=database")
    assert res.status_code == 201
    database_id = res.json()

    # Import the same output inside the DB study to perform the tests
    output_path = tmp_path / "ext_workspace" / "STA-mini" / "output" / "20201014-1422eco-hello"
    output_archive_path = tmp_path / "output_zipped.zip"
    archive_dir(output_path, output_archive_path)
    client.post(f"/v1/studies/{database_id}/output", files={"output": io.BytesIO(output_archive_path.read_bytes())})
    # Ensures the output has been successfully imported
    res = client.get(f"/v1/studies/{database_id}/outputs")
    assert len(res.json()) == 1

    # Use both the Database and the Filesystem studies to ensure we find the same results
    expected_date = utc_to_local("20201014-1222")
    output_id = f"{expected_date}eco-hello"
    for study_id in [database_id, internal_study_id]:
        print("STUDY ID", study_id)
        download_url = f"/v1/studies/{study_id}/raw/download"

        # `mc-ind` link matrix
        path = f"output/{output_id}/economy/mc-ind/00001/links/de/fr/values-hourly"
        res = client.get(download_url, params={"path": path, "format": "tsv"})
        dataframe = _parse_dataframe(res)
        assert list(dataframe.columns) == [
            "('FLOW LIN.', 'MWh', '')",
            "('UCAP LIN.', 'MWh', '')",
            "('LOOP FLOW', 'MWh', '')",
            "('FLOW QUAD.', 'MWh', '')",
            "('CONG. FEE (ALG.)', 'Euro', '')",
            "('CONG. FEE (ABS.)', 'Euro', '')",
            "('MARG. COST', 'Euro/MW', '')",
            "('CONG. PROB +', '%', '')",
            "('CONG. PROB -', '%', '')",
            "('HURDLE COST', 'Euro', '')",
        ]
        assert dataframe.shape == (168, 10)

        # `mc-ind` areas matrix
        path = f"output/{output_id}/economy/mc-ind/00001/areas/fr/details-hourly"
        res = client.get(download_url, params={"path": path, "format": "tsv"})
        dataframe = _parse_dataframe(res)
        assert dataframe.shape == (168, 27)
        assert list(dataframe["('01_solar', 'MWh', '')"]) == [100 * k for k in range(20)] + 148 * [2000]

        # `mc-all` areas matrix
        path = f"output/{output_id}/economy/mc-all/areas/de/id-monthly"
        res = client.get(download_url, params={"path": path, "format": "tsv"})
        dataframe = _parse_dataframe(res)
        assert dataframe.shape == (1, 58)
        assert list(dataframe.columns) == [
            "('OP. COST', 'Euro', 'min')",
            "('OP. COST', 'Euro', 'max')",
            "('MRG. PRICE', 'Euro', 'min')",
            "('MRG. PRICE', 'Euro', 'max')",
            "('BALANCE', 'MWh', 'min')",
            "('BALANCE', 'MWh', 'max')",
            "('LOAD', 'MWh', 'min')",
            "('LOAD', 'MWh', 'max')",
            "('H. ROR', 'MWh', 'min')",
            "('H. ROR', 'MWh', 'max')",
            "('WIND', 'MWh', 'min')",
            "('WIND', 'MWh', 'max')",
            "('SOLAR', 'MWh', 'min')",
            "('SOLAR', 'MWh', 'max')",
            "('NUCLEAR', 'MWh', 'min')",
            "('NUCLEAR', 'MWh', 'max')",
            "('LIGNITE', 'MWh', 'min')",
            "('LIGNITE', 'MWh', 'max')",
            "('COAL', 'MWh', 'min')",
            "('COAL', 'MWh', 'max')",
            "('GAS', 'MWh', 'min')",
            "('GAS', 'MWh', 'max')",
            "('OIL', 'MWh', 'min')",
            "('OIL', 'MWh', 'max')",
            "('MIX. FUEL', 'MWh', 'min')",
            "('MIX. FUEL', 'MWh', 'max')",
            "('MISC. DTG', 'MWh', 'min')",
            "('MISC. DTG', 'MWh', 'max')",
            "('H. STOR', 'MWh', 'min')",
            "('H. STOR', 'MWh', 'max')",
            "('H. PUMP', 'MWh', 'min')",
            "('H. PUMP', 'MWh', 'max')",
            "('H. LEV', '%', 'min')",
            "('H. LEV', '%', 'max')",
            "('H. INFL', 'MWh', 'min')",
            "('H. INFL', 'MWh', 'max')",
            "('H. OVFL', '%', 'min')",
            "('H. OVFL', '%', 'max')",
            "('H. VAL', 'Euro/MWh', 'min')",
            "('H. VAL', 'Euro/MWh', 'max')",
            "('H. COST', 'Euro', 'min')",
            "('H. COST', 'Euro', 'max')",
            "('UNSP. ENRG', 'MWh', 'min')",
            "('UNSP. ENRG', 'MWh', 'max')",
            "('SPIL. ENRG', 'MWh', 'min')",
            "('SPIL. ENRG', 'MWh', 'max')",
            "('LOLD', 'Hours', 'min')",
            "('LOLD', 'Hours', 'max')",
            "('AVL DTG', 'MWh', 'min')",
            "('AVL DTG', 'MWh', 'max')",
            "('DTG MRG', 'MWh', 'min')",
            "('DTG MRG', 'MWh', 'max')",
            "('MAX MRG', 'MWh', 'min')",
            "('MAX MRG', 'MWh', 'max')",
            "('NP COST', 'Euro', 'min')",
            "('NP COST', 'Euro', 'max')",
            "('NODU', ' ', 'min')",
            "('NODU', ' ', 'max')",
        ]


def _parse_dataframe(res: Response) -> pd.DataFrame:
    print(res.content)
    assert res.status_code == 200
    content = io.BytesIO(res.content)
    return pd.read_csv(content, index_col=0, sep="\t")
