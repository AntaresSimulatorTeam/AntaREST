from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import (
    CommandReverter,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.remove_district import (
    RemoveDistrict,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command.update_district import (
    UpdateDistrict,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


def test_manage_district(
    empty_study: FileStudy, command_context: CommandContext
):
    study_path = empty_study.config.study_path
    area1 = "Area1"
    area1_id = transform_name_to_id(area1)

    area2 = "Area2"
    area2_id = transform_name_to_id(area2)

    area3 = "Area3"
    area3_id = transform_name_to_id(area3)

    CreateArea.parse_obj(
        {
            "area_name": area1,
            "command_context": command_context,
        }
    ).apply(empty_study)

    CreateArea.parse_obj(
        {
            "area_name": area2,
            "command_context": command_context,
        }
    ).apply(empty_study)

    CreateArea.parse_obj(
        {
            "area_name": area3,
            "command_context": command_context,
        }
    ).apply(empty_study)

    create_district1_command: ICommand = CreateDistrict(
        name="Two added zone",
        filter_items=[area1_id, area2_id],
        comments="First district",
        command_context=command_context,
    )
    output_d1 = create_district1_command.apply(
        study_data=empty_study,
    )
    assert output_d1.status
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    set_config = sets_config.get("two added zone")
    assert set(set_config["+"]) == {area1_id, area2_id}
    assert set_config["output"]
    assert set_config["comments"] == "First district"

    create_district2_command: ICommand = CreateDistrict(
        name="One subtracted zone",
        metadata={},
        base_filter=DistrictBaseFilter.add_all,
        filter_items=[area1_id],
        command_context=command_context,
    )
    output_d2 = create_district2_command.apply(
        study_data=empty_study,
    )
    assert output_d2.status
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    set_config = sets_config.get("one subtracted zone")
    assert set_config["-"] == [area1_id]
    assert set_config["apply-filter"] == "add-all"

    update_district2_command: ICommand = UpdateDistrict(
        id="one subtracted zone",
        metadata={},
        base_filter=DistrictBaseFilter.remove_all,
        filter_items=[area2_id],
        command_context=command_context,
    )
    output_ud2 = update_district2_command.apply(study_data=empty_study)
    assert output_ud2.status

    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    set_config = sets_config.get("one subtracted zone")
    assert set_config["+"] == [area2_id]
    assert set_config["apply-filter"] == "remove-all"

    create_district3_command: ICommand = CreateDistrict(
        name="Empty district without output",
        metadata={},
        output=False,
        command_context=command_context,
    )
    output_d3 = create_district3_command.apply(
        study_data=empty_study,
    )
    assert output_d3.status
    assert output_d2.status
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    set_config = sets_config.get("empty district without output")
    assert not set_config["output"]

    output_d3 = create_district3_command.apply(
        study_data=empty_study,
    )
    assert not output_d3.status

    read_config = build(empty_study.config.study_path, "")
    assert len(read_config.sets.keys()) == 4

    remove_district3_command: ICommand = RemoveDistrict(
        id="empty district without output", command_context=command_context
    )
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    assert len(sets_config.keys()) == 4
    remove_output_d3 = remove_district3_command.apply(
        study_data=empty_study,
    )
    assert remove_output_d3.status
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    assert len(sets_config.keys()) == 3


def test_match(command_context: CommandContext):
    base = CreateDistrict(
        name="foo",
        base_filter=DistrictBaseFilter.add_all,
        filter_items=["a", "b"],
        command_context=command_context,
    )
    other_match = CreateDistrict(
        name="foo",
        base_filter=DistrictBaseFilter.add_all,
        filter_items=["a", "b"],
        command_context=command_context,
    )
    other_not_match = CreateDistrict(
        name="foo2", command_context=command_context
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match, True)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "create_district%foo"
    assert base.get_inner_matrices() == []

    base = RemoveDistrict(id="id", command_context=command_context)
    other_match = RemoveDistrict(id="id", command_context=command_context)
    other_not_match = RemoveDistrict(id="id2", command_context=command_context)
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match, True)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_district%id"
    assert base.get_inner_matrices() == []


def test_revert(command_context: CommandContext):
    base = CreateDistrict(
        name="foo",
        base_filter=DistrictBaseFilter.add_all,
        filter_items=["a", "b"],
        command_context=command_context,
    )
    assert CommandReverter().revert(base, [], None) == [
        RemoveDistrict(id="foo", command_context=command_context)
    ]


def test_create_diff(command_context: CommandContext):
    base = CreateDistrict(
        name="foo",
        base_filter=DistrictBaseFilter.add_all,
        filter_items=["a", "b"],
        command_context=command_context,
    )
    other_match = CreateDistrict(
        name="foo",
        base_filter=DistrictBaseFilter.remove_all,
        filter_items=["c"],
        command_context=command_context,
    )
    assert base.create_diff(other_match) == [
        UpdateConfig(
            target="input/areas/sets/foo",
            data={
                "caption": "foo",
                "apply-filter": DistrictBaseFilter.remove_all.value,
                "+": ["c"],
                "output": True,
                "comments": "",
            },
            command_context=command_context,
        )
    ]

    base = RemoveDistrict(id="id", command_context=command_context)
    other_match = RemoveDistrict(id="id", command_context=command_context)
    assert base.create_diff(other_match) == []
