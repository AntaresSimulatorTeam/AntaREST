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

import datetime
import io
import typing as t

import numpy as np
import pandas as pd
import pytest
from pandas._testing import assert_frame_equal
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


class Proxy:
    def __init__(self, client: TestClient, user_access_token: str):
        self.client = client
        self.user_access_token = user_access_token
        self.headers = {"Authorization": f"Bearer {user_access_token}"}


class PreparerProxy(Proxy):
    def copy_upgrade_study(self, ref_study_id, target_version=820):
        """
        Copy a study in the managed workspace and upgrade it to a specific version
        """
        # Prepare a managed study to test specific matrices for version 8.2
        res = self.client.post(
            f"/v1/studies/{ref_study_id}/copy",
            params={"study_name": "copied-820", "use_task": False},
            headers=self.headers,
        )
        res.raise_for_status()
        study_820_id = res.json()

        res = self.client.put(
            f"/v1/studies/{study_820_id}/upgrade",
            params={"target_version": target_version},
            headers=self.headers,
        )
        res.raise_for_status()
        task_id = res.json()
        assert task_id

        task = wait_task_completion(self.client, self.user_access_token, task_id, base_timeout=20)
        assert task.status == TaskStatus.COMPLETED
        return study_820_id

    def upload_matrix(self, internal_study_id: str, matrix_path: str, df: pd.DataFrame) -> None:
        tsv = io.BytesIO()
        df.to_csv(tsv, sep="\t", index=False, header=False)
        tsv.seek(0)
        # noinspection SpellCheckingInspection
        res = self.client.put(
            f"/v1/studies/{internal_study_id}/raw",
            params={"path": matrix_path},
            headers=self.headers,
            files={"file": tsv},
        )
        res.raise_for_status()

    def create_variant(self, parent_id: str, *, name: str) -> str:
        res = self.client.post(
            f"/v1/studies/{parent_id}/variants",
            headers=self.headers,
            params={"name": name},
        )
        res.raise_for_status()
        variant_id = res.json()
        return variant_id

    def generate_snapshot(self, variant_id: str, denormalize=False, from_scratch=True) -> None:
        # Generate a snapshot for the variant
        res = self.client.put(
            f"/v1/studies/{variant_id}/generate",
            headers=self.headers,
            params={"denormalize": denormalize, "from_scratch": from_scratch},
        )
        res.raise_for_status()
        task_id = res.json()
        assert task_id

        task = wait_task_completion(self.client, self.user_access_token, task_id, base_timeout=20)
        assert task.status == TaskStatus.COMPLETED

    def create_area(self, parent_id, *, name: str, country: str = "FR") -> str:
        res = self.client.post(
            f"/v1/studies/{parent_id}/areas",
            headers=self.headers,
            json={"name": name, "type": "AREA", "metadata": {"country": country}},
        )
        res.raise_for_status()
        area_id = res.json()["id"]
        return area_id

    def update_general_data(self, internal_study_id: str, **data: t.Any):
        res = self.client.put(
            f"/v1/studies/{internal_study_id}/config/general/form",
            json=data,
            headers=self.headers,
        )
        res.raise_for_status()


