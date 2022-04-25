from unittest.mock import Mock, patch

from checksumdir import dirhash

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
    ENR_MODELLING,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import (
    CreateRenewablesCluster,
)
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import (
    RemoveRenewablesCluster,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestRemoveRenewablesCluster:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self, empty_study: FileStudy, command_context: CommandContext
    ):
        empty_study.config.enr_modelling = ENR_MODELLING.CLUSTERS.value
        area_name = "Area_name"
        area_id = transform_name_to_id(area_name)
        cluster_name = "cluster_name"
        cluster_id = transform_name_to_id(cluster_name)

        CreateArea.parse_obj(
            {
                "area_name": area_name,
                "command_context": command_context,
            }
        ).apply(empty_study)

        hash_before_cluster = dirhash(empty_study.config.study_path, "md5")

        CreateRenewablesCluster(
            area_id=area_id,
            cluster_name=cluster_name,
            parameters={
                "name": "name",
                "ts-interpretation": "power-generation",
            },
            command_context=command_context,
        ).apply(empty_study)

        output = RemoveRenewablesCluster(
            area_id=area_id,
            cluster_id=cluster_id,
            command_context=command_context,
        ).apply(empty_study)

        assert output.status
        assert (
            dirhash(empty_study.config.study_path, "md5")
            == hash_before_cluster
        )

        output = RemoveRenewablesCluster(
            area_id="non_existent_area",
            cluster_id=cluster_id,
            command_context=command_context,
        ).apply(empty_study)
        assert not output.status

        output = RemoveRenewablesCluster(
            area_id=area_name,
            cluster_id="non_existent_cluster",
            command_context=command_context,
        ).apply(empty_study)
        assert not output.status


def test_match(command_context: CommandContext):
    base = RemoveRenewablesCluster(
        area_id="foo", cluster_id="bar", command_context=command_context
    )
    other_match = RemoveRenewablesCluster(
        area_id="foo", cluster_id="bar", command_context=command_context
    )
    other_not_match = RemoveRenewablesCluster(
        area_id="foo", cluster_id="baz", command_context=command_context
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_renewables_cluster%bar%foo"
    assert base.get_inner_matrices() == []


@patch(
    "antarest.study.storage.variantstudy.model.command.utils_extractor.CommandExtraction.extract_renewables_cluster",
)
def test_revert(
    mock_extract_renewables_cluster, command_context: CommandContext
):
    base = RemoveRenewablesCluster(
        area_id="foo", cluster_id="bar", command_context=command_context
    )
    assert base.revert(
        [
            CreateRenewablesCluster(
                area_id="foo",
                cluster_name="bar",
                parameters={},
                command_context=command_context,
            )
        ],
        None,
    ) == [
        CreateRenewablesCluster(
            area_id="foo",
            cluster_name="bar",
            parameters={},
            command_context=command_context,
        )
    ]
    study = FileStudy(config=Mock(), tree=Mock())
    mock_extract_renewables_cluster.side_effect = ChildNotFoundError("")
    base.revert([], study)
    mock_extract_renewables_cluster.assert_called_with(study, "foo", "bar")


def test_create_diff(command_context: CommandContext):
    base = RemoveRenewablesCluster(
        area_id="foo", cluster_id="bar", command_context=command_context
    )
    other_match = RemoveRenewablesCluster(
        area_id="foo", cluster_id="bar", command_context=command_context
    )
    assert base.create_diff(other_match) == []
