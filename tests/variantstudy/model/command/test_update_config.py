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

import json

import pytest

from antarest.core.serde.ini_reader import read_ini
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.mark.unit_test
def test_update_config(empty_study_880: FileStudy, command_context: CommandContext):
    empty_study = empty_study_880
    study_path = empty_study.config.study_path
    study_version = empty_study.config.version
    area1 = "Area1"
    area1_id = transform_name_to_id(area1)

    CreateArea.model_validate(
        {"area_name": area1, "command_context": command_context, "study_version": study_version}
    ).apply(empty_study)

    update_settings_command = UpdateConfig(
        target="settings/generaldata/optimization/simplex-range",
        data="day",
        command_context=command_context,
        study_version=study_version,
    )
    output = update_settings_command.apply(empty_study)
    assert output.status
    generaldata = read_ini(study_path / "settings/generaldata.ini")
    assert generaldata["optimization"]["simplex-range"] == "day"
    assert generaldata["optimization"]["transmission-capacities"]

    update_settings_command = UpdateConfig(
        target=f"input/areas/{area1_id}/optimization/nodal optimization/other-dispatchable-power",
        data=False,
        command_context=command_context,
        study_version=study_version,
    )
    output = update_settings_command.apply(empty_study)
    assert output.status
    area_config = read_ini(study_path / f"input/areas/{area1_id}/optimization.ini")
    assert not area_config["nodal optimization"]["other-dispatchable-power"]

    # test UpdateConfig with byte object which is necessary with the API PUT /v1/studies/{uuid}/raw
    data = json.dumps({"first_layer": {"0": "Nothing"}}).encode("utf-8")
    command = UpdateConfig(
        target="layers/layers", data=data, command_context=command_context, study_version=study_version
    )
    command.apply(empty_study)
    layers = read_ini(study_path / "layers/layers.ini")
    assert layers == {"first_layer": {"0": "Nothing"}}
    new_data = json.dumps({"1": False}).encode("utf-8")
    command = UpdateConfig(
        target="layers/layers/first_layer", data=new_data, command_context=command_context, study_version=study_version
    )
    command.apply(empty_study)
    layers = read_ini(study_path / "layers/layers.ini")
    assert layers == {"first_layer": {"1": False}}