@pytest.mark.integration_test
class TestDownloadMatrices:
    """
    Checks the retrieval of matrices with the endpoint GET studies/uuid/raw/download
    """

    def test_download_matrices(self, client: TestClient, user_access_token: str, internal_study_id: str) -> None:
        user_headers = {"Authorization": f"Bearer {user_access_token}"}
        client.headers = user_headers

        # =====================
        #  STUDIES PREPARATION
        # =====================

        preparer = PreparerProxy(client, user_access_token)

        study_820_id = preparer.copy_upgrade_study(internal_study_id, target_version=820)

        # Create Variant
        variant_id = preparer.create_variant(study_820_id, name="New Variant")

        # Create a new area to implicitly create normalized matrices
        area_id = preparer.create_area(variant_id, name="Mayenne", country="France")

        # Change study start_date
        preparer.update_general_data(variant_id, firstMonth="July")

        # Really generates the snapshot
        preparer.generate_snapshot(variant_id)

        # Prepare a managed study to test specific matrices for version 8.6
        study_860_id = preparer.copy_upgrade_study(internal_study_id, target_version=860)

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
            expected_matrix["columns"] = [f"TS-{n + 1}" for n in expected_matrix["columns"]]

            time_column = [
                (start_date + datetime.timedelta(hours=i)).strftime(date_format)
                for i in range(len(expected_matrix["data"]))
            ]

            expected_matrix["index"] = time_column
            expected = pd.DataFrame(**expected_matrix)
            assert_frame_equal(dataframe, expected)

        # =============================
        # TESTS INDEX AND HEADER PARAMETERS
        # =============================

        # test only few possibilities as each API call is quite long
        # (also check that the format is case-insensitive)
        for header in [True, False]:
            index = not header
            res = client.get(
                f"/v1/studies/{study_820_id}/raw/download",
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

        # tests links headers after v8.2
        res = client.get(
            f"/v1/studies/{study_820_id}/raw/download", params={"path": "input/links/de/fr_parameters", "format": "tsv"}
        )
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

        # allocation and correlation matrices
        for path in ["input/hydro/allocation", "input/hydro/correlation"]:
            res = client.get(f"/v1/studies/{study_820_id}/raw/download", params={"path": path, "format": "tsv"})
            assert res.status_code == 200
            content = io.BytesIO(res.content)
            dataframe = pd.read_csv(content, index_col=0, sep="\t")
            assert list(dataframe.index) == list(dataframe.columns) == ["de", "es", "fr", "it"]
            assert all(np.isclose(dataframe.iloc[i, i], 1.0) for i in range(len(dataframe)))

        # checks default value for an empty water_values matrix
        res = client.get(
            f"/v1/studies/{internal_study_id}/raw/download",
            params={"path": "input/hydro/common/capacity/waterValues_de", "format": "tsv"},
        )
        assert res.status_code == 200
        content = io.BytesIO(res.content)
        dataframe = pd.read_csv(content, index_col=0, sep="\t")
        assert dataframe.to_numpy().tolist() == 365 * [101 * [0.0]]

        # modulation matrix
        res = client.get(
            f"/v1/studies/{study_820_id}/raw/download",
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

        # asserts endpoint returns the right columns for output matrix
        res = client.get(
            f"/v1/studies/{internal_study_id}/raw/download",
            params={
                "path": "output/20201014-1422eco-hello/economy/mc-ind/00001/links/de/fr/values-hourly",
                "format": "tsv",
            },
        )
        assert res.status_code == 200
        content = io.BytesIO(res.content)
        dataframe = pd.read_csv(content, index_col=0, sep="\t")
        # noinspection SpellCheckingInspection
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

        # checks default value for an empty energy matrix
        res = client.get(
            f"/v1/studies/{internal_study_id}/raw/download",
            params={"path": "input/hydro/prepro/de/energy", "format": "tsv"},
        )
        assert res.status_code == 200
        content = io.BytesIO(res.content)
        dataframe = pd.read_csv(content, index_col=0, sep="\t")
        assert dataframe.to_numpy().tolist() == 12 * [5 * [0.0]]

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
                dataframe = pd.read_excel(content, index_col=0)  # type: ignore
            assert dataframe.shape == (8760, 3)
            assert dataframe.columns.tolist() == ["TS-1", "TS-2", "TS-3"]
            assert str(dataframe.index[0]) == "2018-01-01 00:00:00"
            assert np.array_equal(dataframe.to_numpy(), min_gen_df.to_numpy())

        # test that downloading the digest file doesn't fail
        digest_path = "output/20201014-1422eco-hello/economy/mc-all/grid/digest"
        res = client.get(f"/v1/studies/{internal_study_id}/raw/download", params={"path": digest_path, "format": "tsv"})
        assert res.status_code == 200

        # =============================
        #  ERRORS
        # =============================

        fake_str = "fake_str"

        # fake study_id
        res = client.get(f"/v1/studies/{fake_str}/raw/download", params={"path": raw_matrix_path, "format": "tsv"})
        assert res.status_code == 400
        assert "is not a valid UUID" in res.json()["description"]

        # fake path
        res = client.get(
            f"/v1/studies/{study_820_id}/raw/download", params={"path": f"input/links/de/{fake_str}", "format": "tsv"}
        )
        assert res.status_code == 404
        assert res.json()["exception"] == "ChildNotFoundError"

        # path that does not lead to a matrix
        res = client.get(
            f"/v1/studies/{study_820_id}/raw/download", params={"path": "settings/generaldata", "format": "tsv"}
        )
        assert res.status_code == 404
        assert res.json()["exception"] == "IncorrectPathError"
        assert res.json()["description"] == "The provided path does not point to a valid matrix: 'settings/generaldata'"

        # wrong format
        res = client.get(
            f"/v1/studies/{study_820_id}/raw/download", params={"path": raw_matrix_path, "format": fake_str}
        )
        assert res.status_code == 422
        assert res.json()["exception"] == "RequestValidationError"
