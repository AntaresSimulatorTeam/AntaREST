import io
import typing as t

import pandas as pd
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


class PreparerProxy:
    """
    Proxy to prepare the test environment for integration tests

    Attributes:
        client: The client to be used for requests.
        user_access_token: The access token of the user.
        headers: The headers to be used for requests.
    """

    def __init__(self, client: TestClient, user_access_token: str):
        """
        Initialize the proxy.

        Args:
            client: The client to be used for requests.
            user_access_token: The access token of the user.
        """
        self.client = client
        self.user_access_token = user_access_token
        self.headers = {"Authorization": f"Bearer {user_access_token}"}

    def create_study(self, name: str, *, version: int = 870) -> str:
        """
        Create a new study in the managed workspace.

        Args:
            name: The name of the study.
            version: The version of the study. Defaults to 870.

        Returns:
            The ID of the created study.
        """
        res = self.client.post(
            "/v1/studies",
            params={"name": name, "version": version},  # type: ignore
            headers=self.headers,
        )
        assert res.status_code == 201, res.json()
        return t.cast(str, res.json())

    def copy_study_and_upgrade(self, ref_study_id: str, target_version: int) -> str:
        """
        Copy a study in the managed workspace and upgrade it to a specific version.

        Args:
            ref_study_id: The ID of the study to copy.
            target_version: The version to upgrade the copied study to. Defaults to 820.

        Returns:
            The ID of the copied and upgraded study.
        """
        # Prepare a managed study to test specific matrices for version 8.2
        res = self.client.post(
            f"/v1/studies/{ref_study_id}/copy",
            params={"dest": "copied-820", "use_task": False},  # type: ignore
            headers=self.headers,
        )
        res.raise_for_status()
        study_id = t.cast(str, res.json())

        res = self.client.put(
            f"/v1/studies/{study_id}/upgrade",
            params={"target_version": target_version},
            headers=self.headers,
        )
        res.raise_for_status()
        task_id = res.json()
        assert task_id

        task = wait_task_completion(self.client, self.user_access_token, task_id, timeout=20)
        assert task.status == TaskStatus.COMPLETED
        return study_id

    def upload_matrix(self, study_id: str, matrix_path: str, df: pd.DataFrame) -> None:
        """
        Upload a matrix to the study.

        Args:
            study_id: The ID of the study to upload the matrix to.
            matrix_path: The path to the matrix in the study.
            df: The data to upload.
        """
        tsv = io.BytesIO()
        df.to_csv(tsv, sep="\t", index=False, header=False)
        tsv.seek(0)
        # noinspection SpellCheckingInspection
        res = self.client.put(
            f"/v1/studies/{study_id}/raw",
            params={"path": matrix_path, "create_missing": True},  # type: ignore
            headers=self.headers,
            files={"file": tsv, "create_missing": "true"},  # type: ignore
        )
        res.raise_for_status()

    def download_matrix(self, study_id: str, matrix_path: str) -> pd.DataFrame:
        """
        Download a matrix from the study.

        Args:
            study_id: The ID of the study to download the matrix from.
            matrix_path: The path to the matrix in the study.

        Returns:
            pd.DataFrame: The downloaded data.
        """
        res = self.client.get(
            f"/v1/studies/{study_id}/raw",
            params={"depth": 1, "formatted": True, "path": matrix_path},  # type: ignore
            headers=self.headers,
        )
        res.raise_for_status()
        return pd.DataFrame(**res.json())

    def create_variant(self, parent_id: str, *, name: str) -> str:
        """
        Create a variant of a study.

        Args:
            parent_id: The ID of the parent study.
            name: The name of the variant.

        Returns:
            str: The ID of the created variant.
        """
        res = self.client.post(
            f"/v1/studies/{parent_id}/variants",
            headers=self.headers,
            params={"name": name},
        )
        res.raise_for_status()
        variant_id = t.cast(str, res.json())
        return variant_id

    def generate_snapshot(self, variant_id: str, denormalize: bool = False, from_scratch: bool = True) -> None:
        """
        Generate a snapshot for a variant.

        Args:
            variant_id: The ID of the variant study.
            denormalize: Whether to denormalize the snapshot (replace the matrix links by the actual data).
            from_scratch: Whether to generate the snapshot from scratch (recompute the data).
        """
        # Generate a snapshot for the variant
        res = self.client.put(
            f"/v1/studies/{variant_id}/generate",
            headers=self.headers,
            params={"denormalize": denormalize, "from_scratch": from_scratch},
        )
        res.raise_for_status()
        task_id = res.json()
        assert task_id

        task = wait_task_completion(self.client, self.user_access_token, task_id, timeout=20)
        assert task.status == TaskStatus.COMPLETED

    def create_area(self, study_id: str, *, name: str, country: str = "FR") -> str:
        """
        Create an area in a study.

        Args:
            study_id: The ID of the parent study.
            name: Name of the area.
            country: Country of the area.

        Returns:
            The ID of the created area.
        """
        res = self.client.post(
            f"/v1/studies/{study_id}/areas",
            headers=self.headers,
            json={"name": name, "type": "AREA", "metadata": {"country": country}},
        )
        res.raise_for_status()
        area_id = t.cast(str, res.json()["id"])
        return area_id

    def update_general_data(self, study_id: str, **data: t.Any) -> None:
        """
        Update the general data of a study.

        Args:
            study_id: The ID of the study.
            **data: The data to update.
        """
        res = self.client.put(
            f"/v1/studies/{study_id}/config/general/form",
            json=data,
            headers=self.headers,
        )
        res.raise_for_status()
