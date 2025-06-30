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

from typing import List, Optional

from typing_extensions import override

from antarest.core.exceptions import ReferencedObjectDeletionNotAllowed
from antarest.study.business.model.binding_constraint_model import ClusterTerm
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveCluster(ICommand):
    """
    Command used to remove a thermal cluster in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_THERMAL_CLUSTER

    # Command parameters
    # ==================

    area_id: str
    cluster_id: str

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if not study_data.thermal_exists(self.area_id, self.cluster_id):
            return command_failed(f"Thermal cluster '{self.cluster_id}' in area '{self.area_id}' does not exist")
        thermal = study_data.get_thermal(self.area_id, self.cluster_id)

        # Checks that the cluster is not referenced in any binding constraint
        lowered_id = thermal.id.lower()  # Thermal ids are stored in lowercase in the INI file
        referencing_binding_constraints = []
        for bc in study_data.get_all_constraints().values():
            for term in bc.terms:
                data = term.data
                if isinstance(data, ClusterTerm) and data.area == self.area_id and data.cluster == lowered_id:
                    referencing_binding_constraints.append(bc)
                    break
        if referencing_binding_constraints:
            binding_ids = [bc.id for bc in referencing_binding_constraints]
            raise ReferencedObjectDeletionNotAllowed(lowered_id, binding_ids, object_type="Cluster")

        # Delete the cluster
        study_data.delete_thermal(self.area_id, thermal)
        return command_succeeded(f"Thermal cluster '{self.cluster_id}' inside area '{self.area_id}' deleted")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"area_id": self.area_id, "cluster_id": self.cluster_id},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
