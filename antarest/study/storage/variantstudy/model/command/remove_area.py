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
from typing import List, Optional

from typing_extensions import override

from antarest.core.exceptions import (
    AreaReferencedInsideSTStorageAdditionalConstraints,
    ChildNotFoundError,
    ReferencedObjectDeletionNotAllowed,
)
from antarest.core.model import JSON
from antarest.study.business.model.binding_constraint_model import ClusterTerm, LinkTerm
from antarest.study.model import STUDY_VERSION_6_5, STUDY_VERSION_8_1, STUDY_VERSION_8_2, STUDY_VERSION_8_6
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

logger = logging.getLogger(__name__)


class RemoveArea(ICommand):
    """
    Command used to remove an area.
    """

    command_name: CommandName = CommandName.REMOVE_AREA

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
        for id_, set_ in study_data_config.sets.items():
            if set_.areas and self.id in set_.areas:
                with contextlib.suppress(ValueError):
                    set_.areas.remove(self.id)
                    study_data_config.sets[id_] = set_

    def remove_from_config(self, study_data_config: FileStudyTreeConfig) -> None:
        del study_data_config.areas[self.id]

        self._remove_area_from_links_in_config(study_data_config)
        self._remove_area_from_sets_in_config(study_data_config)

    def _remove_area_from_links(self, study_data: FileStudy) -> None:
        for area_name, area in study_data.config.areas.items():
            for link in area.links:
                if link == self.id:
                    study_data.tree.delete(["input", "links", area_name, "properties", self.id])
                    try:
                        if study_data.config.version < STUDY_VERSION_8_2:
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

    def _remove_area_from_scenario_builder(self, study_data: FileStudy) -> None:
        """
        Update the scenario builder by removing the rows that correspond to the area to remove.

        NOTE: this update can be very long if the scenario builder configuration is large.
        """
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        area_keys = {"l", "h", "w", "s", "t", "r", "hl", "hfl", "hgp"}
        link_keys = {"ntc"}
        for ruleset in rulesets.values():
            for key in list(ruleset):
                symbol, *parts = key.split(",")
                if (symbol in area_keys and parts[0] == self.id) or (
                    symbol in link_keys and (parts[0] == self.id or parts[1] == self.id)
                ):
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])

    # noinspection SpellCheckingInspection
    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        # Checks that the area is not referenced in any binding constraint
        referencing_binding_constraints = []
        for bc in study_data.config.bindings:
            for term in bc.terms:
                data = term.data
                if (isinstance(data, ClusterTerm) and data.area == self.id) or (
                    isinstance(data, LinkTerm) and (data.area1 == self.id or data.area2 == self.id)
                ):
                    referencing_binding_constraints.append(bc)
                    break
        if referencing_binding_constraints:
            binding_ids = [bc.id for bc in referencing_binding_constraints]
            raise ReferencedObjectDeletionNotAllowed(self.id, binding_ids, object_type="Area")

        # Checks that the area is not referenced in any st-storage constraint
        path = ["input", "st-storage", "constraints", self.id]
        with contextlib.suppress(ChildNotFoundError):
            files = study_data.tree.get(path, depth=1)
            if files:
                raise AreaReferencedInsideSTStorageAdditionalConstraints(self.id)

        # Delete files
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
        study_data.tree.delete(["input", "thermal", "prepro", self.id])
        study_data.tree.delete(["input", "thermal", "series", self.id])
        study_data.tree.delete(["input", "thermal", "areas", "unserverdenergycost", self.id])
        study_data.tree.delete(["input", "thermal", "areas", "spilledenergycost", self.id])
        study_data.tree.delete(["input", "wind", "prepro", self.id])
        study_data.tree.delete(["input", "wind", "series", f"wind_{self.id}"])
        study_data.tree.delete(["input", "links", self.id])

        study_version = study_data.config.version
        if study_version > STUDY_VERSION_6_5:
            study_data.tree.delete(["input", "hydro", "hydro", "initialize reservoir date", self.id])
            study_data.tree.delete(["input", "hydro", "hydro", "leeway low", self.id])
            study_data.tree.delete(["input", "hydro", "hydro", "leeway up", self.id])
            study_data.tree.delete(["input", "hydro", "hydro", "pumping efficiency", self.id])
            study_data.tree.delete(["input", "hydro", "common", "capacity", f"creditmodulations_{self.id}"])
            study_data.tree.delete(["input", "hydro", "common", "capacity", f"inflowPattern_{self.id}"])
            study_data.tree.delete(["input", "hydro", "common", "capacity", f"waterValues_{self.id}"])

        if study_version >= STUDY_VERSION_8_1:
            with contextlib.suppress(ChildNotFoundError):
                #  renewables folder only exist in tree if study.renewable-generation-modelling is "clusters"
                study_data.tree.delete(["input", "renewables", "clusters", self.id])
                study_data.tree.delete(["input", "renewables", "series", self.id])

        if study_version >= STUDY_VERSION_8_6:
            study_data.tree.delete(["input", "st-storage", "clusters", self.id])
            study_data.tree.delete(["input", "st-storage", "series", self.id])

        self._remove_area_from_links(study_data)
        self._remove_area_from_correlation_matrices(study_data)
        self._remove_area_from_hydro_allocation(study_data)
        self._remove_area_from_districts(study_data)
        self._remove_area_from_scenario_builder(study_data)

        self.remove_from_config(study_data.config)

        new_area_data: JSON = {"input": {"areas": {"list": [area.name for area in study_data.config.areas.values()]}}}
        study_data.tree.save(new_area_data)

        return command_succeeded(message=f"Area '{self.id}' deleted")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_AREA.value,
            args={
                "id": self.id,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
