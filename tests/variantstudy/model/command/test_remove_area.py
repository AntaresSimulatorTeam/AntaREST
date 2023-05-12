import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.study_upgrader import upgrade_study
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
    @pytest.mark.parametrize("version", [810, 840])
    def test_apply(
        self,
        empty_study: FileStudy,
        command_context: CommandContext,
        version: int,
    ):
        # noinspection SpellCheckingInspection
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

        area_name = "Area"
        area_id = transform_name_to_id(area_name)
        create_area_command: ICommand = CreateArea.parse_obj(
            {
                "area_name": area_name,
                "command_context": command_context,
            }
        )
        output = create_area_command.apply(study_data=empty_study)
        assert output.status

        create_district_command = CreateDistrict(
            name="foo",
            base_filter=DistrictBaseFilter.add_all,
            filter_items=[area_id],
            command_context=command_context,
        )
        output = create_district_command.apply(study_data=empty_study)
        assert output.status

        ########################################################################################

        upgrade_study(empty_study.config.study_path, str(version))

        empty_study_cfg = empty_study.tree.get(depth=999)
        if version >= 830:
            empty_study_cfg["input"]["areas"][area_id]["adequacy_patch"] = {
                "adequacy-patch": {"adequacy-patch-mode": "outside"}
            }
            empty_study_cfg["input"]["links"][area_id]["capacities"] = {}

        area_name2 = "Area2"
        area_id2 = transform_name_to_id(area_name2)

        empty_study.config.version = version
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

        # noinspection SpellCheckingInspection
        create_cluster_command = CreateCluster.parse_obj(
            {
                "area_id": area_id2,
                "cluster_name": "cluster",
                "parameters": {
                    "group": "Other",
                    "unitcount": "1",
                    "nominalcapacity": "1000000",
                    "marginal-cost": "30",
                    "market-bid-cost": "30",
                },
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

        actual_cfg = empty_study.tree.get(depth=999)
        assert actual_cfg == empty_study_cfg


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


def test_create_diff(command_context: CommandContext):
    base = RemoveArea(id="foo", command_context=command_context)
    other_match = RemoveArea(id="foo", command_context=command_context)
    assert base.create_diff(other_match) == []
