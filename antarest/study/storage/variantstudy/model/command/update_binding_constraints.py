# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.business.binding_constraint_management import OPERATOR_MATRIX_FILE_MAP, ConstraintInput
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode
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
from antarest.study.storage.variantstudy.business.utils import AliasDecoder
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    AbstractBindingConstraintCommand,
    TermMatrices,
    create_binding_constraint_config,
)
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import update_matrices_names
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateBindingConstraints(AbstractBindingConstraintCommand):
    """
    Command used to update a binding constraint.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_BINDING_CONSTRAINT
    version: int = 1

    # Command parameters
    # ==================

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    id: str
    # TODO input should be ConstraintProperties
    # TODO
    bcs_by_ids: t.Mapping[str, ConstraintInput]

    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        # index = next(i for i, bc in enumerate(study_data.bindings) if bc.id == self.id)
        # existing_constraint = study_data.bindings[index]
        # areas_set = existing_constraint.areas
        # clusters_set = existing_constraint.clusters
        # if self.coeffs:
        #     areas_set = set()
        #     clusters_set = set()
        #     for j in self.coeffs.keys():
        #         if "%" in j:
        #             areas_set |= set(j.split("%"))
        #         elif "." in j:
        #             clusters_set.add(j)
        #             areas_set.add(j.split(".")[0])
        # group = self.group or existing_constraint.group
        # operator = self.operator or existing_constraint.operator
        # time_step = self.time_step or existing_constraint.time_step
        # new_constraint = BindingConstraintDTO(
        #     id=self.id,
        #     group=group,
        #     areas=areas_set,
        #     clusters=clusters_set,
        #     operator=operator,
        #     time_step=time_step,
        # )
        # study_data.bindings[index] = new_constraint
        return CommandOutput(status=True), {}

    def _find_binding_config(self, binding_constraints: t.Mapping[str, JSON]) -> t.Optional[t.Tuple[str, JSON]]:
        """
        Find the binding constraint with the given ID in the list of binding constraints,
        and returns its index and configuration, or `None` if it does not exist.
        """
        for index, binding_config in binding_constraints.items():
            if binding_config["id"] == self.id:
                # convert to string because the index could be an integer
                return str(index), binding_config
        return None

    def _apply(self, file_study: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        study_version = file_study.config.version
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        dict_config = {value["id"]: key for (key, value) in config.items()}
        # next_bc_props_by_id = {}
        for bc_id, bc_input in self.bcs_by_ids.items():
            if bc_id not in dict_config:
                return CommandOutput(
                    status=False,
                    message=f"Binding contraint '{bc_id}' not found.",
                )

            input_bc_props = create_binding_constraint_config(study_version, **bc_input.model_dump())
            new_bc_props = input_bc_props.model_dump(mode="json", by_alias=True, exclude_unset=True)
            next_bc_props = config[dict_config[bc_id]]
            prev_bc_props = copy.deepcopy(next_bc_props)
            next_bc_props.update(new_bc_props)
            # output = BindingConstraintManager.constraint_model_adapter(next_bc_props, study_version)
            # next_bc_props_by_id[bc_id] = next_bc_props

            if bc_input.time_step and bc_input.time_step != BindingConstraintFrequency(prev_bc_props["type"]):
                # The user changed the time step, we need to update the matrix accordingly
                for [target, next_matrice] in self.generate_replacement_matrices():
                    try:
                        self.save_matrix(file_study, target, next_matrice)
                    except (KeyError, ChildNotFoundError):
                        return CommandOutput(
                            status=False,
                            message=f"Path '{self.target}' does not exist.",
                        )
                    except AssertionError:
                        return CommandOutput(
                            status=False,
                            message=f"Path '{self.target}' does not target a matrix.",
                        )
                    except Exception:
                        return CommandOutput(
                            status=False,
                            message=f"Couldn't save matrix {target}.",
                        )

            if bc_input.operator and study_version >= STUDY_VERSION_8_7:
                # The user changed the operator, we have to rename matrices accordingly
                existing_operator = BindingConstraintOperator(prev_bc_props["operator"])
                update_matrices_names(file_study, bc_id, existing_operator, bc_input.operator)

        # call appl_config on this constraint
        study_file_target = "input/bindingconstraints/bindingconstraints"
        url = study_file_target.split("/")
        tree_node = file_study.tree.get_node(url)
        if not isinstance(tree_node, IniFileNode):
            return CommandOutput(
                status=False,
                message=f"Study node at path {study_file_target} is invalid",
            )
        file_study.tree.save(self.data, url)

        # TODO add group logic remove_bc_from_scenario_builder(study_data, removed_groups)
        return CommandOutput(status=True, message="ok"), {}

    def to_dto(self) -> CommandDTO:
        matrices = ["values"] + [m.value for m in TermMatrices]
        matrix_service = self.command_context.matrix_service

        excluded_fields = set(ICommand.model_fields)
        json_command = self.model_dump(mode="json", exclude=excluded_fields, exclude_none=True)
        for key in json_command:
            if key in matrices:
                json_command[key] = matrix_service.get_matrix_id(json_command[key])

        return CommandDTO(
            action=self.command_name.value, args=json_command, version=self.version, study_version=self.study_version
        )

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id)

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        return [other]

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if not equal:
            return self.id == other.id
        return super().match(other, equal)

    # def replace_and_save_matrix():

    def save_matrix(self, study_data: FileStudy, target: str, matrix: t.Union[t.List[t.List[MatrixData]], str]):
        if target[0] == "@":
            target = AliasDecoder.decode(target, study_data)

        replace_matrix_data: JSON = {}
        target_matrix = replace_matrix_data
        url = target.split("/")
        for element in url[:-1]:
            target_matrix[element] = {}
            target_matrix = target_matrix[element]

        target_matrix[url[-1]] = matrix

        try:
            last_node = study_data.tree.get_node(url)
            assert_this(isinstance(last_node, MatrixNode))
        except (KeyError, ChildNotFoundError):
            return CommandOutput(
                status=False,
                message=f"Path '{target}' does not exist.",
            )
        except AssertionError:
            return CommandOutput(
                status=False,
                message=f"Path '{target}' does not target a matrix.",
            )

        study_data.tree.save(replace_matrix_data)

    def generate_replacement_matrices(
        bc_id: str,
        study_version: StudyVersion,
        value: ConstraintInput,
        operator: BindingConstraintOperator,
    ) -> t.Iterator[t.Tuple[str, t.Union[t.List[t.List[MatrixData]], str]]]:
        if study_version < STUDY_VERSION_8_7:
            target = f"input/bindingconstraints/{bc_id}"
            matrix = {
                BindingConstraintFrequency.HOURLY.value: default_bc_hourly_86,
                BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_86,
                BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_86,
            }[value.time_step].tolist()
            yield (target, matrix)
        else:
            matrix = {
                BindingConstraintFrequency.HOURLY.value: default_bc_hourly_87,
                BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_87,
                BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_87,
            }[value.time_step].tolist()
            matrices_to_replace = OPERATOR_MATRIX_FILE_MAP[operator]
            for matrix_name in matrices_to_replace:
                matrix_id = matrix_name.format(bc_id=bc_id)
                target = f"input/bindingconstraints/{matrix_id}"
                yield (target, matrix)
