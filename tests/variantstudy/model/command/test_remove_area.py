from unittest.mock import Mock, patch

from checksumdir import dirhash

from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.variantstudy.business.command_reverter import (
    CommandReverter,
)
from antarest.study.storage.variantstudy.model.command.common import (
    TimeStep,
    BindingConstraintOperator,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.remove_district import (
    RemoveDistrict,
)
from antarest.study.storage.variantstudy.model.command.remove_link import (
    RemoveLink,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestRemoveArea:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self,
        empty_study: FileStudy,
        command_context: CommandContext,
    ):
        bd_config = IniReader().read(
            empty_study.config.study_path
            / "input"
            / "bindingconstraints"
            / "bindingconstraints.ini"
        )

        area_name = "Area"
        area_id = transform_name_to_id(area_name)
        area_name2 = "Area2"
        area_id2 = transform_name_to_id(area_name2)
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

        create_area_command: ICommand = CreateArea.parse_obj(
            {
                "area_name": area_name,
                "command_context": command_context,
            }
        )
        output = create_area_command.apply(study_data=empty_study)
        assert output.status

        parameters = {
            "group": "Other",
            "unitcount": "1",
            "nominalcapacity": "1000000",
            "marginal-cost": "30",
            "market-bid-cost": "30",
        }

        create_district_command = CreateDistrict(
            name="foo",
            base_filter=DistrictBaseFilter.add_all,
            filter_items=[area_id],
            command_context=command_context,
        )
        output = create_district_command.apply(study_data=empty_study)
        assert output.status

        ########################################################################################

        empty_study_hash = dirhash(empty_study.config.study_path, "md5")

        create_area_command: ICommand = CreateArea.parse_obj(
            {
                "area_name": area_name2,
                "command_context": command_context,
            }
        )
        output = create_area_command.apply(study_data=empty_study)
        assert output.status

        create_link_command: ICommand = CreateLink(
            area1=area_id,
            area2=area_id2,
            parameters={},
            command_context=command_context,
            series=[[0]],
        )
        output = create_link_command.apply(study_data=empty_study)
        assert output.status

        create_cluster_command = CreateCluster.parse_obj(
            {
                "area_id": area_id2,
                "cluster_name": "cluster",
                "parameters": parameters,
                "prepro": [[0]],
                "modulation": [[0]],
                "command_context": command_context,
            }
        )
        output = create_cluster_command.apply(study_data=empty_study)
        assert output.status

        bind1_cmd = CreateBindingConstraint(
            name="BD 2",
            time_step=TimeStep.HOURLY,
            operator=BindingConstraintOperator.LESS,
            coeffs={
                f"{area_id}%{area_id2}": [400, 30],
                f"{area_id2}.cluster": [400, 30],
            },
            comments="Hello",
            command_context=command_context,
        )
        output = bind1_cmd.apply(study_data=empty_study)
        assert output.status

        remove_district_command = RemoveDistrict(
            id="foo",
            command_context=command_context,
        )
        output = remove_district_command.apply(study_data=empty_study)
        assert output.status

        create_district_command = CreateDistrict(
            name="foo",
            base_filter=DistrictBaseFilter.add_all,
            filter_items=[area_id, area_id2],
            command_context=command_context,
        )
        output = create_district_command.apply(study_data=empty_study)
        assert output.status

        remove_area_command: ICommand = RemoveArea.parse_obj(
            {
                "id": transform_name_to_id(area_name2),
                "command_context": command_context,
            }
        )
        output = remove_area_command.apply(study_data=empty_study)
        assert output.status

        assert (
            dirhash(empty_study.config.study_path, "md5") == empty_study_hash
        )


def test_match(command_context: CommandContext):
    base = RemoveArea(id="foo", command_context=command_context)
    other_match = RemoveArea(id="foo", command_context=command_context)
    other_not_match = RemoveArea(id="bar", command_context=command_context)
    other_other = RemoveLink(
        area1="id", area2="id2", command_context=command_context
    )
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_area%foo"
    assert base.get_inner_matrices() == []


@patch(
    "antarest.study.storage.variantstudy.business.command_extractor.CommandExtractor.extract_area",
)
def test_revert(mock_extract_area, command_context: CommandContext):
    base = RemoveArea(id="foo", command_context=command_context)
    assert CommandReverter().revert(
        base,
        [CreateArea(area_name="foo", command_context=command_context)],
        None,
    ) == [CreateArea(area_name="foo", command_context=command_context)]
    study = FileStudy(config=Mock(), tree=Mock())
    mock_extract_area.return_value = (
        [Mock()],
        [Mock()],
    )
    mock_extract_area.side_effect = ChildNotFoundError("")
    CommandReverter().revert(base, [], study)
    mock_extract_area.assert_called_with(study, "foo")


def test_create_diff(command_context: CommandContext):
    base = RemoveArea(id="foo", command_context=command_context)
    other_match = RemoveArea(id="foo", command_context=command_context)
    assert base.create_diff(other_match) == []
