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
import typing as t

from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.model import JSON
from antarest.study.model import (
    STUDY_VERSION_6_5,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_7,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils_binding_constraint import (
    remove_area_cluster_from_binding_constraints,
)
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
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

    @override
    def _apply_config(self, study_data_config: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
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

    def _remove_area_from_binding_constraints(self, study_data: FileStudy) -> None:
        """
        Remove the binding constraints that are related to the area.

        Notes:
            A binding constraint has properties, a list of terms (which form a linear equation) and
            a right-hand side (which is the matrix of the binding constraint).
            The terms are of the form `area1%area2` or `area.cluster` where `area` is the ID of the area
            and `cluster` is the ID of the cluster.

            When an area is removed, it has an impact on the terms of the binding constraints.
            At first, we could decide to remove the terms that are related to the area.
            However, this would lead to a linear equation that is not valid anymore.

            Instead, we decide to remove the binding constraints that are related to the area.
        """
        # See also `RemoveArea`
        # noinspection SpellCheckingInspection
        url = ["input", "bindingconstraints", "bindingconstraints"]
        binding_constraints = study_data.tree.get(url)

        # Collect the binding constraints that are related to the area to remove
        # by searching the terms that contain the ID of the area.
        bc_to_remove = {}
        lower_area_id = self.id.lower()
        for bc_index, bc in list(binding_constraints.items()):
            for key in bc:
                # Term IDs are in the form `area1%area2` or `area.cluster`
                if "%" in key:
                    related_areas = key.split("%")
                elif "." in key:
                    related_areas = key.split(".")[:-1]
                else:
                    # This key belongs to the set of properties, it isn't a term ID, so we skip it
                    continue
                related_areas = [area.lower() for area in related_areas]
                if lower_area_id in related_areas:
                    bc_to_remove[bc_index] = binding_constraints.pop(bc_index)
                    break

        matrix_suffixes = ["_lt", "_gt", "_eq"] if study_data.config.version >= STUDY_VERSION_8_7 else [""]

        for bc_index, bc in bc_to_remove.items():
            for suffix in matrix_suffixes:
                # noinspection SpellCheckingInspection
                study_data.tree.delete(["input", "bindingconstraints", f"{bc['id']}{suffix}"])

        study_data.tree.save(binding_constraints, url)

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
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
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
        self._remove_area_from_binding_constraints(study_data)
        self._remove_area_from_correlation_matrices(study_data)
        self._remove_area_from_hydro_allocation(study_data)
        self._remove_area_from_districts(study_data)
        self._remove_area_from_scenario_builder(study_data)

        output, _ = self._apply_config(study_data.config)

        new_area_data: JSON = {"input": {"areas": {"list": [area.name for area in study_data.config.areas.values()]}}}
        study_data.tree.save(new_area_data)

        return output

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
    def get_inner_matrices(self) -> t.List[str]:
        return []
