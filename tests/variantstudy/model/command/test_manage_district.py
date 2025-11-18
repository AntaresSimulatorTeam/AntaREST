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
from antarest.study.business.model.district_model import DistrictApplyFilter, DistrictCreation, DistrictUpdate
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_district import CreateDistrict
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_district import RemoveDistrict
from antarest.study.storage.variantstudy.model.command.update_district import UpdateDistrict
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def test_manage_district(empty_study_810: FileStudy, command_context: CommandContext) -> None:
    empty_study = empty_study_810
    study_dao = FileStudyTreeDao(empty_study, command_context.generator_matrix_constants, command_context.blob_service)
    area1 = "Area1"
    area1_id = transform_name_to_id(area1)

    area2 = "Area2"
    area2_id = transform_name_to_id(area2)

    area3 = "Area3"

    study_version = empty_study.config.version

    CreateArea.model_validate(
        {"area_name": area1, "command_context": command_context, "study_version": study_version}
    ).apply(study_dao)

    CreateArea.model_validate(
        {"area_name": area2, "command_context": command_context, "study_version": study_version}
    ).apply(study_dao)

    CreateArea.model_validate(
        {"area_name": area3, "command_context": command_context, "study_version": study_version}
    ).apply(study_dao)

    # create district with two added areas
    create_district1_command: ICommand = CreateDistrict(
        parameters=DistrictCreation(
            name="Two added zone",
            # duplication here is intentional, it should be handled by the command
            areas=[area1_id, area2_id, area2_id],
            comments="First district",
        ),
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

    # create district with one subtracted area, apply-filter set to add-all
    create_district2_command: ICommand = CreateDistrict(
        parameters=DistrictCreation(
            name="One subtracted zone",
            apply_filter=DistrictApplyFilter.add_all,
            areas=[area1_id],
        ),
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

    # update district to remove area1 and keep area2, apply-filter set to remove-all
    update_district2_command: ICommand = UpdateDistrict(
        id="one subtracted zone",
        parameters=DistrictUpdate(apply_filter=DistrictApplyFilter.remove_all, areas=[area2_id]),
        command_context=command_context,
        study_version=study_version,
    )
    output_ud2 = update_district2_command.apply(study_data=study_dao)
    assert output_ud2.status

    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    set_config = sets_config.get("one subtracted zone")
    assert set_config["+"] == [area2_id]
    assert set_config["apply-filter"] == "remove-all"

    # case create empty district with output false
    create_district3_command: ICommand = CreateDistrict(
        parameters=DistrictCreation(name="Empty district without output", output=False),
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

    # case where district already exists
    output_d3 = create_district3_command.apply(
        study_data=study_dao,
    )
    assert not output_d3.status

    # case create district with invalid area
    create_district4_command: ICommand = CreateDistrict(
        parameters=DistrictCreation(name="district with invalid area", output=False, areas=["unknown_area"]),
        command_context=command_context,
        study_version=study_version,
    )
    output_d4 = create_district4_command.apply(
        study_data=study_dao,
    )
    assert not output_d4.status
    assert output_d4.message == "District 'district with invalid area' has invalid areas: ['unknown_area']"

    # case update district with invalid area
    update_district5_command: ICommand = UpdateDistrict(
        id="one subtracted zone",
        parameters=DistrictUpdate(areas=["unknown_area"]),
        command_context=command_context,
        study_version=study_version,
    )
    output_d5 = update_district5_command.apply(
        study_data=study_dao,
    )
    assert not output_d5.status
    assert output_d5.message == "District 'one subtracted zone' has invalid areas: ['unknown_area']"

    read_config = build(empty_study.config.study_path, "")
    assert len(read_config.districts.keys()) == 4

    # case remove district
    remove_district3_command: ICommand = RemoveDistrict(
        id="empty district without output", command_context=command_context, study_version=study_version
    )
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    assert len(sets_config.keys()) == 4
    remove_output_d3 = remove_district3_command.apply(
        study_data=study_dao,
    )
    assert remove_output_d3.status
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    assert len(sets_config.keys()) == 3

    # case update district with empty area
    update_district6_command: ICommand = UpdateDistrict(
        id="one subtracted zone",
        parameters=DistrictUpdate(areas=[]),
        command_context=command_context,
        study_version=study_version,
    )
    output_d6 = update_district6_command.apply(
        study_data=study_dao,
    )
    assert output_d6.status
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    set_config = sets_config.get("one subtracted zone")
    assert "+" not in set_config
    assert "-" not in set_config

    # case update district, set back apply_filter to add-all and areas to area1
    update_district7_command: ICommand = UpdateDistrict(
        id="one subtracted zone",
        parameters=DistrictUpdate(
            output=True, areas=["area1"], apply_filter=DistrictApplyFilter.add_all, comments="basic comment"
        ),
        command_context=command_context,
        study_version=study_version,
    )
    output_d7 = update_district7_command.apply(
        study_data=study_dao,
    )
    assert output_d7.status
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    set_config = sets_config.get("one subtracted zone")
    assert set_config["-"] == ["area1"]
    assert "+" not in set_config
    assert set_config["apply-filter"] == "add-all"
    assert set_config["output"]
    assert set_config["comments"] == "basic comment"

    # This test covers a bug where, if the initial state was "add-filter" and the update command
    # omitted the "apply filter" field, applying the command incorrectly reset "apply filter" to "remove-all".
    update_district8_command: ICommand = UpdateDistrict(
        id="one subtracted zone",
        parameters=DistrictUpdate(output=False, comments="next gen comment"),
        command_context=command_context,
        study_version=study_version,
    )
    output_d8 = update_district8_command.apply(
        study_data=study_dao,
    )
    assert output_d8.status
    sets_config = IniReader(["+", "-"]).read(empty_study.config.study_path / "input/areas/sets.ini")
    set_config = sets_config.get("one subtracted zone")
    assert set_config["-"] == ["area1"]
    assert "+" not in set_config
    assert set_config["apply-filter"] == "add-all"
    assert not set_config["output"]
    assert set_config["comments"] == "next gen comment"
