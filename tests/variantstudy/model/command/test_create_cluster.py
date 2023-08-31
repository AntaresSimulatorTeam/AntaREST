import configparser

from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import CommandReverter
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.remove_cluster import RemoveCluster
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateCluster:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(self, empty_study: FileStudy, command_context: CommandContext):
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
            "group": "Other",
            "unitcount": "1",
            "nominalcapacity": "1000000",
            "marginal-cost": "30",
            "market-bid-cost": "30",
        }

        command = CreateCluster.parse_obj(
            {
                "area_id": area_id,
                "cluster_name": cluster_name,
                "parameters": parameters,
                "prepro": [[0]],
                "modulation": [[0]],
                "command_context": command_context,
            }
        )

        output = command.apply(empty_study)
        assert output.status

        clusters = configparser.ConfigParser()
        clusters.read(study_path / "input" / "thermal" / "clusters" / area_id / "list.ini")
        assert str(clusters[cluster_name]["name"]) == cluster_name
        assert str(clusters[cluster_name]["group"]) == parameters["group"]
        assert int(clusters[cluster_name]["unitcount"]) == int(parameters["unitcount"])
        assert float(clusters[cluster_name]["nominalcapacity"]) == float(parameters["nominalcapacity"])
        assert float(clusters[cluster_name]["marginal-cost"]) == float(parameters["marginal-cost"])
        assert float(clusters[cluster_name]["market-bid-cost"]) == float(parameters["market-bid-cost"])

        assert (study_path / "input" / "thermal" / "prepro" / area_id / cluster_id / "data.txt.link").exists()
        assert (study_path / "input" / "thermal" / "prepro" / area_id / cluster_id / "modulation.txt.link").exists()

        output = CreateCluster.parse_obj(
            {
                "area_id": area_id,
                "cluster_name": cluster_name,
                "parameters": parameters,
                "prepro": [[0]],
                "modulation": [[0]],
                "command_context": command_context,
            }
        ).apply(empty_study)
        assert not output.status

        output = CreateCluster.parse_obj(
            {
                "area_id": "non_existent_area",
                "cluster_name": cluster_name,
                "parameters": parameters,
                "prepro": [[0]],
                "modulation": [[0]],
                "command_context": command_context,
            }
        ).apply(empty_study)
        assert not output.status


def test_match(command_context: CommandContext):
    base = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        prepro=[[0]],
        modulation=[[0]],
        command_context=command_context,
    )
    other_match = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        prepro=[[0]],
        modulation=[[0]],
        command_context=command_context,
    )
    other_not_match = CreateCluster(
        area_id="foo",
        cluster_name="bar",
        parameters={},
        prepro=[[0]],
        modulation=[[0]],
        command_context=command_context,
    )
    other_other = RemoveCluster(area_id="id", cluster_id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "create_cluster%foo%foo"
    assert base.get_inner_matrices() == ["matrix_id", "matrix_id"]


def test_revert(command_context: CommandContext):
    base = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        prepro=[[0]],
        modulation=[[0]],
        command_context=command_context,
    )
    assert CommandReverter().revert(base, [], None) == [
        RemoveCluster(
            area_id="foo",
            cluster_id="foo",
            command_context=command_context,
        )
    ]


def test_create_diff(command_context: CommandContext):
    base = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={},
        prepro="a",
        modulation="b",
        command_context=command_context,
    )
    other_match = CreateCluster(
        area_id="foo",
        cluster_name="foo",
        parameters={"a": "b"},
        prepro="c",
        modulation="d",
        command_context=command_context,
    )
    assert base.create_diff(other_match) == [
        ReplaceMatrix(
            target=f"input/thermal/prepro/foo/foo/data",
            matrix="c",
            command_context=command_context,
        ),
        ReplaceMatrix(
            target=f"input/thermal/prepro/foo/foo/modulation",
            matrix="d",
            command_context=command_context,
        ),
        UpdateConfig(
            target=f"input/thermal/clusters/foo/list/foo",
            data={"a": "b"},
            command_context=command_context,
        ),
    ]
