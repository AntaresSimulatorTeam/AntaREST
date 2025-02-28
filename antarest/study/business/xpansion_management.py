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

import contextlib
import http
import logging
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from pydantic import Field

from antarest.core.exceptions import (
    ChildNotFoundError,
    LinkNotFound,
    MatrixImportFailed,
    XpansionFileAlreadyExistsError,
)
from antarest.core.model import JSON
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.xpansion_model import (
    GetXpansionSettings,
    XpansionResourceFileType,
    XpansionSettingsUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import imports_matrix_from_bytes
from antarest.study.storage.variantstudy.model.command.create_xpansion_configuration import CreateXpansionConfiguration
from antarest.study.storage.variantstudy.model.command.create_xpansion_constraint import CreateXpansionConstraint
from antarest.study.storage.variantstudy.model.command.create_xpansion_matrix import (
    CreateXpansionCapacity,
    CreateXpansionWeight,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_xpansion_configuration import RemoveXpansionConfiguration
from antarest.study.storage.variantstudy.model.command.remove_xpansion_resource import (
    RemoveXpansionResource,
    checks_resource_deletion_is_allowed,
)
from antarest.study.storage.variantstudy.model.command.xpansion_common import get_resource_dir
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class XpansionCandidateDTO(AntaresBaseModel):
    # The id of the candidate is irrelevant, so it should stay hidden for the user
    # The names should be the section titles of the file, and the id should be removed
    name: str
    link: str
    annual_cost_per_mw: float = Field(alias="annual-cost-per-mw", ge=0)
    unit_size: Optional[float] = Field(default=None, alias="unit-size", ge=0)
    max_units: Optional[int] = Field(default=None, alias="max-units", ge=0)
    max_investment: Optional[float] = Field(default=None, alias="max-investment", ge=0)
    already_installed_capacity: Optional[int] = Field(default=None, alias="already-installed-capacity", ge=0)
    # this is obsolete (replaced by direct/indirect)
    link_profile: Optional[str] = Field(default=None, alias="link-profile")
    # this is obsolete (replaced by direct/indirect)
    already_installed_link_profile: Optional[str] = Field(default=None, alias="already-installed-link-profile")
    direct_link_profile: Optional[str] = Field(default=None, alias="direct-link-profile")
    indirect_link_profile: Optional[str] = Field(default=None, alias="indirect-link-profile")
    already_installed_direct_link_profile: Optional[str] = Field(
        default=None, alias="already-installed-direct-link-profile"
    )
    already_installed_indirect_link_profile: Optional[str] = Field(
        default=None, alias="already-installed-indirect-link-profile"
    )


class XpansionFileNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(http.HTTPStatus.NOT_FOUND, message)


class IllegalCharacterInNameError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(http.HTTPStatus.BAD_REQUEST, message)


class CandidateNameIsEmpty(HTTPException):
    def __init__(self) -> None:
        super().__init__(http.HTTPStatus.BAD_REQUEST)


class WrongLinkFormatError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(http.HTTPStatus.BAD_REQUEST, message)


class CandidateAlreadyExistsError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(http.HTTPStatus.BAD_REQUEST, message)


class BadCandidateFormatError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(http.HTTPStatus.BAD_REQUEST, message)


class CandidateNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(http.HTTPStatus.NOT_FOUND, message)


class XpansionManager:
    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def create_xpansion_configuration(self, study: StudyInterface) -> None:
        logger.info(f"Initiating xpansion configuration for study '{study.id}'")

        command = CreateXpansionConfiguration(command_context=self._command_context, study_version=study.version)
        study.add_commands([command])

    def delete_xpansion_configuration(self, study: StudyInterface) -> None:
        logger.info(f"Deleting xpansion configuration for study '{study.id}'")
        command = RemoveXpansionConfiguration(command_context=self._command_context, study_version=study.version)
        study.add_commands([command])

    def get_xpansion_settings(self, study: StudyInterface) -> GetXpansionSettings:
        logger.info(f"Getting xpansion settings for study '{study.id}'")
        file_study = study.get_files()
        config_obj = file_study.tree.get(["user", "expansion", "settings"])
        with contextlib.suppress(ChildNotFoundError):
            config_obj["sensitivity_config"] = file_study.tree.get(
                ["user", "expansion", "sensitivity", "sensitivity_in"]
            )
        return GetXpansionSettings.from_config(config_obj)

    def update_xpansion_settings(
        self, study: StudyInterface, new_xpansion_settings: XpansionSettingsUpdate
    ) -> GetXpansionSettings:
        logger.info(f"Updating xpansion settings for study '{study.id}'")

        actual_settings = self.get_xpansion_settings(study)
        settings_fields = new_xpansion_settings.model_dump(
            mode="json", exclude_none=True, exclude={"sensitivity_config"}
        )
        updated_settings = actual_settings.model_copy(deep=True, update=settings_fields)

        file_study = study.get_files()

        # Specific handling for yearly_weights and additional_constraints:
        # - If the attributes are given, it means that the user wants to select a file.
        #   It is therefore necessary to check that the file exists.
        # - Else, it means the user want to deselect the additional constraints file,
        #  but he does not want to delete it from the expansion configuration folder.
        excludes = {"sensitivity_config"}
        if constraints_file := new_xpansion_settings.additional_constraints:
            try:
                constraints_url = ["user", "expansion", "constraints", constraints_file]
                file_study.tree.get(constraints_url)
            except ChildNotFoundError:
                msg = f"Additional constraints file '{constraints_file}' does not exist"
                raise XpansionFileNotFoundError(msg) from None
        else:
            excludes.add("additional_constraints")

        if weights_file := new_xpansion_settings.yearly_weights:
            try:
                weights_url = ["user", "expansion", "weights", weights_file]
                file_study.tree.get(weights_url)
            except ChildNotFoundError:
                msg = f"Additional weights file '{weights_file}' does not exist"
                raise XpansionFileNotFoundError(msg) from None
        else:
            excludes.add("yearly_weights")

        config_obj = updated_settings.model_dump(mode="json", by_alias=True, exclude=excludes)
        file_study.tree.save(config_obj, ["user", "expansion", "settings"])

        if new_xpansion_settings.sensitivity_config:
            sensitivity_obj = new_xpansion_settings.sensitivity_config.model_dump(mode="json", by_alias=True)
            file_study.tree.save(sensitivity_obj, ["user", "expansion", "sensitivity", "sensitivity_in"])

        return self.get_xpansion_settings(study)

    @staticmethod
    def _assert_link_profile_are_files(
        file_study: FileStudy,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> None:
        for fieldname, filename in [
            ("link-profile", xpansion_candidate_dto.link_profile),
            (
                "already-installed-link-profile",
                xpansion_candidate_dto.already_installed_link_profile,
            ),
            (
                "direct-link-profile",
                xpansion_candidate_dto.direct_link_profile,
            ),
            (
                "indirect-direct-link-profile",
                xpansion_candidate_dto.indirect_link_profile,
            ),
            (
                "already-installed-direct-link-profile",
                xpansion_candidate_dto.already_installed_direct_link_profile,
            ),
            (
                "already-installed-indirect-link-profile",
                xpansion_candidate_dto.already_installed_indirect_link_profile,
            ),
        ]:
            if filename and not file_study.tree.get(
                [
                    "user",
                    "expansion",
                    "capa",
                    filename,
                ]
            ):
                raise XpansionFileNotFoundError(f"The '{fieldname}' file '{filename}' does not exist")

    @staticmethod
    def _assert_link_exist(
        file_study: FileStudy,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> None:
        if " - " not in xpansion_candidate_dto.link:
            raise WrongLinkFormatError("The link must be in the format 'area1 - area2'")
        area1, area2 = xpansion_candidate_dto.link.split(" - ")
        area_from, area_to = sorted([area1, area2])
        if area_to not in file_study.config.get_links(area_from):
            raise LinkNotFound(f"The link from '{area_from}' to '{area_to}' not found")

    @staticmethod
    def _assert_no_illegal_character_is_in_candidate_name(
        xpansion_candidate_name: str,
    ) -> None:
        illegal_chars = [
            " ",
            "\n",
            "\t",
            "\r",
            "\f",
            "\v",
            "-",
            "+",
            "=",
            ":",
            "[",
            "]",
            "(",
            ")",
        ]
        if xpansion_candidate_name.strip() == "":
            raise CandidateNameIsEmpty()
        for char in illegal_chars:
            if char in xpansion_candidate_name:
                raise IllegalCharacterInNameError(f"The character '{char}' is not allowed in the candidate name")

    @staticmethod
    def _assert_candidate_name_is_not_already_taken(candidates: JSON, xpansion_candidate_name: str) -> None:
        for candidate in candidates.values():
            if candidate["name"] == xpansion_candidate_name:
                raise CandidateAlreadyExistsError(f"The candidate '{xpansion_candidate_name}' already exists")

    @staticmethod
    def _assert_investment_candidate_is_valid(
        max_investment: Optional[float],
        max_units: Optional[int],
        unit_size: Optional[float],
    ) -> None:
        bool_max_investment = max_investment is None
        bool_max_units = max_units is None
        bool_unit_size = unit_size is None

        if not (
            (not bool_max_investment and bool_max_units and bool_unit_size)
            or (bool_max_investment and not bool_max_units and not bool_unit_size)
        ):
            raise BadCandidateFormatError(
                "The candidate is not well formatted."
                "\nIt should either contain max-investment or (max-units and unit-size)."
            )

    def _assert_candidate_is_correct(
        self,
        candidates: JSON,
        file_study: FileStudy,
        xpansion_candidate_dto: XpansionCandidateDTO,
        new_name: bool = False,
    ) -> None:
        logger.info("Checking given candidate is correct")
        self._assert_no_illegal_character_is_in_candidate_name(xpansion_candidate_dto.name)
        if new_name:
            self._assert_candidate_name_is_not_already_taken(candidates, xpansion_candidate_dto.name)
        self._assert_link_profile_are_files(file_study, xpansion_candidate_dto)
        self._assert_link_exist(file_study, xpansion_candidate_dto)
        self._assert_investment_candidate_is_valid(
            xpansion_candidate_dto.max_investment,
            xpansion_candidate_dto.max_units,
            xpansion_candidate_dto.unit_size,
        )
        assert xpansion_candidate_dto.annual_cost_per_mw

    def add_candidate(self, study: StudyInterface, xpansion_candidate: XpansionCandidateDTO) -> XpansionCandidateDTO:
        file_study = study.get_files()

        candidates_obj = file_study.tree.get(["user", "expansion", "candidates"])

        self._assert_candidate_is_correct(candidates_obj, file_study, xpansion_candidate)

        # Find next candidate id
        max_id = 2 if not candidates_obj else int(sorted(candidates_obj.keys()).pop()) + 2
        next_id = next(
            str(i) for i in range(1, max_id) if str(i) not in candidates_obj
        )  # The primary key is actually the name, the id does not matter and is never checked.

        logger.info(f"Adding candidate '{xpansion_candidate.name}' to study '{study.id}'")
        candidates_obj[next_id] = xpansion_candidate.model_dump(mode="json", by_alias=True, exclude_none=True)
        candidates_data = {"user": {"expansion": {"candidates": candidates_obj}}}
        file_study.tree.save(candidates_data)
        # Should we add a field in the study config containing the xpansion candidates like the links or the areas ?
        return self.get_candidate(study, xpansion_candidate.name)

    def get_candidate(self, study: StudyInterface, candidate_name: str) -> XpansionCandidateDTO:
        logger.info(f"Getting candidate '{candidate_name}' of study '{study.id}'")
        # This takes the first candidate with the given name and not the id, because the name is the primary key.
        file_study = study.get_files()
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        try:
            candidate = next(c for c in candidates.values() if c["name"] == candidate_name)
            return XpansionCandidateDTO(**candidate)

        except StopIteration:
            raise CandidateNotFoundError(f"The candidate '{candidate_name}' does not exist")

    def get_candidates(self, study: StudyInterface) -> List[XpansionCandidateDTO]:
        logger.info(f"Getting all candidates of study {study.id}")
        file_study = study.get_files()
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        return [XpansionCandidateDTO(**c) for c in candidates.values()]

    def update_candidate(
        self,
        study: StudyInterface,
        candidate_name: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> None:
        file_study = study.get_files()

        candidates = file_study.tree.get(["user", "expansion", "candidates"])

        new_name = candidate_name != xpansion_candidate_dto.name
        self._assert_candidate_is_correct(candidates, file_study, xpansion_candidate_dto, new_name=new_name)

        logger.info(f"Checking candidate {candidate_name} exists")
        for candidate_id, candidate in candidates.items():
            if candidate["name"] == candidate_name:
                logger.info(f"Updating candidate '{candidate_name}' of study '{study.id}'")
                candidates[candidate_id] = xpansion_candidate_dto.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                )
                file_study.tree.save(candidates, ["user", "expansion", "candidates"])
                return
        raise CandidateNotFoundError(f"The candidate '{xpansion_candidate_dto.name}' does not exist")

    def delete_candidate(self, study: StudyInterface, candidate_name: str) -> None:
        file_study = study.get_files()

        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        candidate_id = next(
            candidate_id for candidate_id, candidate in candidates.items() if candidate["name"] == candidate_name
        )

        logger.info(f"Deleting candidate '{candidate_name}' from study '{study.id}'")
        file_study.tree.delete(["user", "expansion", "candidates", candidate_id])

    def update_xpansion_constraints_settings(
        self, study: StudyInterface, constraints_file_name: str
    ) -> GetXpansionSettings:
        # Make sure filename is not `None`, because `None` values are ignored by the update.
        constraints_file_name = constraints_file_name or ""
        # noinspection PyArgumentList
        args = {"additional_constraints": constraints_file_name}
        xpansion_settings = XpansionSettingsUpdate.model_validate(args)
        return self.update_xpansion_settings(study, xpansion_settings)

    def add_resource(
        self,
        study: StudyInterface,
        resource_type: XpansionResourceFileType,
        file: UploadFile,
    ) -> None:
        filename = file.filename
        logger.info(f"Adding xpansion {resource_type} resource file {filename} to study '{study.id}'")

        # checks the file doesn't already exist
        keys = get_resource_dir(resource_type)
        file_study = study.get_files()
        if filename in file_study.tree.get(keys):
            raise XpansionFileAlreadyExistsError(f"File '{filename}' already exists")

        # parses the content
        content = file.file.read()
        if isinstance(content, str):
            content = content.encode(encoding="utf-8")

        # creates the command
        if resource_type == XpansionResourceFileType.CONSTRAINTS:
            command: ICommand = CreateXpansionConstraint(
                filename=filename, data=content, command_context=self._command_context, study_version=study.version
            )
        else:
            matrix = imports_matrix_from_bytes(content)
            if matrix is None:
                raise MatrixImportFailed(f"Could not parse the matrix corresponding to file {filename}")
            matrix = matrix.reshape((1, 0)) if matrix.size == 0 else matrix
            matrix = matrix.tolist()

            if resource_type == XpansionResourceFileType.WEIGHTS:
                command = CreateXpansionWeight(
                    filename=filename, matrix=matrix, command_context=self._command_context, study_version=study.version
                )
            elif resource_type == XpansionResourceFileType.CAPACITIES:
                command = CreateXpansionCapacity(
                    filename=filename, matrix=matrix, command_context=self._command_context, study_version=study.version
                )
            else:
                raise NotImplementedError(f"resource_type '{resource_type}' not implemented")

        study.add_commands([command])

    def delete_resource(
        self,
        study: StudyInterface,
        resource_type: XpansionResourceFileType,
        filename: str,
    ) -> None:
        file_study = study.get_files()
        logger.info(f"Checking xpansion file '{filename}' is not used in study '{file_study.config.study_id}'")
        checks_resource_deletion_is_allowed(resource_type, filename, file_study)
        logger.info(f"Deleting xpansion resource {filename} for study '{study.id}'")
        command = RemoveXpansionResource(
            resource_type=resource_type,
            filename=filename,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def get_resource_content(
        self,
        study: StudyInterface,
        resource_type: XpansionResourceFileType,
        filename: str,
    ) -> JSON | bytes:
        logger.info(f"Getting xpansion {resource_type} resource file '{filename}' from study '{study.id}'")
        file_study = study.get_files()
        return file_study.tree.get(get_resource_dir(resource_type) + [filename])

    def list_resources(self, study: StudyInterface, resource_type: XpansionResourceFileType) -> List[str]:
        logger.info(f"Getting all xpansion {resource_type} files from study '{study.id}'")
        file_study = study.get_files()
        try:
            return sorted([filename for filename in file_study.tree.get(get_resource_dir(resource_type)).keys()])
        except ChildNotFoundError:
            return []
