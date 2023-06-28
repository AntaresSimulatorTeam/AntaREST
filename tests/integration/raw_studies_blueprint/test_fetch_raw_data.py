import http
import json
import pathlib
import shutil
from urllib.parse import urlencode

import pytest
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import RawStudy, Study
from starlette.testclient import TestClient
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
        study_id: str,
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
            study: RawStudy = db.session.get(Study, study_id)
            study_dir = pathlib.Path(study.path)

        shutil.copytree(
            ASSETS_DIR.joinpath("user"),
            study_dir.joinpath("user"),
            dirs_exist_ok=True,
        )

        # Then, use the API to download the files from the "user/folder" directory
        user_folder_dir = study_dir.joinpath("user/folder")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir).as_posix()
            query_string = urlencode({"path": f"/{rel_path}", "depth": 1})
            res = client.get(
                f"/v1/studies/{study_id}/raw?{query_string}",
                headers={"Authorization": f"Bearer {user_access_token}"},
            )
            res.raise_for_status()
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
            query_string = urlencode(
                {"path": f"/{rel_path.as_posix()}", "depth": 1}
            )
            res = client.get(
                f"/v1/studies/{study_id}/raw?{query_string}",
                headers={"Authorization": f"Bearer {user_access_token}"},
            )
            res.raise_for_status()
            actual = res.content
            expected = file_path.read_bytes()
            assert actual == expected

        # Some files can be corrupted
        user_folder_dir = study_dir.joinpath("user/bad")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir)
            query_string = urlencode(
                {"path": f"/{rel_path.as_posix()}", "depth": 1}
            )
            res = client.get(
                f"/v1/studies/{study_id}/raw?{query_string}",
                headers={"Authorization": f"Bearer {user_access_token}"},
            )
            assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY

        # We can access to the configuration the classic way,
        # for instance, we can get the list of areas:
        query_string = urlencode({"path": "/input/areas/list", "depth": 1})
        res = client.get(
            f"/v1/studies/{study_id}/raw?{query_string}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        assert res.json() == ["DE", "ES", "FR", "IT"]
