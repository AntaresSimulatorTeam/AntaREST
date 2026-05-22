# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from starlette.testclient import TestClient


def create_minimal_study(client: TestClient, study_id: str) -> None:
    """
    Create a minimal study with basic areas, links, thermal clusters, and a binding constraint.
    """
    for name in ["fr", "be", "ch"]:
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": name})
        res.raise_for_status()

    for name in ["be", "ch"]:
        res = client.post(f"/v1/studies/{study_id}/links", json={"area1": "fr", "area2": name})
        res.raise_for_status()

    for thermal_name in ["lignite plant", "nuclear cluster"]:
        res = client.post(f"/v1/studies/{study_id}/areas/fr/clusters/thermal", json={"name": thermal_name})
        res.raise_for_status()

    res = client.post(
        f"/v1/studies/{study_id}/bindingconstraints",
        json={"name": "Constraint1", "terms": [{"weight": 4, "data": {"area1": "be", "area2": "ch"}}]},
    )
    res.raise_for_status()
