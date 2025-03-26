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

import configparser
import re

import numpy as np
import pytest
from pydantic import ValidationError

from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import Thermal870Properties, ThermalClusterGroup
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext

GEN = np.random.default_rng(1000)


class TestCreateCluster:
    def test_init(self, command_context: CommandContext):
        prepro = GEN.random((365, 6)).tolist()
        modulation = GEN.random((8760, 4)).tolist()
        cl = CreateCluster(
            area_id="foo",
            parameters=Thermal870Properties(
                name="Cluster1", group=ThermalClusterGroup.NUCLEAR, unit_count=2, nominal_capacity=2400
            ),
            command_context=command_context,
            prepro=prepro,
            modulation=modulation,
            study_version=STUDY_VERSION_8_8,
        )

        # Check the command metadata
        assert cl.command_name == CommandName.CREATE_THERMAL_CLUSTER
        assert cl.study_version == STUDY_VERSION_8_8
        assert cl.command_context is command_context

        # Check the command data
        prepro_id = command_context.matrix_service.create(prepro)
        modulation_id = command_context.matrix_service.create(modulation)
        assert cl.area_id == "foo"
        assert cl.cluster_name == "Cluster1"
        assert cl.parameters == Thermal870Properties(
            name="Cluster1", group=ThermalClusterGroup.NUCLEAR, unit_count=2, nominal_capacity=2400
        )
        assert cl.prepro == f"matrix://{prepro_id}"
        assert cl.modulation == f"matrix://{modulation_id}"

    def test_validate_cluster_name(self, command_context: CommandContext):
        with pytest.raises(ValidationError, match="name"):
            CreateCluster(
                area_id="fr",
                parameters=Thermal870Properties(name="%"),
                command_context=command_context,
                study_version=STUDY_VERSION_8_8,
            )

    def test_validate_prepro(self, command_context: CommandContext):
        cl = CreateCluster(
            area_id="fr",
            parameters=Thermal870Properties(name="C1"),
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )
        assert cl.prepro == command_context.generator_matrix_constants.get_thermal_prepro_data()

    def test_validate_modulation(self, command_context: CommandContext):
        cl = CreateCluster(
            area_id="fr",
            parameters=Thermal870Properties(name="C1"),
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )
        assert cl.modulation == command_context.generator_matrix_constants.get_thermal_prepro_modulation()

    def test_apply(self, empty_study_870: FileStudy, command_context: CommandContext):
        empty_study = empty_study_870
        study_path = empty_study.config.study_path
        area_name = "DE"
        area_id = transform_name_to_id(area_name, lower=True)
        cluster_name = "Cluster-1"
        cluster_id = transform_name_to_id(cluster_name, lower=True)

        CreateArea(area_name=area_name, command_context=command_context, study_version=STUDY_VERSION_8_8).apply(
            empty_study
        )

        parameters = Thermal870Properties.model_validate(
            {
                "name": cluster_name,
                "group": "Other",
                "unitcount": "1",
                "nominalcapacity": "1000000",
                "marginal-cost": "30",
                "market-bid-cost": "30",
            }
        )

        prepro = GEN.random((365, 6)).tolist()
        modulation = GEN.random((8760, 4)).tolist()
        command = CreateCluster(
            area_id=area_id,
            parameters=parameters,
            prepro=prepro,
            modulation=modulation,
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )

        output = command.apply(empty_study)
        assert output.status is True
        assert re.match(
            r"Thermal cluster 'cluster-1' added to area 'de'",
            output.message,
            flags=re.IGNORECASE,
        )

        clusters = configparser.ConfigParser()
        clusters.read(study_path / "input" / "thermal" / "clusters" / area_id / "list.ini")
        assert str(clusters[cluster_name]["name"]) == cluster_name
        assert str(clusters[cluster_name]["group"]) == parameters.group
        assert int(clusters[cluster_name]["unitcount"]) == parameters.unit_count
        assert float(clusters[cluster_name]["nominalcapacity"]) == parameters.nominal_capacity
        assert float(clusters[cluster_name]["marginal-cost"]) == parameters.marginal_cost
        assert float(clusters[cluster_name]["market-bid-cost"]) == parameters.market_bid_cost

        assert (study_path / "input" / "thermal" / "prepro" / area_id / cluster_id / "data.txt.link").exists()
        assert (study_path / "input" / "thermal" / "prepro" / area_id / cluster_id / "modulation.txt.link").exists()

        output = CreateCluster(
            area_id=area_id,
            parameters=parameters,
            prepro=prepro,
            modulation=modulation,
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        ).apply(empty_study)
        assert output.status is False
        assert re.match(
            r"Thermal cluster 'cluster-1' already exists in the area 'de'",
            output.message,
            flags=re.IGNORECASE,
        )

        output = CreateCluster(
            area_id="non_existent_area",
            parameters=parameters,
            prepro=prepro,
            modulation=modulation,
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        ).apply(empty_study)
        assert output.status is False
        assert re.match(
            r"Area 'non_existent_area' does not exist",
            output.message,
            flags=re.IGNORECASE,
        )

    def test_to_dto(self, command_context: CommandContext):
        prepro = GEN.random((365, 6)).tolist()
        modulation = GEN.random((8760, 4)).tolist()
        command = CreateCluster(
            area_id="foo",
            parameters=Thermal870Properties(
                name="Cluster1", group=ThermalClusterGroup.NUCLEAR, unit_count=2, nominal_capacity=2400
            ),
            command_context=command_context,
            prepro=prepro,
            modulation=modulation,
            study_version=STUDY_VERSION_8_8,
        )
        dto = command.to_dto()

        prepro_id = command_context.matrix_service.create(prepro)
        modulation_id = command_context.matrix_service.create(modulation)
        assert dto.model_dump() == {
            "action": "create_cluster",
            "args": {
                "area_id": "foo",
                "parameters": {
                    "co2": 0.0,
                    "costgeneration": "SetManually",
                    "efficiency": 100.0,
                    "enabled": True,
                    "fixed-cost": 0.0,
                    "gen-ts": "use global",
                    "group": "nuclear",
                    "law.forced": "uniform",
                    "law.planned": "uniform",
                    "marginal-cost": 0.0,
                    "market-bid-cost": 0.0,
                    "min-down-time": 1,
                    "min-stable-power": 0.0,
                    "min-up-time": 1,
                    "must-run": False,
                    "name": "Cluster1",
                    "nh3": 0.0,
                    "nmvoc": 0.0,
                    "nominalcapacity": 2400.0,
                    "nox": 0.0,
                    "op1": 0.0,
                    "op2": 0.0,
                    "op3": 0.0,
                    "op4": 0.0,
                    "op5": 0.0,
                    "pm10": 0.0,
                    "pm2_5": 0.0,
                    "pm5": 0.0,
                    "so2": 0.0,
                    "spinning": 0.0,
                    "spread-cost": 0.0,
                    "startup-cost": 0.0,
                    "unitcount": 2,
                    "variableomcost": 0.0,
                    "volatility.forced": 0.0,
                    "volatility.planned": 0.0,
                },
                "prepro": prepro_id,
                "modulation": modulation_id,
            },
            "id": None,
            "study_version": "8.8",
            "updated_at": None,
            "user_id": None,
            "version": 2,
        }
