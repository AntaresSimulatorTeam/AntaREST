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
import io
import logging
import shutil
import typing as t
import zipfile

from fastapi import HTTPException, UploadFile
from pydantic import Field, ValidationError, field_validator, model_validator

from antarest.core.exceptions import BadZipBinary, ChildNotFoundError, LinkNotFound
from antarest.core.model import JSON
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import fix_study_root

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
    projection: t.List[str] = Field(default_factory=list, description="List of candidate names to project")
    capex: bool = Field(default=False, description="Whether to include capex in the sensitivity analysis")

    @field_validator("projection", mode="before")
    def projection_validation(cls, v: t.Optional[t.Sequence[str]]) -> t.Sequence[str]:
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
    sensitivity_config: t.Optional[XpansionSensitivitySettings] = None

    @model_validator(mode="before")
    def validate_float_values(cls, values: t.MutableMapping[str, t.Any]) -> t.MutableMapping[str, t.Any]:
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


class XpansionCandidateDTO(AntaresBaseModel):
    # The id of the candidate is irrelevant, so it should stay hidden for the user
    # The names should be the section titles of the file, and the id should be removed
    name: str
    link: str
    annual_cost_per_mw: float = Field(alias="annual-cost-per-mw", ge=0)
    unit_size: t.Optional[float] = Field(default=None, alias="unit-size", ge=0)
    max_units: t.Optional[int] = Field(default=None, alias="max-units", ge=0)
    max_investment: t.Optional[float] = Field(default=None, alias="max-investment", ge=0)
    already_installed_capacity: t.Optional[int] = Field(default=None, alias="already-installed-capacity", ge=0)
    # this is obsolete (replaced by direct/indirect)
    link_profile: t.Optional[str] = Field(default=None, alias="link-profile")
    # this is obsolete (replaced by direct/indirect)
    already_installed_link_profile: t.Optional[str] = Field(default=None, alias="already-installed-link-profile")
    direct_link_profile: t.Optional[str] = Field(default=None, alias="direct-link-profile")
    indirect_link_profile: t.Optional[str] = Field(default=None, alias="indirect-link-profile")
    already_installed_direct_link_profile: t.Optional[str] = Field(
        default=None, alias="already-installed-direct-link-profile"
    )
    already_installed_indirect_link_profile: t.Optional[str] = Field(
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


class FileCurrentlyUsedInSettings(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(http.HTTPStatus.CONFLICT, message)


class FileAlreadyExistsError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(http.HTTPStatus.CONFLICT, message)


class XpansionManager:
    def __init__(self, study_storage_service: StudyStorageService):
        self.study_storage_service = study_storage_service

    def create_xpansion_configuration(self, study: Study, zipped_config: t.Optional[UploadFile] = None) -> None:
        logger.info(f"Initiating xpansion configuration for study '{study.id}'")
        file_study = self.study_storage_service.get_storage(study).get_raw(study)
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

            xpansion_settings = XpansionSettings()
            settings_obj = xpansion_settings.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
                exclude={"sensitivity_config", "yearly_weights", "additional_constraints"},
            )
            if xpansion_settings.sensitivity_config:
                sensitivity_obj = xpansion_settings.sensitivity_config.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                )
            else:
                sensitivity_obj = {}

            xpansion_configuration_data = {
                "user": {
                    "expansion": {
                        "settings": settings_obj,
                        "sensitivity": {"sensitivity_in": sensitivity_obj},
                        "candidates": {},
                        "capa": {},
                        "weights": {},
                        "constraints": {},
                    }
                }
            }

            file_study.tree.save(xpansion_configuration_data)

    def delete_xpansion_configuration(self, study: Study) -> None:
        logger.info(f"Deleting xpansion configuration for study '{study.id}'")
        file_study = self.study_storage_service.get_storage(study).get_raw(study)
        file_study.tree.delete(["user", "expansion"])

    def get_xpansion_settings(self, study: Study) -> GetXpansionSettings:
        logger.info(f"Getting xpansion settings for study '{study.id}'")
        file_study = self.study_storage_service.get_storage(study).get_raw(study)
        config_obj = file_study.tree.get(["user", "expansion", "settings"])
        with contextlib.suppress(ChildNotFoundError):
            config_obj["sensitivity_config"] = file_study.tree.get(
                ["user", "expansion", "sensitivity", "sensitivity_in"]
            )
        return GetXpansionSettings.from_config(config_obj)

    def update_xpansion_settings(
        self, study: Study, new_xpansion_settings: UpdateXpansionSettings
    ) -> GetXpansionSettings:
        logger.info(f"Updating xpansion settings for study '{study.id}'")

        actual_settings = self.get_xpansion_settings(study)
        settings_fields = new_xpansion_settings.model_dump(
            mode="json", by_alias=False, exclude_none=True, exclude={"sensitivity_config"}
        )
        updated_settings = actual_settings.copy(deep=True, update=settings_fields)

        file_study = self.study_storage_service.get_storage(study).get_raw(study)

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
        max_investment: t.Optional[float],
        max_units: t.Optional[int],
        unit_size: t.Optional[float],
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

    def add_candidate(self, study: Study, xpansion_candidate: XpansionCandidateDTO) -> XpansionCandidateDTO:
        file_study = self.study_storage_service.get_storage(study).get_raw(study)

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

    def get_candidate(self, study: Study, candidate_name: str) -> XpansionCandidateDTO:
        logger.info(f"Getting candidate '{candidate_name}' of study '{study.id}'")
        # This takes the first candidate with the given name and not the id, because the name is the primary key.
        file_study = self.study_storage_service.get_storage(study).get_raw(study)
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        try:
            candidate = next(c for c in candidates.values() if c["name"] == candidate_name)
            return XpansionCandidateDTO(**candidate)

        except StopIteration:
            raise CandidateNotFoundError(f"The candidate '{candidate_name}' does not exist")

    def get_candidates(self, study: Study) -> t.List[XpansionCandidateDTO]:
        logger.info(f"Getting all candidates of study {study.id}")
        file_study = self.study_storage_service.get_storage(study).get_raw(study)
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        return [XpansionCandidateDTO(**c) for c in candidates.values()]

    def update_candidate(
        self,
        study: Study,
        candidate_name: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> None:
        file_study = self.study_storage_service.get_storage(study).get_raw(study)

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

    def delete_candidate(self, study: Study, candidate_name: str) -> None:
        file_study = self.study_storage_service.get_storage(study).get_raw(study)

        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        candidate_id = next(
            candidate_id for candidate_id, candidate in candidates.items() if candidate["name"] == candidate_name
        )

        logger.info(f"Deleting candidate '{candidate_name}' from study '{study.id}'")
        file_study.tree.delete(["user", "expansion", "candidates", candidate_id])

    def update_xpansion_constraints_settings(self, study: Study, constraints_file_name: str) -> GetXpansionSettings:
        # Make sure filename is not `None`, because `None` values are ignored by the update.
        constraints_file_name = constraints_file_name or ""
        # noinspection PyArgumentList
        args = {"additional_constraints": constraints_file_name}
        xpansion_settings = UpdateXpansionSettings.model_validate(args)
        return self.update_xpansion_settings(study, xpansion_settings)

    def _raw_file_dir(self, raw_file_type: XpansionResourceFileType) -> t.List[str]:
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
        files: t.List[UploadFile],
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
        study: Study,
        resource_type: XpansionResourceFileType,
        files: t.List[UploadFile],
    ) -> None:
        logger.info(f"Adding xpansion {resource_type} resource file list to study '{study.id}'")
        file_study = self.study_storage_service.get_storage(study).get_raw(study)
        self._add_raw_files(file_study, files, resource_type)

    def delete_resource(
        self,
        study: Study,
        resource_type: XpansionResourceFileType,
        filename: str,
    ) -> None:
        file_study = self.study_storage_service.get_storage(study).get_raw(study)
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
        study: Study,
        resource_type: XpansionResourceFileType,
        filename: str,
    ) -> t.Union[JSON, bytes]:
        logger.info(f"Getting xpansion {resource_type} resource file '{filename}' from study '{study.id}'")
        file_study = self.study_storage_service.get_storage(study).get_raw(study)
        return file_study.tree.get(self._raw_file_dir(resource_type) + [filename])

    def list_resources(self, study: Study, resource_type: XpansionResourceFileType) -> t.List[str]:
        logger.info(f"Getting all xpansion {resource_type} files from study '{study.id}'")
        file_study = self.study_storage_service.get_storage(study).get_raw(study)
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
