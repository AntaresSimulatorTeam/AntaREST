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
from typing import Any, Tuple

from antarest.core.exceptions import XpansionFileAlreadyExistsError
from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandOutput


def get_resource_dir(resource_type: XpansionResourceFileType) -> list[str]:
    if resource_type == XpansionResourceFileType.CONSTRAINTS:
        return ["user", "expansion", "constraints"]
    elif resource_type == XpansionResourceFileType.CAPACITIES:
        return ["user", "expansion", "capa"]
    elif resource_type == XpansionResourceFileType.WEIGHTS:
        return ["user", "expansion", "weights"]
    raise NotImplementedError(f"resource_type '{resource_type}' not implemented")


def apply_config_create_resource_commands(
    filename: str, resource_type: XpansionResourceFileType
) -> Tuple[CommandOutput, dict[str, Any]]:
    return (
        CommandOutput(
            status=True,
            message=f"Xpansion {resource_type.value} matrix '{filename}' has been successfully created.",
        ),
        {},
    )


def apply_create_resource_commands(
    filename: str, data: list[list[float]] | str | bytes, study_data: FileStudy, resource_type: XpansionResourceFileType
) -> CommandOutput:
    # checks the file doesn't already exist
    url = get_resource_dir(resource_type)
    if filename in study_data.tree.get(url):
        raise XpansionFileAlreadyExistsError(f"File '{filename}' already exists")

    study_data.tree.save(data=data, url=url + [filename])
    output, _ = apply_config_create_resource_commands(filename, resource_type)
    return output
