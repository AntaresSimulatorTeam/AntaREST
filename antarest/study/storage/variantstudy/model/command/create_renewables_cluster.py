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

import typing as t

from pydantic import field_validator
from typing_extensions import override

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    EnrModelling,
    FileStudyTreeConfig,
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import create_renewable_config
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateRenewablesCluster(ICommand):
    """
    Command used to create a renewable cluster in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_RENEWABLES_CLUSTER
    version: int = 1

    # Command parameters
    # ==================

    area_id: str
    cluster_name: str
    parameters: t.Dict[str, t.Any]

    @field_validator("cluster_name")
    def validate_cluster_name(cls, val: str) -> str:
        valid_name = transform_name_to_id(val, lower=False)
        if valid_name != val:
            raise ValueError("Area name must only contains [a-zA-Z0-9],&,-,_,(,) characters")
        return val

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        if EnrModelling(study_data.enr_modelling) != EnrModelling.CLUSTERS:
            # Since version 8.1 of the solver, we can use renewable clusters
            # instead of "Load", "Wind" and "Solar" objects for modelling.
            # When the "renewable-generation-modelling" parameter is set to "aggregated",
            # it means that we want to ensure compatibility with previous versions.
            # To use renewable clusters, the parameter must therefore be set to "clusters".
            message = (
                f"Parameter 'renewable-generation-modelling'"
                f" must be set to '{EnrModelling.CLUSTERS}'"
                f" instead of '{study_data.enr_modelling}'"
            )
            return CommandOutput(status=False, message=message), {}

        # Search the Area in the configuration
        if self.area_id not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"Area '{self.area_id}' does not exist in the study configuration.",
                ),
                {},
            )
        area: Area = study_data.areas[self.area_id]

        # Check if the cluster already exists in the area
        version = study_data.version
        cluster = create_renewable_config(version, name=self.cluster_name)
        if any(cl.id == cluster.id for cl in area.renewables):
            return (
                CommandOutput(
                    status=False,
                    message=f"Renewable cluster '{cluster.id}' already exists in the area '{self.area_id}'.",
                ),
                {},
            )

        area.renewables.append(cluster)

        return (
            CommandOutput(
                status=True,
                message=f"Renewable cluster '{cluster.id}' added to area '{self.area_id}'.",
            ),
            {"cluster_id": cluster.id},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output

        # default values
        if "ts-interpretation" not in self.parameters:
            self.parameters["ts-interpretation"] = "power-generation"
        self.parameters.setdefault("name", self.cluster_name)

        cluster_id = data["cluster_id"]
        config = study_data.tree.get(["input", "renewables", "clusters", self.area_id, "list"])
        config[cluster_id] = self.parameters

        # Series identifiers are in lower case.
        series_id = cluster_id.lower()
        new_cluster_data: JSON = {
            "input": {
                "renewables": {
                    "clusters": {self.area_id: {"list": config}},
                    "series": {
                        self.area_id: {
                            series_id: {"series": self.command_context.generator_matrix_constants.get_null_matrix()}
                        }
                    },
                }
            }
        }
        study_data.tree.save(new_cluster_data)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "cluster_name": self.cluster_name,
                "parameters": self.parameters,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return []
