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
import operator
import re
import typing as t
from pathlib import Path

from pytest_mock import MockerFixture
from starlette.testclient import TestClient

from tests.integration.conftest import RESOURCES_DIR


class AnyDiskUsagePercent:
    """A helper object that compares equal to any disk usage percentage."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented
        return bool(re.fullmatch(r"\d+(?:\.\d+)?% used", other))

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return "<AnyDiskUsagePercent>"


class AnyIsoDateTime:
    """A helper object that compares equal to any date time in ISO 8601 format."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented
        try:
            return bool(datetime.datetime.fromisoformat(other))
        except ValueError:
            return False

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return "<AnyDiskUsagePercent>"


class IntegerRange:
    """A helper object that compares equal to any integer in a given range."""

    def __init__(self, start: int, stop: int) -> None:
        self.start = start
        self.stop = stop

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, int):
            return NotImplemented
        return self.start <= other <= self.stop

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented
        return not self.__eq__(other)

    def __repr__(self) -> str:
        start = getattr(self, "start", None)
        stop = getattr(self, "stop", None)
        return f"<IntegerRange({start=}, {stop=})>"


# noinspection SpellCheckingInspection
class TestFilesystemEndpoints:
    """Test the filesystem endpoints."""

    def test_lifecycle(
        self,
        tmp_path: Path,
        caplog: t.Any,
        client: TestClient,
        user_access_token: str,
        admin_access_token: str,
        mocker: MockerFixture,
    ) -> None:
        """
        Test the lifecycle of the filesystem endpoints.

        Args:
            tmp_path: pytest tmp_path fixture.
            caplog: pytest caplog fixture.
            client: test client (tests.integration.conftest.client_fixture).
            user_access_token: access token of a classic user (tests.integration.conftest.user_access_token_fixture).
            admin_access_token: access token of an admin user (tests.integration.conftestin_access_token_fixture).
        """
        # NOTE: all the following paths are based on the configuration defined in the app_fixture.
        archive_dir = tmp_path / "archive_dir"
        matrix_dir = tmp_path / "matrix_store"
        resource_dir = RESOURCES_DIR
        tmp_dir = tmp_path / "tmp"
        default_workspace = tmp_path / "internal_workspace"
        ext_workspace_path = tmp_path / "ext_workspace"

        expected: t.Union[t.Sequence[t.Mapping[str, t.Any]], t.Mapping[str, t.Any]]

        with caplog.at_level(level="ERROR", logger="antarest.main"):
            # Count the number of errors in the caplog
            err_count = 0

            # ==================================================
            # Get the list of filesystems and their mount points
            # ==================================================

            # Without authentication
            res = client.get("/v1/filesystem")
            assert res.status_code == 401, res.json()
            assert res.json()["detail"] == "Missing cookie access_token_cookie"
            # This error generates no log entry
            # err_count += 1

            # With authentication
            user_headers = {"Authorization": f"Bearer {user_access_token}"}
            res = client.get("/v1/filesystem", headers=user_headers)
            assert res.status_code == 200, res.json()
            actual = res.json()
            expected = [
                {
                    "name": "cfg",
                    "mount_dirs": {
                        "archive": str(archive_dir),
                        "matrix": str(matrix_dir),
                        "res": str(resource_dir),
                        "tmp": str(tmp_dir),
                    },
                },
                {
                    "name": "ws",
                    "mount_dirs": {
                        "default": str(default_workspace),
                        "ext": str(ext_workspace_path),
                    },
                },
            ]
            assert actual == expected

            # ===================================================================
            # Get the path and the disk usage of the mount points in a filesystem
            # ===================================================================

            # Unknown filesystem
            res = client.get("/v1/filesystem/foo", headers=user_headers)
            assert res.status_code == 404, res.json()
            assert res.json()["description"] == "Filesystem not found: 'foo'"
            err_count += 1

            # Known filesystem
            mocker.patch("shutil.disk_usage", return_value=(100, 200, 300))
            res = client.get("/v1/filesystem/ws", headers=user_headers)
            assert res.status_code == 200, res.json()
            actual = sorted(res.json(), key=operator.itemgetter("name"))
            expected = [
                {
                    "name": "default",
                    "path": str(default_workspace),
                    "total_bytes": 100,
                    "used_bytes": 200,
                    "free_bytes": 300,
                    "message": AnyDiskUsagePercent(),
                },
                {
                    "name": "ext",
                    "path": str(ext_workspace_path),
                    "total_bytes": 100,
                    "used_bytes": 200,
                    "free_bytes": 300,
                    "message": AnyDiskUsagePercent(),
                },
            ]
            assert actual == expected

            # ================================================
            # Get the path and the disk usage of a mount point
            # ================================================

            # Unknown mount point
            res = client.get("/v1/filesystem/ws/foo", headers=user_headers)
            assert res.status_code == 404, res.json()
            assert res.json()["description"] == "Mount point not found: 'ws/foo'"
            err_count += 1

            res = client.get("/v1/filesystem/ws/default", headers=user_headers)
            assert res.status_code == 200, res.json()
            actual = res.json()
            expected = {
                "name": "default",
                "path": str(default_workspace),
                "total_bytes": 100,
                "used_bytes": 200,
                "free_bytes": 300,
                "message": AnyDiskUsagePercent(),
            }
            assert actual == expected

            # =========================================
            # List files and directories in a workspace
            # =========================================

            # Listing a workspace with and invalid glob pattern raises an error
            res = client.get("/v1/filesystem/ws/default/ls", headers=user_headers, params={"path": "."})
            assert res.status_code == 400, res.json()
            assert res.json()["description"].startswith("Invalid path: '.'"), res.json()
            err_count += 1

            # Providing en absolute to an external workspace is not allowed
            res = client.get("/v1/filesystem/ws/ext/ls", headers=user_headers, params={"path": "/foo"})
            assert res.status_code == 403, res.json()
            assert res.json()["description"].startswith("Access denied to path: '/foo'"), res.json()
            err_count += 1

            # Recursively search all "study.antares" files in the "default" workspace
            res = client.get("/v1/filesystem/ws/default/ls", headers=user_headers, params={"path": "**/study.antares"})
            assert res.status_code == 200, res.json()
            actual = res.json()
            # There is no managed study in the "default" workspace
            expected = []
            assert actual == expected

            # Recursively search all "study.antares" files in the "ext" workspace
            res = client.get("/v1/filesystem/ws/ext/ls", headers=user_headers, params={"path": "**/study.antares"})
            assert res.status_code == 200, res.json()
            actual = res.json()
            # There is one external study in the "ext" workspace, which is "STA-mini"
            expected = [
                {
                    "path": str(ext_workspace_path / "STA-mini" / "study.antares"),
                    "file_type": "file",
                    "file_count": 1,
                    "size_bytes": 112,
                    "created": AnyIsoDateTime(),
                    "accessed": AnyIsoDateTime(),
                    "modified": AnyIsoDateTime(),
                    "message": "OK",
                }
            ]
            assert actual == expected

            # Get the details of the "STA-mini" study
            res = client.get(
                "/v1/filesystem/ws/ext/ls",
                headers=user_headers,
                params={"path": "STA-mini", "details": True},  # type: ignore
            )
            assert res.status_code == 200, res.json()
            actual = res.json()
            expected = [
                {
                    "path": str(ext_workspace_path / "STA-mini"),
                    "file_type": "directory",
                    "file_count": IntegerRange(1000, 1100),  # 1043
                    "size_bytes": IntegerRange(9_000_000, 11_000_000),  # 10_428_620
                    "created": AnyIsoDateTime(),
                    "accessed": AnyIsoDateTime(),
                    "modified": AnyIsoDateTime(),
                    "message": "OK",
                }
            ]
            assert actual == expected

            # =================================
            # View a text file from a workspace
            # =================================

            # Providing an empty path is not allowed
            res = client.get("/v1/filesystem/ws/ext/cat", headers=user_headers, params={"path": ""})
            assert res.status_code == 400, res.json()
            assert res.json()["description"] == "Empty or missing path parameter"
            err_count += 1

            # Providing en absolute to an external workspace is not allowed
            res = client.get("/v1/filesystem/ws/ext/cat", headers=user_headers, params={"path": "/foo"})
            assert res.status_code == 403, res.json()
            assert res.json()["description"] == "Access denied to path: '/foo'"
            err_count += 1

            # Providing a directory path is not allowed
            res = client.get("/v1/filesystem/ws/ext/cat", headers=user_headers, params={"path": "STA-mini"})
            assert res.status_code == 417, res.json()
            assert res.json()["description"] == "Path is not a file: 'STA-mini'"
            err_count += 1

            # Let's create a dummy file in the "ext" workspace, and write some text in it
            dummy_file = ext_workspace_path / "dummy.txt"
            dummy_file.write_text("Hello, world!")

            # Authorized users can view text files
            res = client.get("/v1/filesystem/ws/ext/cat", headers=user_headers, params={"path": "dummy.txt"})
            assert res.status_code == 200, res.json()
            assert res.text == "Hello, world!"

            # If the file is missing, a 404 error is returned
            res = client.get("/v1/filesystem/ws/ext/cat", headers=user_headers, params={"path": "missing.txt"})
            assert res.status_code == 404, res.json()
            assert res.json()["description"] == "Path not found: 'missing.txt'"
            err_count += 1

            # If the file is not a text file, a 417 error is returned
            res = client.get("/v1/filesystem/ws/ext/cat", headers=user_headers, params={"path": "STA-mini"})
            assert res.status_code == 417, res.json()
            assert res.json()["description"] == "Path is not a file: 'STA-mini'"
            err_count += 1

            # If the user choose an unknown encoding, a 417 error is returned
            res = client.get(
                "/v1/filesystem/ws/ext/cat",
                headers=user_headers,
                params={"path": "dummy.txt", "encoding": "unknown"},
            )
            assert res.status_code == 417, res.json()
            assert res.json()["description"] == "Unknown encoding: 'unknown'"
            err_count += 1

            # If the file is not a texte file, a 417 error may be returned
            dummy_file.write_bytes(b"\x81\x82\x83")  # invalid utf-8 bytes
            res = client.get("/v1/filesystem/ws/ext/cat", headers=user_headers, params={"path": "dummy.txt"})
            assert res.status_code == 417, res.json()
            assert res.json()["description"] == "Failed to decode file: 'dummy.txt'"
            err_count += 1

            # ================================
            # Download a file from a workspace
            # ================================

            # Providing an empty path is not allowed
            res = client.get("/v1/filesystem/ws/ext/download", headers=user_headers, params={"path": ""})
            assert res.status_code == 400, res.json()
            assert res.json()["description"] == "Empty or missing path parameter"
            err_count += 1

            # Providing en absolute to an external workspace is not allowed
            res = client.get("/v1/filesystem/ws/ext/download", headers=user_headers, params={"path": "/foo"})
            assert res.status_code == 403, res.json()
            assert res.json()["description"] == "Access denied to path: '/foo'"
            err_count += 1

            # Providing a directory path is not allowed
            res = client.get("/v1/filesystem/ws/ext/download", headers=user_headers, params={"path": "STA-mini"})
            assert res.status_code == 417, res.json()
            assert res.json()["description"] == "Path is not a file: 'STA-mini'"
            err_count += 1

            # Let's create a dummy file in the "ext" workspace, and write some binary data in it
            dummy_file = ext_workspace_path / "dummy.bin"
            dummy_file.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09")

            # Authorized users can download files
            res = client.get("/v1/filesystem/ws/ext/download", headers=user_headers, params={"path": "dummy.bin"})
            assert res.status_code == 200, res.json()
            assert res.content == b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"

            # If the file is missing, a 404 error is returned
            res = client.get("/v1/filesystem/ws/ext/download", headers=user_headers, params={"path": "missing.bin"})
            assert res.status_code == 404, res.json()
            assert res.json()["description"] == "Path not found: 'missing.bin'"
            err_count += 1

            # Downloading a directory is not allowed
            res = client.get("/v1/filesystem/ws/ext/download", headers=user_headers, params={"path": "STA-mini"})
            assert res.status_code == 417, res.json()
            assert res.json()["description"] == "Path is not a file: 'STA-mini'"
            err_count += 1

        # At the end of this unit test, the caplog should have errors
        assert len(caplog.records) == err_count, caplog.records

    def test_size_of_studies(
        self,
        client: TestClient,
        user_access_token: str,
    ):
        """
        This test demonstrates how to compute the size of all studies.

        - First, we get the list of studies using the `/v1/studies` endpoint.
        - Then, we get the size of each study using the `/v1/filesystem/ws/{workspace}/ls` endpoint,
          with the `details` parameter set to `True`.
        """
        user_headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create a new study in the "default" workspace for this demo
        res = client.post(
            "/v1/studies",
            headers=user_headers,
            params={"name": "New Study", "version": "860"},
        )
        res.raise_for_status()

        # Get the list of studies from all workspaces
        res = client.get("/v1/studies", headers=user_headers)
        res.raise_for_status()
        actual = res.json()

        # Get the size of each study
        sizes = []
        for study in actual.values():
            res = client.get(
                f"/v1/filesystem/ws/{study['workspace']}/ls",
                headers=user_headers,
                params={"path": study["folder"], "details": True},
            )
            res.raise_for_status()
            actual = res.json()
            sizes.append(actual[0]["size_bytes"])

        # Check the sizes
        # The size of the new study should be between 140 and 350 KB.
        # The suze of 'STA-mini' should be between 9 and 11 MB.
        sizes.sort()
        assert sizes == [IntegerRange(140_000, 350_000), IntegerRange(9_000_000, 11_000_000)]
