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

from antarest.core.exceptions import (
    AreaNotFound,
    CandidateAlreadyExistsError,
    LinkNotFound,
    XpansionFileAlreadyExistsError,
    XpansionFileNotFoundError,
)
from antarest.study.business.model.xpansion_model import XpansionCandidateInternal, XpansionResourceFileType
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


def assert_xpansion_candidate_name_is_not_already_taken(candidates: dict[str, Any], candidate_name: str) -> None:
    for candidate in candidates.values():
        if candidate["name"] == candidate_name:
            raise CandidateAlreadyExistsError(f"The candidate '{candidate_name}' already exists")


def assert_link_profile_are_files(file_study: FileStudy, xpansion_candidate_dto: XpansionCandidateInternal) -> None:
    existing_files = file_study.tree.get(["user", "expansion", "capa"])
    for attr in [
        "link_profile",
        "already_installed_link_profile",
        "direct_link_profile",
        "indirect_link_profile",
        "already_installed_direct_link_profile",
        "already_installed_indirect_link_profile",
    ]:
        if link_file := getattr(xpansion_candidate_dto, attr, None):
            if link_file not in existing_files:
                raise XpansionFileNotFoundError(f"The '{attr}' file '{link_file}' does not exist")


def assert_link_exist(file_study: FileStudy, xpansion_candidate_dto: XpansionCandidateInternal) -> None:
    area1, area2 = xpansion_candidate_dto.link.split(" - ")
    area_from, area_to = sorted([area1, area2])
    if area_from not in file_study.config.areas:
        raise AreaNotFound(area_from)
    if area_to not in file_study.config.get_links(area_from):
        raise LinkNotFound(f"The link from '{area_from}' to '{area_to}' not found")


def assert_candidate_is_correct(
    existing_candidates: dict[str, Any], file_study: FileStudy, candidate: XpansionCandidateInternal
) -> None:
    assert_xpansion_candidate_name_is_not_already_taken(existing_candidates, candidate.name)
    assert_link_profile_are_files(file_study, candidate)
    assert_link_exist(file_study, candidate)
