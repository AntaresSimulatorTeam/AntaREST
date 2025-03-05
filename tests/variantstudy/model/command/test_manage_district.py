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

from antarest.core.serde.ini_reader import IniReader
from antarest.study.dao.file_study_dao import FileStudyTreeDao
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_district import (
    RemoveDistrict,
)
from antarest.study.storage.variantstudy.model.command.update_district import (
    UpdateDistrict,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def test_manage_district(empty_study: FileStudy, command_context: CommandContext):
    study_dao = FileStudyTreeDao(empty_study)
    area1 = "Area1"
    area1_id = transform_name_to_id(area1)

    area2 = "Area2"
    area2_id = transform_name_to_id(area2)

    area3 = "Area3"

    study_version = empty_study.config.version

    CreateArea.model_validate(
        {
            "area_name": area1,
            "command_context": command_context,
            "study_version": study_version,
        }
    ).apply(study_dao)

    CreateArea.model_validate(
        {
            "area_name": area2,
            "command_context": command_context,
            "study_version": study_version,
        }
    ).apply(study_dao)

    CreateArea.model_validate(
        {
            "area_name": area3,
            "command_context": command_context,
            "study_version": study_version,
        }
    ).apply(study_dao)

    create_district1_command: ICommand = CreateDistrict(
        name="Two added zone",
        filter_items=[area1_id, area2_id],
        comments="First district",
        command_context=command_context,
        study_version=study_version,
    )
    output_d1 = create_district1_command.apply(
        study_data=study_dao,
    )
    assert output_d1.status
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    set_config = sets_config.get("two added zone")
    assert set(set_config["+"]) == {area1_id, area2_id}
    assert set_config["output"]
    assert set_config["comments"] == "First district"

    create_district2_command: ICommand = CreateDistrict(
        name="One subtracted zone",
        base_filter=DistrictBaseFilter.add_all,
        filter_items=[area1_id],
        command_context=command_context,
        study_version=study_version,
    )
    output_d2 = create_district2_command.apply(
        study_data=study_dao,
    )
    assert output_d2.status
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    set_config = sets_config.get("one subtracted zone")
    assert set_config["-"] == [area1_id]
    assert set_config["apply-filter"] == "add-all"

    update_district2_command: ICommand = UpdateDistrict(
        id="one subtracted zone",
        base_filter=DistrictBaseFilter.remove_all,
        filter_items=[area2_id],
        command_context=command_context,
        study_version=study_version,
    )
    output_ud2 = update_district2_command.apply(study_data=study_dao)
    assert output_ud2.status

    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    set_config = sets_config.get("one subtracted zone")
    assert set_config["+"] == [area2_id]
    assert set_config["apply-filter"] == "remove-all"

    create_district3_command: ICommand = CreateDistrict(
        name="Empty district without output",
        output=False,
        command_context=command_context,
        study_version=study_version,
    )
    output_d3 = create_district3_command.apply(
        study_data=study_dao,
    )
    assert output_d3.status
    assert output_d2.status
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    set_config = sets_config.get("empty district without output")
    assert not set_config["output"]

    output_d3 = create_district3_command.apply(
        study_data=study_dao,
    )
    assert not output_d3.status

    read_config = build(empty_study.config.study_path, "")
    assert len(read_config.sets.keys()) == 4

    remove_district3_command: ICommand = RemoveDistrict(
        id="empty district without output",
        command_context=command_context,
        study_version=study_version,
    )
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    assert len(sets_config.keys()) == 4
    remove_output_d3 = remove_district3_command.apply(
        study_data=study_dao,
    )
    assert remove_output_d3.status
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    assert len(sets_config.keys()) == 3
