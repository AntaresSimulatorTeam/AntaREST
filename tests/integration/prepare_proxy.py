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
            params={"name": name, "version": version},
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

        task = wait_task_completion(self.client, self.user_access_token, task_id, base_timeout=20)
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
            params={"path": matrix_path},  # type: ignore
            headers=self.headers,
            files={"file": tsv},  # type: ignore
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

        task = wait_task_completion(self.client, self.user_access_token, task_id, base_timeout=20)
        assert task.status == TaskStatus.COMPLETED

    def create_area(self, study_id: str, *, name: str, country: str = "FR") -> t.Dict[str, t.Any]:
        """
        Create an area in a study.

        Args:
            study_id: The ID of the parent study.
            name: Name of the area.
            country: Country of the area.

        Returns:
            The area properties.
        """
        res = self.client.post(
            f"/v1/studies/{study_id}/areas",
            headers=self.headers,
            json={"name": name, "type": "AREA", "metadata": {"country": country}},
        )
        res.raise_for_status()
        properties = t.cast(t.Dict[str, t.Any], res.json())
        return properties

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

    def create_link(self, study_id: str, area1_id: str, area2_id: str) -> t.Dict[str, t.Any]:
        """
        Create a link between two areas in a study.

        Args:
            study_id: The ID of the study.
            area1_id: The ID of the first area.
            area2_id: The ID of the second area.

        Returns:
            The link properties.
        """
        # Create a link between the two areas
        res = self.client.post(
            f"/v1/studies/{study_id}/links",
            headers=self.headers,
            json={"area1": area1_id, "area2": area2_id},
        )
        assert res.status_code == 200, res.json()
        properties = t.cast(t.Dict[str, t.Any], res.json())
        properties["id"] = f"{area1_id}%{area2_id}"
        return properties

    def create_thermal(self, study_id: str, area1_id: str, *, name: str, **kwargs: t.Any) -> t.Dict[str, t.Any]:
        """
        Create a thermal cluster in an area.

        Args:
            study_id: The ID of the study.
            area1_id: The ID of the area.
            name: The name of the cluster.
            **kwargs: Additional cluster data.

        Returns:
            The cluster properties.
        """
        res = self.client.post(
            f"/v1/studies/{study_id}/areas/{area1_id}/clusters/thermal",
            headers=self.headers,
            json={"name": name, **kwargs},
        )
        res.raise_for_status()
        properties = t.cast(t.Dict[str, t.Any], res.json())
        return properties

    def get_thermals(self, study_id: str, area1_id: str) -> t.List[t.Dict[str, t.Any]]:
        """
        Get the thermal clusters of an area in a study.

        Args:
            study_id: The ID of the study.
            area1_id: The ID of the area.

        Returns:
            The list of cluster properties.
        """
        res = self.client.get(f"/v1/studies/{study_id}/areas/{area1_id}/clusters/thermal", headers=self.headers)
        res.raise_for_status()
        clusters_list = t.cast(t.List[t.Dict[str, t.Any]], res.json())
        return clusters_list

    def create_renewable(self, study_id: str, area1_id: str, *, name: str, **kwargs: t.Any) -> str:
        """
        Create a renewable cluster in an area.

        Args:
            study_id: The ID of the study.
            area1_id: The ID of the area.
            name: The name of the cluster.
            **kwargs: Additional cluster data.
        """
        res = self.client.post(
            f"/v1/studies/{study_id}/areas/{area1_id}/clusters/renewable",
            headers=self.headers,
            json={"name": name, **kwargs},
        )
        res.raise_for_status()
        cluster_id = t.cast(str, res.json()["id"])
        return cluster_id

    def get_renewables(self, study_id: str, area1_id: str) -> t.List[t.Dict[str, t.Any]]:
        """
        Get the renewable clusters of an area in a study.

        Args:
            study_id: The ID of the study.
            area1_id: The ID of the area.

        Returns:
            The list of cluster properties.
        """
        res = self.client.get(f"/v1/studies/{study_id}/areas/{area1_id}/clusters/renewable", headers=self.headers)
        res.raise_for_status()
        clusters_list = t.cast(t.List[t.Dict[str, t.Any]], res.json())
        return clusters_list

    def create_binding_constraint(self, study_id: str, *, name: str, **kwargs: t.Any) -> t.Dict[str, t.Any]:
        """
        Create a binding constraint in a study.

        Args:
            study_id: The ID of the study.
            name: The name of the constraint.
            **kwargs: Additional constraint data.

        Returns:
            The binding constraint properties.
        """
        res = self.client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            headers=self.headers,
            json={"name": name, **kwargs},
        )
        res.raise_for_status()
        properties = t.cast(t.Dict[str, t.Any], res.json())
        return properties

    def get_binding_constraints(self, study_id: str) -> t.List[t.Dict[str, t.Any]]:
        """
        Get the binding constraints of a study.

        Args:
            study_id: The ID of the study.

        Returns:
            The list of constraint properties.
        """
        res = self.client.get(f"/v1/studies/{study_id}/bindingconstraints", headers=self.headers)
        res.raise_for_status()
        binding_constraints_list = t.cast(t.List[t.Dict[str, t.Any]], res.json())
        return binding_constraints_list

    def drop_all_commands(self, variant_id: str) -> None:
        """
        Drop all commands of a variant.

        Args:
            variant_id: The ID of the variant.
        """
        res = self.client.delete(f"/v1/studies/{variant_id}/commands", headers=self.headers)
        res.raise_for_status()
