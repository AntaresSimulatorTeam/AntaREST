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
        assert cluster["name"] == lowered_name
        assert cluster["group"] == lowered_grp

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
