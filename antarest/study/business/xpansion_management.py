import logging
import shutil
from enum import Enum
from http import HTTPStatus
from io import BytesIO
from typing import Optional, Union, List, cast
from zipfile import ZipFile, BadZipFile

from fastapi import HTTPException, UploadFile
from pydantic import Field, BaseModel, validator

from antarest.core.exceptions import BadZipBinary
from antarest.core.model import JSON
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.bucket_node import (
    BucketNode,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.expansion import (
    Expansion,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import fix_study_root

logger = logging.getLogger(__name__)


class UcType(str, Enum):
    EXPANSION_FAST = "expansion_fast"
    EXPANSION_ACCURATE = "expansion_accurate"


class Master(str, Enum):
    INTEGER = "integer"
    RELAXED = "relaxed"


class CutType(str, Enum):
    AVERAGE = "average"
    YEARLY = "yearly"
    WEEKLY = "weekly"


class Solver(str, Enum):
    CBC = "Cbc"
    COIN = "Coin"
    XPRESS = "Xpress"


class MaxIteration(str, Enum):
    INF = "inf"


class XpansionSettingsDTO(BaseModel):
    optimality_gap: Optional[float] = 1
    max_iteration: Optional[Union[int, MaxIteration]] = MaxIteration.INF
    uc_type: UcType = UcType.EXPANSION_FAST
    master: Master = Master.INTEGER
    yearly_weights: Optional[str] = Field(None, alias="yearly-weights")
    additional_constraints: Optional[str] = Field(
        None, alias="additional-constraints"
    )
    relaxed_optimality_gap: Optional[Union[float, str]] = Field(
        None, alias="relaxed-optimality-gap"
    )
    cut_type: Optional[CutType] = Field(None, alias="cut-type")
    ampl_solver: Optional[str] = Field(None, alias="ampl.solver")
    ampl_presolve: Optional[int] = Field(None, alias="ampl.presolve")
    ampl_solve_bounds_frequency: Optional[int] = Field(
        None, alias="ampl.solve_bounds_frequency"
    )
    relative_gap: Optional[float] = 1e-12
    solver: Optional[Solver] = Solver.CBC
    timelimit: Optional[int] = 1e12
    log_level: Optional[int] = 0

    @validator("relaxed_optimality_gap")
    def relaxed_optimality_gap_validation(
        cls, v: Optional[Union[float, str]]
    ) -> Optional[Union[float, str]]:
        if isinstance(v, float):
            return v
        if isinstance(v, str):
            stripped_v = v.strip()
            if stripped_v.endswith("%") and float(stripped_v[:-1]):
                return v
            raise ValueError(
                "season_correlation is not allowed for 'thermal' type"
            )
        return v


class XpansionCandidateDTO(BaseModel):
    # The id of the candidate is irrelevant, so it should stay hidden for the user
    # The names should be the section titles of the file, and the id should be removed
    name: str
    link: str
    annual_cost_per_mw: float = Field(alias="annual-cost-per-mw")
    unit_size: Optional[float] = Field(None, alias="unit-size")
    max_units: Optional[int] = Field(None, alias="max-units")
    max_investment: Optional[float] = Field(None, alias="max-investment")
    already_installed_capacity: Optional[int] = Field(
        None, alias="already-installed-capacity"
    )
    link_profile: Optional[str] = Field(None, alias="link-profile")
    already_installed_link_profile: Optional[str] = Field(
        None, alias="already-installed-link-profile"
    )


class LinkNotFound(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class XpansionFileNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class IllegalCharacterInNameError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class CandidateNameIsEmpty(HTTPException):
    def __init__(self) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST)


class WrongTypeFormat(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class WrongLinkFormatError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class CandidateAlreadyExistsError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class BadCandidateFormatError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.BAD_REQUEST, message)


class CandidateNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class ConstraintsNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class FileCurrentlyUsedInSettings(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.CONFLICT, message)


class FileAlreadyExistsError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.CONFLICT, message)


class XpansionManager:
    def __init__(self, study_storage_service: StudyStorageService):
        self.study_storage_service = study_storage_service

    def create_xpansion_configuration(
        self, study: Study, zipped_config: Optional[UploadFile] = None
    ) -> None:
        logger.info(
            f"Initiating xpansion configuration for study '{study.id}'"
        )
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        try:
            file_study.tree.get(["user", "expansion"])
            logger.info(f"Using existing configuration for study '{study.id}'")
        except ChildNotFoundError:
            if zipped_config:
                try:
                    with ZipFile(
                        BytesIO(zipped_config.file.read())
                    ) as zip_output:
                        logger.info(
                            f"Importing zipped xpansion configuration for study '{study.id}'"
                        )
                        zip_output.extractall(
                            path=file_study.config.path / "user" / "expansion"
                        )
                        fix_study_root(
                            file_study.config.path / "user" / "expansion"
                        )
                    return
                except BadZipFile:
                    shutil.rmtree(
                        file_study.config.path / "user" / "expansion",
                        ignore_errors=True,
                    )
                    raise BadZipBinary("Only zip file are allowed.")

            study_version = file_study.config.version

            xpansion_settings = {
                "optimality_gap": 1,
                "max_iteration": "inf",
                "uc_type": "expansion_fast",
                "master": "integer",
                "yearly-weights": None,
                "additional-constraints": None,
            }

            if study_version < 800:
                xpansion_settings["relaxed-optimality-gap"] = 1e6
                xpansion_settings["cut-type"] = "yearly"
                xpansion_settings["ampl.solver"] = "cbc"
                xpansion_settings["ampl.presolve"] = 0
                xpansion_settings["ampl.solve_bounds_frequency"] = 1000000
            else:
                xpansion_settings["relative_gap"] = 1e-12
                xpansion_settings["solver"] = "Cbc"

            xpansion_configuration_data = {
                "user": {
                    "expansion": {
                        "settings": xpansion_settings,
                        "candidates": {},
                        "capa": {},
                    }
                }
            }

            file_study.tree.save(xpansion_configuration_data)

    def delete_xpansion_configuration(self, study: Study) -> None:
        logger.info(f"Deleting xpansion configuration for study '{study.id}'")
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        file_study.tree.delete(["user", "expansion"])

    def get_xpansion_settings(self, study: Study) -> XpansionSettingsDTO:
        logger.info(f"Getting xpansion settings for study '{study.id}'")
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        json = file_study.tree.get(["user", "expansion", "settings"])
        return XpansionSettingsDTO.parse_obj(json)

    def _assert_xpansion_settings_additional_constraints_is_valid(
        self,
        file_study: FileStudy,
        additional_constraints: str,
    ) -> None:
        if additional_constraints:
            try:
                file_study.tree.get(
                    [
                        "user",
                        "expansion",
                        additional_constraints,
                    ]
                )
            except ChildNotFoundError:
                raise XpansionFileNotFoundError(
                    f"The 'additional-constraints' file '{additional_constraints}' does not exist"
                )

    def _assert_is_positive(
        self,
        name: str,
        param: Union[float, int],
    ) -> None:
        if param < 0:
            raise WrongTypeFormat(
                f"'{name}' must be a float greater than or equal to 0"
            )

    def _assert_max_iteration_is_valid(
        self, max_iteration: Union[int, MaxIteration]
    ) -> None:
        if (
            isinstance(max_iteration, int)
            and max_iteration < 0
            or cast(str, max_iteration) != MaxIteration.INF
        ):
            raise WrongTypeFormat(
                "'max_iteration' must be an integer greater than or equal to 0 OR '+Inf'"
            )

    def update_xpansion_settings(
        self, study: Study, new_xpansion_settings_dto: XpansionSettingsDTO
    ) -> XpansionSettingsDTO:
        logger.info(f"Updating xpansion settings for study '{study.id}'")
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        if new_xpansion_settings_dto.optimality_gap is not None:
            self._assert_is_positive(
                "optimality_gap", new_xpansion_settings_dto.optimality_gap
            )
        if new_xpansion_settings_dto.relative_gap is not None:
            self._assert_is_positive(
                "relative_gap", new_xpansion_settings_dto.relative_gap
            )
        if new_xpansion_settings_dto.max_iteration is not None and isinstance(
            new_xpansion_settings_dto.max_iteration, int
        ):
            self._assert_is_positive(
                "max_iteration", new_xpansion_settings_dto.max_iteration
            )
        if new_xpansion_settings_dto.additional_constraints:
            self._assert_xpansion_settings_additional_constraints_is_valid(
                file_study, new_xpansion_settings_dto.additional_constraints
            )

        file_study.tree.save(
            new_xpansion_settings_dto.dict(by_alias=True),
            ["user", "expansion", "settings"],
        )
        return new_xpansion_settings_dto

    def _assert_link_profile_are_files(
        self,
        file_study: FileStudy,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> None:
        if xpansion_candidate_dto.link_profile and not file_study.tree.get(
            ["user", "expansion", "capa", xpansion_candidate_dto.link_profile]
        ):
            raise XpansionFileNotFoundError(
                f"The 'link-profile' file '{xpansion_candidate_dto.link_profile}' does not exist"
            )
        if (
            xpansion_candidate_dto.already_installed_link_profile
            and not file_study.tree.get(
                [
                    "user",
                    "expansion",
                    "capa",
                    xpansion_candidate_dto.already_installed_link_profile,
                ]
            )
        ):
            raise XpansionFileNotFoundError(
                f"The 'already-installed-link-profile' file '{xpansion_candidate_dto.link_profile}' does not exist"
            )

    def _assert_link_exist(
        self,
        file_study: FileStudy,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> None:
        if " - " not in xpansion_candidate_dto.link:
            raise WrongLinkFormatError(
                "The link must be in the format 'area1 - area2'"
            )
        area1, area2 = xpansion_candidate_dto.link.split(" - ")
        area_from, area_to = sorted([area1, area2])
        if area_to not in file_study.config.get_links(area_from):
            raise LinkNotFound(
                f"The link from '{area_from}' to '{area_to}' not found"
            )

    def _assert_no_illegal_character_is_in_candidate_name(
        self, xpansion_candidate_name: str
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
                raise IllegalCharacterInNameError(
                    f"The character '{char}' is not allowed in the candidate name"
                )

    def _assert_candidate_name_is_not_already_taken(
        self, candidates: JSON, xpansion_candidate_name: str
    ) -> None:
        for candidate in candidates.values():
            if candidate["name"] == xpansion_candidate_name:
                raise CandidateAlreadyExistsError(
                    f"The candidate '{xpansion_candidate_name}' already exists"
                )

    def _assert_investment_candidate_is_valid(
        self,
        max_investment: Optional[float],
        max_units: Optional[int],
        unit_size: Optional[float],
    ) -> None:
        bool_max_investment = max_investment is None
        bool_max_units = max_units is None
        bool_unit_size = unit_size is None

        if not (
            (not bool_max_investment and bool_max_units and bool_unit_size)
            or (
                bool_max_investment
                and not bool_max_units
                and not bool_unit_size
            )
        ):
            raise BadCandidateFormatError(
                "The candidate is not well formatted.\nIt should either contain max-investment or (max-units and unit-size)."
            )

    def _assert_candidate_is_correct(
        self,
        candidates: JSON,
        file_study: FileStudy,
        xpansion_candidate_dto: XpansionCandidateDTO,
        new_name: bool = False,
    ) -> None:
        logger.info(f"Checking given candidate is correct")
        self._assert_no_illegal_character_is_in_candidate_name(
            xpansion_candidate_dto.name
        )
        if new_name:
            self._assert_candidate_name_is_not_already_taken(
                candidates, xpansion_candidate_dto.name
            )
        self._assert_link_profile_are_files(file_study, xpansion_candidate_dto)
        self._assert_link_exist(file_study, xpansion_candidate_dto)
        self._assert_investment_candidate_is_valid(
            xpansion_candidate_dto.max_investment,
            xpansion_candidate_dto.max_units,
            xpansion_candidate_dto.unit_size,
        )
        if xpansion_candidate_dto.annual_cost_per_mw:
            self._assert_is_positive(
                "annual_cost_per_mw", xpansion_candidate_dto.annual_cost_per_mw
            )
        else:
            raise BadCandidateFormatError(
                "The candidate is not well formatted.\nIt should contain annual-cost-per-mw."
            )
        if xpansion_candidate_dto.unit_size is not None:
            self._assert_is_positive(
                "unit_size", xpansion_candidate_dto.unit_size
            )
        if xpansion_candidate_dto.max_investment is not None:
            self._assert_is_positive(
                "max_investment", xpansion_candidate_dto.max_investment
            )
        if xpansion_candidate_dto.already_installed_capacity is not None:
            self._assert_is_positive(
                "already_installed_capacity",
                xpansion_candidate_dto.already_installed_capacity,
            )
        if xpansion_candidate_dto.max_units is not None:
            self._assert_is_positive(
                "max_units", xpansion_candidate_dto.max_units
            )

    def add_candidate(
        self, study: Study, xpansion_candidate_dto: XpansionCandidateDTO
    ) -> None:

        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )

        candidates = file_study.tree.get(["user", "expansion", "candidates"])

        self._assert_candidate_is_correct(
            candidates, file_study, xpansion_candidate_dto
        )

        # Find next candidate id
        max_id = (
            2 if not candidates else int(sorted(candidates.keys()).pop()) + 2
        )
        next_id = next(
            str(i) for i in range(1, max_id) if str(i) not in candidates
        )  # The primary key is actually the name, the id does not matter and is never checked.

        logger.info(
            f"Adding candidate '{xpansion_candidate_dto.name}' to study '{study.id}'"
        )
        candidates[next_id] = xpansion_candidate_dto.dict(
            by_alias=True, exclude_none=True
        )
        candidates_data = {"user": {"expansion": {"candidates": candidates}}}
        file_study.tree.save(candidates_data)
        # Should we add a field in the study config containing the xpansion candidates like the links or the areas ?

    def get_candidate(
        self, study: Study, candidate_name: str
    ) -> XpansionCandidateDTO:
        logger.info(
            f"Getting candidate '{candidate_name}' of study '{study.id}'"
        )
        # This takes the first candidate with the given name and not the id, because the name is the primary key.
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        try:
            candidate = next(
                c for c in candidates.values() if c["name"] == candidate_name
            )
            return XpansionCandidateDTO(**candidate)

        except StopIteration:
            raise CandidateNotFoundError(
                f"The candidate '{candidate_name}' does not exist"
            )

    def get_candidates(self, study: Study) -> List[XpansionCandidateDTO]:
        logger.info(f"Getting all candidates of study {study.id}")
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        return [XpansionCandidateDTO(**c) for c in candidates.values()]

    def update_candidate(
        self,
        study: Study,
        candidate_name: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> None:
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )

        candidates = file_study.tree.get(["user", "expansion", "candidates"])

        new_name = candidate_name != xpansion_candidate_dto.name
        self._assert_candidate_is_correct(
            candidates, file_study, xpansion_candidate_dto, new_name=new_name
        )

        logger.info(f"Checking candidate {candidate_name} exists")
        for id, candidate in candidates.items():
            if candidate["name"] == candidate_name:
                logger.info(
                    f"Updating candidate '{candidate_name}' of study '{study.id}'"
                )
                candidates[id] = xpansion_candidate_dto.dict(
                    by_alias=True, exclude_none=True
                )
                file_study.tree.save(
                    candidates, ["user", "expansion", "candidates"]
                )
                return
        raise CandidateNotFoundError(
            f"The candidate '{xpansion_candidate_dto.name}' does not exist"
        )

    def delete_candidate(self, study: Study, candidate_name: str) -> None:
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )

        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        candidate_id = next(
            id
            for id, candidate in candidates.items()
            if candidate["name"] == candidate_name
        )

        logger.info(
            f"Deleting candidate '{candidate_name}' from study '{study.id}'"
        )
        file_study.tree.delete(
            ["user", "expansion", "candidates", candidate_id]
        )

    def update_xpansion_constraints_settings(
        self, study: Study, constraints_file_name: Optional[str]
    ) -> None:
        self.update_xpansion_settings(
            study,
            XpansionSettingsDTO.parse_obj(
                {"additional-constraints": constraints_file_name}
            ),
        )

    def _add_raw_files(
        self,
        file_study: FileStudy,
        files: List[UploadFile],
        raw_file_type: str,
    ) -> None:
        if raw_file_type == "constraints":
            keys = ["user", "expansion"]
        elif raw_file_type == "capacities":
            keys = ["user", "expansion", "capa"]
        else:
            raise NotImplementedError(
                f"raw_file_type '{raw_file_type}' not implemented"
            )

        data: JSON = {}
        buffer = data

        list_names = [file.filename for file in files]
        for name in list_names:
            if name in file_study.tree.get(keys):
                raise FileAlreadyExistsError(f"File '{name}' already exists")

        if len(list_names) != len(set(list_names)):
            raise FileAlreadyExistsError(
                f"Some files have the same name: {list_names}"
            )

        for key in keys:
            buffer[key] = {}
            buffer = buffer[key]

        for file in files:
            content = file.file.read()
            if type(content) != bytes:
                content = content.encode()
            buffer[file.filename] = content

        file_study.tree.save(data)

    def add_xpansion_constraints(
        self, study: Study, files: List[UploadFile]
    ) -> None:
        logger.info(
            f"Adding xpansion constraints file list to study '{study.id}'"
        )
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        self._add_raw_files(file_study, files, "constraints")

    def _is_constraints_file_used(
        self, file_study: FileStudy, filename: str
    ) -> bool:
        try:
            return (
                str(
                    file_study.tree.get(
                        [
                            "user",
                            "expansion",
                            "settings",
                            "additional-constraints",
                        ]
                    )
                )
                == filename
            )
        except KeyError:
            return False

    def delete_xpansion_constraints(self, study: Study, filename: str) -> None:
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )

        logger.info(
            f"Checking xpansion constraints file '{filename}' is not used in study '{study.id}'"
        )
        if self._is_constraints_file_used(file_study, filename):
            raise FileCurrentlyUsedInSettings(
                f"The constraints file '{filename}' is still used in the xpansion settings and cannot be deleted"
            )

        file_study.tree.delete(["user", "expansion", filename])

    def get_single_xpansion_constraints(
        self, study: Study, filename: str
    ) -> bytes:
        logger.info(
            f"Getting xpansion constraints file '{filename}' from study '{study.id}'"
        )
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        return cast(
            bytes, file_study.tree.get(["user", "expansion", filename])
        )

    def get_all_xpansion_constraints(self, study: Study) -> List[str]:
        logger.info(
            f"Getting all xpansion constraints files from study '{study.id}'"
        )

        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        registered_filenames = [
            registered_file.key
            for registered_file in Expansion.registered_files
        ]
        constraints_filenames = [
            key
            for key, node in cast(
                FolderNode, file_study.tree.get_node(["user", "expansion"])
            )
            .build()
            .items()
            if key not in registered_filenames and type(node) != BucketNode
        ]
        return constraints_filenames

    def add_capa(self, study: Study, files: List[UploadFile]) -> None:
        logger.info(
            f"Adding xpansion capacities file list to study '{study.id}'"
        )
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        self._add_raw_files(file_study, files, "capacities")

    def _is_capa_file_used(self, file_study: FileStudy, filename: str) -> bool:
        logger.info(
            f"Checking xpansion capacities file '{filename}' is not used in study '{file_study.config.study_id}'"
        )

        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        all_link_profiles = [
            candidate.get("link-profile", None)
            for candidate in candidates.values()
        ]
        all_link_profiles += [
            candidate.get("already-installed-link-profile", None)
            for candidate in candidates.values()
        ]
        return filename in all_link_profiles

    def delete_capa(self, study: Study, filename: str) -> None:
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )

        if self._is_capa_file_used(file_study, filename):
            raise FileCurrentlyUsedInSettings(
                f"The capacities file '{filename}' is still used in the xpansion settings and cannot be deleted"
            )

        logger.info(
            f"Delete xpansion capacities file '{filename}' from study '{study.id}'"
        )
        file_study.tree.delete(["user", "expansion", "capa", filename])

    def get_single_capa(self, study: Study, filename: str) -> JSON:
        logger.info(
            f"Getting xpansion capacities file '{filename}' from study '{study.id}'"
        )
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        return file_study.tree.get(["user", "expansion", "capa", filename])

    def get_all_capa(self, study: Study) -> List[str]:
        logger.info(
            f"Getting all xpansion capacities files from study '{study.id}'"
        )
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        return [
            filename
            for filename in file_study.tree.get(
                ["user", "expansion", "capa"]
            ).keys()
        ]
