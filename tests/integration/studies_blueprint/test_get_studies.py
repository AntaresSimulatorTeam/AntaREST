import io
import shutil
import typing as t
import zipfile
from operator import itemgetter
from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.core.model import PublicMode
from antarest.core.tasks.model import TaskStatus
from tests.integration.assets import ASSETS_DIR
from tests.integration.utils import wait_task_completion


class TestStudiesListing:
    """
    This class contains tests related to the following endpoints:

    - GET /v1/studies
    """

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
    ):
        """
        This test verifies that database is correctly initialized and then runs the filtering tests with different
        parameters
        """

        # database update to include non managed studies
        res = client.post(
            "/v1/watcher/_scan",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"path": "ext"},
        )
        res.raise_for_status()
        task_id = res.json()
        task = wait_task_completion(client, admin_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        accept_status_codes = {200, 201}
        studies_url = "/v1/studies"

        # retrieve a created non managed + to be deleted studies ids
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert res.status_code in accept_status_codes, res.json()
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
                f"{studies_url}/{non_managed_study}/public_mode/{no_access_code}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
                json={"name": "James Bond", "password": "0007"},
            )
            assert res.status_code in accept_status_codes, res.json()

        # create a user 'James Bond' with password '007'
        res = client.post(
            "/v1/users",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"name": "James Bond", "password": "0007"},
        )
        assert res.status_code in accept_status_codes, res.json()
        james_bond_id = res.json().get("id")

        # create a user 'John Doe' with password '0011'
        res = client.post(
            "/v1/users",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"name": "John Doe", "password": "0011"},
        )
        assert res.status_code in accept_status_codes, res.json()
        john_doe_id = res.json().get("id")

        # create a group 'Group X' with id 'groupX'
        res = client.post(
            "/v1/groups",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"name": "Group X", "id": "groupX"},
        )
        assert res.status_code in accept_status_codes, res.json()
        group_x_id = res.json().get("id")
        assert group_x_id == "groupX"

        # create a group 'Group Y' with id 'groupY'
        res = client.post(
            "/v1/groups",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            json={"name": "Group Y", "id": "groupY"},
        )
        assert res.status_code in accept_status_codes, res.json()
        group_y_id = res.json().get("id")
        assert group_y_id == "groupY"

        # login 'James Bond'
        res = client.post(
            "/v1/login",
            json={"username": "James Bond", "password": "0007"},
        )
        assert res.status_code in accept_status_codes, res.json()
        assert res.json().get("user") == james_bond_id
        james_bond_access_token = res.json().get("access_token")

        # login 'John Doe'
        res = client.post(
            "/v1/login",
            json={"username": "John Doe", "password": "0011"},
        )
        assert res.status_code in accept_status_codes, res.json()
        assert res.json().get("user") == john_doe_id
        john_doe_access_token = res.json().get("access_token")

        # create a bot user 'James Bond'
        res = client.post(
            "/v1/bots",
            headers={"Authorization": f"Bearer {james_bond_access_token}"},
            json={"name": "James Bond", "roles": []},
        )
        assert res.status_code in accept_status_codes, res.json()
        james_bond_bot_token = res.json()

        # create a raw study version 840
        res = client.post(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "raw-840", "version": "840"},
        )
        assert res.status_code in accept_status_codes, res.json()
        raw_840_id = res.json()

        # create a raw study version 850
        res = client.post(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "raw-850", "version": "850"},
        )
        assert res.status_code in accept_status_codes, res.json()
        raw_850_id = res.json()

        # create a raw study version 860
        res = client.post(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "raw-860", "version": "860"},
        )
        assert res.status_code in accept_status_codes, res.json()
        raw_860_id = res.json()

        # create a variant study version 840
        res = client.post(
            f"{studies_url}/{raw_840_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "variant-840", "version": "840"},
        )
        assert res.status_code in accept_status_codes, res.json()
        variant_840_id = res.json()

        # create a variant study version 850
        res = client.post(
            f"{studies_url}/{raw_850_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "variant-850", "version": "850"},
        )
        assert res.status_code in accept_status_codes, res.json()
        variant_850_id = res.json()

        # create a variant study version 860
        res = client.post(
            f"{studies_url}/{raw_860_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "variant-860", "version": "860"},
        )
        assert res.status_code in accept_status_codes, res.json()
        variant_860_id = res.json()

        # create a raw study version 840 to be archived
        res = client.post(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "archived-raw-840", "version": "840"},
        )
        assert res.status_code in accept_status_codes, res.json()
        archived_raw_840_id = res.json()

        # create a raw study version 850 to be archived
        res = client.post(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "archived-raw-850", "version": "850"},
        )
        assert res.status_code in accept_status_codes, res.json()
        archived_raw_850_id = res.json()

        # create a variant study version 840
        res = client.post(
            f"{studies_url}/{archived_raw_840_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "archived-variant-840", "version": "840"},
        )
        assert res.status_code in accept_status_codes, res.json()
        archived_variant_840_id = res.json()

        # create a variant study version 850 to be archived
        res = client.post(
            f"{studies_url}/{archived_raw_850_id}/variants",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "archived-variant-850", "version": "850"},
        )
        assert res.status_code in accept_status_codes, res.json()
        archived_variant_850_id = res.json()

        # create a raw study to be transfered in folder1
        zip_path = ASSETS_DIR / "STA-mini.zip"
        res = client.post(
            f"{studies_url}/_import",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            files={"study": io.BytesIO(zip_path.read_bytes())},
        )
        assert res.status_code in accept_status_codes, res.json()
        folder1_study_id = res.json()
        res = client.put(
            f"{studies_url}/{folder1_study_id}/move",
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"folder_dest": "folder1"},
        )
        assert res.status_code in accept_status_codes, res.json()

        # give permission to James Bond for some select studies
        james_bond_studies: set = {raw_840_id, variant_850_id, non_managed_860_id}
        for james_bond_study in james_bond_studies:
            res = client.put(
                f"{studies_url}/{james_bond_study}/owner/{james_bond_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code in accept_status_codes, res.json()

        # associate select studies to each group: groupX, groupY
        group_x_studies: set = {variant_850_id, raw_860_id}
        group_y_studies: set = {raw_850_id, raw_860_id}
        for group_x_study in group_x_studies:
            res = client.put(
                f"{studies_url}/{group_x_study}/groups/{group_x_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code in accept_status_codes, res.json()
        for group_y_study in group_y_studies:
            res = client.put(
                f"{studies_url}/{group_y_study}/groups/{group_y_id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code in accept_status_codes, res.json()

        # archive studies
        archive_studies = {archived_raw_840_id, archived_raw_850_id}
        for archive_study in archive_studies:
            res = client.put(
                f"{studies_url}/{archive_study}/archive",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            assert res.status_code in accept_status_codes, res.json()
            archiving_study_task_id = res.json()
            task = wait_task_completion(client, admin_access_token, archiving_study_task_id)
            assert task.status == TaskStatus.COMPLETED, task

        # the testing studies set
        all_studies: set = {
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
            archived_variant_840_id,
            archived_variant_850_id,
            folder1_study_id,
            to_be_deleted_id,
        }

        pm = itemgetter("public_mode")

        # tests (1) for user permission filtering
        # test 1.a for a user with no access permission
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {john_doe_access_token}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.intersection(study_map)
        assert all(map(lambda x: pm(x) in [PublicMode.READ, PublicMode.FULL], study_map.values()))
        # test 1.b for an admin user
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(study_map)
        # test 1.c for a user with access to select studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {james_bond_access_token}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not james_bond_studies.difference(study_map)
        assert all(
            map(
                lambda x: pm(x) in [PublicMode.READ, PublicMode.FULL],
                [e for k, e in study_map.items() if k not in james_bond_studies],
            )
        )
        # #TODO you need to update the permission for James Bond bot
        # test 1.d for a user bot with access to select studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {james_bond_bot_token}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        # #TODO add the correct test assertions
        # study_map: t.Dict[str, t.Any] = res.json()
        # assert not set(james_bond_studies).difference(study_map)
        # assert all(
        #     map(
        #         lambda x: pm(x) in [PublicMode.READ, PublicMode.FULL],
        #         [e for k, e in study_map.items() if k not in james_bond_studies],
        #     )
        # )

        # tests (2) for studies names filtering
        # test 2.a with matching studies
        res = client.get(studies_url, headers={"Authorization": f"Bearer {admin_access_token}"}, params={"name": "840"})
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert all(map(lambda x: "840" in x.get("name"), study_map.values())) and len(study_map) >= 5
        # test 2.b with no matching studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"name": "NON-SENSE-746846351469798465"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not study_map

        # tests (3) managed studies vs non managed
        # test 3.a managed
        managed_studies = all_studies.difference(non_managed_studies)
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"managed": True},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not managed_studies.difference(study_map)
        assert not all_studies.difference(managed_studies).intersection(study_map)
        # test 3.b non managed
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"managed": False},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(managed_studies).difference(study_map)
        assert not managed_studies.intersection(study_map)

        # tests (4) archived vs non archived
        # test 4.a archived studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"archived": True},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not archive_studies.difference(study_map)
        assert not all_studies.difference(archive_studies).intersection(study_map)
        # test 4.b non archived
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"archived": False},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(archive_studies).difference(study_map)
        assert not archive_studies.intersection(study_map)

        # tests (5) for filtering variant studies
        variant_studies = {
            variant_840_id,
            variant_850_id,
            variant_860_id,
            archived_variant_840_id,
            archived_variant_850_id,
        }
        # test 5.a get variant studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"variant": True},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not variant_studies.difference(study_map)
        assert not all_studies.difference(variant_studies).intersection(study_map)
        # test 5.b get raw studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"variant": False},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(variant_studies).difference(study_map)
        assert not variant_studies.intersection(study_map)

        # tests (6) for version filtering
        studies_version_850: set = {
            raw_850_id,
            non_managed_850_id,
            variant_850_id,
            archived_raw_850_id,
            archived_variant_850_id,
        }
        studies_version_860: set = {
            raw_860_id,
            non_managed_860_id,
            variant_860_id,
        }
        # test 6.a filter for one version: 860
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"versions": "860"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(studies_version_860).intersection(study_map)
        assert not studies_version_860.difference(study_map)
        # test 8.b filter for two versions: 850, 860
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"versions": "850,860"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(studies_version_850.union(studies_version_860)).intersection(study_map)
        assert not studies_version_850.union(studies_version_860).difference(study_map)

        # tests (7) for users filtering
        # test 7.a to get studies for one user: James Bond
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"users": f"{james_bond_id}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(james_bond_studies).intersection(study_map)
        assert not james_bond_studies.difference(study_map)
        # test 7.b to get studies for two users
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"users": f"{james_bond_id},{john_doe_id}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(james_bond_studies).intersection(study_map)
        assert not james_bond_studies.difference(study_map)

        # tests (8) for groups filtering
        # test 8.a filter for one group: groupX
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"groups": f"{group_x_id}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(group_x_studies).intersection(study_map)
        assert not group_x_studies.difference(study_map)
        # test 8.b filter for two groups: groupX, groupY
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"groups": f"{group_x_id},{group_y_id}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(group_x_studies.union(group_y_studies)).intersection(study_map)
        assert not group_x_studies.union(group_y_studies).difference(study_map)

        # TODO you need to add filtering through tags to the search engine
        # tests (9) for tags filtering
        # test 9.a filtering for one tag: decennial
        # test 9.b filtering for two tags: decennial,winter_transition

        # tests (10) for studies uuids sequence filtering
        # test 10.a filter for one uuid
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"studiesIds": f"{raw_840_id}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert {raw_840_id} == set(study_map)
        # test 10.b filter for two uuids
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"studiesIds": f"{raw_840_id},{raw_860_id}"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert {raw_840_id, raw_860_id} == set(study_map)

        # tests (11) studies filtering regarding existence on disk
        existing_studies = all_studies.difference({to_be_deleted_id})
        # test 11.a filter existing studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"exists": True},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not existing_studies.difference(study_map)
        assert not all_studies.difference(existing_studies).intersection(study_map)
        # test 11.b filter non-existing studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"exists": False},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not all_studies.difference(existing_studies).difference(study_map)
        assert not existing_studies.intersection(study_map)

        # tests (12) studies filtering with workspace
        ext_workspace_studies = non_managed_studies
        # test 12.a filter `ext` workspace studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"workspace": "ext"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not ext_workspace_studies.difference(study_map)
        assert not all_studies.difference(ext_workspace_studies).intersection(study_map)

        # tests (13) studies filtering with folder
        # test 13.a filter `folder1` studies
        res = client.get(
            studies_url,
            headers={"Authorization": f"Bearer {admin_access_token}"},
            params={"folder": "folder1"},
        )
        assert res.status_code in accept_status_codes, res.json()
        study_map: t.Dict[str, t.Any] = res.json()
        assert not {folder1_study_id}.difference(study_map)
        assert not all_studies.difference({folder1_study_id}).intersection(study_map)
