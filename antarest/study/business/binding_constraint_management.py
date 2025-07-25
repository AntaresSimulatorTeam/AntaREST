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

import collections
import logging
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from antarest.core.exceptions import (
    BindingConstraintNotFound,
    ConstraintTermNotFound,
    DuplicateConstraintName,
    DuplicateConstraintTerm,
    InvalidConstraintName,
    InvalidFieldForVersionError,
    MatrixWidthMismatchError,
    WrongMatrixHeightError,
)
from antarest.core.model import JSON
from antarest.core.requests import CaseInsensitiveDict
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.binding_constraint_model import (
    DEFAULT_GROUP,
    BindingConstraint,
    BindingConstraintCreation,
    BindingConstraintFrequency,
    BindingConstraintMatrices,
    BindingConstraintOperator,
    BindingConstraintUpdate,
    BindingConstraintUpdates,
    ClusterTerm,
    ConstraintTerm,
    ConstraintTermUpdate,
    LinkTerm,
    create_binding_constraint,
    update_binding_constraint,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    EXPECTED_MATRIX_SHAPES,
    CreateBindingConstraint,
    TermMatrices,
)
from antarest.study.storage.variantstudy.model.command.remove_multiple_binding_constraints import (
    RemoveMultipleBindingConstraints,
)
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint
from antarest.study.storage.variantstudy.model.command.update_binding_constraints import UpdateBindingConstraints
from antarest.study.storage.variantstudy.model.command_context import CommandContext

logger = logging.getLogger(__name__)


class ConstraintFilters(AntaresBaseModel, extra="forbid"):
    """
    Binding Constraint Filters gathering the main filtering parameters.

    Attributes:
        bc_id: binding constraint ID (exact match)
        enabled: enabled status
        operator: operator
        comments: comments (word match, case-insensitive)
        group: on group name (exact match, case-insensitive)
        time_step: time step
        area_name: area name (word match, case-insensitive)
        cluster_name: cluster name (word match, case-insensitive)
        link_id: link ID ('area1%area2') in at least one term.
        cluster_id: cluster ID ('area.cluster') in at least one term.
    """

    bc_id: str = ""
    enabled: Optional[bool] = None
    operator: Optional[BindingConstraintOperator] = None
    comments: str = ""
    group: str = ""
    time_step: Optional[BindingConstraintFrequency] = None
    area_name: str = ""
    cluster_name: str = ""
    link_id: str = ""
    cluster_id: str = ""

    def match_filters(self, constraint: BindingConstraint) -> bool:
        """
        Check if the constraint matches the filters.

        Args:
            constraint: the constraint to check

        Returns:
            True if the constraint matches the filters, False otherwise
        """
        if self.bc_id and self.bc_id != constraint.id:
            # The `bc_id` filter is a case-sensitive exact match.
            return False
        if self.enabled is not None and self.enabled != constraint.enabled:
            return False
        if self.operator is not None and self.operator != constraint.operator:
            return False
        if self.comments:
            # The `comments` filter is a case-insensitive substring match.
            comments = constraint.comments or ""
            if self.comments.upper() not in comments.upper():
                return False
        if self.group:
            # The `group` filter is a case-insensitive exact match.
            group = constraint.group or DEFAULT_GROUP
            if self.group.upper() != group.upper():
                return False
        if self.time_step is not None and self.time_step != constraint.time_step:
            return False

        terms = constraint.terms

        if self.area_name:
            # The `area_name` filter is a case-insensitive substring match.
            area_name_upper = self.area_name.upper()
            for data in (term.data for term in terms if term.data):
                # fmt: off
                if (
                    isinstance(data, LinkTerm)
                    and (area_name_upper in data.area1.upper() or area_name_upper in data.area2.upper())
                ) or (
                    isinstance(data, ClusterTerm)
                    and area_name_upper in data.area.upper()
                ):
                    break
                # fmt: on
            else:
                return False

        if self.cluster_name:
            # The `cluster_name` filter is a case-insensitive substring match.
            cluster_name_upper = self.cluster_name.upper()
            for data in (term.data for term in terms if term.data):
                if isinstance(data, ClusterTerm) and cluster_name_upper in data.cluster.upper():
                    break
            else:
                return False

        if self.link_id:
            # The `link_id` filter is a case-insensitive exact match.
            all_link_ids = [term.generate_id() for term in terms if isinstance(term.data, LinkTerm)]
            if self.link_id.lower() not in all_link_ids:
                return False

        if self.cluster_id:
            # The `cluster_id` filter is a case-insensitive exact match.
            all_cluster_ids = [term.generate_id() for term in terms if isinstance(term.data, ClusterTerm)]
            if self.cluster_id.lower() not in all_cluster_ids:
                return False

        return True


