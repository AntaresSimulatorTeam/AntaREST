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

import http
import io
import itertools
import json
import pathlib
import shutil
from unittest.mock import ANY

import numpy as np
import pandas as pd
import pytest
from httpx import Response
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.prepro.area.thermal.thermal import (
    default_data_matrix,
)
from tests.integration.raw_studies_blueprint.assets import ASSETS_DIR
from tests.integration.utils import wait_for


def _check_endpoint_response(
    study_type: str, res: Response, client: TestClient, study_id: str, expected_msg: str, exception: str
):
    # The command will only fail when applied so on raw studies only.
    # So we have to differentiate the test based on the study type.
    if study_type == "raw":
        assert res.status_code == 403
        assert res.json()["exception"] == exception
        assert expected_msg in res.json()["description"]
    else:
        res.raise_for_status()
        task_id = client.put(f"/v1/studies/{study_id}/generate").json()
        res = client.get(f"/v1/tasks/{task_id}?wait_for_completion=True")
        task = res.json()
        assert task["status"] == TaskStatus.FAILED.value
        assert not task["result"]["success"]
        assert expected_msg in task["result"]["message"]
        # Check the message users will see inside the front-end (GET /comments endpoint will fail)
        res = client.get(f"/v1/studies/{study_id}/comments")
        assert res.status_code == 417
        response = res.json()
        assert response["exception"] == "VariantGenerationError"
        assert response["description"] == f"Error while generating variant {study_id} : {expected_msg}"
        # We have to delete the command to make the variant "clean" again.
        res = client.get(f"/v1/studies/{study_id}/commands")
        cmd_id = res.json()[-1]["id"]
        res = client.delete(f"/v1/studies/{study_id}/commands/{cmd_id}")
        res.raise_for_status()


