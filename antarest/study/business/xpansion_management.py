from typing import Optional, Literal, Union

from pydantic import Field, BaseModel

from antarest.study.model import Study
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


class XpansionNewCandidateDTO(BaseModel):
    name: str
    link: str
    annual_cost_per_mw: int = Field(alias="annual-cost-per-mw")
    unit_size: Optional[int] = Field(None, alias="unit-size")
    max_units: Optional[int] = Field(None, alias="max-units")
    max_investment: Optional[int] = Field(None, alias="max-investment")
    already_installed_capacity: Optional[int] = Field(
        None, alias="already-installed-capacity"
    )
    link_profile: Optional[str] = Field(None, alias="link-profile")
    already_installed_link_profile: Optional[str] = Field(
        None, alias="already-installed-link-profile"
    )


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

    def add_candidate(
        self, study: Study, xpansion_candidate_dto: XpansionNewCandidateDTO
    ) -> str:

        file_study = self.study_storage_service.get_storage(study).get_raw(
            study
        )
        area1, area2 = xpansion_candidate_dto.link.split(" - ")
        area_from, area_to = sorted([area1, area2])

        # Assert that the link exists
        if area_to not in file_study.config.get_links(area_from):
            raise LinkDoesNotExistError(
                f"The link from {area_from} to {area_to} does not exist"
            )

        # Find id of new candidate
        candidates = file_study.tree.get(["user", "expansion", "candidates"])
        max_id = (
            2 if not candidates else int(sorted(candidates.keys()).pop()) + 2
        )
        next_id = next(
            str(i) for i in range(1, max_id) if str(i) not in candidates
        )  # TODO: looks ugly, is there a better way to do this?

        # Add candidate
        candidates[next_id] = xpansion_candidate_dto.dict(
            by_alias=True, exclude_none=True
        )
        candidates_data = {"user": {"expansion": {"candidates": candidates}}}
        file_study.tree.save(candidates_data)

        return next_id
