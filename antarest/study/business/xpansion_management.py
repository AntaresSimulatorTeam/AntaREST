from http import HTTPStatus
from typing import Optional, Literal, Union, List

from fastapi import HTTPException
from pydantic import Field, BaseModel

from antarest.core.model import JSON
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.storage_service import StudyStorageService


class LinkDoesNotExistError(Exception):
    pass


class XpansionSettingsDTO(BaseModel):
    optimality_gap: Optional[float] = None
    max_iteration: Optional[Union[int, Literal["inf"]]] = None
    uc_type: Union[
        Literal["expansion_fast"], Literal["expansion_accurate"]
    ] = "expansion_fast"
    master: Union[Literal["integer"], Literal["relaxed"]] = "integer"
    yearly_weight: Optional[str] = None
    additional_constraints: Optional[str] = Field(
        None, alias="additional-constraints"
    )
    relaxed_optimality_gap: Optional[float] = Field(
        None, alias="relaxed-optimality-gap"
    )
    cut_type: Optional[
        Union[Literal["average"], Literal["yearly"], Literal["weekly"]]
    ] = Field(None, alias="cut-type")
    ampl_solver: Optional[str] = Field(None, alias="ampl.solver")
    ampl_presolve: Optional[int] = Field(None, alias="ampl.presolve")
    ampl_solve_bounds_frequency: Optional[int] = Field(
        None, alias="ampl.solve_bounds_frequency"
    )
    relative_gap: Optional[float] = None
    solver: Optional[Union[Literal["Cbc"], Literal["Coin"]]] = None


class XpansionCandidateDTO(BaseModel):
    name: str
    link: str
    annual_cost_per_mw: int = Field(alias="annual-cost-per-mw")
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


class LinkProfileNotFoundError(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class AlreadyInstalledLinkProfileNotFoundError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(HTTPStatus.NOT_FOUND, message)


class IllegalCharacterInNameError(HTTPException):
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


class XpansionManager:
    def __init__(self, study_storage_service: StudyStorageService):
        self.study_storage_service = study_storage_service

    def create_xpansion_configuration(self, study: Study) -> None:
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        try:
            file_study.tree.get(["user", "expansion"])
        except ChildNotFoundError:
            study_version = file_study.config.version

            xpansion_settings = {
                "optimality_gap": 1,
                "max_iteration": float("inf"),
                "uc_type": "expansion_fast",
                "master": "integer",
                "yearly-weights": None,
                "additional-constraints": None,
            }

            if study_version < 800:
                xpansion_settings["relaxed-optimality-gap"] = 1e6
                xpansion_settings["cut-type"] = "average"
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
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        file_study.tree.delete(["user", "expansion"])

    def get_xpansion_settings(self, study: Study) -> XpansionSettingsDTO:
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        json = file_study.tree.get(["user", "expansion", "settings"])
        return XpansionSettingsDTO.parse_obj(json)

    def update_xpansion_settings(
        self, study: Study, new_xpansion_settings_dto: XpansionSettingsDTO
    ) -> XpansionSettingsDTO:
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
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
            raise LinkProfileNotFoundError(
                f"The file {xpansion_candidate_dto.link_profile} does not exist"
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
            raise AlreadyInstalledLinkProfileNotFoundError(
                f"The file {xpansion_candidate_dto.already_installed_link_profile} does not exist"
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
            raise LinkDoesNotExistError(
                f"The link from {area_from} to {area_to} does not exist"
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
                f"The candidate is not well formatted."
                f"It should either contain max-investment or (max-units and unit-size)."
            )

    def _assert_candidate_is_correct(
        self,
        candidates: JSON,
        file_study: FileStudy,
        xpansion_candidate_dto: XpansionCandidateDTO,
    ) -> None:
        self._assert_link_profile_are_files(file_study, xpansion_candidate_dto)
        self._assert_link_exist(file_study, xpansion_candidate_dto)
        self._assert_no_illegal_character_is_in_candidate_name(
            xpansion_candidate_dto.name
        )
        self._assert_candidate_name_is_not_already_taken(
            candidates, xpansion_candidate_dto.name
        )
        self._assert_investment_candidate_is_valid(
            xpansion_candidate_dto.max_investment,
            xpansion_candidate_dto.max_units,
            xpansion_candidate_dto.unit_size,
        )

    def add_candidate(
        self, study: Study, xpansion_candidate_dto: XpansionCandidateDTO
    ) -> str:

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

        # Add candidate
        candidates[next_id] = xpansion_candidate_dto.dict(
            by_alias=True, exclude_none=True
        )
        candidates_data = {"user": {"expansion": {"candidates": candidates}}}
        file_study.tree.save(candidates_data)
        # Should we add a field in the study config containing the xpansion candidates like the links or the areas ?

        return next_id

    def get_candidate(
        self, study: Study, candidate_name: str
    ) -> XpansionCandidateDTO:
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
        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        return [XpansionCandidateDTO(**c) for c in candidates.values()]
