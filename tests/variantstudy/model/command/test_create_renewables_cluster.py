# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from unittest import mock

import pytest
from pydantic import ValidationError

from antarest.study.model import STUDY_VERSION_8_1, STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import EnrModelling
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import RenewableProperties
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import CommandReverter
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import RemoveRenewablesCluster
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateRenewablesCluster:
    # noinspection SpellCheckingInspection
    def test_init(self, command_context: CommandContext) -> None:
        parameters = {"group": "Solar Thermal", "unitcount": 2, "nominalcapacity": 2400}
        cl = CreateRenewablesCluster(
            area_id="foo",
            cluster_name="Cluster1",
            parameters=parameters,
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )

        # Check the command metadata
        assert cl.command_name == CommandName.CREATE_RENEWABLES_CLUSTER
        assert cl.version == 1
        assert cl.command_context is command_context

        # Check the command data
        assert cl.area_id == "foo"
        assert cl.cluster_name == "cluster1"
        assert cl.parameters.model_dump(by_alias=True) == RenewableProperties.model_validate(
            {"name": "cluster1", **parameters}
        ).model_dump(by_alias=True)

    def test_validate_cluster_name(self, command_context: CommandContext) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateRenewablesCluster(
                area_id="fr",
                cluster_name="%",
                command_context=command_context,
                parameters={},
                study_version=STUDY_VERSION_8_8,
            )

    def test_apply(self, empty_study: FileStudy, command_context: CommandContext) -> None:
        empty_study.config.enr_modelling = str(EnrModelling.CLUSTERS)
        study_version = STUDY_VERSION_8_1
        empty_study.config.version = study_version
        study_path = empty_study.config.study_path
        area_name = "DE"
        area_id = transform_name_to_id(area_name)
        cluster_name = "Cluster-1"

        CreateArea(area_name=area_name, command_context=command_context, study_version=study_version).apply(empty_study)

        parameters = {
            "name": cluster_name,
            "ts-interpretation": "power-generation",
        }

        command = CreateRenewablesCluster(
            area_id=area_id,
            cluster_name=cluster_name,
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
        assert str(clusters[cluster_name.lower()]["name"]) == cluster_name.lower()
        assert str(clusters[cluster_name.lower()]["ts-interpretation"]) == parameters["ts-interpretation"]

        output = CreateRenewablesCluster(
            area_id=area_id,
            cluster_name=cluster_name,
            parameters=parameters,
            command_context=command_context,
            study_version=study_version,
        ).apply(empty_study)
        assert not output.status

        output = CreateRenewablesCluster(
            area_id=area_id,
            cluster_name=cluster_name,
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

        output = CreateRenewablesCluster(
            area_id="non_existent_area",
            cluster_name=cluster_name,
            parameters=parameters,
            command_context=command_context,
            study_version=study_version,
        ).apply(empty_study)
        assert output.status is False
        assert re.match(
            r"Area 'non_existent_area' does not exist",
            output.message,
            flags=re.IGNORECASE,
        )

    # noinspection SpellCheckingInspection
    def test_to_dto(self, command_context: CommandContext) -> None:
        parameters = {"group": "Solar Thermal", "unitcount": 2, "nominalcapacity": 2400}
        command = CreateRenewablesCluster(
            area_id="foo",
            cluster_name="Cluster1",
            parameters=parameters,
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )
        dto = command.to_dto()
        assert dto.model_dump() == {
            "action": "create_renewables_cluster",  # "renewables" with a final "s".
            "args": {
                "area_id": "foo",
                "cluster_name": "cluster1",
                "parameters": RenewableProperties.model_validate({"name": "cluster1", **parameters}).model_dump(
                    by_alias=True
                ),
            },
            "id": None,
            "version": 1,
            "study_version": STUDY_VERSION_8_8,
            "updated_at": None,
            "user_id": None,
        }


def test_match(command_context: CommandContext) -> None:
    base = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_match = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_not_match = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="bar",
        parameters={},
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_other = RemoveRenewablesCluster(
        area_id="id", cluster_id="id", command_context=command_context, study_version=STUDY_VERSION_8_8
    )
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)

    assert base.match(other_match, equal=True)
    assert not base.match(other_not_match, equal=True)
    assert not base.match(other_other, equal=True)

    assert base.match_signature() == "create_renewables_cluster%foo%foo"
    assert base.get_inner_matrices() == []


def test_revert(command_context: CommandContext) -> None:
    base = CreateRenewablesCluster(
        area_id="area_foo",
        cluster_name="cl1",
        parameters={},
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    file_study = mock.MagicMock(spec=FileStudy)
    file_study.config.version = STUDY_VERSION_8_8
    revert_cmd = CommandReverter().revert(base, [], file_study)
    assert revert_cmd == [
        RemoveRenewablesCluster(
            area_id="area_foo", cluster_id="cl1", command_context=command_context, study_version=STUDY_VERSION_8_8
        )
    ]


def test_create_diff(command_context: CommandContext) -> None:
    base = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    parameters = {"nominal_capacity": 1.2}
    other_match = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters=parameters,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    assert base.create_diff(other_match) == [
        UpdateConfig(
            target="input/renewables/clusters/foo/list/foo",
            data=RenewableProperties.model_validate({"name": "foo", **parameters}).model_dump(
                mode="json", by_alias=True
            ),
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        ),
    ]