def _get_references_by_widths(
    study: StudyInterface, bcs: Sequence[BindingConstraint]
) -> Mapping[int, Sequence[Tuple[str, str]]]:
    """
    Iterates over each BC and its associated matrices.
    For each matrix, it checks its width according to the expected matrix shapes.
    It then groups the binding constraints by these widths.

    Notes:
        The height of the matrices may vary depending on the time step,
        but the width should be consistent within a group of binding constraints.
    """

    references_by_width: Dict[int, List[Tuple[str, str]]] = {}
    _total = len(bcs)
    study_dao = study.get_study_dao()
    for _index, bc in enumerate(bcs):
        if study.version < STUDY_VERSION_8_7:
            matrices = {"values": study_dao.get_constraint_values_matrix(bc.id)}
        else:
            matrices = {}
            operator = bc.operator
            if operator == BindingConstraintOperator.EQUAL:
                matrices["equal term"] = study_dao.get_constraint_equal_term_matrix(bc.id)
            if operator in {BindingConstraintOperator.GREATER, BindingConstraintOperator.BOTH}:
                matrices["greater term"] = study_dao.get_constraint_greater_term_matrix(bc.id)
            if operator in {BindingConstraintOperator.LESS, BindingConstraintOperator.BOTH}:
                matrices["less term"] = study_dao.get_constraint_less_term_matrix(bc.id)

        for matrix_id, matrix in matrices.items():
            if matrix.empty:
                # We ignore empty matrices as there are default matrices for the simulator.
                continue

            matrix_height = matrix.shape[0]
            expected_height = EXPECTED_MATRIX_SHAPES[bc.time_step][0]
            if matrix_height != expected_height:
                raise WrongMatrixHeightError(
                    f"The binding constraint '{bc.name}' should have {expected_height} rows, currently: {matrix_height}"
                )
            matrix_width = matrix.shape[1]
            if matrix_width > 1:
                references_by_width.setdefault(matrix_width, []).append((bc.id, matrix_id))

    return references_by_width


def _validate_binding_constraints(study: StudyInterface, bcs: Sequence[BindingConstraint]) -> bool:
    """
    Validates the binding constraints within a group.
    """
    references_by_widths = _get_references_by_widths(study, bcs)

    if len(references_by_widths) > 1:
        most_common = collections.Counter(references_by_widths.keys()).most_common()
        invalid_constraints: Dict[str, str] = {}

        for width, _ in most_common[1:]:
            references = references_by_widths[width]
            for bc_id, matrix_id in references:
                existing_key = invalid_constraints.get(bc_id, "")
                if existing_key:
                    existing_key += ", "
                existing_key += f"'{matrix_id}' has {width} columns"
                invalid_constraints[bc_id] = existing_key

        expected_width = most_common[0][0]
        raise MatrixWidthMismatchError(
            f"Mismatch widths: the most common width in the group is {expected_width}"
            f" but we have: {invalid_constraints!r}"
        )

    return True


