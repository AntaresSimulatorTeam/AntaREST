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
import io
import logging
import shutil
import zipfile
from typing import Any, List, MutableMapping, Optional, Sequence

from fastapi import UploadFile
from pydantic import Field, ValidationError, field_validator, model_validator

from antarest.core.exceptions import (
    BadZipBinary,
    CandidateNotFoundError,
    ChildNotFoundError,
    FileAlreadyExistsError,
    FileCurrentlyUsedInSettings,
    XpansionFileNotFoundError,
)
from antarest.core.model import JSON
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.model.xpansion_model import XpansionCandidateDTO
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.utils import fix_study_root
from antarest.study.storage.variantstudy.model.command.create_xpansion_candidate import CreateXpansionCandidate
from antarest.study.storage.variantstudy.model.command.remove_xpansion_candidate import RemoveXpansionCandidate
from antarest.study.storage.variantstudy.model.command.remove_xpansion_configuration import RemoveXpansionConfiguration
from antarest.study.storage.variantstudy.model.command.update_xpansion_candidate import UpdateXpansionCandidate
from antarest.study.storage.variantstudy.model.command.xpansion_common import assert_link_exist
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class XpansionResourceFileType(EnumIgnoreCase):
    CAPACITIES = "capacities"
    WEIGHTS = "weights"
    CONSTRAINTS = "constraints"


class UcType(EnumIgnoreCase):
    EXPANSION_FAST = "expansion_fast"
    EXPANSION_ACCURATE = "expansion_accurate"


class Master(EnumIgnoreCase):
    INTEGER = "integer"
    RELAXED = "relaxed"


class Solver(EnumIgnoreCase):
    CBC = "Cbc"
    COIN = "Coin"
    XPRESS = "Xpress"


class XpansionSensitivitySettings(AntaresBaseModel):
    """
    A DTO representing the sensitivity analysis settings used for Xpansion.

    The sensitivity analysis is optional.

    Attributes:
        epsilon: Max deviation from optimum (€).
        projection: List of candidate names to project (the candidate names should be in "candidates.ini" file).
        capex: Whether to include CAPEX in the sensitivity analysis.
    """

    epsilon: float = Field(default=0, ge=0, description="Max deviation from optimum (€)")
    projection: List[str] = Field(default_factory=list, description="List of candidate names to project")
    capex: bool = Field(default=False, description="Whether to include capex in the sensitivity analysis")

    @field_validator("projection", mode="before")
    def projection_validation(cls, v: Optional[Sequence[str]]) -> Sequence[str]:
        return [] if v is None else v


