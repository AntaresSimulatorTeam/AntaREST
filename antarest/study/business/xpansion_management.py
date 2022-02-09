from typing import Optional, Literal, Union

from pydantic import Field, BaseModel

from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.storage_service import StudyStorageService


class XpansionSettingsDTO(BaseModel):
    optimality_gap: Optional[int] = None
    max_iteration: Optional[Union[int, Literal["inf"]]] = None
    uc_type: Optional[str] = None
    master: Optional[str] = None
    yearly_weight: Optional[str] = None
    additional_constraints: Optional[str] = Field(
        None, alias="additional-constraints"
    )
    relaxed_optimality_gap: Optional[float] = Field(
        None, alias="relaxed-optimality-gap"
    )
    cut_type: Optional[str] = Field(None, alias="cut-type")
    ampl_solver: Optional[str] = Field(None, alias="ampl.solver")
    ampl_presolve: Optional[int] = Field(None, alias="ampl.presolve")
    ampl_solve_bounds_frequency: Optional[int] = Field(
        None, alias="ampl.solve_bounds_frequency"
    )
    relative_gap: Optional[float] = None
    solver: Optional[str] = None


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
