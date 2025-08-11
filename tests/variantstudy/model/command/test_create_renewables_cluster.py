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

import pytest
from pydantic import ValidationError

from antarest.study.business.model.renewable_cluster_model import (
    RenewableClusterCreation,
    RenewableClusterGroup,
    TimeSeriesInterpretation,
)
from antarest.study.model import STUDY_VERSION_8_1, STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import EnrModelling
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateRenewablesCluster:
    # noinspection SpellCheckingInspection
    def test_init(self, command_context: CommandContext) -> None:
        cl = CreateRenewablesCluster(
            area_id="foo",
            parameters=RenewableClusterCreation(
                name="Cluster1", group=RenewableClusterGroup.THERMAL_SOLAR, unit_count=2, nominal_capacity=2400
            ),
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )

        # Check the command metadata
        assert cl.command_name == CommandName.CREATE_RENEWABLES_CLUSTER
        assert cl.command_context is command_context

        # Check the command data
        assert cl.area_id == "foo"
        assert cl.parameters == RenewableClusterCreation(
            name="Cluster1", group=RenewableClusterGroup.THERMAL_SOLAR, unit_count=2, nominal_capacity=2400
        )

    def test_validate_cluster_name(self, command_context: CommandContext) -> None:
        with pytest.raises(ValidationError, match="Invalid name"):
            CreateRenewablesCluster(
                area_id="fr",
                command_context=command_context,
                parameters=RenewableClusterCreation(name="%"),
                study_version=STUDY_VERSION_8_8,
            )

    def test_apply(self, empty_study_810: FileStudy, command_context: CommandContext) -> None:
        empty_study = empty_study_810
        empty_study.config.enr_modelling = str(EnrModelling.CLUSTERS)
        study_version = STUDY_VERSION_8_1
        empty_study.config.version = study_version
        study_path = empty_study.config.study_path
        area_name = "DE"
        area_id = transform_name_to_id(area_name, lower=True)
        cluster_name = "Cluster-1"

        CreateArea(area_name=area_name, command_context=command_context, study_version=study_version).apply(empty_study)

        parameters = RenewableClusterCreation(
            name=cluster_name, ts_interpretation=TimeSeriesInterpretation.POWER_GENERATION
        )

        command = CreateRenewablesCluster(
            area_id=area_id,
            parameters=parameters,
            command_context=command_context,
            study_version=study_version,
        )

        output = command.apply(empty_study)
        assert output.status is True
        assert re.match(
            r"Renewable cluster 'cluster-1' added to area 'de'",
            output.message,
            flags=re.IGNORECASE,
        )

        clusters = configparser.ConfigParser()
        clusters.read(study_path / "input" / "renewables" / "clusters" / area_id / "list.ini")
        assert str(clusters[cluster_name]["name"]) == cluster_name
        assert str(clusters[cluster_name]["ts-interpretation"]) == "power-generation"

        output = CreateRenewablesCluster(
            area_id=area_id,
            parameters=parameters,
            command_context=command_context,
            study_version=study_version,
        ).apply(empty_study)
        assert not output.status

        output = CreateRenewablesCluster(
            area_id=area_id,
            parameters=parameters,
            command_context=command_context,
            study_version=study_version,
        ).apply(empty_study)
        assert output.status is False

        assert re.match(
            r"Renewable cluster 'cluster-1' already exists in the area 'de'",
            output.message,
            flags=re.IGNORECASE,
        )

        fake_area = "non_existent_area"
        output = CreateRenewablesCluster(
            area_id=fake_area,
            parameters=parameters,
            command_context=command_context,
            study_version=study_version,
        ).apply(empty_study)
        assert output.status is False
        assert f"The area '{fake_area}' does not exist" in output.message

    # noinspection SpellCheckingInspection
    def test_to_dto(self, command_context: CommandContext) -> None:
        command = CreateRenewablesCluster(
            area_id="foo",
            parameters=RenewableClusterCreation(
                name="Cluster1", group=RenewableClusterGroup.THERMAL_SOLAR, unit_count=2, nominal_capacity=2400
            ),
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )
        dto = command.to_dto()
        assert dto.model_dump() == {
            "action": "create_renewables_cluster",  # "renewables" with a final "s".
            "args": {
                "area_id": "foo",
                "parameters": {"name": "Cluster1", "group": "solar thermal", "nominalCapacity": 2400, "unitCount": 2},
            },
            "id": None,
            "version": 3,
            "study_version": "8.8",
            "updated_at": None,
            "user_id": None,
        }
