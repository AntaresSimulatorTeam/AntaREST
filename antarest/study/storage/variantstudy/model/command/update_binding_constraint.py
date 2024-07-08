import json
import shutil
import typing as t
from pathlib import Path

from pydantic import BaseModel, Field

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    DEFAULT_GROUP,
    TERM_MATRICES,
    AbstractBindingConstraintCommand,
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


class MatrixInputTargetPaths(BaseModel, frozen=True, extra="forbid"):
    """
    Model used to store the input and target paths for matrices.
    """

    matrix_input_paths: t.List[Path] = Field(..., min_items=1, max_items=2)
    matrix_target_paths: t.List[Path] = Field(..., min_items=1, max_items=2)


def _infer_input_and_target_paths(
    parent_node: FolderNode,
    binding_constraint_id: str,
    existing_operator: BindingConstraintOperator,
    new_operator: BindingConstraintOperator,
) -> MatrixInputTargetPaths:
    """
    Infer the target paths of the matrices to update according to the existing and new operators.

    Args:
        parent_node: the parent folder node
        binding_constraint_id: the binding constraint ID
        existing_operator: the existing operator
        new_operator: the new operator

    Returns:
        the matrix input and target paths
    """
    # new and existing operators should be different
    assert existing_operator != new_operator, "Existing and new operators should be different"

    matrix_node_lt = parent_node.get_node([f"{binding_constraint_id}_lt"])
    assert isinstance(
        matrix_node_lt, LazyNode
    ), f"Node type not handled yet: LazyNode expected, got {type(matrix_node_lt)}"
    matrix_node_eq = parent_node.get_node([f"{binding_constraint_id}_eq"])
    assert isinstance(
        matrix_node_eq, LazyNode
    ), f"Node type not handled yet: LazyNode expected, got {type(matrix_node_eq)}"
    matrix_node_gt = parent_node.get_node([f"{binding_constraint_id}_gt"])
    assert isinstance(
        matrix_node_gt, LazyNode
    ), f"Node type not handled yet: LazyNode expected, got {type(matrix_node_gt)}"

    is_link_eq = matrix_node_eq.infer_is_link_path()
    is_link_lt = matrix_node_lt.infer_is_link_path()
    is_link_gt = matrix_node_gt.infer_is_link_path()

    if existing_operator != BindingConstraintOperator.BOTH and new_operator != BindingConstraintOperator.BOTH:
        matrix_node = parent_node.get_node([f"{binding_constraint_id}_{ALIAS_OPERATOR_MAP[existing_operator]}"])
        assert isinstance(
            matrix_node, LazyNode
        ), f"Node type not handled yet: LazyNode expected, got {type(matrix_node)}"
        new_matrix_node = parent_node.get_node([f"{binding_constraint_id}_{ALIAS_OPERATOR_MAP[new_operator]}"])
        assert isinstance(
            new_matrix_node, LazyNode
        ), f"Node type not handled yet: LazyNode expected, got {type(new_matrix_node)}"
        is_link = matrix_node.infer_is_link_path()
        return MatrixInputTargetPaths(
            matrix_input_paths=[matrix_node.infer_path()],
            matrix_target_paths=[new_matrix_node.infer_target_path(is_link)],
        )
    elif new_operator == BindingConstraintOperator.BOTH:
        if existing_operator == BindingConstraintOperator.EQUAL:
            return MatrixInputTargetPaths(
                matrix_input_paths=[matrix_node_eq.infer_path()],
                matrix_target_paths=[
                    matrix_node_lt.infer_target_path(is_link_eq),
                    matrix_node_gt.infer_target_path(is_link_eq),
                ],
            )
        elif existing_operator == BindingConstraintOperator.LESS:
            return MatrixInputTargetPaths(
                matrix_input_paths=[matrix_node_lt.infer_path()],
                matrix_target_paths=[matrix_node_lt.infer_path(), matrix_node_gt.infer_target_path(is_link_lt)],
            )
        elif existing_operator == BindingConstraintOperator.GREATER:
            return MatrixInputTargetPaths(
                matrix_input_paths=[matrix_node_gt.infer_path()],
                matrix_target_paths=[matrix_node_lt.infer_target_path(is_link_gt), matrix_node_gt.infer_path()],
            )
        else:
            raise NotImplementedError(
                f"Case not handled yet: existing_operator={existing_operator}, new_operator={new_operator}"
            )
    elif existing_operator == BindingConstraintOperator.BOTH:
        if new_operator == BindingConstraintOperator.EQUAL:
            return MatrixInputTargetPaths(
                matrix_input_paths=[matrix_node_lt.infer_path(), matrix_node_gt.infer_path()],
                matrix_target_paths=[matrix_node_eq.infer_target_path(is_link_lt)],
            )
        elif new_operator == BindingConstraintOperator.LESS:
            return MatrixInputTargetPaths(
                matrix_input_paths=[matrix_node_lt.infer_path(), matrix_node_gt.infer_path()],
                matrix_target_paths=[matrix_node_lt.infer_target_path(is_link_lt)],
            )
        elif new_operator == BindingConstraintOperator.GREATER:
            return MatrixInputTargetPaths(
                matrix_input_paths=[matrix_node_lt.infer_path(), matrix_node_gt.infer_path()],
                matrix_target_paths=[matrix_node_gt.infer_target_path(is_link_gt)],
            )
        else:
            raise NotImplementedError(
                f"Case not handled yet: existing_operator={existing_operator}, new_operator={new_operator}"
            )
    else:
        raise NotImplementedError(
            f"Case not handled yet: existing_operator={existing_operator}, new_operator={new_operator}"
        )


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

    if existing_operator == new_operator:
        return

    parent_folder_node = file_study.tree.get_node(["input", "bindingconstraints"])
    assert isinstance(parent_folder_node, FolderNode), f"Node type not handled yet: {type(parent_folder_node)}"

    matrix_paths = _infer_input_and_target_paths(
        parent_folder_node, binding_constraint_id, existing_operator, new_operator
    )

    # TODO: due to legacy matrices generation, we need to check if the new matrix file already exists
    #  and if it does, we need to first remove it before renaming the existing matrix file

    if existing_operator != BindingConstraintOperator.BOTH and new_operator != BindingConstraintOperator.BOTH:
        (matrix_path,) = matrix_paths.matrix_input_paths
        (new_matrix_path,) = matrix_paths.matrix_target_paths
        new_matrix_path.unlink(missing_ok=True)
        matrix_path.rename(new_matrix_path)
    elif new_operator == BindingConstraintOperator.BOTH:
        matrix_path_lt, matrix_path_gt = matrix_paths.matrix_target_paths
        if existing_operator == BindingConstraintOperator.EQUAL:
            (matrix_path_eq,) = matrix_paths.matrix_input_paths
            matrix_path_lt.unlink(missing_ok=True)
            matrix_path_gt.unlink(missing_ok=True)
            matrix_path_eq.rename(matrix_path_lt)
            # copy the matrix lt to gt
            shutil.copy(matrix_path_lt, matrix_path_gt)
        elif existing_operator == BindingConstraintOperator.LESS:
            matrix_path_gt.unlink(missing_ok=True)
            shutil.copy(matrix_path_lt, matrix_path_gt)
        elif existing_operator == BindingConstraintOperator.GREATER:
            matrix_path_lt.unlink(missing_ok=True)
            shutil.copy(matrix_path_gt, matrix_path_lt)
    elif existing_operator == BindingConstraintOperator.BOTH:
        matrix_path_lt, matrix_path_gt = matrix_paths.matrix_input_paths
        if new_operator == BindingConstraintOperator.EQUAL:
            # TODO: we may retrieve the mean of the two matrices, but here we just copy the lt matrix
            (matrix_path_eq,) = matrix_paths.matrix_target_paths
            shutil.copy(matrix_path_lt, matrix_path_eq)
            matrix_path_gt.unlink(missing_ok=True)
            matrix_path_lt.unlink(missing_ok=True)
        elif new_operator == BindingConstraintOperator.LESS:
            matrix_path_gt.unlink(missing_ok=True)
        elif new_operator == BindingConstraintOperator.GREATER:
            matrix_path_lt.unlink(missing_ok=True)


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

        # rename matrices if the operator has changed
        if self.operator:
            existing_operator = BindingConstraintOperator(actual_cfg.get("operator"))
            new_operator = BindingConstraintOperator(self.operator)
            _update_matrices_names(study_data, self.id, existing_operator, new_operator)

        updated_matrices = [term for term in TERM_MATRICES if hasattr(self, term) and getattr(self, term)]
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
        matrices = ["values"] + TERM_MATRICES
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
