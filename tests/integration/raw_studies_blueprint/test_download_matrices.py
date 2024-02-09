import io

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


@pytest.mark.integration_test
class TestDownloadMatrices:
    """
    Checks the retrieval of matrices with the endpoint GET studies/uuid/raw/download
    """

    def test_download_matrices(self, client: TestClient, user_access_token: str, study_id: str) -> None:
        user_headers = {"Authorization": f"Bearer {user_access_token}"}

        # =============================
        #  STUDIES PREPARATION
        # =============================

        # Manage parent study and upgrades it to v8.2
        # This is done to test matrix headers according to different versions
        copied = client.post(
            f"/v1/studies/{study_id}/copy", params={"dest": "copied", "use_task": False}, headers=user_headers
        )
        parent_id = copied.json()
        res = client.put(f"/v1/studies/{parent_id}/upgrade", params={"target_version": 820}, headers=user_headers)
        assert res.status_code == 200
        task_id = res.json()
        assert task_id
        task = wait_task_completion(client, user_access_token, task_id, timeout=20)
        assert task.status == TaskStatus.COMPLETED

        # Create Variant
        res = client.post(
            f"/v1/studies/{parent_id}/variants",
            headers=user_headers,
            params={"name": "variant_1"},
        )
        assert res.status_code == 200
        variant_id = res.json()

        # Create a new area to implicitly create normalized matrices
        area_name = "new_area"
        res = client.post(
            f"/v1/studies/{variant_id}/areas",
            headers=user_headers,
            json={"name": area_name, "type": "AREA", "metadata": {"country": "FR"}},
        )
        assert res.status_code in {200, 201}

        # Change study start_date
        res = client.put(
            f"/v1/studies/{variant_id}/config/general/form",
            json={"firstMonth": "July"},
            headers=user_headers,
        )
        assert res.status_code == 200

        # Really generates the snapshot
        client.get(f"/v1/studies/{variant_id}/areas", headers=user_headers)
        assert res.status_code == 200

        # =============================
        #  TESTS NOMINAL CASE ON RAW AND VARIANT STUDY
        # =============================

        raw_matrix_path = r"input/load/series/load_de"
        variant_matrix_path = f"input/load/series/load_{area_name}"

        for uuid, path in [(parent_id, raw_matrix_path), (variant_id, variant_matrix_path)]:
            # Export the matrix in xlsx format (which is the default format)
            # and retrieve it as binary content (a ZIP-like file).
            res = client.get(
                f"/v1/studies/{uuid}/raw/download",
                params={"path": path},
                headers=user_headers,
            )
            assert res.status_code == 200
            # noinspection SpellCheckingInspection
            assert res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            # load into dataframe
            # noinspection PyTypeChecker
            dataframe = pd.read_excel(io.BytesIO(res.content), index_col=0)

            # check time coherence
            generated_index = dataframe.index
            # noinspection PyUnresolvedReferences
            first_date = generated_index[0].to_pydatetime()
            # noinspection PyUnresolvedReferences
            second_date = generated_index[1].to_pydatetime()
            assert first_date.month == second_date.month == 1 if uuid == parent_id else 7
            assert first_date.day == second_date.day == 1
            assert first_date.hour == 0
            assert second_date.hour == 1

            # reformat into a json to help comparison
            new_cols = [int(col) for col in dataframe.columns]
            dataframe.columns = new_cols
            dataframe.index = range(len(dataframe))
            actual_matrix = dataframe.to_dict(orient="split")

            # asserts that the result is the same as the one we get with the classic get /raw endpoint
            res = client.get(f"/v1/studies/{uuid}/raw", params={"path": path, "formatted": True}, headers=user_headers)
            expected_matrix = res.json()
            assert actual_matrix == expected_matrix

        # =============================
        # TESTS INDEX AND HEADER PARAMETERS
        # =============================

        # test only few possibilities as each API call is quite long
        # (also check that the format is case-insensitive)
        for header in [True, False]:
            index = not header
            res = client.get(
                f"/v1/studies/{parent_id}/raw/download",
                params={"path": raw_matrix_path, "format": "TSV", "header": header, "index": index},
                headers=user_headers,
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
            f"/v1/studies/{study_id}/raw/download",
            params={"path": "input/links/de/fr", "format": "tsv", "index": False},
            headers=user_headers,
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
            f"/v1/studies/{parent_id}/raw/download",
            params={"path": "input/links/de/fr_parameters", "format": "tsv"},
            headers=user_headers,
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
            res = client.get(
                f"/v1/studies/{parent_id}/raw/download", params={"path": path, "format": "tsv"}, headers=user_headers
            )
            assert res.status_code == 200
            content = io.BytesIO(res.content)
            dataframe = pd.read_csv(content, index_col=0, sep="\t")
            assert list(dataframe.index) == list(dataframe.columns) == ["de", "es", "fr", "it"]
            assert all(dataframe.iloc[i, i] == 1.0 for i in range(len(dataframe)))

        # test for empty matrix
        res = client.get(
            f"/v1/studies/{study_id}/raw/download",
            params={"path": "input/hydro/common/capacity/waterValues_de", "format": "tsv"},
            headers=user_headers,
        )
        assert res.status_code == 200
        content = io.BytesIO(res.content)
        dataframe = pd.read_csv(content, index_col=0, sep="\t")
        assert dataframe.empty

        # modulation matrix
        res = client.get(
            f"/v1/studies/{parent_id}/raw/download",
            params={"path": "input/thermal/prepro/de/01_solar/modulation", "format": "tsv"},
            headers=user_headers,
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
            f"/v1/studies/{study_id}/raw/download",
            params={
                "path": "output/20201014-1422eco-hello/economy/mc-ind/00001/links/de/fr/values-hourly",
                "format": "tsv",
            },
            headers=user_headers,
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

        # test energy matrix to test the regex
        res = client.get(
            f"/v1/studies/{study_id}/raw/download",
            params={"path": "input/hydro/prepro/de/energy", "format": "tsv"},
            headers=user_headers,
        )
        assert res.status_code == 200
        content = io.BytesIO(res.content)
        dataframe = pd.read_csv(content, index_col=0, sep="\t")
        assert dataframe.empty

        # =============================
        #  ERRORS
        # =============================

        fake_str = "fake_str"

        # fake study_id
        res = client.get(
            f"/v1/studies/{fake_str}/raw/download",
            params={"path": raw_matrix_path, "format": "tsv"},
            headers=user_headers,
        )
        assert res.status_code == 404
        assert res.json()["exception"] == "StudyNotFoundError"

        # fake path
        res = client.get(
            f"/v1/studies/{parent_id}/raw/download",
            params={"path": f"input/links/de/{fake_str}", "format": "tsv"},
            headers=user_headers,
        )
        assert res.status_code == 404
        assert res.json()["exception"] == "ChildNotFoundError"

        # path that does not lead to a matrix
        res = client.get(
            f"/v1/studies/{parent_id}/raw/download",
            params={"path": "settings/generaldata", "format": "tsv"},
            headers=user_headers,
        )
        assert res.status_code == 404
        assert res.json()["exception"] == "IncorrectPathError"
        assert res.json()["description"] == "The provided path does not point to a valid matrix: 'settings/generaldata'"

        # wrong format
        res = client.get(
            f"/v1/studies/{parent_id}/raw/download",
            params={"path": raw_matrix_path, "format": fake_str},
            headers=user_headers,
        )
        assert res.status_code == 422
        assert res.json()["exception"] == "RequestValidationError"
