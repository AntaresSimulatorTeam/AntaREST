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
from checksumdir import dirhash
from pydantic import ValidationError

from antarest.study.business.model.thermal_cluster_model import ThermalClusterUpdate
from antarest.study.model import STUDY_VERSION_8_1
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalClusterGroup,
    parse_thermal_cluster,
    serialize_thermal_cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.update_thermal_clusters import UpdateThermalClusters
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateThermalCluster:
    def _set_up(self, study: FileStudy, command_context: CommandContext, area_name: str, thermal_name: str) -> None:
        CreateArea(area_name=area_name, command_context=command_context, study_version=study.config.version).apply(
            study
        )
        area_id = transform_name_to_id(area_name)
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
            "name": thermal_name,
            "nominal_capacity": 32.1,
            "spinning": 0.0,
            "spread_cost": 0.0,
            "startup_cost": 6035.6,
            "unit_count": 15,
            "volatility_forced": 0.0,
            "volatility_planned": 0.0,
        }
        study.tree.save(thermal, ["input", "thermal", "clusters", area_id, "list", thermal_name])
        thermal_config = parse_thermal_cluster(study_version=study.config.version, data=thermal)
        study.config.areas[area_id].thermals.append(thermal_config)

    def test_update_thermal(self, empty_study_810: FileStudy, command_context: CommandContext):
        empty_study = empty_study_810
        area_name = "FR"
        area_id = "fr"
        thermal_cluster_name = "test"
        self._set_up(empty_study, command_context, area_name, thermal_cluster_name)

        args = {
            "co2": 0.60,
            "enabled": False,
            "gen_ts": LocalTSGenerationBehavior.FORCE_GENERATION,
            "min_up_time": 10,
        }

        properties = ThermalClusterUpdate(**args)

        command = UpdateThermalClusters(
            cluster_properties={area_name: {thermal_cluster_name: properties}},
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
            "name": "test",
            "nominalcapacity": 32.1,
            "spinning": 0.0,
            "spread-cost": 0.0,
            "startup-cost": 6035.6,
            "unitcount": 15,
            "volatility.forced": 0.0,
            "volatility.planned": 0.0,
        }

        thermal = empty_study.tree.get(["input", "thermal", "clusters", area_id, "list", thermal_cluster_name])
        assert thermal == expected
        assert serialize_thermal_cluster(STUDY_VERSION_8_1, empty_study.config.areas[area_id].thermals[0]) == expected

    def test_update_thermal_cluster_does_not_exist(self, empty_study_810: FileStudy, command_context: CommandContext):
        # Set up
        study = empty_study_810
        self._set_up(study, command_context, "fr", "test")
        self._set_up(study, command_context, "second_area", "test_2")
        # Ensures updating an unexisting thermal cluster raises an Exception.
        # Also ensures the study wasn't partially modified.
        hash_before_update = dirhash(study.config.study_path / "input" / "thermal", "md5")
        fake_cluster = "no"
        properties = ThermalClusterUpdate(**{})
        mapping = {"fr": {"test": properties}, "second_area": {fake_cluster: properties}}
        command = UpdateThermalClusters(
            cluster_properties=mapping,
            command_context=command_context,
            study_version=study.config.version,
        )

        output = command.apply(study_data=study)
        assert not output.status
        assert output.message == f"The thermal cluster '{fake_cluster}' in the area 'second_area' is not found."
        hash_after_update = dirhash(study.config.study_path / "input" / "thermal", "md5")
        assert hash_before_update == hash_after_update

    def test_invalid_field_for_version_should_raise_validation_error(self, command_context: CommandContext):
        update_data = ThermalClusterUpdate(nox=12.0)
        with pytest.raises(ValidationError):
            UpdateThermalClusters(
                cluster_properties={"fr": {"cluster": update_data}},
                command_context=command_context,
                study_version=STUDY_VERSION_8_1,
            )
