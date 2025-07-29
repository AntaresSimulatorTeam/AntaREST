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
from typing import Any

from antarest.core.exceptions import (
    ChildNotFoundError,
    XpansionCandidateDeletionError,
    XpansionFileAlreadyExistsError,
    XpansionFileNotFoundError,
)
from antarest.study.business.model.xpansion_model import (
    GetXpansionSettings,
    XpansionResourceFileType,
    XpansionSettingsUpdate,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandOutput, command_succeeded


def get_resource_dir(resource_type: XpansionResourceFileType) -> list[str]:
    if resource_type == XpansionResourceFileType.CONSTRAINTS:
        return ["user", "expansion", "constraints"]
    elif resource_type == XpansionResourceFileType.CAPACITIES:
        return ["user", "expansion", "capa"]
    elif resource_type == XpansionResourceFileType.WEIGHTS:
        return ["user", "expansion", "weights"]
    raise NotImplementedError(f"resource_type '{resource_type}' not implemented")


def apply_create_resource_commands(
    filename: str, data: list[list[float]] | str | bytes, study_data: FileStudy, resource_type: XpansionResourceFileType
) -> CommandOutput:
    # checks the file doesn't already exist
    url = get_resource_dir(resource_type)
    if filename in study_data.tree.get(url):
        raise XpansionFileAlreadyExistsError(f"File '{filename}' already exists")

    study_data.tree.save(data=data, url=url + [filename])
    return command_succeeded(
        message=f"Xpansion {resource_type.value} matrix '{filename}' has been successfully created."
    )


def get_xpansion_settings(file_study: FileStudy) -> GetXpansionSettings:
    config_obj = file_study.tree.get(["user", "expansion", "settings"])
    config_obj["sensitivity_config"] = get_xpansion_sensitivity(file_study)
    return GetXpansionSettings.from_config(config_obj)


def get_xpansion_sensitivity(file_study: FileStudy) -> dict[str, Any]:
    try:
        return file_study.tree.get(["user", "expansion", "sensitivity", "sensitivity_in"])
    except ChildNotFoundError:
        return {}


def checks_settings_are_correct_and_returns_fields_to_exclude(
    settings: XpansionSettingsUpdate, file_study: FileStudy
) -> set[str]:
    """
    Checks yearly_weights and additional_constraints fields.
    - If the attributes are given, it means that the user wants to select a file.
      It is therefore necessary to check that the file exists.
    - Else, it means the user want to deselect the additional constraints file,
     but he does not want to delete it from the expansion configuration folder.

    Returns:
        set[str] -- The fields to not save inside the ini.file
    """
    excludes = {"sensitivity_config"}
    for field in ["additional_constraints", "yearly_weights"]:
        if file := getattr(settings, field, None):
            file_type = field.split("_")[1]
            try:
                constraints_url = ["user", "expansion", file_type, file]
                file_study.tree.get(constraints_url)
            except ChildNotFoundError:
                msg = f"Additional {file_type} file '{file}' does not exist"
                raise XpansionFileNotFoundError(msg) from None
        else:
            excludes.add(field)

    return excludes


def checks_candidate_can_be_deleted(candidate_name: str, file_study: FileStudy) -> None:
    """
    Ensures the candidate isn't referenced inside the sensitivity file as a projection.
    """
    sensitivity_config = get_xpansion_sensitivity(file_study)
    projections = sensitivity_config.get("projection", {})
    if candidate_name in projections:
        raise XpansionCandidateDeletionError(file_study.config.study_id, candidate_name)
