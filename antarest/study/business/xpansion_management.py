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
import logging
from typing import List

from fastapi import UploadFile

from antarest.core.exceptions import (
    CandidateNotFoundError,
    ChildNotFoundError,
    FileImportFailed,
    MatrixImportFailed,
    XpansionFileAlreadyExistsError,
    XpansionFileNotFoundError,
)
from antarest.core.model import JSON
from antarest.study.business.model.xpansion_model import (
    GetXpansionSettings,
    XpansionCandidateDTO,
    XpansionResourceFileType,
    XpansionSettingsUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import imports_matrix_from_bytes
from antarest.study.storage.variantstudy.model.command.create_xpansion_candidate import CreateXpansionCandidate
from antarest.study.storage.variantstudy.model.command.create_xpansion_configuration import CreateXpansionConfiguration
from antarest.study.storage.variantstudy.model.command.create_xpansion_constraint import CreateXpansionConstraint
from antarest.study.storage.variantstudy.model.command.create_xpansion_matrix import (
    CreateXpansionCapacity,
    CreateXpansionWeight,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_xpansion_candidate import RemoveXpansionCandidate
from antarest.study.storage.variantstudy.model.command.remove_xpansion_configuration import RemoveXpansionConfiguration
from antarest.study.storage.variantstudy.model.command.remove_xpansion_resource import (
    RemoveXpansionResource,
    checks_resource_deletion_is_allowed,
)
from antarest.study.storage.variantstudy.model.command.update_xpansion_candidate import ReplaceXpansionCandidate
from antarest.study.storage.variantstudy.model.command.xpansion_common import assert_link_exist, get_resource_dir
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


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

    def add_candidate(self, study: StudyInterface, xpansion_candidate: XpansionCandidateDTO) -> XpansionCandidateDTO:
        logger.info(f"Adding candidate '{xpansion_candidate.name}' to study '{study.id}'")

        file_study = study.get_files()
        internal_candidate = xpansion_candidate.to_internal_model()
        assert_link_exist(file_study, internal_candidate)

        command = CreateXpansionCandidate(
            candidate=internal_candidate, command_context=self._command_context, study_version=study.version
        )
        study.add_commands([command])

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
        internal_candidate = xpansion_candidate_dto.to_internal_model()
        command = ReplaceXpansionCandidate(
            candidate_name=candidate_name,
            new_properties=internal_candidate,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def delete_candidate(self, study: StudyInterface, candidate_name: str) -> None:
        logger.info(f"Deleting candidate '{candidate_name}' from study '{study.id}'")

        command = RemoveXpansionCandidate(
            candidate_name=candidate_name,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def update_xpansion_constraints_settings(
        self, study: StudyInterface, constraints_file_name: str
    ) -> GetXpansionSettings:
        # Make sure filename is not `None`, because `None` values are ignored by the update.
        constraints_file_name = constraints_file_name or ""
        # noinspection PyArgumentList
        args = {"additional_constraints": constraints_file_name}
        xpansion_settings = XpansionSettingsUpdate.model_validate(args)
        return self.update_xpansion_settings(study, xpansion_settings)

    def _create_add_resource_command(
        self, study: StudyInterface, filename: str, content: bytes, resource_type: XpansionResourceFileType
    ) -> ICommand:
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
        return command

    def add_resource(
        self,
        study: StudyInterface,
        resource_type: XpansionResourceFileType,
        file: UploadFile,
    ) -> None:
        filename = file.filename
        if not filename:
            raise FileImportFailed("A filename is required")
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
        command = self._create_add_resource_command(study, filename, content, resource_type)

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
