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

import numpy as np
from checksumdir import dirhash

from antarest.study.business.model.binding_constraint_model import ClusterTerm, ConstraintTerm
from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation, ThermalClusterGroup
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.remove_cluster import RemoveCluster
from antarest.study.storage.variantstudy.model.command.remove_multiple_binding_constraints import (
    RemoveMultipleBindingConstraints,
)
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.variantstudy.model.command.helpers import reset_line_separator


class TestRemoveCluster:
    def test_apply(
        self, empty_study_720: FileStudy, empty_study_870: FileStudy, command_context: CommandContext
    ) -> None:
        for empty_study in [empty_study_720, empty_study_870]:
            area_name = "Area_name"
            area_id = transform_name_to_id(area_name)
            cluster_name = "Cluster Name"
            cluster_id = transform_name_to_id(cluster_name, lower=False)

            study_version = empty_study.config.version

            output = CreateArea(
                area_name=area_name, command_context=command_context, study_version=study_version
            ).apply(empty_study)
            assert output.status, output.message

            ################################################################################################

            # Line ending of the `settings/scenariobuilder.dat` must be reset before checksum
            reset_line_separator(empty_study.config.study_path.joinpath("settings/scenariobuilder.dat"))
            hash_before_removal = dirhash(empty_study.config.study_path, "md5")

            output = CreateCluster(
                area_id=area_id,
                parameters=ThermalClusterCreation(
                    name=cluster_name,
                    group=ThermalClusterGroup.NUCLEAR,
                    unit_count=1,
                    nominal_capacity=100,
                    marginal_cost=40,
                    market_bid_cost=40,
                ),
                command_context=command_context,
                prepro=[[0]],
                modulation=[[0]],
                study_version=study_version,
            ).apply(empty_study)
            assert output.status, output.message

            # Binding constraint 2nd member: array of shape (8784, 3)
            array = np.random.rand(8784, 3) * 1000
            if empty_study.config.version < 870:
                values = array.tolist()
                less_term_matrix = None
            else:
                values = None
                less_term_matrix = array.tolist()

            bind1_cmd = CreateBindingConstraint(
                **{
                    "parameters": {
                        "name": "BD 1",
                        "time_step": BindingConstraintFrequency.HOURLY,
                        "operator": BindingConstraintOperator.LESS,
                        "terms": [
                            ConstraintTerm(weight=800, offset=30, data=ClusterTerm(area=area_id, cluster=cluster_id)),
                        ],
                        "comments": "Hello",
                    },
                    "matrices": {"values": values, "less_term_matrix": less_term_matrix},
                    "command_context": command_context,
                    "study_version": study_version,
                }
            )
            output = bind1_cmd.apply(study_data=empty_study)
            assert output.status, output.message

            # Add scenario builder data
            output = UpdateScenarioBuilder(
                data={"Default Ruleset": {f"t,{area_id},0,{cluster_name.lower()}": 1}},
                command_context=command_context,
                study_version=study_version,
            ).apply(study_data=empty_study)
            assert output.status, output.message

            # Ensures the command fails cause the cluster is referenced in a constraint term
            remove_cluster_cmd = RemoveCluster(
                area_id=area_id, cluster_id=cluster_id, command_context=command_context, study_version=study_version
            )
            output = remove_cluster_cmd.apply(empty_study)
            assert not output.status
            assert (
                "Cluster 'cluster name' is not allowed to be deleted, because it is referenced in the following binding constraints"
                in output.message
            )
            assert "bd 1" in output.message

            # First remove the constraint
            output = RemoveMultipleBindingConstraints(
                id="bd 1", command_context=command_context, study_version=study_version
            ).apply(study_data=empty_study)
            assert output.status, output.message

            # Then remove the cluster
            output = remove_cluster_cmd.apply(empty_study)
            assert output.status, output.message
            assert dirhash(empty_study.config.study_path, "md5") == hash_before_removal

            output = RemoveCluster(
                area_id="non_existent_area",
                cluster_id=cluster_id,
                command_context=command_context,
                study_version=study_version,
            ).apply(empty_study)
            assert not output.status

            output = RemoveCluster(
                area_id=area_name,
                cluster_id="non_existent_cluster",
                command_context=command_context,
                study_version=study_version,
            ).apply(empty_study)
            assert not output.status