class XpansionSettings(AntaresBaseModel, extra="ignore", validate_assignment=True, populate_by_name=True):
    """
    A data transfer object representing the general settings used for Xpansion.

    Attributes:
        optimality_gap: Tolerance on absolute gap for the solution.
        max_iteration: Maximum number of Benders iterations for the solver.
        uc_type: Unit-commitment type used by Antares for the solver.
        master: Resolution mode of the master problem for the solver.
        yearly_weights: Path of the Monte-Carlo weights file for the solution.
        additional_constraints: Path of the additional constraints file for the solution.
        relaxed_optimality_gap: Threshold to switch from relaxed to integer master.
        relative_gap: Tolerance on relative gap for the solution.
        batch_size: Amount of batches in the Benders decomposition.
        separation_parameter: The separation parameter used in the Benders decomposition.
        solver: The solver used to solve the master and the sub-problems in the Benders decomposition.
        timelimit: The timelimit (in seconds) of the Benders step.
        log_level: The severity of the solver's logs in range [0, 3].
        sensitivity_config: The sensitivity analysis configuration for Xpansion, if any.

    Raises:
        ValueError: If the `relaxed_optimality_gap` attribute is not a float
        or a string ending with "%" and a valid float.
        ValueError: If the `max_iteration` attribute is not a valid integer.
    """

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#master
    master: Master = Field(default=Master.INTEGER, description="Master problem resolution mode")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#uc_type
    uc_type: UcType = Field(default=UcType.EXPANSION_FAST, description="Unit commitment type")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#optimality_gap
    optimality_gap: float = Field(default=1, ge=0, description="Absolute optimality gap (€)")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#relative_gap
    relative_gap: float = Field(default=1e-6, ge=0, description="Relative optimality gap")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#relaxed_optimality_gap
    relaxed_optimality_gap: float = Field(default=1e-5, ge=0, description="Relative optimality gap for relaxation")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#max_iteration
    max_iteration: int = Field(default=1000, gt=0, description="Maximum number of iterations")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#solver
    solver: Solver = Field(default=Solver.XPRESS, description="Solver")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#log_level
    log_level: int = Field(default=0, ge=0, le=3, description="Log level in range [0, 3]")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#separation_parameter
    separation_parameter: float = Field(default=0.5, gt=0, le=1, description="Separation parameter in range ]0, 1]")

    # https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition/#batch_size
    batch_size: int = Field(default=96, ge=0, description="Number of batches")

    yearly_weights: str = Field(
        "",
        alias="yearly-weights",
        description="Yearly weights file",
    )
    additional_constraints: str = Field(
        "",
        alias="additional-constraints",
        description="Additional constraints file",
    )

    # (deprecated field)
    timelimit: int = int(1e12)

    # The sensitivity analysis is optional
    sensitivity_config: Optional[XpansionSensitivitySettings] = None

    @model_validator(mode="before")
    def validate_float_values(cls, values: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        if "relaxed-optimality-gap" in values:
            values["relaxed_optimality_gap"] = values.pop("relaxed-optimality-gap")

        relaxed_optimality_gap = values.get("relaxed_optimality_gap")
        if relaxed_optimality_gap and isinstance(relaxed_optimality_gap, str):
            relaxed_optimality_gap = relaxed_optimality_gap.strip()
            if relaxed_optimality_gap.endswith("%"):
                # Don't divide by 100, because the value is already a percentage.
                values["relaxed_optimality_gap"] = float(relaxed_optimality_gap[:-1])
            else:
                values["relaxed_optimality_gap"] = float(relaxed_optimality_gap)

        separation_parameter = values.get("separation_parameter")
        if separation_parameter and isinstance(separation_parameter, str):
            separation_parameter = separation_parameter.strip()
            if separation_parameter.endswith("%"):
                values["separation_parameter"] = float(separation_parameter[:-1]) / 100
            else:
                values["separation_parameter"] = float(separation_parameter)

        if "max_iteration" in values:
            max_iteration = float(values["max_iteration"])
            if max_iteration == float("inf"):
                values["max_iteration"] = 1000

        return values


class GetXpansionSettings(XpansionSettings):
    """
    DTO object used to get the Xpansion settings.
    """

    @classmethod
    def from_config(cls, config_obj: JSON) -> "GetXpansionSettings":
        """
        Create a GetXpansionSettings object from a JSON object.

        First, make an attempt to validate the JSON object.
        If it fails, try to read the settings without validation,
        so that the user can fix the issue in the form.

        Args:
            config_obj: The JSON object to read.

        Returns:
            The object which may contains extra attributes or invalid values.
        """
        try:
            return cls(**config_obj)
        except ValidationError:
            return cls.model_construct(**config_obj)


@all_optional_model
class UpdateXpansionSettings(XpansionSettings):
    """
    DTO object used to update the Xpansion settings.

    Fields with a value of `None` are ignored, this allows a partial update of the settings.
    For that reason the fields "yearly-weights" and "additional-constraints" must
    be set to "" instead of `None` if you want to remove the file.
    """

    # note: for some reason, the alias is not taken into account when using the metaclass,
    # so we have to redefine the fields with the alias.
    yearly_weights: str = Field(
        "",
        alias="yearly-weights",
        description="Yearly weights file",
    )

    additional_constraints: str = Field(
        "",
        alias="additional-constraints",
        description="Additional constraints file",
    )


class XpansionManager:
    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def create_xpansion_configuration(self, study: StudyInterface, zipped_config: Optional[UploadFile] = None) -> None:
        logger.info(f"Initiating xpansion configuration for study '{study.id}'")
        file_study = study.get_files()
        try:
            file_study.tree.get(["user", "expansion"])
            logger.info(f"Using existing configuration for study '{study.id}'")
        except ChildNotFoundError:
            if zipped_config:
                try:
                    with zipfile.ZipFile(io.BytesIO(zipped_config.file.read())) as zip_output:
                        logger.info(f"Importing zipped xpansion configuration for study '{study.id}'")
                        zip_output.extractall(path=file_study.config.path / "user" / "expansion")
                        fix_study_root(file_study.config.path / "user" / "expansion")
                    return
                except zipfile.BadZipFile:
                    shutil.rmtree(
                        file_study.config.path / "user" / "expansion",
                        ignore_errors=True,
                    )
                    raise BadZipBinary("Only zip file are allowed.")

            settings_obj = XpansionSettings().model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
                exclude={"sensitivity_config", "yearly_weights", "additional_constraints"},
            )
            xpansion_configuration_data = {
                "user": {
                    "expansion": {
                        "settings": settings_obj,
                        "sensitivity": {"sensitivity_in": {}},
                        "candidates": {},
                        "capa": {},
                        "weights": {},
                        "constraints": {},
                    }
                }
            }

            file_study.tree.save(xpansion_configuration_data)

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
        self, study: StudyInterface, new_xpansion_settings: UpdateXpansionSettings
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
        command = UpdateXpansionCandidate(
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
        xpansion_settings = UpdateXpansionSettings.model_validate(args)
        return self.update_xpansion_settings(study, xpansion_settings)

    def _raw_file_dir(self, raw_file_type: XpansionResourceFileType) -> List[str]:
        if raw_file_type == XpansionResourceFileType.CONSTRAINTS:
            return ["user", "expansion", "constraints"]
        elif raw_file_type == XpansionResourceFileType.CAPACITIES:
            return ["user", "expansion", "capa"]
        elif raw_file_type == XpansionResourceFileType.WEIGHTS:
            return ["user", "expansion", "weights"]
        raise NotImplementedError(f"raw_file_type '{raw_file_type}' not implemented")

    def _add_raw_files(
        self,
        file_study: FileStudy,
        files: List[UploadFile],
        raw_file_type: XpansionResourceFileType,
    ) -> None:
        keys = self._raw_file_dir(raw_file_type)
        data: JSON = {}
        buffer = data

        list_names = [file.filename for file in files]
        for name in list_names:
            try:
                if name in file_study.tree.get(keys):
                    raise FileAlreadyExistsError(f"File '{name}' already exists")
            except ChildNotFoundError:
                logger.warning(f"Failed to list existing files for {keys}")

        if len(list_names) != len(set(list_names)):
            raise FileAlreadyExistsError(f"Some files have the same name: {list_names}")

        for key in keys:
            buffer[key] = {}
            buffer = buffer[key]

        for file in files:
            content = file.file.read()
            if isinstance(content, str):
                content = content.encode(encoding="utf-8")
            assert file.filename is not None
            buffer[file.filename] = content

        file_study.tree.save(data)

    def add_resource(
        self,
        study: StudyInterface,
        resource_type: XpansionResourceFileType,
        files: List[UploadFile],
    ) -> None:
        logger.info(f"Adding xpansion {resource_type} resource file list to study '{study.id}'")
        file_study = study.get_files()
        self._add_raw_files(file_study, files, resource_type)

    def delete_resource(
        self,
        study: StudyInterface,
        resource_type: XpansionResourceFileType,
        filename: str,
    ) -> None:
        file_study = study.get_files()
        logger.info(
            f"Checking if xpansion {resource_type} resource file '{filename}' is not used in study '{study.id}'"
        )
        if resource_type == XpansionResourceFileType.CONSTRAINTS and self._is_constraints_file_used(
            file_study, filename
        ):
            raise FileCurrentlyUsedInSettings(
                f"The constraints file '{filename}' is still used in the xpansion settings and cannot be deleted"
            )
        elif resource_type == XpansionResourceFileType.CAPACITIES and self._is_capa_file_used(file_study, filename):
            raise FileCurrentlyUsedInSettings(
                f"The capacities file '{filename}' is still used in the xpansion settings and cannot be deleted"
            )
        elif resource_type == XpansionResourceFileType.WEIGHTS and self._is_weights_file_used(file_study, filename):
            raise FileCurrentlyUsedInSettings(
                f"The weight file '{filename}' is still used in the xpansion settings and cannot be deleted"
            )
        file_study.tree.delete(self._raw_file_dir(resource_type) + [filename])

    def get_resource_content(
        self,
        study: StudyInterface,
        resource_type: XpansionResourceFileType,
        filename: str,
    ) -> JSON | bytes:
        logger.info(f"Getting xpansion {resource_type} resource file '{filename}' from study '{study.id}'")
        file_study = study.get_files()
        return file_study.tree.get(self._raw_file_dir(resource_type) + [filename])

    def list_resources(self, study: StudyInterface, resource_type: XpansionResourceFileType) -> List[str]:
        logger.info(f"Getting all xpansion {resource_type} files from study '{study.id}'")
        file_study = study.get_files()
        try:
            return [filename for filename in file_study.tree.get(self._raw_file_dir(resource_type)).keys()]
        except ChildNotFoundError:
            return []

    @staticmethod
    def _is_constraints_file_used(file_study: FileStudy, filename: str) -> bool:  # type: ignore
        with contextlib.suppress(KeyError):
            constraints = file_study.tree.get(["user", "expansion", "settings", "additional-constraints"])
            return str(constraints) == filename

    @staticmethod
    def _is_weights_file_used(file_study: FileStudy, filename: str) -> bool:  # type: ignore
        with contextlib.suppress(KeyError):
            weights = file_study.tree.get(["user", "expansion", "settings", "yearly-weights"])
            return str(weights) == filename

    @staticmethod
    def _is_capa_file_used(file_study: FileStudy, filename: str) -> bool:
        logger.info(
            f"Checking xpansion capacities file '{filename}' is not used in study '{file_study.config.study_id}'"
        )

        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        all_link_profiles = [candidate.get("link-profile", None) for candidate in candidates.values()]
        all_link_profiles += [
            candidate.get("already-installed-link-profile", None) for candidate in candidates.values()
        ]
        return filename in all_link_profiles
