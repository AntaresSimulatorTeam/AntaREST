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

from checksumdir import dirhash

from antarest.study.business.model.renewable_cluster_model import RenewableClusterCreation, TimeSeriesInterpretation
from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation, ThermalClusterGroup
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import RenewableClusterGroup
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.create_district import CreateDistrict, DistrictBaseFilter
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.remove_district import RemoveDistrict
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.variantstudy.model.command.helpers import reset_line_separator


class TestRemoveArea:
    def _set_up(self, empty_study: FileStudy, command_context: CommandContext):
        empty_study.tree.save(
            {
                "input": {
                    "thermal": {
                        "areas": {
                            "unserverdenergycost": {},
                            "spilledenergycost": {},
                        }
                    },
                    "hydro": {
                        "hydro": {
                            "inter-daily-breakdown": {},
                            "intra-daily-modulation": {},
                            "inter-monthly-breakdown": {},
                            "initialize reservoir date": {},
                            "leeway low": {},
                            "leeway up": {},
                            "pumping efficiency": {},
                        }
                    },
                }
            }
        )

        area_name = "Area"
        area_id = transform_name_to_id(area_name)
        create_area_command: ICommand = CreateArea(
            area_name=area_name, command_context=command_context, study_version=empty_study.config.version
        )
        output = create_area_command.apply(study_data=empty_study)
        assert output.status, output.message
        return empty_study, area_id

    def test_remove_with_aggregated(self, empty_study_810: FileStudy, command_context: CommandContext):
        (empty_study, area_id) = self._set_up(empty_study_810, command_context)
        remove_area_command = RemoveArea(id=area_id, command_context=command_context, study_version=STUDY_VERSION_8_8)
        output = remove_area_command.apply(study_data=empty_study)
        assert output.status, output.message

    def test_apply(self, empty_study_810: FileStudy, empty_study_840: FileStudy, command_context: CommandContext):
        for empty_study in [empty_study_810, empty_study_840]:
            # noinspection SpellCheckingInspection
            (empty_study, area_id) = self._set_up(empty_study, command_context)
            study_version = empty_study.config.version

            create_district_command = CreateDistrict(
                name="foo",
                base_filter=DistrictBaseFilter.add_all,
                filter_items=[area_id],
                command_context=command_context,
                study_version=study_version,
            )
            output = create_district_command.apply(study_data=empty_study)
            assert output.status, output.message

            # Change the MC years to 5 to test the scenario builder data
            empty_study.tree.save(5, ["settings", "generaldata", "general", "nbyears"])

            if empty_study.config.version >= 810:
                # Parameter 'renewable-generation-modelling' must be set to 'clusters' instead of 'aggregated'
                update_config = UpdateConfig(
                    target="settings/generaldata/other preferences",
                    data={"renewable-generation-modelling": "clusters"},
                    command_context=command_context,
                    study_version=study_version,
                )
                output = update_config.apply(study_data=empty_study)
                assert output.status, output.message

            ########################################################################################

            # Line ending of the `settings/scenariobuilder.dat` must be reset before checksum
            reset_line_separator(empty_study.config.study_path.joinpath("settings/scenariobuilder.dat"))
            hash_before_removal = dirhash(empty_study.config.study_path, "md5")

            empty_study_cfg = empty_study.tree.get(depth=999)
            if study_version >= 830:
                empty_study_cfg["input"]["areas"][area_id]["adequacy_patch"] = {
                    "adequacy-patch": {"adequacy-patch-mode": "outside"}
                }
                empty_study_cfg["input"]["links"][area_id]["capacities"] = {}

            area_name2 = "Area2"
            area_id2 = transform_name_to_id(area_name2)

            create_area_command: ICommand = CreateArea(
                area_name=area_name2, command_context=command_context, study_version=study_version
            )
            output = create_area_command.apply(study_data=empty_study)
            assert output.status, output.message

            create_link_command: ICommand = CreateLink(
                area1=area_id,
                area2=area_id2,
                parameters={},
                command_context=command_context,
                series=[[0]],
                study_version=study_version,
            )
            output = create_link_command.apply(study_data=empty_study)
            assert output.status, output.message

            thermal_name = "cluster"
            thermal_id = transform_name_to_id(thermal_name)
            output = CreateCluster(
                area_id=area_id2,
                parameters=ThermalClusterCreation(
                    name=thermal_name,
                    group=ThermalClusterGroup.OTHER1,
                    unit_count=1,
                    nominal_capacity=1000000,
                    marginal_cost=30,
                    market_bid_cost=30,
                ),
                prepro=[[0]],
                modulation=[[0]],
                command_context=command_context,
                study_version=study_version,
            ).apply(study_data=empty_study)
            assert output.status, output.message

            renewable_id = None
            if study_version >= 810:
                renewable_name = "Renewable"
                renewable_id = transform_name_to_id(renewable_name)
                output = CreateRenewablesCluster(
                    area_id=area_id2,
                    parameters=RenewableClusterCreation(
                        name=renewable_name,
                        enabled=True,
                        group=RenewableClusterGroup.ROOFTOP_SOLAR,
                        unit_count=10,
                        nominal_capacity=12000,
                        ts_interpretation=TimeSeriesInterpretation.POWER_GENERATION,
                    ),
                    command_context=command_context,
                    study_version=study_version,
                ).apply(study_data=empty_study)
                assert output.status, output.message

            bind1_cmd = CreateBindingConstraint(
                name="BD 2",
                time_step=BindingConstraintFrequency.HOURLY,
                operator=BindingConstraintOperator.LESS,
                coeffs={
                    f"{area_id}%{area_id2}": [400, 30],
                    f"{area_id2}.cluster": [400, 30],
                },
                comments="Hello",
                command_context=command_context,
                study_version=study_version,
            )
            output = bind1_cmd.apply(study_data=empty_study)
            assert output.status, output.message

            remove_district_command = RemoveDistrict(
                id="foo", command_context=command_context, study_version=study_version
            )
            output = remove_district_command.apply(study_data=empty_study)
            assert output.status, output.message

            create_district_command = CreateDistrict(
                name="foo",
                base_filter=DistrictBaseFilter.add_all,
                filter_items=[area_id, area_id2],
                command_context=command_context,
                study_version=study_version,
            )
            output = create_district_command.apply(study_data=empty_study)
            assert output.status, output.message

            # Add scenario builder data
            default_ruleset = {
                f"l,{area_id2},0": 1,
                f"h,{area_id2},0": 1,
                f"w,{area_id2},0": 1,
                f"s,{area_id2},0": 1,
                f"ntc,{area_id},{area_id2},0": 1,
                f"t,{area_id2},0,{thermal_id.lower()}": 1,
            }
            if study_version >= 800:
                default_ruleset[f"hl,{area_id2},0"] = 1
            if study_version >= 810:
                default_ruleset[f"r,{area_id2},0,{renewable_id.lower()}"] = 1
            if study_version >= 870:
                default_ruleset["bc,bd 2,0"] = 1
            if study_version >= 920:
                default_ruleset[f"hfl,{area_id2},0"] = 1
            if study_version >= 910:
                default_ruleset[f"hgp,{area_id2},0"] = 1

            output = UpdateScenarioBuilder(
                data={"Default Ruleset": default_ruleset}, command_context=command_context, study_version=study_version
            ).apply(study_data=empty_study)
            assert output.status, output.message

            remove_area_command: ICommand = RemoveArea(
                id=area_id2, command_context=command_context, study_version=study_version
            )
            output = remove_area_command.apply(study_data=empty_study)
            assert output.status, output.message
            assert dirhash(empty_study.config.study_path, "md5") == hash_before_removal

            actual_cfg = empty_study.tree.get(depth=999)
            assert actual_cfg == empty_study_cfg
