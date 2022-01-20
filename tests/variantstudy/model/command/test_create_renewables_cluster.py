import configparser

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
    ENR_MODELLING,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import (
    CreateRenewablesCluster,
)
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import (
    RemoveRenewablesCluster,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestCreateRenewablesCluster:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self, empty_study: FileStudy, command_context: CommandContext
    ):
        empty_study.config.enr_modelling = ENR_MODELLING.CLUSTERS.value
        study_path = empty_study.config.study_path
        area_name = "Area"
        area_id = transform_name_to_id(area_name, lower=True)
        cluster_name = "cluster_name"
        cluster_id = transform_name_to_id(cluster_name, lower=True)

        CreateArea.parse_obj(
            {
                "area_name": area_name,
                "command_context": command_context,
            }
        ).apply(empty_study)

        parameters = {
            "name": cluster_name,
            "ts-interpretation": "power-generation",
        }

        command = CreateRenewablesCluster.parse_obj(
            {
                "area_id": area_id,
                "cluster_name": cluster_name,
                "parameters": parameters,
                "command_context": command_context,
            }
        )

        output = command.apply(empty_study)
        assert output.status

        clusters = configparser.ConfigParser()
        clusters.read(
            study_path
            / "input"
            / "renewables"
            / "clusters"
            / area_id
            / "list.ini"
        )
        assert str(clusters[cluster_name]["name"]) == cluster_name
        assert (
            str(clusters[cluster_name]["ts-interpretation"])
            == parameters["ts-interpretation"]
        )

        output = CreateRenewablesCluster.parse_obj(
            {
                "area_id": area_id,
                "cluster_name": cluster_name,
                "parameters": parameters,
                "command_context": command_context,
            }
        ).apply(empty_study)
        assert not output.status

        output = CreateRenewablesCluster.parse_obj(
            {
                "area_id": "non_existent_area",
                "cluster_name": cluster_name,
                "parameters": parameters,
                "command_context": command_context,
            }
        ).apply(empty_study)
        assert not output.status


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
    other_other = RemoveRenewablesCluster(
        area_id="id", cluster_id="id", command_context=command_context
    )
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "create_cluster%foo%foo"
    assert base.get_inner_matrices() == []


def test_revert(command_context: CommandContext):
    base = CreateRenewablesCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        command_context=command_context,
    )
    assert base.revert([], None) == [
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
            target=f"input/renewables/clusters/foo/list/foo",
            data={"a": "b"},
            command_context=command_context,
        ),
    ]
