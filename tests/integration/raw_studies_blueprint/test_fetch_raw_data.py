import http
import io
import itertools
import json
import pathlib
import shutil
from unittest.mock import ANY

import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
import pytest
from starlette.testclient import TestClient

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import RawStudy, Study
from tests.integration.raw_studies_blueprint.assets import ASSETS_DIR


@pytest.mark.integration_test
class TestFetchRawData:
    """
    Check the retrieval of Raw Data from Study: JSON, Text, or File Attachment.
    """

    def test_get_study(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """
        Test the `get_study` endpoint for fetching raw data from a study.

        This test retrieves raw data from a study identified by a UUID and checks
        if the returned data matches the expected data.

        The test performs the following steps:
        1. Copies the user resources in the Study directory.
        2. Uses the API to download files from the "user/folder" directory.
        3. Compares the fetched data with the expected data from disk.
        4. Uses the API to download files from the "user/unknown" directory.
        5. Checks for a 415 error when the extension of a file is unknown.
        """
        # First copy the user resources in the Study directory
        with db():
            study: RawStudy = db.session.get(Study, internal_study_id)
            study_dir = pathlib.Path(study.path)
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        shutil.copytree(
            ASSETS_DIR.joinpath("user"),
            study_dir.joinpath("user"),
            dirs_exist_ok=True,
        )

        # Then, use the API to download the files from the "user/folder" directory
        user_folder_dir = study_dir.joinpath("user/folder")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir).as_posix()
            res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": rel_path, "depth": 1})
            assert res.status_code == 200, res.json()
            if file_path.suffix == ".json":
                # special case for JSON files
                actual = res.json()
                expected = json.loads(file_path.read_text(encoding="utf-8"))
            else:
                # NOTE ABOUT TEXT FILES {".txt", ".csv", ".tsv"}:
                # We need to read the file in binary mode to compare bytes,
                # because when reading in text mode, the universal newline
                # rule applies and so there are potentially differences between
                # Windows and Posix newlines. See the doc of the `open()` function.
                # The text files used in the unit tests resources may use CR+LF or LF
                # newlines on Windows, depending on the Git configuration `core.autocrlf`.
                actual = res.content
                expected = file_path.read_bytes()
            assert actual == expected

        # If the extension is unknown, we should have a "binary" content
        user_folder_dir = study_dir.joinpath("user/unknown")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir)
            res = client.get(
                f"/v1/studies/{internal_study_id}/raw", params={"path": f"/{rel_path.as_posix()}", "depth": 1}
            )
            assert res.status_code == 200, res.json()
            actual = res.content
            expected = file_path.read_bytes()
            assert actual == expected

        # If you try to retrieve a file that doesn't exist, we should have a 404 error
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": "user/somewhere/something.txt"})
        assert res.status_code == 404, res.json()
        assert res.json() == {
            "description": "'somewhere' not a child of User",
            "exception": "ChildNotFoundError",
        }

        # If you want to update an existing resource, you can use PUT method.
        # But, if the resource doesn't exist, you should have a 404 Not Found error.
        res = client.put(
            f"/v1/studies/{internal_study_id}/raw",
            params={"path": "user/somewhere/something.txt"},
            files={"file": io.BytesIO(b"Goodbye World!")},
        )
        assert res.status_code == 404, res.json()
        assert res.json() == {
            "description": "'somewhere' not a child of User",
            "exception": "ChildNotFoundError",
        }

        # To create a resource, you can use PUT method and the `create_missing` flag.
        # The expected status code should be 204 No Content.
        res = client.put(
            f"/v1/studies/{internal_study_id}/raw",
            params={"path": "user/somewhere/something.txt", "create_missing": True},
            files={"file": io.BytesIO(b"Goodbye Cruel World!")},
        )
        assert res.status_code == 204, res.json()

        # To update a resource, you can use PUT method, with or without the `create_missing` flag.
        # The expected status code should be 204 No Content.
        res = client.put(
            f"/v1/studies/{internal_study_id}/raw",
            params={"path": "user/somewhere/something.txt", "create_missing": True},
            files={"file": io.BytesIO(b"This is the end!")},
        )
        assert res.status_code == 204, res.json()

        # You can check that the resource has been created or updated.
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": "user/somewhere/something.txt"})
        assert res.status_code == 200, res.json()
        assert res.content == b"This is the end!"

        # If we ask for properties, we should have a JSON content
        rel_path = "/input/links/de/properties/fr"
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": rel_path, "depth": 2})
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert actual == {
            "asset-type": "ac",
            "colorb": 112,
            "colorg": 112,
            "colorr": 112,
            "display-comments": True,
            "filter-synthesis": "",
            "filter-year-by-year": "hourly",
            "hurdles-cost": True,
            "link-style": "plain",
            "link-width": 1,
            "loop-flow": False,
            "transmission-capacities": "enabled",
            "use-phase-shifter": False,
        }

        # If we ask for a matrix, we should have a JSON content if formatted is True
        rel_path = "/input/links/de/fr"
        expected_row = [100000, 100000, 0.01, 0.01, 0, 0, 0, 0]
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": rel_path, "formatted": True})
        assert res.status_code == 200, res.json()
        old_result = res.json()
        assert old_result == {"index": ANY, "columns": ANY, "data": ANY}
        assert old_result["data"][0] == expected_row

        # We should have the same result with new flag 'format' set to 'JSON'
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": rel_path, "format": "json"})
        assert res.status_code == 200, res.json()
        new_result = res.json()
        assert new_result == old_result

        # If we ask for a matrix, we should have a CSV content if formatted is False
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": rel_path, "formatted": False})
        assert res.status_code == 200, res.json()
        old_result = res.text
        actual_lines = old_result.splitlines()
        first_row = [float(x) for x in actual_lines[0].split("\t")]
        assert first_row == expected_row

        # We should have the same result with new flag 'format' set to 'bytes'
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": rel_path, "format": "bytes"})
        assert res.status_code == 200, res.json()
        new_result = res.text
        assert new_result == old_result

        # If we ask for a matrix, we should have arrow binary if format = "arrow"
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": rel_path, "format": "arrow"})
        assert res.status_code == 200
        assert isinstance(res.content, bytes)
        assert res.text.startswith("ARROW")
        arrow_bytes = res.content
        buffer = pa.BufferReader(arrow_bytes)
        table = feather.read_table(buffer)
        df = table.to_pandas()
        assert list(df.loc[0]) == expected_row

        # Asserts output matrix (containing index and columns) can be retrieved with arrow
        output_path = "/output/20201014-1422eco-hello/economy/mc-all/areas/de/id-daily"
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": output_path, "format": "arrow"})
        assert res.status_code == 200
        assert isinstance(res.content, bytes)
        assert res.text.startswith("ARROW")
        buffer = pa.BufferReader(res.content)
        table = feather.read_table(buffer)
        df = table.to_pandas()
        assert df.columns[0] == "Index"  # asserts the first columns corresponds to the index in such a case.

        # Try to replace a matrix with a one in arrow format
        res = client.put(f"/v1/studies/{internal_study_id}/raw", params={"path": rel_path}, files={"file": arrow_bytes})
        assert res.status_code in {201, 204}

        # If ask for an empty matrix, we should have an empty binary content
        res = client.get(
            f"/v1/studies/{internal_study_id}/raw",
            params={"path": "input/thermal/prepro/de/01_solar/data", "formatted": False},
        )
        assert res.status_code == 200, res.json()
        assert res.content == b""

        # But, if we use formatted = True, we should have a JSON objet representing and empty matrix
        res = client.get(
            f"/v1/studies/{internal_study_id}/raw",
            params={"path": "input/thermal/prepro/de/01_solar/data", "formatted": True},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == {"index": [0], "columns": [], "data": []}

        # Some files can be corrupted
        user_folder_dir = study_dir.joinpath("user/bad")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir)
            res = client.get(
                f"/v1/studies/{internal_study_id}/raw", params={"path": f"/{rel_path.as_posix()}", "depth": 1}
            )
            assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY

        # We can access to the configuration the classic way,
        # for instance, we can get the list of areas:
        res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": "/input/areas/list", "depth": 1})
        assert res.status_code == 200, res.json()
        assert res.json() == ["DE", "ES", "FR", "IT"]

        # asserts that the GET /raw endpoint is able to read matrix containing NaN values
        res = client.get(
            f"/v1/studies/{internal_study_id}/raw",
            params={"path": "output/20201014-1427eco/economy/mc-all/areas/de/id-monthly"},
        )
        assert res.status_code == 200
        assert np.isnan(res.json()["data"][0]).any()

        # Iterate over all possible combinations of path and depth
        for path, depth in itertools.product([None, "", "/"], [0, 1, 2]):
            res = client.get(f"/v1/studies/{internal_study_id}/raw", params={"path": path, "depth": depth})
            assert res.status_code == 200, f"Error for path={path} and depth={depth}"