class BindingConstraintManager:
    def __init__(
        self,
        command_context: CommandContext,
    ) -> None:
        self._command_context = command_context

    def get_binding_constraint(self, study: StudyInterface, bc_id: str) -> BindingConstraint:
        """
        Retrieves a binding constraint by its ID within a given study.

        Args:
            study: The study from which to retrieve the constraint.
            bc_id: The ID of the binding constraint to retrieve.

        Returns:
            A BindingConstraint object representing the binding constraint with the specified ID.

        Raises:
            BindingConstraintNotFound: If no binding constraint with the specified ID is found.
        """
        return study.get_study_dao().get_constraint(bc_id)

    def get_binding_constraints(
        self, study: StudyInterface, filters: ConstraintFilters = ConstraintFilters()
    ) -> Sequence[BindingConstraint]:
        """
        Retrieves all binding constraints within a given study, optionally filtered by specific criteria.

        Args:
            study: The study from which to retrieve the constraints.
            filters: The filters to apply when retrieving the constraints.

        Returns:
            A list of BindingConstraint objects representing the binding constraints that match the specified filters.
        """
        all_constraints = study.get_study_dao().get_all_constraints()
        filtered_constraints = list(filter(lambda c: filters.match_filters(c), all_constraints.values()))
        return filtered_constraints

    def get_grouped_constraints(self, study: StudyInterface) -> Mapping[str, Sequence[BindingConstraint]]:
        """
         Retrieves and groups all binding constraints by their group names within a given study.

        This method organizes binding constraints into a dictionary where each key corresponds to a group name,
        and the value is a list of BindingConstraint objects associated with that group.

        Args:
            study: the study

        Returns:
            A dictionary mapping group names to lists of binding constraints associated with each group.

        Notes:
        The grouping considers the exact group name, implying case sensitivity. If case-insensitive grouping
        is required, normalization of group names to a uniform case (e.g., all lower or upper) should be performed.
        """
        all_constraints = study.get_study_dao().get_all_constraints()
        grouped_constraints = CaseInsensitiveDict()
        for constraint in all_constraints.values():
            group = constraint.group or DEFAULT_GROUP
            grouped_constraints.setdefault(group, []).append(constraint)
        return grouped_constraints

    def get_constraints_by_group(self, study: StudyInterface, group_name: str) -> Sequence[BindingConstraint]:
        """
         Retrieve all binding constraints belonging to a specified group within a study.

        Args:
            study: The study from which to retrieve the constraints.
            group_name: The name of the group (case-insensitive).

        Returns:
            A list of BindingConstraint objects that belong to the specified group.

        Raises:
            BindingConstraintNotFound: If the specified group name is not found among the constraint groups.
        """
        grouped_constraints = self.get_grouped_constraints(study)

        if group_name not in grouped_constraints:
            raise BindingConstraintNotFound(f"Group '{group_name}' not found")

        return grouped_constraints[group_name]

    def validate_constraint_group(self, study: StudyInterface, group_name: str) -> bool:
        """
        Validates if the specified group name exists within the study's binding constraints
        and checks the validity of the constraints within that group.

        This method performs a case-insensitive search to match the specified group name against
        existing groups of binding constraints. It ensures that the group exists and then
        validates the constraints within that found group.

        Args:
            study: The study object containing binding constraints.
            group_name: The name of the group (case-insensitive).

        Returns:
            True if the group exists and the constraints within the group are valid; False otherwise.

        Raises:
            BindingConstraintNotFound: If no matching group name is found in a case-insensitive manner.
        """
        grouped_constraints = self.get_grouped_constraints(study)

        if group_name not in grouped_constraints:
            raise BindingConstraintNotFound(f"Group '{group_name}' not found")

        constraints = grouped_constraints[group_name]
        return _validate_binding_constraints(study, constraints)

    def validate_constraint_groups(self, study: StudyInterface) -> bool:
        """
        Validates all groups of binding constraints within the given study.

        This method checks each group of binding constraints for validity based on specific criteria
        (e.g., coherence between matrices lengths). If any group fails the validation, an aggregated
        error detailing all incoherence is raised.

        Args:
            study: The study object containing binding constraints.

        Returns:
            True if all constraint groups are valid.

        Raises:
            IncoherenceBetweenMatricesLength: If any validation checks fail.
        """
        grouped_constraints = self.get_grouped_constraints(study)
        invalid_groups = {}

        for group_name, bcs in grouped_constraints.items():
            try:
                _validate_binding_constraints(study, bcs)
            except MatrixWidthMismatchError as e:
                invalid_groups[group_name] = e.detail

        if invalid_groups:
            err_msg = ", ".join(f"'{grp}': {msg}" for grp, msg in sorted(invalid_groups.items()))
            raise MatrixWidthMismatchError(err_msg)

        return True

    def create_binding_constraint(
        self,
        study: StudyInterface,
        data: BindingConstraintCreation,
        matrices: BindingConstraintMatrices,
    ) -> BindingConstraint:
        bc_id = transform_name_to_id(data.name)

        if not bc_id:
            raise InvalidConstraintName(f"Invalid binding constraint name: {data.name}.")

        if bc_id in {bc.id for bc in self.get_binding_constraints(study)}:
            raise DuplicateConstraintName(f"A binding constraint with the same name already exists: {bc_id}.")

        new_constraint = create_binding_constraint(data, study.version)
        if study.version >= STUDY_VERSION_8_7:
            _check_matrices_coherence(new_constraint, matrices)

        args = {
            "parameters": data,
            "matrices": matrices,
            "command_context": self._command_context,
            "study_version": study.version,
        }
        command = CreateBindingConstraint(**args)
        study.add_commands([command])

        return new_constraint

    def duplicate_binding_constraint(
        self, study: StudyInterface, source_id: str, new_constraint_name: str
    ) -> BindingConstraint:
        """
        Creates a duplicate constraint with a new name.

        Args:
            study: The study in which the cluster will be duplicated.
            source_id: The identifier of the constraint to be duplicated.
            new_constraint_name: The new name for the duplicated constraint.

        Returns:
            The duplicated constraint configuration.

        Raises:
            DuplicateConstraintName: If a constraint with the new name already exists in the study.
        """

        # Checks if the new constraint already exists
        new_constraint_id = transform_name_to_id(new_constraint_name)
        existing_constraints = self.get_binding_constraints(study)
        if new_constraint_id in {bc.id for bc in existing_constraints}:
            raise DuplicateConstraintName(
                f"A binding constraint with the same name already exists: {new_constraint_name}."
            )

        # Retrieval of the source constraint properties
        source_constraint = next(iter(bc for bc in existing_constraints if bc.id == source_id), None)
        if not source_constraint:
            raise BindingConstraintNotFound(f"Binding constraint '{source_id}' not found")

        source_constraint.name = new_constraint_name
        constraint_creation = BindingConstraintCreation.from_constraint(source_constraint)

        args: dict[str, Any] = {
            "parameters": constraint_creation,
            "command_context": self._command_context,
            "study_version": study.version,
            "matrices": {},
        }

        # Retrieval of the source constraint matrices
        study_dao = study.get_study_dao()
        if study.version < STUDY_VERSION_8_7:
            matrix = study_dao.get_constraint_values_matrix(source_id).to_numpy().tolist()
            args["matrices"]["values"] = matrix
        else:
            if source_constraint.operator == BindingConstraintOperator.EQUAL:
                matrix = study_dao.get_constraint_equal_term_matrix(source_id).to_numpy().tolist()
                args["matrices"]["equal_term_matrix"] = matrix

            if source_constraint.operator in {BindingConstraintOperator.GREATER, BindingConstraintOperator.BOTH}:
                matrix = study_dao.get_constraint_greater_term_matrix(source_id).to_numpy().tolist()
                args["matrices"]["greater_term_matrix"] = matrix

            if source_constraint.operator in {BindingConstraintOperator.LESS, BindingConstraintOperator.BOTH}:
                matrix = study_dao.get_constraint_less_term_matrix(source_id).to_numpy().tolist()
                args["matrices"]["less_term_matrix"] = matrix

        # Creates and applies constraint
        command = CreateBindingConstraint(**args)
        study.add_commands([command])

        # Returns the new constraint
        return create_binding_constraint(constraint_creation, study.version)

    def update_binding_constraint(
        self,
        study: StudyInterface,
        binding_constraint_id: str,
        data: BindingConstraintUpdate,
        matrices: BindingConstraintMatrices,
    ) -> BindingConstraint:
        existing_constraint = self.get_binding_constraint(study, binding_constraint_id)

        args: dict[str, Any] = {
            "id": binding_constraint_id,
            "parameters": data,
            "matrices": matrices,
            "command_context": self._command_context,
            "study_version": study.version,
        }

        new_constraint = update_binding_constraint(existing_constraint, data)

        if study.version >= STUDY_VERSION_8_7:
            _check_matrices_coherence(new_constraint, matrices)

        command = UpdateBindingConstraint(**args)
        study.add_commands([command])

        return update_binding_constraint(existing_constraint, data)

    def update_binding_constraints(
        self,
        study: StudyInterface,
        bcs_by_ids: BindingConstraintUpdates,
    ) -> Mapping[str, BindingConstraint]:
        """
        Updates multiple binding constraints within a study.

        Args:
            study: The study from which to update the constraints.
            bcs_by_ids: A mapping of binding constraint IDs to their updated configurations.

        Returns:
            A dictionary of the updated binding constraints, indexed by their IDs.

        Raises:
            BindingConstraintNotFound: If any of the specified binding constraint IDs are not found.
        """
        study_dao = study.get_study_dao()
        all_constraints = study_dao.get_all_constraints()
        constraints = {}

        for bc_id, bc_update in bcs_by_ids.items():
            # check binding constraint id sent by user exist for this study
            # Note that this check is both done here and when the command is applied as well
            if bc_id not in all_constraints:
                raise BindingConstraintNotFound(f"Binding constraint '{bc_id}' not found")

            # Update the binding constraint properties
            old_constraint = all_constraints[bc_id]
            new_constraint = update_binding_constraint(old_constraint, bc_update)
            constraints[new_constraint.id] = new_constraint

        command = UpdateBindingConstraints(
            bc_props_by_id=bcs_by_ids,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

        return constraints

    def remove_multiple_binding_constraints(self, study: StudyInterface, binding_constraints_ids: List[str]) -> None:
        """
        Removes multiple binding constraints from a study.

        Args:
            study: The study from which to remove the constraint.
            binding_constraints_ids: The IDs of the binding constraints to remove.
        """

        all_constraints = study.get_study_dao().get_all_constraints()
        missing_bc_ids = [bc_id for bc_id in binding_constraints_ids if bc_id not in all_constraints]
        if missing_bc_ids:
            raise BindingConstraintNotFound(f"Binding constraint(s) '{missing_bc_ids}' not found")

        command = RemoveMultipleBindingConstraints(
            ids=binding_constraints_ids,
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

    def _update_constraint_with_terms(
        self, study: StudyInterface, bc: BindingConstraint, terms: Mapping[str, ConstraintTerm]
    ) -> None:
        constraint_update = BindingConstraintUpdate(**{"terms": terms.values()})
        args = {
            "id": bc.id,
            "parameters": constraint_update,
            "matrices": {},
            "command_context": self._command_context,
            "study_version": study.version,
        }
        command = UpdateBindingConstraint.model_validate(args)
        study.add_commands([command])

    def add_constraint_terms(
        self, study: StudyInterface, binding_constraint_id: str, constraint_terms: Sequence[ConstraintTerm]
    ) -> None:
        """
        Adds new constraint terms to an existing binding constraint.

        Args:
            study: The study from which to update the binding constraint.
            binding_constraint_id: The ID of the binding constraint to update.
            constraint_terms: The constraint terms to add.
        """
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        existing_terms = {term.generate_id(): term for term in constraint.terms}

        new_terms = {term.generate_id(): term for term in constraint_terms}
        duplicate_terms = set(new_terms) & set(existing_terms)
        if duplicate_terms:
            raise DuplicateConstraintTerm(binding_constraint_id, *duplicate_terms)

        existing_terms.update(new_terms)
        sorted_terms = dict(sorted(existing_terms.items()))
        self._update_constraint_with_terms(study, constraint, sorted_terms)

    def update_constraint_terms(
        self, study: StudyInterface, binding_constraint_id: str, constraint_terms: Sequence[ConstraintTermUpdate]
    ) -> None:
        """
        Update the specified constraint terms.

        Args:
            study: The study from which to update the binding constraint.
            binding_constraint_id: The ID of the binding constraint to update.
            constraint_terms: The constraint terms to update.
        """

        constraint = self.get_binding_constraint(study, binding_constraint_id)
        existing_terms = {term.generate_id(): term for term in constraint.terms}

        ids_to_update = {term.id for term in constraint_terms}
        missing_terms = ids_to_update - set(existing_terms)
        if missing_terms:
            raise ConstraintTermNotFound(binding_constraint_id, *missing_terms)

        # Updates existing terms
        for term in constraint_terms:
            new_term = existing_terms.pop(term.id).update_from(term)
            existing_terms[new_term.generate_id()] = new_term

        sorted_terms = dict(sorted(existing_terms.items()))
        self._update_constraint_with_terms(study, constraint, sorted_terms)

    def remove_constraint_term(
        self,
        study: StudyInterface,
        binding_constraint_id: str,
        term_id: str,
    ) -> None:
        """
        Remove a constraint term from an existing binding constraint.

        Args:
            study: The study from which to update the binding constraint.
            binding_constraint_id: The ID of the binding constraint to update.
            term_id: The ID of the term to remove.
        """
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        existing_terms = collections.OrderedDict((term.generate_id(), term) for term in constraint.terms)
        removed_term = existing_terms.pop(term_id, None)
        if removed_term is None:
            raise ConstraintTermNotFound(binding_constraint_id, term_id)
        self._update_constraint_with_terms(study, constraint, existing_terms)

    @staticmethod
    def get_table_schema() -> JSON:
        return BindingConstraint.model_json_schema()


def _check_matrices_coherence(constraint: BindingConstraint, matrices: BindingConstraintMatrices) -> None:
    OPERATOR_CONFLICT_MAP = {
        BindingConstraintOperator.EQUAL: [TermMatrices.LESS.value, TermMatrices.GREATER.value],
        BindingConstraintOperator.GREATER: [TermMatrices.LESS.value, TermMatrices.EQUAL.value],
        BindingConstraintOperator.LESS: [TermMatrices.EQUAL.value, TermMatrices.GREATER.value],
        BindingConstraintOperator.BOTH: [TermMatrices.EQUAL.value],
    }

    operator = constraint.operator

    conflicting_matrices = [
        getattr(matrices, matrix) for matrix in OPERATOR_CONFLICT_MAP[operator] if getattr(matrices, matrix)
    ]
    if conflicting_matrices:
        raise InvalidFieldForVersionError(
            f"You cannot fill matrices '{OPERATOR_CONFLICT_MAP[operator]}' while using the operator '{operator}'"
        )
