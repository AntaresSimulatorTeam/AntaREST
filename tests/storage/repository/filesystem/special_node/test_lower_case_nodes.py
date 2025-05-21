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

import pytest
from antares.study.version import StudyVersion

from antarest.core.serde.ini_reader import read_ini
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8
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


@pytest.fixture
def study_dir(tmp_path: Path) -> Path:
    study_path = tmp_path / "study"
    study_path.mkdir()
    return study_path


@pytest.fixture
def ini_file(study_dir: Path) -> Path:
    file_path = study_dir / "test.ini"
    file_path.touch()
    return file_path


def create_study_config(study_dir: Path, ini_file: Path, version: StudyVersion, area_name: str) -> FileStudyTreeConfig:
    area = Area(
        name=area_name, links={}, thermals=[], renewables=[], filters_synthesis=[], filters_year=[], st_storages=[]
    )
    areas = {area_name: area}
    return FileStudyTreeConfig(study_path=study_dir, path=ini_file, version=version, study_id="id", areas=areas)


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "ini_node_cluster_class",
    [InputSTStorageAreaList, ClusteredRenewableClusterConfig, InputThermalClustersAreaList],
)
def test_group_is_parsed_to_lower_case(study_dir: Path, ini_file: Path, ini_node_cluster_class):
    ini_file.write_text(
        textwrap.dedent(
            """
            [Cluster 1]
            group = Gas
            """
        )
    )

    node = ini_node_cluster_class(
        config=create_study_config(study_dir, ini_file, STUDY_VERSION_8_8, "area_test"),
        area="area_test",
    )

    assert node.get() == {"Cluster 1": {"group": "gas"}}


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "ini_node_cluster_class",
    [InputSTStorageAreaList, ClusteredRenewableClusterConfig, InputThermalClustersAreaList],
)
def test_cluster_ini_list(study_dir: Path, ini_file: Path, ini_node_cluster_class):
    data = {"Cluster 1": {"group": "Gas"}}
    node = ini_node_cluster_class(
        config=create_study_config(study_dir, ini_file, STUDY_VERSION_8_8, "area_test"),
        area="area_test",
    )

    node.save(data)
    # Asserts the data is saved correctly
    ini_content = read_ini(ini_file)
    assert ini_content == {"Cluster 1": {"group": "gas"}}
    # Asserts cluster group is returned in lower case
    content = node.get([])
    assert content == {"Cluster 1": {"group": "gas"}}
    # Asserts saving the group in upper case works and that it will be returned in lower case
    node.save("NUCLEAR", ["Cluster 1", "group"])
    content = node.get([])
    assert content == {"Cluster 1": {"group": "nuclear"}}


@pytest.mark.unit_test
def test_binding_constraint_group_writing(
    study_dir: Path,
    ini_file: Path,
):
    node = BindingConstraintsIni(
        config=FileStudyTreeConfig(study_path=study_dir, path=ini_file, version=STUDY_VERSION_8_8, study_id="id"),
    )

    node.save({"0": {"name": "BC_1", "group": "GRP_1"}})
    assert read_ini(ini_file) == {"0": {"name": "BC_1", "group": "grp_1"}}

    node.save(data="GRP_2", url=["0", "group"])
    assert read_ini(ini_file) == {"0": {"name": "BC_1", "group": "grp_2"}}


@pytest.mark.unit_test
def test_binding_constraint_group_parsing(
    study_dir: Path,
    ini_file: Path,
):
    ini_file.write_text(
        textwrap.dedent(
            """
            [0]
            group = GRP
            """
        )
    )

    node = BindingConstraintsIni(
        config=FileStudyTreeConfig(study_path=study_dir, path=ini_file, version=STUDY_VERSION_8_8, study_id="id"),
    )

    content = node.get()
    assert content == {"0": {"group": "grp"}}


@pytest.mark.unit_test
def test_st_storage_group_is_written_to_title_case_for_8_6(study_dir: Path, ini_file: Path):
    ini_file.write_text(
        textwrap.dedent(
            """
            [Cluster 1]
            group = gas
            """
        )
    )
    node = InputSTStorageAreaList(
        config=create_study_config(study_dir, ini_file, STUDY_VERSION_8_6, "area_test"),
        area="area_test",
    )

    node.save({"Cluster 1": {"group": "PsP_open"}, "Cluster 2": {"group": "UnknownGroup"}})
    assert read_ini(ini_file) == {"Cluster 1": {"group": "PSP_open"}, "Cluster 2": {"group": "unknowngroup"}}
