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
import textwrap
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.renewables.clusters import (
    ClusteredRenewableClusterConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.clusters.area.list import (
    InputSTStorageAreaList,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.cluster.area.list import (
    InputThermalClustersAreaList,
)


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "ini_node_cluster_class",
    [InputSTStorageAreaList, ClusteredRenewableClusterConfig, InputThermalClustersAreaList],
)
def test_group_is_parsed_to_lower_case(tmp_path: Path, ini_node_cluster_class):
    study_path = tmp_path / "study"
    study_path.mkdir()
    file_path = study_path / "test.ini"
    file_path.write_text(
        textwrap.dedent(
            """
            [Cluster 1]
            group = Gas
            """
        )
    )

    area_name = "area_test"
    area = Area(
        name=area_name, links={}, thermals=[], renewables=[], filters_synthesis=[], filters_year=[], st_storages=[]
    )
    areas = {area_name: area}
    node = ini_node_cluster_class(
        context=Mock(),
        config=FileStudyTreeConfig(study_path=study_path, path=file_path, version=-1, study_id="id", areas=areas),
        area=area_name,
    )

    assert node.get() == {"Cluster 1": {"group": "gas"}}


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "ini_node_cluster_class",
    [InputSTStorageAreaList, ClusteredRenewableClusterConfig, InputThermalClustersAreaList],
)
def test_cluster_ini_list(tmp_path: Path, ini_node_cluster_class):
    study_path = tmp_path / "study"
    study_path.mkdir()
    file_path = study_path / "test.ini"
    file_path.touch()
    data = {"Cluster 1": {"group": "Gas"}}
    area_name = "area_test"
    area = Area(
        name=area_name, links={}, thermals=[], renewables=[], filters_synthesis=[], filters_year=[], st_storages=[]
    )
    areas = {area_name: area}
    node = ini_node_cluster_class(
        context=Mock(),
        config=FileStudyTreeConfig(study_path=study_path, path=file_path, version=-1, study_id="id", areas=areas),
        area=area_name,
    )
    node.save(data)
    # Asserts the data is saved correctly
    ini_content = IniReader().read(file_path)
    assert ini_content == data
    # Asserts cluster group and ids are returned in lower case
    content = node.get([])
    assert content == {"Cluster 1": {"group": "gas"}}
    # Asserts saving the group in upper case works and that it will be returned in lower case
    node.save("NUCLEAR", ["Cluster 1", "group"])
    content = node.get([])
    assert content == {"Cluster 1": {"group": "nuclear"}}
    # Asserts updating the file with an id not in lower case will be done correctly
    node.save({"params": "43"}, ["cluster 1"])
    content = node.get([])
    assert content == {"Cluster 1": {"params": 43}}


@pytest.mark.unit_test
def test_binding_constraint_group_writing(tmp_path: Path):
    study_path = tmp_path / "study"
    study_path.mkdir()
    file_path = study_path / "test.ini"
    file_path.touch()
    node = BindingConstraintsIni(
        context=Mock(),
        config=FileStudyTreeConfig(study_path=study_path, path=file_path, version=-1, study_id="id"),
    )

    data = {"0": {"name": "BC_1", "group": "GRP_1"}}
    node.save(data)
    # Asserts the data is saved correctly
    ini_content = IniReader().read(file_path)
    assert ini_content == data
    # Asserts the constraint group is returned in lower case
    content = node.get([])
    assert content == {"0": {"name": "BC_1", "group": "grp_1"}}