@pytest.mark.integration_test
class TestFetchRawData:
    """
    Check the retrieval of Raw Data from Study: JSON, Text, or File Attachment.
    """

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_get_study_data(self, client: TestClient, user_access_token: str, internal_study_id: str, study_type: str):
        """
        Test the `get_study_data` endpoint for fetching raw data from a study.

        This test retrieves raw data from a study identified by a UUID and checks
        if the returned data matches the expected data.

        The test performs the following steps:
        1. Copies the user resources in the Study directory.
        2. Uses the API to download files from the "user/folder" directory.
        3. Compares the fetched data with the expected data from disk.
        4. Uses the API to download files from the "user/unknown" directory.
        5. Checks for a 415 error when the extension of a file is unknown.
        """

        if pytest.FAST_MODE:
            pytest.skip("Skipping test")

        # =============================
        #  SET UP
        # =============================

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

        if study_type == "variant":
            # Copies the study, to convert it into a managed one.
            res = client.post(
                f"/v1/studies/{internal_study_id}/copy",
                headers={"Authorization": f"Bearer {user_access_token}"},
                params={"study_name": "default", "with_outputs": False, "use_task": False},
            )
            assert res.status_code == 201
            parent_id = res.json()
            res = client.post(f"/v1/studies/{parent_id}/variants", params={"name": "variant 1"})
            internal_study_id = res.json()

        raw_url = f"/v1/studies/{internal_study_id}/raw"

        # =============================
        #  NOMINAL CASES
        # =============================

        # Then, use the API to download the files from the "user/folder" directory
        user_folder_dir = study_dir.joinpath("user/folder")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir).as_posix()
            res = client.get(raw_url, params={"path": rel_path, "depth": 1})
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
            res = client.get(raw_url, params={"path": f"/{rel_path.as_posix()}", "depth": 1})
            assert res.status_code == 200, res.json()
            actual = res.content
            expected = file_path.read_bytes()
            assert actual == expected

        # If you try to retrieve a file that doesn't exist, we should have a 404 error
        res = client.get(raw_url, params={"path": "user/somewhere/something.txt"})
        assert res.status_code == 404, res.json()
        assert res.json() == {
            "description": "'somewhere' not a child of User",
            "exception": "ChildNotFoundError",
        }

        # If you want to update an existing resource, you can use PUT method.
        # But, if the resource doesn't exist, you should have a 404 Not Found error.
        res = client.put(
            raw_url, params={"path": "user/somewhere/something.txt"}, files={"file": io.BytesIO(b"Goodbye World!")}
        )
        assert res.status_code == 404, res.json()
        assert res.json() == {
            "description": "'somewhere' not a child of User",
            "exception": "ChildNotFoundError",
        }

        # To create a resource, you can use PUT method and the `create_missing` flag.
        # The expected status code should be 204 No Content.
        file_to_create = "user/somewhere/something.txt"
        res = client.put(
            raw_url,
            params={"path": file_to_create, "create_missing": True},
            files={"file": io.BytesIO(b"Goodbye Cruel World!")},
        )
        assert res.status_code == 204, res.json()
        if study_type == "variant":
            # Asserts the generation succeeds
            task_id = client.put(f"/v1/studies/{internal_study_id}/generate?from_scratch=True").json()
            res = client.get(f"/v1/tasks/{task_id}?wait_for_completion=True")
            task = res.json()
            assert task["status"] == TaskStatus.COMPLETED.value
            assert task["result"]["success"]
            # Checks created commands
            res = client.get(f"/v1/studies/{internal_study_id}/commands")
            commands = res.json()
            # First command is created automatically to respect owners, we ignore it.
            assert commands[1]["action"] == "create_user_resource"
            assert commands[1]["args"] == [{"data": {"path": "somewhere/something.txt", "resource_type": "file"}}]
            assert commands[2]["action"] == "update_file"
            assert commands[2]["args"] == [{"target": file_to_create, "b64Data": "R29vZGJ5ZSBDcnVlbCBXb3JsZCE="}]

        # To update a resource, you can use PUT method, with or without the `create_missing` flag.
        # The expected status code should be 204 No Content.
        res = client.put(
            raw_url,
            params={"path": file_to_create, "create_missing": True},
            files={"file": io.BytesIO(b"This is the end!")},
        )
        assert res.status_code == 204, res.json()

        # You can check that the resource has been created or updated.
        res = client.get(raw_url, params={"path": file_to_create})
        assert res.status_code == 200, res.json()
        assert res.content == b"This is the end!"

        # You can import a csv or a tsv file inside a matrix
        matrix_path = "input/load/series/load_de"
        for content, delimiter in zip(
            [
                b"1.20000\n3.400000\n",
                b"1.4\t0.5\n0.0\t0.4\n",
                b"1.2,1.3\n1.4,1.5\n",
                b"",
                b"\xef\xbb\xbf1;1;1;1;1\r\n1;1;1;1;1",
                b"1;1;1;1;1\r1;1;1;1;1",
                b"0,000000;0,000000;0,000000;0,000000\n0,000000;0,000000;0,000000;0,000000",
                b"1;2;3;;;\n4;5;6;;;\n",
                b"1;1;1;1\r\n1;1;1;1\r\n1;1;1;1\r\n1;1;1;1\r\n1;1;1;1\r\n1;1;1;1\r\n1;1;1;1\r\n1;1;1;1\r\n",
            ],
            ["\t", "\t", ",", "\t", ";", ";", ";", ";", ";"],
        ):
            res = client.put(raw_url, params={"path": matrix_path}, files={"file": io.BytesIO(content)})
            assert res.status_code == 204, res.json()
            res = client.get(raw_url, params={"path": matrix_path})
            written_data = res.json()["data"]
            if not content.decode("utf-8"):
                # The `GET` returns the default matrix when it's empty
                expected = 8760 * [[0]]
            else:
                df = pd.read_csv(io.BytesIO(content), delimiter=delimiter, header=None).replace(",", ".", regex=True)
                df = df.dropna(axis=1, how="all")  # We want to remove columns full of NaN at the import
                expected = df.to_numpy(dtype=np.float64).tolist()
            assert written_data == expected

        # If we ask for properties, we should have a JSON content
        rel_path = "/input/links/de/properties/fr"
        res = client.get(raw_url, params={"path": rel_path, "depth": 2})
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
        res = client.get(raw_url, params={"path": rel_path, "formatted": True})
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert actual == {"index": ANY, "columns": ANY, "data": ANY}

        # If we ask for a matrix, we should have a CSV content if formatted is False
        res = client.get(raw_url, params={"path": rel_path, "formatted": False})
        assert res.status_code == 200, res.json()
        actual = res.json()
        actual_lines = actual.splitlines()
        first_row = [float(x) for x in actual_lines[0].split("\t")]
        assert first_row == [100000, 100000, 0.01, 0.01, 0, 0, 0, 0]

        # If ask for an empty matrix, we should return its default value
        res = client.get(raw_url, params={"path": "input/thermal/prepro/de/01_solar/data", "formatted": True})
        assert res.status_code == 200, res.json()
        assert res.json()["index"] == list(range(365))
        assert res.json()["columns"] == list(range(6))
        assert res.json()["data"] == default_data_matrix.tolist()

        # We can access to the configuration the classic way,
        # for instance, we can get the list of areas:
        res = client.get(raw_url, params={"path": "/input/areas/list", "depth": 1})
        assert res.status_code == 200, res.json()
        assert res.json() == ["DE", "ES", "FR", "IT"]

        # asserts that the GET /raw endpoint is able to read matrix containing NaN values
        if study_type == "raw":
            res = client.get(raw_url, params={"path": "output/20201014-1427eco/economy/mc-all/areas/de/id-monthly"})
            assert res.status_code == 200
            assert np.isnan(res.json()["data"][0]).any()

        # Iterate over all possible combinations of path and depth
        for path, depth in itertools.product([None, "", "/"], [0, 1, 2]):
            res = client.get(raw_url, params={"path": path, "depth": depth})
            assert res.status_code == 200, f"Error for path={path} and depth={depth}"

        # =============================
        #  ERRORS
        # =============================

        # Some files can be corrupted
        user_folder_dir = study_dir.joinpath("user/bad")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir)
            res = client.get(raw_url, params={"path": f"/{rel_path.as_posix()}", "depth": 1})
            assert res.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY

        # Imports a wrongly formatted matrix
        res = client.put(raw_url, params={"path": matrix_path}, files={"file": io.BytesIO(b"BLABLABLA")})
        assert res.status_code == 422
        assert res.json()["exception"] == "MatrixImportFailed"
        assert res.json()["description"] == "Could not parse the given matrix"

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_delete_raw(
        self, client: TestClient, user_access_token: str, internal_study_id: str, study_type: str
    ) -> None:
        # =============================
        #  SET UP
        # =============================
        if pytest.FAST_MODE:
            pytest.skip("Skipping test")
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        if study_type == "variant":
            # Copies the study, to convert it into a managed one.
            res = client.post(
                f"/v1/studies/{internal_study_id}/copy",
                headers={"Authorization": f"Bearer {user_access_token}"},
                params={"study_name": "default", "with_outputs": False, "use_task": False},
            )
            assert res.status_code == 201
            parent_id = res.json()
            res = client.post(f"/v1/studies/{parent_id}/variants", params={"name": "variant 1"})
            internal_study_id = res.json()

        # =============================
        #  NOMINAL CASES
        # =============================

        content = io.BytesIO(b"This is the end!")
        file_1_path = "user/file_1.txt"
        file_2_path = "user/folder/file_2.txt"
        file_3_path = "user/folder_2/file_3.txt"
        for f in [file_1_path, file_2_path, file_3_path]:
            # Creates a file / folder inside user folder.
            res = client.put(
                f"/v1/studies/{internal_study_id}/raw",
                params={"path": f, "create_missing": True},
                files={"file": content},
            )
            assert res.status_code == 204, res.json()

            # Deletes the file / folder
            if f == file_2_path:
                f = "user/folder"
            res = client.delete(f"/v1/studies/{internal_study_id}/raw?path={f}")
            assert res.status_code == 200
            # Asserts it doesn't exist anymore
            res = client.get(f"/v1/studies/{internal_study_id}/raw?path={f}")
            assert res.status_code == 404
            assert "not a child of" in res.json()["description"]

            # checks debug view
            res = client.get(f"/v1/studies/{internal_study_id}/raw?path=&depth=-1")
            assert res.status_code == 200
            tree = res.json()["user"]
            if f == file_3_path:
                # asserts the folder that wasn't deleted is still here.
                assert list(tree.keys()) == ["expansion", "folder_2"]
                assert tree["folder_2"] == {}
            else:
                # asserts deleted files cannot be seen inside the debug view
                assert list(tree.keys()) == ["expansion"]

        # =============================
        #  ERRORS
        # =============================

        # try to delete expansion folder
        res = client.delete(f"/v1/studies/{internal_study_id}/raw?path=/user/expansion")
        expected_msg = (
            "Resource deletion failed because the given path is inside the `expansion` folder: /user/expansion"
        )
        assert res.status_code == 403
        assert res.json()["exception"] == "ResourceDeletionNotAllowed"
        assert expected_msg in res.json()["description"]

        # try to delete a file which isn't inside the 'User' folder
        res = client.delete(f"/v1/studies/{internal_study_id}/raw?path=/input/thermal")
        expected_msg = "the given path isn't inside the 'User' folder"
        assert res.status_code == 403
        assert res.json()["exception"] == "ResourceDeletionNotAllowed"
        assert expected_msg in res.json()["description"]

        # With a path that doesn't exist
        res = client.delete(f"/v1/studies/{internal_study_id}/raw?path=user/fake_folder/fake_file.txt")
        expected_msg = "the given path doesn't exist"
        _check_endpoint_response(study_type, res, client, internal_study_id, expected_msg, "ResourceDeletionNotAllowed")

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_create_folder(
        self, client: TestClient, user_access_token: str, internal_study_id: str, study_type: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        if study_type == "variant":
            # Copies the study, to convert it into a managed one.
            res = client.post(
                f"/v1/studies/{internal_study_id}/copy",
                headers={"Authorization": f"Bearer {user_access_token}"},
                params={"study_name": "default", "with_outputs": False, "use_task": False},
            )
            assert res.status_code == 201
            parent_id = res.json()
            res = client.post(f"/v1/studies/{parent_id}/variants", params={"name": "variant 1"})
            internal_study_id = res.json()

        raw_url = f"/v1/studies/{internal_study_id}/raw"

        # =============================
        # NOMINAL CASES
        # =============================
        additional_params = {"resource_type": "folder", "create_missing": True}

        res = client.put(raw_url, params={"path": "user/folder_1", **additional_params})
        assert res.status_code == 204

        # same case with different writing should succeed
        res = client.put(raw_url, params={"path": "/user/folder_2", **additional_params})
        assert res.status_code == 204

        # create a folder within a non-existing one
        res = client.put(raw_url, params={"path": "/user/folder_x/folder_y", **additional_params})
        assert res.status_code == 204

        # checks debug view to see that folders were created
        res = client.get(f"/v1/studies/{internal_study_id}/raw?path=&depth=-1")
        assert res.status_code == 200
        tree = res.json()["user"]
        assert list(tree.keys()) == ["expansion", "folder_1", "folder_2", "folder_x"]
        assert tree["folder_x"] == {"folder_y": {}}

        # =============================
        #  ERRORS
        # =============================

        # we can't create a file without specifying a content
        res = client.put(raw_url, params={"path": "fake_path"})
        assert res.status_code == 422
        assert res.json()["description"] == "Argument mismatch: Must give a content to create a file"

        # we can't create a folder and specify a content at the same time
        res = client.put(raw_url, params={"path": "", "resource_type": "folder"}, files={"file": b"content"})
        assert res.status_code == 422
        assert res.json()["description"] == "Argument mismatch: Cannot give a content to create a folder"

        # try to create a folder outside `user` folder
        wrong_folder = "input/wrong_folder"
        expected_msg = f"the given path isn't inside the 'User' folder: {wrong_folder}"
        res = client.put(raw_url, params={"path": wrong_folder, **additional_params})
        assert res.status_code == 403
        assert res.json()["exception"] == "FolderCreationNotAllowed"
        assert expected_msg in res.json()["description"]

        # try to create a folder inside the 'expansion` folder
        expansion_folder = "user/expansion/wrong_folder"
        expected_msg = "Folder creation failed because the given path is inside the `expansion` folder: user/expansion/wrong_folder"
        res = client.put(raw_url, params={"path": expansion_folder, **additional_params})
        assert res.status_code == 403
        assert res.json()["exception"] == "FolderCreationNotAllowed"
        assert expected_msg in res.json()["description"]

        # try to create an already existing folder
        existing_folder = "user/folder_1"
        expected_msg = "the given resource already exists: folder_1"
        res = client.put(raw_url, params={"path": existing_folder, **additional_params})
        _check_endpoint_response(study_type, res, client, internal_study_id, expected_msg, "FolderCreationNotAllowed")

    def test_retrieve_from_archive(self, client: TestClient, user_access_token: str) -> None:
        # client headers
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # create a new study
        res = client.post("/v1/studies?name=MyStudy")
        assert res.status_code == 201

        # get the study id
        study_id = res.json()

        # add a new area to the study
        res = client.post(
            f"/v1/studies/{study_id}/areas",
            json={
                "name": "area 1",
                "type": "AREA",
                "metadata": {"country": "FR", "tags": ["a"]},
            },
        )
        assert res.status_code == 200, res.json()

        # archive the study
        res = client.put(f"/v1/studies/{study_id}/archive")
        assert res.status_code == 200
        task_id = res.json()
        wait_for(
            lambda: client.get(
                f"/v1/tasks/{task_id}",
            ).json()["status"]
            == 3
        )

        # retrieve a `Desktop.ini` file from inside the archive
        rel_path = "Desktop"
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": rel_path, "formatted": True},
        )
        assert res.status_code == 200

        # retrieve a `study.antares` file from inside the archive
        rel_path = "study"
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": rel_path, "formatted": True},
        )
        assert res.status_code == 200


