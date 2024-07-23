import json
import typing as t

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    DEFAULT_GROUP,
    AbstractBindingConstraintCommand,
    TermMatrices,
    create_binding_constraint_config,
)
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

MatrixType = t.List[t.List[MatrixData]]

ALIAS_OPERATOR_MAP = {
    BindingConstraintOperator.EQUAL: "eq",
    BindingConstraintOperator.LESS: "lt",
    BindingConstraintOperator.GREATER: "gt",
}


def _update_matrices_names(
    file_study: FileStudy,
    binding_constraint_id: str,
    existing_operator: BindingConstraintOperator,
    new_operator: BindingConstraintOperator,
) -> None:
    """
    Update the matrix file name according to the new operator.

    Args:
        file_study: the file study
        binding_constraint_id: the binding constraint ID
        existing_operator: the existing operator
        new_operator: the new operator

    Raises:
        NotImplementedError: if the case is not handled
    """

    parent_folder_node = file_study.tree.get_node(["input", "bindingconstraints"])
    matrix_lt = parent_folder_node.get_node([f"{binding_constraint_id}_lt"])
    assert isinstance(matrix_lt, LazyNode), f"Node type not handled yet: LazyNode expected, got {type(matrix_lt)}"
    matrix_eq = parent_folder_node.get_node([f"{binding_constraint_id}_eq"])
    assert isinstance(matrix_eq, LazyNode), f"Node type not handled yet: LazyNode expected, got {type(matrix_eq)}"
    matrix_gt = parent_folder_node.get_node([f"{binding_constraint_id}_gt"])
    assert isinstance(matrix_gt, LazyNode), f"Node type not handled yet: LazyNode expected, got {type(matrix_gt)}"

    # Due to legacy matrices generation, we need to check if the new matrix file already exists
    #  and if it does, we need to first remove it before renaming the existing matrix file

    handled_operators = [
        BindingConstraintOperator.EQUAL,
        BindingConstraintOperator.LESS,
        BindingConstraintOperator.GREATER,
        BindingConstraintOperator.BOTH,
    ]

    if (existing_operator not in handled_operators) or (new_operator not in handled_operators):
        raise NotImplementedError(
            f"Case not handled yet: existing_operator={existing_operator}, new_operator={new_operator}"
        )
    elif existing_operator == new_operator:
        return  # nothing to do
    elif existing_operator != BindingConstraintOperator.BOTH and new_operator != BindingConstraintOperator.BOTH:
        matrix_node = parent_folder_node.get_node([f"{binding_constraint_id}_{ALIAS_OPERATOR_MAP[existing_operator]}"])
        assert isinstance(
            matrix_node, LazyNode
        ), f"Node type not handled yet: LazyNode expected, got {type(matrix_node)}"
        new_matrix_node = parent_folder_node.get_node([f"{binding_constraint_id}_{ALIAS_OPERATOR_MAP[new_operator]}"])
        assert isinstance(
            new_matrix_node, LazyNode
        ), f"Node type not handled yet: LazyNode expected, got {type(new_matrix_node)}"
        matrix_node.rename_filename(new_matrix_node)
    elif new_operator == BindingConstraintOperator.BOTH:
        if existing_operator == BindingConstraintOperator.EQUAL:
            matrix_eq.rename_filename(matrix_lt)
            matrix_gt.delete()
            # copy the matrix lt to gt
            matrix_lt.copy_file(matrix_gt)
        elif existing_operator == BindingConstraintOperator.LESS:
            matrix_gt.delete()
            matrix_lt.copy_file(matrix_gt)
        else:
            matrix_lt.delete()
            matrix_gt.copy_file(matrix_lt)
    else:
        if new_operator == BindingConstraintOperator.EQUAL:
            # we may retrieve the mean of the two matrices, but here we just copy the lt matrix
            matrix_lt.rename_filename(matrix_eq)
            matrix_gt.delete()
        elif new_operator == BindingConstraintOperator.LESS:
            matrix_gt.delete()
        else:
            matrix_lt.delete()


class UpdateBindingConstraint(AbstractBindingConstraintCommand):
    """
    Command used to update a binding constraint.
    """

    # Overloaded metadata
    # ===================

    command_name = CommandName.UPDATE_BINDING_CONSTRAINT
    version: int = 1

    # Command parameters
    # ==================

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    id: str

    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
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

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        # When all BC of a given group are removed, the group should be removed from the scenario builder
        old_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in binding_constraints.values()}

        index_and_cfg = self._find_binding_config(binding_constraints)
        if index_and_cfg is None:
            return CommandOutput(
                status=False,
                message="The binding constraint with ID '{self.id}' does not exist",
            )

        index, actual_cfg = index_and_cfg

        # rename matrices if the operator has changed for version >= 870
        if self.operator and study_data.config.version >= 870:
            existing_operator = BindingConstraintOperator(actual_cfg.get("operator"))
            new_operator = BindingConstraintOperator(self.operator)
            _update_matrices_names(study_data, self.id, existing_operator, new_operator)

        updated_matrices = [
            term for term in [m.value for m in TermMatrices] if hasattr(self, term) and getattr(self, term)
        ]
        study_version = study_data.config.version
        time_step = self.time_step or BindingConstraintFrequency(actual_cfg.get("type"))
        self.validates_and_fills_matrices(
            time_step=time_step, specific_matrices=updated_matrices or None, version=study_version, create=False
        )

        study_version = study_data.config.version
        props = create_binding_constraint_config(study_version, **self.dict())
        obj = json.loads(props.json(by_alias=True, exclude_unset=True))

        updated_cfg = binding_constraints[index]
        updated_cfg.update(obj)

        excluded_fields = set(ICommand.__fields__) | {"id"}
        updated_properties = self.dict(exclude=excluded_fields, exclude_none=True)
        # This 2nd check is here to remove the last term.
        if self.coeffs or updated_properties == {"coeffs": {}}:
            # Remove terms which IDs contain a "%" or a "." in their name
            term_ids = {k for k in updated_cfg if "%" in k or "." in k}
            binding_constraints[index] = {k: v for k, v in updated_cfg.items() if k not in term_ids}

        return super().apply_binding_constraint(study_data, binding_constraints, index, self.id, old_groups=old_groups)

    def to_dto(self) -> CommandDTO:
        matrices = ["values"] + [m.value for m in TermMatrices]
        matrix_service = self.command_context.matrix_service

        excluded_fields = frozenset(ICommand.__fields__)
        json_command = json.loads(self.json(exclude=excluded_fields, exclude_none=True))
        for key in json_command:
            if key in matrices:
                json_command[key] = matrix_service.get_matrix_id(json_command[key])

        return CommandDTO(action=self.command_name.value, args=json_command, version=self.version)

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
