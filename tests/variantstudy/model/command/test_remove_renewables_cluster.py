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
from antares.study.version import StudyVersion
from checksumdir import dirhash

from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import EnrModelling
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import (
    RenewableProperties,
    TimeSeriesInterpretation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import RemoveRenewablesCluster
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.variantstudy.model.command.helpers import reset_line_separator


class TestRemoveRenewablesCluster:
    def test_apply(self, empty_study_810: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_810
        empty_study.config.enr_modelling = str(EnrModelling.CLUSTERS)
        study_version = StudyVersion.parse(810)
        empty_study.config.version = study_version
        area_name = "Area_name"
        area_id = transform_name_to_id(area_name)
        cluster_name = "Cluster Name"
        cluster_id = transform_name_to_id(cluster_name, lower=False)

        output = CreateArea(area_name=area_name, command_context=command_context, study_version=study_version).apply(
            empty_study
        )
        assert output.status, output.message

        ################################################################################################

        # Line ending of the `settings/scenariobuilder.dat` must be reset before checksum
        reset_line_separator(empty_study.config.study_path.joinpath("settings/scenariobuilder.dat"))
        hash_before_removal = dirhash(empty_study.config.study_path, "md5")

        CreateRenewablesCluster(
            area_id=area_id,
            parameters=RenewableProperties(
                name=cluster_name, ts_interpretation=TimeSeriesInterpretation.POWER_GENERATION
            ),
            command_context=command_context,
            study_version=study_version,
        ).apply(empty_study)

        # Add scenario builder data
        output = UpdateScenarioBuilder(
            data={"Default Ruleset": {f"r,{area_id},0,{cluster_name.lower()}": 1}},
            command_context=command_context,
            study_version=study_version,
        ).apply(study_data=empty_study)
        assert output.status, output.message

        output = RemoveRenewablesCluster(
            area_id=area_id, cluster_id=cluster_id, command_context=command_context, study_version=study_version
        ).apply(empty_study)

        assert output.status, output.message
        assert dirhash(empty_study.config.study_path, "md5") == hash_before_removal

        output = RemoveRenewablesCluster(
            area_id="non_existent_area",
            cluster_id=cluster_id,
            command_context=command_context,
            study_version=study_version,
        ).apply(empty_study)
        assert not output.status

        output = RemoveRenewablesCluster(
            area_id=area_name,
            cluster_id="non_existent_cluster",
            command_context=command_context,
            study_version=study_version,
        ).apply(empty_study)
        assert not output.status
