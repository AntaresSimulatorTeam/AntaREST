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

import copy
import typing as t

from antares.study.version import StudyVersion
from pydantic import model_validator
from typing_extensions import override

from antarest.matrixstore.model import MatrixData
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    DEFAULT_GROUP,
    OPERATOR_MATRIX_FILE_MAP,
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import BindingConstraintDTO, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_hourly as default_bc_hourly_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_hourly as default_bc_hourly_86,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_86,
)
from antarest.study.storage.variantstudy.model.command.binding_constraint_utils import remove_bc_from_scenario_builder
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    BindingConstraintProperties,
    create_binding_constraint_properties,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import update_matrices_names
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateBindingConstraints(ICommand):
    """
    Command used to update several binding constraints.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_BINDING_CONSTRAINTS
    version: int = 1

    # Command parameters
    # ==================

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    bc_props_by_id: t.Mapping[str, BindingConstraintProperties]

    def update_in_config(self, study_data: FileStudyTreeConfig) -> CommandOutput:
        def update_binding_constraint_dto(existing_constraint: BindingConstraintDTO) -> BindingConstraintDTO:
            if existing_constraint.id in self.bc_props_by_id:
                bc_props = self.bc_props_by_id[existing_constraint.id]
                bc_props_as_dict = bc_props.model_dump(mode="json", exclude_unset=True)
                group = bc_props_as_dict.get("group") or existing_constraint.group
                operator = bc_props_as_dict.get("operator") or existing_constraint.operator
                time_step = bc_props_as_dict.get("time_step") or existing_constraint.time_step
                return BindingConstraintDTO(
                    id=existing_constraint.id,
                    group=group,
                    areas=existing_constraint.areas,
                    clusters=existing_constraint.clusters,
                    operator=operator,
                    time_step=time_step,
                )
            return existing_constraint

        existing_ids = {b.id for b in study_data.bindings}
        for bc_id, _ in self.bc_props_by_id.items():
            if bc_id not in existing_ids:
                return CommandOutput(
                    status=False,
                    message=f"Binding contraint '{bc_id}' not found in study config id : {study_data.study_id}.",
                )
        study_data.bindings = list(map(update_binding_constraint_dto, study_data.bindings))
        return CommandOutput(
            status=True,
            message=f"UpdatedBindingConstraints command applied successfully on study {study_data.study_id}.",
        )

    @model_validator(mode="before")
    @classmethod
    def check_version_consistency(cls, values: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """
        Make sure this object is buit with bc props that matches the study version.
        """
        bc_props_by_id = values["bc_props_by_id"]
        study_version = values["study_version"]
        bc_props_by_id_validated = {}
        for bc_id, bc_props in bc_props_by_id.items():
            # bc_props_by_id can be a dict or a mapping of BindingConstraintProperties object
            # when the command is serialized to the database, the bc_props are serialized as a dict in to_dto
            # at some point the app will create an instance of this object using the command dto
            # so we need to handle both cases
            if isinstance(bc_props, dict):
                bc_props_as_dict = bc_props
            else:
                bc_props_as_dict = bc_props.model_dump(mode="json", exclude_unset=True)
            bc_props_validated = create_binding_constraint_properties(study_version, **bc_props_as_dict)
            bc_props_by_id_validated[bc_id] = bc_props_validated
        values["bc_props_by_id"] = bc_props_by_id_validated
        return values

    @override
    def _apply(self, file_study: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        bcs_url = ["input", "bindingconstraints", "bindingconstraints"]
        bcs_json = file_study.tree.get(bcs_url)
        bc_index_by_id = {value["id"]: key for (key, value) in bcs_json.items()}  # 'bc_0': '0', 'bc_1': '1', ...
        old_groups = set()
        new_groups = set()
        for bc_id, bc_props in self.bc_props_by_id.items():
            if bc_id not in bc_index_by_id:
                return CommandOutput(
                    status=False,
                    message=f"Binding contraint '{bc_id}' not found in study.",
                )
            # It's important to use exclude_unset=True. Otherwise we'd override
            # existing values with the default bc_props values.
            bc_props_as_dict = bc_props.model_dump(mode="json", by_alias=True, exclude_unset=True)
            bc_json = bcs_json[bc_index_by_id[bc_id]]
            current_properties = copy.deepcopy(bc_json)
            bc_json.update(bc_props_as_dict)
            current_operator = BindingConstraintOperator(current_properties["operator"])

            # Time Step
            existing_time_step = BindingConstraintFrequency(current_properties["type"])
            new_time_step = BindingConstraintFrequency(bc_props_as_dict.get("type", current_properties["type"]))
            if new_time_step != existing_time_step:
                # The user changed the time step, we need to update the matrix accordingly
                for [target, new_matrix] in generate_replacement_matrices(
                    bc_id, self.study_version, new_time_step, current_operator
                ):
                    # prepare matrix as a dict to save it in the tree
                    matrix_url = target.split("/")
                    file_study.tree.save(data={"data": new_matrix}, url=matrix_url)

            if self.study_version >= STUDY_VERSION_8_7:
                # Groups
                old_groups.add(current_properties.get("group", DEFAULT_GROUP).lower())
                new_groups.add(bc_props_as_dict.get("group", DEFAULT_GROUP).lower())

                # Operator
                new_operator = BindingConstraintOperator(
                    bc_props_as_dict.get("operator", current_properties["operator"])
                )
                if new_operator != current_operator:
                    # The user changed the operator, we have to rename matrices accordingly
                    update_matrices_names(file_study, bc_id, current_operator, new_operator)

        # Groups
        removed_groups = old_groups - new_groups
        remove_bc_from_scenario_builder(file_study, removed_groups)

        file_study.tree.save(bcs_json, bcs_url)
        return self.update_in_config(file_study.config)

    @override
    def to_dto(self) -> CommandDTO:
        excluded_fields = set(ICommand.model_fields)
        json_command = self.model_dump(mode="json", exclude=excluded_fields, exclude_unset=True)
        return CommandDTO(
            action=self.command_name.value, args=json_command, version=self.version, study_version=self.study_version
        )

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return []


def generate_replacement_matrices(
    bc_id: str,
    study_version: StudyVersion,
    new_time_step: BindingConstraintFrequency,
    current_operator: BindingConstraintOperator,
) -> t.Iterator[t.Tuple[str, t.List[t.List[MatrixData]]]]:
    """
    Yield one (or two when operator is "BOTH") matrices initialized with default values.
    """
    if study_version < STUDY_VERSION_8_7:
        target = f"input/bindingconstraints/{bc_id}"
        matrix = {
            BindingConstraintFrequency.HOURLY: default_bc_hourly_86,
            BindingConstraintFrequency.DAILY: default_bc_weekly_daily_86,
            BindingConstraintFrequency.WEEKLY: default_bc_weekly_daily_86,
        }[new_time_step].tolist()
        yield target, matrix
    else:
        matrix = {
            BindingConstraintFrequency.HOURLY: default_bc_hourly_87,
            BindingConstraintFrequency.DAILY: default_bc_weekly_daily_87,
            BindingConstraintFrequency.WEEKLY: default_bc_weekly_daily_87,
        }[new_time_step].tolist()
        matrices_to_replace = OPERATOR_MATRIX_FILE_MAP[current_operator]
        for matrix_name in matrices_to_replace:
            matrix_id = matrix_name.format(bc_id=bc_id)
            target = f"input/bindingconstraints/{matrix_id}"
            yield target, matrix
