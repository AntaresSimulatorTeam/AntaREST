import configparser
import re

import pytest
from pydantic import ValidationError

from antarest.study.storage.rawstudy.model.filesystem.config.model import EnrModelling, transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import CommandReverter
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import RemoveRenewablesCluster
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateRenewablesCluster:
    def test_init(self, command_context: CommandContext):
        cl = CreateRenewablesCluster(
            area_id="foo",
            cluster_name="Cluster1",
            parameters={"group": "Solar Thermal", "unitcount": 2, "nominalcapacity": 2400},
            command_context=command_context,
        )

        # Check the command metadata
        assert cl.command_name == CommandName.CREATE_RENEWABLES_CLUSTER
        assert cl.version == 1
        assert cl.command_context is command_context

        # Check the command data
        assert cl.area_id == "foo"
        assert cl.cluster_name == "Cluster1"
        assert cl.parameters == {"group": "Solar Thermal", "nominalcapacity": "2400", "unitcount": "2"}

    def test_validate_cluster_name(self, command_context: CommandContext):
        with pytest.raises(ValidationError, match="cluster_name"):
            CreateRenewablesCluster(area_id="fr", cluster_name="%", command_context=command_context, parameters={})

    def test_apply(self, empty_study: FileStudy, command_context: CommandContext):
        empty_study.config.enr_modelling = EnrModelling.CLUSTERS.value
        study_path = empty_study.config.study_path
        area_name = "DE"
        area_id = transform_name_to_id(area_name, lower=True)
        cluster_name = "Cluster-1"

        CreateArea(area_name=area_name, command_context=command_context).apply(empty_study)

        parameters = {
            "name": cluster_name,
            "ts-interpretation": "power-generation",
        }

        command = CreateRenewablesCluster(
            area_id=area_id,
            cluster_name=cluster_name,
            parameters=parameters,
            command_context=command_context,
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
        assert str(clusters[cluster_name]["ts-interpretation"]) == parameters["ts-interpretation"]

        output = CreateRenewablesCluster(
            area_id=area_id,
            cluster_name=cluster_name,
            parameters=parameters,
            command_context=command_context,
        ).apply(empty_study)
        assert not output.status

        output = CreateRenewablesCluster(
            area_id=area_id,
            cluster_name=cluster_name,
            parameters=parameters,
            command_context=command_context,
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
        ).apply(empty_study)
        assert output.status is False
        assert re.match(
            r"Area 'non_existent_area' does not exist",
            output.message,
            flags=re.IGNORECASE,
        )

    def test_to_dto(self, command_context: CommandContext):
        command = CreateRenewablesCluster(
            area_id="foo",
            cluster_name="Cluster1",
            parameters={"group": "Solar Thermal", "unitcount": 2, "nominalcapacity": 2400},
            command_context=command_context,
        )
        dto = command.to_dto()
        assert dto.dict() == {
            "action": "create_renewables_cluster",  # "renewables" with a final "s".
            "args": {
                "area_id": "foo",
                "cluster_name": "Cluster1",
                "parameters": {"group": "Solar Thermal", "nominalcapacity": "2400", "unitcount": "2"},
            },
            "id": None,
            "version": 1,
        }


def test_match(command_context: CommandContext):
    base = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        command_context=command_context,
    )
    other_match = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        command_context=command_context,
    )
    other_not_match = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="bar",
        parameters={},
        command_context=command_context,
    )
    other_other = RemoveRenewablesCluster(area_id="id", cluster_id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)

    assert base.match(other_match, equal=True)
    assert not base.match(other_not_match, equal=True)
    assert not base.match(other_other, equal=True)

    assert base.match_signature() == "create_renewables_cluster%foo%foo"
    assert base.get_inner_matrices() == []


def test_revert(command_context: CommandContext):
    base = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        command_context=command_context,
    )
    assert CommandReverter().revert(base, [], None) == [
        RemoveRenewablesCluster(
            area_id="foo",
            cluster_id="foo",
            command_context=command_context,
        )
    ]


def test_create_diff(command_context: CommandContext):
    base = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        command_context=command_context,
    )
    other_match = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={"a": "b"},
        command_context=command_context,
    )
    assert base.create_diff(other_match) == [
        UpdateConfig(
            target="input/renewables/clusters/foo/list/foo",
            data={"a": "b"},
            command_context=command_context,
        ),
    ]