@pytest.mark.integration_test
class TestFetchOriginalFile:
    """
    Check the retrieval of a file from Study folder
    """

    def test_get_study_file(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """
        Test the `get_study_file` endpoint for fetching for a file in its original format.

        This test retrieves a specific file from a study identified by a UUID and checks

        The test performs the following steps:
        1. Copies the user resources in the Study directory.
        2. Uses the API to download a file from the "user/folder" directory.
        3. Compares the fetched data with the expected file from disk.
        4. Check for cases where Errors should be returned.
        """
        # First copy the user resources in the Study directory
        with db():
            study: RawStudy = db.session.get(Study, internal_study_id)
            study_dir = pathlib.Path(study.path)
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        original_file_url = f"/v1/studies/{internal_study_id}/raw/original-file"

        shutil.copytree(
            ASSETS_DIR.joinpath("user"),
            study_dir.joinpath("user"),
            dirs_exist_ok=True,
        )

        # Then, use the API to download the files from the "user/folder" directory
        user_folder_dir = study_dir.joinpath("user/folder")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir).as_posix()
            res = client.get(original_file_url, params={"path": rel_path})
            assert res.status_code == 200, res.json()
            actual = res.content
            expected = file_path.read_bytes()
            assert actual == expected

        # retrieves a txt file from the outputs
        file_path = "output/20201014-1422eco-hello/simulation"
        res = client.get(f"/v1/studies/{internal_study_id}/raw/original-file", params={"path": file_path})
        assert res.status_code == 200
        assert res.headers.get("content-disposition") == "attachment; filename=simulation.log"
        actual = res.content
        expected = study_dir.joinpath(f"{file_path}.log").read_bytes()
        assert actual == expected

        # If the extension is unknown, we should have a "binary" content
        user_folder_dir = study_dir.joinpath("user/unknown")
        for file_path in user_folder_dir.glob("*.*"):
            rel_path = file_path.relative_to(study_dir)
            res = client.get(original_file_url, params={"path": f"/{rel_path.as_posix()}"})
            assert res.status_code == 200, res.json()

            actual = res.content
            expected = file_path.read_bytes()
            assert actual == expected

        # If you try to retrieve a file that doesn't exist, we should have a 404 error
        res = client.get(original_file_url, params={"path": "user/somewhere/something.txt"})
        assert res.status_code == 404, res.json()
        assert res.json() == {
            "description": "'somewhere' not a child of User",
            "exception": "ChildNotFoundError",
        }

        # If you try to retrieve a folder, we should get an Error 422
        res = client.get(original_file_url, params={"path": "user/folder"})
        assert res.status_code == 422, res.json()
        assert res.json()["description"] == "Node at user/folder is a folder node."
        assert res.json()["exception"] == "PathIsAFolderError"

    @pytest.mark.parametrize("archive", [True, False])
    def test_retrieve_original_files(self, client: TestClient, user_access_token: str, archive: bool) -> None:
        # client headers
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # create a new study
        res = client.post("/v1/studies", params={"name": "MyStudy", "version": "880"})
        assert res.status_code == 201
        study_id = res.json()

        # add a new area to the study
        res = client.post(
            f"/v1/studies/{study_id}/areas",
            json={
                "name": "area 1",
                "type": "AREA",
                "metadata": {"country": "FR", "tags": ["a"]},
            },
        )
        assert res.status_code == 200, res.json()

        if archive:
            # archive the study
            res = client.put(f"/v1/studies/{study_id}/archive")
            assert res.status_code == 200
            task_id = res.json()
            wait_for(lambda: client.get(f"/v1/tasks/{task_id}").json()["status"] == 3)

        # retrieves an `ini` file
        res = client.get(
            f"/v1/studies/{study_id}/raw/original-file", params={"path": "input/areas/area 1/adequacy_patch"}
        )
        assert res.status_code == 200
        assert res.headers.get("content-disposition") == "attachment; filename=adequacy_patch.ini"
        assert res.content.strip().decode("utf-8").splitlines() == ["[adequacy-patch]", "adequacy-patch-mode = outside"]

        # retrieves the `study.antares`
        res = client.get(f"/v1/studies/{study_id}/raw/original-file", params={"path": "study"})
        assert res.status_code == 200
        assert res.headers.get("content-disposition") == "attachment; filename=study.antares"
        assert res.content.strip().decode().splitlines()[:3] == ["[antares]", "version = 880", "caption = MyStudy"]

        # retrieves a matrix (a link towards the matrix store if the study is unarchived, else the real matrix)
        res = client.get(f"/v1/studies/{study_id}/raw/original-file", params={"path": "input/load/series/load_area 1"})
        assert res.status_code == 200
        assert res.headers.get("content-disposition") == "attachment; filename=load_area 1.txt"
        expected_content = np.zeros((8760, 1))
        actual_content = pd.read_csv(io.BytesIO(res.content), header=None)
        assert actual_content.to_numpy().tolist() == expected_content.tolist()
