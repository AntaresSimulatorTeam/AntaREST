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
import zipfile
from pathlib import Path
from unittest.mock import ANY

from starlette.testclient import TestClient

from antarest.core.serde.ini_reader import read_ini
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, initialize_thermal_cluster
from antarest.study.model import STUDY_VERSION_9_3
from tests.test_helpers.download import download_to_file


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


def check_minimal_study_integrity(client: TestClient, study_id: str) -> None:
    # Areas + Thermals
    res = client.get(f"/v1/studies/{study_id}/areas")
    result = res.json()
    sorted_result = sorted(result, key=lambda a: a["id"])  # For testing purposes

    default_thermal = ThermalCluster(name="fake")  # Just to have a readable test
    initialize_thermal_cluster(default_thermal, STUDY_VERSION_9_3)
    default_thermal_params = default_thermal.model_dump(mode="json", exclude={"name", "id"}, by_alias=True)

    assert sorted_result == [
        {"id": "be", "name": "be", "thermals": [], "type": "AREA"},
        {"id": "ch", "name": "ch", "thermals": [], "type": "AREA"},
        {
            "id": "fr",
            "name": "fr",
            "thermals": [
                {"id": "lignite plant", "name": "lignite plant", **default_thermal_params},
                {"id": "nuclear cluster", "name": "nuclear cluster", **default_thermal_params},
            ],
            "type": "AREA",
        },
    ]

    # Links
    res = client.get(f"/v1/studies/{study_id}/links")

    sorted_result = sorted(res.json(), key=lambda a: a["area1"])  # For testing purposes
    default_link_params = Link(area1="a", area2="b").model_dump(mode="json", exclude={"area1", "area2"}, by_alias=True)

    assert sorted_result == [
        {"area1": "be", "area2": "fr", **default_link_params},
        {"area1": "ch", "area2": "fr", **default_link_params},
    ]

    # Binding constraints
    res = client.get(f"/v1/studies/{study_id}/bindingconstraints")
    assert res.json() == [
        {
            "comments": "",
            "enabled": True,
            "filterSynthesis": "",
            "filterYearByYear": "",
            "group": "default",
            "id": "constraint1",
            "name": "Constraint1",
            "operator": "equal",
            "terms": [{"data": {"area1": "be", "area2": "ch"}, "offset": None, "weight": 4.0}],
            "timeStep": "hourly",
        }
    ]


def check_exported_study_integrity(client: TestClient, export_path: Path, download_id: str) -> None:
    zip_path = export_path / "export.zip"
    download_to_file(client, download_id, export_path / zip_path)
    assert zip_path.exists()

    study_path = export_path / "exported_study"
    with zipfile.ZipFile(zip_path) as zip_output:
        zip_output.extractall(path=study_path)

    assert study_path.exists()

    # Check the path content to be sure the study was correctly exported
    study_antares = read_ini(study_path / "study.antares")
    assert study_antares == {
        "antares": {
            "version": 9.3,
            "caption": "MyStudy",
            "author": "George",
            "editor": "George",
            "created": ANY,
            "lastsave": ANY,
        }
    }

    # Areas
    assert sorted([f.name for f in (study_path / "input" / "areas").iterdir()]) == [
        "be",
        "ch",
        "fr",
        "list.txt",
        "sets.ini",
    ]
    # Links
    assert sorted([f.name for f in (study_path / "input" / "links").iterdir()]) == ["be", "ch", "fr"]
    # Thermals
    ini_path = study_path / "input" / "thermal" / "clusters" / "fr" / "list.ini"
    ini_content = read_ini(ini_path)
    assert sorted(ini_content) == ["lignite plant", "nuclear cluster"]
    # Binding constraints
    ini_path = study_path / "input" / "bindingconstraints" / "bindingconstraints.ini"
    ini_content = read_ini(ini_path)
    assert ini_content == {
        "0": {
            "id": "constraint1",
            "name": "Constraint1",
            "enabled": True,
            "type": "hourly",
            "operator": "equal",
            "comments": "",
            "filter-year-by-year": "",
            "filter-synthesis": "",
            "group": "default",
            "be%ch": 4.0,
        }
    }
