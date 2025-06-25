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
import operator
import re
import shutil
import typing as t
import zipfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.model import PublicMode
from antarest.core.roles import RoleType
from antarest.core.tasks.model import TaskStatus
from tests.integration.assets import ASSETS_DIR
from tests.integration.utils import wait_task_completion

# URL used to create or list studies
STUDIES_URL = "/v1/studies"

# Status codes for study creation requests
CREATE_STATUS_CODES = {200, 201}

# Status code for study listing requests
LIST_STATUS_CODE = 200

# Status code for study listing with invalid parameters
INVALID_PARAMS_STATUS_CODE = 422


class TestStudiesListing:
    """
    This class contains tests related to the following endpoints:

    - GET /v1/studies
    """

    # noinspection PyUnusedLocal
    @pytest.fixture(name="to_be_deleted_study_path", autouse=True)
    def studies_in_ext_fixture(self, tmp_path: Path, app: FastAPI) -> Path:
        # create a non managed raw study version 840
        study_dir = tmp_path / "ext_workspace" / "ext-840"
        study_dir.mkdir(exist_ok=True)
        zip_path = ASSETS_DIR.joinpath("ext-840.zip")
        with zipfile.ZipFile(zip_path) as zip_output:
            zip_output.extractall(path=study_dir)

        # create a non managed raw study version 850
        study_dir = tmp_path / "ext_workspace" / "ext-850"
        study_dir.mkdir(exist_ok=True)
        zip_path = ASSETS_DIR.joinpath("ext-850.zip")
        with zipfile.ZipFile(zip_path) as zip_output:
            zip_output.extractall(path=study_dir)

        # create a non managed raw study version 860
        study_dir = tmp_path / "ext_workspace" / "ext-860"
        study_dir.mkdir(exist_ok=True)
        zip_path = ASSETS_DIR.joinpath("ext-860.zip")
        with zipfile.ZipFile(zip_path) as zip_output:
            zip_output.extractall(path=study_dir)

        # create a non managed raw study version 840 to be deleted from disk
        study_dir = tmp_path / "ext_workspace" / "to-be-deleted-840"
        study_dir.mkdir(exist_ok=True)
        zip_path = ASSETS_DIR.joinpath("ext-840.zip")
        with zipfile.ZipFile(zip_path) as zip_output:
            zip_output.extractall(path=study_dir)

        return study_dir

    def test_study_listing(
        self,
        client: TestClient,
        admin_access_token: str,
        to_be_deleted_study_path: Path,
    ) -> None:
        """
        This test verifies that database is correctly initialized and then runs the filtering tests with different
        parameters
        """

        # ==========================
        # 1. Database initialization
        # ==========================

        # database update to include non managed studies using the watcher
        res = client.post(
            "/v1/watcher/_scan",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"path": "ext"},
        )
        res.raise_for_status()
        task_id = res.json()
        task = wait_task_completion(client, admin_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        # retrieve a created non managed + to be deleted study IDs
        res = client.get(STUDIES_URL, headers={"Authorization": f"Bearer {admin_access_token}"})
        res.raise_for_status()
        folder_map = {v["folder"]: k for k, v in res.json().items()}
        non_managed_840_id = folder_map["ext-840"]
        non_managed_850_id = folder_map["ext-850"]
        non_managed_860_id = folder_map["ext-860"]
        to_be_deleted_id = folder_map["to-be-deleted-840"]

        # delete study `to_be_deleted_id` from disk
        shutil.rmtree(to_be_deleted_study_path)
        assert not to_be_deleted_study_path.exists()

        # database update with missing studies
        res = client.post(
            "/v1/watcher/_scan",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"path": "ext"},
        )
        res.raise_for_status()
        task_id = res.json()
        task = wait_task_completion(client, admin_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        # change permissions for non managed studies (no access but to admin)
        non_managed_studies = {non_managed_840_id, non_managed_850_id, non_managed_860_id, to_be_deleted_id}
        no_access_code = "NONE"
        for non_managed_study in non_managed_studies:
            res = client.put(
                f"/v1/studies/{non_managed_study}/public_mode/{no_access_code}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
                json={"name": "James Bond", "password": "0007"},
            )
            res.raise_for_status()

        # create a user 'James Bond' with password '007'
        res = client.post(
            "/v1/users",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"name": "James Bond", "password": "0007"},
        )
        res.raise_for_status()
        james_bond_id = res.json().get("id")

        # create a user 'John Doe' with password '0011'
        res = client.post(
            "/v1/users",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"name": "John Doe", "password": "0011"},
        )
        res.raise_for_status()
        john_doe_id = res.json().get("id")

        # create a group 'Group X' with id 'groupX'
        res = client.post(
            "/v1/groups",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"name": "Group X", "id": "groupX"},
        )
        res.raise_for_status()
        group_x_id = res.json().get("id")
        assert group_x_id == "groupX"

        # create a group 'Group Y' with id 'groupY'
        res = client.post(
            "/v1/groups",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"name": "Group Y", "id": "groupY"},
        )
        res.raise_for_status()
        group_y_id = res.json().get("id")
        assert group_y_id == "groupY"

        # login 'James Bond'
        res = client.post(
            "/v1/login",
            json={"username": "James Bond", "password": "0007"},
        )
        res.raise_for_status()
        assert res.json().get("user") == james_bond_id
        james_bond_access_token = res.json().get("access_token")

        # login 'John Doe'
        res = client.post(
            "/v1/login",
            json={"username": "John Doe", "password": "0011"},
        )
        res.raise_for_status()
        assert res.json().get("user") == john_doe_id
        john_doe_access_token = res.json().get("access_token")

        # create a bot user 'James Bond'
        res = client.post(
            "/v1/bots",
            headers={"Authorization": f"Bearer {james_bond_access_token}"},
            json={"name": "James Bond", "roles": []},
        )
        res.raise_for_status()
        james_bond_bot_token = res.json()

        # create a raw study version 840
        res = client.post(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "raw-840", "version": "840"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        raw_840_id = res.json()

        # create a raw study version 850
        res = client.post(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "raw-850", "version": "850"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        raw_850_id = res.json()

        # create a raw study version 860
        res = client.post(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "raw-860", "version": "860"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        raw_860_id = res.json()

        # create a variant study version 840
        res = client.post(
            f"{STUDIES_URL}/{raw_840_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "variant-840", "version": "840"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        variant_840_id = res.json()

        # create a variant study version 850
        res = client.post(
            f"{STUDIES_URL}/{raw_850_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "variant-850", "version": "850"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        variant_850_id = res.json()

        # create a variant study version 860
        res = client.post(
            f"{STUDIES_URL}/{raw_860_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "variant-860", "version": "860"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        variant_860_id = res.json()

        # create a raw study version 840 to be archived
        res = client.post(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "archived-raw-840", "version": "840"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        archived_raw_840_id = res.json()

        # create a raw study version 850 to be archived
        res = client.post(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "archived-raw-850", "version": "850"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        archived_raw_850_id = res.json()

        # create a raw study to be transferred in folder1
        zip_path = ASSETS_DIR / "STA-mini.zip"
        res = client.post(
            f"{STUDIES_URL}/_import",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            files={"study": io.BytesIO(zip_path.read_bytes())},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        folder1_study_id = res.json()
        res = client.put(
            f"{STUDIES_URL}/{folder1_study_id}/move",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"folder_dest": "folder1"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()

        # give permission to James Bond for some select studies
        james_bond_studies = {raw_840_id, variant_850_id, non_managed_860_id}
        for james_bond_study in james_bond_studies:
            res = client.put(
                f"{STUDIES_URL}/{james_bond_study}/owner/{james_bond_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()

        # associate select studies to each group: groupX, groupY
        group_x_studies = {variant_850_id, raw_860_id}
        group_y_studies = {raw_850_id, raw_860_id}
        for group_x_study in group_x_studies:
            res = client.put(
                f"{STUDIES_URL}/{group_x_study}/groups/{group_x_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()
        for group_y_study in group_y_studies:
            res = client.put(
                f"{STUDIES_URL}/{group_y_study}/groups/{group_y_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()

        # archive studies
        archive_studies = {archived_raw_840_id, archived_raw_850_id}
        for archive_study in archive_studies:
            res = client.put(
                f"{STUDIES_URL}/{archive_study}/archive",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()
            archiving_study_task_id = res.json()
            task = wait_task_completion(client, admin_access_token, archiving_study_task_id)
            assert task.status == TaskStatus.COMPLETED, task

        # create a raw study version 840 to be tagged with `Winter_Transition`
        res = client.post(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "winter-transition-raw-840", "version": "840"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        tagged_raw_840_id = res.json()
        res = client.put(
            f"{STUDIES_URL}/{tagged_raw_840_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"tags": ["Winter_Transition"]},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "winter-transition-raw-840"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map: t.Dict[str, t.Dict[str, t.Any]] = res.json()
        assert len(study_map) == 1
        assert set(study_map[tagged_raw_840_id]["tags"]) == {"Winter_Transition"}

        # create a raw study version 850 to be tagged with `decennial`
        res = client.post(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "decennial-raw-850", "version": "850"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        tagged_raw_850_id = res.json()
        res = client.put(
            f"{STUDIES_URL}/{tagged_raw_850_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"tags": ["decennial"]},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "decennial-raw-850"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert len(study_map) == 1
        assert set(study_map[tagged_raw_850_id]["tags"]) == {"decennial"}

        # create a variant study version 840 to be tagged with `decennial`
        res = client.post(
            f"{STUDIES_URL}/{tagged_raw_840_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "decennial-variant-840", "version": "840"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        tagged_variant_840_id = res.json()
        res = client.put(
            f"{STUDIES_URL}/{tagged_variant_840_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"tags": ["decennial"]},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "decennial-variant-840"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert len(study_map) == 1
        assert set(study_map[tagged_variant_840_id]["tags"]) == {"decennial"}

        # create a variant study version 850 to be tagged with `winter_transition`.
        # also test that the tag label is case-insensitive.
        res = client.post(
            f"{STUDIES_URL}/{tagged_raw_850_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "winter-transition-variant-850", "version": "850"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        tagged_variant_850_id = res.json()
        res = client.put(
            f"{STUDIES_URL}/{tagged_variant_850_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"tags": ["winter_transition"]},  # note the tag label is in lower case
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "winter-transition-variant-850"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert len(study_map) == 1
        assert set(study_map[tagged_variant_850_id]["tags"]) == {"Winter_Transition"}

        # ==========================
        # 2. Filtering testing
        # ==========================

        # the testing studies set
        all_studies = {
            raw_840_id,
            raw_850_id,
            raw_860_id,
            non_managed_840_id,
            non_managed_850_id,
            non_managed_860_id,
            variant_840_id,
            variant_850_id,
            variant_860_id,
            archived_raw_840_id,
            archived_raw_850_id,
            folder1_study_id,
            to_be_deleted_id,
            tagged_raw_840_id,
            tagged_raw_850_id,
            tagged_variant_840_id,
            tagged_variant_850_id,
        }

        pm = operator.itemgetter("public_mode")

        # tests (1) for user permission filtering
        # test 1.a for a user with no access permission
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {john_doe_access_token}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.intersection(study_map)
        assert all(map(lambda x: pm(x) in [PublicMode.READ, PublicMode.FULL], study_map.values()))
        # test pagination
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {john_doe_access_token}"},
            params={"pageNb": 1, "pageSize": 2},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        page_studies = res.json()
        assert len(page_studies) == max(0, min(2, len(study_map) - 2))

        # test 1.b for an admin user
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(study_map)
        # test pagination
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"pageNb": 1, "pageSize": 2},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        page_studies = res.json()
        assert len(page_studies) == max(0, min(len(study_map) - 2, 2))
        # test pagination concatenation
        paginated_studies = {}
        page_number = 0
        number_of_pages = 0
        while len(paginated_studies) < len(study_map):
            res = client.get(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"pageNb": page_number, "pageSize": 2},
            )
            assert res.status_code == LIST_STATUS_CODE, res.json()
            paginated_studies.update(res.json())
            page_number += 1
            number_of_pages += 1
        assert paginated_studies == study_map
        assert number_of_pages == len(study_map) // 2 + len(study_map) % 2

        # test 1.c for a user with access to select studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {james_bond_access_token}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not james_bond_studies.difference(study_map)
        assert all(
            map(
                lambda x: pm(x) in [PublicMode.READ, PublicMode.FULL],
                [e for k, e in study_map.items() if k not in james_bond_studies],
            )
        )

        # #TODO you need to update the permission for James Bond bot above
        # test 1.d for a user bot with access to select studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {james_bond_bot_token}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        # #TODO add the correct test assertions
        # ] = res.json()
        # assert not set(james_bond_studies).difference(study_map)
        # assert all(
        #     map(
        #         lambda x: pm(x) in [PublicMode.READ, PublicMode.FULL],
        #         [e for k, e in study_map.items() if k not in james_bond_studies],
        #     )
        # )

        # tests (2) for studies names filtering
        # test 2.a with matching studies
        res = client.get(STUDIES_URL, headers={"Authorization": f"Bearer {admin_access_token}"}, params={"name": "840"})
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert all(map(lambda x: "840" in x["name"], study_map.values())) and len(study_map) >= 5
        # test 2.b with no matching studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "NON-SENSE-746846351469798465"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not study_map

        # tests (3) managed studies vs non managed
        # test 3.a managed
        managed_studies = all_studies.difference(non_managed_studies)
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"managed": True},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not managed_studies.difference(study_map)
        assert not all_studies.difference(managed_studies).intersection(study_map)
        # test 3.b non managed
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"managed": False},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(managed_studies).difference(study_map)
        assert not managed_studies.intersection(study_map)

        # tests (4) archived vs non archived
        # test 4.a archived studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"archived": True},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not archive_studies.difference(study_map)
        assert not all_studies.difference(archive_studies).intersection(study_map)
        # test 4.b non archived
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"archived": False},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(archive_studies).difference(study_map)
        assert not archive_studies.intersection(study_map)

        # tests (5) for filtering variant studies
        variant_studies = {
            variant_840_id,
            variant_850_id,
            variant_860_id,
            tagged_variant_840_id,
            tagged_variant_850_id,
        }
        # test 5.a get variant studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"variant": True},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not variant_studies.difference(study_map)
        assert not all_studies.difference(variant_studies).intersection(study_map)
        # test 5.b get raw studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"variant": False},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(variant_studies).difference(study_map)
        assert not variant_studies.intersection(study_map)

        # tests (6) for version filtering
        studies_version_850 = {
            raw_850_id,
            non_managed_850_id,
            variant_850_id,
            archived_raw_850_id,
            tagged_variant_850_id,
            tagged_raw_850_id,
        }
        studies_version_860 = {
            raw_860_id,
            non_managed_860_id,
            variant_860_id,
        }
        # test 6.a filter for one version: 860
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"versions": "860"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(studies_version_860).intersection(study_map)
        assert not studies_version_860.difference(study_map)
        # test 8.b filter for two versions: 850, 860
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"versions": "850,860"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(studies_version_850.union(studies_version_860)).intersection(study_map)
        assert not studies_version_850.union(studies_version_860).difference(study_map)
        # test pagination
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"versions": "850,860", "pageNb": 1, "pageSize": 2},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        page_studies = res.json()
        assert len(page_studies) == max(0, min(len(study_map) - 2, 2))

        # tests (7) for users filtering
        # test 7.a to get studies for one user: James Bond
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"users": f"{james_bond_id}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(james_bond_studies).intersection(study_map)
        assert not james_bond_studies.difference(study_map)
        # test 7.b to get studies for two users
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"users": f"{james_bond_id},{john_doe_id}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(james_bond_studies).intersection(study_map)
        assert not james_bond_studies.difference(study_map)

        # tests (8) for groups filtering
        # test 8.a filter for one group: groupX
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"groups": f"{group_x_id}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(group_x_studies).intersection(study_map)
        assert not group_x_studies.difference(study_map)
        # test 8.b filter for two groups: groupX, groupY
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"groups": f"{group_x_id},{group_y_id}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(group_x_studies.union(group_y_studies)).intersection(study_map)
        assert not group_x_studies.union(group_y_studies).difference(study_map)

        # tests (9) for tags filtering
        # test 9.a filtering for one tag: decennial
        decennial_tagged_studies = {tagged_raw_850_id, tagged_variant_840_id}
        winter_transition_tagged_studies = {tagged_raw_840_id, tagged_variant_850_id}
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"tags": "DECENNIAL"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(decennial_tagged_studies).intersection(study_map)
        assert not decennial_tagged_studies.difference(study_map)
        # test 9.b filtering for two tags: decennial,winter_transition
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"tags": "decennial,winter_transition"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(
            decennial_tagged_studies.union(winter_transition_tagged_studies)
        ).intersection(study_map)
        assert not decennial_tagged_studies.union(winter_transition_tagged_studies).difference(study_map)

        # tests (10) for studies uuids sequence filtering
        # test 10.a filter for one uuid
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"studyIds": f"{raw_840_id}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert {raw_840_id} == set(study_map)
        # test 10.b filter for two uuids
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"studyIds": f"{raw_840_id},{raw_860_id}"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert {raw_840_id, raw_860_id} == set(study_map)

        # tests (11) studies filtering regarding existence on disk
        existing_studies = all_studies.difference({to_be_deleted_id})
        # test 11.a filter existing studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"exists": True},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not existing_studies.difference(study_map)
        assert not all_studies.difference(existing_studies).intersection(study_map)
        # test 11.b filter non-existing studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"exists": False},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not all_studies.difference(existing_studies).difference(study_map)
        assert not existing_studies.intersection(study_map)

        # tests (12) studies filtering with workspace
        ext_workspace_studies = non_managed_studies
        # test 12.a filter `ext` workspace studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"workspace": "ext"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not ext_workspace_studies.difference(study_map)
        assert not all_studies.difference(ext_workspace_studies).intersection(study_map)

        # tests (13) studies filtering with folder
        # test 13.a filter `folder1` studies
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"folder": "folder1"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert not {folder1_study_id}.difference(study_map)
        assert not all_studies.difference({folder1_study_id}).intersection(study_map)

        # test sort by name ASC
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"sortBy": "+name"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        values = list(study_map.values())
        assert values == sorted(values, key=lambda x: x["name"].upper())

        # test sort by name DESC
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"sortBy": "-name"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        values = list(study_map.values())
        assert values == sorted(values, key=lambda x: x["name"].upper(), reverse=True)

        # test sort by date ASC
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"sortBy": "+date"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        values = list(study_map.values())
        assert values == sorted(values, key=lambda x: x["created"])

        # test sort by date DESC
        res = client.get(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"sortBy": "-date"},
        )
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        values = list(study_map.values())
        assert values == sorted(values, key=lambda x: x["created"], reverse=True)

    def test_get_studies__access_permissions(self, client: TestClient, admin_access_token: str) -> None:
        """
        Test the access permissions for the `GET /studies` endpoint.

        Args:
            client: client App fixture to perform the requests
            admin_access_token: fixture to get the admin access token

        Returns:

        """
        ##########################
        # 1. Database initialization
        ##########################
        if pytest.FAST_MODE:
            pytest.skip("Skipping test")
        users = {"user_1": "pass_1", "user_2": "pass_2", "user_3": "pass_3"}
        users_tokens = {}
        users_ids = {}
        groups = {"group_1", "group_2", "group_3"}
        groups_ids = {}
        user_groups_mapping = {"user_1": ["group_2"], "user_2": ["group_1"], "user_3": []}

        # create users
        for user, password in users.items():
            res = client.post(
                "/v1/users",
                headers={"Authorization": f"Bearer {admin_access_token}"},
                json={"name": user, "password": password},
            )
            res.raise_for_status()
            users_ids[user] = res.json().get("id")

        # create groups
        for group in groups:
            res = client.post(
                "/v1/groups",
                headers={"Authorization": f"Bearer {admin_access_token}"},
                json={"name": group},
            )
            res.raise_for_status()
            groups_ids[group] = res.json().get("id")

        # associate users to groups
        for user, groups in user_groups_mapping.items():
            user_id = users_ids[user]
            for group in groups:
                group_id = groups_ids[group]
                res = client.post(
                    "/v1/roles",
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                    json={"identity_id": user_id, "group_id": group_id, "type": RoleType.READER.value},
                )
                res.raise_for_status()

        # login users
        for user, password in users.items():
            res = client.post(
                "/v1/login",
                json={"username": user, "password": password},
            )
            res.raise_for_status()
            assert res.json().get("user") == users_ids[user]
            users_tokens[user] = res.json().get("access_token")

        # studies creation
        studies_ids_mapping = {}

        # create variant studies for user_1 and user_2 that are part of some groups
        # studies that have owner and groups
        for study, study_info in {
            "study_1": {"owner": "user_1", "groups": ["group_1"]},
            "study_2": {"owner": "user_1", "groups": ["group_2"]},
            "study_4": {"owner": "user_2", "groups": ["group_1"]},
            "study_5": {"owner": "user_2", "groups": ["group_2"]},
            "study_7": {"owner": "user_1", "groups": ["group_1", "group_2"]},
            "study_8": {"owner": "user_2", "groups": ["group_1", "group_2"]},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": f"dummy_{study[6:]}"},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            res = client.post(
                f"{STUDIES_URL}/{study_id}/variants",
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            owner_id = users_ids[study_info.get("owner")]
            res = client.put(
                f"{STUDIES_URL}/{study_id}/owner/{owner_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()
            for group in study_info.get("groups"):
                group_id = groups_ids[group]
                res = client.put(
                    f"{STUDIES_URL}/{study_id}/groups/{group_id}",
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                )
                assert res.status_code == 200, res.json()
        # studies that have owner but no groups
        for study, study_info in {
            "study_X10": {"owner": "user_1"},
            "study_X11": {"owner": "user_2"},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": f"dummy_{study[6:]}"},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            res = client.post(
                f"{STUDIES_URL}/{study_id}/variants",
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            owner_id = users_ids[study_info.get("owner")]
            res = client.put(
                f"{STUDIES_URL}/{study_id}/owner/{owner_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()
        # studies that have groups but no owner
        for study, study_info in {
            "study_3": {"groups": ["group_1"]},
            "study_6": {"groups": ["group_2"]},
            "study_9": {"groups": ["group_1", "group_2"]},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": f"dummy_{study[6:]}"},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            res = client.post(
                f"{STUDIES_URL}/{study_id}/variants",
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            for group in study_info.get("groups"):
                group_id = groups_ids[group]
                res = client.put(
                    f"{STUDIES_URL}/{study_id}/groups/{group_id}",
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                )
                assert res.status_code == 200, res.json()

        # create variant studies with neither owner nor groups
        for study, study_info in {
            "study_X12": {"public_mode": None},
            "study_X13": {"public_mode": PublicMode.READ.value},
            "study_X14": {"public_mode": PublicMode.EDIT.value},
            "study_X15": {"public_mode": PublicMode.EXECUTE.value},
            "study_X16": {"public_mode": PublicMode.FULL.value},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": f"dummy_{study[6:]}"},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            res = client.post(
                f"{STUDIES_URL}/{study_id}/variants",
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            public_mode = study_info.get("public_mode")
            if public_mode:
                res = client.put(
                    f"{STUDIES_URL}/{study_id}/public_mode/{public_mode}",
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                )
                assert res.status_code == 200, res.json()

        # create raw studies for user_1 and user_2 that are part of some groups
        # studies that have owner and groups
        for study, study_info in {
            "study_X17": {"owner": "user_1", "groups": ["group_1"]},
            "study_X18": {"owner": "user_1", "groups": ["group_2"]},
            "study_X20": {"owner": "user_2", "groups": ["group_1"]},
            "study_X21": {"owner": "user_2", "groups": ["group_2"]},
            "study_X23": {"owner": "user_1", "groups": ["group_1", "group_2"]},
            "study_X24": {"owner": "user_2", "groups": ["group_1", "group_2"]},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            owner = users_ids[study_info.get("owner")]
            res = client.put(
                f"{STUDIES_URL}/{study_id}/owner/{owner}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()
            for group in study_info.get("groups"):
                group_id = groups_ids[group]
                res = client.put(
                    f"{STUDIES_URL}/{study_id}/groups/{group_id}",
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                )
                assert res.status_code == 200, res.json()
        # studies that have owner but no groups
        for study, study_info in {
            "study_X26": {"owner": "user_1"},
            "study_X27": {"owner": "user_2"},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            owner_id = users_ids[study_info.get("owner")]
            res = client.put(
                f"{STUDIES_URL}/{study_id}/owner/{owner_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()
        # studies that have groups but no owner
        for study, study_info in {
            "study_X19": {"groups": ["group_1"]},
            "study_X22": {"groups": ["group_2"]},
            "study_X25": {"groups": ["group_1", "group_2"]},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            for group in study_info.get("groups"):
                group_id = groups_ids[group]
                res = client.put(
                    f"{STUDIES_URL}/{study_id}/groups/{group_id}",
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                )
                assert res.status_code == 200, res.json()

        # create raw studies with neither owner nor groups
        for study, study_info in {
            "study_X28": {"public_mode": None},
            "study_X29": {"public_mode": PublicMode.READ.value},
            "study_X30": {"public_mode": PublicMode.EDIT.value},
            "study_X31": {"public_mode": PublicMode.EXECUTE.value},
            "study_X32": {"public_mode": PublicMode.FULL.value},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            public_mode = study_info.get("public_mode")
            if public_mode:
                res = client.put(
                    f"{STUDIES_URL}/{study_id}/public_mode/{public_mode}",
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                )
                assert res.status_code == 200, res.json()

        # create studies for user_3 that is not part of any group
        # variant studies
        for study, study_info in {
            "study_X33": {"groups": ["group_1"]},
            "study_X35": {"groups": []},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": f"dummy_{study[6:]}"},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            res = client.post(
                f"{STUDIES_URL}/{study_id}/variants",
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            owner_id = users_ids["user_3"]
            res = client.put(
                f"{STUDIES_URL}/{study_id}/owner/{owner_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()
            for group in study_info.get("groups", []):
                group_id = groups_ids[group]
                res = client.put(
                    f"{STUDIES_URL}/{study_id}/groups/{group_id}",
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                )
                assert res.status_code == 200, res.json()
        # raw studies
        for study, study_info in {
            "study_X34": {"groups": ["group_2"]},
            "study_X36": {"groups": []},
        }.items():
            res = client.post(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {admin_access_token}"},
                params={"name": study},
            )
            assert res.status_code in CREATE_STATUS_CODES, res.json()
            study_id = res.json()
            studies_ids_mapping[study] = study_id
            owner_id = users_ids["user_3"]
            res = client.put(
                f"{STUDIES_URL}/{study_id}/owner/{owner_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code == 200, res.json()
            for group in study_info.get("groups"):
                group_id = groups_ids[group]
                res = client.put(
                    f"{STUDIES_URL}/{study_id}/groups/{group_id}",
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                )
                assert res.status_code == 200, res.json()

        # create studies for group_3 that has no user
        res = client.post(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "dummy_37"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        study_id = res.json()
        res = client.post(
            f"{STUDIES_URL}/{study_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "study_X37"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        study_id = res.json()
        group_3_id = groups_ids["group_3"]
        res = client.put(
            f"{STUDIES_URL}/{study_id}/groups/{group_3_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert res.status_code == 200, res.json()
        studies_ids_mapping["study_X37"] = study_id
        res = client.post(
            STUDIES_URL,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "study_X38"},
        )
        assert res.status_code in CREATE_STATUS_CODES, res.json()
        study_id = res.json()
        res = client.put(
            f"{STUDIES_URL}/{study_id}/groups/{group_3_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert res.status_code == 200, res.json()
        studies_ids_mapping["study_X38"] = study_id

        # verify the studies creation was done correctly and that admin has access to all studies
        all_studies = set(studies_ids_mapping.values())
        studies_target_info = {
            "study_1": {
                "type": "variantstudy",
                "owner": "user_1",
                "groups": ["group_1"],
                "public_mode": PublicMode.NONE,
            },
            "study_2": {
                "type": "variantstudy",
                "owner": "user_1",
                "groups": ["group_2"],
                "public_mode": PublicMode.NONE,
            },
            "study_3": {"type": "variantstudy", "owner": None, "groups": ["group_1"], "public_mode": PublicMode.NONE},
            "study_4": {
                "type": "variantstudy",
                "owner": "user_2",
                "groups": ["group_1"],
                "public_mode": PublicMode.NONE,
            },
            "study_5": {
                "type": "variantstudy",
                "owner": "user_2",
                "groups": ["group_2"],
                "public_mode": PublicMode.NONE,
            },
            "study_6": {"type": "variantstudy", "owner": None, "groups": ["group_2"], "public_mode": PublicMode.NONE},
            "study_7": {
                "type": "variantstudy",
                "owner": "user_1",
                "groups": ["group_1", "group_2"],
                "public_mode": PublicMode.NONE,
            },
            "study_8": {
                "type": "variantstudy",
                "owner": "user_2",
                "groups": ["group_1", "group_2"],
                "public_mode": PublicMode.NONE,
            },
            "study_9": {
                "type": "variantstudy",
                "owner": None,
                "groups": ["group_1", "group_2"],
                "public_mode": PublicMode.NONE,
            },
            "study_X10": {"type": "variantstudy", "owner": "user_1", "groups": None, "public_mode": PublicMode.NONE},
            "study_X11": {"type": "variantstudy", "owner": "user_2", "groups": None, "public_mode": PublicMode.NONE},
            "study_X12": {"type": "variantstudy", "owner": None, "groups": None, "public_mode": PublicMode.NONE},
            "study_X13": {"type": "variantstudy", "owner": None, "groups": None, "public_mode": PublicMode.READ},
            "study_X14": {"type": "variantstudy", "owner": None, "groups": None, "public_mode": PublicMode.EDIT},
            "study_X15": {"type": "variantstudy", "owner": None, "groups": None, "public_mode": PublicMode.EXECUTE},
            "study_X16": {"type": "variantstudy", "owner": None, "groups": None, "public_mode": PublicMode.FULL},
            "study_X17": {"type": "rawstudy", "owner": "user_1", "groups": ["group_1"], "public_mode": PublicMode.NONE},
            "study_X18": {"type": "rawstudy", "owner": "user_1", "groups": ["group_2"], "public_mode": PublicMode.NONE},
            "study_X19": {"type": "rawstudy", "owner": None, "groups": ["group_1"], "public_mode": PublicMode.NONE},
            "study_X20": {"type": "rawstudy", "owner": "user_2", "groups": ["group_1"], "public_mode": PublicMode.NONE},
            "study_X21": {"type": "rawstudy", "owner": "user_2", "groups": ["group_2"], "public_mode": PublicMode.NONE},
            "study_X22": {"type": "rawstudy", "owner": None, "groups": ["group_2"], "public_mode": PublicMode.NONE},
            "study_X23": {
                "type": "rawstudy",
                "owner": "user_1",
                "groups": ["group_1", "group_2"],
                "public_mode": PublicMode.NONE,
            },
            "study_X24": {
                "type": "rawstudy",
                "owner": "user_2",
                "groups": ["group_1", "group_2"],
                "public_mode": PublicMode.NONE,
            },
            "study_X25": {
                "type": "rawstudy",
                "owner": None,
                "groups": ["group_1", "group_2"],
                "public_mode": PublicMode.NONE,
            },
            "study_X26": {"type": "rawstudy", "owner": "user_1", "groups": None, "public_mode": PublicMode.NONE},
            "study_X27": {"type": "rawstudy", "owner": "user_2", "groups": None, "public_mode": PublicMode.NONE},
            "study_X28": {"type": "rawstudy", "owner": None, "groups": None, "public_mode": PublicMode.NONE},
            "study_X29": {"type": "rawstudy", "owner": None, "groups": None, "public_mode": PublicMode.READ},
            "study_X30": {"type": "rawstudy", "owner": None, "groups": None, "public_mode": PublicMode.EDIT},
            "study_X31": {"type": "rawstudy", "owner": None, "groups": None, "public_mode": PublicMode.EXECUTE},
            "study_X32": {"type": "rawstudy", "owner": None, "groups": None, "public_mode": PublicMode.FULL},
            "study_X33": {
                "type": "variantstudy",
                "owner": "user_3",
                "groups": ["group_1"],
                "public_mode": PublicMode.NONE,
            },
            "study_X34": {"type": "rawstudy", "owner": "user_3", "groups": ["group_2"], "public_mode": PublicMode.NONE},
            "study_X35": {"type": "variantstudy", "owner": "user_3", "groups": None, "public_mode": PublicMode.NONE},
            "study_X36": {"type": "rawstudy", "owner": "user_3", "groups": None, "public_mode": PublicMode.NONE},
            "study_X37": {"type": "variantstudy", "owner": None, "groups": ["group_3"], "public_mode": PublicMode.NONE},
            "study_X38": {"type": "rawstudy", "owner": None, "groups": ["group_3"], "public_mode": PublicMode.NONE},
        }
        res = client.get(STUDIES_URL, headers={"Authorization": f"Bearer {admin_access_token}"})
        assert res.status_code == LIST_STATUS_CODE, res.json()
        study_map = res.json()
        assert len(all_studies) == 38
        assert not all_studies.difference(study_map)
        for study, study_info in studies_target_info.items():
            study_id = studies_ids_mapping[study]
            study_data = study_map[study_id]
            assert study_data.get("type") == study_info.get("type")
            if study_data.get("owner") and study_info.get("owner"):
                assert study_data["owner"]["name"] == study_info.get("owner")
                assert study_data["owner"]["id"] == users_ids[study_info.get("owner")]
            else:
                assert not study_info.get("owner")
                assert study_data["owner"]["name"] == "admin"
            if study_data.get("groups"):
                expected_groups = set(study_info.get("groups"))
                assert all(
                    (group["name"] in expected_groups) and groups_ids[group["name"]] == group["id"]
                    for group in study_data["groups"]
                )
            else:
                assert not study_info.get("groups")
            assert study_data["public_mode"] == study_info.get("public_mode")

        ##########################
        # 2. Tests
        ##########################

        # user_1 access
        # fmt: off
        requests_params_expected_studies = [
            ([], {"1", "2", "5", "6", "7", "8", "9", "10", "13", "14", "15", "16", "17",
                  "18", "21", "22", "23", "24", "25", "26", "29", "30", "31", "32", "34"}),
            (["1"], {"1", "7", "8", "9", "17", "23", "24", "25"}),
            (["2"], {"2", "5", "6", "7", "8", "9", "18", "21", "22", "23", "24", "25", "34"}),
            (["3"], set()),
            (["1", "2"], {"1", "2", "5", "6", "7", "8", "9", "17", "18", "21", "22", "23", "24", "25", "34"}),
            (["1", "3"], {"1", "7", "8", "9", "17", "23", "24", "25"}),
            (["2", "3"], {"2", "5", "6", "7", "8", "9", "18", "21", "22", "23", "24", "25", "34"}),
            (
                ["1", "2", "3"],
                {"1", "2", "5", "6", "7", "8", "9", "17", "18", "21", "22", "23", "24", "25", "34"},
            ),
        ]
        # fmt: on
        for request_groups_numbers, expected_studies_numbers in requests_params_expected_studies:
            request_groups_ids = [groups_ids[f"group_{group_number}"] for group_number in request_groups_numbers]
            expected_studies = [
                studies_ids_mapping[f"study_{(study_number if int(study_number) <= 9 else 'X' + study_number)}"]
                for study_number in expected_studies_numbers
            ]
            res = client.get(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {users_tokens['user_1']}"},
                params={"groups": ",".join(request_groups_ids)} if request_groups_ids else {},
            )
            assert res.status_code == LIST_STATUS_CODE, res.json()
            study_map = res.json()
            assert not set(expected_studies).difference(set(study_map))
            assert not all_studies.difference(expected_studies).intersection(set(study_map))
            # test pagination
            res = client.get(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {users_tokens['user_1']}"},
                params=(
                    {"groups": ",".join(request_groups_ids), "pageNb": 1, "pageSize": 2}
                    if request_groups_ids
                    else {"pageNb": 1, "pageSize": 2}
                ),
            )
            assert res.status_code == LIST_STATUS_CODE, res.json()
            assert len(res.json()) == max(0, min(2, len(expected_studies) - 2))
            # assert list(res.json()) == expected_studies[2:4]

        # user_2 access
        # fmt: off
        requests_params_expected_studies = [
            ([], {"1", "3", "4", "5", "7", "8", "9", "11", "13", "14", "15", "16", "17",
                  "19", "20", "21", "23", "24", "25", "27", "29", "30", "31", "32", "33"}),
            (["1"], {"1", "3", "4", "7", "8", "9", "17", "19", "20", "23", "24", "25", "33"}),
            (["2"], {"5", "7", "8", "9", "21", "23", "24", "25"}),
            (["3"], set()),
            (["1", "2"], {"1", "3", "4", "5", "7", "8", "9", "17", "19", "20", "21", "23", "24", "25", "33"}),
            (["1", "3"], {"1", "3", "4", "7", "8", "9", "17", "19", "20", "23", "24", "25", "33"}),
            (["2", "3"], {"5", "7", "8", "9", "21", "23", "24", "25"}),
            (
                ["1", "2", "3"],
                {"1", "3", "4", "5", "7", "8", "9", "17", "19", "20", "21", "23", "24", "25", "33"},
            ),
        ]
        # fmt: on
        for request_groups_numbers, expected_studies_numbers in requests_params_expected_studies:
            request_groups_ids = [groups_ids[f"group_{group_number}"] for group_number in request_groups_numbers]
            expected_studies = {
                studies_ids_mapping[f"study_{(study_number if int(study_number) <= 9 else 'X' + study_number)}"]
                for study_number in expected_studies_numbers
            }
            res = client.get(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {users_tokens['user_2']}"},
                params={"groups": ",".join(request_groups_ids)} if request_groups_ids else {},
            )
            assert res.status_code == LIST_STATUS_CODE, res.json()
            study_map = res.json()
            assert not expected_studies.difference(set(study_map))
            assert not all_studies.difference(expected_studies).intersection(set(study_map))

        # user_3 access
        requests_params_expected_studies = [
            ([], {"13", "14", "15", "16", "29", "30", "31", "32", "33", "34", "35", "36"}),
            (["1"], {"33"}),
            (["2"], {"34"}),
            (["3"], set()),
            (["1", "2"], {"33", "34"}),
            (["1", "3"], {"33"}),
            (["2", "3"], {"34"}),
            (["1", "2", "3"], {"33", "34"}),
        ]
        for request_groups_numbers, expected_studies_numbers in requests_params_expected_studies:
            request_groups_ids = [groups_ids[f"group_{group_number}"] for group_number in request_groups_numbers]
            expected_studies = {
                studies_ids_mapping[f"study_{(study_number if int(study_number) <= 9 else 'X' + study_number)}"]
                for study_number in expected_studies_numbers
            }
            res = client.get(
                STUDIES_URL,
                headers={"Authorization": f"Bearer {users_tokens['user_3']}"},
                params={"groups": ",".join(request_groups_ids)} if request_groups_ids else {},
            )
            assert res.status_code == LIST_STATUS_CODE, res.json()
            study_map = res.json()
            assert not expected_studies.difference(set(study_map))
            assert not all_studies.difference(expected_studies).intersection(set(study_map))

    def test_get_studies__invalid_parameters(
        self,
        client: TestClient,
        user_access_token: str,
    ) -> None:
        headers = {"Authorization": f"Bearer {user_access_token}"}

        # Invalid `sortBy` parameter
        res = client.get(STUDIES_URL, headers=headers, params={"sortBy": "invalid"})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search("Input should be", description), f"{description=}"

        # Invalid `pageNb` parameter (negative integer)
        res = client.get(STUDIES_URL, headers=headers, params={"pageNb": -1})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"greater than or equal to 0", description), f"{description=}"

        # Invalid `pageNb` parameter (not an integer)
        res = client.get(STUDIES_URL, headers=headers, params={"pageNb": "invalid"})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"should be a valid integer", description), f"{description=}"

        # Invalid `pageSize` parameter (negative integer)
        res = client.get(STUDIES_URL, headers=headers, params={"pageSize": -1})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"greater than or equal to 0", description), f"{description=}"

        # Invalid `pageSize` parameter (not an integer)
        res = client.get(STUDIES_URL, headers=headers, params={"pageSize": "invalid"})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"should be a valid integer", description), f"{description=}"

        # Invalid `managed` parameter (not a boolean)
        res = client.get(STUDIES_URL, headers=headers, params={"managed": "invalid"})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"should be a valid boolean", description), f"{description=}"

        # Invalid `archived` parameter (not a boolean)
        res = client.get(STUDIES_URL, headers=headers, params={"archived": "invalid"})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"should be a valid boolean", description), f"{description=}"

        # Invalid `variant` parameter (not a boolean)
        res = client.get(STUDIES_URL, headers=headers, params={"variant": "invalid"})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"should be a valid boolean", description), f"{description=}"

        # Invalid `versions` parameter (not a list of integers)
        res = client.get(STUDIES_URL, headers=headers, params={"versions": "invalid"})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"String should match pattern", description), f"{description=}"

        # Invalid `users` parameter (not a list of integers)
        res = client.get(STUDIES_URL, headers=headers, params={"users": "invalid"})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"String should match pattern", description), f"{description=}"

        # Invalid `exists` parameter (not a boolean)
        res = client.get(STUDIES_URL, headers=headers, params={"exists": "invalid"})
        assert res.status_code == INVALID_PARAMS_STATUS_CODE, res.json()
        description = res.json()["description"]
        assert re.search(r"should be a valid boolean", description), f"{description=}"


def test_studies_counting(client: TestClient, admin_access_token: str, user_access_token: str) -> None:
    # test admin and non admin user studies count requests
    for access_token in [admin_access_token, user_access_token]:
        res = client.get(STUDIES_URL, headers={"Authorization": f"Bearer {access_token}"})
        assert res.status_code == 200, res.json()
        expected_studies_count = len(res.json())
        res = client.get(STUDIES_URL + "/count", headers={"Authorization": f"Bearer {access_token}"})
        assert res.status_code == 200, res.json()
        assert res.json() == expected_studies_count
