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
import pytest

from antarest.study.business.model.thermal_cluster_model import ThermalClusterUpdate
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalClusterGroup,
    create_thermal_config,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.update_thermal_cluster import UpdateThermalCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateThermalCluster:
    def _set_up(self, study: FileStudy, command_context: CommandContext, area_id: str, thermal_id: str) -> None:
        CreateArea(area_name=area_id, command_context=command_context, study_version=study.config.version).apply(study)
        thermal = {
            "co2": 0.57,
            "enabled": True,
            "fixed_cost": 0.0,
            "gen_ts": LocalTSGenerationBehavior.USE_GLOBAL,
            "group": ThermalClusterGroup.GAS,
            "law_forced": LawOption.UNIFORM,
            "law_planned": LawOption.UNIFORM,
            "marginal_cost": 181.267,
            "market_bid_cost": 181.267,
            "min_down_time": 5,
            "min_stable_power": 5.4984,
            "min_up_time": 5,
            "must_run": False,
            "name": "FR_Gas conventional old 1",
            "nominal_capacity": 32.1,
            "spinning": 0.0,
            "spread_cost": 0.0,
            "startup_cost": 6035.6,
            "unit_count": 15,
            "volatility_forced": 0.0,
            "volatility_planned": 0.0,
        }
        study.tree.save(thermal, ["input", "thermal", "clusters", area_id, "list", thermal_id])
        thermal.update({"id": thermal_id})
        thermal_config = create_thermal_config(study_version=study.config.version, **thermal)
        study.config.areas[area_id].thermals.append(thermal_config)

    @pytest.mark.parametrize("empty_study", ["empty_study_810.zip"], indirect=True)
    def test_update_thermal(self, empty_study: FileStudy, command_context: CommandContext):
        area_id = "fr"
        thermal_cluster_id = "test"

        self._set_up(empty_study, command_context, area_id, thermal_cluster_id)

        args = {
            "co2": 0.60,
            "enabled": False,
            "gen_ts": LocalTSGenerationBehavior.FORCE_GENERATION,
            "min_up_time": 10,
        }

        properties = ThermalClusterUpdate(**args)

        command = UpdateThermalCluster(
            area_id=area_id,
            thermal_cluster_id=thermal_cluster_id,
            properties=properties,
            command_context=command_context,
            study_version=empty_study.config.version,
        )
        output = command.apply(study_data=empty_study)

        assert output.status

        expected = {
            "co2": 0.6,
            "enabled": False,
            "fixed-cost": 0.0,
            "gen-ts": LocalTSGenerationBehavior.FORCE_GENERATION,
            "group": ThermalClusterGroup.GAS,
            "law.forced": LawOption.UNIFORM,
            "law.planned": LawOption.UNIFORM,
            "marginal-cost": 181.267,
            "market-bid-cost": 181.267,
            "min-down-time": 5,
            "min-stable-power": 5.4984,
            "min-up-time": 10,
            "must-run": False,
            "name": "FR_Gas conventional old 1",
            "nominalcapacity": 32.1,
            "spinning": 0.0,
            "spread-cost": 0.0,
            "startup-cost": 6035.6,
            "unitcount": 15,
            "volatility.forced": 0.0,
            "volatility.planned": 0.0,
        }

        thermal = empty_study.tree.get(["input", "thermal", "clusters", area_id, "list", thermal_cluster_id])
        assert thermal == expected
        assert empty_study.config.areas[area_id].thermals[0].model_dump(exclude={"id"}, by_alias=True) == expected

    @pytest.mark.parametrize("empty_study", ["empty_study_810.zip"], indirect=True)
    def test_update_thermal_cluster_does_not_exist(self, empty_study: FileStudy, command_context: CommandContext):
        area_id = "fr"
        thermal_cluster_id = "no"

        self._set_up(empty_study, command_context, area_id, "cluster")

        properties = ThermalClusterUpdate(**{})

        command = UpdateThermalCluster(
            area_id=area_id,
            thermal_cluster_id=thermal_cluster_id,
            properties=properties,
            command_context=command_context,
            study_version=empty_study.config.version,
        )

        output = command.apply(study_data=empty_study)
        assert not output.status
        assert (
            output.message
            == "Unexpected exception occurred when trying to apply command CommandName.UPDATE_THERMAL_CLUSTER: 'Could not match section no'"
        )
