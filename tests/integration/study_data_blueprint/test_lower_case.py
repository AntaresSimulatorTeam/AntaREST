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

import copy
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from tests.integration.prepare_proxy import PreparerProxy
from tests.integration.utils import wait_task_completion


class TestLowerCase:
    """
    Checks the app read and writes several fields in lower-case and handle all cases correctly
    """

    @pytest.mark.parametrize("cluster_type", ["thermal", "renewables", "st-storage"])
    def test_clusters(self, client: TestClient, user_access_token: str, tmp_path: Path, cluster_type: str) -> None:
        # Study preparation
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        study_path = tmp_path / "internal_workspace" / study_id
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]

        # Creates the cluster
        if cluster_type == "thermal":
            cluster_grp = "Nuclear"
            url = "clusters/thermal"
        elif cluster_type == "renewables":
            cluster_grp = "Solar Thermal"
            url = "clusters/renewable"
        else:
            cluster_grp = "Battery"
            url = "storages"
        cluster_name = "Cluster 1"
        lowered_name = cluster_name.lower()
        lowered_grp = cluster_grp.lower()
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area1_id}/{url}", json={"name": cluster_name, "group": cluster_grp}
        )
        assert res.status_code == 200, res.json()

        # Asserts the fields are written in lower case inside the ini file
        ini_path = study_path / "input" / cluster_type / "clusters" / area1_id / "list.ini"
        ini_content = IniReader().read(ini_path)
        assert list(ini_content.keys()) == [lowered_name]
        assert ini_content[lowered_name]["group"] == lowered_grp

        # Rewrite the cluster name in MAJ to mimic legacy clusters
        new_content = copy.deepcopy(ini_content)
        new_content[cluster_name] = new_content.pop(lowered_name)
        new_content[cluster_name]["name"] = cluster_name
        new_content[cluster_name]["group"] = cluster_grp
        IniWriter().write(new_content, ini_path)

        # Asserts the GET still works and returns the name in lower case
        res = client.get(f"/v1/studies/{study_id}/areas/{area1_id}/{url}/{cluster_name}")
        cluster = res.json()
        assert cluster["name"] == cluster_name
        assert cluster["group"] == lowered_grp

        # Also checks the GET /raw endpoint
        res = client.get(f"/v1/studies/{study_id}/raw?path=input/{cluster_type}/clusters/{area1_id}/list")
        cluster_list = res.json()
        assert list(cluster_list.keys()) == [lowered_name]
        assert cluster_list[lowered_name]["name"] == cluster_name
        assert cluster_list[lowered_name]["group"] == lowered_grp

        # Try to update a property
        if cluster_type == "st-storage":
            params = {"efficiency": 0.8}
        else:
            params = {"nominalCapacity": 2}
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area1_id}/{url}/{cluster_name}", json={"name": cluster_name, **params}
        )
        assert res.status_code == 200, res.json()

        # We shouldn't create a 2nd cluster, but rather update the first one
        res = client.get(f"/v1/studies/{study_id}/areas/{area1_id}/{url}")
        assert res.status_code == 200, res.json()
        clusters = res.json()
        assert len(clusters) == 1
        assert clusters[0][list(params.keys())[0]] == list(params.values())[0]

    def test_constraints(self, client: TestClient, user_access_token: str, tmp_path: Path) -> None:
        # Study preparation
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        study_id = preparer.create_variant(study_id, name="variant_1")
        study_path = tmp_path / "internal_workspace" / study_id / "snapshot"

        # Create the Binding Constraint with a group in MAJ
        bc_group = "Group 1"
        lowered_group = bc_group.lower()
        bc_1 = preparer.create_binding_constraint(study_id, name="bc_1", group=bc_group)
        assert bc_1["group"] == lowered_group

        # Generates the variant
        task_id = client.put(f"/v1/studies/{study_id}/generate")
        wait_task_completion(client, user_access_token, task_id.json())

        # Asserts the field is in lower case in the INI file
        ini_path = study_path / "input" / "bindingconstraints" / "bindingconstraints.ini"
        ini_content = IniReader().read(ini_path)
        assert ini_content["0"]["group"] == lowered_group

        # Writes the group in MAJ to mimic legacy constraint
        new_content = copy.deepcopy(ini_content)
        new_content["0"]["group"] = bc_group
        IniWriter().write(new_content, ini_path)

        # Asserts the group is read as lower case
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints")
        assert res.status_code == 200, res.json()
        bcs = res.json()
        assert len(bcs) == 1
        assert bcs[0]["group"] == lowered_group

        res = client.get(f"/v1/studies/{study_id}/raw?path=input/bindingconstraints/bindingconstraints")
        assert res.status_code == 200, res.json()
        bcs = res.json()
        assert len(bcs) == 1
        assert bcs["0"]["group"] == lowered_group
