import contextlib
import logging
from typing import Any, Dict, List, Tuple

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import ChildNotFoundError
from antarest.study.storage.variantstudy.business.utils_binding_constraint import (
    remove_area_cluster_from_binding_constraints,
)
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


class RemoveArea(ICommand):
    """
    Command used to remove an area.
    """

    command_name = CommandName.REMOVE_AREA
    version: int = 1

    # Properties of the `REMOVE_AREA` command:
    id: str

    def _remove_area_from_links_in_config(self, study_data_config: FileStudyTreeConfig) -> None:
        link_to_remove = [
            (area_name, link)
            for area_name, area in study_data_config.areas.items()
            for link in area.links
            if link == self.id
        ]
        for area_name, link in link_to_remove:
            del study_data_config.areas[area_name].links[link]

    def _remove_area_from_sets_in_config(self, study_data_config: FileStudyTreeConfig) -> None:
        for id, set in study_data_config.sets.items():
            if set.areas and self.id in set.areas:
                with contextlib.suppress(ValueError):
                    set.areas.remove(self.id)
                    study_data_config.sets[id] = set

    def _apply_config(self, study_data_config: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        del study_data_config.areas[self.id]

        self._remove_area_from_links_in_config(study_data_config)
        self._remove_area_from_sets_in_config(study_data_config)

        remove_area_cluster_from_binding_constraints(study_data_config, self.id)

        return (
            CommandOutput(status=True, message=f"Area '{self.id}' deleted"),
            {},
        )

    def _remove_area_from_links(self, study_data: FileStudy) -> None:
        for area_name, area in study_data.config.areas.items():
            for link in area.links:
                if link == self.id:
                    study_data.tree.delete(["input", "links", area_name, "properties", self.id])
                    try:
                        if study_data.config.version < 820:
                            study_data.tree.delete(["input", "links", area_name, self.id])
                        else:
                            study_data.tree.delete(["input", "links", area_name, f"{self.id}_parameters"])
                            study_data.tree.delete(["input", "links", area_name, "capacities", f"{self.id}_indirect"])
                            study_data.tree.delete(["input", "links", area_name, "capacities", f"{self.id}_direct"])

                    except ChildNotFoundError as e:
                        logger.warning(
                            f"Failed to clean link data when deleting area {self.id}"
                            f" in study {study_data.config.study_id}",
                            exc_info=e,
                        )

    def _remove_area_from_binding_constraints(self, study_data: FileStudy) -> None:
        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        id_to_remove = {bc_id for bc_id, bc in binding_constraints.items() for key in bc if self.id in key}

        for bc_id in id_to_remove:
            if study_data.config.version < 870:
                study_data.tree.delete(["input", "bindingconstraints", binding_constraints[bc_id]["id"]])
            else:
                for name in ["lt", "gt", "eq"]:
                    study_data.tree.delete(
                        ["input", "bindingconstraints", f"{binding_constraints[bc_id]['id']}_{name}"]
                    )
            del binding_constraints[bc_id]

        study_data.tree.save(binding_constraints, ["input", "bindingconstraints", "bindingconstraints"])

    def _remove_area_from_hydro_allocation(self, study_data: FileStudy) -> None:
        """
        Delete the column for the hydraulic production area
        and updates the rows for the other areas.

        Args:
            study_data: file study
        """
        study_data.tree.delete(["input", "hydro", "allocation", self.id])
        allocation_cfg = study_data.tree.get(["input", "hydro", "allocation", "*"])
        if len(allocation_cfg) == 1:
            # IMPORTANT: when there is only one element left the function returns
            # the allocation of the element in place of the dictionary by zone
            allocation_cfg = {self.id: allocation_cfg}
        allocation_cfg.pop(self.id, None)  # ensure allocation is removed
        for prod_area, allocation_dict in allocation_cfg.items():
            for name, allocations in allocation_dict.items():
                allocations.pop(self.id, None)
        study_data.tree.save(allocation_cfg, ["input", "hydro", "allocation"])

    def _remove_area_from_correlation_matrices(self, study_data: FileStudy) -> None:
        """
        Removes the values from the correlation matrix that match the current area.

        This function can update the following configurations:
        - ["input", "hydro", "prepro", "correlation"]

        Args:
            study_data:File Study to update.
        """
        # Today, only the 'hydro' category is fully supported, but
        # we could also manage the 'load' 'solar' and 'wind'
        # categories but the usage is deprecated.
        url = ["input", "hydro", "prepro", "correlation"]
        correlation_cfg = study_data.tree.get(url)
        for section, correlation in correlation_cfg.items():
            if section == "general":
                continue
            for key in list(correlation):
                a1, a2 = key.split("%")
                if a1 == self.id or a2 == self.id:
                    del correlation[key]
        study_data.tree.save(correlation_cfg, url)

    def _remove_area_from_districts(self, study_data: FileStudy) -> None:
        districts = study_data.tree.get(["input", "areas", "sets"])
        for district in districts.values():
            if district.get("+", None):
                with contextlib.suppress(ValueError):
                    district["+"].remove(self.id)
            elif district.get("-", None):
                with contextlib.suppress(ValueError):
                    district["-"].remove(self.id)

        study_data.tree.save(districts, ["input", "areas", "sets"])

    def _remove_area_from_cluster(self, study_data: FileStudy) -> None:
        study_data.tree.delete(["input", "thermal", "prepro", self.id])

    def _remove_area_from_time_series(self, study_data: FileStudy) -> None:
        study_data.tree.delete(["input", "thermal", "series", self.id])

    # noinspection SpellCheckingInspection
    def _apply(self, study_data: FileStudy) -> CommandOutput:
        study_data.tree.delete(["input", "areas", self.id])
        study_data.tree.delete(["input", "hydro", "common", "capacity", f"maxpower_{self.id}"])
        study_data.tree.delete(["input", "hydro", "common", "capacity", f"reservoir_{self.id}"])
        study_data.tree.delete(["input", "hydro", "prepro", self.id])
        study_data.tree.delete(["input", "hydro", "series", self.id])
        study_data.tree.delete(["input", "hydro", "hydro", "inter-daily-breakdown", self.id])
        study_data.tree.delete(["input", "hydro", "hydro", "intra-daily-modulation", self.id])
        study_data.tree.delete(["input", "hydro", "hydro", "inter-monthly-breakdown", self.id])
        study_data.tree.delete(["input", "load", "prepro", self.id])
        study_data.tree.delete(["input", "load", "series", f"load_{self.id}"])
        study_data.tree.delete(["input", "misc-gen", f"miscgen-{self.id}"])
        study_data.tree.delete(["input", "reserves", self.id])
        study_data.tree.delete(["input", "solar", "prepro", self.id])
        study_data.tree.delete(["input", "solar", "series", f"solar_{self.id}"])
        study_data.tree.delete(["input", "thermal", "clusters", self.id])
        study_data.tree.delete(["input", "thermal", "areas", "unserverdenergycost", self.id])
        study_data.tree.delete(["input", "thermal", "areas", "spilledenergycost", self.id])
        study_data.tree.delete(["input", "wind", "prepro", self.id])
        study_data.tree.delete(["input", "wind", "series", f"wind_{self.id}"])
        study_data.tree.delete(["input", "links", self.id])

        if study_data.config.version > 650:
            study_data.tree.delete(["input", "hydro", "hydro", "initialize reservoir date", self.id])
            study_data.tree.delete(["input", "hydro", "hydro", "leeway low", self.id])
            study_data.tree.delete(["input", "hydro", "hydro", "leeway up", self.id])
            study_data.tree.delete(["input", "hydro", "hydro", "pumping efficiency", self.id])
            study_data.tree.delete(["input", "hydro", "common", "capacity", f"creditmodulations_{self.id}"])
            study_data.tree.delete(["input", "hydro", "common", "capacity", f"inflowPattern_{self.id}"])
            study_data.tree.delete(["input", "hydro", "common", "capacity", f"waterValues_{self.id}"])

        if study_data.config.version >= 860:
            study_data.tree.delete(["input", "st-storage", "clusters", self.id])
            study_data.tree.delete(["input", "st-storage", "series", self.id])

        self._remove_area_from_links(study_data)
        self._remove_area_from_binding_constraints(study_data)
        self._remove_area_from_correlation_matrices(study_data)
        self._remove_area_from_hydro_allocation(study_data)
        self._remove_area_from_districts(study_data)
        self._remove_area_from_cluster(study_data)
        self._remove_area_from_time_series(study_data)

        output, _ = self._apply_config(study_data.config)

        new_area_data: JSON = {
            "input": {
                "areas": {
                    "list": [area.name for area in study_data.config.areas.values()],
                }
            }
        }
        study_data.tree.save(new_area_data)

        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_AREA.value,
            args={
                "id": self.id,
            },
        )

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id)

    def match(self, other: ICommand, equal: bool = False) -> bool:
        return isinstance(other, RemoveArea) and self.id == other.id

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
